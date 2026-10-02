"""Pure application logic for translating user measurements to model inputs."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


MEASUREMENT_FIELDS: tuple[dict[str, Any], ...] = (
    {"feature": "bod_mg_l", "label": "Biochemical oxygen demand (BOD)", "unit": "mg/L", "description": "An indicator of oxygen consumed by biological processes in water.", "censor_prefix": "bod", "qualifiers": ("exact", "below", "above")},
    {"feature": "ammonia_n_mg_l", "label": "Ammonia as nitrogen", "unit": "mg/L", "description": "Ammonia concentration reported as nitrogen.", "censor_prefix": "ammonia", "qualifiers": ("exact", "below", "above")},
    {"feature": "nitrite_n_mg_l", "label": "Nitrite as nitrogen", "unit": "mg/L", "description": "Nitrite concentration reported as nitrogen.", "censor_prefix": "nitrite", "qualifiers": ("exact", "below")},
    {"feature": "nitrate_n_mg_l", "label": "Nitrate as nitrogen", "unit": "mg/L", "description": "Nitrate concentration reported as nitrogen.", "censor_prefix": "nitrate", "qualifiers": ("exact", "below")},
    {"feature": "soluble_reactive_phosphorus_mg_l", "label": "Soluble reactive phosphorus", "unit": "mg/L", "description": "The source's soluble reactive phosphorus measurement.", "censor_prefix": "phosphorus", "qualifiers": ("exact", "below", "above")},
    {"feature": "ph", "label": "pH", "unit": "pH units", "description": "Acidity/alkalinity on the pH scale.", "censor_prefix": None, "qualifiers": ("exact",)},
    {"feature": "alkalinity_mg_l", "label": "Alkalinity", "unit": "mg/L", "description": "Alkalinity as reported in the source export.", "censor_prefix": "alkalinity", "qualifiers": ("exact", "below")},
    {"feature": "conductivity_us_cm", "label": "Conductivity", "unit": "µS/cm", "description": "Electrical conductivity of the sample.", "censor_prefix": None, "qualifiers": ("exact",)},
    {"feature": "suspended_solids_mg_l", "label": "Suspended solids", "unit": "mg/L", "description": "Material suspended in the water sample.", "censor_prefix": "suspended_solids", "qualifiers": ("exact", "below")},
)

QUALIFIER_LABELS = {
    "exact": "Exact measurement",
    "below": "Below reporting limit (<)",
    "above": "Above reporting limit (>)",
}

PERCENTILE_POSITION_COLUMNS: tuple[str, ...] = (
    "Measurement",
    "Entered value",
    "Unit",
    "Training percentile",
    "Observed minimum",
    "Observed maximum",
)


def cyclical_day_of_year(sample_date: date | datetime | pd.Timestamp) -> tuple[float, float]:
    """Reproduce the exact Phase 4 day-of-year transformation."""
    timestamp = pd.Timestamp(sample_date)
    if pd.isna(timestamp):
        raise ValueError("A valid sampling date is required.")
    day_of_year = float(timestamp.dayofyear)
    angle = 2 * np.pi * day_of_year / 365.25
    return float(np.sin(angle)), float(np.cos(angle))


def validate_measurement_value(feature: str, value: float | None) -> None:
    """Reject non-finite and mathematically impossible inputs, not risk levels."""
    if value is None or pd.isna(value):
        return
    numeric = float(value)
    if not np.isfinite(numeric):
        raise ValueError(f"{feature} must be finite or marked unavailable.")
    if feature == "ph":
        if not 0 <= numeric <= 14:
            raise ValueError("pH must be within the mathematical 0–14 scale.")
    elif numeric < 0:
        raise ValueError(f"{feature} cannot be negative.")


def build_model_input(
    values: Mapping[str, float | None],
    qualifiers: Mapping[str, str],
    sample_date: date | datetime | pd.Timestamp,
    expected_features: Sequence[str],
) -> pd.DataFrame:
    """Translate public inputs into one row matching the saved artifact exactly."""
    row: dict[str, float] = {feature: 0.0 for feature in expected_features}
    for field in MEASUREMENT_FIELDS:
        feature = field["feature"]
        value = values.get(feature)
        validate_measurement_value(feature, value)
        row[feature] = np.nan if value is None or pd.isna(value) else float(value)
        prefix = field["censor_prefix"]
        qualifier = qualifiers.get(feature, "exact")
        if qualifier not in field["qualifiers"]:
            raise ValueError(f"Unsupported qualifier '{qualifier}' for {feature}.")
        if qualifier != "exact" and pd.isna(row[feature]):
            raise ValueError("A reporting-limit qualifier requires a numeric reported limit.")
        if prefix:
            row[f"{prefix}_is_below_limit"] = float(qualifier == "below")
            row[f"{prefix}_is_above_limit"] = float(qualifier == "above")

    day_sin, day_cos = cyclical_day_of_year(sample_date)
    row["day_of_year_sin"] = day_sin
    row["day_of_year_cos"] = day_cos

    expected = list(expected_features)
    if "dissolved_oxygen_mg_l" in expected or "Q_DO" in expected:
        raise ValueError("Target information must never be part of prediction input.")
    missing = sorted(set(expected) - set(row))
    unexpected = sorted(set(row) - set(expected))
    if missing or unexpected:
        raise ValueError(f"Application/model feature mismatch; missing={missing}, unexpected={unexpected}")
    return pd.DataFrame([[row[feature] for feature in expected]], columns=expected)


def training_range_warnings(
    model_row: pd.DataFrame, training_reference: pd.DataFrame
) -> list[dict[str, Any]]:
    """Flag entered measurements beyond observed model-training ranges."""
    warnings: list[dict[str, Any]] = []
    measurement_features = {field["feature"] for field in MEASUREMENT_FIELDS}
    for feature in measurement_features:
        value = model_row.iloc[0][feature]
        if pd.isna(value):
            continue
        observed = training_reference[feature].dropna()
        minimum, maximum = float(observed.min()), float(observed.max())
        if value < minimum or value > maximum:
            warnings.append({"feature": feature, "value": float(value), "minimum": minimum, "maximum": maximum})
    return warnings


def input_percentile_positions(
    model_row: pd.DataFrame, training_reference: pd.DataFrame
) -> pd.DataFrame:
    """Describe entered measurements relative to real training observations."""
    rows: list[dict[str, Any]] = []
    for field in MEASUREMENT_FIELDS:
        feature = field["feature"]
        value = model_row.iloc[0][feature]
        if pd.isna(value):
            continue
        observed = training_reference[feature].dropna()
        if observed.empty:
            continue
        percentile = float((observed <= value).mean() * 100)
        rows.append({
            "Measurement": field["label"],
            "Entered value": float(value),
            "Unit": field["unit"],
            "Training percentile": percentile,
            "Observed minimum": float(observed.min()),
            "Observed maximum": float(observed.max()),
        })
    return pd.DataFrame(rows, columns=PERCENTILE_POSITION_COLUMNS)


def format_percentile_positions(positions: pd.DataFrame) -> pd.DataFrame:
    """Format a valid percentile result without assuming that it has rows."""
    if positions.empty or not set(PERCENTILE_POSITION_COLUMNS).issubset(positions.columns):
        return pd.DataFrame(columns=PERCENTILE_POSITION_COLUMNS)

    display = positions.loc[:, PERCENTILE_POSITION_COLUMNS].copy()
    display["Training percentile"] = display["Training percentile"].map(
        lambda value: "Not available" if pd.isna(value) else f"{value:.1f}%"
    )
    return display
