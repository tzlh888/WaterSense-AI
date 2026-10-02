"""Application-critical input-contract and model-loading tests."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from app.utils.model_input import (
    MEASUREMENT_FIELDS,
    PERCENTILE_POSITION_COLUMNS,
    build_model_input,
    cyclical_day_of_year,
    format_percentile_positions,
    input_percentile_positions,
    training_range_warnings,
)
from app.utils.model_loader import load_model_artifact


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def ordinary_values() -> dict[str, float | None]:
    return {
        "bod_mg_l": 2.0,
        "ammonia_n_mg_l": 0.04,
        "nitrite_n_mg_l": 0.02,
        "nitrate_n_mg_l": 1.5,
        "soluble_reactive_phosphorus_mg_l": 0.05,
        "ph": 7.5,
        "alkalinity_mg_l": 90.0,
        "conductivity_us_cm": 300.0,
        "suspended_solids_mg_l": 5.0,
    }


class ApplicationLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = load_model_artifact(
            PROJECT_ROOT / "models/phase4_selected_model.joblib"
        )
        cls.expected = cls.artifact["feature_columns"]

    def test_model_loads_with_verified_contract(self) -> None:
        self.assertEqual(self.artifact["target_column"], "dissolved_oxygen_mg_l")
        self.assertEqual(self.artifact["model_name"], "Random Forest")
        self.assertEqual(len(self.expected), 25)

    def test_ui_input_has_exact_expected_features_and_no_target(self) -> None:
        row = build_model_input(
            ordinary_values(), {}, date(2024, 6, 15), self.expected
        )
        self.assertEqual(row.columns.tolist(), self.expected)
        self.assertNotIn("dissolved_oxygen_mg_l", row.columns)
        self.assertNotIn("Q_DO", row.columns)

    def test_date_transformation_matches_processed_phase4_data(self) -> None:
        processed = pd.read_csv(
            PROJECT_ROOT / "data/processed/water_quality_modeling.csv", nrows=1
        ).iloc[0]
        day_sin, day_cos = cyclical_day_of_year(processed["sample_date"])
        self.assertAlmostEqual(day_sin, processed["day_of_year_sin"], places=12)
        self.assertAlmostEqual(day_cos, processed["day_of_year_cos"], places=12)

    def test_censoring_qualifiers_create_correct_flags(self) -> None:
        qualifiers = {
            "bod_mg_l": "below",
            "ammonia_n_mg_l": "above",
            "nitrite_n_mg_l": "below",
        }
        row = build_model_input(
            ordinary_values(), qualifiers, date(2024, 1, 1), self.expected
        ).iloc[0]
        self.assertEqual(row["bod_is_below_limit"], 1)
        self.assertEqual(row["bod_is_above_limit"], 0)
        self.assertEqual(row["ammonia_is_above_limit"], 1)
        self.assertEqual(row["nitrite_is_below_limit"], 1)
        self.assertEqual(row["nitrite_is_above_limit"], 0)

    def test_unavailable_measurement_remains_nan(self) -> None:
        values = ordinary_values()
        values["alkalinity_mg_l"] = None
        row = build_model_input(values, {}, date(2024, 3, 2), self.expected)
        self.assertTrue(np.isnan(row.iloc[0]["alkalinity_mg_l"]))
        self.assertEqual(row.iloc[0]["alkalinity_is_below_limit"], 0)

    def test_model_returns_one_finite_prediction(self) -> None:
        row = build_model_input(
            ordinary_values(), {}, date(2024, 6, 15), self.expected
        )
        predictions = self.artifact["pipeline"].predict(row)
        self.assertEqual(len(predictions), 1)
        self.assertTrue(np.isfinite(predictions[0]))

    def percentile_reference(self) -> pd.DataFrame:
        values = ordinary_values()
        return pd.DataFrame(
            {
                field["feature"]: [
                    float(values[field["feature"]]) - 1,
                    float(values[field["feature"]]),
                    float(values[field["feature"]]) + 1,
                ]
                for field in MEASUREMENT_FIELDS
            }
        )

    def test_percentile_positions_include_every_complete_measurement(self) -> None:
        row = build_model_input(
            ordinary_values(), {}, date(2024, 6, 15), self.expected
        )
        positions = input_percentile_positions(row, self.percentile_reference())
        self.assertEqual(len(positions), len(MEASUREMENT_FIELDS))
        self.assertEqual(positions.columns.tolist(), list(PERCENTILE_POSITION_COLUMNS))

    def test_percentile_positions_omit_one_missing_measurement(self) -> None:
        values = ordinary_values()
        values["ph"] = None
        row = build_model_input(values, {}, date(2024, 6, 15), self.expected)
        positions = input_percentile_positions(row, self.percentile_reference())
        self.assertEqual(len(positions), len(MEASUREMENT_FIELDS) - 1)
        self.assertNotIn("pH", positions["Measurement"].tolist())

    def test_percentile_positions_omit_multiple_missing_measurements(self) -> None:
        values = ordinary_values()
        values["ph"] = None
        values["alkalinity_mg_l"] = None
        values["conductivity_us_cm"] = None
        row = build_model_input(values, {}, date(2024, 6, 15), self.expected)
        positions = input_percentile_positions(row, self.percentile_reference())
        self.assertEqual(len(positions), len(MEASUREMENT_FIELDS) - 3)
        self.assertTrue(
            {"pH", "Alkalinity", "Conductivity"}.isdisjoint(
                positions["Measurement"]
            )
        )

    def test_percentile_positions_use_real_reference_values(self) -> None:
        row = build_model_input(
            ordinary_values(), {}, date(2024, 6, 15), self.expected
        )
        positions = input_percentile_positions(row, self.percentile_reference())
        self.assertTrue(
            np.allclose(positions["Training percentile"], 200 / 3)
        )
        display = format_percentile_positions(positions)
        self.assertTrue(
            (display["Training percentile"] == "66.7%").all()
        )

    def test_zero_usable_percentile_rows_keep_stable_columns(self) -> None:
        values = {field["feature"]: None for field in MEASUREMENT_FIELDS}
        row = build_model_input(values, {}, date(2024, 6, 15), self.expected)
        positions = input_percentile_positions(row, self.percentile_reference())
        self.assertTrue(positions.empty)
        self.assertEqual(positions.columns.tolist(), list(PERCENTILE_POSITION_COLUMNS))

    def test_empty_or_malformed_percentile_result_never_raises_key_error(self) -> None:
        for positions in (pd.DataFrame(), pd.DataFrame(columns=PERCENTILE_POSITION_COLUMNS)):
            display = format_percentile_positions(positions)
            self.assertTrue(display.empty)
            self.assertIn("Training percentile", display.columns)

    def test_example_monitoring_record_returns_finite_prediction(self) -> None:
        example = pd.read_csv(
            PROJECT_ROOT / "data/app/example_input.csv", parse_dates=["sample_date"]
        ).iloc[0]
        values = {
            field["feature"]: float(example[field["feature"]])
            for field in MEASUREMENT_FIELDS
        }
        row = build_model_input(values, {}, example["sample_date"], self.expected)
        prediction = float(self.artifact["pipeline"].predict(row)[0])
        self.assertTrue(np.isfinite(prediction))

    def test_training_range_checker_flags_only_outside_values(self) -> None:
        values = ordinary_values()
        row = build_model_input(values, {}, date(2024, 6, 15), self.expected)
        reference = pd.DataFrame(
            {
                field["feature"]: [
                    float(values[field["feature"]]) - 1,
                    float(values[field["feature"]]) + 1,
                ]
                for field in MEASUREMENT_FIELDS
            }
        )
        self.assertEqual(training_range_warnings(row, reference), [])
        row.loc[0, "conductivity_us_cm"] = 10_000
        warnings = training_range_warnings(row, reference)
        self.assertEqual([warning["feature"] for warning in warnings], ["conductivity_us_cm"])

    def test_application_code_contains_no_local_absolute_paths(self) -> None:
        for path in (PROJECT_ROOT / "app").rglob("*.py"):
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                self.assertNotRegex(text, r"(?:/Users/|/home/|[A-Za-z]:\\Users\\)")


if __name__ == "__main__":
    unittest.main()
