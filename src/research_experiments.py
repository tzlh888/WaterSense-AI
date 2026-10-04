"""Re-fit fixed models for generalisation research without replacing app artifacts."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import GroupKFold, train_test_split

from .preprocessing import grouped_station_holdout, load_niea_raw, prepare_water_quality_modeling_data
from .refine import phase4_pipeline
from .research_config import DATE, GROUP, TARGET, FEATURE_SETS, ResearchConfig
from .research_analysis import (assert_disjoint, chronological_split, distribution_summary,
                                error_summary, grouped_errors, interval_predictions,
                                label_do_ranges, residual_frame, residual_radius,
                                spatiotemporal_split, standardized_mean_difference,
                                target_distribution)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def research_pipeline(config: ResearchConfig, feature_set: str = "full"):
    """Reuse Phase 4 preprocessing; ablate indicators only when specified."""
    features, indicators = FEATURE_SETS[feature_set]
    model = RandomForestRegressor(n_estimators=config.n_estimators,
                                  min_samples_leaf=config.min_samples_leaf,
                                  max_features=config.max_features,
                                  random_state=config.seed, n_jobs=config.n_jobs)
    pipeline = phase4_pipeline(features, model)
    pipeline.set_params(preprocessing__numeric__imputer__add_indicator=indicators)
    return pipeline


class ResearchRunner:
    """In-run reuse of fitted models; each invocation writes one coherent run."""

    def __init__(self, data: pd.DataFrame, output: Path, config: ResearchConfig):
        self.data = data.reset_index(drop=True)
        self.output, self.config = Path(output), config
        for folder in ("tables", "figures", "predictions", "reports"):
            (self.output / folder).mkdir(parents=True, exist_ok=True)
        self.models, self.predictions, self.tables, self.splits = {}, {}, {}, {}
        self.fits = []
        self.group_train, self.group_test = grouped_station_holdout(
            self.data, test_size=config.test_fraction, random_state=config.seed)
        assert_disjoint(self.data, self.group_train, self.group_test, stations=True)

    def save_table(self, name: str, table: pd.DataFrame) -> pd.DataFrame:
        table.to_csv(self.output / "tables" / f"{name}.csv", index=False)
        self.tables[name] = table
        return table

    def save_predictions(self, name: str, frame: pd.DataFrame) -> None:
        frame.to_csv(self.output / "predictions" / f"{name}.csv.gz", index=False,
                     compression={"method": "gzip", "mtime": 0})
        self.predictions[name] = frame

    def record_split(self, name: str, **parts) -> None:
        self.splits[name] = {
            role: {"rows": len(indices), "stations": self.data.iloc[indices][GROUP].nunique(),
                   "first_date": str(self.data.iloc[indices][DATE].min()),
                   "last_date": str(self.data.iloc[indices][DATE].max())}
            for role, indices in parts.items()}
        records = pd.concat([self.data.iloc[indices][["source_object_id", GROUP, DATE]].assign(
            partition=role) for role, indices in parts.items()], ignore_index=True)
        records.to_csv(self.output / "predictions" / f"split_{name}.csv.gz", index=False,
                       compression={"method": "gzip", "mtime": 0})

    def fit(self, name, train, feature_set="full", *, retain=True):
        if name in self.models:
            return self.models[name]
        print(f"Fitting {name}: {len(train):,} rows / {feature_set}", flush=True)
        start = perf_counter()
        features = FEATURE_SETS[feature_set][0]
        pipeline = research_pipeline(self.config, feature_set)
        pipeline.fit(self.data.iloc[train][features], self.data.iloc[train][TARGET])
        self.fits.append({"name": name, "feature_set": feature_set,
                          "train_rows": len(train), "elapsed_seconds": perf_counter() - start})
        if retain:
            self.models[name] = pipeline
        return pipeline

    def evaluate(self, pipeline, indices, feature_set="full"):
        features = FEATURE_SETS[feature_set][0]
        return residual_frame(self.data.iloc[indices], pipeline.predict(self.data.iloc[indices][features]))

    def validation_row(self, name, train, test, frame):
        overlap = set(self.data.iloc[train][GROUP]) & set(self.data.iloc[test][GROUP])
        return {"strategy": name, **error_summary(frame), "train_rows": len(train),
                "test_rows": len(test), "train_stations": self.data.iloc[train][GROUP].nunique(),
                "test_stations": self.data.iloc[test][GROUP].nunique(),
                "station_overlap": len(overlap)}

    def grouped(self):
        if "grouped" not in self.predictions:
            self.record_split("grouped", train=self.group_train, test=self.group_test)
            pipe = self.fit("grouped", self.group_train)
            self.save_predictions("grouped", self.evaluate(pipe, self.group_test))
        return self.validation_row("Unseen stations", self.group_train, self.group_test,
                                   self.predictions["grouped"])

    def random(self):
        train, test = train_test_split(np.arange(len(self.data)), test_size=self.config.test_fraction,
                                      random_state=self.config.seed)
        assert_disjoint(self.data, train, test)
        self.record_split("random", train=train, test=test)
        pipe = self.fit("random", train, retain=False)
        frame = self.evaluate(pipe, test)
        self.save_predictions("random", frame)
        return self.validation_row("Random rows", train, test, frame)

    def temporal(self):
        train, validation, test = chronological_split(
            self.data, self.config.train_end_year, self.config.validation_end_year)
        if "temporal" not in self.predictions:
            assert_disjoint(self.data, train, validation, test)
            self.record_split("temporal", train=train, calibration=validation, test=test)
            pipe = self.fit("temporal", train)
            self.save_predictions("temporal", self.evaluate(pipe, test))
            self.save_predictions("temporal_calibration", self.evaluate(pipe, validation))
            self.save_table("temporal_target_distribution", distribution_summary(
                {"train": self.data.iloc[train], "calibration": self.data.iloc[validation],
                 "test": self.data.iloc[test]}, [TARGET]))
            self.save_table("temporal_yearly_error", grouped_errors(self.predictions["temporal"], "sample_year"))
            self.save_table("temporal_validation", pd.DataFrame([
                self.validation_row("2019–2021 calibration (not final test)", train, validation,
                                    self.predictions["temporal_calibration"])]))
        return self.validation_row("Future years", train, test, self.predictions["temporal"])

    def ablation(self):
        self.grouped()
        folds = list(GroupKFold(n_splits=self.config.cv_folds).split(
            self.group_train, groups=self.data.iloc[self.group_train][GROUP]))
        fold_rows, rows = [], []
        for name, (features, indicators) in FEATURE_SETS.items():
            cv_metrics = []
            for fold, (local_train, local_validation) in enumerate(folds, 1):
                train, validation = self.group_train[local_train], self.group_train[local_validation]
                assert_disjoint(self.data, train, validation, self.group_test, stations=True)
                if name == "core":
                    self.record_split(f"cv_{fold}", train=train, validation=validation)
                pipe = self.fit(f"cv_{name}_{fold}", train, name, retain=False)
                scores = error_summary(self.evaluate(pipe, validation, name))
                cv_metrics.append(scores["mae"])
                fold_rows.append({"feature_set": name, "fold": fold, **scores,
                                  "train_rows": len(train), "validation_rows": len(validation)})
            pipe = self.models["grouped"] if name == "full" else self.fit(
                f"ablation_{name}", self.group_train, name, retain=False)
            frame = self.evaluate(pipe, self.group_test, name)
            self.save_predictions(f"ablation_{name}", frame)
            rows.append({"feature_set": name, "number_of_features": len(features),
                         "transformed_features": len(pipe.named_steps["preprocessing"].get_feature_names_out()),
                         "missingness_indicators": indicators, **error_summary(frame),
                         "cv_mae_mean": np.mean(cv_metrics), "cv_mae_std": np.std(cv_metrics, ddof=1)})
            self.save_table("ablation_results", pd.DataFrame(rows))
        self.save_table("group_cv_results", pd.DataFrame(fold_rows))

    def spatiotemporal(self):
        parts, inventory = spatiotemporal_split(
            self.data, self.config.validation_end_year, self.config.test_fraction, self.config.seed)
        self.save_table("spatiotemporal_station_inventory", inventory)
        self.record_split("spatiotemporal", **parts)
        train, test = parts["train"], parts["test"]
        pipe = self.fit("spatiotemporal", train)
        frame = self.evaluate(pipe, test)
        self.save_predictions("spatiotemporal", frame)
        row = self.validation_row("Spatiotemporal Holdout", train, test, frame)
        row.update(seed=self.config.seed, historical_end_year=self.config.validation_end_year,
                   eligible_stations=int(inventory.eligible.sum()),
                   heldout_station_fraction=self.config.test_fraction)
        for role, indices in (("train", train), ("test", test)):
            subset = self.data.iloc[indices]
            row.update({f"{role}_first_date": subset[DATE].min(),
                        f"{role}_last_date": subset[DATE].max(),
                        f"{role}_target_mean": subset[TARGET].mean(),
                        f"{role}_target_median": subset[TARGET].median(),
                        f"{role}_low_do_fraction": subset[TARGET].lt(4).mean()})
        self.save_table("spatiotemporal_validation", pd.DataFrame([row]))
        errors = grouped_errors(label_do_ranges(frame), "do_range").set_index("do_range").reindex(
            ["<4", "4–<8", "8–<12", "≥12"])
        errors["sample_count"] = errors.sample_count.fillna(0).astype(int)
        errors["small_sample"] = errors.sample_count < self.config.minimum_station_samples
        self.save_table("spatiotemporal_error_by_do_range", errors.reset_index())
        # The existing importance ranking is descriptive only: all 25 features
        # still enter the model. Never select predictors using this new test.
        top = self.tables["feature_importance"].feature.head(6).tolist()
        summaries = distribution_summary(
            {"train": self.data.iloc[train], "test": self.data.iloc[test]}, top)
        a = summaries[summaries.partition.eq("train")].drop(columns="partition").set_index("feature")
        b = summaries[summaries.partition.eq("test")].drop(columns="partition").set_index("feature")
        shift = a.add_prefix("train_").join(b.add_prefix("test_"))
        shift["standardized_mean_difference"] = [standardized_mean_difference(
            self.data.iloc[train][f], self.data.iloc[test][f]) for f in shift.index]
        self.save_table("spatiotemporal_shift", shift.reset_index())
        return row

    def compare_target_distributions(self):
        self.save_table("validation_target_distribution", pd.DataFrame([
            {"strategy": label, **target_distribution(self.predictions[key])}
            for key, label in (("random", "Random rows"), ("grouped", "Unseen stations"),
                               ("temporal", "Future years"),
                               ("spatiotemporal", "Spatiotemporal Holdout"))]))

    def errors(self):
        self.grouped()
        frame = self.predictions["grouped"]
        self.save_table("do_range_error", grouped_errors(label_do_ranges(frame), "do_range"))
        stations = grouped_errors(frame, GROUP)
        training = self.data.iloc[self.group_train]
        tests = self.data.iloc[self.group_test].copy()
        measurements = [f for f in FEATURE_SETS["full"][0] if not f.endswith(("_limit", "_sin", "_cos"))]
        lo, hi = training[measurements].quantile(.01), training[measurements].quantile(.99)
        observed = tests[measurements].notna()
        tests["unusual_feature_fraction"] = ((tests[measurements].lt(lo) | tests[measurements].gt(hi)) & observed).sum(axis=1) / observed.sum(axis=1).replace(0, np.nan)
        tests["missing_feature_fraction"] = tests[measurements].isna().mean(axis=1)
        tests["extreme_do_fraction"] = ((tests[TARGET] < 4) | (tests[TARGET] >= 12)).astype(float)
        tests["recent_fraction"] = (tests.sample_year >= 2019).astype(float)
        context = tests.groupby(GROUP).agg(
            unusual_feature_fraction=("unusual_feature_fraction", "mean"),
            missing_feature_fraction=("missing_feature_fraction", "mean"),
            extreme_do_fraction=("extreme_do_fraction", "mean"),
            recent_fraction=("recent_fraction", "mean"),
            first_year=("sample_year", "min"), last_year=("sample_year", "max"))
        concentration = tests.groupby([GROUP, "sample_year"]).size().groupby(level=0).max() / tests.groupby(GROUP).size()
        context["largest_year_fraction"] = concentration
        stations = stations.merge(context, on=GROUP)
        stations["ranking_eligible"] = stations.sample_count >= self.config.minimum_station_samples
        self.save_table("station_error", stations)
        ranked = stations[stations.ranking_eligible].sort_values("mae")
        self.save_table("station_extremes", pd.concat([ranked.head(10).assign(rank_group="lowest MAE"),
                                                       ranked.tail(10).assign(rank_group="highest MAE")]))
        predictors = ["sample_count", "unusual_feature_fraction", "missing_feature_fraction",
                      "extreme_do_fraction", "recent_fraction", "largest_year_fraction"]
        self.save_table("station_associations", pd.DataFrame([
            {"variable": f, "spearman_r_with_mae": ranked[f].corr(ranked.mae, method="spearman"),
             "eligible_stations": len(ranked)} for f in predictors]))
        self.save_table("yearly_error", grouped_errors(frame, "sample_year"))
        self.save_table("error_summary", pd.DataFrame([error_summary(frame)]))

    def uncertainty(self):
        self.temporal()
        proper, calibration = grouped_station_holdout(self.data.iloc[self.group_train],
            test_size=self.config.calibration_fraction, random_state=self.config.seed)
        train, cal, test = self.group_train[proper], self.group_train[calibration], self.group_test
        assert_disjoint(self.data, train, cal, test, stations=True)
        self.record_split("station_calibration", train=train, calibration=cal, test=test)
        pipe = self.fit("station_calibration", train, retain=False)
        cal_frame, test_frame = self.evaluate(pipe, cal), self.evaluate(pipe, test)
        self.save_predictions("station_calibration", cal_frame)
        rows = []
        for name, calibrate, evaluate in (("Station calibration", cal_frame, test_frame),
            ("Temporal calibration", self.predictions["temporal_calibration"], self.predictions["temporal"])):
            radius = residual_radius(calibrate.residual.to_numpy(), self.config.coverage)
            intervals = interval_predictions(evaluate, radius)
            key = "station" if name.startswith("Station") else "temporal"
            self.save_predictions(f"intervals_{key}", intervals)
            rows.append({"experiment": name, "target_coverage": self.config.coverage,
                         "empirical_coverage": intervals.covered.mean(),
                         "mean_interval_width": (intervals.upper - intervals.lower).mean(),
                         "radius": radius, "calibration_rows": len(calibrate),
                         "calibration_stations": calibrate[GROUP].nunique(),
                         "test_rows": len(evaluate), "test_stations": evaluate[GROUP].nunique(),
                         "point_mae": evaluate.absolute_error.mean()})
            bins = label_do_ranges(intervals)
            self.save_table(f"coverage_by_do_{key}", bins.groupby("do_range", observed=True).agg(
                sample_count=("covered", "size"), empirical_coverage=("covered", "mean")).reset_index())
        self.save_table("uncertainty_results", pd.DataFrame(rows))

    def importance(self):
        self.grouped()
        sample = self.data.iloc[self.group_test].sample(
            n=min(self.config.permutation_rows, len(self.group_test)), random_state=self.config.seed)
        features = FEATURE_SETS["full"][0]
        print("Computing held-out permutation importance", flush=True)
        values = permutation_importance(self.models["grouped"], sample[features], sample[TARGET],
            scoring="neg_mean_absolute_error", n_repeats=self.config.permutation_repeats,
            random_state=self.config.seed, n_jobs=1)
        self.save_table("feature_importance", pd.DataFrame({"feature": features,
            "mae_increase_mean": values.importances_mean, "mae_increase_std": values.importances_std,
            "test_rows": len(sample), "repeats": self.config.permutation_repeats}).sort_values(
                "mae_increase_mean", ascending=False))

    def shift(self):
        if "feature_importance" not in self.tables:
            self.importance()
        self.temporal()
        train, _, test = chronological_split(self.data, self.config.train_end_year,
                                              self.config.validation_end_year)
        top = self.tables["feature_importance"].feature.head(6).tolist()
        parts = {"group_train": self.data.iloc[self.group_train], "group_test": self.data.iloc[self.group_test],
                 "temporal_train": self.data.iloc[train], "temporal_test": self.data.iloc[test]}
        summary = distribution_summary(parts, top)
        contrasts = []
        for feature in top:
            for prefix in ("group", "temporal"):
                a, b = parts[f"{prefix}_train"][feature], parts[f"{prefix}_test"][feature]
                contrasts.append({"comparison": prefix, "feature": feature,
                    "standardized_mean_difference": standardized_mean_difference(a, b)})
        self.save_table("distribution_shift", summary)
        self.save_table("distribution_shift_contrasts", pd.DataFrame(contrasts))


def protected_hashes(root: Path) -> dict:
    """All existing data, saved-model and historical-result files, not just joblib."""
    return {str(p.relative_to(root)): sha256(p)
            for directory in ("data/raw", "data/processed", "data/app", "models", "results")
            for p in sorted((root / directory).rglob("*")) if p.is_file()}


def verified_research(output: Path) -> dict:
    manifest = json.loads((output / "manifest.json").read_text())
    if (manifest.get("status") != "complete" or manifest.get("experiment") != "all"
            or manifest["config"]["fast"]):
        raise ValueError("Comparison requires a completed full-data research run.")
    for name, expected in manifest["output_hashes"].items():
        if sha256(output / name) != expected:
            raise ValueError(f"Stored output checksum mismatch: {name}")
    return manifest


def extend_spatiotemporal(root: Path, output: Path, config: ResearchConfig) -> ResearchRunner:
    """Fit only the new model; reuse checksum-verified original comparison evidence.

    Explicitly targeting research_outputs permits a one-time extension. Only the
    combined validation table/chart/report and manifest may change; every other
    existing output must retain its checksum. Fresh outputs remain standalone.
    """
    from types import SimpleNamespace
    from .research_reporting import create_figures, write_report

    reference = root / "research_outputs"
    baseline = verified_research(reference)
    append = output.resolve() == reference.resolve()
    if append and (config.fast or "spatiotemporal_validation" in baseline["generated_tables"]):
        raise ValueError("Cannot overwrite an existing experiment or append smoke evidence.")
    if output.exists() and any(output.iterdir()) and not append:
        raise ValueError("Output must be new or empty.")
    for key in ("seed", "test_fraction", "n_estimators", "min_samples_leaf", "max_features",
                "validation_end_year"):
        if not config.fast and getattr(config, key) != baseline["config"][key]:
            raise ValueError(f"Comparison configuration differs: {key}")
    before = protected_hashes(root)
    for name, expected in baseline["protected_hashes"].items():
        if before.get(name) != expected:
            raise ValueError(f"Protected artifact differs from baseline: {name}")
    source = {str(p.relative_to(root)): sha256(p) for p in [
        *sorted((root / "src").glob("*.py")), root / "scripts/run_research_experiments.py"]}
    for name in ("src/preprocessing.py", "src/refine.py", "src/evaluate.py"):
        if source[name] != baseline["source_hashes"][name]:
            raise ValueError(f"Scientific pipeline differs from verified baseline: {name}")
    if json.dumps(config.metadata()["feature_sets"], sort_keys=True) != json.dumps(
            baseline["config"]["feature_sets"], sort_keys=True):
        raise ValueError("Feature definitions differ from verified baseline.")
    baseline_manifest_hash = sha256(reference / "manifest.json")
    data, _ = prepare_water_quality_modeling_data(load_niea_raw(
        root / "data/raw/niea_river_water_quality_1990_2024.csv"))
    if config.fast:
        data = data.groupby("sample_year", group_keys=False).sample(
            frac=.04, random_state=config.seed).reset_index(drop=True)
    runner = ResearchRunner(data, output, config)
    names = baseline["generated_tables"] if append else ["validation_comparison", "feature_importance"]
    runner.tables = {name: pd.read_csv(reference / "tables" / f"{name}.csv", float_precision="round_trip")
                     for name in names}
    original_tables = set(runner.tables)
    for name in ("random", "grouped", "temporal"):
        runner.predictions[name] = pd.read_csv(reference / "predictions" / f"{name}.csv.gz",
                                               float_precision="round_trip")
    old = runner.tables["validation_comparison"]
    old = old[old.strategy.ne("Spatiotemporal Holdout")].copy()
    row = runner.spatiotemporal()
    runner.save_table("validation_comparison", pd.concat([old, pd.DataFrame([row])[old.columns]], ignore_index=True))
    runner.compare_target_distributions()
    create_figures(SimpleNamespace(output=output, config=config,
                                  tables={"validation_comparison": runner.tables["validation_comparison"]},
                                  predictions={}))
    extension = {"experiment": "spatiotemporal", "config": config.metadata(),
                 "baseline_manifest_sha256": baseline_manifest_hash,
                 "baseline_output_hashes": baseline["output_hashes"], "source_hashes": source,
                 "splits": runner.splits, "fits": runner.fits,
                 "python": platform.python_version(), "numpy": np.__version__,
                 "pandas": pd.__version__, "sklearn": sklearn.__version__}
    if append:
        run = dict(baseline)
        run["extensions"] = [*baseline.get("extensions", []), extension]
        run["splits"] = {**baseline["splits"], **runner.splits}
    else:
        # Imported original metrics/ranking are saved verbatim in value, with
        # their source checksums retained; no old-model fitting occurs.
        runner.save_table("feature_importance", runner.tables["feature_importance"])
        run = {**extension, "status": "complete", "dataset": baseline["dataset"],
               "executed_rows": len(data), "generated_tables": list(runner.tables)}
    run.update(protected_hashes=before, generated_tables=list(runner.tables),
               protected_artifacts_unchanged=protected_hashes(root) == before)
    if not run["protected_artifacts_unchanged"]:
        raise RuntimeError("Protected artifacts changed.")
    exported = (set(runner.tables) - original_tables) | {"validation_comparison"}
    write_report(runner, run, table_names=exported if append else None)
    if append:
        allowed = {"tables/validation_comparison.csv", "figures/validation_strategy_comparison.png",
                   "reports/validation_comparison.md", "reports/RESEARCH_RESULTS.md"}
        for name, expected in baseline["output_hashes"].items():
            if name not in allowed and sha256(output / name) != expected:
                raise RuntimeError(f"Unrelated research output changed: {name}")
    run["report_source_sha256"] = sha256(root / "src/research_reporting.py")
    run["output_hashes"] = {str(p.relative_to(output)): sha256(p) for p in sorted(output.rglob("*"))
                            if p.is_file() and p.name != "manifest.json"}
    (output / "manifest.json").write_text(json.dumps(run, indent=2, default=str) + "\n")
    return runner


def execute(root: Path, output: Path, config: ResearchConfig, experiment: str = "all") -> ResearchRunner:
    """Recompute cleaning in memory, protect legacy files, and record provenance."""
    from .research_reporting import create_figures, write_report

    if experiment == "spatiotemporal":
        return extend_spatiotemporal(root, output, config)

    raw_path = root / "data/raw/niea_river_water_quality_1990_2024.csv"
    before = protected_hashes(root)
    raw = load_niea_raw(raw_path)
    data, audit = prepare_water_quality_modeling_data(raw)
    dataset = {**audit, "raw_columns": len(raw.columns), "raw_stations": raw.StationCode.nunique(),
               "first_date": data[DATE].min(), "last_date": data[DATE].max()}
    if config.fast:
        data = data.groupby("sample_year", group_keys=False).sample(frac=.04, random_state=config.seed).reset_index(drop=True)
    runner = ResearchRunner(data, output, config)
    run = {"status": "running", "experiment": experiment, "config": config.metadata(),
           "dataset": dataset, "executed_rows": len(data),
           "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
           "sklearn": sklearn.__version__, "protected_hashes": before,
           "source_hashes": {str(p.relative_to(root)): sha256(p) for p in [
               *sorted((root / "src").glob("*.py")), root / "scripts/run_research_experiments.py"]}}
    manifest = output / "manifest.json"
    manifest.write_text(json.dumps(run, indent=2, default=str) + "\n")
    comparisons = []
    if experiment in ("all", "validation"):
        comparisons += [runner.random(), runner.grouped()]
    if experiment in ("all", "validation", "temporal", "uncertainty", "shift"):
        comparisons.append(runner.temporal())
    if comparisons:
        runner.save_table("validation_comparison", pd.DataFrame(comparisons))
    if experiment in ("all", "ablation"):
        runner.ablation()
    if experiment in ("all", "error"):
        runner.errors()
    if experiment in ("all", "uncertainty"):
        runner.uncertainty()
    if experiment in ("all", "importance", "shift"):
        runner.importance()
    if experiment in ("all", "shift"):
        runner.shift()
    if experiment == "all":
        comparisons.append(runner.spatiotemporal())
        runner.save_table("validation_comparison", pd.DataFrame(comparisons))
        runner.compare_target_distributions()
    if experiment in ("all", "validation"):
        values = runner.tables["validation_comparison"].set_index("strategy")
        random, group = values.loc["Random rows"], values.loc["Unseen stations"]
        runner.save_table("validation_differences", pd.DataFrame([{
            "group_minus_random_mae": group.mae - random.mae,
            "mae_degradation_percent": 100 * (group.mae - random.mae) / random.mae,
            "group_minus_random_r2": group.r2 - random.r2}]))
    create_figures(runner)
    run.update(status="complete", splits=runner.splits, fits=runner.fits,
               generated_tables=list(runner.tables),
               best_ablation_by_cv=(runner.tables["ablation_results"].sort_values("cv_mae_mean").iloc[0].feature_set
                                    if "ablation_results" in runner.tables else None))
    if protected_hashes(root) != before:
        raise RuntimeError("Protected artifacts changed.")
    run["protected_artifacts_unchanged"] = True
    write_report(runner, run)
    run["output_hashes"] = {str(p.relative_to(output)): sha256(p) for p in sorted(output.rglob("*"))
                            if p.is_file() and p != manifest}
    manifest.write_text(json.dumps(run, indent=2, default=str) + "\n")
    return runner
