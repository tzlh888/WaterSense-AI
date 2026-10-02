"""Small unit tests using clearly synthetic software-test data."""

import unittest

import pandas as pd

from src.preprocessing import (
    build_preprocessor,
    clean_column_names,
    identify_feature_types,
    split_features_target,
)


class PreprocessingTests(unittest.TestCase):
    def test_column_names_are_normalised_without_mutating_input(self) -> None:
        original = pd.DataFrame({" pH Value ": [7.0], "Site-Type": ["river"]})
        cleaned = clean_column_names(original)

        self.assertEqual(cleaned.columns.tolist(), ["ph_value", "site_type"])
        self.assertEqual(original.columns.tolist(), [" pH Value ", "Site-Type"])

    def test_column_name_collision_is_rejected(self) -> None:
        data = pd.DataFrame([[1, 2]], columns=["Site ID", "site-id"])
        with self.assertRaises(ValueError):
            clean_column_names(data)

    def test_target_is_separated_and_feature_types_are_identified(self) -> None:
        data = pd.DataFrame(
            {"measurement": [1.0, 2.0], "site": ["a", "b"], "target": [0, 1]}
        )
        features, target = split_features_target(data, "target")
        numeric, categorical = identify_feature_types(features)

        self.assertEqual(target.tolist(), [0, 1])
        self.assertEqual(numeric, ["measurement"])
        self.assertEqual(categorical, ["site"])
        self.assertIsNotNone(build_preprocessor(features))


if __name__ == "__main__":
    unittest.main()

