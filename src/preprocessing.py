"""Data loading, splitting, and leakage-safe preprocessing utilities.

The preprocessing transformer returned here is deliberately *not* fitted.
It should be placed inside a scikit-learn Pipeline so that it learns imputation,
scaling, and encoding parameters from training data only.
"""

from __future__ import annotations

import re
from math import ceil
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TaskType = Literal["classification", "regression"]

# Phase 3 water-quality experiment schema. Metadata is retained for splitting and
# error analysis but is deliberately absent from BASELINE_FEATURES.
WATER_QUALITY_TARGET = "dissolved_oxygen_mg_l"
WATER_QUALITY_GROUP = "station_code"
WATER_QUALITY_MEASUREMENT_FEATURES = [
    "bod_mg_l",
    "ammonia_n_mg_l",
    "nitrite_n_mg_l",
    "nitrate_n_mg_l",
    "soluble_reactive_phosphorus_mg_l",
    "ph",
]
WATER_QUALITY_CENSOR_FEATURES = [
    "bod_is_below_limit",
    "bod_is_above_limit",
    "ammonia_is_below_limit",
    "ammonia_is_above_limit",
    "nitrite_is_below_limit",
    "nitrite_is_above_limit",
    "nitrate_is_below_limit",
    "nitrate_is_above_limit",
    "phosphorus_is_below_limit",
    "phosphorus_is_above_limit",
]
WATER_QUALITY_BASELINE_FEATURES = (
    WATER_QUALITY_MEASUREMENT_FEATURES + WATER_QUALITY_CENSOR_FEATURES
)
WATER_QUALITY_EXTENDED_MEASUREMENT_FEATURES = [
    "alkalinity_mg_l",
    "conductivity_us_cm",
    "suspended_solids_mg_l",
]
WATER_QUALITY_EXTENDED_CENSOR_FEATURES = [
    "alkalinity_is_below_limit",
    "alkalinity_is_above_limit",
    "suspended_solids_is_below_limit",
    "suspended_solids_is_above_limit",
]
WATER_QUALITY_TEMPORAL_FEATURES = ["day_of_year_sin", "day_of_year_cos"]
WATER_QUALITY_FEATURE_SETS = {
    "A_core_chemistry": WATER_QUALITY_BASELINE_FEATURES,
    "B_extended_chemistry": (
        WATER_QUALITY_BASELINE_FEATURES
        + WATER_QUALITY_EXTENDED_MEASUREMENT_FEATURES
        + WATER_QUALITY_EXTENDED_CENSOR_FEATURES
    ),
    "C_core_plus_temporal": (
        WATER_QUALITY_BASELINE_FEATURES + WATER_QUALITY_TEMPORAL_FEATURES
    ),
    "D_extended_plus_temporal": (
        WATER_QUALITY_BASELINE_FEATURES
        + WATER_QUALITY_EXTENDED_MEASUREMENT_FEATURES
        + WATER_QUALITY_EXTENDED_CENSOR_FEATURES
        + WATER_QUALITY_TEMPORAL_FEATURES
    ),
}

_RAW_REQUIRED_COLUMNS = {
    "OBJECTID",
    "StationCode",
    "Date",
    "DO_mg_l_",
    "Q_DO",
    "BOD_mg_l_",
    "Q_BOD",
    "NH4_N_mg_l_",
    "Q_NH4N",
    "NO2_N_mg_l_",
    "Q_NO2N",
    "NO3_N_mg_l_",
    "Q_NO3N",
    "P_SOL__mg_l_",
    "Q_PSOL",
    "PH_PHUNITS_",
    "Q_pH",
    "Q_Alk",
    "ALK_mg_l_",
    "Q_COND",
    "COND_US_CM_",
    "Q_SS",
    "SS_mg_l_",
}

_MEASUREMENT_RENAMES = {
    "BOD_mg_l_": "bod_mg_l",
    "NH4_N_mg_l_": "ammonia_n_mg_l",
    "NO2_N_mg_l_": "nitrite_n_mg_l",
    "NO3_N_mg_l_": "nitrate_n_mg_l",
    "P_SOL__mg_l_": "soluble_reactive_phosphorus_mg_l",
    "PH_PHUNITS_": "ph",
    "ALK_mg_l_": "alkalinity_mg_l",
    "COND_US_CM_": "conductivity_us_cm",
    "SS_mg_l_": "suspended_solids_mg_l",
}

_CENSOR_COLUMNS = {
    "bod": "Q_BOD",
    "ammonia": "Q_NH4N",
    "nitrite": "Q_NO2N",
    "nitrate": "Q_NO3N",
    "phosphorus": "Q_PSOL",
    "alkalinity": "Q_Alk",
    "suspended_solids": "Q_SS",
}


def load_data(path: str | Path) -> pd.DataFrame:
    """Load a CSV dataset without changing the source file.

    Args:
        path: Path to a CSV file.

    Raises:
        FileNotFoundError: If ``path`` does not point to a file.
        ValueError: If the file is not a CSV file or contains no rows.
    """
    dataset_path = Path(path)
    if not dataset_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    if dataset_path.suffix.lower() != ".csv":
        raise ValueError("This baseline framework currently supports CSV files only.")

    data = pd.read_csv(dataset_path)
    if data.empty:
        raise ValueError(f"Dataset contains no observations: {dataset_path}")
    return data


def normalise_column_name(name: object) -> str:
    """Convert one column name to a consistent lowercase snake_case form."""
    cleaned = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip().lower())
    return cleaned.strip("_")


def clean_column_names(data: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with normalised, non-empty, unique column names."""
    cleaned = data.copy()
    new_names = [normalise_column_name(column) for column in cleaned.columns]

    if any(not name for name in new_names):
        raise ValueError("At least one column name becomes empty after normalisation.")
    duplicates = pd.Index(new_names)[pd.Index(new_names).duplicated()].unique().tolist()
    if duplicates:
        raise ValueError(
            "Column-name normalisation creates duplicates: " + ", ".join(duplicates)
        )

    cleaned.columns = new_names
    return cleaned


def split_features_target(
    data: pd.DataFrame, target_column: str
) -> tuple[pd.DataFrame, pd.Series]:
    """Separate predictors and target, rejecting missing target values.

    Missing feature values may be handled by the fitted preprocessing pipeline.
    Missing targets are rejected because silently dropping them can hide a data
    quality problem and change the study population.
    """
    if target_column not in data.columns:
        raise KeyError(
            f"Target column '{target_column}' was not found. "
            f"Available columns: {list(data.columns)}"
        )

    target = data[target_column]
    if target.isna().any():
        raise ValueError(
            f"Target column '{target_column}' contains {int(target.isna().sum())} "
            "missing values. Decide and document how these rows should be handled."
        )

    features = data.drop(columns=[target_column])
    if features.shape[1] == 0:
        raise ValueError("The dataset has no predictor columns after removing the target.")
    return features, target


def identify_feature_types(features: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Return numeric and categorical feature column names.

    Datetime and other unsupported dtypes are treated as categorical so the
    baseline remains transparent. Dataset-specific feature engineering should be
    added only after those variables have been understood.
    """
    numeric_columns = features.select_dtypes(include="number").columns.tolist()
    categorical_columns = [
        column for column in features.columns if column not in numeric_columns
    ]
    return numeric_columns, categorical_columns


def build_preprocessor(features: pd.DataFrame) -> ColumnTransformer:
    """Build an unfitted transformer for numeric and categorical predictors."""
    numeric_columns, categorical_columns = identify_feature_types(features)
    transformers: list[tuple[str, Pipeline, list[str]]] = []

    if numeric_columns:
        numeric_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        transformers.append(("numeric", numeric_pipeline, numeric_columns))

    if categorical_columns:
        categorical_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                (
                    "one_hot",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ),
            ]
        )
        transformers.append(("categorical", categorical_pipeline, categorical_columns))

    if not transformers:
        raise ValueError("No usable predictor columns were identified.")

    return ColumnTransformer(transformers=transformers, remainder="drop")


def split_data(
    features: pd.DataFrame,
    target: pd.Series,
    task: TaskType,
    *,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Create a reproducible train/test split.

    Classification is stratified when every class has at least two observations.
    If stratification is impossible, the split still runs; evaluation should then
    explicitly check which classes are represented in the test set.
    """
    if task not in {"classification", "regression"}:
        raise ValueError("task must be either 'classification' or 'regression'.")

    stratify = None
    if task == "classification":
        class_count = target.nunique(dropna=False)
        test_rows = ceil(len(target) * test_size)
        train_rows = len(target) - test_rows
        enough_per_class = target.value_counts(dropna=False).min() >= 2
        if enough_per_class and test_rows >= class_count and train_rows >= class_count:
            stratify = target

    return train_test_split(
        features,
        target,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )


def load_niea_raw(path: str | Path) -> pd.DataFrame:
    """Load the unchanged NIEA CSV while recognising blank source fields.

    The UTF-8 signature is removed from the first header. Whitespace-only cells
    are interpreted as missing in memory; the source file is never rewritten.
    """
    dataset_path = Path(path)
    if not dataset_path.is_file():
        raise FileNotFoundError(f"NIEA raw dataset not found: {dataset_path}")
    return pd.read_csv(
        dataset_path,
        encoding="utf-8-sig",
        na_values=[" ", ""],
        low_memory=False,
    )


def prepare_water_quality_modeling_data(
    raw_data: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Create the Phase 3 modelling table without modifying ``raw_data``.

    Rows with a missing target or any target qualifier are excluded. Predictor
    numeric values are preserved as exported, and separate below-/above-limit
    flags retain censoring information. Missing predictors remain missing for a
    training-only imputer inside the model pipeline.
    """
    missing_columns = sorted(_RAW_REQUIRED_COLUMNS - set(raw_data.columns))
    if missing_columns:
        raise ValueError(f"Raw dataset is missing required columns: {missing_columns}")

    sample_dates = pd.to_datetime(raw_data["Date"], format="%Y/%m/%d", errors="coerce")
    if sample_dates.isna().any():
        raise ValueError(
            f"{int(sample_dates.isna().sum())} sampling dates could not be parsed."
        )

    target_missing = raw_data["DO_mg_l_"].isna()
    target_qualified = raw_data["Q_DO"].notna()
    eligible = ~(target_missing | target_qualified)

    processed = pd.DataFrame(
        {
            "source_object_id": raw_data.loc[eligible, "OBJECTID"].astype(int),
            WATER_QUALITY_GROUP: raw_data.loc[eligible, "StationCode"].astype(str),
            "sample_date": sample_dates.loc[eligible].dt.strftime("%Y-%m-%d"),
            "sample_year": sample_dates.loc[eligible].dt.year.astype(int),
            "sample_month": sample_dates.loc[eligible].dt.month.astype(int),
            "season": sample_dates.loc[eligible].dt.month.map(
                {
                    12: "winter", 1: "winter", 2: "winter",
                    3: "spring", 4: "spring", 5: "spring",
                    6: "summer", 7: "summer", 8: "summer",
                    9: "autumn", 10: "autumn", 11: "autumn",
                }
            ),
            WATER_QUALITY_TARGET: pd.to_numeric(
                raw_data.loc[eligible, "DO_mg_l_"], errors="raise"
            ),
        }
    )

    for raw_column, processed_column in _MEASUREMENT_RENAMES.items():
        processed[processed_column] = pd.to_numeric(
            raw_data.loc[eligible, raw_column], errors="coerce"
        )

    for feature_prefix, qualifier_column in _CENSOR_COLUMNS.items():
        qualifiers = raw_data.loc[eligible, qualifier_column]
        processed[f"{feature_prefix}_is_below_limit"] = qualifiers.eq("<").astype(int)
        processed[f"{feature_prefix}_is_above_limit"] = qualifiers.eq(">").astype(int)

    day_of_year = sample_dates.loc[eligible].dt.dayofyear.astype(float)
    processed["day_of_year_sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
    processed["day_of_year_cos"] = np.cos(2 * np.pi * day_of_year / 365.25)

    processed = processed.reset_index(drop=True)
    complete_case_rows = int(
        processed[WATER_QUALITY_MEASUREMENT_FEATURES].notna().all(axis=1).sum()
    )
    audit = {
        "raw_rows": int(len(raw_data)),
        "missing_target_rows_excluded": int(target_missing.sum()),
        "qualified_target_rows_excluded": int((~target_missing & target_qualified).sum()),
        "processed_rows": int(len(processed)),
        "processed_stations": int(processed[WATER_QUALITY_GROUP].nunique()),
        "complete_case_rows": complete_case_rows,
        "complete_case_percent_of_processed": float(
            complete_case_rows / len(processed) * 100
        ),
        "feature_missing_counts": {
            column: int(processed[column].isna().sum())
            for column in WATER_QUALITY_MEASUREMENT_FEATURES
        },
        "extended_feature_missing_counts": {
            column: int(processed[column].isna().sum())
            for column in WATER_QUALITY_EXTENDED_MEASUREMENT_FEATURES
        },
        "extended_feature_censor_counts": {
            column: int(processed[column].sum())
            for column in WATER_QUALITY_EXTENDED_CENSOR_FEATURES
        },
        "temperature_field_available": False,
        "transformations": [
            "Excluded rows with missing dissolved-oxygen target.",
            "Excluded rows with any dissolved-oxygen target qualifier.",
            "Parsed sample date and derived sample year.",
            "Derived month, season, and cyclical day-of-year context from sample date.",
            "Renamed selected core chemistry columns for modelling.",
            "Preserved predictor numeric values exactly as exported.",
            "Added separate below-limit and above-limit flags for qualified predictors.",
            "Retained predictor missing values for training-only median imputation.",
        ],
    }
    return processed, audit


def build_water_quality_preprocessor() -> ColumnTransformer:
    """Build the unfitted Phase 3 transformer.

    Measurement medians and missingness indicators are learned from training
    rows only. Explicit censoring flags pass through unchanged.
    """
    measurement_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scaler", StandardScaler()),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("measurements", measurement_pipeline, WATER_QUALITY_MEASUREMENT_FEATURES),
            ("censor_flags", "passthrough", WATER_QUALITY_CENSOR_FEATURES),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def build_water_quality_feature_preprocessor(
    feature_columns: list[str],
) -> ColumnTransformer:
    """Build an unfitted numeric Phase 4 transformer for one feature set.

    Measurements and temporal context receive training-only median imputation,
    missingness indicators, and scaling. Explicit qualifier flags pass through.
    """
    censor_columns = [
        column
        for column in feature_columns
        if column.endswith("_is_below_limit") or column.endswith("_is_above_limit")
    ]
    numeric_columns = [
        column for column in feature_columns if column not in censor_columns
    ]
    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_columns,
            ),
            ("censor_flags", "passthrough", censor_columns),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def grouped_station_holdout(
    data: pd.DataFrame,
    *,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Return row indices for a station-disjoint grouped holdout."""
    splitter = GroupShuffleSplit(
        n_splits=1, test_size=test_size, random_state=random_state
    )
    train_indices, test_indices = next(
        splitter.split(data, groups=data[WATER_QUALITY_GROUP])
    )
    train_stations = set(data.iloc[train_indices][WATER_QUALITY_GROUP])
    test_stations = set(data.iloc[test_indices][WATER_QUALITY_GROUP])
    assert train_stations.isdisjoint(test_stations), "Station leakage detected."
    return train_indices, test_indices


def temporal_sensitivity_holdout(
    data: pd.DataFrame,
    *,
    test_start_year: int = 2019,
) -> tuple[np.ndarray, np.ndarray]:
    """Return earlier-year training and later-year sensitivity indices."""
    train_mask = data["sample_year"] < test_start_year
    test_mask = data["sample_year"] >= test_start_year
    if not train_mask.any() or not test_mask.any():
        raise ValueError("Temporal split must contain both training and test rows.")
    return np.flatnonzero(train_mask), np.flatnonzero(test_mask)
