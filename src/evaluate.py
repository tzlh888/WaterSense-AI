"""Reusable evaluation and error-analysis helpers for baseline models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)


def evaluate_classification(
    y_true: pd.Series | np.ndarray,
    y_pred: pd.Series | np.ndarray,
) -> dict[str, Any]:
    """Calculate classification metrics without inventing a positive class.

    Macro averages give each class equal weight; weighted averages account for
    class frequency. Per-class values are retained in ``classification_report``.
    """
    labels = np.unique(np.concatenate([np.asarray(y_true), np.asarray(y_pred)]))
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(
            precision_score(y_true, y_pred, average="macro", zero_division=0)
        ),
        "recall_macro": float(
            recall_score(y_true, y_pred, average="macro", zero_division=0)
        ),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "precision_weighted": float(
            precision_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "recall_weighted": float(
            recall_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "f1_weighted": float(
            f1_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "labels": labels.tolist(),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        "classification_report": classification_report(
            y_true, y_pred, labels=labels, output_dict=True, zero_division=0
        ),
    }


def evaluate_regression(
    y_true: pd.Series | np.ndarray,
    y_pred: pd.Series | np.ndarray,
) -> dict[str, float]:
    """Calculate common regression metrics on actual predictions."""
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
    }


def classification_errors(
    features: pd.DataFrame,
    y_true: pd.Series,
    y_pred: pd.Series | np.ndarray,
) -> pd.DataFrame:
    """Return misclassified test rows with actual and predicted labels."""
    analysis = features.copy().reset_index(names="source_index")
    analysis["actual"] = y_true.reset_index(drop=True)
    analysis["predicted"] = np.asarray(y_pred)
    return analysis.loc[analysis["actual"] != analysis["predicted"]].copy()


def regression_errors(
    features: pd.DataFrame,
    y_true: pd.Series,
    y_pred: pd.Series | np.ndarray,
) -> pd.DataFrame:
    """Return test rows with signed and absolute residuals."""
    analysis = features.copy().reset_index(names="source_index")
    analysis["actual"] = y_true.reset_index(drop=True)
    analysis["predicted"] = np.asarray(y_pred)
    analysis["residual"] = analysis["actual"] - analysis["predicted"]
    analysis["absolute_error"] = analysis["residual"].abs()
    return analysis.sort_values("absolute_error", ascending=False)


def water_quality_error_table(
    metadata: pd.DataFrame,
    y_true: pd.Series | np.ndarray,
    y_pred: pd.Series | np.ndarray,
) -> pd.DataFrame:
    """Combine holdout metadata, predictions, residuals, and error direction."""
    errors = metadata.reset_index(drop=True).copy()
    errors["actual_do_mg_l"] = np.asarray(y_true)
    errors["predicted_do_mg_l"] = np.asarray(y_pred)
    errors["residual_mg_l"] = errors["actual_do_mg_l"] - errors["predicted_do_mg_l"]
    errors["absolute_error_mg_l"] = errors["residual_mg_l"].abs()
    errors["error_direction"] = np.select(
        [errors["residual_mg_l"] > 0, errors["residual_mg_l"] < 0],
        ["under_prediction", "over_prediction"],
        default="exact",
    )
    return errors


def dissolved_oxygen_range_metrics(errors: pd.DataFrame) -> pd.DataFrame:
    """Summarise errors for the lowest, middle, and highest target ranges.

    Ranges are defined from the held-out target distribution and are descriptive
    error-analysis groups, not ecological or regulatory classes.
    """
    lower = float(errors["actual_do_mg_l"].quantile(0.10))
    upper = float(errors["actual_do_mg_l"].quantile(0.90))
    range_names = np.select(
        [
            errors["actual_do_mg_l"] <= lower,
            errors["actual_do_mg_l"] >= upper,
        ],
        ["lowest_10_percent", "highest_10_percent"],
        default="middle_80_percent",
    )
    labelled = errors.assign(do_range=range_names)
    rows: list[dict[str, Any]] = []
    for range_name in ["overall", "lowest_10_percent", "middle_80_percent", "highest_10_percent"]:
        subset = labelled if range_name == "overall" else labelled[labelled["do_range"] == range_name]
        metrics = evaluate_regression(
            subset["actual_do_mg_l"], subset["predicted_do_mg_l"]
        )
        rows.append(
            {
                "range": range_name,
                "rows": int(len(subset)),
                "minimum_actual_do_mg_l": float(subset["actual_do_mg_l"].min()),
                "maximum_actual_do_mg_l": float(subset["actual_do_mg_l"].max()),
                **metrics,
            }
        )
    return pd.DataFrame(rows)


def grouped_regression_errors(errors: pd.DataFrame, group_column: str) -> pd.DataFrame:
    """Summarise absolute and signed error by a metadata column."""
    return (
        errors.groupby(group_column, dropna=False)
        .agg(
            rows=("absolute_error_mg_l", "size"),
            mae_mg_l=("absolute_error_mg_l", "mean"),
            mean_residual_mg_l=("residual_mg_l", "mean"),
            maximum_absolute_error_mg_l=("absolute_error_mg_l", "max"),
        )
        .reset_index()
        .sort_values("mae_mg_l", ascending=False)
    )


def save_regression_diagnostic_plots(
    errors: pd.DataFrame, output_dir: str | Path
) -> list[Path]:
    """Save four transparent holdout diagnostic plots and return their paths."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    specifications = [
        (
            "actual_vs_predicted.png",
            errors["actual_do_mg_l"],
            errors["predicted_do_mg_l"],
            "Actual dissolved oxygen (mg/L)",
            "Predicted dissolved oxygen (mg/L)",
            "Actual vs predicted — station-grouped holdout",
        ),
        (
            "residual_vs_predicted.png",
            errors["predicted_do_mg_l"],
            errors["residual_mg_l"],
            "Predicted dissolved oxygen (mg/L)",
            "Residual: actual − predicted (mg/L)",
            "Residual vs predicted",
        ),
        (
            "absolute_error_vs_actual.png",
            errors["actual_do_mg_l"],
            errors["absolute_error_mg_l"],
            "Actual dissolved oxygen (mg/L)",
            "Absolute error (mg/L)",
            "Absolute error across the target range",
        ),
    ]
    for filename, x_values, y_values, x_label, y_label, title in specifications:
        figure, axis = plt.subplots(figsize=(7, 5))
        axis.scatter(x_values, y_values, s=8, alpha=0.2)
        if filename == "actual_vs_predicted.png":
            lower = min(float(x_values.min()), float(y_values.min()))
            upper = max(float(x_values.max()), float(y_values.max()))
            axis.plot([lower, upper], [lower, upper], "--", color="black", linewidth=1)
        elif filename == "residual_vs_predicted.png":
            axis.axhline(0, linestyle="--", color="black", linewidth=1)
        axis.set(xlabel=x_label, ylabel=y_label, title=title)
        axis.grid(alpha=0.2)
        figure.tight_layout()
        path = destination / filename
        figure.savefig(path, dpi=160)
        plt.close(figure)
        paths.append(path)

    figure, axis = plt.subplots(figsize=(7, 5))
    axis.hist(errors["residual_mg_l"], bins=80)
    axis.axvline(0, linestyle="--", color="black", linewidth=1)
    axis.set(
        xlabel="Residual: actual − predicted (mg/L)",
        ylabel="Holdout observations",
        title="Residual distribution",
    )
    figure.tight_layout()
    path = destination / "residual_distribution.png"
    figure.savefig(path, dpi=160)
    plt.close(figure)
    paths.append(path)
    return paths
