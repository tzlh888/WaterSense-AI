import json
from pathlib import Path
import unittest

import pandas as pd

from src.portfolio_analysis import (
    break_even_ratio,
    confusion_counts,
    regression_summary,
    sha256_file,
    station_concentration,
    verify_regression_identity,
)


ROOT = Path(__file__).resolve().parents[1]


class PortfolioAnalysisTests(unittest.TestCase):
    def test_confusion_counts(self):
        actual = pd.Series([True, True, False, False])
        predicted = pd.Series([True, False, True, False])
        self.assertEqual(
            confusion_counts(actual, predicted), {"tp": 1, "fp": 1, "tn": 1, "fn": 1}
        )

    def test_break_even_ratio(self):
        baseline = {"fn": 660, "fp": 26}
        weighted = {"fn": 482, "fp": 219}
        self.assertAlmostEqual(break_even_ratio(baseline, weighted), 193 / 178)

    def test_identity_and_concentration(self):
        rows = []
        for variant, predictions in [("baseline", [3.0, 5.0]), ("weighted", [2.0, 4.5])]:
            for object_id, (actual, predicted) in enumerate(zip([2.0, 6.0], predictions), 1):
                rows.append(
                    {
                        "variant": variant,
                        "source_object_id": object_id,
                        "station_code": f"S{object_id}",
                        "sample_date": f"2020-01-0{object_id}",
                        "outer_fold": object_id,
                        "actual_do_mg_l": actual,
                        "predicted_do_mg_l": predicted,
                        "actual_low_do": actual < 4,
                    }
                )
        frame = pd.DataFrame(rows)
        verify_regression_identity(frame)
        table, summary = station_concentration(frame)
        self.assertEqual(len(table), 1)
        self.assertEqual(summary["low_do_events"], 1)
        self.assertEqual(summary["effective_station_count"], 1.0)
        self.assertEqual(regression_summary(frame[frame.variant.eq("baseline")])["fn"], 0)

    def test_identity_rejects_station_in_multiple_folds(self):
        frame = pd.DataFrame(
            {
                "variant": ["baseline", "baseline", "weighted", "weighted"],
                "source_object_id": [1, 2, 1, 2],
                "station_code": ["S", "S", "S", "S"],
                "sample_date": ["2020-01-01", "2020-01-02"] * 2,
                "outer_fold": [1, 2, 1, 2],
                "actual_do_mg_l": [3.0, 6.0, 3.0, 6.0],
                "actual_low_do": [True, False, True, False],
            }
        )
        with self.assertRaisesRegex(ValueError, "Station leakage"):
            verify_regression_identity(frame)

    def test_generated_manifest_matches_outputs(self):
        manifest = json.loads(
            (ROOT / "research_extension/ARTIFACT_MANIFEST.json").read_text()
        )
        for relative, expected in manifest["files"].items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(sha256_file(path), expected, relative)

    def test_evidence_ledger_uses_fixed_statuses_and_resolvable_paths(self):
        ledger = pd.read_csv(ROOT / "audits/EVIDENCE_LEDGER.csv")
        allowed = {
            "VERIFIED",
            "REPORTED_ONLY",
            "EXPLORATORY",
            "UNVERIFIED",
            "CONTRADICTED",
        }
        self.assertTrue(set(ledger["status"]).issubset(allowed))
        for evidence in ledger["evidence"]:
            self.assertTrue((ROOT / evidence).exists(), evidence)


if __name__ == "__main__":
    unittest.main()
