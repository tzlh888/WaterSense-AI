"""Data and nested-CV readiness checks for WaterSense Phase 2B-0.

The functions in this module validate data and construct fold indices.  They do
not import, fit, score, or select prediction models.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from io import StringIO
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold


LOW_DO_THRESHOLD_MG_L = 4.0
NESTED_CV_SEED = 20_261_012
OUTER_FOLDS = 5
INNER_FOLDS = 4

EXPECTED_RAW_SHA256 = "a5ce02d9ab3703edc4279c8dc5f9d38a593b92c555945c5cdb2ab3ca55632632"
EXPECTED_PROCESSED_SHA256 = "5685c2c352b1cc9502cd664736d85295580127016fb60bdca45c082c5d031761"
EXPECTED_AUDIT_SHA256 = "da6a408003ad98a23887596eecfbc329fb3c370f936a2cb63237d3bc27b0174d"
EXPECTED_SPLIT_SHA256 = "b42814782f7290ab73faece96634c7a65448912ea40891f3c9a714b157594229"

EXPECTED_RAW_ROWS = 178_680
EXPECTED_RAW_STATIONS = 1_311
EXPECTED_PROCESSED_ROWS = 151_031
EXPECTED_PROCESSED_STATIONS = 840
EXPECTED_DEVELOPMENT_ROWS = 119_690
EXPECTED_DEVELOPMENT_STATIONS = 672
EXPECTED_LEGACY_TEST_ROWS = 31_341
EXPECTED_LEGACY_TEST_STATIONS = 168

EXPECTED_RAW_COLUMNS = (
    "X", "Y", "OBJECTID", "StationCode", "OpenClosed", "DateClosed",
    "Location", "PrimaryBasin", "GridReference", "Easting", "Northing",
    "Depth", "Date", "Time", "Q_Alk", "ALK_mg_l_", "Q_BOD",
    "BOD_mg_l_", "Q_COND", "COND_US_CM_", "Q_DCu_µg_l_",
    "D_Cu_µg_l_", "Q_Fe", "D_FE_µg_l_", "Q_DO", "DO_mg_l_",
    "Q_NH4N", "NH4_N_mg_l_", "Q_NO2N", "NO2_N_mg_l_", "Q_NO3N",
    "NO3_N_mg_l_", "Q_PSOL", "P_SOL__mg_l_", "Q_pH", "PH_PHUNITS_",
    "Q_SS", "SS_mg_l_", "Q_ZnSOL", "ZNSOL_µg_l_",
)

EXPECTED_PROCESSED_COLUMNS = (
    "source_object_id", "station_code", "sample_date", "sample_year",
    "sample_month", "season", "dissolved_oxygen_mg_l", "bod_mg_l",
    "ammonia_n_mg_l", "nitrite_n_mg_l", "nitrate_n_mg_l",
    "soluble_reactive_phosphorus_mg_l", "ph", "alkalinity_mg_l",
    "conductivity_us_cm", "suspended_solids_mg_l", "bod_is_below_limit",
    "bod_is_above_limit", "ammonia_is_below_limit",
    "ammonia_is_above_limit", "nitrite_is_below_limit",
    "nitrite_is_above_limit", "nitrate_is_below_limit",
    "nitrate_is_above_limit", "phosphorus_is_below_limit",
    "phosphorus_is_above_limit", "alkalinity_is_below_limit",
    "alkalinity_is_above_limit", "suspended_solids_is_below_limit",
    "suspended_solids_is_above_limit", "day_of_year_sin",
    "day_of_year_cos",
)


class DataReadinessError(RuntimeError):
    """Raised when historical data identity or fold readiness fails closed."""


@dataclass(frozen=True)
class FoldCriteria:
    """Pre-model support gates frozen for every nested-CV partition."""

    validation_min_low_rows: int = 10
    validation_min_low_sites: int = 3
    validation_max_single_site_low_share: float = 0.50
    training_min_low_rows: int = 50
    training_min_low_sites: int = 10


@dataclass(frozen=True)
class NestedCVResult:
    """Site assignments, support table, and deterministic hashes."""

    site_assignments: pd.DataFrame
    fold_support: pd.DataFrame
    site_assignments_sha256: str
    outer_row_assignments_sha256: str
    inner_row_assignments_sha256: str
    qualified: bool


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_frame_sha256(data: pd.DataFrame, columns: Iterable[str]) -> str:
    """Hash a canonical LF-terminated CSV representation."""
    buffer = StringIO()
    data.loc[:, list(columns)].to_csv(buffer, index=False, lineterminator="\n")
    return hashlib.sha256(buffer.getvalue().encode("utf-8")).hexdigest()


def low_do_mask(values: pd.Series) -> pd.Series:
    """Return the frozen low-DO label; equality at 4 mg/L is not positive."""
    if values.isna().any():
        raise DataReadinessError("Low-DO labels cannot be computed with missing targets")
    if not is_numeric_dtype(values):
        raise DataReadinessError("Low-DO labels require a numeric target")
    return values.lt(LOW_DO_THRESHOLD_MG_L)


def require_exact_columns(
    data: pd.DataFrame, expected: Iterable[str], *, label: str
) -> None:
    observed = tuple(data.columns)
    expected_tuple = tuple(expected)
    if observed != expected_tuple:
        missing = [column for column in expected_tuple if column not in observed]
        extra = [column for column in observed if column not in expected_tuple]
        raise DataReadinessError(
            f"{label} schema mismatch; missing={missing}, extra={extra}, "
            f"order_matches={set(observed) == set(expected_tuple)}"
        )


def validate_raw_data(data: pd.DataFrame) -> dict[str, object]:
    """Validate the exact historical raw-table schema and identifiers."""
    require_exact_columns(data, EXPECTED_RAW_COLUMNS, label="raw data")
    if len(data) != EXPECTED_RAW_ROWS:
        raise DataReadinessError(
            f"Raw row count is {len(data)}, expected {EXPECTED_RAW_ROWS}"
        )
    if data["StationCode"].nunique() != EXPECTED_RAW_STATIONS:
        raise DataReadinessError("Raw station count does not match historical evidence")
    if data["OBJECTID"].isna().any() or not data["OBJECTID"].is_unique:
        raise DataReadinessError("Raw OBJECTID must be complete and unique")
    if data["StationCode"].isna().any():
        raise DataReadinessError("Raw StationCode contains missing values")
    parsed_dates = pd.to_datetime(data["Date"], format="%Y/%m/%d", errors="coerce")
    if parsed_dates.isna().any():
        raise DataReadinessError("Raw sample dates contain unparseable values")
    if not is_numeric_dtype(data["DO_mg_l_"]):
        raise DataReadinessError("Raw dissolved oxygen target is not numeric")
    return {
        "rows": int(len(data)),
        "columns": int(len(data.columns)),
        "stations": int(data["StationCode"].nunique()),
        "unique_object_ids": int(data["OBJECTID"].nunique()),
        "exact_duplicate_rows": int(data.duplicated().sum()),
        "duplicate_station_date_time": int(
            data.duplicated(["StationCode", "Date", "Time"]).sum()
        ),
        "first_date": parsed_dates.min().date().isoformat(),
        "last_date": parsed_dates.max().date().isoformat(),
        "target": "DO_mg_l_",
        "target_unit": "mg/L",
        "target_missing_rows": int(data["DO_mg_l_"].isna().sum()),
        "target_qualified_rows": int(
            (data["DO_mg_l_"].notna() & data["Q_DO"].notna()).sum()
        ),
    }


def validate_processed_data(
    data: pd.DataFrame,
    *,
    expected_rows: int = EXPECTED_PROCESSED_ROWS,
    expected_stations: int = EXPECTED_PROCESSED_STATIONS,
) -> dict[str, object]:
    """Validate row identity, target and schema of a modelling table."""
    require_exact_columns(data, EXPECTED_PROCESSED_COLUMNS, label="processed data")
    if len(data) != expected_rows:
        raise DataReadinessError(
            f"Processed row count is {len(data)}, expected {expected_rows}"
        )
    if data["station_code"].nunique() != expected_stations:
        raise DataReadinessError(
            "Processed station count does not match the expected value"
        )
    if data["source_object_id"].isna().any() or not data["source_object_id"].is_unique:
        raise DataReadinessError("source_object_id must be complete and unique")
    if data["station_code"].isna().any():
        raise DataReadinessError("station_code contains missing values")
    if data["dissolved_oxygen_mg_l"].isna().any():
        raise DataReadinessError("Processed target contains missing values")
    if not is_numeric_dtype(data["dissolved_oxygen_mg_l"]):
        raise DataReadinessError("Processed dissolved oxygen target is not numeric")
    parsed_dates = pd.to_datetime(data["sample_date"], errors="coerce")
    if parsed_dates.isna().any():
        raise DataReadinessError("Processed sample dates contain unparseable values")
    return {
        "rows": int(len(data)),
        "columns": int(len(data.columns)),
        "stations": int(data["station_code"].nunique()),
        "unique_source_object_ids": int(data["source_object_id"].nunique()),
        "exact_duplicate_rows": int(data.duplicated().sum()),
        "duplicate_station_date_rows": int(
            data.duplicated(["station_code", "sample_date"]).sum()
        ),
        "target": "dissolved_oxygen_mg_l",
        "target_unit": "mg/L",
        "low_do_definition": f"dissolved_oxygen_mg_l < {LOW_DO_THRESHOLD_MG_L:g}",
        "low_do_rows": int(low_do_mask(data["dissolved_oxygen_mg_l"]).sum()),
        "low_do_sites": int(
            data.loc[
                low_do_mask(data["dissolved_oxygen_mg_l"]),
                "station_code",
            ].nunique()
        ),
    }


def audit_development_partition(
    processed: pd.DataFrame,
    membership: pd.DataFrame,
    *,
    expected_development_rows: int = EXPECTED_DEVELOPMENT_ROWS,
    expected_development_stations: int = EXPECTED_DEVELOPMENT_STATIONS,
    expected_test_rows: int = EXPECTED_LEGACY_TEST_ROWS,
    expected_test_stations: int = EXPECTED_LEGACY_TEST_STATIONS,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Verify the historical grouped membership and return development rows."""
    required = {"source_object_id", "station_code", "sample_date", "partition"}
    missing = sorted(required.difference(membership.columns))
    if missing:
        raise DataReadinessError(f"Split membership is missing columns: {missing}")
    if membership["source_object_id"].duplicated().any():
        raise DataReadinessError("Split membership contains duplicate source IDs")
    if set(membership["partition"]) != {"train", "test"}:
        raise DataReadinessError("Split membership must contain only train and test")

    merged = processed.merge(
        membership[list(required)],
        on=["source_object_id", "station_code", "sample_date"],
        how="outer",
        indicator=True,
        validate="one_to_one",
    )
    if not merged["_merge"].eq("both").all():
        counts = merged["_merge"].value_counts().to_dict()
        raise DataReadinessError(f"Processed/split identity mismatch: {counts}")
    merged = merged.drop(columns="_merge")
    development = merged.loc[merged["partition"].eq("train")].copy()
    legacy_test = merged.loc[merged["partition"].eq("test")].copy()
    observed = (
        len(development),
        development["station_code"].nunique(),
        len(legacy_test),
        legacy_test["station_code"].nunique(),
    )
    expected = (
        expected_development_rows,
        expected_development_stations,
        expected_test_rows,
        expected_test_stations,
    )
    if observed != expected:
        raise DataReadinessError(
            f"Historical partition counts differ: observed={observed}, expected={expected}"
        )
    overlap = sorted(
        set(development["station_code"]) & set(legacy_test["station_code"])
    )
    if overlap:
        raise DataReadinessError(
            f"Development and legacy test share {len(overlap)} stations"
        )

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_index, test_index = next(
        splitter.split(processed, groups=processed["station_code"])
    )
    reconstructed_train_ids = set(processed.iloc[train_index]["source_object_id"])
    reconstructed_test_ids = set(processed.iloc[test_index]["source_object_id"])
    saved_train_ids = set(development["source_object_id"])
    saved_test_ids = set(legacy_test["source_object_id"])
    if reconstructed_train_ids != saved_train_ids or reconstructed_test_ids != saved_test_ids:
        raise DataReadinessError(
            "Seed-42 GroupShuffleSplit does not reproduce saved row membership"
        )

    development = development.sort_values("source_object_id").reset_index(drop=True)
    low = low_do_mask(development["dissolved_oxygen_mg_l"])
    return development, {
        "development_rows": int(len(development)),
        "development_stations": int(development["station_code"].nunique()),
        "legacy_test_rows": int(len(legacy_test)),
        "legacy_test_stations": int(legacy_test["station_code"].nunique()),
        "station_overlap": 0,
        "development_unique_source_ids": int(
            development["source_object_id"].nunique()
        ),
        "legacy_test_unique_source_ids": int(
            legacy_test["source_object_id"].nunique()
        ),
        "development_low_do_rows": int(low.sum()),
        "development_low_do_sites": int(
            development.loc[low, "station_code"].nunique()
        ),
        "development_low_do_fraction": float(low.mean()),
        "saved_membership_matches_seed42_group_split": True,
    }


def _support_row(
    data: pd.DataFrame,
    *,
    level: str,
    outer_fold: int,
    inner_fold: int | None,
    role: str,
    counterpart_site_overlap: int,
    development_low_fraction: float,
    criteria: FoldCriteria,
) -> dict[str, object]:
    low = low_do_mask(data["dissolved_oxygen_mg_l"])
    low_rows = int(low.sum())
    low_sites = int(data.loc[low, "station_code"].nunique())
    if low_rows:
        maximum_share = float(
            data.loc[low].groupby("station_code").size().max() / low_rows
        )
    else:
        maximum_share = float("nan")
    reasons: list[str] = []
    if counterpart_site_overlap:
        reasons.append("station_overlap")
    if data["dissolved_oxygen_mg_l"].isna().any():
        reasons.append("missing_target")
    if role == "validation":
        if low_rows < criteria.validation_min_low_rows:
            reasons.append("too_few_low_rows")
        if low_sites < criteria.validation_min_low_sites:
            reasons.append("too_few_low_sites")
        if np.isfinite(maximum_share) and (
            maximum_share > criteria.validation_max_single_site_low_share
        ):
            reasons.append("single_site_dominates_low_support")
    else:
        if low_rows < criteria.training_min_low_rows:
            reasons.append("too_few_training_low_rows")
        if low_sites < criteria.training_min_low_sites:
            reasons.append("too_few_training_low_sites")
    low_fraction = float(low.mean())
    return {
        "level": level,
        "outer_fold": outer_fold,
        "inner_fold": inner_fold if inner_fold is not None else pd.NA,
        "role": role,
        "rows": int(len(data)),
        "sites": int(data["station_code"].nunique()),
        "low_do_rows": low_rows,
        "low_do_sites": low_sites,
        "low_do_fraction": low_fraction,
        "low_fraction_vs_development": float(
            low_fraction / development_low_fraction
        ),
        "max_single_site_low_share": maximum_share,
        "counterpart_site_overlap": int(counterpart_site_overlap),
        "qualified": not reasons,
        "failure_reasons": ";".join(reasons),
    }


def generate_nested_site_folds(
    development: pd.DataFrame,
    *,
    outer_folds: int = OUTER_FOLDS,
    inner_folds: int = INNER_FOLDS,
    seed: int = NESTED_CV_SEED,
    criteria: FoldCriteria | None = None,
    fail_on_unqualified: bool = True,
) -> NestedCVResult:
    """Generate deterministic stratified site-grouped outer and inner folds."""
    criteria = criteria or FoldCriteria()
    required = {
        "source_object_id",
        "station_code",
        "dissolved_oxygen_mg_l",
    }
    missing = sorted(required.difference(development.columns))
    if missing:
        raise DataReadinessError(f"Development data missing columns: {missing}")
    if development.empty:
        raise DataReadinessError("Development data are empty")
    if development["source_object_id"].duplicated().any():
        raise DataReadinessError("Development source IDs are not unique")
    if development[list(required)].isna().any().any():
        raise DataReadinessError("Development identity/group/target contains missing data")

    ordered = development.sort_values("source_object_id").reset_index(drop=True)
    y = low_do_mask(ordered["dissolved_oxygen_mg_l"]).astype(int)
    development_low_fraction = float(y.mean())
    if not y.any():
        raise DataReadinessError("Development data contain no low-DO observations")
    if ordered.loc[y.eq(1), "station_code"].nunique() < outer_folds:
        raise DataReadinessError("Too few low-DO sites for the requested outer folds")

    site_assignment_rows: list[dict[str, object]] = []
    support_rows: list[dict[str, object]] = []
    outer_row_rows: list[pd.DataFrame] = []
    inner_row_rows: list[pd.DataFrame] = []
    outer_splitter = StratifiedGroupKFold(
        n_splits=outer_folds, shuffle=True, random_state=seed
    )
    outer_splits = list(
        outer_splitter.split(ordered, y, groups=ordered["station_code"])
    )
    for outer_number, (outer_train_index, outer_validation_index) in enumerate(
        outer_splits, start=1
    ):
        outer_train = ordered.iloc[outer_train_index].copy()
        outer_validation = ordered.iloc[outer_validation_index].copy()
        train_sites = set(outer_train["station_code"])
        validation_sites = set(outer_validation["station_code"])
        overlap = len(train_sites & validation_sites)
        for station in sorted(validation_sites):
            site_assignment_rows.append(
                {
                    "level": "outer",
                    "outer_fold": 0,
                    "station_code": station,
                    "validation_fold": outer_number,
                }
            )
        outer_row_rows.append(
            outer_validation[
                ["source_object_id", "station_code"]
            ].assign(outer_validation_fold=outer_number)
        )
        support_rows.extend(
            [
                _support_row(
                    outer_train,
                    level="outer",
                    outer_fold=outer_number,
                    inner_fold=None,
                    role="train",
                    counterpart_site_overlap=overlap,
                    development_low_fraction=development_low_fraction,
                    criteria=criteria,
                ),
                _support_row(
                    outer_validation,
                    level="outer",
                    outer_fold=outer_number,
                    inner_fold=None,
                    role="validation",
                    counterpart_site_overlap=overlap,
                    development_low_fraction=development_low_fraction,
                    criteria=criteria,
                ),
            ]
        )

        inner_y = low_do_mask(outer_train["dissolved_oxygen_mg_l"]).astype(int)
        if outer_train.loc[inner_y.eq(1), "station_code"].nunique() < inner_folds:
            raise DataReadinessError(
                f"Outer fold {outer_number} has too few low-DO sites for inner CV"
            )
        inner_splitter = StratifiedGroupKFold(
            n_splits=inner_folds,
            shuffle=True,
            random_state=seed + outer_number,
        )
        for inner_number, (inner_train_index, inner_validation_index) in enumerate(
            inner_splitter.split(
                outer_train, inner_y, groups=outer_train["station_code"]
            ),
            start=1,
        ):
            inner_train = outer_train.iloc[inner_train_index].copy()
            inner_validation = outer_train.iloc[inner_validation_index].copy()
            inner_train_sites = set(inner_train["station_code"])
            inner_validation_sites = set(inner_validation["station_code"])
            inner_overlap = len(inner_train_sites & inner_validation_sites)
            for station in sorted(inner_validation_sites):
                site_assignment_rows.append(
                    {
                        "level": "inner",
                        "outer_fold": outer_number,
                        "station_code": station,
                        "validation_fold": inner_number,
                    }
                )
            inner_row_rows.append(
                outer_train.iloc[inner_validation_index][
                    ["source_object_id", "station_code"]
                ].assign(
                    outer_fold=outer_number,
                    inner_validation_fold=inner_number,
                )
            )
            support_rows.extend(
                [
                    _support_row(
                        inner_train,
                        level="inner",
                        outer_fold=outer_number,
                        inner_fold=inner_number,
                        role="train",
                        counterpart_site_overlap=inner_overlap,
                        development_low_fraction=development_low_fraction,
                        criteria=criteria,
                    ),
                    _support_row(
                        inner_validation,
                        level="inner",
                        outer_fold=outer_number,
                        inner_fold=inner_number,
                        role="validation",
                        counterpart_site_overlap=inner_overlap,
                        development_low_fraction=development_low_fraction,
                        criteria=criteria,
                    ),
                ]
            )

    assignments = pd.DataFrame(site_assignment_rows).sort_values(
        ["level", "outer_fold", "validation_fold", "station_code"]
    ).reset_index(drop=True)
    support = pd.DataFrame(support_rows).sort_values(
        ["level", "outer_fold", "inner_fold", "role"], na_position="first"
    ).reset_index(drop=True)
    outer_rows = pd.concat(outer_row_rows, ignore_index=True).sort_values(
        "source_object_id"
    )
    inner_rows = pd.concat(inner_row_rows, ignore_index=True).sort_values(
        ["outer_fold", "source_object_id"]
    )
    assignment_hash = canonical_frame_sha256(assignments, assignments.columns)
    outer_hash = canonical_frame_sha256(outer_rows, outer_rows.columns)
    inner_hash = canonical_frame_sha256(inner_rows, inner_rows.columns)
    qualified = bool(support["qualified"].all())
    if fail_on_unqualified and not qualified:
        failures = support.loc[
            ~support["qualified"],
            ["level", "outer_fold", "inner_fold", "role", "failure_reasons"],
        ].to_dict("records")
        raise DataReadinessError(f"Nested-CV support gates failed: {failures}")
    return NestedCVResult(
        site_assignments=assignments,
        fold_support=support,
        site_assignments_sha256=assignment_hash,
        outer_row_assignments_sha256=outer_hash,
        inner_row_assignments_sha256=inner_hash,
        qualified=qualified,
    )


def criteria_as_dict(criteria: FoldCriteria) -> dict[str, object]:
    return asdict(criteria)
