"""Frozen utilities for WaterSense Phase 2B Experiment 1.

This module contains the preregistered candidate enumeration, fold-local
weighting, metric calculations, selection, and paired site bootstrap.  The
runner is responsible for loading only the verified development partition and
the frozen site assignments.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from itertools import product
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    ExtraTreesRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)


LOW_DO_THRESHOLD_MG_L = 4.0
EXPERIMENT_SEED = 20_261_012
BOOTSTRAP_RESAMPLES = 2_000
ANCHOR_CANDIDATE_ID = (
    "RandomForestRegressor__n_estimators=150__min_samples_leaf=2__"
    "max_features=0.8__weight=1"
)

METRIC_COLUMNS = [
    "overall_mae_mg_l",
    "overall_rmse_mg_l",
    "overall_r2",
    "low_do_mae_mg_l",
    "low_do_rmse_mg_l",
    "low_do_bias_prediction_minus_truth_mg_l",
    "low_do_recall",
    "low_do_precision",
    "low_do_f1",
    "low_do_false_negative_rate",
    "low_do_false_positive_rate",
]


class ExperimentIntegrityError(RuntimeError):
    """Raised when frozen experiment identity or pairing is violated."""


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    family: str
    parameters: dict[str, int | float]
    weight_multiplier: int
    complexity_score: float


def _candidate_id(
    family: str, parameters: dict[str, int | float], weight_multiplier: int
) -> str:
    order = {
        "RandomForestRegressor": [
            "n_estimators", "min_samples_leaf", "max_features"
        ],
        "ExtraTreesRegressor": [
            "n_estimators", "min_samples_leaf", "max_features"
        ],
        "HistGradientBoostingRegressor": [
            "learning_rate", "max_leaf_nodes", "min_samples_leaf",
            "l2_regularization",
        ],
    }[family]
    encoded = "__".join(f"{key}={parameters[key]:g}" for key in order)
    return f"{family}__{encoded}__weight={weight_multiplier}"


def enumerate_frozen_candidates(config: dict[str, Any]) -> list[Candidate]:
    """Enumerate the machine-frozen grid in stable candidate-ID order."""
    multipliers = [int(value) for value in config["sample_weight"]["multipliers"]]
    candidates: list[Candidate] = []
    for family, space in config["candidates"].items():
        if family in {"RandomForestRegressor", "ExtraTreesRegressor"}:
            combinations = product(
                space["n_estimators"],
                space["min_samples_leaf"],
                space["max_features"],
                multipliers,
            )
            for trees, leaf, max_features, multiplier in combinations:
                parameters = {
                    "n_estimators": int(trees),
                    "min_samples_leaf": int(leaf),
                    "max_features": float(max_features),
                }
                complexity = float(trees) * float(max_features) / float(leaf)
                candidates.append(
                    Candidate(
                        _candidate_id(family, parameters, multiplier),
                        family,
                        parameters,
                        int(multiplier),
                        complexity,
                    )
                )
        elif family == "HistGradientBoostingRegressor":
            combinations = product(
                space["learning_rate"],
                space["max_leaf_nodes"],
                space["min_samples_leaf"],
                space["l2_regularization"],
                multipliers,
            )
            for rate, leaves, min_leaf, l2, multiplier in combinations:
                parameters = {
                    "learning_rate": float(rate),
                    "max_leaf_nodes": int(leaves),
                    "min_samples_leaf": int(min_leaf),
                    "l2_regularization": float(l2),
                }
                complexity = (
                    float(leaves) / float(min_leaf) / (1.0 + float(l2))
                )
                candidates.append(
                    Candidate(
                        _candidate_id(family, parameters, multiplier),
                        family,
                        parameters,
                        int(multiplier),
                        complexity,
                    )
                )
        else:
            raise ExperimentIntegrityError(f"Unsupported frozen family: {family}")
    candidates.sort(key=lambda candidate: candidate.candidate_id)
    if len(candidates) != 128:
        raise ExperimentIntegrityError(
            f"Frozen grid produced {len(candidates)} candidates, expected 128"
        )
    ids = [candidate.candidate_id for candidate in candidates]
    if len(ids) != len(set(ids)):
        raise ExperimentIntegrityError("Frozen candidate IDs are not unique")
    if ANCHOR_CANDIDATE_ID not in ids:
        raise ExperimentIntegrityError("Historical unweighted RF anchor is absent")
    return candidates


def compute_training_weights(
    training_targets: pd.Series | np.ndarray,
    multiplier: int,
    *,
    threshold_mg_l: float = LOW_DO_THRESHOLD_MG_L,
) -> np.ndarray:
    """Compute normalized sample weights from training targets only."""
    target = np.asarray(training_targets, dtype=float)
    if target.ndim != 1 or not len(target):
        raise ExperimentIntegrityError("Training target must be a nonempty vector")
    if not np.isfinite(target).all():
        raise ExperimentIntegrityError("Training target contains non-finite values")
    if multiplier not in {1, 2, 4, 8}:
        raise ExperimentIntegrityError(f"Unfrozen weight multiplier: {multiplier}")
    raw = np.where(target < threshold_mg_l, float(multiplier), 1.0)
    normalized = raw / raw.mean()
    if not np.isfinite(normalized).all() or not np.isclose(normalized.mean(), 1.0):
        raise ExperimentIntegrityError("Normalized training weights are invalid")
    return normalized


def make_estimator(candidate: Candidate, *, n_jobs: int = 1) -> Any:
    parameters = dict(candidate.parameters)
    if candidate.family == "RandomForestRegressor":
        return RandomForestRegressor(
            **parameters,
            random_state=EXPERIMENT_SEED,
            n_jobs=n_jobs,
        )
    if candidate.family == "ExtraTreesRegressor":
        return ExtraTreesRegressor(
            **parameters,
            random_state=EXPERIMENT_SEED,
            n_jobs=n_jobs,
        )
    if candidate.family == "HistGradientBoostingRegressor":
        return HistGradientBoostingRegressor(
            **parameters,
            random_state=EXPERIMENT_SEED,
        )
    raise ExperimentIntegrityError(f"Unsupported candidate family: {candidate.family}")


def compute_experiment_metrics(
    actual: Iterable[float],
    predicted: Iterable[float],
    *,
    stations: Iterable[str] | None = None,
    threshold_mg_l: float = LOW_DO_THRESHOLD_MG_L,
) -> dict[str, float | int | bool]:
    actual_array = np.asarray(actual, dtype=float)
    predicted_array = np.asarray(predicted, dtype=float)
    if actual_array.ndim != 1 or predicted_array.shape != actual_array.shape:
        raise ExperimentIntegrityError("Actual/predicted vectors must have equal shape")
    if not len(actual_array) or not (
        np.isfinite(actual_array).all() and np.isfinite(predicted_array).all()
    ):
        raise ExperimentIntegrityError("Predictions must be nonempty and finite")
    error = predicted_array - actual_array
    actual_low = actual_array < threshold_mg_l
    predicted_low = predicted_array < threshold_mg_l
    tp = int(np.sum(actual_low & predicted_low))
    fp = int(np.sum(~actual_low & predicted_low))
    fn = int(np.sum(actual_low & ~predicted_low))
    tn = int(np.sum(~actual_low & ~predicted_low))
    positive = tp + fn
    negative = tn + fp
    predicted_positive = tp + fp
    low_error = error[actual_low]
    tss = float(np.sum((actual_array - actual_array.mean()) ** 2))
    precision = float(tp / predicted_positive) if predicted_positive else math.nan
    recall = float(tp / positive) if positive else math.nan
    f1 = (
        float(2 * tp / (2 * tp + fp + fn))
        if positive and predicted_positive
        else math.nan
    )
    station_array = (
        np.asarray(list(stations), dtype=object) if stations is not None else None
    )
    if station_array is not None and len(station_array) != len(actual_array):
        raise ExperimentIntegrityError("Station vector length differs from predictions")
    return {
        "sample_count": int(len(actual_array)),
        "station_count": (
            int(pd.Series(station_array).nunique())
            if station_array is not None else 0
        ),
        "overall_mae_mg_l": float(np.mean(np.abs(error))),
        "overall_rmse_mg_l": float(np.sqrt(np.mean(error**2))),
        "overall_r2": (
            float(1.0 - np.sum(error**2) / tss) if tss > 0 else math.nan
        ),
        "low_do_count": int(positive),
        "low_do_station_count": (
            int(pd.Series(station_array[actual_low]).nunique())
            if station_array is not None else 0
        ),
        "predicted_low_do_count": int(predicted_positive),
        "true_positive_count": tp,
        "false_positive_count": fp,
        "true_negative_count": tn,
        "false_negative_count": fn,
        "low_do_mae_mg_l": (
            float(np.mean(np.abs(low_error))) if positive else math.nan
        ),
        "low_do_rmse_mg_l": (
            float(np.sqrt(np.mean(low_error**2))) if positive else math.nan
        ),
        "low_do_bias_prediction_minus_truth_mg_l": (
            float(np.mean(low_error)) if positive else math.nan
        ),
        "low_do_precision": precision,
        "low_do_recall": recall,
        "low_do_f1": f1,
        "low_do_false_negative_rate": (
            float(fn / positive) if positive else math.nan
        ),
        "low_do_false_positive_rate": (
            float(fp / negative) if negative else math.nan
        ),
        "precision_defined": bool(predicted_positive),
        "recall_defined": bool(positive),
        "f1_defined": bool(positive and predicted_positive),
        "sum_absolute_error": float(np.sum(np.abs(error))),
        "sum_squared_error": float(np.sum(error**2)),
        "sum_actual": float(np.sum(actual_array)),
        "sum_actual_squared": float(np.sum(actual_array**2)),
        "low_sum_absolute_error": float(np.sum(np.abs(low_error))),
        "low_sum_squared_error": float(np.sum(low_error**2)),
        "low_sum_error": float(np.sum(low_error)),
    }


def _metrics_from_fold_totals(rows: pd.DataFrame) -> dict[str, float | int]:
    summed = rows[
        [
            "sample_count", "sum_absolute_error", "sum_squared_error",
            "sum_actual", "sum_actual_squared", "low_do_count",
            "low_sum_absolute_error", "low_sum_squared_error", "low_sum_error",
            "true_positive_count", "false_positive_count", "true_negative_count",
            "false_negative_count",
        ]
    ].sum()
    n = float(summed["sample_count"])
    low_n = float(summed["low_do_count"])
    tp = float(summed["true_positive_count"])
    fp = float(summed["false_positive_count"])
    tn = float(summed["true_negative_count"])
    fn = float(summed["false_negative_count"])
    tss = float(summed["sum_actual_squared"] - summed["sum_actual"] ** 2 / n)
    predicted_positive = tp + fp
    return {
        "sample_count": int(n),
        "overall_mae_mg_l": float(summed["sum_absolute_error"] / n),
        "overall_rmse_mg_l": float(np.sqrt(summed["sum_squared_error"] / n)),
        "overall_r2": (
            float(1.0 - summed["sum_squared_error"] / tss)
            if tss > 0 else math.nan
        ),
        "low_do_count": int(low_n),
        "predicted_low_do_count": int(predicted_positive),
        "true_positive_count": int(tp),
        "false_positive_count": int(fp),
        "true_negative_count": int(tn),
        "false_negative_count": int(fn),
        "low_do_mae_mg_l": (
            float(summed["low_sum_absolute_error"] / low_n)
            if low_n else math.nan
        ),
        "low_do_rmse_mg_l": (
            float(np.sqrt(summed["low_sum_squared_error"] / low_n))
            if low_n else math.nan
        ),
        "low_do_bias_prediction_minus_truth_mg_l": (
            float(summed["low_sum_error"] / low_n) if low_n else math.nan
        ),
        "low_do_precision": (
            float(tp / predicted_positive) if predicted_positive else math.nan
        ),
        "low_do_recall": float(tp / low_n) if low_n else math.nan,
        "low_do_f1": (
            float(2 * tp / (2 * tp + fp + fn))
            if low_n and predicted_positive else math.nan
        ),
        "low_do_false_negative_rate": float(fn / low_n) if low_n else math.nan,
        "low_do_false_positive_rate": (
            float(fp / (fp + tn)) if fp + tn else math.nan
        ),
    }


def summarize_and_select_candidates(
    fold_results: pd.DataFrame,
    candidates: list[Candidate],
) -> tuple[pd.DataFrame, Candidate | None]:
    """Apply frozen pooled qualification and lexicographic inner selection."""
    candidate_map = {candidate.candidate_id: candidate for candidate in candidates}
    required_folds = set(fold_results["inner_fold"].unique())
    anchor_rows = fold_results.loc[
        fold_results["candidate_id"].eq(ANCHOR_CANDIDATE_ID)
        & fold_results["run_status"].eq("complete")
    ]
    if set(anchor_rows["inner_fold"]) != required_folds:
        raise ExperimentIntegrityError("Unweighted anchor is incomplete")
    anchor_pooled = _metrics_from_fold_totals(anchor_rows)
    summaries: list[dict[str, Any]] = []
    for candidate_id in sorted(candidate_map):
        candidate = candidate_map[candidate_id]
        rows = fold_results.loc[fold_results["candidate_id"].eq(candidate_id)]
        failures: list[str] = []
        if set(rows["inner_fold"]) != required_folds or len(rows) != len(required_folds):
            failures.append("incomplete_inner_folds")
        if not rows["run_status"].eq("complete").all():
            failures.append("runtime_or_metric_failure")
        if failures:
            pooled = {metric: math.nan for metric in METRIC_COLUMNS}
            pooled.update({"sample_count": 0, "low_do_count": 0})
        else:
            pooled = _metrics_from_fold_totals(rows)
            if pooled["overall_mae_mg_l"] > 1.10 * anchor_pooled["overall_mae_mg_l"]:
                failures.append("overall_mae_over_10_percent_anchor")
            precision = float(pooled["low_do_precision"])
            if not np.isfinite(precision) or precision < 0.30:
                failures.append("low_do_precision_below_0.30_or_undefined")
            if rows["predicted_low_do_count"].le(0).any():
                failures.append("inner_fold_without_predicted_low")
            if not all(np.isfinite(float(pooled[key])) for key in [
                "overall_mae_mg_l", "low_do_mae_mg_l", "low_do_recall"
            ]):
                failures.append("undefined_required_metric")
        summaries.append(
            {
                "candidate_id": candidate_id,
                "family": candidate.family,
                "parameters_json": json.dumps(candidate.parameters, sort_keys=True),
                "weight_multiplier": candidate.weight_multiplier,
                "complexity_score": candidate.complexity_score,
                "inner_fold_count": int(len(rows)),
                "anchor_pooled_overall_mae_mg_l": anchor_pooled[
                    "overall_mae_mg_l"
                ],
                "overall_mae_ratio_to_anchor": (
                    float(pooled["overall_mae_mg_l"])
                    / float(anchor_pooled["overall_mae_mg_l"])
                    if np.isfinite(float(pooled["overall_mae_mg_l"])) else math.nan
                ),
                "mean_fold_low_do_recall": float(rows["low_do_recall"].mean()),
                "mean_fold_low_do_mae_mg_l": float(
                    rows["low_do_mae_mg_l"].mean()
                ),
                "mean_fold_overall_mae_mg_l": float(
                    rows["overall_mae_mg_l"].mean()
                ),
                **{f"pooled_{key}": value for key, value in pooled.items()},
                "qualified": not failures,
                "failure_reasons": ";".join(failures),
            }
        )
    summary = pd.DataFrame(summaries)
    qualified = summary.loc[summary["qualified"]].copy()
    selected: Candidate | None = None
    if not qualified.empty:
        qualified = qualified.sort_values(
            [
                "mean_fold_low_do_recall",
                "mean_fold_low_do_mae_mg_l",
                "mean_fold_overall_mae_mg_l",
                "complexity_score",
                "candidate_id",
            ],
            ascending=[False, True, True, True, True],
            kind="mergesort",
        )
        selected_id = str(qualified.iloc[0]["candidate_id"])
        selected = candidate_map[selected_id]
        summary["selected"] = summary["candidate_id"].eq(selected_id)
    else:
        summary["selected"] = False
    return summary.sort_values("candidate_id").reset_index(drop=True), selected


def verify_prediction_pairing(predictions: pd.DataFrame) -> None:
    required = {
        "variant", "source_object_id", "station_code", "outer_fold",
        "actual_do_mg_l", "predicted_do_mg_l",
    }
    missing = sorted(required.difference(predictions.columns))
    if missing:
        raise ExperimentIntegrityError(f"Prediction columns missing: {missing}")
    if set(predictions["variant"]) != {"baseline", "weighted"}:
        raise ExperimentIntegrityError("Predictions require baseline and weighted rows")
    key = ["source_object_id", "station_code", "outer_fold"]
    baseline = predictions.loc[predictions["variant"].eq("baseline")].sort_values(key)
    weighted = predictions.loc[predictions["variant"].eq("weighted")].sort_values(key)
    if baseline[key].reset_index(drop=True).equals(weighted[key].reset_index(drop=True)) is False:
        raise ExperimentIntegrityError("Baseline and weighted prediction identities differ")
    if not np.array_equal(
        baseline["actual_do_mg_l"].to_numpy(),
        weighted["actual_do_mg_l"].to_numpy(),
    ):
        raise ExperimentIntegrityError("Paired predictions disagree on ground truth")
    for variant in [baseline, weighted]:
        if variant["source_object_id"].duplicated().any():
            raise ExperimentIntegrityError("Outer predictions duplicate source IDs")


def _site_totals(predictions: pd.DataFrame) -> tuple[list[str], dict[str, np.ndarray]]:
    verify_prediction_pairing(predictions)
    columns = [
        "n", "sum_abs", "sum_sq", "sum_y", "sum_y_sq", "low_n",
        "low_abs", "low_sq", "low_error", "tp", "fp", "tn", "fn",
    ]
    matrices: dict[str, np.ndarray] = {}
    sites = sorted(predictions["station_code"].unique())
    for variant in ["baseline", "weighted"]:
        frame = predictions.loc[predictions["variant"].eq(variant)].copy()
        y = frame["actual_do_mg_l"].to_numpy(dtype=float)
        pred = frame["predicted_do_mg_l"].to_numpy(dtype=float)
        error = pred - y
        low = y < LOW_DO_THRESHOLD_MG_L
        pred_low = pred < LOW_DO_THRESHOLD_MG_L
        work = frame[["station_code"]].assign(
            n=1.0,
            sum_abs=np.abs(error),
            sum_sq=error**2,
            sum_y=y,
            sum_y_sq=y**2,
            low_n=low.astype(float),
            low_abs=np.where(low, np.abs(error), 0.0),
            low_sq=np.where(low, error**2, 0.0),
            low_error=np.where(low, error, 0.0),
            tp=(low & pred_low).astype(float),
            fp=(~low & pred_low).astype(float),
            tn=(~low & ~pred_low).astype(float),
            fn=(low & ~pred_low).astype(float),
        )
        totals = work.groupby("station_code", sort=True)[columns].sum()
        if list(totals.index) != sites:
            raise ExperimentIntegrityError("Variant site sets differ")
        matrices[variant] = totals.to_numpy(dtype=float)
    return sites, matrices


def _metrics_from_site_vector(total: np.ndarray) -> dict[str, float]:
    (
        n, sum_abs, sum_sq, sum_y, sum_y_sq, low_n, low_abs, low_sq,
        low_error, tp, fp, tn, fn,
    ) = total
    predicted_positive = tp + fp
    tss = sum_y_sq - sum_y**2 / n if n else 0.0
    return {
        "overall_mae_mg_l": sum_abs / n if n else math.nan,
        "overall_rmse_mg_l": math.sqrt(sum_sq / n) if n else math.nan,
        "overall_r2": 1.0 - sum_sq / tss if n > 1 and tss > 0 else math.nan,
        "low_do_mae_mg_l": low_abs / low_n if low_n else math.nan,
        "low_do_rmse_mg_l": math.sqrt(low_sq / low_n) if low_n else math.nan,
        "low_do_bias_prediction_minus_truth_mg_l": (
            low_error / low_n if low_n else math.nan
        ),
        "low_do_recall": tp / low_n if low_n else math.nan,
        "low_do_precision": tp / predicted_positive if predicted_positive else math.nan,
        "low_do_f1": (
            2 * tp / (2 * tp + fp + fn)
            if low_n and predicted_positive else math.nan
        ),
        "low_do_false_negative_rate": fn / low_n if low_n else math.nan,
        "low_do_false_positive_rate": fp / (fp + tn) if fp + tn else math.nan,
    }


def paired_site_bootstrap(
    predictions: pd.DataFrame,
    *,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = EXPERIMENT_SEED,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute paired whole-site intervals for both variants and their delta."""
    if resamples <= 0:
        raise ValueError("resamples must be positive")
    sites, matrices = _site_totals(predictions)
    point = {
        variant: _metrics_from_site_vector(matrix.sum(axis=0))
        for variant, matrix in matrices.items()
    }
    rng = np.random.default_rng(seed)
    replicate_rows: list[dict[str, float | int]] = []
    for replicate in range(resamples):
        selected = rng.integers(0, len(sites), size=len(sites))
        baseline = _metrics_from_site_vector(
            matrices["baseline"][selected].sum(axis=0)
        )
        weighted = _metrics_from_site_vector(
            matrices["weighted"][selected].sum(axis=0)
        )
        row: dict[str, float | int] = {"replicate": replicate}
        for metric in METRIC_COLUMNS:
            row[f"baseline__{metric}"] = baseline[metric]
            row[f"weighted__{metric}"] = weighted[metric]
            row[f"delta_weighted_minus_baseline__{metric}"] = (
                weighted[metric] - baseline[metric]
            )
        replicate_rows.append(row)
    replicates = pd.DataFrame(replicate_rows)
    summary_rows: list[dict[str, Any]] = []
    for metric in METRIC_COLUMNS:
        for comparison in ["baseline", "weighted", "delta_weighted_minus_baseline"]:
            column = f"{comparison}__{metric}"
            valid = replicates[column].dropna()
            estimate = (
                point[comparison][metric]
                if comparison in point
                else point["weighted"][metric] - point["baseline"][metric]
            )
            summary_rows.append(
                {
                    "metric": metric,
                    "comparison": comparison,
                    "estimate": estimate,
                    "ci_95_lower": valid.quantile(0.025) if len(valid) else math.nan,
                    "ci_95_upper": valid.quantile(0.975) if len(valid) else math.nan,
                    "valid_resamples": int(len(valid)),
                    "invalid_resamples": int(resamples - len(valid)),
                    "resamples": int(resamples),
                    "seed": int(seed),
                    "cluster_unit": "station_code",
                    "cluster_count": int(len(sites)),
                    "delta_direction": (
                        "weighted_minus_baseline"
                        if comparison == "delta_weighted_minus_baseline" else "not_applicable"
                    ),
                }
            )
    return pd.DataFrame(summary_rows), replicates


def site_error_comparison(predictions: pd.DataFrame) -> pd.DataFrame:
    verify_prediction_pairing(predictions)
    rows: list[dict[str, Any]] = []
    for station, station_frame in predictions.groupby("station_code", sort=True):
        variants: dict[str, dict[str, float | int | bool]] = {}
        for variant in ["baseline", "weighted"]:
            subset = station_frame.loc[station_frame["variant"].eq(variant)]
            variants[variant] = compute_experiment_metrics(
                subset["actual_do_mg_l"], subset["predicted_do_mg_l"],
                stations=subset["station_code"],
            )
        row: dict[str, Any] = {
            "station_code": station,
            "rows": variants["baseline"]["sample_count"],
            "low_do_rows": variants["baseline"]["low_do_count"],
        }
        for metric in [
            "overall_mae_mg_l", "low_do_mae_mg_l",
            "low_do_bias_prediction_minus_truth_mg_l", "low_do_recall",
            "low_do_precision", "predicted_low_do_count", "true_positive_count",
            "false_positive_count", "false_negative_count",
        ]:
            row[f"baseline_{metric}"] = variants["baseline"][metric]
            row[f"weighted_{metric}"] = variants["weighted"][metric]
            row[f"delta_weighted_minus_baseline_{metric}"] = (
                float(variants["weighted"][metric])
                - float(variants["baseline"][metric])
            )
        rows.append(row)
    return pd.DataFrame(rows)


def classify_research_conclusion(
    comparison: pd.DataFrame,
    uncertainty: pd.DataFrame,
    selected_candidates: Iterable[Candidate],
) -> tuple[str, list[str]]:
    """Apply the pre-result conclusion rule recorded for Experiment 1.

    Support requires both co-primary paired intervals to exclude zero in the
    beneficial direction, pooled overall MAE within 10% of baseline, pooled
    precision at least 0.30, and at least one selected multiplier greater than
    one.  Mixed, costly, or interval-crossing results are inconclusive.
    """
    selected = list(selected_candidates)
    reasons: list[str] = []
    if not selected:
        return "NO QUALIFIED MODEL", ["No outer fold produced a qualified candidate"]
    values = comparison.set_index("variant")
    baseline = values.loc["baseline"]
    weighted = values.loc["weighted"]
    deltas = uncertainty.loc[
        uncertainty["comparison"].eq("delta_weighted_minus_baseline")
    ].set_index("metric")
    recall_supported = deltas.loc["low_do_recall", "ci_95_lower"] > 0
    mae_supported = deltas.loc["low_do_mae_mg_l", "ci_95_upper"] < 0
    global_qualified = (
        weighted["overall_mae_mg_l"] <= 1.10 * baseline["overall_mae_mg_l"]
    )
    precision_qualified = weighted["low_do_precision"] >= 0.30
    genuinely_weighted = any(candidate.weight_multiplier > 1 for candidate in selected)
    if recall_supported and mae_supported and global_qualified and precision_qualified and genuinely_weighted:
        reasons.append("Both co-primary paired 95% intervals exclude zero beneficially")
        return "IMPROVEMENT SUPPORTED", reasons
    point_recall = weighted["low_do_recall"] - baseline["low_do_recall"]
    point_low_mae = weighted["low_do_mae_mg_l"] - baseline["low_do_mae_mg_l"]
    if point_recall <= 0 and point_low_mae >= 0:
        reasons.append("Neither co-primary point estimate improved")
        return "NO SUPPORTED IMPROVEMENT", reasons
    if not recall_supported:
        reasons.append("Recall paired interval does not exclude zero beneficially")
    if not mae_supported:
        reasons.append("Low-DO MAE paired interval does not exclude zero beneficially")
    if not global_qualified:
        reasons.append("Pooled overall MAE exceeds the 10% degradation guard")
    if not precision_qualified:
        reasons.append("Pooled low-DO precision is below 0.30")
    if not genuinely_weighted:
        reasons.append("Inner selection did not choose any multiplier above one")
    return "TRADE-OFF / INCONCLUSIVE", reasons
