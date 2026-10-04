"""Fixed protocol for the retrospective generalisation study (no tuning)."""

from dataclasses import asdict, dataclass

from .preprocessing import (
    WATER_QUALITY_TARGET as TARGET,
    WATER_QUALITY_GROUP as GROUP,
    WATER_QUALITY_MEASUREMENT_FEATURES,
    WATER_QUALITY_CENSOR_FEATURES,
    WATER_QUALITY_TEMPORAL_FEATURES,
    WATER_QUALITY_FEATURE_SETS,
)

DATE = "sample_date"
FEATURE_SETS = {
    "core": (list(WATER_QUALITY_MEASUREMENT_FEATURES), False),
    "core_indicators": (WATER_QUALITY_MEASUREMENT_FEATURES + WATER_QUALITY_CENSOR_FEATURES, True),
    "core_date": (WATER_QUALITY_MEASUREMENT_FEATURES + WATER_QUALITY_TEMPORAL_FEATURES, False),
    "full": (list(WATER_QUALITY_FEATURE_SETS["D_extended_plus_temporal"]), True),
}


@dataclass(frozen=True)
class ResearchConfig:
    seed: int = 42
    test_fraction: float = 0.2
    calibration_fraction: float = 0.2
    n_estimators: int = 150
    min_samples_leaf: int = 2
    max_features: float = 0.8
    n_jobs: int = -1
    cv_folds: int = 5
    train_end_year: int = 2018
    validation_end_year: int = 2021
    coverage: float = 0.9
    minimum_station_samples: int = 20
    permutation_rows: int = 5000
    permutation_repeats: int = 5
    fast: bool = False

    def metadata(self) -> dict:
        return {**asdict(self), "target": TARGET, "group": GROUP, "date": DATE,
                "feature_sets": FEATURE_SETS}
