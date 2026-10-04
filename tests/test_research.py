"""Critical research contracts; synthetic fixtures are not scientific evidence."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.research_analysis import (assert_disjoint, chronological_split, error_summary,
                                   interval_predictions, residual_frame, residual_radius,
                                   spatiotemporal_split, target_distribution)
from src.research_config import DATE, GROUP, TARGET, FEATURE_SETS, ResearchConfig
from src.research_experiments import ResearchRunner, research_pipeline, execute, verified_research
from src.research_reporting import markdown_table
from src.preprocessing import grouped_station_holdout


def synthetic_data():
    rng = np.random.default_rng(72)
    rows = []
    for station in range(20):
        for year in range(2016, 2025):
            row = {feature: float(rng.uniform(0, 1)) for feature in FEATURE_SETS["full"][0]}
            for feature in row:
                if feature.endswith("_limit"):
                    row[feature] = 0
            row.update(source_object_id=len(rows), station_code=f"synthetic_{station}",
                       sample_date=f"{year}-06-15", sample_year=year,
                       dissolved_oxygen_mg_l=6 + row["ph"] * 3)
            rows.append(row)
    frame = pd.DataFrame(rows)
    frame.loc[::13, "bod_mg_l"] = np.nan
    return frame


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.data = synthetic_data()
        self.config = ResearchConfig(n_estimators=2, cv_folds=2, n_jobs=1,
                                     permutation_rows=20, permutation_repeats=2, fast=True)

    def test_station_disjoint_partitions_and_reject_leakage(self):
        train, test = grouped_station_holdout(self.data)
        assert_disjoint(self.data, train, test, stations=True)
        with self.assertRaises(ValueError):
            assert_disjoint(self.data, train, train)
        with self.assertRaises(ValueError):
            assert_disjoint(self.data, np.array([0]), np.array([1]), stations=True)

    def test_strict_temporal_order_even_when_input_is_shuffled(self):
        data = self.data.sample(frac=1, random_state=8).reset_index(drop=True)
        train, validation, test = chronological_split(data)
        assert_disjoint(data, train, validation, test)
        self.assertEqual(len(train) + len(validation) + len(test), len(data))
        self.assertLess(data.iloc[train][DATE].max(), data.iloc[validation][DATE].min())
        self.assertLess(data.iloc[validation][DATE].max(), data.iloc[test][DATE].min())
        self.assertEqual(data.iloc[test].sample_year.min(), 2022)
        self.assertTrue(data.iloc[train][DATE].is_monotonic_increasing)
        with self.assertRaises(ValueError):
            chronological_split(data[data.sample_year < 2019])

    def test_metrics_and_residual_direction(self):
        frame = self.data.iloc[:3].copy()
        frame[TARGET] = [1, 2, 3]
        errors = residual_frame(frame, np.array([2, 2, 2]))
        result = error_summary(errors)
        self.assertAlmostEqual(result["mae"], 2 / 3)
        self.assertAlmostEqual(result["rmse"], np.sqrt(2 / 3))
        self.assertEqual(result["r2"], 0)
        self.assertEqual(result["bias"], 0)
        self.assertEqual(errors.residual.tolist(), [-1, 0, 1])

    def test_feature_sets_exclude_metadata_and_truly_ablate_indicators(self):
        forbidden = {TARGET, GROUP, DATE, "source_object_id", "Q_DO"}
        for name, (features, indicators) in FEATURE_SETS.items():
            self.assertTrue(forbidden.isdisjoint(features))
            self.assertEqual(len(features), len(set(features)))
            pipe = research_pipeline(self.config, name)
            self.assertEqual(pipe.get_params()["preprocessing__numeric__imputer__add_indicator"], indicators)
            pipe.fit(self.data[features], self.data[TARGET])
            names = pipe.named_steps["preprocessing"].get_feature_names_out()
            self.assertEqual(any("missingindicator" in f for f in names), indicators)
        self.assertEqual(len(FEATURE_SETS["full"][0]), 25)

    def test_imputer_learns_only_training_rows(self):
        features = FEATURE_SETS["full"][0]
        train = self.data.iloc[:80].copy()
        test = self.data.iloc[80:].copy()
        train["bod_mg_l"] = 2.
        test["bod_mg_l"] = 999.
        pipe = research_pipeline(self.config)
        pipe.fit(train[features], train[TARGET])
        transformer = pipe.named_steps["preprocessing"]
        imputer = transformer.named_transformers_["numeric"].named_steps["imputer"]
        before = imputer.statistics_.copy()
        pipe.predict(test[features])
        np.testing.assert_array_equal(before, imputer.statistics_)
        self.assertEqual(before[0], 2.)

    def test_finite_sample_interval_rank_and_boundary_coverage(self):
        radius = residual_radius(np.arange(1, 11), .9)
        self.assertEqual(radius, 10.)  # ceil(11*.9)=10; not interpolated percentile
        frame = residual_frame(self.data.iloc[:3].assign(**{TARGET: [-1, 1, 2]}), np.zeros(3))
        intervals = interval_predictions(frame, 1.)
        self.assertEqual(intervals.covered.tolist(), [True, True, False])
        self.assertTrue(((intervals.upper - intervals.lower) == 2).all())
        for bad in ([], [np.nan], [1, 2]):
            with self.assertRaises(ValueError):
                residual_radius(np.array(bad), .9)

    def test_small_experiment_outputs_and_calibration_separation(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = ResearchRunner(self.data, Path(directory), self.config)
            random, grouped, temporal = runner.random(), runner.grouped(), runner.temporal()
            runner.save_table("validation_comparison", pd.DataFrame([random, grouped, temporal]))
            runner.ablation()
            runner.errors()
            runner.uncertainty()
            runner.importance()
            runner.shift()
            self.assertEqual(grouped["station_overlap"], 0)
            self.assertGreater(random["station_overlap"], 0)
            self.assertEqual(len(runner.tables["ablation_results"]), 4)
            self.assertEqual(len(runner.tables["uncertainty_results"]), 2)
            split = pd.read_csv(Path(directory) / "predictions/split_station_calibration.csv.gz")
            roles = {key: set(part[GROUP]) for key, part in split.groupby("partition")}
            self.assertTrue(roles["train"].isdisjoint(roles["calibration"]))
            self.assertTrue(roles["test"].isdisjoint(roles["calibration"]))
            for name in runner.tables:
                self.assertTrue((Path(directory) / f"tables/{name}.csv").is_file())
            self.assertIn("| strategy |", markdown_table(runner.tables["validation_comparison"]))

    def test_spatiotemporal_station_time_and_exact_test_integrity(self):
        parts, inventory = spatiotemporal_split(self.data)
        train, test = self.data.iloc[parts["train"]], self.data.iloc[parts["test"]]
        heldout = set(inventory.loc[inventory.held_out, GROUP])
        self.assertTrue(set(train[GROUP]).isdisjoint(test[GROUP]))
        self.assertTrue(train.sample_year.le(2021).all())
        self.assertTrue(test.sample_year.ge(2022).all())
        self.assertLess(train[DATE].max(), test[DATE].min())
        self.assertEqual(set(parts["test"]), set(np.flatnonzero(
            self.data[GROUP].isin(heldout) & self.data.sample_year.ge(2022))))
        self.assertFalse(train[GROUP].isin(heldout).any())
        self.assertEqual(sum(map(len, parts.values())), len(self.data))

    def test_spatiotemporal_determinism_independent_of_row_order(self):
        _, first = spatiotemporal_split(self.data, seed=42)
        _, repeated = spatiotemporal_split(self.data, seed=42)
        _, shuffled = spatiotemporal_split(self.data.sample(frac=1, random_state=11), seed=42)
        pd.testing.assert_frame_equal(first, repeated)
        pd.testing.assert_frame_equal(first, shuffled)
        self.assertEqual(first.held_out.sum(), 4)

    def test_spatiotemporal_eligibility_accounts_for_all_stations(self):
        extra = self.data.iloc[:2].copy()
        extra[GROUP] = ["history_only", "future_only"]
        extra[DATE] = ["2000-01-01", "2024-01-01"]
        extra["sample_year"] = [2000, 2024]
        data = pd.concat([self.data, extra], ignore_index=True)
        parts, inventory = spatiotemporal_split(data)
        inventory = inventory.set_index(GROUP)
        self.assertEqual(inventory.loc["history_only", "eligibility_reason"], "historical_only")
        self.assertEqual(inventory.loc["future_only", "eligibility_reason"], "future_only")
        self.assertIn(len(data)-2, parts["train"])
        self.assertIn(len(data)-1, parts["unused_other_future"])
        self.assertEqual(inventory.eligible.sum(), 20)

    def test_spatiotemporal_rejects_invalid_dates_and_insufficient_stations(self):
        with self.assertRaises(ValueError):
            spatiotemporal_split(self.data.assign(sample_date=None))
        with self.assertRaises(ValueError):
            spatiotemporal_split(self.data[self.data.sample_year.le(2021)])

    def test_spatiotemporal_metrics_metadata_and_training_only_preprocessing(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = ResearchRunner(self.data, Path(directory), self.config)
            runner.tables["feature_importance"] = pd.DataFrame({"feature": ["bod_mg_l", "ph"]})
            result = runner.spatiotemporal()
            required = {"mae", "rmse", "r2", "train_rows", "test_rows", "train_stations", "test_stations",
                        "train_first_date", "train_last_date", "test_first_date", "test_last_date",
                        "train_target_mean", "test_target_mean", "train_target_median", "test_target_median",
                        "test_low_do_fraction", "median_absolute_error", "p90_absolute_error", "p95_absolute_error"}
            self.assertTrue(required.issubset(result))
            self.assertTrue(np.isfinite([result[k] for k in ("mae", "rmse", "r2")]).all())
            self.assertEqual(result["station_overlap"], 0)
            self.assertEqual(result["test_rows"], 12)
            parts, _ = spatiotemporal_split(self.data)
            imputer = runner.models["spatiotemporal"].named_steps["preprocessing"].named_transformers_["numeric"].named_steps["imputer"]
            self.assertEqual(imputer.statistics_[0], self.data.iloc[parts["train"]].bod_mg_l.median())
            errors = runner.tables["spatiotemporal_error_by_do_range"]
            self.assertEqual(errors.sample_count.sum(), 12)
            empty = errors[errors.sample_count.eq(0)]
            self.assertTrue(empty.mae.isna().all())
            self.assertTrue(errors.small_sample.all())
            self.assertEqual(len(runner.fits), 1)
            self.assertTrue((Path(directory) / "predictions/spatiotemporal.csv.gz").is_file())
            self.assertTrue((Path(directory) / "predictions/split_spatiotemporal.csv.gz").is_file())

    def test_target_distribution_preserves_exact_bin_boundaries(self):
        result = target_distribution(pd.DataFrame({"actual": [3, 4, 8, 12]}))
        for label in ("<4", "4–<8", "8–<12", "≥12"):
            self.assertEqual(result[f"fraction_{label}"], .25)

    def test_all_experiments_include_spatiotemporal_without_changing_old_splits(self):
        root = Path(__file__).resolve().parents[1]
        raw = self.data.assign(StationCode=self.data[GROUP])
        audit = {"raw_rows": len(raw), "processed_rows": len(raw), "processed_stations": 20}
        # Use every synthetic row while retaining tiny model settings.
        from dataclasses import replace
        config = replace(self.config, fast=False)
        with tempfile.TemporaryDirectory() as directory, \
             patch("src.research_experiments.load_niea_raw", return_value=raw), \
             patch("src.research_experiments.prepare_water_quality_modeling_data", return_value=(self.data, audit)), \
             patch("src.research_experiments.protected_hashes", return_value={}):
            runner = execute(root, Path(directory), config, "all")
            self.assertEqual(len(runner.tables["validation_comparison"]), 4)
            self.assertEqual(len(runner.tables["validation_target_distribution"]), 4)
            self.assertEqual(runner.splits["temporal"]["train"]["last_date"], "2018-06-15")
            self.assertEqual(runner.splits["spatiotemporal"]["train"]["last_date"], "2021-06-15")
            self.assertIn("## Spatiotemporal Generalization", (Path(directory)/"reports/RESEARCH_RESULTS.md").read_text())
            verified_research(Path(directory))
            (Path(directory)/"tables/spatiotemporal_validation.csv").write_text("altered")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                verified_research(Path(directory))


if __name__ == "__main__":
    unittest.main()
