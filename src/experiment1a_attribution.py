"""Post-hoc attribution utilities for WaterSense Experiment 1A.

This module only analyzes saved Experiment 1 metrics and predictions.  It does
not fit estimators, select a new model, or access legacy-test evidence.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


class AttributionIntegrityError(RuntimeError):
    """Raised when saved Experiment 1 evidence cannot be paired exactly."""


ANCHOR_CANDIDATE_ID = (
    "RandomForestRegressor__n_estimators=150__min_samples_leaf=2__"
    "max_features=0.8__weight=1"
)

INNER_METRICS = (
    "overall_mae_mg_l",
    "low_do_mae_mg_l",
    "low_do_bias_prediction_minus_truth_mg_l",
    "low_do_recall",
    "low_do_precision",
    "low_do_f1",
    "false_positive_count",
    "true_positive_count",
)

SELECTED_METRICS = (
    "pooled_overall_mae_mg_l",
    "pooled_low_do_mae_mg_l",
    "pooled_low_do_bias_prediction_minus_truth_mg_l",
    "pooled_low_do_recall",
    "pooled_low_do_precision",
    "pooled_low_do_f1",
    "pooled_false_positive_count",
)


def _require_columns(frame: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise AttributionIntegrityError(f"Missing required columns: {missing}")


def pair_outer_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    """Return one exactly paired baseline/weighted row per source observation."""

    required = {
        "variant",
        "source_object_id",
        "station_code",
        "outer_fold",
        "actual_do_mg_l",
        "predicted_do_mg_l",
    }
    _require_columns(predictions, required)
    if set(predictions["variant"]) != {"baseline", "weighted"}:
        raise AttributionIntegrityError("Expected exactly baseline and weighted variants")
    identity = ["source_object_id"]
    base_columns = [
        "source_object_id",
        "station_code",
        "outer_fold",
        "actual_do_mg_l",
        "predicted_do_mg_l",
    ]
    baseline = predictions.loc[
        predictions["variant"].eq("baseline"), base_columns
    ].copy()
    weighted = predictions.loc[
        predictions["variant"].eq("weighted"), base_columns
    ].copy()
    if baseline[identity].duplicated().any() or weighted[identity].duplicated().any():
        raise AttributionIntegrityError("Variant contains duplicate observation identity")
    paired = baseline.merge(
        weighted,
        on=identity,
        how="outer",
        validate="one_to_one",
        suffixes=("__baseline", "__weighted"),
        indicator=True,
    )
    if not paired["_merge"].eq("both").all():
        raise AttributionIntegrityError("Baseline/weighted observation identities differ")
    for column in ("station_code", "outer_fold", "actual_do_mg_l"):
        left = paired[f"{column}__baseline"]
        right = paired[f"{column}__weighted"]
        if column == "actual_do_mg_l":
            equal = np.isclose(left, right, rtol=0.0, atol=0.0)
        else:
            equal = left.eq(right)
        if not bool(np.all(equal)):
            raise AttributionIntegrityError(f"Paired {column} differs")
    result = pd.DataFrame(
        {
            "source_object_id": paired["source_object_id"],
            "station_code": paired["station_code__baseline"],
            "outer_fold": paired["outer_fold__baseline"].astype(int),
            "actual_do_mg_l": paired["actual_do_mg_l__baseline"],
            "baseline_prediction_mg_l": paired["predicted_do_mg_l__baseline"],
            "weighted_prediction_mg_l": paired["predicted_do_mg_l__weighted"],
        }
    )
    result["baseline_absolute_error_mg_l"] = (
        result["baseline_prediction_mg_l"] - result["actual_do_mg_l"]
    ).abs()
    result["weighted_absolute_error_mg_l"] = (
        result["weighted_prediction_mg_l"] - result["actual_do_mg_l"]
    ).abs()
    result["delta_absolute_error_weighted_minus_baseline_mg_l"] = (
        result["weighted_absolute_error_mg_l"]
        - result["baseline_absolute_error_mg_l"]
    )
    result["prediction_shift_weighted_minus_baseline_mg_l"] = (
        result["weighted_prediction_mg_l"] - result["baseline_prediction_mg_l"]
    )
    result["actual_low_do"] = result["actual_do_mg_l"].lt(4.0)
    result["baseline_predicted_low_do"] = result[
        "baseline_prediction_mg_l"
    ].lt(4.0)
    result["weighted_predicted_low_do"] = result[
        "weighted_prediction_mg_l"
    ].lt(4.0)
    return result.sort_values("source_object_id").reset_index(drop=True)


def matched_inner_weight_pairs(inner_results: pd.DataFrame) -> pd.DataFrame:
    """Pair weight 8 with weight 1 for every identical inner-fold configuration."""

    keys = ["outer_fold", "inner_fold", "family", "parameters_json"]
    _require_columns(
        inner_results,
        [*keys, "weight_multiplier", "run_status", *INNER_METRICS],
    )
    if not inner_results["run_status"].eq("complete").all():
        raise AttributionIntegrityError("Incomplete inner candidate rows present")
    frames: dict[int, pd.DataFrame] = {}
    for weight in (1, 8):
        subset = inner_results.loc[
            inner_results["weight_multiplier"].eq(weight), [*keys, *INNER_METRICS]
        ].copy()
        if subset.duplicated(keys).any():
            raise AttributionIntegrityError(f"Duplicate weight {weight} pair key")
        frames[weight] = subset
    paired = frames[1].merge(
        frames[8],
        on=keys,
        how="outer",
        validate="one_to_one",
        suffixes=("__weight1", "__weight8"),
        indicator=True,
    )
    if not paired["_merge"].eq("both").all():
        raise AttributionIntegrityError("Weight 1 and 8 grids do not match")
    paired = paired.drop(columns="_merge")
    for metric in INNER_METRICS:
        paired[f"delta_weight8_minus_weight1__{metric}"] = (
            paired[f"{metric}__weight8"] - paired[f"{metric}__weight1"]
        )
    return paired.sort_values(keys).reset_index(drop=True)


def summarize_inner_weight_pairs(pairs: pd.DataFrame) -> pd.DataFrame:
    """Create descriptive summaries; matched folds are not treated as independent."""

    rows: list[dict[str, object]] = []
    groups = [("ALL", pairs), *list(pairs.groupby("family", sort=True))]
    lower_is_better = {
        "overall_mae_mg_l",
        "low_do_mae_mg_l",
        "low_do_bias_prediction_minus_truth_mg_l",
        "false_positive_count",
    }
    for family, subset in groups:
        for metric in INNER_METRICS:
            delta = subset[f"delta_weight8_minus_weight1__{metric}"]
            beneficial = delta.lt(0) if metric in lower_is_better else delta.gt(0)
            rows.append(
                {
                    "family": family,
                    "metric": metric,
                    "matched_pair_count": len(delta),
                    "mean_delta_weight8_minus_weight1": float(delta.mean()),
                    "median_delta_weight8_minus_weight1": float(delta.median()),
                    "beneficial_pair_count": int(beneficial.sum()),
                    "zero_delta_pair_count": int(delta.eq(0).sum()),
                    "adverse_pair_count": int((~beneficial & ~delta.eq(0)).sum()),
                    "interpretation_scope": (
                        "descriptive post-hoc inner-fold evidence; folds overlap and "
                        "are not independent replicates"
                    ),
                }
            )
    return pd.DataFrame(rows)


def selected_config_attribution(selection: pd.DataFrame) -> pd.DataFrame:
    """Decompose selected inner results into architecture and weight contrasts."""

    keys = ["outer_fold", "family", "parameters_json"]
    _require_columns(
        selection,
        [
            *keys,
            "candidate_id",
            "weight_multiplier",
            "selected",
            *SELECTED_METRICS,
        ],
    )
    selected = selection.loc[selection["selected"], keys]
    if len(selected) != 5 or selected["outer_fold"].nunique() != 5:
        raise AttributionIntegrityError("Expected one selected row in each outer fold")
    weight1 = selection.loc[selection["weight_multiplier"].eq(1)].merge(
        selected, on=keys, how="inner", validate="one_to_one"
    )
    weight8 = selection.loc[selection["selected"]].copy()
    anchor = selection.loc[selection["candidate_id"].eq(ANCHOR_CANDIDATE_ID)].copy()
    if not (len(weight1) == len(weight8) == len(anchor) == 5):
        raise AttributionIntegrityError("Selected/weight-1/anchor decomposition incomplete")
    weight1 = weight1.set_index("outer_fold")
    weight8 = weight8.set_index("outer_fold")
    anchor = anchor.set_index("outer_fold")
    rows: list[dict[str, object]] = []
    for outer_fold in range(1, 6):
        row: dict[str, object] = {
            "outer_fold": outer_fold,
            "selected_family": weight8.loc[outer_fold, "family"],
            "selected_parameters_json": weight8.loc[outer_fold, "parameters_json"],
        }
        for metric in SELECTED_METRICS:
            anchor_value = float(anchor.loc[outer_fold, metric])
            weight1_value = float(weight1.loc[outer_fold, metric])
            weight8_value = float(weight8.loc[outer_fold, metric])
            row[f"anchor__{metric}"] = anchor_value
            row[f"matched_hgb_weight1__{metric}"] = weight1_value
            row[f"selected_weight8__{metric}"] = weight8_value
            row[f"architecture_delta_hgb_weight1_minus_anchor__{metric}"] = (
                weight1_value - anchor_value
            )
            row[f"weight_delta_weight8_minus_weight1__{metric}"] = (
                weight8_value - weight1_value
            )
            row[f"full_delta_weight8_minus_anchor__{metric}"] = (
                weight8_value - anchor_value
            )
        rows.append(row)
    return pd.DataFrame(rows)


def outer_error_decomposition(paired: pd.DataFrame) -> pd.DataFrame:
    """Decompose total absolute-error change by actual-DO range."""

    frame = paired.copy()
    labels = ["<2", "2-<3", "3-<4", "4-<5", "5-<6", "6-<8", "8-<10", ">=10"]
    frame["actual_do_range_mg_l"] = pd.cut(
        frame["actual_do_mg_l"],
        bins=[-np.inf, 2, 3, 4, 5, 6, 8, 10, np.inf],
        labels=labels,
        right=False,
    )
    delta_column = "delta_absolute_error_weighted_minus_baseline_mg_l"
    result = (
        frame.groupby("actual_do_range_mg_l", observed=True, sort=False)
        .agg(
            sample_count=("actual_do_mg_l", "size"),
            station_count=("station_code", "nunique"),
            baseline_mae_mg_l=("baseline_absolute_error_mg_l", "mean"),
            weighted_mae_mg_l=("weighted_absolute_error_mg_l", "mean"),
            delta_mae_weighted_minus_baseline_mg_l=(delta_column, "mean"),
            delta_total_absolute_error_mg_l=(delta_column, "sum"),
            mean_prediction_shift_mg_l=(
                "prediction_shift_weighted_minus_baseline_mg_l",
                "mean",
            ),
            median_prediction_shift_mg_l=(
                "prediction_shift_weighted_minus_baseline_mg_l",
                "median",
            ),
        )
        .reset_index()
    )
    net = float(result["delta_total_absolute_error_mg_l"].sum())
    result["share_of_net_total_absolute_error_change"] = (
        result["delta_total_absolute_error_mg_l"] / net
    )
    return result


def classification_transitions(paired: pd.DataFrame) -> pd.DataFrame:
    """Count paired classification-state transitions and their station support."""

    frame = paired.copy()
    frame["baseline_state"] = np.where(
        frame["actual_low_do"],
        np.where(frame["baseline_predicted_low_do"], "TP", "FN"),
        np.where(frame["baseline_predicted_low_do"], "FP", "TN"),
    )
    frame["weighted_state"] = np.where(
        frame["actual_low_do"],
        np.where(frame["weighted_predicted_low_do"], "TP", "FN"),
        np.where(frame["weighted_predicted_low_do"], "FP", "TN"),
    )
    return (
        frame.groupby(
            ["actual_low_do", "baseline_state", "weighted_state"], sort=True
        )
        .agg(
            observation_count=("source_object_id", "size"),
            station_count=("station_code", "nunique"),
        )
        .reset_index()
    )


def low_do_recall_site_analysis(paired: pd.DataFrame) -> pd.DataFrame:
    """Describe where additional true-low detections occur across stations."""

    low = paired.loc[paired["actual_low_do"]].copy()
    result = (
        low.groupby("station_code", sort=True)
        .agg(
            low_do_observation_count=("source_object_id", "size"),
            baseline_true_positive_count=("baseline_predicted_low_do", "sum"),
            weighted_true_positive_count=("weighted_predicted_low_do", "sum"),
            delta_total_absolute_error_mg_l=(
                "delta_absolute_error_weighted_minus_baseline_mg_l",
                "sum",
            ),
        )
        .reset_index()
    )
    result["true_positive_gain"] = (
        result["weighted_true_positive_count"]
        - result["baseline_true_positive_count"]
    )
    result["baseline_recall"] = (
        result["baseline_true_positive_count"]
        / result["low_do_observation_count"]
    )
    result["weighted_recall"] = (
        result["weighted_true_positive_count"]
        / result["low_do_observation_count"]
    )
    result["delta_recall"] = result["weighted_recall"] - result["baseline_recall"]
    return result.sort_values(
        ["true_positive_gain", "station_code"], ascending=[False, True]
    ).reset_index(drop=True)


def false_positive_site_analysis(paired: pd.DataFrame) -> pd.DataFrame:
    """Summarize newly introduced false positives by station."""

    new_false_positive = paired.loc[
        ~paired["actual_low_do"]
        & ~paired["baseline_predicted_low_do"]
        & paired["weighted_predicted_low_do"]
    ].copy()
    return (
        new_false_positive.groupby("station_code", sort=True)
        .agg(
            new_false_positive_count=("source_object_id", "size"),
            actual_do_mean_mg_l=("actual_do_mg_l", "mean"),
            actual_do_min_mg_l=("actual_do_mg_l", "min"),
            actual_do_max_mg_l=("actual_do_mg_l", "max"),
            weighted_prediction_mean_mg_l=("weighted_prediction_mg_l", "mean"),
        )
        .reset_index()
        .sort_values(
            ["new_false_positive_count", "station_code"], ascending=[False, True]
        )
        .reset_index(drop=True)
    )


def false_positive_range_analysis(paired: pd.DataFrame) -> pd.DataFrame:
    """Summarize newly introduced false positives by actual-DO range."""

    frame = paired.loc[
        ~paired["actual_low_do"]
        & ~paired["baseline_predicted_low_do"]
        & paired["weighted_predicted_low_do"]
    ].copy()
    frame["actual_do_range_mg_l"] = pd.cut(
        frame["actual_do_mg_l"],
        bins=[4, 4.25, 4.5, 5, 6, 8, np.inf],
        labels=["4-<4.25", "4.25-<4.5", "4.5-<5", "5-<6", "6-<8", ">=8"],
        right=False,
    )
    return (
        frame.groupby("actual_do_range_mg_l", observed=True, sort=False)
        .agg(
            new_false_positive_count=("source_object_id", "size"),
            station_count=("station_code", "nunique"),
            actual_do_mean_mg_l=("actual_do_mg_l", "mean"),
            weighted_prediction_mean_mg_l=("weighted_prediction_mg_l", "mean"),
        )
        .reset_index()
    )


def prediction_shift_quantiles(paired: pd.DataFrame) -> pd.DataFrame:
    """Return a compact empirical distribution of weighted prediction shifts."""

    probabilities = [0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0]
    shifts = paired["prediction_shift_weighted_minus_baseline_mg_l"]
    return pd.DataFrame(
        {
            "quantile": probabilities,
            "prediction_shift_weighted_minus_baseline_mg_l": [
                float(shifts.quantile(probability)) for probability in probabilities
            ],
        }
    )
