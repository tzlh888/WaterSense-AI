"""Scoped v2 robustness analyses; v1 outputs and the deployed model stay read-only."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import (ExtraTreesRegressor, HistGradientBoostingRegressor,
                              RandomForestRegressor)
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

from .preprocessing import (
    WATER_QUALITY_CENSOR_FEATURES,
    WATER_QUALITY_EXTENDED_CENSOR_FEATURES,
    WATER_QUALITY_EXTENDED_MEASUREMENT_FEATURES,
    WATER_QUALITY_MEASUREMENT_FEATURES,
    WATER_QUALITY_TEMPORAL_FEATURES,
    grouped_station_holdout,
    load_niea_raw,
    prepare_water_quality_modeling_data,
)
from .refine import phase4_pipeline
from .research_analysis import (
    assert_disjoint,
    chronological_split,
    error_summary,
    interval_predictions,
    label_do_ranges,
    residual_frame,
    residual_radius,
    spatiotemporal_split,
    standardized_mean_difference,
)
from .research_config import DATE, FEATURE_SETS, GROUP, TARGET, ResearchConfig
from .research_experiments import protected_hashes, sha256, verified_research
from .research_reporting import markdown_table


V2_SEEDS = (11, 23, 42, 57, 71, 89, 101, 123, 149, 173)
DO_RANGES = ("<4", "4–<8", "8–<12", "≥12")


def reduced_feature_sets() -> dict[str, tuple[list[str], bool]]:
    """Five predeclared, cumulative groups; bool controls learned indicators."""
    core = list(WATER_QUALITY_MEASUREMENT_FEATURES)
    date = list(WATER_QUALITY_TEMPORAL_FEATURES)
    censor = list(WATER_QUALITY_CENSOR_FEATURES)
    return {
        "Core": (core, False),
        "Core + Date": (core + date, False),
        "Core + Date + Missingness": (core + date, True),
        "Core + Date + Missingness + Censoring": (core + date + censor, True),
        "Full": (list(FEATURE_SETS["full"][0]), True),
    }


def fixed_models(config: ResearchConfig) -> dict[str, object]:
    """Five fixed model families; no search and no production-model selection."""
    return {
        "DummyRegressor": DummyRegressor(strategy="mean"),
        "Ridge": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(
            n_estimators=config.n_estimators, min_samples_leaf=config.min_samples_leaf,
            max_features=config.max_features, random_state=config.seed, n_jobs=config.n_jobs),
        "Extra Trees": ExtraTreesRegressor(
            n_estimators=config.n_estimators, min_samples_leaf=config.min_samples_leaf,
            max_features=config.max_features, random_state=config.seed, n_jobs=config.n_jobs),
        "HistGradientBoosting": HistGradientBoostingRegressor(
            learning_rate=.05, max_iter=200, max_leaf_nodes=15,
            l2_regularization=1.0, random_state=config.seed),
    }


def make_pipeline(estimator, features: list[str], missingness: bool):
    pipeline = phase4_pipeline(features, clone(estimator))
    pipeline.set_params(preprocessing__numeric__imputer__add_indicator=missingness)
    return pipeline


def split_summary(frame: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    """Summarise independent split-level values without pseudo-confidence bounds."""
    rows = []
    for metric in metrics:
        values = frame[metric].dropna().astype(float)
        rows.append({"metric": metric, "splits": len(values), "mean": values.mean(),
                     "std": values.std(ddof=1), "median": values.median(),
                     "iqr": values.quantile(.75) - values.quantile(.25),
                     "minimum": values.min(), "maximum": values.max()})
    return pd.DataFrame(rows)


def coverage_by_do(frame: pd.DataFrame) -> pd.DataFrame:
    labelled = label_do_ranges(frame)
    rows = []
    for concentration in DO_RANGES:
        part = labelled[labelled.do_range == concentration]
        rows.append({"do_range": concentration, "sample_count": len(part),
                     "empirical_coverage": part.covered.mean() if len(part) else np.nan})
    return pd.DataFrame(rows)


def importance_aggregation(fold_values: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate permutation-repeat SD within folds from variation across folds."""
    required = {"fold", "feature", "mae_increase", "permutation_sd", "rank"}
    if not required.issubset(fold_values.columns):
        raise ValueError(f"Importance rows require {sorted(required)}")
    folds = sorted(fold_values.fold.unique())
    features = fold_values.feature.unique()
    if len(folds) < 2 or any(set(fold_values[fold_values.fold == f].feature) != set(features)
                             for f in folds):
        raise ValueError("Complete importance vectors from at least two folds are required.")
    summary = fold_values.groupby("feature", sort=False).agg(
        mean_mae_increase=("mae_increase", "mean"),
        across_fold_mae_increase_sd=("mae_increase", "std"),
        mean_within_fold_permutation_sd=("permutation_sd", "mean"),
        mean_rank=("rank", "mean"), rank_sd=("rank", "std"),
        top5_fraction=("rank", lambda x: x.le(5).mean()),
        top10_fraction=("rank", lambda x: x.le(10).mean()),
    ).reset_index().sort_values(["mean_rank", "feature"])
    wide = fold_values.pivot(index="feature", columns="fold", values="rank")
    rows = []
    for i, left in enumerate(folds):
        for right in folds[i + 1:]:
            rho = wide[left].corr(wide[right], method="spearman")
            rows.append({"fold_a": left, "fold_b": right, "spearman_r": rho})
    correlations = pd.DataFrame(rows)
    return summary, correlations


def verify_hash_mapping(root: Path, hashes: dict[str, str]) -> None:
    for name, expected in hashes.items():
        path = root / name
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"Protected file changed or is missing: {name}")


def _save_csv(output: Path, name: str, frame: pd.DataFrame) -> None:
    frame.to_csv(output / "tables" / f"{name}.csv", index=False)


def _save_gzip(output: Path, name: str, frame: pd.DataFrame) -> None:
    frame.to_csv(output / "predictions" / f"{name}.csv.gz", index=False,
                 compression={"method": "gzip", "mtime": 0})


def _evaluate(data: pd.DataFrame, pipeline, indices: np.ndarray,
              features: list[str]) -> pd.DataFrame:
    return residual_frame(data.iloc[indices], pipeline.predict(data.iloc[indices][features]))


def _fit(data: pd.DataFrame, train: np.ndarray, estimator, features: list[str],
         missingness: bool):
    pipeline = make_pipeline(estimator, features, missingness)
    pipeline.fit(data.iloc[train][features], data.iloc[train][TARGET])
    return pipeline


def _low_do_summary(frame: pd.DataFrame) -> dict:
    low = frame[frame.actual < 4]
    if low.empty:
        return {"low_do_n": 0, "low_do_mae": np.nan, "low_do_rmse": np.nan,
                "low_do_mean_residual": np.nan, "low_do_overpredicted_fraction": np.nan}
    return {"low_do_n": len(low), "low_do_mae": low.absolute_error.mean(),
            "low_do_rmse": np.sqrt(np.mean(low.residual ** 2)),
            "low_do_mean_residual": low.residual.mean(),
            "low_do_overpredicted_fraction": low.predicted.gt(low.actual).mean()}


def _do_error_rows(frame: pd.DataFrame, **metadata) -> list[dict]:
    labelled = label_do_ranges(frame)
    rows = []
    for concentration in DO_RANGES:
        part = labelled[labelled.do_range == concentration]
        values = ({"sample_count": 0, "mae": np.nan, "rmse": np.nan,
                   "bias": np.nan, "overpredicted_fraction": np.nan}
                  if part.empty else
                  {"sample_count": len(part), "mae": part.absolute_error.mean(),
                   "rmse": np.sqrt(np.mean(part.residual ** 2)), "bias": part.residual.mean(),
                   "overpredicted_fraction": part.predicted.gt(part.actual).mean()})
        rows.append({**metadata, "do_range": concentration, **values})
    return rows


def _model_metrics(frame: pd.DataFrame, **metadata) -> dict:
    return {**metadata, **error_summary(frame), **_low_do_summary(frame),
            "low_do_sufficient_n20": int((frame.actual < 4).sum()) >= 20}


def _station_basin_metadata(raw: pd.DataFrame, data: pd.DataFrame) -> pd.DataFrame:
    meta = raw[["StationCode", "PrimaryBasin"]].copy()
    meta["PrimaryBasin"] = meta.PrimaryBasin.astype("string").str.strip().replace("", pd.NA)
    model_stations = set(data[GROUP])
    meta = meta[meta.StationCode.isin(model_stations)]
    consistency = meta.groupby("StationCode").PrimaryBasin.agg(
        lambda x: x.dropna().nunique())
    if consistency.gt(1).any():
        raise ValueError("PrimaryBasin is inconsistent within a monitoring station.")
    mapping = meta.dropna().drop_duplicates("StationCode").rename(
        columns={"StationCode": GROUP, "PrimaryBasin": "primary_basin"})
    return mapping[[GROUP, "primary_basin"]]


def basin_group_split(data: pd.DataFrame, test_fraction: float = .2,
                      seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """One basin-disjoint split; stations must map to exactly one nonmissing basin."""
    if data.primary_basin.isna().any():
        raise ValueError("Basin validation requires nonmissing PrimaryBasin labels.")
    if data.groupby(GROUP).primary_basin.nunique().gt(1).any():
        raise ValueError("A monitoring station cannot span multiple basin groups.")
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_fraction,
                                 random_state=seed)
    train, test = next(splitter.split(data, groups=data.primary_basin))
    if set(data.iloc[train].primary_basin) & set(data.iloc[test].primary_basin):
        raise RuntimeError("River-basin leakage detected.")
    assert_disjoint(data, train, test, stations=True)
    return train, test


def _git_commit(root: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def run_v2(root: Path, output: Path, config: ResearchConfig | None = None) -> dict:
    """Execute only the scoped v2 analyses into a new empty directory."""
    root, output = Path(root), Path(output)
    config = config or ResearchConfig()
    if config.fast:
        raise ValueError("v2 release evidence cannot use smoke mode.")
    if output.exists() and any(output.iterdir()):
        raise ValueError("v2 output directory must be new or empty.")
    for folder in ("tables", "figures", "predictions", "reports", "manifests"):
        (output / folder).mkdir(parents=True, exist_ok=True)

    v1_dir = root / "research_outputs"
    v1 = verified_research(v1_dir)
    v1_manifest_hash = sha256(v1_dir / "manifest.json")
    before_protected = protected_hashes(root)
    verify_hash_mapping(v1_dir, v1["output_hashes"])
    raw_path = root / "data/raw/niea_river_water_quality_1990_2024.csv"
    raw = load_niea_raw(raw_path)
    data, audit = prepare_water_quality_modeling_data(raw)
    features = list(FEATURE_SETS["full"][0])
    rf = fixed_models(config)["Random Forest"]
    top_features = pd.read_csv(v1_dir / "tables/feature_importance.csv").feature.head(6).tolist()
    timings = []

    # A. Exactly ten predefined spatiotemporal splits and their training-side intervals.
    split_rows, predictions, bin_rows, low_rows = [], [], [], []
    uncertainty_rows, uncertainty_bins, interval_predictions_rows = [], [], []
    shift_rows = []
    heldout_rows = []
    for seed in V2_SEEDS:
        print(f"Repeated spatiotemporal seed {seed}", flush=True)
        parts, inventory = spatiotemporal_split(
            data, config.validation_end_year, config.test_fraction, seed)
        train, test = parts["train"], parts["test"]
        start = perf_counter()
        pipeline = _fit(data, train, rf, features, True)
        frame = _evaluate(data, pipeline, test, features)
        timings.append({"experiment": "repeated_spatiotemporal", "seed": seed,
                        "elapsed_seconds": perf_counter() - start})
        frame.insert(0, "seed", seed)
        predictions.append(frame)
        heldout = inventory[inventory.held_out][GROUP].sort_values()
        heldout_rows.extend({"seed": seed, GROUP: station} for station in heldout)
        row = {"seed": seed, **error_summary(frame),
               "train_rows": len(train), "test_rows": len(test),
               "train_stations": data.iloc[train][GROUP].nunique(),
               "test_stations": data.iloc[test][GROUP].nunique(),
               "station_overlap": len(set(data.iloc[train][GROUP]) & set(data.iloc[test][GROUP])),
               "train_first_date": data.iloc[train][DATE].min(),
               "train_last_date": data.iloc[train][DATE].max(),
               "test_first_date": data.iloc[test][DATE].min(),
               "test_last_date": data.iloc[test][DATE].max(),
               "test_target_mean": data.iloc[test][TARGET].mean(),
               "test_target_median": data.iloc[test][TARGET].median(),
               "test_low_do_fraction": data.iloc[test][TARGET].lt(4).mean()}
        split_rows.append(row)
        low_rows.append({"seed": seed, **_low_do_summary(frame)})
        bin_rows.extend(_do_error_rows(frame, seed=seed))
        for feature in top_features:
            shift_rows.append({"seed": seed, "feature": feature,
                               "standardized_mean_difference": standardized_mean_difference(
                                   data.iloc[train][feature], data.iloc[test][feature]),
                               "train_median": data.iloc[train][feature].median(),
                               "test_median": data.iloc[test][feature].median(),
                               "train_iqr": data.iloc[train][feature].quantile(.75) - data.iloc[train][feature].quantile(.25),
                               "test_iqr": data.iloc[test][feature].quantile(.75) - data.iloc[test][feature].quantile(.25)})

        # Same empirical residual-interval method, calibration wholly on training-side stations.
        proper_local, cal_local = grouped_station_holdout(
            data.iloc[train], test_size=config.calibration_fraction, random_state=seed)
        proper, calibration = train[proper_local], train[cal_local]
        assert_disjoint(data, proper, calibration, test, stations=True)
        interval_pipe = _fit(data, proper, rf, features, True)
        calibration_frame = _evaluate(data, interval_pipe, calibration, features)
        interval_test = _evaluate(data, interval_pipe, test, features)
        radius = residual_radius(calibration_frame.residual.to_numpy(), config.coverage)
        interval_test = interval_predictions(interval_test, radius)
        interval_test.insert(0, "seed", seed)
        interval_predictions_rows.append(interval_test)
        uncertainty_rows.append({"regime": "Repeated spatiotemporal", "seed": seed,
                                 "nominal_coverage": config.coverage,
                                 "empirical_coverage": interval_test.covered.mean(),
                                 "mean_interval_width": (interval_test.upper - interval_test.lower).mean(),
                                 "radius": radius, "proper_train_rows": len(proper),
                                 "calibration_rows": len(calibration), "test_rows": len(test),
                                 "point_mae": interval_test.absolute_error.mean()})
        coverage = coverage_by_do(interval_test)
        coverage.insert(0, "seed", seed)
        uncertainty_bins.append(coverage)

    repeated = pd.DataFrame(split_rows)
    low_do = pd.DataFrame(low_rows)
    errors_by_range = pd.DataFrame(bin_rows)
    shifts = pd.DataFrame(shift_rows)
    uncertainty = pd.DataFrame(uncertainty_rows)
    uncertainty_by_range = pd.concat(uncertainty_bins, ignore_index=True)
    all_predictions = pd.concat(predictions, ignore_index=True)
    all_intervals = pd.concat(interval_predictions_rows, ignore_index=True)
    _save_csv(output, "repeated_spatiotemporal_results", repeated)
    _save_csv(output, "repeated_spatiotemporal_summary", split_summary(repeated, [
        "mae", "rmse", "r2", "median_absolute_error", "p90_absolute_error",
        "p95_absolute_error", "train_rows", "test_rows", "train_stations",
        "test_stations", "test_target_mean", "test_target_median", "test_low_do_fraction"]))
    _save_csv(output, "repeated_spatiotemporal_low_do", low_do)
    _save_csv(output, "repeated_spatiotemporal_low_do_summary", split_summary(low_do, [
        "low_do_n", "low_do_mae", "low_do_rmse", "low_do_mean_residual",
        "low_do_overpredicted_fraction"]))
    _save_csv(output, "repeated_spatiotemporal_error_by_do_range", errors_by_range)
    _save_csv(output, "repeated_spatiotemporal_heldout_stations", pd.DataFrame(heldout_rows))
    _save_gzip(output, "repeated_spatiotemporal_predictions", all_predictions)

    # B. One river-basin-disjoint validation using existing, audited metadata.
    basin_mapping = _station_basin_metadata(raw, data)
    spatial_data = data.merge(basin_mapping, on=GROUP, how="inner", validate="many_to_one")
    excluded_stations = data.loc[~data[GROUP].isin(basin_mapping[GROUP]), GROUP].nunique()
    basin_train, basin_test = basin_group_split(
        spatial_data, config.test_fraction, config.seed)
    basin_pipe = _fit(spatial_data, basin_train, rf, features, True)
    basin_frame = _evaluate(spatial_data, basin_pipe, basin_test, features)
    spatial_result = pd.DataFrame([{
        "strategy": "PrimaryBasin holdout", **error_summary(basin_frame),
        "train_rows": len(basin_train), "test_rows": len(basin_test),
        "train_stations": spatial_data.iloc[basin_train][GROUP].nunique(),
        "test_stations": spatial_data.iloc[basin_test][GROUP].nunique(),
        "train_basins": spatial_data.iloc[basin_train].primary_basin.nunique(),
        "test_basins": spatial_data.iloc[basin_test].primary_basin.nunique(),
        "basin_overlap": 0, "station_overlap": 0,
        "excluded_missing_basin_rows": len(data) - len(spatial_data),
        "excluded_missing_basin_stations": excluded_stations,
        **_low_do_summary(basin_frame)}])
    basin_assignments = spatial_data[[GROUP, "primary_basin"]].drop_duplicates().assign(
        partition=lambda x: np.where(x.primary_basin.isin(
            spatial_data.iloc[basin_test].primary_basin.unique()), "test", "train"))
    _save_csv(output, "spatial_basin_validation", spatial_result)
    _save_csv(output, "spatial_basin_assignments", basin_assignments)
    _save_gzip(output, "spatial_basin_predictions", basin_frame)

    # Shared v1 station-grouped training folds for importance, ablation and models.
    group_train, group_test = grouped_station_holdout(
        data, test_size=config.test_fraction, random_state=config.seed)
    assert_disjoint(data, group_train, group_test, stations=True)
    folds = [(group_train[a], group_train[b]) for a, b in GroupKFold(
        n_splits=config.cv_folds).split(group_train, groups=data.iloc[group_train][GROUP])]
    cache: dict[tuple[str, str, int], tuple[object, pd.DataFrame]] = {}

    def fold_eval(model_name: str, feature_name: str, fold_number: int,
                  estimator, selected: list[str], indicators: bool):
        key = (model_name, feature_name, fold_number)
        if key not in cache:
            train, validation = folds[fold_number - 1]
            assert_disjoint(data, train, validation, group_test, stations=True)
            pipe = _fit(data, train, estimator, selected, indicators)
            cache[key] = (pipe, _evaluate(data, pipe, validation, selected))
        return cache[key]

    # C. Reduced five-configuration grouped-CV ablation.
    ablation_folds = []
    transformed_counts = {}
    for feature_name, (selected, indicators) in reduced_feature_sets().items():
        for fold_number in range(1, config.cv_folds + 1):
            pipe, frame = fold_eval("Random Forest", feature_name, fold_number,
                                    rf, selected, indicators)
            transformed_counts.setdefault(
                feature_name, len(pipe.named_steps["preprocessing"].get_feature_names_out()))
            ablation_folds.append({"feature_set": feature_name, "fold": fold_number,
                                   "feature_count": len(selected),
                                   "transformed_feature_count": transformed_counts[feature_name],
                                   **error_summary(frame)})
    ablation_fold_table = pd.DataFrame(ablation_folds)
    ablation_summary = ablation_fold_table.groupby(
        ["feature_set", "feature_count", "transformed_feature_count"], sort=False).agg(
        cv_mae_mean=("mae", "mean"), cv_mae_sd=("mae", "std"),
        cv_rmse_mean=("rmse", "mean"), cv_rmse_sd=("rmse", "std"),
        cv_r2_mean=("r2", "mean"), cv_r2_sd=("r2", "std")).reset_index()
    _save_csv(output, "reduced_ablation_folds", ablation_fold_table)
    _save_csv(output, "reduced_ablation_summary", ablation_summary)

    # D. Permutation importance over those same full-feature fold models.
    importance_rows = []
    for fold_number, (_, validation) in enumerate(folds, 1):
        pipe, _ = fold_eval("Random Forest", "Full", fold_number, rf, features, True)
        sample = data.iloc[validation].sample(
            n=min(config.permutation_rows, len(validation)), random_state=config.seed + fold_number)
        values = permutation_importance(
            pipe, sample[features], sample[TARGET], scoring="neg_mean_absolute_error",
            n_repeats=10, random_state=config.seed + fold_number, n_jobs=1)
        ranks = pd.Series(values.importances_mean, index=features).rank(
            ascending=False, method="average")
        importance_rows.extend({"fold": fold_number, "feature": feature,
                                "mae_increase": values.importances_mean[i],
                                "permutation_sd": values.importances_std[i],
                                "rank": ranks[feature], "validation_rows_used": len(sample),
                                "permutation_repeats": 10}
                               for i, feature in enumerate(features))
    importance_folds = pd.DataFrame(importance_rows)
    importance_summary, importance_correlations = importance_aggregation(importance_folds)
    _save_csv(output, "importance_by_fold", importance_folds)
    _save_csv(output, "importance_stability", importance_summary)
    _save_csv(output, "importance_rank_correlations", importance_correlations)

    # E. Five fixed model families: grouped CV, temporal, and seed-42 secondary check.
    models = fixed_models(config)
    model_rows = []
    cv_low_rows = []
    for model_name, estimator in models.items():
        cv_frames = []
        for fold_number in range(1, config.cv_folds + 1):
            _, frame = fold_eval(model_name, "Full", fold_number,
                                 estimator, features, True)
            cv_frames.append(frame)
            model_rows.append(_model_metrics(frame, model=model_name,
                                             regime="Station-grouped CV",
                                             fold=fold_number))
        cv_low_rows.append({"model": model_name,
                            **_low_do_summary(pd.concat(cv_frames, ignore_index=True))})
        # Existing temporal definition: fit through 2018, test 2022–2024.
        temporal_train, _, temporal_test = chronological_split(
            data, config.train_end_year, config.validation_end_year)
        temporal_pipe = _fit(data, temporal_train, estimator, features, True)
        model_rows.append(_model_metrics(
            _evaluate(data, temporal_pipe, temporal_test, features),
            model=model_name, regime="Temporal holdout", fold=np.nan))
        parts42, _ = spatiotemporal_split(
            data, config.validation_end_year, config.test_fraction, 42)
        spatio_pipe = _fit(data, parts42["train"], estimator, features, True)
        model_rows.append(_model_metrics(
            _evaluate(data, spatio_pipe, parts42["test"], features),
            model=model_name, regime="Spatiotemporal seed 42", fold=np.nan))
    model_detail = pd.DataFrame(model_rows)
    cv_models = model_detail[model_detail.regime == "Station-grouped CV"].groupby(
        "model", sort=False).agg(mae=("mae", "mean"), mae_sd=("mae", "std"),
        rmse=("rmse", "mean"), r2=("r2", "mean"),
        low_do_splits_sufficient_n20=("low_do_sufficient_n20", "sum")).reset_index()
    cv_models = cv_models.merge(pd.DataFrame(cv_low_rows)[
        ["model", "low_do_n", "low_do_mae"]], on="model")
    holdout_models = model_detail[model_detail.regime != "Station-grouped CV"].copy()
    model_summary = pd.concat([
        cv_models.assign(regime="Station-grouped CV"),
        holdout_models[["model", "regime", "mae", "rmse", "r2", "low_do_n",
                        "low_do_mae", "low_do_sufficient_n20"]].rename(
                            columns={"low_do_sufficient_n20": "low_do_splits_sufficient_n20"})
    ], ignore_index=True)
    _save_csv(output, "model_family_detail", model_detail)
    _save_csv(output, "model_family_summary", model_summary)

    # F. v1 station/temporal interval evidence plus new repeated regime.
    baseline_uncertainty = pd.read_csv(v1_dir / "tables/uncertainty_results.csv").rename(
        columns={"target_coverage": "nominal_coverage"})
    baseline_coverage = []
    for regime, key in (("Station calibration", "station"),
                        ("Temporal calibration", "temporal")):
        table = pd.read_csv(v1_dir / f"tables/coverage_by_do_{key}.csv")
        table.insert(0, "regime", regime)
        baseline_coverage.append(table)
    uncertainty_summary = split_summary(
        uncertainty, ["empirical_coverage", "mean_interval_width", "radius", "point_mae"])
    uncertainty_range_summary = uncertainty_by_range.groupby("do_range", sort=False).agg(
        splits=("seed", "nunique"), mean_sample_count=("sample_count", "mean"),
        min_sample_count=("sample_count", "min"), max_sample_count=("sample_count", "max"),
        mean_coverage=("empirical_coverage", "mean"),
        sd_coverage=("empirical_coverage", "std"),
        median_coverage=("empirical_coverage", "median"),
        min_coverage=("empirical_coverage", "min"),
        max_coverage=("empirical_coverage", "max")).reset_index()
    _save_csv(output, "uncertainty_v1_reference", baseline_uncertainty)
    _save_csv(output, "uncertainty_v1_coverage_reference", pd.concat(baseline_coverage, ignore_index=True))
    _save_csv(output, "v1_validation_reference", pd.read_csv(
        v1_dir / "tables/validation_comparison.csv"))
    _save_csv(output, "repeated_spatiotemporal_uncertainty", uncertainty)
    _save_csv(output, "repeated_spatiotemporal_uncertainty_summary", uncertainty_summary)
    _save_csv(output, "repeated_spatiotemporal_coverage_by_do", uncertainty_by_range)
    _save_csv(output, "repeated_spatiotemporal_coverage_summary", uncertainty_range_summary)
    _save_gzip(output, "repeated_spatiotemporal_intervals", all_intervals)

    # G. Minimal existing-feature shift extension and descriptive relationships.
    _save_csv(output, "repeated_spatiotemporal_shift", shifts)
    shift_summary = shifts.groupby("feature", sort=False).agg(
        mean_smd=("standardized_mean_difference", "mean"),
        sd_smd=("standardized_mean_difference", "std"),
        median_smd=("standardized_mean_difference", "median"),
        min_smd=("standardized_mean_difference", "min"),
        max_smd=("standardized_mean_difference", "max")).reset_index()
    _save_csv(output, "repeated_spatiotemporal_shift_summary", shift_summary)
    seed_shift = shifts.assign(abs_smd=shifts.standardized_mean_difference.abs()).groupby("seed").agg(
        mean_absolute_smd=("abs_smd", "mean"), max_absolute_smd=("abs_smd", "max")).reset_index()
    seed_shift = seed_shift.merge(repeated[["seed", "mae", "test_low_do_fraction"]], on="seed")
    relationships = pd.DataFrame([
        {"relationship": "mean absolute SMD vs MAE",
         "spearman_r": seed_shift.mean_absolute_smd.corr(seed_shift.mae, method="spearman")},
        {"relationship": "low-DO prevalence vs MAE",
         "spearman_r": seed_shift.test_low_do_fraction.corr(seed_shift.mae, method="spearman")},
    ])
    _save_csv(output, "shift_performance_by_seed", seed_shift)
    _save_csv(output, "shift_performance_relationships", relationships)

    create_v2_figures(output, repeated, low_do, importance_summary)
    tables = {p.stem: pd.read_csv(p) for p in sorted((output / "tables").glob("*.csv"))}

    run = {
        "status": "complete", "release": "v2.0-research", "purpose": "scoped robustness analysis",
        "git_commit": _git_commit(root), "git_worktree_dirty": bool(subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=root, text=True).strip()),
        "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
        "sklearn": sklearn.__version__, "config": asdict(config), "seeds": list(V2_SEEDS),
        "dataset": {**audit, "raw_sha256": sha256(raw_path), "rows": len(data),
                    "stations": data[GROUP].nunique(), "first_date": str(data[DATE].min()),
                    "last_date": str(data[DATE].max())},
        "spatial_metadata": {"field": "PrimaryBasin", "covered_stations": len(basin_mapping),
                             "missing_stations": excluded_stations,
                             "unique_groups": basin_mapping.primary_basin.nunique()},
        "v1_manifest_sha256": v1_manifest_hash, "v1_output_hashes": v1["output_hashes"],
        "protected_hashes": before_protected, "timings": timings,
        "source_hashes": {str(p.relative_to(root)): sha256(p) for p in [
            root / "src/research_v2.py", root / "scripts/run_research_v2.py",
            root / "src/preprocessing.py", root / "src/refine.py",
            root / "src/research_analysis.py", root / "src/research_config.py"]},
        "settings": {"importance_repeats_per_fold": 10,
                     "importance_rows_per_fold": config.permutation_rows,
                     "model_families": list(models),
                     "reduced_feature_sets": {k: {"features": v[0], "missingness_indicators": v[1]}
                                              for k, v in reduced_feature_sets().items()},
                     "interval_method": "existing absolute-residual order statistic",
                     "do_ranges": list(DO_RANGES)},
    }
    report = write_v2_report(output, tables, run)
    (output / "reports/RESEARCH_RESULTS_V2.md").write_text(report)

    # v1 and all project data/model/result artifacts must be byte-identical.
    verify_hash_mapping(v1_dir, v1["output_hashes"])
    if sha256(v1_dir / "manifest.json") != v1_manifest_hash:
        raise RuntimeError("v1 manifest changed.")
    if protected_hashes(root) != before_protected:
        raise RuntimeError("Data, model, app-data, or historical result artifacts changed.")
    manifest_path = output / "manifests/v2_manifest.json"
    run["v1_outputs_unchanged"] = True
    run["protected_artifacts_unchanged"] = True
    run["output_hashes"] = {str(p.relative_to(output)): sha256(p)
                            for p in sorted(output.rglob("*"))
                            if p.is_file() and p != manifest_path}
    manifest_path.write_text(json.dumps(run, indent=2, default=str) + "\n")
    return run


def create_v2_figures(output: Path, repeated: pd.DataFrame, low_do: pd.DataFrame,
                      importance: pd.DataFrame) -> None:
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "savefig.dpi": 240})

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(output / "figures" / f"{name}.png", bbox_inches="tight")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(range(len(repeated)), repeated.mae, marker="o", color="#176B5B")
    ax.axhline(repeated.mae.mean(), linestyle="--", color="#B7791F", label="10-split mean")
    ax.set(xticks=range(len(repeated)), xticklabels=repeated.seed,
           xlabel="Predefined station-partition seed", ylabel="MAE (mg/L)",
           title="Repeated spatiotemporal holdout: split-level MAE")
    ax.legend(); save(fig, "spatiotemporal_mae_across_seeds")

    fig, axes = plt.subplots(1, 3, figsize=(10, 4))
    for ax, metric, label in zip(axes, ("mae", "rmse", "r2"),
                                 ("MAE (mg/L)", "RMSE (mg/L)", "R²")):
        ax.boxplot(repeated[metric], widths=.45, showmeans=True)
        ax.scatter(np.ones(len(repeated)), repeated[metric], alpha=.7, s=20, color="#176B5B")
        ax.set(xticks=[], ylabel=label)
    fig.suptitle("Across-split validation metrics (10 predefined seeds)")
    save(fig, "spatiotemporal_metric_distributions")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.scatter(repeated.test_low_do_fraction * 100, repeated.mae, color="#176B5B")
    for row in repeated.itertuples():
        ax.annotate(str(row.seed), (row.test_low_do_fraction * 100, row.mae),
                    xytext=(4, 3), textcoords="offset points", fontsize=8)
    ax.set(xlabel="Test observations below 4 mg/L (%)", ylabel="MAE (mg/L)",
           title="Split MAE and low-DO prevalence (descriptive)")
    save(fig, "spatiotemporal_mae_vs_low_do")

    shown = importance.head(12).sort_values("mean_rank", ascending=False)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.errorbar(shown.mean_rank, shown.feature, xerr=shown.rank_sd, fmt="o",
                color="#176B5B", ecolor="#749AB6", capsize=3)
    ax.invert_xaxis()
    ax.set(xlabel="Mean rank ± across-fold SD (lower rank is stronger)",
           title="Permutation-importance rank stability across grouped folds")
    save(fig, "importance_stability")


def write_v2_report(output: Path, tables: dict[str, pd.DataFrame], manifest: dict) -> str:
    t = tables
    summary = t["repeated_spatiotemporal_summary"].set_index("metric")
    low = t["repeated_spatiotemporal_low_do"]
    low_summary = t["repeated_spatiotemporal_low_do_summary"].set_index("metric")
    spatial = t["spatial_basin_validation"].iloc[0]
    importance = t["importance_stability"]
    corr = t["importance_rank_correlations"]
    ablation = t["reduced_ablation_summary"]
    models = t["model_family_summary"]
    uncertainty = t["repeated_spatiotemporal_uncertainty_summary"].set_index("metric")
    coverage = t["repeated_spatiotemporal_coverage_summary"]
    base_uncertainty = t["uncertainty_v1_reference"]
    base_coverage = t["uncertainty_v1_coverage_reference"]
    relationships = t["shift_performance_relationships"]

    def stat(metric, field):
        return summary.loc[metric, field]

    seed42 = t["repeated_spatiotemporal_results"].set_index("seed").loc[42]
    lines = ["# WaterSense AI — Research Results v2.0", "",
             "**Scoped robustness analysis; the v1.0 production model and evidence remain unchanged.**", "",
             "## 1. Purpose of v2.0", "",
             "v2.0 closes six predefined methodological gaps: repeated spatiotemporal evaluation, one existing-metadata "
             "river-basin holdout, grouped-fold permutation-importance stability, a five-configuration reduced ablation, "
             "a five-family fixed-model comparison, and empirical residual-interval evaluation across regimes. "
             "No test-set tuning, production-model replacement, new targets, external data or new uncertainty method was used.", "",
             "**Retrospective limitation:** the original model and feature choices were selected retrospectively using "
             "earlier grouped experiments spanning the historical dataset. v2.0 is a robustness analysis and does not "
             "convert that earlier process into prospective validation.", "",
             "## 2. v1.0 Baseline", "",
             markdown_table(t["v1_validation_reference"][[
                 "strategy", "mae", "rmse", "r2", "test_rows", "test_stations"]]), "",
             "All v1.0 output hashes were verified before and after v2.0; v2 writes only to `research_outputs_v2/`.", "",
             "## 3. Repeated Spatiotemporal Validation", "",
             "Exactly 10 station partitions use seeds 11, 23, 42, 57, 71, 89, 101, 123, 149 and 173. "
             "Eligibility and the 2021/2022 boundary are unchanged from v1.0. Each model trains on historical rows "
             "from non-held-out stations and tests future rows from held-out stations; station overlap is zero and "
             "preprocessing is training-only.", "",
             markdown_table(t["repeated_spatiotemporal_results"][[
                 "seed", "mae", "rmse", "r2", "median_absolute_error", "p90_absolute_error",
                 "p95_absolute_error", "train_rows", "test_rows", "train_stations", "test_stations",
                 "test_target_mean", "test_target_median", "test_low_do_fraction"]]), "",
             markdown_table(t["repeated_spatiotemporal_summary"]), "",
             f"MAE across splits: mean {stat('mae','mean'):.4f}, SD {stat('mae','std'):.4f}, median "
             f"{stat('mae','median'):.4f}, IQR {stat('mae','iqr'):.4f}, range "
             f"{stat('mae','minimum'):.4f}–{stat('mae','maximum'):.4f} mg/L. "
             f"Seed 42 is {seed42.mae:.4f} mg/L, directly reproducing the v1.0 partition; it was not selected as best.", "",
             "![MAE across seeds](../figures/spatiotemporal_mae_across_seeds.png)", "",
             "![Metric distributions](../figures/spatiotemporal_metric_distributions.png)", "",
             "![MAE versus low-DO prevalence](../figures/spatiotemporal_mae_vs_low_do.png)", "",
             "## 4. Low-DO Reliability", "",
             markdown_table(low), "",
             f"Every split contained low-DO observations (n range {int(low.low_do_n.min())}–{int(low.low_do_n.max())}). "
             f"Split-level low-DO MAE averaged {low_summary.loc['low_do_mae','mean']:.4f} mg/L "
             f"(SD {low_summary.loc['low_do_mae','std']:.4f}; range "
             f"{low_summary.loc['low_do_mae','minimum']:.4f}–{low_summary.loc['low_do_mae','maximum']:.4f}). "
             f"Overprediction occurred for {int((low.low_do_overpredicted_fraction == 1).sum())} of 10 splits "
             "at 100% of their low-DO observations. Repeated appearances support a persistent warning under these "
             "partitions, not a universal bias claim. Split summaries are not pooled as independent observations.", "",
             "## 5. Spatial / Hydrological Validation", "",
             f"`PrimaryBasin` was present for {manifest['spatial_metadata']['covered_stations']} of "
             f"{manifest['dataset']['processed_stations']} modelling stations across "
             f"{manifest['spatial_metadata']['unique_groups']} consistent basin labels. Six stations lacking a label "
             "were excluded only from this experiment. A seed-42 80/20 group split held out entire named basins; "
             "both basin and station overlap are zero.", "",
             markdown_table(t["spatial_basin_validation"][[
                 "strategy", "mae", "rmse", "r2", "train_rows", "test_rows",
                 "train_stations", "test_stations", "train_basins", "test_basins",
                 "basin_overlap", "station_overlap", "excluded_missing_basin_stations",
                 "low_do_n", "low_do_mae"]]), "",
             "PrimaryBasin is stricter than station separation but remains an administrative/source field, not proof "
             "of hydrological independence; basin size and sample counts are unequal.", "",
             "## 6. Feature-Importance Stability", "",
             "Permutation importance uses the existing five station-grouped folds and 10 repeats per fold on up to "
             "5,000 validation rows. Mean within-fold permutation SD describes shuffle randomness; across-fold SD and "
             "rank SD describe fold variation. Importance is predictive association, not causation.", "",
             markdown_table(importance.head(12)), "",
             f"Mean pairwise Spearman rank correlation across the 10 fold pairs is {corr.spearman_r.mean():.4f} "
             f"(range {corr.spearman_r.min():.4f}–{corr.spearman_r.max():.4f}).", "",
             "![Importance stability](../figures/importance_stability.png)", "",
             "## 7. Reduced Feature Ablation", "",
             markdown_table(ablation), "",
             "These five cumulative configurations use identical grouped folds and fixed Random Forest settings. "
             "Differences indicate predictive contribution under this design, not causal environmental effects.", "",
             "## 8. Model-Family Comparison", "",
             markdown_table(models), "",
             "DummyRegressor, Ridge, Random Forest, Extra Trees and HistGradientBoosting use fixed settings. "
             "The temporal and seed-42 spatiotemporal checks are secondary; no result changes the deployed model. "
             "Low-DO MAE is interpreted only where n≥20; the seed-42 low-DO subgroup has n=14 for every model.", "",
             "## 9. Empirical Uncertainty Across Regimes", "",
             "The unchanged absolute-residual interval method targets 90% marginal coverage. Station and temporal "
             "values below are checksum-verified v1.0 results; repeated spatiotemporal intervals use a separate "
             "training-side station calibration split for each seed.", "",
             markdown_table(base_uncertainty), "", markdown_table(base_coverage), "",
             markdown_table(t["repeated_spatiotemporal_uncertainty"]), "",
             markdown_table(coverage), "",
             f"Repeated-spatiotemporal empirical coverage averaged "
             f"{uncertainty.loc['empirical_coverage','mean']:.2%} with mean width "
             f"{uncertainty.loc['mean_interval_width','mean']:.3f} mg/L. These are empirical residual intervals, "
             "not conformal guarantees. Repeated measurements and spatial/temporal shift may violate exchangeability.", "",
             "## 10. Distribution Shift", "",
             "The existing six top features use the same pooled-SD standardized mean difference and median/IQR "
             "summaries across all 10 train/test pairs. No new shift framework or statistical test was introduced.", "",
             markdown_table(t["repeated_spatiotemporal_shift_summary"]), "",
             markdown_table(relationships), "",
             "These 10-point Spearman associations are descriptive only. Shift and low-DO prevalence do not establish "
             "causes of split-level error.", "",
             "## 11. Remaining Limitations", "",
             "- v2.0 is retrospective robustness analysis, not prospective validation.\n"
             "- Repeated partitions reuse observations; the 10 scores are not independent external tests.\n"
             "- Continuing-station eligibility excludes newly appearing future stations and can create selection effects.\n"
             "- PrimaryBasin grouping is not proof of geographic distance or hydrological independence.\n"
             "- Six stations lack basin labels; basin groups and station sampling are unequal.\n"
             "- Low-DO observations remain sparse in individual splits, and metrics are observation-weighted.\n"
             "- Feature importance can vary with correlated predictors and does not identify causes.\n"
             "- Water temperature, flow and catchment characteristics are absent from model inputs.\n"
             "- Empirical interval coverage is distribution-dependent and lacks finite-sample guarantees under shift.\n"
             "- Evidence remains specific to Northern Ireland and does not replace direct measurement.", "",
             "## 12. Conclusion", "",
             f"Repeated spatiotemporal MAE varied from {stat('mae','minimum'):.4f} to "
             f"{stat('mae','maximum'):.4f} mg/L, replacing reliance on one favorable or unfavorable partition. "
             "The nonlinear tree/boosting families and reduced ablation clarify which conclusions persist under fixed "
             "alternatives, while importance ranks show measurable fold variation. Low-DO point errors and interval "
             "coverage remain the central reliability weakness. Aggregate metrics do not establish uniform reliability.", "",
             "## 13. Reproducibility", "",
             "From the repository root, run:", "",
             "```bash\npython scripts/run_research_v2.py --output research_outputs_v2\n"
             "python -m unittest discover -s tests -v\n```", "",
             "The v2 manifest records the commit, source/data/v1 hashes, package versions, exact seeds, settings and "
             "output hashes. The runner refuses a non-empty destination.", ""]
    return "\n".join(lines)
