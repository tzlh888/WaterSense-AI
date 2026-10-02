"""Load and validate the immutable Phase 4 model artifact."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import streamlit as st

from .app_helpers import PROJECT_ROOT


DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "phase4_selected_model.joblib"
REQUIRED_ARTIFACT_KEYS = {
    "pipeline",
    "task",
    "target_column",
    "feature_columns",
    "feature_set",
    "model_name",
    "parameters",
}


def load_model_artifact(path: str | Path = DEFAULT_MODEL_PATH) -> dict[str, Any]:
    """Load the saved pipeline; never train a replacement implicitly."""
    artifact_path = Path(path)
    if not artifact_path.is_file():
        raise FileNotFoundError(
            f"Model artifact not found at {artifact_path}. "
            "Reproduce it from the repository root with `python -m src.refine`."
        )
    artifact = joblib.load(artifact_path)
    if not isinstance(artifact, dict) or not REQUIRED_ARTIFACT_KEYS.issubset(artifact):
        raise ValueError("The file is not a recognised Phase 4 WaterSense artifact.")
    if artifact["task"] != "regression":
        raise ValueError("The application requires the verified regression artifact.")
    if artifact["target_column"] != "dissolved_oxygen_mg_l":
        raise ValueError("Unexpected model target in saved artifact.")
    if "dissolved_oxygen_mg_l" in artifact["feature_columns"] or "Q_DO" in artifact["feature_columns"]:
        raise ValueError("Target or target qualifier found in prediction features.")
    return artifact


@st.cache_resource(show_spinner="Loading the verified model…")
def load_cached_model() -> dict[str, Any]:
    """Return one cached model artifact per Streamlit server process."""
    return load_model_artifact()
