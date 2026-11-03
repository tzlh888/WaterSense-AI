"""Evidence-only analyses for the WaterSense admissions portfolio."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


LOW_DO_THRESHOLD = 4.0
PERIOD_EDGES = [
    pd.Timestamp("1989-12-31"),
    pd.Timestamp("1999-12-31"),
    pd.Timestamp("2009-12-31"),
    pd.Timestamp("2019-12-31"),
    pd.Timestamp("2024-12-31"),
]
PERIOD_LABELS = ["1990–1999", "2000–2009", "2010–2019", "2020–2024"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def confusion_counts(actual: pd.Series, predicted: pd.Series) -> dict[str, int]:
    actual_bool = actual.astype(bool)
    predicted_bool = predicted.astype(bool)
    return {
        "tp": int((actual_bool & predicted_bool).sum()),
        "fp": int((~actual_bool & predicted_bool).sum()),
        "tn": int((~actual_bool & ~predicted_bool).sum()),
        "fn": int((actual_bool & ~predicted_bool).sum()),
    }


def regression_summary(frame: pd.DataFrame) -> dict[str, float | int]:
    actual = frame["actual_do_mg_l"].astype(float)
    predicted = frame["predicted_do_mg_l"].astype(float)
    low = actual < LOW_DO_THRESHOLD
    counts = confusion_counts(low, predicted < LOW_DO_THRESHOLD)
    absolute_error = (predicted - actual).abs()
    precision_denominator = counts["tp"] + counts["fp"]
    recall_denominator = counts["tp"] + counts["fn"]
    return {
        "rows": int(len(frame)),
        "stations": int(frame["station_code"].nunique()),
        "low_do_rows": int(low.sum()),
        "mae_mg_l": float(absolute_error.mean()),
        "low_do_mae_mg_l": float(absolute_error[low].mean()),
        "low_do_bias_mg_l": float((predicted[low] - actual[low]).mean()),
        **counts,
        "precision": counts["tp"] / precision_denominator,
        "recall": counts["tp"] / recall_denominator,
    }


def verify_regression_identity(frame: pd.DataFrame) -> None:
    expected_variants = {"baseline", "weighted"}
    if set(frame["variant"]) != expected_variants:
        raise ValueError("Expected exactly baseline and weighted variants")
    key = ["source_object_id", "station_code", "sample_date", "outer_fold"]
    indexed = {
        name: group.sort_values(key).reset_index(drop=True)
        for name, group in frame.groupby("variant", sort=False)
    }
    if len(indexed["baseline"]) != len(indexed["weighted"]):
        raise ValueError("Variant row counts differ")
    for column in [*key, "actual_do_mg_l", "actual_low_do"]:
        if not indexed["baseline"][column].equals(indexed["weighted"][column]):
            raise ValueError(f"Variant identity mismatch in {column}")
    for name, group in indexed.items():
        if group["source_object_id"].duplicated().any():
            raise ValueError(f"Duplicate source identity in {name}")
        folds_per_station = group.groupby("station_code")["outer_fold"].nunique()
        if not folds_per_station.eq(1).all():
            raise ValueError(f"Station leakage across outer folds in {name}")


def station_concentration(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float | int]]:
    baseline = frame.loc[frame["variant"].eq("baseline")].copy()
    low = baseline.loc[baseline["actual_do_mg_l"] < LOW_DO_THRESHOLD]
    counts = low.groupby("station_code").size().sort_values(ascending=False)
    shares = counts / counts.sum()
    table = pd.DataFrame(
        {
            "station_code": counts.index,
            "low_do_events": counts.values,
            "event_share": shares.values,
            "cumulative_event_share": shares.cumsum().values,
        }
    )
    hhi = float(np.square(shares).sum())
    summary: dict[str, float | int] = {
        "low_do_events": int(counts.sum()),
        "stations_with_low_do": int(len(counts)),
        "stations_with_one_event": int(counts.eq(1).sum()),
        "top_1_share": float(shares.head(1).sum()),
        "top_5_share": float(shares.head(5).sum()),
        "top_10_share": float(shares.head(10).sum()),
        "top_20_share": float(shares.head(20).sum()),
        "hhi": hhi,
        "effective_station_count": float(1 / hhi),
    }
    return table, summary


def temporal_summary(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    data = frame.copy()
    data["sample_date"] = pd.to_datetime(data["sample_date"], errors="raise")
    data["period"] = pd.cut(
        data["sample_date"], PERIOD_EDGES, labels=PERIOD_LABELS
    )
    if data["period"].isna().any():
        raise ValueError("Prediction date falls outside fixed temporal bands")
    baseline = data.loc[data["variant"].eq("baseline")]
    station_period = baseline.groupby(["station_code", "period"], observed=True).size().unstack()
    balanced_stations = station_period.dropna().index
    rows: list[dict[str, object]] = []
    for variant, variant_data in data.groupby("variant", sort=False):
        variant_data = variant_data.assign(
            absolute_error=(
                variant_data["predicted_do_mg_l"] - variant_data["actual_do_mg_l"]
            ).abs()
        )
        for period in PERIOD_LABELS:
            period_data = variant_data.loc[variant_data["period"].eq(period)]
            balanced = period_data.loc[
                period_data["station_code"].isin(balanced_stations)
            ]
            station_mae = balanced.groupby("station_code")["absolute_error"].mean()
            rows.append(
                {
                    "variant": variant,
                    "period": period,
                    "rows": int(len(period_data)),
                    "stations": int(period_data["station_code"].nunique()),
                    "low_do_rows": int(
                        (period_data["actual_do_mg_l"] < LOW_DO_THRESHOLD).sum()
                    ),
                    "pooled_mae_mg_l": float(period_data["absolute_error"].mean()),
                    "balanced_stations": int(len(balanced_stations)),
                    "balanced_station_macro_mae_mg_l": float(station_mae.mean()),
                }
            )
    return pd.DataFrame(rows), {"balanced_station_count": int(len(balanced_stations))}


def break_even_ratio(first: dict[str, int], second: dict[str, int]) -> float:
    """Return r where r*FN+FP is equal; positive infinity means no crossing."""
    fn_difference = first["fn"] - second["fn"]
    fp_difference = second["fp"] - first["fp"]
    if fn_difference == 0:
        return float("inf")
    ratio = fp_difference / fn_difference
    return float(ratio) if ratio >= 0 else float("inf")


def cost_scenarios(
    model_counts: dict[str, dict[str, int]], ratios: tuple[int, ...] = (1, 2, 5, 10, 25, 50)
) -> pd.DataFrame:
    rows = []
    for ratio in ratios:
        for model, counts in model_counts.items():
            rows.append(
                {
                    "fn_to_fp_cost_ratio": ratio,
                    "model": model,
                    "false_negatives": counts["fn"],
                    "false_positives": counts["fp"],
                    "hypothetical_cost": ratio * counts["fn"] + counts["fp"],
                }
            )
    return pd.DataFrame(rows)
