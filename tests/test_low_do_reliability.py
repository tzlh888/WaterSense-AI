from __future__ import annotations

import math
import unittest

import pandas as pd

from src.low_do_reliability import (
    aggregate_repeated_observations,
    compute_low_do_metrics,
    site_clustered_bootstrap,
)


def predictions(rows: list[tuple[int, str, float, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        rows,
        columns=[
            "source_object_id",
            "station_code",
            "actual_do_mg_l",
            "predicted_do_mg_l",
        ],
    )


class LowDoReliabilityTests(unittest.TestCase):
    def test_low_do_threshold_is_strictly_below_four(self) -> None:
        result = compute_low_do_metrics(
            predictions([(1, "A", 3.999, 3.999), (2, "B", 4.0, 4.0)])
        )
        self.assertEqual(result["low_do_count"], 1)
        self.assertEqual(result["predicted_low_do_count"], 1)
        self.assertEqual(result["true_positive_count"], 1)

    def test_false_negative_count_and_rate(self) -> None:
        result = compute_low_do_metrics(
            predictions(
                [(1, "A", 2.0, 5.0), (2, "A", 3.0, 3.5), (3, "B", 7.0, 7.0)]
            )
        )
        self.assertEqual(result["false_negative_count"], 1)
        self.assertEqual(result["true_positive_count"], 1)
        self.assertAlmostEqual(result["low_do_recall"], 0.5)
        self.assertAlmostEqual(result["low_do_false_negative_rate"], 0.5)

    def test_zero_predicted_positives_marks_precision_and_f1_undefined(self) -> None:
        result = compute_low_do_metrics(
            predictions([(1, "A", 2.0, 6.0), (2, "B", 7.0, 8.0)])
        )
        self.assertEqual(result["predicted_low_do_count"], 0)
        self.assertTrue(math.isnan(result["low_do_precision"]))
        self.assertTrue(math.isnan(result["low_do_f1"]))
        self.assertFalse(result["precision_defined"])
        self.assertFalse(result["f1_defined"])

    def test_site_bootstrap_is_deterministic_and_reports_invalid_metrics(self) -> None:
        data = predictions([(1, "A", 2.0, 5.0)])
        first = site_clustered_bootstrap(data, n_resamples=25, seed=7)
        second = site_clustered_bootstrap(data, n_resamples=25, seed=7)
        pd.testing.assert_frame_equal(first.summary, second.summary)
        pd.testing.assert_frame_equal(first.replicate_metrics, second.replicate_metrics)
        r2 = first.summary.set_index("metric").loc["overall_r2"]
        self.assertEqual(r2["cluster_unit"], "station_code")
        self.assertEqual(r2["cluster_count"], 1)
        self.assertEqual(r2["invalid_resamples"], 25)

    def test_site_bootstrap_resamples_whole_clusters_not_rows(self) -> None:
        data = predictions(
            [
                (1, "A", 2.0, 5.0),
                (2, "A", 3.0, 5.0),
                (3, "B", 7.0, 7.0),
                (4, "B", 8.0, 8.0),
            ]
        )
        result = site_clustered_bootstrap(
            data, n_resamples=100, seed=19, metrics=["low_do_count"]
        )
        # Two station draws produce 0, 2, or 4 low rows. Row-level bootstrap
        # could produce 1 or 3 and would fail this assertion.
        self.assertTrue(
            set(result.replicate_metrics["low_do_count"].unique()).issubset(
                {0.0, 2.0, 4.0}
            )
        )

    def test_unique_observation_count_and_repeated_prediction_aggregation(self) -> None:
        data = pd.DataFrame(
            {
                "seed": [11, 23, 11],
                "source_object_id": [1, 1, 2],
                "station_code": ["A", "A", "B"],
                "sample_date": ["2022-01-01", "2022-01-01", "2022-02-01"],
                "sample_year": [2022, 2022, 2022],
                "actual": [3.0, 3.0, 8.0],
                "predicted": [5.0, 7.0, 8.0],
            }
        )
        appearances = compute_low_do_metrics(data)
        unique = aggregate_repeated_observations(data)
        self.assertEqual(appearances["sample_count"], 3)
        self.assertEqual(appearances["unique_observation_count"], 2)
        self.assertEqual(len(unique), 2)
        self.assertEqual(
            unique.loc[
                unique["source_object_id"] == 1, "predicted_do_mg_l"
            ].item(),
            6.0,
        )
        self.assertEqual(
            unique.loc[unique["source_object_id"] == 1, "appearance_count"].item(),
            2,
        )

    def test_repeated_split_identity_mismatch_is_rejected(self) -> None:
        data = predictions([(1, "A", 3.0, 5.0), (1, "B", 3.0, 6.0)])
        with self.assertRaisesRegex(ValueError, "invariant fields"):
            aggregate_repeated_observations(data)


if __name__ == "__main__":
    unittest.main()
