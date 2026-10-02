"""Cached loaders for application data and executed result tables."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from .app_helpers import PROJECT_ROOT


APP_DATA_DIR = PROJECT_ROOT / "data" / "app"
RESULTS_DIR = PROJECT_ROOT / "results"


def _app_data_path(filename: str) -> Path:
    path = APP_DATA_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"Required application artifact not found: {path}. "
            "Rebuild public app data with `python scripts/build_app_artifacts.py`."
        )
    return path


@st.cache_data(show_spinner=False)
def load_training_reference_data() -> pd.DataFrame:
    """Load measurement columns from the verified 672-station training split."""
    data = pd.read_csv(_app_data_path("training_feature_reference.csv.gz"))
    if len(data) != 119_690:
        raise RuntimeError("Training reference artifact has an unexpected row count.")
    return data


@st.cache_data(show_spinner="Loading exploration data…")
def load_explorer_sample() -> pd.DataFrame:
    """Load a deterministic real-record sample used for interactive charts."""
    return pd.read_csv(_app_data_path("explorer_sample.csv.gz"), parse_dates=["sample_date"])


@st.cache_data(show_spinner=False)
def load_app_table(filename: str) -> pd.DataFrame:
    """Load one allow-listed public app table."""
    allowed = {
        "dataset_summary.csv",
        "yearly_summary.csv",
        "monthly_summary.csv",
        "missingness_summary.csv",
        "example_input.csv",
        "holdout_prediction_sample.csv.gz",
    }
    if filename not in allowed:
        raise ValueError("Unrecognised application data artifact.")
    parse_dates = ["sample_date"] if filename == "example_input.csv" else None
    return pd.read_csv(_app_data_path(filename), parse_dates=parse_dates)


@st.cache_data(show_spinner=False)
def load_result_table(filename: str) -> pd.DataFrame:
    """Load one executed CSV result table by safe filename."""
    if Path(filename).name != filename or not filename.endswith(".csv"):
        raise ValueError("Result filename must be a plain CSV filename.")
    path = RESULTS_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Required result table not found: {path}")
    return pd.read_csv(path)
