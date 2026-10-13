"""Phase 2B-0 readiness tests.

``SyntheticReadinessUnitTests`` uses fabricated rows only to exercise code
paths.  ``HistoricalDataIntegrationTests`` is explicitly gated on the locally
recovered research data and verifies the real historical evidence.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from scripts.recover_phase2b0_data import _require_existing_exact

from src.phase2b0_readiness import (
    EXPECTED_PROCESSED_COLUMNS,
    EXPECTED_PROCESSED_SHA256,
    EXPECTED_SPLIT_SHA256,
    DataReadinessError,
    FoldCriteria,
    audit_development_partition,
    generate_nested_site_folds,
    low_do_mask,
    sha256_file,
    validate_processed_data,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_PATH = REPOSITORY_ROOT / "data/processed/water_quality_modeling.csv"
SPLIT_PATH = REPOSITORY_ROOT / "research_outputs/predictions/split_grouped.csv.gz"


def synthetic_processed(site_count: int = 18, rows_per_site: int = 4) -> pd.DataFrame:
    """Build schema-correct synthetic rows; these are never research evidence."""
    rows: list[dict[str, object]] = []
    object_id = 1
    for site_number in range(site_count):
        for row_number in range(rows_per_site):
            row = {column: 0.0 for column in EXPECTED_PROCESSED_COLUMNS}
            row.update(
                {
                    "source_object_id": object_id,
                    "station_code": f"S{site_number:03d}",
                    "sample_date": f"2020-01-{site_number + 1:02d}",
                    "sample_year": 2020,
                    "sample_month": 1,
                    "season": "winter",
                    # Exactly one low-DO row per site; 4.0 remains non-low.
                    "dissolved_oxygen_mg_l": (
                        3.0 if row_number == 0 else 4.0 + row_number
                    ),
                }
            )
            rows.append(row)
            object_id += 1
    return pd.DataFrame(rows, columns=EXPECTED_PROCESSED_COLUMNS)


def historical_membership_for(data: pd.DataFrame) -> pd.DataFrame:
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_index, test_index = next(
        splitter.split(data, groups=data["station_code"])
    )
    membership = data[
        ["source_object_id", "station_code", "sample_date"]
    ].copy()
    membership["partition"] = ""
    membership.loc[train_index, "partition"] = "train"
    membership.loc[test_index, "partition"] = "test"
    return membership


SYNTHETIC_CRITERIA = FoldCriteria(
    validation_min_low_rows=1,
    validation_min_low_sites=1,
    validation_max_single_site_low_share=1.0,
    training_min_low_rows=1,
    training_min_low_sites=1,
)


class SyntheticReadinessUnitTests(unittest.TestCase):
    """Code-level tests on labelled synthetic fixtures, not empirical results."""

    def test_schema_and_expected_counts_are_enforced(self) -> None:
        data = synthetic_processed()
        result = validate_processed_data(
            data, expected_rows=len(data), expected_stations=18
        )
        self.assertEqual(result["rows"], 72)
        self.assertEqual(result["stations"], 18)
        with self.assertRaisesRegex(DataReadinessError, "schema mismatch"):
            validate_processed_data(
                data.drop(columns="ph"),
                expected_rows=len(data),
                expected_stations=18,
            )
        with self.assertRaisesRegex(DataReadinessError, "row count"):
            validate_processed_data(
                data, expected_rows=len(data) + 1, expected_stations=18
            )

    def test_unique_observation_identity_is_required(self) -> None:
        data = synthetic_processed()
        data.loc[1, "source_object_id"] = data.loc[0, "source_object_id"]
        with self.assertRaisesRegex(DataReadinessError, "complete and unique"):
            validate_processed_data(
                data, expected_rows=len(data), expected_stations=18
            )

    def test_strict_low_do_threshold(self) -> None:
        labels = low_do_mask(pd.Series([3.999, 4.0, 4.001]))
        self.assertEqual(labels.tolist(), [True, False, False])

    def test_missing_and_nonnumeric_targets_fail_closed(self) -> None:
        with self.assertRaisesRegex(DataReadinessError, "missing targets"):
            low_do_mask(pd.Series([3.0, None], dtype="float64"))
        with self.assertRaisesRegex(DataReadinessError, "numeric target"):
            low_do_mask(pd.Series(["3.0", "5.0"]))

    def test_recovery_refuses_to_overwrite_nonmatching_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.csv"
            path.write_bytes(b"expected")
            expected = sha256_file(path)
            self.assertTrue(_require_existing_exact(path, expected))
            path.write_bytes(b"different")
            with self.assertRaisesRegex(DataReadinessError, "Refusing to overwrite"):
                _require_existing_exact(path, expected)

    def test_saved_development_membership_and_counts(self) -> None:
        data = synthetic_processed()
        membership = historical_membership_for(data)
        development = membership["partition"].eq("train")
        legacy_test = ~development
        restored, audit = audit_development_partition(
            data,
            membership,
            expected_development_rows=int(development.sum()),
            expected_development_stations=int(
                membership.loc[development, "station_code"].nunique()
            ),
            expected_test_rows=int(legacy_test.sum()),
            expected_test_stations=int(
                membership.loc[legacy_test, "station_code"].nunique()
            ),
        )
        self.assertEqual(set(restored["source_object_id"]), set(
            membership.loc[development, "source_object_id"]
        ))
        self.assertTrue(audit["saved_membership_matches_seed42_group_split"])

    def test_partition_identity_mismatch_is_rejected(self) -> None:
        data = synthetic_processed()
        membership = historical_membership_for(data)
        membership.loc[0, "source_object_id"] = 999_999
        with self.assertRaisesRegex(DataReadinessError, "identity mismatch"):
            audit_development_partition(data, membership)

    def test_cross_partition_station_overlap_is_rejected(self) -> None:
        data = synthetic_processed(site_count=2, rows_per_site=4)
        membership = data[
            ["source_object_id", "station_code", "sample_date"]
        ].copy()
        membership["partition"] = ["train", "test"] * 4
        with self.assertRaisesRegex(DataReadinessError, "share 2 stations"):
            audit_development_partition(
                data,
                membership,
                expected_development_rows=4,
                expected_development_stations=2,
                expected_test_rows=4,
                expected_test_stations=2,
            )

    def test_nested_cv_is_reproducible_and_station_disjoint(self) -> None:
        data = synthetic_processed()
        first = generate_nested_site_folds(
            data,
            outer_folds=3,
            inner_folds=2,
            seed=17,
            criteria=SYNTHETIC_CRITERIA,
        )
        second = generate_nested_site_folds(
            data.sample(frac=1.0, random_state=99),
            outer_folds=3,
            inner_folds=2,
            seed=17,
            criteria=SYNTHETIC_CRITERIA,
        )
        self.assertTrue(first.qualified)
        self.assertEqual(first.site_assignments_sha256, second.site_assignments_sha256)
        self.assertEqual(
            first.outer_row_assignments_sha256,
            second.outer_row_assignments_sha256,
        )
        self.assertEqual(
            first.inner_row_assignments_sha256,
            second.inner_row_assignments_sha256,
        )
        self.assertTrue(first.fold_support["counterpart_site_overlap"].eq(0).all())

    def test_fold_hash_changes_when_seed_changes(self) -> None:
        data = synthetic_processed()
        first = generate_nested_site_folds(
            data,
            outer_folds=3,
            inner_folds=2,
            seed=17,
            criteria=SYNTHETIC_CRITERIA,
        )
        changed = generate_nested_site_folds(
            data,
            outer_folds=3,
            inner_folds=2,
            seed=18,
            criteria=SYNTHETIC_CRITERIA,
        )
        self.assertNotEqual(
            first.site_assignments_sha256, changed.site_assignments_sha256
        )

    def test_unqualified_fold_exits_before_experiment(self) -> None:
        data = synthetic_processed()
        impossible = FoldCriteria(
            validation_min_low_rows=1,
            validation_min_low_sites=100,
            validation_max_single_site_low_share=1.0,
            training_min_low_rows=1,
            training_min_low_sites=1,
        )
        with self.assertRaisesRegex(DataReadinessError, "support gates failed"):
            generate_nested_site_folds(
                data,
                outer_folds=3,
                inner_folds=2,
                seed=17,
                criteria=impossible,
            )


@unittest.skipUnless(
    PROCESSED_PATH.is_file() and SPLIT_PATH.is_file(),
    "Exact recovered research data are not available; synthetic unit tests still run",
)
class HistoricalDataIntegrationTests(unittest.TestCase):
    """Integration checks against exact recovered historical research data."""

    def test_exact_historical_identity_partition_and_fold_hashes(self) -> None:
        self.assertEqual(sha256_file(PROCESSED_PATH), EXPECTED_PROCESSED_SHA256)
        self.assertEqual(sha256_file(SPLIT_PATH), EXPECTED_SPLIT_SHA256)
        processed = pd.read_csv(PROCESSED_PATH)
        membership = pd.read_csv(SPLIT_PATH)
        validate_processed_data(processed)
        development, audit = audit_development_partition(processed, membership)
        self.assertEqual(audit["development_rows"], 119_690)
        self.assertEqual(audit["development_stations"], 672)
        result = generate_nested_site_folds(development)
        self.assertTrue(result.qualified)
        self.assertEqual(
            result.site_assignments_sha256,
            "0fa76b39cd3697aed2b615f5921a2cfa8dbaf0fdbd216393520c25c52bf58025",
        )
        self.assertEqual(
            result.outer_row_assignments_sha256,
            "d18f55c62e6baab38223c804cc3dbcdf549837560f5984dccda6139d6599b1fd",
        )
        self.assertEqual(
            result.inner_row_assignments_sha256,
            "7a143df06162994efc65b0fb58770b21a2b49a6371a66ce46a592d7218dcb0b0",
        )


if __name__ == "__main__":
    unittest.main()
