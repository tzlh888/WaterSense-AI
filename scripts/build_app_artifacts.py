"""Build lightweight, reproducible data artifacts for the Streamlit app.

The script never changes the raw data, processed modelling table, saved model, or
executed model results. Run it from the repository root after Phase 4 artifacts
have been reproduced.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_PATH = ROOT / "data" / "processed" / "water_quality_modeling.csv"
HOLDOUT_PREDICTIONS_PATH = ROOT / "results" / "phase4_holdout_predictions.csv"
OUTPUT_DIR = ROOT / "data" / "app"

MEASUREMENTS = {
    "dissolved_oxygen_mg_l": "Dissolved oxygen",
    "bod_mg_l": "BOD",
    "ammonia_n_mg_l": "Ammonia as N",
    "nitrite_n_mg_l": "Nitrite as N",
    "nitrate_n_mg_l": "Nitrate as N",
    "soluble_reactive_phosphorus_mg_l": "Soluble reactive phosphorus",
    "ph": "pH",
    "alkalinity_mg_l": "Alkalinity",
    "conductivity_us_cm": "Conductivity",
    "suspended_solids_mg_l": "Suspended solids",
}

MODEL_MEASUREMENTS = [column for column in MEASUREMENTS if column != "dissolved_oxygen_mg_l"]
CENSOR_FLAGS = [
    "bod_is_below_limit",
    "bod_is_above_limit",
    "ammonia_is_below_limit",
    "ammonia_is_above_limit",
    "nitrite_is_below_limit",
    "nitrite_is_above_limit",
    "nitrate_is_below_limit",
    "nitrate_is_above_limit",
    "phosphorus_is_below_limit",
    "phosphorus_is_above_limit",
    "alkalinity_is_below_limit",
    "alkalinity_is_above_limit",
    "suspended_solids_is_below_limit",
    "suspended_solids_is_above_limit",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def grouped_split(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_index, test_index = next(splitter.split(data, groups=data["station_code"]))
    train = data.iloc[train_index].copy()
    test = data.iloc[test_index].copy()
    observed = (len(train), len(test), train["station_code"].nunique(), test["station_code"].nunique())
    if observed != (119_690, 31_341, 672, 168):
        raise RuntimeError(f"Processed data no longer reproduces the verified split: {observed}")
    if set(train["station_code"]) & set(test["station_code"]):
        raise RuntimeError("Training and test stations overlap.")
    return train, test


def build_explorer_sample(data: pd.DataFrame) -> pd.DataFrame:
    """Keep every station plus a balanced deterministic sample across years."""
    one_per_station = data.sort_values("sample_date").groupby("station_code", sort=True).head(1)
    per_year = pd.concat(
        [group.sample(n=min(400, len(group)), random_state=42) for _, group in data.groupby("sample_year")],
        ignore_index=True,
    )
    sample = pd.concat([one_per_station, per_year], ignore_index=True).drop_duplicates()
    columns = ["station_code", "sample_date", "sample_year", "sample_month", *MEASUREMENTS]
    return sample[columns].sort_values(["sample_date", "station_code"]).reset_index(drop=True)


def main() -> None:
    if not PROCESSED_PATH.is_file():
        raise FileNotFoundError(f"Missing processed data: {PROCESSED_PATH}")
    if not HOLDOUT_PREDICTIONS_PATH.is_file():
        raise FileNotFoundError(f"Missing Phase 4 predictions: {HOLDOUT_PREDICTIONS_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(PROCESSED_PATH, parse_dates=["sample_date"])
    train, test = grouped_split(data)

    summary = pd.DataFrame(
        [
            ("modelling_observations", len(data)),
            ("eligible_stations", data["station_code"].nunique()),
            ("first_sample", data["sample_date"].min().date().isoformat()),
            ("last_sample", data["sample_date"].max().date().isoformat()),
            ("training_observations", len(train)),
            ("training_stations", train["station_code"].nunique()),
            ("test_observations", len(test)),
            ("test_stations", test["station_code"].nunique()),
        ],
        columns=["metric", "value"],
    )
    summary.to_csv(OUTPUT_DIR / "dataset_summary.csv", index=False)

    yearly = data.groupby("sample_year").agg(
        records=("station_code", "size"),
        stations=("station_code", "nunique"),
        mean_do_mg_l=("dissolved_oxygen_mg_l", "mean"),
        median_do_mg_l=("dissolved_oxygen_mg_l", "median"),
    ).reset_index()
    yearly.to_csv(OUTPUT_DIR / "yearly_summary.csv", index=False)

    monthly = data.groupby("sample_month").agg(
        records=("station_code", "size"),
        stations=("station_code", "nunique"),
        mean_do_mg_l=("dissolved_oxygen_mg_l", "mean"),
        median_do_mg_l=("dissolved_oxygen_mg_l", "median"),
    ).reset_index()
    monthly.to_csv(OUTPUT_DIR / "monthly_summary.csv", index=False)

    missingness = pd.DataFrame(
        {
            "feature": list(MEASUREMENTS),
            "measurement": list(MEASUREMENTS.values()),
            "missing_count": [int(data[column].isna().sum()) for column in MEASUREMENTS],
            "missing_percent": [float(data[column].isna().mean() * 100) for column in MEASUREMENTS],
        }
    )
    missingness.to_csv(OUTPUT_DIR / "missingness_summary.csv", index=False)

    explorer = build_explorer_sample(data)
    explorer.to_csv(OUTPUT_DIR / "explorer_sample.csv.gz", index=False, compression="gzip")
    train[MODEL_MEASUREMENTS].to_csv(
        OUTPUT_DIR / "training_feature_reference.csv.gz", index=False, compression="gzip"
    )

    complete = train.dropna(subset=MODEL_MEASUREMENTS)
    exact = complete[(complete[CENSOR_FLAGS].fillna(0) == 0).all(axis=1)]
    if exact.empty:
        raise RuntimeError("No complete exact monitoring record is available for the example input.")
    exact[["sample_date", "station_code", *MODEL_MEASUREMENTS, *CENSOR_FLAGS]].head(1).to_csv(
        OUTPUT_DIR / "example_input.csv", index=False
    )

    predictions = pd.read_csv(HOLDOUT_PREDICTIONS_PATH)
    prediction_sample = predictions.sample(n=min(5_000, len(predictions)), random_state=42)
    prediction_sample.to_csv(
        OUTPUT_DIR / "holdout_prediction_sample.csv.gz", index=False, compression="gzip"
    )

    manifest = {
        "generator": "scripts/build_app_artifacts.py",
        "source": "data/processed/water_quality_modeling.csv",
        "source_sha256": sha256(PROCESSED_PATH),
        "source_rows": len(data),
        "training_rows": len(train),
        "test_rows": len(test),
        "explorer_sample_rows": len(explorer),
        "holdout_prediction_sample_rows": len(prediction_sample),
        "sampling_random_state": 42,
    }
    (OUTPUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
