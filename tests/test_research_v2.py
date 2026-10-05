"""Contracts for the scoped v2 robustness analysis."""

import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from src.research_analysis import spatiotemporal_split
from src.research_config import DATE, FEATURE_SETS, GROUP
from src.research_experiments import sha256
from src.research_v2 import (V2_SEEDS, basin_group_split, coverage_by_do, importance_aggregation,
                             reduced_feature_sets, split_summary)


def synthetic_data():
    rng = np.random.default_rng(72)
    rows = []
    for station in range(20):
        for year in range(2016, 2025):
            row = {feature: float(rng.uniform(0, 1)) for feature in FEATURE_SETS["full"][0]}
            row.update(source_object_id=len(rows), station_code=f"synthetic_{station}",
                       sample_date=f"{year}-06-15", sample_year=year,
                       dissolved_oxygen_mg_l=6 + row["ph"] * 3)
            rows.append(row)
    return pd.DataFrame(rows)


class ResearchV2Tests(unittest.TestCase):
    def setUp(self):
        self.data = synthetic_data()

    def test_exact_repeated_seeds_are_deterministic_and_strictly_separated(self):
        self.assertEqual(V2_SEEDS, (11, 23, 42, 57, 71, 89, 101, 123, 149, 173))
        for seed in V2_SEEDS:
            first, first_inventory = spatiotemporal_split(self.data, seed=seed)
            second, second_inventory = spatiotemporal_split(self.data, seed=seed)
            np.testing.assert_array_equal(first["train"], second["train"])
            np.testing.assert_array_equal(first["test"], second["test"])
            pd.testing.assert_frame_equal(first_inventory, second_inventory)
            train, test = self.data.iloc[first["train"]], self.data.iloc[first["test"]]
            self.assertTrue(set(train[GROUP]).isdisjoint(test[GROUP]))
            self.assertTrue(train.sample_year.le(2021).all())
            self.assertTrue(test.sample_year.ge(2022).all())
            self.assertLess(train[DATE].max(), test[DATE].min())

    def test_reduced_ablation_has_exactly_five_cumulative_groups(self):
        sets = reduced_feature_sets()
        self.assertEqual(list(sets), ["Core", "Core + Date", "Core + Date + Missingness",
                                     "Core + Date + Missingness + Censoring", "Full"])
        self.assertEqual(len(sets), 5)
        core, _ = sets["Core"]
        core_date, indicators = sets["Core + Date"]
        missing, missing_indicators = sets["Core + Date + Missingness"]
        censor, censor_indicators = sets["Core + Date + Missingness + Censoring"]
        full, full_indicators = sets["Full"]
        self.assertTrue(set(core).issubset(core_date))
        self.assertEqual(core_date, missing)
        self.assertFalse(indicators)
        self.assertTrue(missing_indicators and censor_indicators and full_indicators)
        self.assertTrue(set(missing).issubset(censor))
        self.assertTrue(set(censor).issubset(full))
        self.assertEqual(len(full), 25)

    def test_importance_aggregation_ranks_and_correlations(self):
        rows = []
        values = {1: [3., 2., 1.], 2: [2., 3., 1.], 3: [3., 1., 2.]}
        for fold, importances in values.items():
            ranks = pd.Series(importances).rank(ascending=False)
            for feature, value, rank in zip(["a", "b", "c"], importances, ranks):
                rows.append({"fold": fold, "feature": feature, "mae_increase": value,
                             "permutation_sd": .1 * fold, "rank": rank})
        summary, correlations = importance_aggregation(pd.DataFrame(rows))
        self.assertEqual(len(summary), 3)
        self.assertEqual(len(correlations), 3)
        self.assertAlmostEqual(summary.set_index("feature").loc["a", "mean_rank"], 4/3)
        self.assertTrue(summary.top5_fraction.eq(1).all())
        self.assertTrue(np.isfinite(correlations.spearman_r).all())
        broken = pd.DataFrame(rows[:-1])
        with self.assertRaises(ValueError):
            importance_aggregation(broken)

    def test_interval_coverage_uses_fixed_ranges_and_boundaries(self):
        frame = pd.DataFrame({"actual": [3., 4., 8., 12.],
                              "predicted": [4., 4., 7., 13.],
                              "covered": [False, True, False, True]})
        result = coverage_by_do(frame)
        self.assertEqual(result.do_range.tolist(), ["<4", "4–<8", "8–<12", "≥12"])
        self.assertEqual(result.sample_count.tolist(), [1, 1, 1, 1])
        self.assertEqual(result.empirical_coverage.tolist(), [0., 1., 0., 1.])

    def test_basin_split_has_zero_basin_and_station_overlap(self):
        data = self.data.copy()
        data["primary_basin"] = data[GROUP].str.extract(r"(\d+)")[0].astype(int).floordiv(4)
        train, test = basin_group_split(data, seed=42)
        self.assertTrue(set(data.iloc[train].primary_basin).isdisjoint(
            data.iloc[test].primary_basin))
        self.assertTrue(set(data.iloc[train][GROUP]).isdisjoint(data.iloc[test][GROUP]))
        broken = data.copy()
        broken.loc[broken.index[-1], GROUP] = broken.iloc[0][GROUP]
        with self.assertRaises(ValueError):
            basin_group_split(broken)

    def test_split_summary_uses_requested_statistics_only(self):
        summary = split_summary(pd.DataFrame({"mae": [1., 2., 3., 4.]}), ["mae"])
        self.assertEqual(summary.columns.tolist(), ["metric", "splits", "mean", "std",
                                                    "median", "iqr", "minimum", "maximum"])
        self.assertEqual(summary.iloc[0]["iqr"], 1.5)

    def test_v1_output_hashes_remain_unchanged_when_v2_exists(self):
        root = Path(__file__).resolve().parents[1]
        v2_manifest = root / "research_outputs_v2/manifests/v2_manifest.json"
        if not v2_manifest.exists():
            self.skipTest("Full v2 output has not been generated in this checkout.")
        manifest = json.loads(v2_manifest.read_text())
        for name, expected in manifest["v1_output_hashes"].items():
            self.assertEqual(sha256(root / "research_outputs" / name), expected, name)
        self.assertEqual(sha256(root / "research_outputs/manifest.json"),
                         manifest["v1_manifest_sha256"])


if __name__ == "__main__":
    unittest.main()
