"""Phase 7 public-artifact and deployment-readiness checks."""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
APP_DATA = ROOT / "data" / "app"


class ReleaseReadinessTests(unittest.TestCase):
    def test_required_public_app_artifacts_exist(self) -> None:
        required = {
            "dataset_summary.csv",
            "yearly_summary.csv",
            "monthly_summary.csv",
            "missingness_summary.csv",
            "explorer_sample.csv.gz",
            "training_feature_reference.csv.gz",
            "example_input.csv",
            "holdout_prediction_sample.csv.gz",
            "manifest.json",
        }
        self.assertEqual({path.name for path in APP_DATA.iterdir()}, required)
        for filename in required:
            self.assertGreater((APP_DATA / filename).stat().st_size, 0)

    def test_public_app_artifact_manifest_matches_files(self) -> None:
        manifest = json.loads((APP_DATA / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["source_rows"], 151_031)
        self.assertEqual(manifest["training_rows"], 119_690)
        self.assertEqual(manifest["test_rows"], 31_341)
        self.assertEqual(len(pd.read_csv(APP_DATA / "explorer_sample.csv.gz")), manifest["explorer_sample_rows"])
        self.assertEqual(len(pd.read_csv(APP_DATA / "training_feature_reference.csv.gz")), 119_690)
        self.assertEqual(len(pd.read_csv(APP_DATA / "holdout_prediction_sample.csv.gz")), 5_000)

    def test_example_is_complete_and_is_not_labelled_by_risk(self) -> None:
        example = pd.read_csv(APP_DATA / "example_input.csv")
        measurement_columns = [
            "bod_mg_l",
            "ammonia_n_mg_l",
            "nitrite_n_mg_l",
            "nitrate_n_mg_l",
            "soluble_reactive_phosphorus_mg_l",
            "ph",
            "alkalinity_mg_l",
            "conductivity_us_cm",
            "suspended_solids_mg_l",
        ]
        self.assertEqual(len(example), 1)
        self.assertFalse(example[measurement_columns].isna().any(axis=None))
        self.assertFalse(any("risk" in column.lower() or "safe" in column.lower() for column in example.columns))

    def test_release_configuration_protects_secrets_and_large_model(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn(".streamlit/secrets.toml", gitignore)
        self.assertIn("!models/phase4_selected_model.joblib", gitignore)
        self.assertIn("models/phase4_selected_model.joblib filter=lfs", attributes)
        self.assertFalse((ROOT / ".streamlit" / "secrets.toml").exists())

    def test_readme_local_links_resolve(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        targets = re.findall(r"!?(?:\[[^]]*\])\(([^)]+)\)", readme)
        missing: list[str] = []
        for target in targets:
            if target.startswith(("http://", "https://", "#")):
                continue
            clean = target.split("#", 1)[0]
            if clean and not (ROOT / clean).exists():
                missing.append(target)
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
