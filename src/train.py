"""Train reproducible baseline models for an explicitly selected target."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

try:
    from .evaluate import (
        dissolved_oxygen_range_metrics,
        evaluate_classification,
        evaluate_regression,
        grouped_regression_errors,
        save_regression_diagnostic_plots,
        water_quality_error_table,
    )
    from .preprocessing import (
        TaskType,
        WATER_QUALITY_BASELINE_FEATURES,
        WATER_QUALITY_GROUP,
        WATER_QUALITY_TARGET,
        build_preprocessor,
        build_water_quality_preprocessor,
        clean_column_names,
        grouped_station_holdout,
        load_data,
        normalise_column_name,
        split_data,
        split_features_target,
        temporal_sensitivity_holdout,
    )
except ImportError:  # Allows `python src/train.py ...` from the project root.
    from evaluate import (
        dissolved_oxygen_range_metrics,
        evaluate_classification,
        evaluate_regression,
        grouped_regression_errors,
        save_regression_diagnostic_plots,
        water_quality_error_table,
    )
    from preprocessing import (
        TaskType,
        WATER_QUALITY_BASELINE_FEATURES,
        WATER_QUALITY_GROUP,
        WATER_QUALITY_TARGET,
        build_preprocessor,
        build_water_quality_preprocessor,
        clean_column_names,
        grouped_station_holdout,
        load_data,
        normalise_column_name,
        split_data,
        split_features_target,
        temporal_sensitivity_holdout,
    )

RANDOM_STATE = 42


def baseline_estimators(task: TaskType) -> dict[str, BaseEstimator]:
    """Return simple, deliberately untuned estimators for the requested task."""
    if task == "classification":
        return {
            "logistic_regression": LogisticRegression(max_iter=1_000),
            "decision_tree": DecisionTreeClassifier(random_state=RANDOM_STATE),
            "random_forest": RandomForestClassifier(
                n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1
            ),
        }
    if task == "regression":
        return {
            "dummy_regressor": DummyRegressor(strategy="mean"),
            "linear_regression": LinearRegression(),
            "decision_tree": DecisionTreeRegressor(random_state=RANDOM_STATE),
            "random_forest": RandomForestRegressor(
                n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1
            ),
        }
    raise ValueError("task must be either 'classification' or 'regression'.")


def water_quality_regressors() -> dict[str, BaseEstimator]:
    """Return the four untuned Phase 3 regression baselines."""
    return {
        "Dummy Mean": DummyRegressor(strategy="mean"),
        "Linear Regression": LinearRegression(),
        "Decision Tree": DecisionTreeRegressor(random_state=RANDOM_STATE),
        "Random Forest": RandomForestRegressor(
            n_estimators=100,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
    }


def _water_quality_pipeline(estimator: BaseEstimator) -> Pipeline:
    """Create a fresh leakage-safe preprocessing and regression pipeline."""
    return Pipeline(
        steps=[
            ("preprocessing", build_water_quality_preprocessor()),
            ("model", estimator),
        ]
    )


def _fit_water_quality_models(
    data: pd.DataFrame,
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    *,
    validation_name: str,
    model_dir: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Pipeline], dict[str, np.ndarray]]:
    """Fit all baselines for one fixed split and return executed metrics."""
    features = data[WATER_QUALITY_BASELINE_FEATURES]
    target = data[WATER_QUALITY_TARGET]
    X_train, X_test = features.iloc[train_indices], features.iloc[test_indices]
    y_train, y_test = target.iloc[train_indices], target.iloc[test_indices]

    result_rows: list[dict[str, Any]] = []
    fitted: dict[str, Pipeline] = {}
    predictions: dict[str, np.ndarray] = {}
    artifact_names = {
        "Dummy Mean": "dummy_regressor.joblib",
        "Linear Regression": "linear_regression.joblib",
        "Decision Tree": "decision_tree.joblib",
        "Random Forest": "random_forest.joblib",
    }

    for model_name, estimator in water_quality_regressors().items():
        pipeline = _water_quality_pipeline(estimator)
        pipeline.fit(X_train, y_train)
        model_predictions = pipeline.predict(X_test)
        metrics = evaluate_regression(y_test, model_predictions)
        result_rows.append(
            {
                "model": model_name,
                "mae": metrics["mae"],
                "rmse": metrics["rmse"],
                "r2": metrics["r2"],
                "validation": validation_name,
                "train_rows": int(len(train_indices)),
                "test_rows": int(len(test_indices)),
            }
        )
        fitted[model_name] = pipeline
        predictions[model_name] = model_predictions

        if model_dir is not None:
            artifact = {
                "pipeline": pipeline,
                "task": "regression",
                "target_column": WATER_QUALITY_TARGET,
                "feature_columns": WATER_QUALITY_BASELINE_FEATURES,
                "validation": validation_name,
                "random_state": RANDOM_STATE,
            }
            joblib.dump(artifact, model_dir / artifact_names[model_name])

    return pd.DataFrame(result_rows), fitted, predictions


def run_water_quality_baseline_experiment(
    data: pd.DataFrame,
    model_dir: str | Path,
    results_dir: str | Path,
    *,
    permutation_repeats: int = 5,
) -> dict[str, Any]:
    """Run the complete Phase 3 baseline and temporal sensitivity experiment."""
    required = {
        WATER_QUALITY_TARGET,
        WATER_QUALITY_GROUP,
        "source_object_id",
        "sample_date",
        "sample_year",
        *WATER_QUALITY_BASELINE_FEATURES,
    }
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Processed data is missing required columns: {missing}")
    if data[WATER_QUALITY_TARGET].isna().any():
        raise ValueError("Processed target must not contain missing values.")

    model_destination = Path(model_dir)
    result_destination = Path(results_dir)
    figure_destination = result_destination / "figures"
    model_destination.mkdir(parents=True, exist_ok=True)
    result_destination.mkdir(parents=True, exist_ok=True)

    group_train, group_test = grouped_station_holdout(
        data, test_size=0.2, random_state=RANDOM_STATE
    )
    train_stations = set(data.iloc[group_train][WATER_QUALITY_GROUP])
    test_stations = set(data.iloc[group_test][WATER_QUALITY_GROUP])
    station_overlap = sorted(train_stations & test_stations)
    assert not station_overlap, "Station overlap must be empty."

    baseline_results, fitted, predictions = _fit_water_quality_models(
        data,
        group_train,
        group_test,
        validation_name="station_grouped_holdout",
        model_dir=model_destination,
    )
    baseline_results = baseline_results.sort_values("mae").reset_index(drop=True)
    baseline_results.to_csv(result_destination / "baseline_results.csv", index=False)

    temporal_train, temporal_test = temporal_sensitivity_holdout(
        data, test_start_year=2019
    )
    temporal_results, _, _ = _fit_water_quality_models(
        data,
        temporal_train,
        temporal_test,
        validation_name="train_through_2018_test_2019_2024",
    )
    temporal_results = temporal_results.sort_values("mae").reset_index(drop=True)
    temporal_results.to_csv(
        result_destination / "temporal_sensitivity_results.csv", index=False
    )

    best_model_name = str(baseline_results.iloc[0]["model"])
    best_pipeline = fitted[best_model_name]
    best_predictions = predictions[best_model_name]
    metadata_columns = [
        "source_object_id",
        WATER_QUALITY_GROUP,
        "sample_date",
        "sample_year",
    ]
    errors = water_quality_error_table(
        data.iloc[group_test][metadata_columns],
        data.iloc[group_test][WATER_QUALITY_TARGET],
        best_predictions,
    )
    errors.to_csv(
        result_destination / "best_model_holdout_predictions.csv", index=False
    )
    errors.nlargest(100, "absolute_error_mg_l").to_csv(
        result_destination / "largest_absolute_errors.csv", index=False
    )
    range_results = dissolved_oxygen_range_metrics(errors)
    range_results.to_csv(result_destination / "error_by_do_range.csv", index=False)
    grouped_regression_errors(errors, "sample_year").sort_values("sample_year").to_csv(
        result_destination / "error_by_year.csv", index=False
    )
    grouped_regression_errors(errors, WATER_QUALITY_GROUP).to_csv(
        result_destination / "error_by_station.csv", index=False
    )
    save_regression_diagnostic_plots(errors, figure_destination)

    random_forest = fitted["Random Forest"]
    transformed_names = random_forest.named_steps[
        "preprocessing"
    ].get_feature_names_out()
    impurity = pd.DataFrame(
        {
            "transformed_feature": transformed_names,
            "impurity_importance": random_forest.named_steps[
                "model"
            ].feature_importances_,
        }
    ).sort_values("impurity_importance", ascending=False)
    impurity.to_csv(
        result_destination / "random_forest_impurity_importance.csv", index=False
    )

    permutation = permutation_importance(
        random_forest,
        data.iloc[group_test][WATER_QUALITY_BASELINE_FEATURES],
        data.iloc[group_test][WATER_QUALITY_TARGET],
        scoring="neg_mean_absolute_error",
        n_repeats=permutation_repeats,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    permutation_table = pd.DataFrame(
        {
            "input_feature": WATER_QUALITY_BASELINE_FEATURES,
            "mae_increase_mean": permutation.importances_mean,
            "mae_increase_std": permutation.importances_std,
        }
    ).sort_values("mae_increase_mean", ascending=False)
    permutation_table.to_csv(
        result_destination / "random_forest_permutation_importance.csv", index=False
    )

    split_summary = {
        "random_state": RANDOM_STATE,
        "grouped_holdout": {
            "train_rows": int(len(group_train)),
            "test_rows": int(len(group_test)),
            "train_stations": int(len(train_stations)),
            "test_stations": int(len(test_stations)),
            "station_overlap": station_overlap,
        },
        "temporal_sensitivity": {
            "train_period": "1990-2018",
            "test_period": "2019-2024",
            "train_rows": int(len(temporal_train)),
            "test_rows": int(len(temporal_test)),
        },
        "best_baseline_by_grouped_holdout_mae": best_model_name,
        "low_do_boundary_mg_l": float(
            errors["actual_do_mg_l"].quantile(0.10)
        ),
        "high_do_boundary_mg_l": float(
            errors["actual_do_mg_l"].quantile(0.90)
        ),
    }
    with (result_destination / "split_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(split_summary, handle, indent=2)

    return {
        "baseline_results": baseline_results.to_dict(orient="records"),
        "temporal_results": temporal_results.to_dict(orient="records"),
        "split_summary": split_summary,
        "error_by_do_range": range_results.to_dict(orient="records"),
        "top_permutation_features": permutation_table.head(10).to_dict(
            orient="records"
        ),
    }


def train_baselines(
    data: pd.DataFrame,
    target_column: str,
    task: TaskType,
    output_dir: str | Path,
    *,
    test_size: float = 0.2,
) -> dict[str, dict[str, Any]]:
    """Train and save baseline pipelines, returning real held-out metrics.

    The caller must choose ``target_column`` and ``task`` based on documented
    dataset meaning. This function intentionally does not invent labels or infer
    a scientific question from a column's dtype.
    """
    cleaned_data = clean_column_names(data)
    cleaned_target = target_column
    if target_column not in cleaned_data.columns:
        # Permit callers to supply the original spelling of the target name.
        cleaned_target = normalise_column_name(target_column)

    features, target = split_features_target(cleaned_data, cleaned_target)
    if task == "classification" and target.nunique() < 2:
        raise ValueError("Classification requires at least two observed target classes.")
    if task == "regression" and not pd.api.types.is_numeric_dtype(target):
        raise ValueError("Regression requires a numeric target column.")
    X_train, X_test, y_train, y_test = split_data(
        features,
        target,
        task,
        test_size=test_size,
        random_state=RANDOM_STATE,
    )

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, Any]] = {}

    for model_name, estimator in baseline_estimators(task).items():
        pipeline = Pipeline(
            steps=[
                ("preprocessing", build_preprocessor(X_train)),
                ("model", estimator),
            ]
        )
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)
        metrics = (
            evaluate_classification(y_test, predictions)
            if task == "classification"
            else evaluate_regression(y_test, predictions)
        )

        artifact = {
            "pipeline": pipeline,
            "task": task,
            "target_column": cleaned_target,
            "feature_columns": features.columns.tolist(),
            "random_state": RANDOM_STATE,
        }
        artifact_path = destination / f"{model_name}.joblib"
        joblib.dump(artifact, artifact_path)
        results[model_name] = {
            "metrics": metrics,
            "artifact_path": str(artifact_path),
            "test_observations": int(len(y_test)),
        }

    return results


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Path to a CSV dataset.")
    parser.add_argument(
        "--water-quality-baseline",
        action="store_true",
        help="Run the fixed Phase 3 dissolved-oxygen experiment.",
    )
    parser.add_argument(
        "--target",
        required=False,
        help="Scientifically justified target column; no target is inferred.",
    )
    parser.add_argument(
        "--task", required=False, choices=("classification", "regression")
    )
    parser.add_argument("--output-dir", default="models")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--test-size", type=float, default=0.2)
    return parser.parse_args()


def main() -> None:
    """Run baseline training from the command line."""
    args = parse_args()
    data = load_data(args.data)
    if args.water_quality_baseline:
        results = run_water_quality_baseline_experiment(
            data,
            model_dir=args.output_dir,
            results_dir=args.results_dir,
        )
        print(json.dumps(results, indent=2))
        return
    if args.target is None or args.task is None:
        raise SystemExit(
            "--target and --task are required unless --water-quality-baseline is used."
        )
    results = train_baselines(
        data,
        target_column=args.target,
        task=args.task,
        output_dir=args.output_dir,
        test_size=args.test_size,
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
