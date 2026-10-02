"""Practical Phase 3 tests using clearly synthetic software-test records."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.pipeline import Pipeline

from src.preprocessing import (
    WATER_QUALITY_BASELINE_FEATURES,
    WATER_QUALITY_GROUP,
    WATER_QUALITY_TARGET,
    build_water_quality_preprocessor,
    grouped_station_holdout,
    load_niea_raw,
    prepare_water_quality_modeling_data,
)


def synthetic_raw_data() -> pd.DataFrame:
    """Return small schema-compatible records that are not research data."""
    rows = 12
    return pd.DataFrame(
        {
            "OBJECTID": range(1, rows + 1),
            "StationCode": ["station_a"] * 4 + ["station_b"] * 4 + ["station_c"] * 4,
            "Date": pd.date_range("2020-01-01", periods=rows).strftime("%Y/%m/%d"),
            "DO_mg_l_": [8.0, 8.4, 8.8, 9.0, 7.1, 7.4, 7.8, 8.1, 10.0, 10.4, 10.8, 11.0],
            "Q_DO": [None] * rows,
            "BOD_mg_l_": [1.0, 1.2, None, 1.4, 2.0, 2.2, 2.4, 2.6, 1.1, 1.3, 1.5, 1.7],
            "Q_BOD": ["<", None, None, None, None, ">", None, None, None, None, None, None],
            "NH4_N_mg_l_": [0.04] * rows,
            "Q_NH4N": ["<"] * 3 + [None] * 9,
            "NO2_N_mg_l_": [0.01] * rows,
            "Q_NO2N": [None] * rows,
            "NO3_N_mg_l_": [1.0, 1.1, 1.2, 1.3] * 3,
            "Q_NO3N": [None] * rows,
            "P_SOL__mg_l_": [0.05] * rows,
            "Q_PSOL": [None] * rows,
            "PH_PHUNITS_": [7.0, 7.1, 7.2, 7.3] * 3,
            "Q_pH": [None] * rows,
            "ALK_mg_l_": [80.0, 82.0, None, 84.0] * 3,
            "Q_Alk": [None, None, "<", None] * 3,
            "COND_US_CM_": [250.0, 260.0, 270.0, None] * 3,
            "Q_COND": [None] * rows,
            "SS_mg_l_": [3.0, 4.0, 5.0, 6.0] * 3,
            "Q_SS": ["<", None, None, None] * 3,
        }
    )


class WaterQualityPipelineTests(unittest.TestCase):
    def test_preparation_does_not_overwrite_raw_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw_path = Path(directory) / "raw.csv"
            synthetic_raw_data().to_csv(raw_path, index=False)
            before = hashlib.sha256(raw_path.read_bytes()).hexdigest()
            prepare_water_quality_modeling_data(load_niea_raw(raw_path))
            after = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        self.assertEqual(before, after)

    def test_target_and_target_qualifier_are_not_predictors(self) -> None:
        self.assertNotIn(WATER_QUALITY_TARGET, WATER_QUALITY_BASELINE_FEATURES)
        self.assertNotIn("Q_DO", WATER_QUALITY_BASELINE_FEATURES)
        self.assertNotIn("q_do", WATER_QUALITY_BASELINE_FEATURES)

    def test_grouped_split_has_no_station_overlap(self) -> None:
        processed, _ = prepare_water_quality_modeling_data(synthetic_raw_data())
        train_indices, test_indices = grouped_station_holdout(
            processed, test_size=1 / 3, random_state=42
        )
        train_stations = set(processed.iloc[train_indices][WATER_QUALITY_GROUP])
        test_stations = set(processed.iloc[test_indices][WATER_QUALITY_GROUP])
        self.assertTrue(train_stations.isdisjoint(test_stations))

    def test_pipeline_transforms_and_predicts_without_nan_output(self) -> None:
        processed, _ = prepare_water_quality_modeling_data(synthetic_raw_data())
        train_indices, test_indices = grouped_station_holdout(
            processed, test_size=1 / 3, random_state=42
        )
        X_train = processed.iloc[train_indices][WATER_QUALITY_BASELINE_FEATURES]
        X_test = processed.iloc[test_indices][WATER_QUALITY_BASELINE_FEATURES]
        y_train = processed.iloc[train_indices][WATER_QUALITY_TARGET]

        pipeline = Pipeline(
            [
                ("preprocessing", build_water_quality_preprocessor()),
                ("model", DummyRegressor(strategy="mean")),
            ]
        )
        pipeline.fit(X_train, y_train)
        transformed = pipeline.named_steps["preprocessing"].transform(X_test)
        predictions = pipeline.predict(X_test)

        self.assertFalse(np.isnan(transformed).any())
        self.assertEqual(len(predictions), len(X_test))
        self.assertFalse(np.isnan(predictions).any())


if __name__ == "__main__":
    unittest.main()
