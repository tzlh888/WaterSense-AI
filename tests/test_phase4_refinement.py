"""Phase 4 group-validation and saved-artifact checks."""

from __future__ import annotations

import unittest
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.preprocessing import (
    WATER_QUALITY_FEATURE_SETS,
    WATER_QUALITY_GROUP,
    WATER_QUALITY_TARGET,
    build_water_quality_feature_preprocessor,
)
from src.refine import fixed_phase3_split, group_fold_indices


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Phase4RefinementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = pd.read_csv(
            PROJECT_ROOT / "data/processed/water_quality_modeling.csv"
        )

    def test_group_cv_and_final_test_stations_never_overlap(self) -> None:
        training, test = fixed_phase3_split(self.data)
        final_test_stations = set(self.data.iloc[test][WATER_QUALITY_GROUP])
        for fold_train, fold_validation in group_fold_indices(self.data, training):
            train_stations = set(self.data.iloc[fold_train][WATER_QUALITY_GROUP])
            validation_stations = set(
                self.data.iloc[fold_validation][WATER_QUALITY_GROUP]
            )
            self.assertTrue(train_stations.isdisjoint(validation_stations))
            self.assertTrue(final_test_stations.isdisjoint(train_stations))
            self.assertTrue(final_test_stations.isdisjoint(validation_stations))

    def test_feature_sets_exclude_target_and_target_qualifier(self) -> None:
        for feature_columns in WATER_QUALITY_FEATURE_SETS.values():
            self.assertNotIn(WATER_QUALITY_TARGET, feature_columns)
            self.assertNotIn("Q_DO", feature_columns)

    def test_feature_transformers_are_reproducible_and_finite(self) -> None:
        training, _ = fixed_phase3_split(self.data)
        sample = self.data.iloc[training[:500]]
        for feature_columns in WATER_QUALITY_FEATURE_SETS.values():
            first = build_water_quality_feature_preprocessor(feature_columns)
            second = build_water_quality_feature_preprocessor(feature_columns)
            first_values = first.fit_transform(sample[feature_columns])
            second_values = second.fit_transform(sample[feature_columns])
            self.assertTrue(np.isfinite(first_values).all())
            np.testing.assert_allclose(first_values, second_values)

    def test_saved_final_pipeline_reloads_and_predicts_expected_rows(self) -> None:
        artifact = joblib.load(PROJECT_ROOT / "models/phase4_selected_model.joblib")
        sample = self.data.iloc[:7]
        predictions = artifact["pipeline"].predict(
            sample[artifact["feature_columns"]]
        )
        self.assertEqual(len(predictions), len(sample))
        self.assertTrue(np.isfinite(predictions).all())


if __name__ == "__main__":
    unittest.main()
