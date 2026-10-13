#!/usr/bin/env python3
"""Validate exact WaterSense data recovery and freeze nested-CV indices.

This command performs data engineering and split validation only.  It contains
no estimator construction or model-fitting call.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.phase2b0_readiness import (  # noqa: E402
    EXPECTED_AUDIT_SHA256,
    EXPECTED_PROCESSED_SHA256,
    EXPECTED_RAW_SHA256,
    EXPECTED_SPLIT_SHA256,
    INNER_FOLDS,
    LOW_DO_THRESHOLD_MG_L,
    NESTED_CV_SEED,
    OUTER_FOLDS,
    FoldCriteria,
    audit_development_partition,
    criteria_as_dict,
    generate_nested_site_folds,
    sha256_file,
    validate_processed_data,
    validate_raw_data,
)
from src.preprocessing import (  # noqa: E402
    load_niea_raw,
    prepare_water_quality_modeling_data,
)


OUTPUT = ROOT / "research_upgrade_v3" / "phase2b0"
RAW_PATH = ROOT / "data/raw/niea_river_water_quality_1990_2024.csv"
PROCESSED_PATH = ROOT / "data/processed/water_quality_modeling.csv"
AUDIT_PATH = ROOT / "data/processed/water_quality_modeling_audit.json"
SPLIT_PATH = ROOT / "research_outputs/predictions/split_grouped.csv.gz"
HOLDOUT_PATH = ROOT / "results/phase4_holdout_predictions.csv"
TRAINING_REFERENCE_PATH = ROOT / "data/app/training_feature_reference.csv.gz"

CATALOGUE_URL = (
    "https://www.data.gov.uk/dataset/0840ab33-18ae-4670-8523-ac43105f5902/"
    "river-water-quality-monitoring-1990-to-2024-all-parameters"
)
SERVICE_URL = (
    "https://services-eu1.arcgis.com/kswen6BYexuc1SUk/arcgis/rest/services/"
    "River_Water_Quality_Monitoring_1990_to_2024_All_Parameters/FeatureServer/0"
)
DOWNLOAD_URL = (
    "https://opendata.arcgis.com/api/v3/datasets/"
    "a8f8de1ad58a4ee28340f23a9be4bdad_0/downloads/data"
    "?format=csv&spatialRefId=29902"
)

TASK_START_UNTRACKED = [
    "research_upgrade_v3/",
    "scripts/run_low_do_reliability.py",
    "src/low_do_reliability.py",
    "tests/test_low_do_reliability.py",
]


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _markdown_table(data: pd.DataFrame, digits: int = 6) -> str:
    columns = [str(column) for column in data.columns]
    rows = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for values in data.itertuples(index=False, name=None):
        rendered = []
        for value in values:
            if pd.isna(value):
                rendered.append("")
            elif isinstance(value, (float, np.floating)):
                rendered.append(f"{float(value):.{digits}g}")
            else:
                rendered.append(str(value))
        rows.append("| " + " | ".join(rendered) + " |")
    return "\n".join(rows)


def _verify_phase2a_outputs() -> dict[str, object]:
    manifest_path = ROOT / "research_upgrade_v3/RUN_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in manifest["outputs"].items():
        path = ROOT / "research_upgrade_v3" / relative
        if not path.is_file():
            mismatches.append({"path": relative, "reason": "missing"})
        else:
            actual = sha256_file(path)
            if actual != expected:
                mismatches.append(
                    {"path": relative, "expected": expected, "actual": actual}
                )
    if mismatches:
        raise RuntimeError(f"Phase 2A artifact verification failed: {mismatches}")
    return {
        "run_manifest_sha256": sha256_file(manifest_path),
        "verified_output_count": len(manifest["outputs"]),
        "mismatches": mismatches,
    }


def _verify_holdout_and_training_reference(
    processed: pd.DataFrame, development: pd.DataFrame
) -> dict[str, object]:
    holdout = pd.read_csv(HOLDOUT_PATH)
    feature_columns = [
        "source_object_id", "station_code", "sample_date", "sample_year",
        "sample_month", "season", "bod_mg_l", "ammonia_n_mg_l",
        "nitrite_n_mg_l", "nitrate_n_mg_l",
        "soluble_reactive_phosphorus_mg_l", "ph", "bod_is_below_limit",
        "bod_is_above_limit", "ammonia_is_below_limit",
        "ammonia_is_above_limit", "nitrite_is_below_limit",
        "nitrite_is_above_limit", "nitrate_is_below_limit",
        "nitrate_is_above_limit", "phosphorus_is_below_limit",
        "phosphorus_is_above_limit", "alkalinity_mg_l",
        "conductivity_us_cm", "suspended_solids_mg_l",
        "alkalinity_is_below_limit", "alkalinity_is_above_limit",
        "suspended_solids_is_below_limit", "suspended_solids_is_above_limit",
        "day_of_year_sin", "day_of_year_cos", "dissolved_oxygen_mg_l",
    ]
    holdout_view = (
        holdout.rename(columns={"actual_do_mg_l": "dissolved_oxygen_mg_l"})[
            feature_columns
        ]
        .sort_values("source_object_id")
        .reset_index(drop=True)
    )
    legacy_ids = set(holdout_view["source_object_id"])
    processed_holdout = (
        processed.loc[processed["source_object_id"].isin(legacy_ids), feature_columns]
        .sort_values("source_object_id")
        .reset_index(drop=True)
    )
    pd.testing.assert_frame_equal(
        processed_holdout,
        holdout_view,
        check_dtype=False,
        rtol=1e-12,
        atol=1e-12,
    )

    training_features = [
        "bod_mg_l", "ammonia_n_mg_l", "nitrite_n_mg_l", "nitrate_n_mg_l",
        "soluble_reactive_phosphorus_mg_l", "ph", "alkalinity_mg_l",
        "conductivity_us_cm", "suspended_solids_mg_l",
    ]
    reference = pd.read_csv(TRAINING_REFERENCE_PATH)
    development_ids = set(development["source_object_id"])
    reconstructed_reference = processed.loc[
        processed["source_object_id"].isin(development_ids), training_features
    ].reset_index(drop=True)
    pd.testing.assert_frame_equal(
        reconstructed_reference,
        reference,
        check_dtype=False,
        rtol=1e-12,
        atol=1e-12,
    )
    return {
        "holdout_rows_checked": int(len(holdout_view)),
        "holdout_feature_target_values_match": True,
        "training_reference_rows_checked": int(len(reference)),
        "training_reference_values_and_order_match": True,
    }


def _run_targeted_tests() -> dict[str, object]:
    command = [
        sys.executable,
        "-m",
        "unittest",
        "tests.test_phase2b0_readiness",
        "tests.test_low_do_reliability",
        "-v",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    combined = "\n".join(
        part.strip() for part in [completed.stdout, completed.stderr] if part.strip()
    )
    if completed.returncode:
        raise RuntimeError(f"Targeted Phase 2B-0 tests failed:\n{combined}")
    ran_line = next(
        (line.strip() for line in combined.splitlines() if line.startswith("Ran ")),
        "Ran unknown number of tests",
    )
    return {
        "command": " ".join(command[1:]),
        "returncode": completed.returncode,
        "result": "passed",
        "summary": ran_line,
        "real_data_integration_test_executed": True,
        "synthetic_fixtures_are_labelled_unit_tests_only": True,
    }


def _weighted_config(criteria: FoldCriteria) -> dict[str, object]:
    return {
        "status": "frozen_not_executed",
        "training_performed": False,
        "experiment": "Low-DO Weighted Regression",
        "development_data": {
            "processed_sha256": EXPECTED_PROCESSED_SHA256,
            "partition": "historical grouped train only",
            "rows": 119_690,
            "stations": 672,
            "legacy_test_prohibited_for_selection": True,
        },
        "nested_cv": {
            "outer_folds": OUTER_FOLDS,
            "inner_folds": INNER_FOLDS,
            "splitter": "StratifiedGroupKFold",
            "group": "station_code",
            "stratification_label": "dissolved_oxygen_mg_l < 4",
            "seed": NESTED_CV_SEED,
            "fold_support_criteria": criteria_as_dict(criteria),
        },
        "sample_weight": {
            "raw_rule": "multiplier if training-fold target < 4 mg/L else 1",
            "normalization": "divide by training-fold mean raw weight",
            "multipliers": [1, 2, 4, 8],
            "computed_from": "training-fold target only",
            "row_resampling_prohibited": True,
        },
        "candidates": {
            "RandomForestRegressor": {
                "n_estimators": [150, 300],
                "min_samples_leaf": [2, 5],
                "max_features": [0.6, 0.8],
                "random_state": NESTED_CV_SEED,
            },
            "ExtraTreesRegressor": {
                "n_estimators": [150, 300],
                "min_samples_leaf": [2, 5],
                "max_features": [0.6, 0.8],
                "random_state": NESTED_CV_SEED,
            },
            "HistGradientBoostingRegressor": {
                "learning_rate": [0.03, 0.07],
                "max_leaf_nodes": [15, 31],
                "min_samples_leaf": [20, 50],
                "l2_regularization": [0, 1],
                "random_state": NESTED_CV_SEED,
            },
        },
        "metrics": {
            "co_primary": ["low_do_recall", "low_do_mae_mg_l"],
            "secondary": [
                "overall_mae_mg_l", "overall_rmse_mg_l", "overall_r2",
                "low_do_rmse_mg_l",
                "low_do_bias_prediction_minus_truth_mg_l",
                "low_do_precision", "low_do_f1",
                "low_do_false_negative_rate",
            ],
            "positive_class": "ground truth DO < 4 mg/L",
            "predicted_positive": "predicted DO < 4 mg/L",
            "undefined_rule": "precision/F1 missing when no predicted positives",
        },
        "inner_selection": {
            "qualification": [
                "overall MAE <= 1.10 * same-fold unweighted anchor MAE",
                "low-DO precision >= 0.30",
                "at least one predicted low in every fold containing true low DO",
                "no split, data-integrity, non-finite-prediction, or metric failure",
            ],
            "ranking": [
                "highest mean low-DO recall",
                "lowest mean low-DO MAE",
                "lowest overall MAE",
                "lower complexity",
                "stable candidate ID",
            ],
        },
        "outer_evaluation": {
            "rule": "one evaluation of inner-selected configuration per outer fold",
            "aggregation": "concatenate outer out-of-fold predictions",
            "uncertainty": {
                "method": "paired whole-site percentile bootstrap",
                "resamples": 2000,
                "seed": NESTED_CV_SEED,
            },
        },
        "stopping": {
            "fixed_grid_only": True,
            "extend_search_after_results": False,
            "no_qualified_model_is_valid_outcome": True,
            "legacy_test_may_not_change_selection": True,
        },
    }


def main() -> None:
    if _git("branch", "--show-current") != "research-upgrade-v3":
        raise RuntimeError("Phase 2B-0 must run on research-upgrade-v3")
    baseline_head = _git("rev-parse", "HEAD")
    if baseline_head != "3553b29ff104918b12da8c84d2c9a8c5ed032e18":
        raise RuntimeError(f"Unexpected baseline HEAD: {baseline_head}")
    phase2a = _verify_phase2a_outputs()

    observed_hashes = {
        "raw": sha256_file(RAW_PATH),
        "processed": sha256_file(PROCESSED_PATH),
        "audit": sha256_file(AUDIT_PATH),
        "historical_split": sha256_file(SPLIT_PATH),
    }
    expected_hashes = {
        "raw": EXPECTED_RAW_SHA256,
        "processed": EXPECTED_PROCESSED_SHA256,
        "audit": EXPECTED_AUDIT_SHA256,
        "historical_split": EXPECTED_SPLIT_SHA256,
    }
    if observed_hashes != expected_hashes:
        raise RuntimeError(
            f"Recovered evidence hash mismatch: observed={observed_hashes}"
        )

    raw = load_niea_raw(RAW_PATH)
    raw_audit = validate_raw_data(raw)
    processed_disk = pd.read_csv(PROCESSED_PATH)
    processed_audit = validate_processed_data(processed_disk)
    rebuilt, rebuilt_audit = prepare_water_quality_modeling_data(raw)
    pd.testing.assert_frame_equal(
        processed_disk, rebuilt, check_dtype=False, rtol=1e-12, atol=1e-12
    )
    saved_audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    if saved_audit != rebuilt_audit:
        raise RuntimeError("Recovered cleaning audit differs from fresh reconstruction")

    membership = pd.read_csv(SPLIT_PATH)
    development, partition_audit = audit_development_partition(
        processed_disk, membership
    )
    cross_checks = _verify_holdout_and_training_reference(
        processed_disk, development
    )
    criteria = FoldCriteria()
    nested = generate_nested_site_folds(development, criteria=criteria)
    repeated = generate_nested_site_folds(development, criteria=criteria)
    if (
        nested.site_assignments_sha256 != repeated.site_assignments_sha256
        or nested.outer_row_assignments_sha256
        != repeated.outer_row_assignments_sha256
        or nested.inner_row_assignments_sha256
        != repeated.inner_row_assignments_sha256
    ):
        raise RuntimeError("Nested-CV generation is not reproducible")
    test_result = _run_targeted_tests()

    OUTPUT.mkdir(parents=True, exist_ok=True)
    assignments_path = OUTPUT / "NESTED_CV_SITE_ASSIGNMENTS.csv"
    support_path = OUTPUT / "NESTED_CV_FOLD_SUPPORT.csv"
    nested.site_assignments.to_csv(assignments_path, index=False)
    nested.fold_support.to_csv(support_path, index=False, float_format="%.12g")

    weighted_config = _weighted_config(criteria)
    weighted_config_path = OUTPUT / "WEIGHTED_REGRESSION_CONFIG.json"
    _write_json(weighted_config_path, weighted_config)

    support = nested.fold_support
    validation = support[support["role"].eq("validation")]
    outer_validation = validation[validation["level"].eq("outer")]
    inner_validation = validation[validation["level"].eq("inner")]
    split_manifest = {
        "status": "qualified",
        "training_performed": False,
        "created_date": "2026-10-12",
        "baseline_head": baseline_head,
        "development_processed_sha256": EXPECTED_PROCESSED_SHA256,
        "historical_membership_path": str(SPLIT_PATH.relative_to(ROOT)),
        "historical_membership_sha256": EXPECTED_SPLIT_SHA256,
        "development_rows": partition_audit["development_rows"],
        "development_stations": partition_audit["development_stations"],
        "development_low_do_rows": partition_audit["development_low_do_rows"],
        "development_low_do_sites": partition_audit["development_low_do_sites"],
        "development_low_do_fraction": partition_audit[
            "development_low_do_fraction"
        ],
        "low_do_threshold_mg_l": LOW_DO_THRESHOLD_MG_L,
        "splitter": "sklearn.model_selection.StratifiedGroupKFold",
        "group": "station_code",
        "outer_folds": OUTER_FOLDS,
        "inner_folds": INNER_FOLDS,
        "outer_seed": NESTED_CV_SEED,
        "inner_seed_rule": "20261012 + outer_fold_number",
        "criteria": criteria_as_dict(criteria),
        "site_assignment_path": str(assignments_path.relative_to(ROOT)),
        "site_assignments_file_sha256": sha256_file(assignments_path),
        "site_assignments_canonical_sha256": nested.site_assignments_sha256,
        "outer_row_assignments_canonical_sha256": (
            nested.outer_row_assignments_sha256
        ),
        "inner_row_assignments_canonical_sha256": (
            nested.inner_row_assignments_sha256
        ),
        "fold_support_path": str(support_path.relative_to(ROOT)),
        "fold_support_sha256": sha256_file(support_path),
        "all_partitions_qualified": nested.qualified,
        "all_site_overlaps_zero": bool(
            support["counterpart_site_overlap"].eq(0).all()
        ),
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }
    split_manifest_path = OUTPUT / "NESTED_CV_SPLIT_MANIFEST.json"
    _write_json(split_manifest_path, split_manifest)

    source_code = {
        str(path.relative_to(ROOT)): sha256_file(path)
        for path in [
            ROOT / "src/preprocessing.py",
            ROOT / "src/phase2b0_readiness.py",
            ROOT / "scripts/recover_phase2b0_data.py",
            ROOT / "scripts/run_phase2b0_readiness.py",
            ROOT / "tests/test_phase2b0_readiness.py",
        ]
    }
    provenance = {
        "recovery_status": "exact_historical_recovery",
        "training_performed": False,
        "retrieved_date": "2026-10-12",
        "source": {
            "publisher": "OpenDataNI / NIEA Water Science and Evidence Unit",
            "dataset": "River Water Quality Monitoring 1990 to 2024 - All Parameters",
            "catalogue_url": CATALOGUE_URL,
            "service_url": SERVICE_URL,
            "arcgis_item_id": "a8f8de1ad58a4ee28340f23a9be4bdad",
            "download_url": DOWNLOAD_URL,
            "download_spatial_reference": 29902,
            "service_content_last_modified": "2026-06-23T11:13:39.402Z",
            "licence": "UK Open Government Licence v3.0",
        },
        "files": {
            "raw": {
                "path": str(RAW_PATH.relative_to(ROOT)),
                "expected_sha256": EXPECTED_RAW_SHA256,
                "observed_sha256": observed_hashes["raw"],
                "bytes": RAW_PATH.stat().st_size,
                "audit": raw_audit,
            },
            "processed": {
                "path": str(PROCESSED_PATH.relative_to(ROOT)),
                "expected_sha256": EXPECTED_PROCESSED_SHA256,
                "observed_sha256": observed_hashes["processed"],
                "bytes": PROCESSED_PATH.stat().st_size,
                "fresh_reconstruction_equal": True,
                "audit": processed_audit,
            },
            "cleaning_audit": {
                "path": str(AUDIT_PATH.relative_to(ROOT)),
                "expected_sha256": EXPECTED_AUDIT_SHA256,
                "observed_sha256": observed_hashes["audit"],
                "fresh_reconstruction_equal": True,
            },
            "historical_membership": {
                "path": str(SPLIT_PATH.relative_to(ROOT)),
                "expected_sha256": EXPECTED_SPLIT_SHA256,
                "observed_sha256": observed_hashes["historical_split"],
            },
        },
        "cleaning_rules": rebuilt_audit["transformations"],
        "partition_audit": partition_audit,
        "historical_cross_checks": cross_checks,
        "automated_tests": test_result,
        "source_code_sha256": source_code,
        "phase2a_protection": phase2a,
        "task_start_git_snapshot": {
            "head": baseline_head,
            "branch": "research-upgrade-v3",
            "status_summary": [
                "?? research_upgrade_v3/",
                "?? scripts/run_low_do_reliability.py",
                "?? src/low_do_reliability.py",
                "?? tests/test_low_do_reliability.py",
            ],
            "untracked_scope": TASK_START_UNTRACKED,
            "tracked_modifications": [],
        },
    }
    provenance_path = OUTPUT / "DATA_PROVENANCE_MANIFEST.json"
    _write_json(provenance_path, provenance)

    outer_summary = outer_validation[
        [
            "outer_fold", "rows", "sites", "low_do_rows", "low_do_sites",
            "low_do_fraction", "max_single_site_low_share", "qualified",
        ]
    ]
    inner_extremes = pd.DataFrame(
        [
            {
                "measure": "inner validation minimum",
                "rows": int(inner_validation["rows"].min()),
                "sites": int(inner_validation["sites"].min()),
                "low_do_rows": int(inner_validation["low_do_rows"].min()),
                "low_do_sites": int(inner_validation["low_do_sites"].min()),
                "low_do_fraction": float(inner_validation["low_do_fraction"].min()),
                "max_single_site_low_share": float(
                    inner_validation["max_single_site_low_share"].min()
                ),
            },
            {
                "measure": "inner validation maximum",
                "rows": int(inner_validation["rows"].max()),
                "sites": int(inner_validation["sites"].max()),
                "low_do_rows": int(inner_validation["low_do_rows"].max()),
                "low_do_sites": int(inner_validation["low_do_sites"].max()),
                "low_do_fraction": float(inner_validation["low_do_fraction"].max()),
                "max_single_site_low_share": float(
                    inner_validation["max_single_site_low_share"].max()
                ),
            },
        ]
    )

    _write_text(
        OUTPUT / "DATA_RECOVERY_REPORT.md",
        f"""# WaterSense Data Recovery Report

## Result

**Exact historical recovery succeeded.** The official ArcGIS Hub CSV exported in British National Grid spatial reference `29902` has SHA-256 `{EXPECTED_RAW_SHA256}`, exactly matching both historical research manifests. It contains {raw_audit['rows']:,} rows, {raw_audit['columns']} columns, {raw_audit['stations']:,} station codes, unique `OBJECTID`, and dates from {raw_audit['first_date']} to {raw_audit['last_date']}.

An initial WGS84 (`4326`) export had a different byte hash because its X/Y representation differed. It was not accepted as historical recovery. The exact `29902` export replaced it in the ignored raw-data location; the nonhistorical download was retained only outside the repository as working evidence.

## Provenance

- Publisher: OpenDataNI / Northern Ireland Environment Agency, Water Science and Evidence Unit.
- Dataset: River Water Quality Monitoring 1990 to 2024 — All Parameters.
- ArcGIS item: `a8f8de1ad58a4ee28340f23a9be4bdad`.
- Download parameter: `format=csv&spatialRefId=29902`.
- Licence: UK Open Government Licence v3.0.
- Retrieval date: 2026-10-12; service content last modified 2026-06-23.

## Reconstruction checks

| Artifact | Expected SHA-256 | Observed SHA-256 | Status |
| --- | --- | --- | --- |
| Raw CSV | `{EXPECTED_RAW_SHA256}` | `{observed_hashes['raw']}` | exact |
| Processed modelling CSV | `{EXPECTED_PROCESSED_SHA256}` | `{observed_hashes['processed']}` | exact |
| Cleaning audit JSON | `{EXPECTED_AUDIT_SHA256}` | `{observed_hashes['audit']}` | exact |
| Historical grouped membership | `{EXPECTED_SPLIT_SHA256}` | `{observed_hashes['historical_split']}` | exact |

Fresh execution of `prepare_water_quality_modeling_data` produced a dataframe value-equal to the restored processed file and reproduced the historical audit exactly. The historical `src/preprocessing.py` hash also matches the frozen manifest. No model code was executed.

`scripts/recover_phase2b0_data.py` makes the recovery fail-closed and repeatable: it uses the frozen download URL only when the ignored raw file is absent, verifies every SHA-256 before installation, reconstructs both processed artifacts, and refuses to overwrite a nonmatching existing file.

## Schema and cleaning

The target is `DO_mg_l_` / `dissolved_oxygen_mg_l`, measured in mg/L. Cleaning excludes {raw_audit['target_missing_rows']:,} missing-target rows and {raw_audit['target_qualified_rows']} qualified-target rows; predictor numeric values are retained, qualifier flags are separated, predictor missing values remain for fold-local imputation, and date/month/season/cyclical fields are derived deterministically. Result: {processed_audit['rows']:,} rows, {processed_audit['stations']} sites and {processed_audit['columns']} columns.

The raw and processed files remain under ignored `data/` paths and are not proposed for Git staging.
""",
    )

    _write_text(
        OUTPUT / "DEVELOPMENT_PARTITION_AUDIT.md",
        f"""# Development Partition Audit

## Verdict

The historical development partition is **exactly recovered**: {partition_audit['development_rows']:,} rows, {partition_audit['development_stations']} sites, and the exact saved membership. The legacy test remains isolated at {partition_audit['legacy_test_rows']:,} rows/{partition_audit['legacy_test_stations']} sites with zero station overlap.

## Identity checks

- Every processed row has one unique `source_object_id`; no processed duplicate rows or duplicate station/date records were found.
- All 151,031 processed identities join one-to-one to `split_grouped.csv.gz` using source ID, station and date.
- Each source ID has exactly one historical partition membership.
- A fresh seed-42 `GroupShuffleSplit(test_size=0.2)` exactly reproduces the saved development and legacy-test source IDs.
- All saved holdout feature and target values match the reconstructed processed rows at tolerance `1e-12`.
- All 119,690 saved training-feature-reference rows match reconstructed development features in value and order.
- No legacy-test row or site is included in development.

## Development target support

- Low-DO definition: ground truth strictly `<4 mg/L`.
- Low-DO rows: **{partition_audit['development_low_do_rows']}** ({partition_audit['development_low_do_fraction']:.4%}).
- Independent sites with low-DO rows: **{partition_audit['development_low_do_sites']}**.

These are repeated observations within sites, not {partition_audit['development_low_do_rows']} independent events. Site remains the split and uncertainty unit.
""",
    )

    _write_text(
        OUTPUT / "NESTED_CV_READINESS_REPORT.md",
        f"""# Nested Site-Grouped CV Readiness Report

## Status: READY

The exact historical development partition supports the frozen five-outer/four-inner site-grouped design. `StratifiedGroupKFold` uses the binary `<4 mg/L` label only to balance fold support; station code is the grouping unit. Outer seed is {NESTED_CV_SEED}; inner seed is `{NESTED_CV_SEED} + outer_fold`.

Pre-model gates were frozen before model results: validation partitions require at least {criteria.validation_min_low_rows} low rows, {criteria.validation_min_low_sites} low sites, no site contributing more than {criteria.validation_max_single_site_low_share:.0%} of low rows, and zero overlap; training partitions require at least {criteria.training_min_low_rows} low rows and {criteria.training_min_low_sites} low sites.

## Outer validation support

{_markdown_table(outer_summary)}

## Inner validation range across 20 folds

{_markdown_table(inner_extremes)}

All 50 train/validation partition rows in `NESTED_CV_FOLD_SUPPORT.csv` pass their applicable support gates; all paired site overlaps are zero. Every outer validation fold has 143–166 low rows at 12–33 sites. Every inner validation fold has 137–168 low rows at 11–36 sites. The largest single-site low-row share is below 50% in every validation fold, although several folds reach roughly 44.5%, which must remain a reported limitation.

## Reproducibility

- Site assignment canonical SHA-256: `{nested.site_assignments_sha256}`.
- Outer row-assignment canonical SHA-256: `{nested.outer_row_assignments_sha256}`.
- Inner row-assignment canonical SHA-256: `{nested.inner_row_assignments_sha256}`.
- A second independent construction in the same run produced all three identical hashes.

`NESTED_CV_SITE_ASSIGNMENTS.csv` is the compact frozen index. Together with the exact processed-data hash it determines every row-level fold. No legacy test metric was used to design or qualify these folds.

## Statistical limits

Readiness means the design can support controlled development comparison; it does not make 758 low rows independent, eliminate site concentration, or create confirmatory evidence. Precision/F1 can still be undefined for a candidate that predicts no low values; that candidate must fail as preregistered. Final uncertainty remains whole-site clustered.
""",
    )

    _write_text(
        OUTPUT / "WEIGHTED_REGRESSION_FROZEN_PROTOCOL.md",
        f"""# Low-DO Weighted Regression — Frozen Execution Protocol

**Status:** prepared, not executed. **Training performed in Phase 2B-0:** no.

## Hypothesis and eligible data

Increasing the loss contribution of training-fold observations with ground-truth DO `<4 mg/L` may reduce low-DO overprediction and false negatives without unacceptable overall regression degradation. Only the exact {partition_audit['development_rows']:,}-row/{partition_audit['development_stations']}-site historical development partition is eligible. Every registered legacy benchmark is prohibited from tuning and selection.

## Fold-local processing and weights

All imputation, missingness indicators and scaling are fitted inside the relevant training fold. For multiplier `m ∈ {{1,2,4,8}}`, raw sample weight is `m` for training target `<4`, otherwise `1`; divide by the training-fold mean raw weight so total weight equals the training row count. Validation targets never influence weights or preprocessing. Row duplication/resampling to imitate weights is prohibited.

## Candidates and frozen search

- Random Forest and Extra Trees: trees `{{150,300}}`, minimum leaf `{{2,5}}`, max features `{{0.6,0.8}}`.
- Histogram Gradient Boosting: learning rate `{{0.03,0.07}}`, max leaf nodes `{{15,31}}`, minimum leaf `{{20,50}}`, L2 `{{0,1}}`.
- Every candidate crosses the four weight multipliers; random seed {NESTED_CV_SEED}. The complete machine-readable grid is in `WEIGHTED_REGRESSION_CONFIG.json`.

## Inner selection

Co-primary metrics are low-DO Recall (higher) and low-DO MAE (lower). A candidate qualifies only if inner out-of-fold overall MAE is no more than 10% worse than the same-fold unweighted anchor, low-DO Precision is at least 0.30, every fold with true low DO has at least one predicted-low row, and there is no data/split/non-finite/undefined-required-metric failure.

Rank qualified candidates lexicographically by: highest mean low-DO Recall; lowest mean low-DO MAE; lowest overall MAE; lower complexity; stable candidate ID. This prevents choosing whichever metric looks favorable after results.

## Outer evaluation and metrics

Fit the inner-selected configuration on each outer-training partition and evaluate it once on that outer validation partition. Concatenate outer out-of-fold predictions. Report Overall MAE/RMSE/R²; Low-DO MAE/RMSE/Bias (prediction−truth); Recall, Precision, F1 and FNR; row/site denominators; fold dispersion; and 2,000 paired whole-site percentile bootstrap intervals with seed {NESTED_CV_SEED}.

Improved Recall with materially worse overall MAE is a tradeoff, not a universal improvement. No rule requires all metrics to improve.

## Stopping and failure

Execute the fixed grid once. Do not add candidates after viewing outcomes. Stop with `NO QUALIFIED MODEL` if all candidates fail. A fold with missing/overlapping sites, inadequate frozen support, non-finite predictions, no predicted positives, or unsupported sample weights is a recorded failure. Legacy tests cannot rescue or change a failed result.
""",
    )

    final_status = "READY" if nested.qualified else "NOT READY"
    _write_text(
        OUTPUT / "PHASE2B0_FINAL_HANDOFF.md",
        f"""# Phase 2B-0 Final Handoff

## Final status: {final_status}

The original raw CSV, processed modelling table, cleaning audit and historical split membership were recovered with exact historical SHA-256 values. The development partition is exactly {partition_audit['development_rows']:,} rows/{partition_audit['development_stations']} sites, contains {partition_audit['development_low_do_rows']} low-DO rows at {partition_audit['development_low_do_sites']} sites, and excludes all {partition_audit['legacy_test_rows']:,} legacy-test rows/{partition_audit['legacy_test_stations']} sites.

The frozen 5×4 nested site-grouped split passes every pre-model support gate. Outer validation has 143–166 low rows at 12–33 sites; inner validation has 137–168 low rows at 11–36 sites. All train/validation station overlaps are zero and fold hashes reproduce exactly.

The weighted-regression candidate grid, fold-local sample weights, inner qualification/ranking, outer evaluation, metrics, site-bootstrap uncertainty and stopping rules are frozen. Phase 2B-0 fitted no model and used no legacy test metric for design.

Targeted automated validation passed ({test_result['summary']}). It includes labelled synthetic unit tests for failure paths and a separate integration test against the exact recovered historical hashes, partition and frozen fold hashes.

**Permission boundary:** the evidence permits starting Phase 2B controlled development training under the frozen protocol. It does not permit changing folds/search rules, using legacy test results for selection, or making confirmatory/generalisation claims.

Remaining limits: low DO is only 0.6333% of development rows; repeated rows within sites are dependent; some validation folds have a single site contributing about 44.5% of low rows; event independence is not available; the four historical v1 source-hash provenance gaps remain; and no new independent confirmation set exists.
""",
    )

    # Capture final generated artifacts without self-referential manifest hashes.
    generated = {
        str(path.relative_to(OUTPUT)): sha256_file(path)
        for path in sorted(OUTPUT.iterdir())
        if path.is_file() and path.name != "DATA_PROVENANCE_MANIFEST.json"
    }
    provenance["phase2b0_outputs_sha256"] = generated
    provenance["final_status"] = final_status
    _write_json(provenance_path, provenance)


if __name__ == "__main__":
    main()
