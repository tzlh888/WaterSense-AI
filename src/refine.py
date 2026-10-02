"""Phase 4 group-aware refinement and explainability experiment.

All feature and parameter decisions use only the Phase 3 training stations. The
unchanged station-grouped holdout is evaluated only after model selection.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.inspection import PartialDependenceDisplay, permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline

try:
    from .evaluate import evaluate_regression
    from .preprocessing import (
        WATER_QUALITY_FEATURE_SETS,
        WATER_QUALITY_GROUP,
        WATER_QUALITY_TARGET,
        build_water_quality_feature_preprocessor,
        grouped_station_holdout,
        load_data,
        temporal_sensitivity_holdout,
    )
except ImportError:  # pragma: no cover - supports direct script execution
    from evaluate import evaluate_regression
    from preprocessing import (
        WATER_QUALITY_FEATURE_SETS,
        WATER_QUALITY_GROUP,
        WATER_QUALITY_TARGET,
        build_water_quality_feature_preprocessor,
        grouped_station_holdout,
        load_data,
        temporal_sensitivity_holdout,
    )


RANDOM_STATE = 42
N_GROUP_FOLDS = 5


def phase4_pipeline(feature_columns: list[str], estimator: Any) -> Pipeline:
    """Return a fresh leakage-safe pipeline for one candidate."""
    return Pipeline(
        [
            ("preprocessing", build_water_quality_feature_preprocessor(feature_columns)),
            ("model", estimator),
        ]
    )


def fixed_phase3_split(data: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Recreate and verify the sealed Phase 3 station-grouped holdout."""
    train_indices, test_indices = grouped_station_holdout(
        data, test_size=0.2, random_state=RANDOM_STATE
    )
    train_stations = set(data.iloc[train_indices][WATER_QUALITY_GROUP])
    test_stations = set(data.iloc[test_indices][WATER_QUALITY_GROUP])
    assert train_stations.isdisjoint(test_stations)
    assert (len(train_indices), len(test_indices)) == (119_690, 31_341)
    assert (len(train_stations), len(test_stations)) == (672, 168)
    return train_indices, test_indices


def group_fold_indices(
    data: pd.DataFrame, training_indices: np.ndarray, n_splits: int = N_GROUP_FOLDS
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Return absolute row indices for non-overlapping station folds."""
    training = data.iloc[training_indices]
    splitter = GroupKFold(n_splits=n_splits)
    folds: list[tuple[np.ndarray, np.ndarray]] = []
    for fold_train, fold_validation in splitter.split(
        training, groups=training[WATER_QUALITY_GROUP]
    ):
        absolute_train = training_indices[fold_train]
        absolute_validation = training_indices[fold_validation]
        train_stations = set(data.iloc[absolute_train][WATER_QUALITY_GROUP])
        validation_stations = set(data.iloc[absolute_validation][WATER_QUALITY_GROUP])
        assert train_stations.isdisjoint(validation_stations)
        folds.append((absolute_train, absolute_validation))
    return folds


def cross_validate_grouped(
    data: pd.DataFrame,
    folds: list[tuple[np.ndarray, np.ndarray]],
    feature_columns: list[str],
    estimator: Any,
    *,
    model_name: str,
    feature_set_name: str,
    collect_predictions: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """Evaluate one pipeline with group folds and optional OOF predictions."""
    rows: list[dict[str, Any]] = []
    prediction_rows: list[pd.DataFrame] = []
    for fold_number, (fold_train, fold_validation) in enumerate(folds, start=1):
        pipeline = phase4_pipeline(feature_columns, clone(estimator))
        X_train = data.iloc[fold_train][feature_columns]
        X_validation = data.iloc[fold_validation][feature_columns]
        y_train = data.iloc[fold_train][WATER_QUALITY_TARGET]
        y_validation = data.iloc[fold_validation][WATER_QUALITY_TARGET]
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_validation)
        metrics = evaluate_regression(y_validation, predictions)
        rows.append(
            {
                "record_type": "fold",
                "model": model_name,
                "feature_set": feature_set_name,
                "fold": fold_number,
                "mae": metrics["mae"],
                "rmse": metrics["rmse"],
                "r2": metrics["r2"],
                "train_rows": len(fold_train),
                "validation_rows": len(fold_validation),
                "train_stations": data.iloc[fold_train][WATER_QUALITY_GROUP].nunique(),
                "validation_stations": data.iloc[fold_validation][WATER_QUALITY_GROUP].nunique(),
            }
        )
        if collect_predictions:
            fold_errors = data.iloc[fold_validation][
                ["source_object_id", WATER_QUALITY_GROUP]
            ].copy()
            fold_errors["fold"] = fold_number
            fold_errors["actual_do_mg_l"] = y_validation.to_numpy()
            fold_errors["predicted_do_mg_l"] = predictions
            fold_errors["absolute_error_mg_l"] = np.abs(
                fold_errors["actual_do_mg_l"] - fold_errors["predicted_do_mg_l"]
            )
            prediction_rows.append(fold_errors)

    fold_results = pd.DataFrame(rows)
    summaries: list[dict[str, Any]] = []
    for statistic in ["mean", "std", "min", "max"]:
        metric_values = getattr(fold_results[["mae", "rmse", "r2"]], statistic)()
        summaries.append(
            {
                "record_type": statistic,
                "model": model_name,
                "feature_set": feature_set_name,
                "fold": pd.NA,
                "mae": metric_values["mae"],
                "rmse": metric_values["rmse"],
                "r2": metric_values["r2"],
                "train_rows": pd.NA,
                "validation_rows": pd.NA,
                "train_stations": pd.NA,
                "validation_stations": pd.NA,
            }
        )
    full_results = pd.concat([fold_results, pd.DataFrame(summaries)], ignore_index=True)
    predictions = (
        pd.concat(prediction_rows, ignore_index=True) if prediction_rows else None
    )
    return full_results, predictions


def _cv_summary(cv_results: pd.DataFrame) -> dict[str, float]:
    folds = cv_results[cv_results["record_type"] == "fold"]
    return {
        "cv_mae_mean": float(folds["mae"].mean()),
        "cv_mae_std": float(folds["mae"].std()),
        "cv_rmse_mean": float(folds["rmse"].mean()),
        "cv_r2_mean": float(folds["r2"].mean()),
    }


def _tail_error_table(errors: pd.DataFrame) -> pd.DataFrame:
    actual = errors["actual_do_mg_l"]
    quantiles = actual.quantile([0.05, 0.10, 0.25, 0.75, 0.90, 0.95])
    ranges = {
        "lowest_5_percent": actual <= quantiles.loc[0.05],
        "lowest_10_percent": actual <= quantiles.loc[0.10],
        "10_to_25_percent": (actual > quantiles.loc[0.10]) & (actual <= quantiles.loc[0.25]),
        "25_to_75_percent": (actual > quantiles.loc[0.25]) & (actual < quantiles.loc[0.75]),
        "75_to_90_percent": (actual >= quantiles.loc[0.75]) & (actual < quantiles.loc[0.90]),
        "highest_10_percent": actual >= quantiles.loc[0.90],
        "highest_5_percent": actual >= quantiles.loc[0.95],
        "overall": pd.Series(True, index=errors.index),
    }
    rows = []
    for name, mask in ranges.items():
        subset = errors.loc[mask]
        residual = subset["residual_mg_l"]
        metrics = evaluate_regression(
            subset["actual_do_mg_l"], subset["predicted_do_mg_l"]
        )
        rows.append(
            {
                "range": name,
                "rows": len(subset),
                "minimum_actual_do_mg_l": subset["actual_do_mg_l"].min(),
                "maximum_actual_do_mg_l": subset["actual_do_mg_l"].max(),
                "mae_mg_l": metrics["mae"],
                "rmse_mg_l": metrics["rmse"],
                "mean_residual_mg_l": residual.mean(),
                "median_residual_mg_l": residual.median(),
                "percent_overpredicted": float((residual < 0).mean() * 100),
                "percent_underpredicted": float((residual > 0).mean() * 100),
            }
        )
    return pd.DataFrame(rows)


def _save_phase4_figures(
    group_summary: pd.DataFrame,
    feature_comparison: pd.DataFrame,
    errors: pd.DataFrame,
    tail_errors: pd.DataFrame,
    bins: pd.DataFrame,
    importance: pd.DataFrame,
    monthly: pd.DataFrame,
    figure_dir: Path,
) -> None:
    figure_dir.mkdir(parents=True, exist_ok=True)

    def save_bar(data: pd.DataFrame, x: str, y: str, error: str | None, title: str, ylabel: str, filename: str) -> None:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(data[x], data[y], yerr=data[error] if error else None, capsize=4)
        ax.set(title=title, ylabel=ylabel, xlabel="")
        ax.tick_params(axis="x", rotation=20)
        ax.grid(axis="y", alpha=0.2)
        fig.tight_layout()
        fig.savefig(figure_dir / filename, dpi=160)
        plt.close(fig)

    save_bar(group_summary, "model", "cv_mae_mean", "cv_mae_std", "Group-CV model comparison", "MAE (mg/L)", "phase4_cv_model_comparison.png")
    save_bar(feature_comparison, "feature_set", "cv_mae_mean", "cv_mae_std", "Feature-set comparison", "Group-CV MAE (mg/L)", "phase4_feature_set_comparison.png")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(errors["actual_do_mg_l"], errors["predicted_do_mg_l"], s=8, alpha=0.2)
    bounds = [min(errors["actual_do_mg_l"].min(), errors["predicted_do_mg_l"].min()), max(errors["actual_do_mg_l"].max(), errors["predicted_do_mg_l"].max())]
    ax.plot(bounds, bounds, "--", color="black", linewidth=1)
    ax.set(title="Phase 4 actual vs predicted — untouched station holdout", xlabel="Actual dissolved oxygen (mg/L)", ylabel="Predicted dissolved oxygen (mg/L)")
    ax.grid(alpha=0.2)
    fig.tight_layout(); fig.savefig(figure_dir / "phase4_actual_vs_predicted.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(errors["residual_mg_l"], bins=80)
    ax.axvline(0, linestyle="--", color="black", linewidth=1)
    ax.set(title="Phase 4 residual distribution", xlabel="Residual: actual − predicted (mg/L)", ylabel="Observations")
    fig.tight_layout(); fig.savefig(figure_dir / "phase4_residual_distribution.png", dpi=160); plt.close(fig)

    plot_tail = tail_errors[tail_errors["range"] != "overall"]
    save_bar(plot_tail, "range", "mae_mg_l", None, "Error across dissolved-oxygen ranges", "MAE (mg/L)", "phase4_error_by_do_range.png")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(bins["mean_actual_do_mg_l"], bins["mean_predicted_do_mg_l"], marker="o")
    lower = min(bins["mean_actual_do_mg_l"].min(), bins["mean_predicted_do_mg_l"].min())
    upper = max(bins["mean_actual_do_mg_l"].max(), bins["mean_predicted_do_mg_l"].max())
    ax.plot([lower, upper], [lower, upper], "--", color="black", linewidth=1)
    ax.set(title="Prediction compression by actual-DO decile", xlabel="Mean actual dissolved oxygen (mg/L)", ylabel="Mean predicted dissolved oxygen (mg/L)")
    ax.grid(alpha=0.2)
    fig.tight_layout(); fig.savefig(figure_dir / "phase4_prediction_compression.png", dpi=160); plt.close(fig)

    top_importance = importance.head(15).sort_values("mae_increase_mean")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(top_importance["input_feature"], top_importance["mae_increase_mean"], xerr=top_importance["mae_increase_std"], capsize=3)
    ax.set(title="Held-out permutation importance", xlabel="Increase in MAE after permutation (mg/L)", ylabel="Input feature")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout(); fig.savefig(figure_dir / "phase4_permutation_importance.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(monthly["sample_month"], monthly["mae_mg_l"], marker="o")
    ax.set(title="Holdout error by sampling month", xlabel="Month", ylabel="MAE (mg/L)", xticks=range(1, 13))
    ax.grid(alpha=0.2)
    fig.tight_layout(); fig.savefig(figure_dir / "phase4_monthly_error.png", dpi=160); plt.close(fig)


def run_phase4_experiment(
    data: pd.DataFrame,
    results_dir: str | Path = "results",
    model_dir: str | Path = "models",
) -> dict[str, Any]:
    """Execute Phase 4 while preserving the fixed test set until selection."""
    results = Path(results_dir)
    figures = results / "figures"
    models = Path(model_dir)
    results.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    models.mkdir(parents=True, exist_ok=True)

    required = {WATER_QUALITY_TARGET, WATER_QUALITY_GROUP, "source_object_id", "sample_date", "sample_year", "sample_month", "season"}
    required.update(column for columns in WATER_QUALITY_FEATURE_SETS.values() for column in columns)
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Processed data is missing Phase 4 columns: {missing}")

    phase3_train, sealed_test = fixed_phase3_split(data)
    sealed_test_stations = set(data.iloc[sealed_test][WATER_QUALITY_GROUP])
    folds = group_fold_indices(data, phase3_train)
    assert all(
        sealed_test_stations.isdisjoint(set(data.iloc[train][WATER_QUALITY_GROUP]))
        and sealed_test_stations.isdisjoint(set(data.iloc[validation][WATER_QUALITY_GROUP]))
        for train, validation in folds
    )

    core_features = WATER_QUALITY_FEATURE_SETS["A_core_chemistry"]
    candidates = {
        "Dummy Mean": DummyRegressor(strategy="mean"),
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1),
        "HistGradientBoosting": HistGradientBoostingRegressor(random_state=RANDOM_STATE),
    }
    all_group_cv = []
    group_summaries = []
    for name, estimator in candidates.items():
        cv, _ = cross_validate_grouped(data, folds, core_features, estimator, model_name=name, feature_set_name="A_core_chemistry")
        all_group_cv.append(cv)
        group_summaries.append({"model": name, **_cv_summary(cv)})
    group_cv_results = pd.concat(all_group_cv, ignore_index=True)
    group_cv_results.to_csv(results / "group_cv_results.csv", index=False)
    group_summary = pd.DataFrame(group_summaries).sort_values("cv_mae_mean").reset_index(drop=True)

    comparison_model_name = str(group_summary.iloc[0]["model"])
    comparison_estimator = candidates[comparison_model_name]
    feature_rows = []
    feature_cv_cache: dict[str, pd.DataFrame] = {}
    for feature_set_name, feature_columns in WATER_QUALITY_FEATURE_SETS.items():
        if feature_set_name == "A_core_chemistry":
            cv = group_cv_results[(group_cv_results["model"] == comparison_model_name) & (group_cv_results["feature_set"] == feature_set_name)].copy()
        else:
            cv, _ = cross_validate_grouped(data, folds, feature_columns, comparison_estimator, model_name=comparison_model_name, feature_set_name=feature_set_name)
        feature_cv_cache[feature_set_name] = cv
        feature_rows.append({"feature_set": feature_set_name, "number_of_predictors": len(feature_columns), "comparison_model": comparison_model_name, **_cv_summary(cv)})
    feature_comparison = pd.DataFrame(feature_rows).sort_values("cv_mae_mean").reset_index(drop=True)
    feature_comparison.to_csv(results / "feature_set_comparison.csv", index=False)
    selected_feature_set = str(feature_comparison.iloc[0]["feature_set"])
    selected_features = WATER_QUALITY_FEATURE_SETS[selected_feature_set]

    tuning_candidates: list[tuple[str, str, dict[str, Any], Any]] = [
        ("Random Forest", "rf_phase3", {"n_estimators": 100, "max_depth": None, "min_samples_leaf": 1, "max_features": 1.0}, RandomForestRegressor(n_estimators=100, max_depth=None, min_samples_leaf=1, max_features=1.0, random_state=RANDOM_STATE, n_jobs=-1)),
        ("Random Forest", "rf_leaf2", {"n_estimators": 150, "max_depth": None, "min_samples_leaf": 2, "max_features": 0.8}, RandomForestRegressor(n_estimators=150, max_depth=None, min_samples_leaf=2, max_features=0.8, random_state=RANDOM_STATE, n_jobs=-1)),
        ("Random Forest", "rf_depth20_leaf4", {"n_estimators": 150, "max_depth": 20, "min_samples_leaf": 4, "max_features": 0.8}, RandomForestRegressor(n_estimators=150, max_depth=20, min_samples_leaf=4, max_features=0.8, random_state=RANDOM_STATE, n_jobs=-1)),
        ("HistGradientBoosting", "hgb_baseline", {"learning_rate": 0.1, "max_iter": 100, "max_leaf_nodes": 31, "l2_regularization": 0.0}, HistGradientBoostingRegressor(learning_rate=0.1, max_iter=100, max_leaf_nodes=31, l2_regularization=0.0, random_state=RANDOM_STATE)),
        ("HistGradientBoosting", "hgb_slow", {"learning_rate": 0.05, "max_iter": 200, "max_leaf_nodes": 31, "l2_regularization": 0.1}, HistGradientBoostingRegressor(learning_rate=0.05, max_iter=200, max_leaf_nodes=31, l2_regularization=0.1, random_state=RANDOM_STATE)),
        ("HistGradientBoosting", "hgb_regularized", {"learning_rate": 0.05, "max_iter": 200, "max_leaf_nodes": 15, "l2_regularization": 1.0}, HistGradientBoostingRegressor(learning_rate=0.05, max_iter=200, max_leaf_nodes=15, l2_regularization=1.0, random_state=RANDOM_STATE)),
        ("HistGradientBoosting", "hgb_compact", {"learning_rate": 0.1, "max_iter": 150, "max_leaf_nodes": 15, "l2_regularization": 0.1}, HistGradientBoostingRegressor(learning_rate=0.1, max_iter=150, max_leaf_nodes=15, l2_regularization=0.1, random_state=RANDOM_STATE)),
    ]
    tuning_rows = []
    candidate_objects: dict[str, Any] = {}
    for family, candidate_id, params, estimator in tuning_candidates:
        cv, _ = cross_validate_grouped(data, folds, selected_features, estimator, model_name=candidate_id, feature_set_name=selected_feature_set)
        candidate_objects[candidate_id] = estimator
        tuning_rows.append({"model_family": family, "candidate_id": candidate_id, "feature_set": selected_feature_set, "parameters": json.dumps(params, sort_keys=True), **_cv_summary(cv)})
    tuning_results = pd.DataFrame(tuning_rows).sort_values("cv_mae_mean").reset_index(drop=True)
    tuning_results.to_csv(results / "model_tuning_results.csv", index=False)

    selected_id = str(tuning_results.iloc[0]["candidate_id"])
    selected_family = str(tuning_results.iloc[0]["model_family"])
    selected_parameters = json.loads(str(tuning_results.iloc[0]["parameters"]))
    selected_estimator = candidate_objects[selected_id]

    # Only now is the sealed holdout accessed for Phase 4 evaluation.
    final_pipeline = phase4_pipeline(selected_features, clone(selected_estimator))
    final_pipeline.fit(data.iloc[phase3_train][selected_features], data.iloc[phase3_train][WATER_QUALITY_TARGET])
    holdout_predictions = final_pipeline.predict(data.iloc[sealed_test][selected_features])
    holdout_actual = data.iloc[sealed_test][WATER_QUALITY_TARGET]
    holdout_metrics = evaluate_regression(holdout_actual, holdout_predictions)
    artifact = {
        "pipeline": final_pipeline,
        "task": "regression",
        "target_column": WATER_QUALITY_TARGET,
        "feature_columns": selected_features,
        "feature_set": selected_feature_set,
        "model_name": selected_family,
        "candidate_id": selected_id,
        "parameters": selected_parameters,
        "selection_metric": "lowest mean five-fold station-grouped CV MAE on Phase 3 training stations",
        "random_state": RANDOM_STATE,
    }
    joblib.dump(artifact, models / "phase4_selected_model.joblib", compress=3)

    metadata = ["source_object_id", WATER_QUALITY_GROUP, "sample_date", "sample_year", "sample_month", "season"]
    errors = data.iloc[sealed_test][metadata + selected_features].copy().reset_index(drop=True)
    errors["actual_do_mg_l"] = holdout_actual.to_numpy()
    errors["predicted_do_mg_l"] = holdout_predictions
    errors["residual_mg_l"] = errors["actual_do_mg_l"] - errors["predicted_do_mg_l"]
    errors["absolute_error_mg_l"] = errors["residual_mg_l"].abs()
    errors.to_csv(results / "phase4_holdout_predictions.csv", index=False)

    tail_errors = _tail_error_table(errors)
    tail_errors.to_csv(results / "error_by_target_range_phase4.csv", index=False)

    station_errors = errors.groupby(WATER_QUALITY_GROUP).agg(
        sample_count=("absolute_error_mg_l", "size"),
        mae_mg_l=("absolute_error_mg_l", "mean"),
        rmse_mg_l=("residual_mg_l", lambda values: float(np.sqrt(np.mean(np.square(values))))),
        mean_residual_mg_l=("residual_mg_l", "mean"),
        mean_actual_do_mg_l=("actual_do_mg_l", "mean"),
        mean_predicted_do_mg_l=("predicted_do_mg_l", "mean"),
    ).reset_index().sort_values("mae_mg_l", ascending=False)
    station_errors.to_csv(results / "error_by_station_phase4.csv", index=False)

    def time_errors(column: str) -> pd.DataFrame:
        return errors.groupby(column).agg(
            sample_count=("absolute_error_mg_l", "size"),
            mae_mg_l=("absolute_error_mg_l", "mean"),
            mean_residual_mg_l=("residual_mg_l", "mean"),
        ).reset_index()
    yearly = time_errors("sample_year"); monthly = time_errors("sample_month"); seasonal = time_errors("season")
    yearly.to_csv(results / "error_by_year_phase4.csv", index=False)
    monthly.to_csv(results / "error_by_month_phase4.csv", index=False)
    seasonal.to_csv(results / "error_by_season_phase4.csv", index=False)

    permutation = permutation_importance(final_pipeline, data.iloc[sealed_test][selected_features], holdout_actual, scoring="neg_mean_absolute_error", n_repeats=5, random_state=RANDOM_STATE, n_jobs=-1)
    importance = pd.DataFrame({"input_feature": selected_features, "mae_increase_mean": permutation.importances_mean, "mae_increase_std": permutation.importances_std}).sort_values("mae_increase_mean", ascending=False)
    importance.to_csv(results / "permutation_importance_phase4.csv", index=False)

    errors["actual_do_decile"] = pd.qcut(errors["actual_do_mg_l"], 10, duplicates="drop")
    bins = errors.groupby("actual_do_decile", observed=True).agg(
        sample_count=("actual_do_mg_l", "size"),
        mean_actual_do_mg_l=("actual_do_mg_l", "mean"),
        mean_predicted_do_mg_l=("predicted_do_mg_l", "mean"),
        mean_residual_mg_l=("residual_mg_l", "mean"),
    ).reset_index()
    bins["actual_do_decile"] = bins["actual_do_decile"].astype(str)
    bins.to_csv(results / "do_prediction_bins.csv", index=False)

    selected_cv, cv_predictions = cross_validate_grouped(data, folds, selected_features, selected_estimator, model_name=selected_id, feature_set_name=selected_feature_set, collect_predictions=True)
    assert cv_predictions is not None
    percentiles = [0.50, 0.75, 0.90, 0.95]
    percentile_rows = [{"scope": "all_group_cv_validation_rows", "percentile": percentile, "absolute_error_mg_l": cv_predictions["absolute_error_mg_l"].quantile(percentile)} for percentile in percentiles]
    for fold_number, subset in cv_predictions.groupby("fold"):
        percentile_rows.extend({"scope": f"fold_{fold_number}", "percentile": percentile, "absolute_error_mg_l": subset["absolute_error_mg_l"].quantile(percentile)} for percentile in percentiles)
    error_percentiles = pd.DataFrame(percentile_rows)
    error_percentiles.to_csv(results / "error_percentiles.csv", index=False)

    temporal_train, temporal_test = temporal_sensitivity_holdout(data, test_start_year=2019)
    temporal_pipeline = phase4_pipeline(selected_features, clone(selected_estimator))
    temporal_pipeline.fit(data.iloc[temporal_train][selected_features], data.iloc[temporal_train][WATER_QUALITY_TARGET])
    temporal_predictions = temporal_pipeline.predict(data.iloc[temporal_test][selected_features])
    temporal_metrics = evaluate_regression(data.iloc[temporal_test][WATER_QUALITY_TARGET], temporal_predictions)
    pd.DataFrame([{ "model": selected_family, "candidate_id": selected_id, "feature_set": selected_feature_set, "train_period": "1990-2018", "test_period": "2019-2024", "train_rows": len(temporal_train), "test_rows": len(temporal_test), **temporal_metrics }]).to_csv(results / "temporal_sensitivity_phase4.csv", index=False)

    _save_phase4_figures(group_summary, feature_comparison, errors, tail_errors, bins, importance, monthly, figures)
    # Limit the display to three well-supported numeric inputs. Features with
    # substantial raw missingness can yield unhelpful empty PDP panels in some
    # scikit-learn versions even though the pipeline imputes them for prediction.
    numeric_top = [
        feature
        for feature in importance["input_feature"]
        if not feature.endswith(("_is_below_limit", "_is_above_limit"))
        and not data.iloc[sealed_test][feature].isna().any()
    ][:3]
    pd_sample = data.iloc[sealed_test][selected_features].sample(n=min(5_000, len(sealed_test)), random_state=RANDOM_STATE)
    fig, axes = plt.subplots(1, len(numeric_top), figsize=(5 * len(numeric_top), 4.5))
    PartialDependenceDisplay.from_estimator(final_pipeline, pd_sample, features=numeric_top, ax=np.atleast_1d(axes), grid_resolution=30)
    fig.suptitle("Partial dependence — selected Phase 4 model behaviour", y=1.02)
    fig.tight_layout(); fig.savefig(figures / "phase4_partial_dependence.png", dpi=160, bbox_inches="tight"); plt.close(fig)

    phase3_mae = float(pd.read_csv(results / "baseline_results.csv").query("model == 'Random Forest'")["mae"].iloc[0])
    low = tail_errors.set_index("range").loc["lowest_10_percent"]
    high = tail_errors.set_index("range").loc["highest_10_percent"]
    summary = {
        "sealed_holdout": {"train_rows": len(phase3_train), "test_rows": len(sealed_test), "train_stations": data.iloc[phase3_train][WATER_QUALITY_GROUP].nunique(), "test_stations": len(sealed_test_stations), "station_overlap": 0},
        "feature_comparison_model": comparison_model_name,
        "selected_model": selected_family,
        "selected_candidate_id": selected_id,
        "selected_parameters": selected_parameters,
        "selected_feature_set": selected_feature_set,
        "selected_features": selected_features,
        "selection_cv": _cv_summary(selected_cv),
        "holdout_metrics": holdout_metrics,
        "phase3_random_forest_mae": phase3_mae,
        "absolute_mae_improvement": phase3_mae - holdout_metrics["mae"],
        "percentage_mae_improvement": (phase3_mae - holdout_metrics["mae"]) / phase3_mae * 100,
        "lowest_10_percent": low.to_dict(),
        "highest_10_percent": high.to_dict(),
        "temporal_sensitivity": temporal_metrics,
        "top_permutation_features": importance.head(10).to_dict(orient="records"),
        "error_percentiles": error_percentiles[error_percentiles["scope"] == "all_group_cv_validation_rows"].to_dict(orient="records"),
    }
    (results / "phase4_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    summary = run_phase4_experiment(load_data("data/processed/water_quality_modeling.csv"))
    print(json.dumps(summary, indent=2))
