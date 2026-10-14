import importlib.util
import gzip
import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("v4", HERE / "v4_upgrade.py")
v4 = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(v4)


class V4Tests(unittest.TestCase):
    def test_metric_counts_and_definitions(self):
        row = v4.metric_row("x", np.array([1, 1, 0, 0]), np.array([1, 0, 1, 0]))
        self.assertEqual((row["true_positives"], row["false_positives"], row["false_negatives"], row["true_negatives"]), (1, 1, 1, 1))
        self.assertAlmostEqual(row["precision"], 0.5)
        self.assertAlmostEqual(row["recall"], 0.5)

    def test_frozen_external_export_is_rejected(self):
        self.assertEqual(v4.sha256(v4.RAW), v4.CURRENT_EXPORT_SHA256)

    def test_outputs_do_not_target_historical_directories(self):
        self.assertEqual(v4.OUT.name, "research_upgrade_v4_candidate")
        self.assertNotIn(v4.V3, v4.OUT.parents)

    def test_v4_artifact_manifest(self):
        manifest = json.loads((HERE / "V4_ARTIFACT_MANIFEST.json").read_text())
        for relative, expected in manifest["files"].items():
            self.assertEqual(v4.sha256(HERE / relative), expected, relative)

    def test_release_candidate_manifest(self):
        manifest = json.loads((HERE / "V4_RELEASE_CANDIDATE_MANIFEST.json").read_text())
        for relative, expected in manifest["files"].items():
            self.assertEqual(v4.sha256(v4.ROOT / relative), expected, relative)

    def test_frozen_classifier_metrics_and_claim_language(self):
        predictions = pd.read_csv(HERE / "WATERSENSE_CLASSIFIER_OOF_PREDICTIONS.csv.gz")
        row = v4.metric_row(
            "classifier",
            predictions["actual_low_do"].to_numpy(dtype=int),
            predictions["predicted_low_do"].to_numpy(dtype=int),
        )
        self.assertEqual(
            (row["true_positives"], row["false_positives"], row["true_negatives"], row["false_negatives"]),
            (699, 9517, 109415, 59),
        )
        self.assertAlmostEqual(row["recall"], 0.9221635883905013)
        self.assertAlmostEqual(row["precision"], 0.06842208300704777)
        self.assertAlmostEqual(row["f1"], 0.12739201676280678)
        report = (HERE / "WATERSENSE_V4_SCIENTIFIC_REPORT.md").read_text()
        self.assertNotIn("The preregistered", report)
        self.assertNotIn("V4 confirmed improvement", report)
        self.assertIn("independent preregistration is not established", report)
        self.assertIn("NOT DIRECTLY COMPARABLE AS A PERFORMANCE-IMPROVEMENT EXPERIMENT", report)

    def test_deterministic_gzip_header_and_decoded_rows(self):
        path = HERE / "WATERSENSE_CLASSIFIER_OOF_PREDICTIONS.csv.gz"
        self.assertEqual(int.from_bytes(path.read_bytes()[4:8], "little"), 0)
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            self.assertEqual(sum(1 for _ in handle), 119_691)

    def test_w02_frozen_grid_and_execution_are_consistent(self):
        frozen = json.loads((v4.V3 / "phase2b0/WEIGHTED_REGRESSION_CONFIG.json").read_text())
        executed = json.loads((v4.V3 / "experiment1_weighted_regression/EXPERIMENT1_CONFIG.json").read_text())
        manifest = json.loads((v4.V3 / "experiment1_weighted_regression/EXPERIMENT1_RUN_MANIFEST.json").read_text())
        weights = frozen["sample_weight"]["multipliers"]
        self.assertEqual(weights, [1, 2, 4, 8])
        self.assertEqual(executed["frozen_search"]["sample_weight"]["multipliers"], weights)
        candidates = frozen["candidates"]
        non_weight = 1
        total = 0
        for config in candidates.values():
            family_count = 1
            for key, values in config.items():
                if key != "random_state":
                    family_count *= len(values)
            total += family_count
        non_weight = total
        self.assertEqual(non_weight, 32)
        self.assertEqual(non_weight * len(weights), 128)
        folds = pd.read_csv(v4.V3 / "experiment1_weighted_regression/INNER_CV_FOLD_RESULTS.csv.gz")
        self.assertEqual(len(folds), 2560)
        self.assertEqual(folds["candidate_id"].nunique(), 128)
        self.assertEqual(folds.duplicated(["outer_fold", "inner_fold", "candidate_id"]).sum(), 0)
        self.assertTrue((folds["run_status"] == "complete").all())
        self.assertEqual(manifest["completed_inner_candidate_evaluations"], 2560)
        self.assertEqual(manifest["failed_inner_candidate_evaluations"], 0)


if __name__ == "__main__":
    unittest.main()
