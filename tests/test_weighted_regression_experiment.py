"""Tests for the frozen Phase 2B weighted-regression experiment.

Synthetic fixtures exercise algorithm behavior only.  Tests explicitly marked
as integration checks use the recovered historical development evidence.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.phase2b0_readiness import sha256_file
from src.weighted_regression_experiment import (
    ANCHOR_CANDIDATE_ID,
    Candidate,
    ExperimentIntegrityError,
    compute_experiment_metrics,
    compute_training_weights,
    enumerate_frozen_candidates,
    make_estimator,
    paired_site_bootstrap,
    summarize_and_select_candidates,
    verify_prediction_pairing,
)


ROOT = Path(__file__).resolve().parents[1]
FROZEN_CONFIG = ROOT / "research_upgrade_v3/phase2b0/WEIGHTED_REGRESSION_CONFIG.json"
ASSIGNMENTS = ROOT / "research_upgrade_v3/phase2b0/NESTED_CV_SITE_ASSIGNMENTS.csv"
EXPERIMENT_OUTPUT = ROOT / "research_upgrade_v3/experiment1_weighted_regression"


class SyntheticWeightedRegressionTests(unittest.TestCase):
    """Unit tests with fabricated data that are not research evidence."""

    def test_frozen_grid_has_128_unique_candidates_and_anchor(self) -> None:
        config = json.loads(FROZEN_CONFIG.read_text())
        candidates = enumerate_frozen_candidates(config)
        ids = [candidate.candidate_id for candidate in candidates]
        self.assertEqual(len(ids), 128)
        self.assertEqual(len(set(ids)), 128)
        self.assertIn(ANCHOR_CANDIDATE_ID, ids)

    def test_training_weights_use_strict_threshold_and_normalize(self) -> None:
        targets = pd.Series([3.999, 4.0, 8.0])
        weights = compute_training_weights(targets, 4)
        self.assertAlmostEqual(float(weights.mean()), 1.0)
        self.assertAlmostEqual(float(weights[0] / weights[1]), 4.0)
        self.assertAlmostEqual(float(weights[1]), float(weights[2]))
        with self.assertRaisesRegex(ExperimentIntegrityError, "Unfrozen"):
            compute_training_weights(targets, 3)

    def test_all_frozen_model_families_accept_native_sample_weight(self) -> None:
        rng = np.random.default_rng(7)
        x = rng.normal(size=(40, 4))
        y = np.r_[np.full(5, 3.0), rng.normal(8.0, 0.4, size=35)]
        candidates = [
            Candidate(
                "rf", "RandomForestRegressor",
                {"n_estimators": 5, "min_samples_leaf": 2, "max_features": 0.8},
                2, 1.0,
            ),
            Candidate(
                "et", "ExtraTreesRegressor",
                {"n_estimators": 5, "min_samples_leaf": 2, "max_features": 0.8},
                2, 1.0,
            ),
            Candidate(
                "hgb", "HistGradientBoostingRegressor",
                {
                    "learning_rate": 0.07, "max_leaf_nodes": 15,
                    "min_samples_leaf": 5, "l2_regularization": 1.0,
                },
                2, 1.0,
            ),
        ]
        weights = compute_training_weights(y, 2)
        for candidate in candidates:
            estimator = make_estimator(candidate, n_jobs=1)
            estimator.fit(x, y, sample_weight=weights)
            prediction = estimator.predict(x[:3])
            self.assertTrue(np.isfinite(prediction).all())

    def test_metrics_recompute_confusion_and_zero_positive_rule(self) -> None:
        metrics = compute_experiment_metrics(
            [2.0, 3.0, 5.0, 6.0],
            [5.0, 3.5, 5.0, 6.0],
            stations=["A", "A", "B", "B"],
        )
        self.assertEqual(metrics["true_positive_count"], 1)
        self.assertEqual(metrics["false_negative_count"], 1)
        self.assertEqual(metrics["false_positive_count"], 0)
        self.assertAlmostEqual(metrics["low_do_recall"], 0.5)
        zero = compute_experiment_metrics(
            [2.0, 6.0], [5.0, 6.0], stations=["A", "B"]
        )
        self.assertFalse(zero["precision_defined"])
        self.assertTrue(np.isnan(zero["low_do_precision"]))
        self.assertTrue(np.isnan(zero["low_do_f1"]))

    def test_prediction_pairing_rejects_identity_mismatch(self) -> None:
        frame = pd.DataFrame(
            {
                "variant": ["baseline", "weighted"],
                "source_object_id": [1, 2],
                "station_code": ["A", "A"],
                "outer_fold": [1, 1],
                "actual_do_mg_l": [3.0, 3.0],
                "predicted_do_mg_l": [5.0, 4.0],
            }
        )
        with self.assertRaisesRegex(ExperimentIntegrityError, "identities differ"):
            verify_prediction_pairing(frame)

    def test_paired_site_bootstrap_is_reproducible(self) -> None:
        rows = []
        for variant, predictions in [
            ("baseline", [5.0, 5.0, 7.0, 8.0]),
            ("weighted", [3.0, 4.5, 7.0, 8.0]),
        ]:
            for source_id, station, actual, predicted in zip(
                [1, 2, 3, 4], ["A", "A", "B", "B"],
                [2.0, 3.0, 7.0, 8.0], predictions,
            ):
                rows.append(
                    {
                        "variant": variant,
                        "source_object_id": source_id,
                        "station_code": station,
                        "outer_fold": 1,
                        "actual_do_mg_l": actual,
                        "predicted_do_mg_l": predicted,
                    }
                )
        frame = pd.DataFrame(rows)
        first_summary, first_replicates = paired_site_bootstrap(
            frame, resamples=50, seed=19
        )
        second_summary, second_replicates = paired_site_bootstrap(
            frame, resamples=50, seed=19
        )
        pd.testing.assert_frame_equal(first_summary, second_summary)
        pd.testing.assert_frame_equal(first_replicates, second_replicates)
        self.assertTrue(first_summary["cluster_count"].eq(2).all())

    def test_inner_selection_applies_qualification_and_ranking(self) -> None:
        anchor = Candidate(
            ANCHOR_CANDIDATE_ID,
            "RandomForestRegressor",
            {"n_estimators": 150, "min_samples_leaf": 2, "max_features": 0.8},
            1,
            60.0,
        )
        alternative = Candidate(
            "weighted_candidate",
            "ExtraTreesRegressor",
            {"n_estimators": 150, "min_samples_leaf": 2, "max_features": 0.8},
            4,
            60.0,
        )
        rows = []
        for inner_fold in [1, 2]:
            actual = [2.0, 8.0, 8.0, 8.0]
            for candidate, predicted in [
                (anchor, [5.0, 8.0, 8.0, 8.0]),
                (alternative, [3.0, 8.0, 8.0, 8.0]),
            ]:
                metrics = compute_experiment_metrics(
                    actual, predicted, stations=["A", "B", "C", "D"]
                )
                rows.append(
                    {
                        "inner_fold": inner_fold,
                        "candidate_id": candidate.candidate_id,
                        "run_status": "complete",
                        **metrics,
                    }
                )
        summary, selected = summarize_and_select_candidates(
            pd.DataFrame(rows), [anchor, alternative]
        )
        self.assertIsNotNone(selected)
        self.assertEqual(selected.candidate_id, alternative.candidate_id)
        anchor_summary = summary.set_index("candidate_id").loc[ANCHOR_CANDIDATE_ID]
        self.assertFalse(anchor_summary["qualified"])


@unittest.skipUnless(ASSIGNMENTS.is_file(), "Frozen research folds unavailable")
class HistoricalFoldIntegrationTests(unittest.TestCase):
    """Real-data identity tests, separate from synthetic unit tests."""

    def test_frozen_fold_file_hash_and_station_assignment_coverage(self) -> None:
        self.assertEqual(
            sha256_file(ASSIGNMENTS),
            "0fa76b39cd3697aed2b615f5921a2cfa8dbaf0fdbd216393520c25c52bf58025",
        )
        assignments = pd.read_csv(ASSIGNMENTS)
        outer = assignments.loc[assignments["level"].eq("outer")]
        self.assertEqual(outer["station_code"].nunique(), 672)
        self.assertTrue(outer["station_code"].value_counts().eq(1).all())
        for outer_fold in range(1, 6):
            inner = assignments.loc[
                assignments["level"].eq("inner")
                & assignments["outer_fold"].eq(outer_fold)
            ]
            self.assertTrue(inner["station_code"].value_counts().eq(1).all())
            held_out = set(
                outer.loc[outer["validation_fold"].eq(outer_fold), "station_code"]
            )
            self.assertTrue(held_out.isdisjoint(set(inner["station_code"])))

    @unittest.skipUnless(
        (EXPERIMENT_OUTPUT / "OUTER_CV_PREDICTIONS.csv.gz").is_file(),
        "Experiment outputs not generated yet",
    )
    def test_generated_outputs_are_paired_and_traceable(self) -> None:
        predictions = pd.read_csv(
            EXPERIMENT_OUTPUT / "OUTER_CV_PREDICTIONS.csv.gz"
        )
        verify_prediction_pairing(predictions)
        self.assertEqual(
            predictions.loc[
                predictions["variant"].eq("baseline"), "source_object_id"
            ].nunique(),
            119_690,
        )
        for name in [
            "EXPERIMENT1_CONFIG.json",
            "INNER_CV_SELECTION.csv",
            "OUTER_CV_METRICS.csv",
            "BASELINE_VS_WEIGHTED.csv",
            "LOW_DO_CLASSIFICATION.csv",
            "SITE_CLUSTERED_UNCERTAINTY.csv",
            "SITE_ERROR_COMPARISON.csv",
            "PREDICTION_SHIFT_ANALYSIS.csv",
        ]:
            self.assertTrue((EXPERIMENT_OUTPUT / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
