"""Reproducible low-dissolved-oxygen evaluation utilities.

This module operates only on saved predictions.  It never fits a model and it
does not mutate historical experiment artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

import numpy as np
import pandas as pd


LOW_DO_THRESHOLD_MG_L = 4.0
BOOTSTRAP_SEED = 20_261_012
BOOTSTRAP_RESAMPLES = 2_000

_COLUMN_ALIASES = {
    "actual": "actual_do_mg_l",
    "predicted": "predicted_do_mg_l",
    "absolute_error": "absolute_error_mg_l",
}
_REQUIRED_COLUMNS = {
    "source_object_id",
    "station_code",
    "actual_do_mg_l",
    "predicted_do_mg_l",
}


@dataclass(frozen=True)
class BootstrapResult:
    """Long-form site-clustered bootstrap summary."""

    summary: pd.DataFrame
    replicate_metrics: pd.DataFrame


def normalise_prediction_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Return a validated prediction table with canonical column names."""
    renamed = data.rename(
        columns={old: new for old, new in _COLUMN_ALIASES.items() if new not in data}
    ).copy()
    missing = sorted(_REQUIRED_COLUMNS.difference(renamed.columns))
    if missing:
        raise ValueError(f"Prediction table is missing columns: {', '.join(missing)}")

    for column in ("actual_do_mg_l", "predicted_do_mg_l"):
        renamed[column] = pd.to_numeric(renamed[column], errors="raise")
        if not np.isfinite(renamed[column].to_numpy(dtype=float)).all():
            raise ValueError(f"Prediction table contains non-finite {column} values")
    if renamed["station_code"].isna().any():
        raise ValueError("Prediction table contains missing station_code values")
    if renamed["source_object_id"].isna().any():
        raise ValueError("Prediction table contains missing source_object_id values")

    renamed["prediction_minus_ground_truth_mg_l"] = (
        renamed["predicted_do_mg_l"] - renamed["actual_do_mg_l"]
    )
    renamed["absolute_error_mg_l"] = renamed[
        "prediction_minus_ground_truth_mg_l"
    ].abs()
    renamed["squared_error_mg_l2"] = renamed[
        "prediction_minus_ground_truth_mg_l"
    ].pow(2)
    return renamed


def _safe_ratio(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else float("nan")


def compute_low_do_metrics(
    data: pd.DataFrame, *, threshold_mg_l: float = LOW_DO_THRESHOLD_MG_L
) -> dict[str, float | int | str | bool]:
    """Compute regression and low-DO detection metrics.

    The positive class is ground-truth DO strictly below ``threshold_mg_l``;
    predicted positive is predicted DO strictly below the same threshold.
    Precision and F1 are undefined (NaN) when there are no predicted positives.
    Recall and false-negative rate are undefined when there are no actual
    positives.
    """
    frame = normalise_prediction_columns(data)
    actual = frame["actual_do_mg_l"].to_numpy(dtype=float)
    predicted = frame["predicted_do_mg_l"].to_numpy(dtype=float)
    error = predicted - actual
    actual_low = actual < threshold_mg_l
    predicted_low = predicted < threshold_mg_l
    tp = int(np.sum(actual_low & predicted_low))
    fp = int(np.sum(~actual_low & predicted_low))
    fn = int(np.sum(actual_low & ~predicted_low))
    tn = int(np.sum(~actual_low & ~predicted_low))
    actual_positive = tp + fn
    predicted_positive = tp + fp

    precision = _safe_ratio(tp, predicted_positive)
    recall = _safe_ratio(tp, actual_positive)
    false_negative_rate = _safe_ratio(fn, actual_positive)
    f1 = (
        _safe_ratio(2 * tp, 2 * tp + fp + fn)
        if predicted_positive and actual_positive
        else float("nan")
    )
    low_error = error[actual_low]
    residual_sum_squares = float(np.sum(error**2))
    total_sum_squares = float(np.sum((actual - actual.mean()) ** 2))
    r2 = (
        float(1.0 - residual_sum_squares / total_sum_squares)
        if len(actual) > 1 and total_sum_squares > 0
        else float("nan")
    )
    return {
        "threshold_mg_l": float(threshold_mg_l),
        "positive_class": f"ground_truth_do < {threshold_mg_l:g} mg/L",
        "predicted_positive_rule": f"predicted_do < {threshold_mg_l:g} mg/L",
        "sample_count": int(len(frame)),
        "unique_observation_count": int(frame["source_object_id"].nunique()),
        "station_count": int(frame["station_code"].nunique()),
        "overall_mae_mg_l": float(np.mean(np.abs(error))),
        "overall_rmse_mg_l": float(np.sqrt(np.mean(error**2))),
        "overall_r2": r2,
        "low_do_count": actual_positive,
        "low_do_station_count": int(frame.loc[actual_low, "station_code"].nunique()),
        "predicted_low_do_count": predicted_positive,
        "true_positive_count": tp,
        "false_positive_count": fp,
        "false_negative_count": fn,
        "true_negative_count": tn,
        "low_do_mae_mg_l": (
            float(np.mean(np.abs(low_error))) if actual_positive else float("nan")
        ),
        "low_do_rmse_mg_l": (
            float(np.sqrt(np.mean(low_error**2)))
            if actual_positive
            else float("nan")
        ),
        "low_do_bias_prediction_minus_truth_mg_l": (
            float(np.mean(low_error)) if actual_positive else float("nan")
        ),
        "low_do_recall": recall,
        "low_do_precision": precision,
        "low_do_f1": f1,
        "low_do_false_negative_rate": false_negative_rate,
        "precision_defined": bool(predicted_positive),
        "recall_defined": bool(actual_positive),
        "f1_defined": bool(predicted_positive and actual_positive),
    }


def aggregate_repeated_observations(data: pd.DataFrame) -> pd.DataFrame:
    """Collapse repeated-split appearances to one row per source observation.

    Predictions are averaged across appearances.  Ground truth, station, date,
    and year must be invariant for a source ID; otherwise the function refuses
    to aggregate because the observation identity is not trustworthy.
    """
    frame = normalise_prediction_columns(data)
    invariants = ["station_code", "actual_do_mg_l"]
    invariants.extend(c for c in ("sample_date", "sample_year") if c in frame)
    variation = frame.groupby("source_object_id", dropna=False)[invariants].nunique(
        dropna=False
    )
    bad = variation.gt(1).any(axis=1)
    if bad.any():
        examples = ", ".join(map(str, variation.index[bad][:5]))
        raise ValueError(
            "Repeated appearances disagree on invariant fields for source IDs: "
            + examples
        )

    aggregation: dict[str, str] = {
        "station_code": "first",
        "actual_do_mg_l": "first",
        "predicted_do_mg_l": "mean",
    }
    for column in ("sample_date", "sample_year"):
        if column in frame:
            aggregation[column] = "first"
    grouped = frame.groupby("source_object_id", as_index=False).agg(aggregation)
    appearances = frame.groupby("source_object_id").size().rename("appearance_count")
    grouped = grouped.join(appearances, on="source_object_id")
    if "seed" in frame:
        seeds = frame.groupby("source_object_id")["seed"].nunique().rename("seed_count")
        grouped = grouped.join(seeds, on="source_object_id")
    return normalise_prediction_columns(grouped)


def _metric_from_totals(totals: np.ndarray) -> dict[str, float]:
    (
        n,
        sum_abs,
        sum_squared_error,
        sum_actual,
        sum_actual_squared,
        low_n,
        low_sum_abs,
        low_sum_squared_error,
        low_sum_error,
        tp,
        fp,
        fn,
    ) = totals
    predicted_positive = tp + fp
    tss = sum_actual_squared - (sum_actual**2 / n) if n else 0.0
    return {
        "overall_mae_mg_l": _safe_ratio(sum_abs, n),
        "overall_rmse_mg_l": np.sqrt(_safe_ratio(sum_squared_error, n)),
        "overall_r2": (
            float(1.0 - sum_squared_error / tss) if n > 1 and tss > 0 else np.nan
        ),
        "low_do_mae_mg_l": _safe_ratio(low_sum_abs, low_n),
        "low_do_rmse_mg_l": np.sqrt(_safe_ratio(low_sum_squared_error, low_n)),
        "low_do_bias_prediction_minus_truth_mg_l": _safe_ratio(
            low_sum_error, low_n
        ),
        "low_do_recall": _safe_ratio(tp, low_n),
        "low_do_precision": _safe_ratio(tp, predicted_positive),
        "low_do_f1": (
            _safe_ratio(2 * tp, 2 * tp + fp + fn)
            if low_n and predicted_positive
            else np.nan
        ),
        "low_do_false_negative_rate": _safe_ratio(fn, low_n),
        "low_do_count": float(low_n),
    }


def site_clustered_bootstrap(
    data: pd.DataFrame,
    *,
    threshold_mg_l: float = LOW_DO_THRESHOLD_MG_L,
    n_resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
    metrics: Iterable[str] | None = None,
) -> BootstrapResult:
    """Bootstrap whole stations and return percentile 95% intervals.

    Each draw samples the observed number of stations with replacement.  A
    selected station contributes all of its rows; duplicated draws contribute
    duplicated clusters, not falsely relabelled independent observations.
    """
    if n_resamples <= 0:
        raise ValueError("n_resamples must be positive")
    frame = normalise_prediction_columns(data)
    actual_low = frame["actual_do_mg_l"] < threshold_mg_l
    predicted_low = frame["predicted_do_mg_l"] < threshold_mg_l
    error = frame["prediction_minus_ground_truth_mg_l"]
    work = frame.assign(
        _n=1.0,
        _abs=error.abs(),
        _sq=error.pow(2),
        _actual=frame["actual_do_mg_l"],
        _actual_sq=frame["actual_do_mg_l"].pow(2),
        _low_n=actual_low.astype(float),
        _low_abs=error.abs().where(actual_low, 0.0),
        _low_sq=error.pow(2).where(actual_low, 0.0),
        _low_error=error.where(actual_low, 0.0),
        _tp=(actual_low & predicted_low).astype(float),
        _fp=(~actual_low & predicted_low).astype(float),
        _fn=(actual_low & ~predicted_low).astype(float),
    )
    value_columns = [
        "_n",
        "_abs",
        "_sq",
        "_actual",
        "_actual_sq",
        "_low_n",
        "_low_abs",
        "_low_sq",
        "_low_error",
        "_tp",
        "_fp",
        "_fn",
    ]
    site_totals = work.groupby("station_code", sort=True)[value_columns].sum()
    if site_totals.empty:
        raise ValueError("Cannot bootstrap an empty prediction table")
    matrix = site_totals.to_numpy(dtype=float)
    station_count = len(site_totals)
    rng = np.random.default_rng(seed)
    requested_metrics = list(metrics) if metrics is not None else list(
        _metric_from_totals(matrix.sum(axis=0))
    )
    rows: list[dict[str, float | int]] = []
    for replicate in range(n_resamples):
        selected = rng.integers(0, station_count, size=station_count)
        values = _metric_from_totals(matrix[selected].sum(axis=0))
        rows.append(
            {"replicate": replicate, **{key: values[key] for key in requested_metrics}}
        )
    replicates = pd.DataFrame(rows)
    point = _metric_from_totals(matrix.sum(axis=0))
    summaries: list[dict[str, float | int | str]] = []
    for metric in requested_metrics:
        valid = replicates[metric].dropna()
        summaries.append(
            {
                "metric": metric,
                "estimate": point[metric],
                "ci_95_lower": valid.quantile(0.025) if len(valid) else np.nan,
                "ci_95_upper": valid.quantile(0.975) if len(valid) else np.nan,
                "valid_resamples": int(len(valid)),
                "invalid_resamples": int(n_resamples - len(valid)),
                "resamples": int(n_resamples),
                "seed": int(seed),
                "cluster_unit": "station_code",
                "cluster_count": int(station_count),
            }
        )
    return BootstrapResult(pd.DataFrame(summaries), replicates)


def low_do_site_analysis(
    data: pd.DataFrame, *, threshold_mg_l: float = LOW_DO_THRESHOLD_MG_L
) -> pd.DataFrame:
    """Summarise low-DO errors by station, including error contribution."""
    frame = normalise_prediction_columns(data)
    low = frame.loc[frame["actual_do_mg_l"] < threshold_mg_l].copy()
    if low.empty:
        return pd.DataFrame()
    low["false_negative"] = low["predicted_do_mg_l"] >= threshold_mg_l
    grouped = low.groupby("station_code", sort=True)
    result = grouped.agg(
        low_do_count=("source_object_id", "size"),
        unique_observation_count=("source_object_id", "nunique"),
        false_negative_count=("false_negative", "sum"),
        low_do_mae_mg_l=("absolute_error_mg_l", "mean"),
        low_do_rmse_mg_l=("squared_error_mg_l2", lambda x: float(np.sqrt(x.mean()))),
        low_do_bias_prediction_minus_truth_mg_l=(
            "prediction_minus_ground_truth_mg_l",
            "mean",
        ),
        total_low_do_absolute_error_mg_l=("absolute_error_mg_l", "sum"),
        total_low_do_squared_error_mg_l2=("squared_error_mg_l2", "sum"),
        minimum_actual_do_mg_l=("actual_do_mg_l", "min"),
        maximum_actual_do_mg_l=("actual_do_mg_l", "max"),
    ).reset_index()
    result["false_negative_rate"] = (
        result["false_negative_count"] / result["low_do_count"]
    )
    result["absolute_error_share"] = result[
        "total_low_do_absolute_error_mg_l"
    ] / result["total_low_do_absolute_error_mg_l"].sum()
    result["squared_error_share"] = result[
        "total_low_do_squared_error_mg_l2"
    ] / result["total_low_do_squared_error_mg_l2"].sum()
    return result.sort_values(
        ["total_low_do_absolute_error_mg_l", "station_code"],
        ascending=[False, True],
    ).reset_index(drop=True)


def stratified_metrics(
    data: pd.DataFrame,
    strata: pd.Series,
    *,
    stratum_name: str,
    threshold_mg_l: float = LOW_DO_THRESHOLD_MG_L,
) -> pd.DataFrame:
    """Apply the core metrics to supplied, index-aligned strata."""
    frame = normalise_prediction_columns(data)
    aligned = pd.Series(strata, index=data.index, name=stratum_name)
    rows = []
    for label, indexes in aligned.groupby(aligned, dropna=False).groups.items():
        metrics = compute_low_do_metrics(frame.loc[indexes], threshold_mg_l=threshold_mg_l)
        rows.append({stratum_name: label, **metrics})
    return pd.DataFrame(rows)


def spearman_feature_associations(
    data: pd.DataFrame,
    feature_columns: Iterable[str],
    *,
    threshold_mg_l: float = LOW_DO_THRESHOLD_MG_L,
) -> pd.DataFrame:
    """Compute exploratory low-DO Spearman associations, never causality."""
    frame = normalise_prediction_columns(data)
    low = frame.loc[frame["actual_do_mg_l"] < threshold_mg_l]
    rows = []
    for feature in feature_columns:
        if feature not in low:
            continue
        values = pd.to_numeric(low[feature], errors="coerce")
        valid = values.notna()
        rows.append(
            {
                "feature": feature,
                "low_do_count": int(len(low)),
                "nonmissing_count": int(valid.sum()),
                "missing_fraction": float(1 - valid.mean()),
                "spearman_with_absolute_error": (
                    float(values[valid].corr(low.loc[valid, "absolute_error_mg_l"], method="spearman"))
                    if valid.sum() >= 3 and values[valid].nunique() > 1
                    else np.nan
                ),
                "spearman_with_prediction_minus_truth": (
                    float(
                        values[valid].corr(
                            low.loc[valid, "prediction_minus_ground_truth_mg_l"],
                            method="spearman",
                        )
                    )
                    if valid.sum() >= 3 and values[valid].nunique() > 1
                    else np.nan
                ),
            }
        )
    return pd.DataFrame(rows)


def sha256_file(path: str | "PathLike[str]") -> str:
    """Return a streaming SHA-256 digest for an evidence file."""
    import hashlib

    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
