"""Generate predictions with a trained WaterSense AI model artifact."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

try:
    from .preprocessing import clean_column_names, load_data
except ImportError:  # Allows `python src/predict.py ...` from the project root.
    from preprocessing import clean_column_names, load_data


def load_artifact(path: str | Path) -> dict[str, Any]:
    """Load and minimally validate a saved training artifact."""
    artifact_path = Path(path)
    if not artifact_path.is_file():
        raise FileNotFoundError(f"Model artifact not found: {artifact_path}")
    artifact = joblib.load(artifact_path)
    required_keys = {"pipeline", "task", "target_column", "feature_columns"}
    if not isinstance(artifact, dict) or not required_keys.issubset(artifact):
        raise ValueError("File is not a recognised WaterSense AI model artifact.")
    return artifact


def predict(artifact: dict[str, Any], data: pd.DataFrame) -> pd.DataFrame:
    """Predict from a dataframe after checking its required feature columns."""
    cleaned = clean_column_names(data)
    feature_columns = artifact["feature_columns"]
    missing = sorted(set(feature_columns) - set(cleaned.columns))
    if missing:
        raise ValueError(f"Prediction data is missing required columns: {missing}")

    result = cleaned.copy()
    result["prediction"] = artifact["pipeline"].predict(cleaned[feature_columns])
    return result


def main() -> None:
    """Run prediction from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Path to a .joblib artifact.")
    parser.add_argument("--data", required=True, help="Path to a CSV file.")
    parser.add_argument("--output", required=True, help="Destination CSV path.")
    args = parser.parse_args()

    artifact = load_artifact(args.model)
    result = predict(artifact, load_data(args.data))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    print(f"Saved {len(result)} predictions to {output_path}")


if __name__ == "__main__":
    main()

