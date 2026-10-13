"""Tests for saved-evidence-only Experiment 1A attribution analysis."""

from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from src.experiment1a_attribution import (
    AttributionIntegrityError,
    classification_transitions,
    matched_inner_weight_pairs,
    pair_outer_predictions,
    selected_config_attribution,
)


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT1 = ROOT / "research_upgrade_v3/experiment1_weighted_regression"


class SyntheticAttributionTests(unittest.TestCase):
    """Fabricated fixtures test logic only and are not research evidence."""

    def test_prediction_pairing_and_transition_accounting(self) -> None:
        rows = []
        for variant, values in {
            "baseline": [5.0, 3.0, 5.0, 3.0],
            "weighted": [3.0, 5.0, 3.0, 3.0],
        }.items():
            for source_id, station, actual, predicted in zip(
                [1, 2, 3, 4], ["A", "A", "B", "B"],
                [2.0, 3.0, 5.0, 6.0], values,
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
        paired = pair_outer_predictions(pd.DataFrame(rows))
        transitions = classification_transitions(paired)
        self.assertEqual(len(paired), 4)
        self.assertEqual(int(transitions["observation_count"].sum()), 4)
        lookup = transitions.set_index(["baseline_state", "weighted_state"])
        self.assertEqual(int(lookup.loc[("FN", "TP"), "observation_count"]), 1)
        self.assertEqual(int(lookup.loc[("TN", "FP"), "observation_count"]), 1)

    def test_prediction_pairing_rejects_actual_mismatch(self) -> None:
        frame = pd.DataFrame(
            {
                "variant": ["baseline", "weighted"],
                "source_object_id": [1, 1],
                "station_code": ["A", "A"],
                "outer_fold": [1, 1],
                "actual_do_mg_l": [3.0, 3.1],
                "predicted_do_mg_l": [5.0, 4.0],
            }
        )
        with self.assertRaisesRegex(AttributionIntegrityError, "actual_do_mg_l"):
            pair_outer_predictions(frame)

    def test_inner_weight_pairs_require_identical_grid(self) -> None:
        base = {
            "outer_fold": 1,
            "inner_fold": 1,
            "family": "Model",
            "parameters_json": "{}",
            "run_status": "complete",
            **{metric: 1.0 for metric in (
                "overall_mae_mg_l", "low_do_mae_mg_l",
                "low_do_bias_prediction_minus_truth_mg_l", "low_do_recall",
                "low_do_precision", "low_do_f1", "false_positive_count",
                "true_positive_count",
            )},
        }
        frame = pd.DataFrame([{**base, "weight_multiplier": 1}])
        with self.assertRaisesRegex(AttributionIntegrityError, "do not match"):
            matched_inner_weight_pairs(frame)


@unittest.skipUnless(
    (EXPERIMENT1 / "OUTER_CV_PREDICTIONS.csv.gz").is_file(),
    "Experiment 1 evidence unavailable",
)
class HistoricalAttributionIntegrationTests(unittest.TestCase):
    """Identity checks against complete saved Experiment 1 evidence."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.inner = pd.read_csv(EXPERIMENT1 / "INNER_CV_FOLD_RESULTS.csv.gz")
        cls.selection = pd.read_csv(EXPERIMENT1 / "INNER_CV_SELECTION.csv")
        cls.predictions = pd.read_csv(EXPERIMENT1 / "OUTER_CV_PREDICTIONS.csv.gz")

    def test_complete_matched_weight_grid(self) -> None:
        pairs = matched_inner_weight_pairs(self.inner)
        self.assertEqual(len(pairs), 640)
        self.assertEqual(pairs.groupby(["family", "parameters_json"]).ngroups, 32)
        self.assertTrue(
            pairs["delta_weight8_minus_weight1__low_do_mae_mg_l"].lt(0).all()
        )
        self.assertTrue(
            pairs["delta_weight8_minus_weight1__low_do_recall"].gt(0).all()
        )

    def test_selected_configuration_decomposition_is_complete(self) -> None:
        result = selected_config_attribution(self.selection)
        self.assertEqual(len(result), 5)
        self.assertTrue(
            result[
                "weight_delta_weight8_minus_weight1__pooled_low_do_mae_mg_l"
            ].lt(0).all()
        )
        self.assertTrue(
            result[
                "weight_delta_weight8_minus_weight1__pooled_low_do_recall"
            ].gt(0).all()
        )

    def test_outer_predictions_cover_each_development_row_once(self) -> None:
        paired = pair_outer_predictions(self.predictions)
        self.assertEqual(len(paired), 119_690)
        self.assertEqual(paired["source_object_id"].nunique(), 119_690)
        self.assertEqual(paired["station_code"].nunique(), 672)
        self.assertEqual(int(paired["actual_low_do"].sum()), 758)


if __name__ == "__main__":
    unittest.main()
