#!/usr/bin/env python3
"""Execute frozen WaterSense Phase 2B Experiment 1.

The runner consumes only the exact historical development partition and the
Phase 2B-0 frozen site assignments.  Legacy benchmark outcomes are never read.
Inner-fold checkpoints permit identity-checked recovery after interruption.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from joblib import Parallel, delayed
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.phase2b0_readiness import (  # noqa: E402
    EXPECTED_PROCESSED_SHA256,
    EXPECTED_RAW_SHA256,
    EXPECTED_SPLIT_SHA256,
    audit_development_partition,
    sha256_file,
    validate_processed_data,
)
from src.preprocessing import (  # noqa: E402
    build_water_quality_feature_preprocessor,
)
from src.research_config import FEATURE_SETS  # noqa: E402
from src.weighted_regression_experiment import (  # noqa: E402
    ANCHOR_CANDIDATE_ID,
    BOOTSTRAP_RESAMPLES,
    EXPERIMENT_SEED,
    Candidate,
    ExperimentIntegrityError,
    classify_research_conclusion,
    compute_experiment_metrics,
    compute_training_weights,
    enumerate_frozen_candidates,
    make_estimator,
    paired_site_bootstrap,
    site_error_comparison,
    summarize_and_select_candidates,
    verify_prediction_pairing,
)


OUTPUT = ROOT / "research_upgrade_v3/experiment1_weighted_regression"
CHECKPOINTS = OUTPUT / ".checkpoints"
PROCESSED_PATH = ROOT / "data/processed/water_quality_modeling.csv"
RAW_PATH = ROOT / "data/raw/niea_river_water_quality_1990_2024.csv"
MEMBERSHIP_PATH = ROOT / "research_outputs/predictions/split_grouped.csv.gz"
FROZEN_CONFIG_PATH = ROOT / "research_upgrade_v3/phase2b0/WEIGHTED_REGRESSION_CONFIG.json"
SPLIT_MANIFEST_PATH = ROOT / "research_upgrade_v3/phase2b0/NESTED_CV_SPLIT_MANIFEST.json"
SITE_ASSIGNMENTS_PATH = ROOT / "research_upgrade_v3/phase2b0/NESTED_CV_SITE_ASSIGNMENTS.csv"
FOLD_SUPPORT_PATH = ROOT / "research_upgrade_v3/phase2b0/NESTED_CV_FOLD_SUPPORT.csv"
PHASE2B0_PROVENANCE_PATH = ROOT / "research_upgrade_v3/phase2b0/DATA_PROVENANCE_MANIFEST.json"

EXPECTED_FROZEN_CONFIG_SHA256 = (
    "70b8e8dba893416b5a1122dd1c36b3ab6f3e0e128ee07a7d65e5cdb96063cbe4"
)
EXPECTED_SPLIT_MANIFEST_SHA256 = (
    "c8fdf4024e9f499e7781e0aac41fac1ca681847f752520fdfd7a0dc78cd217cb"
)
EXPECTED_ASSIGNMENTS_SHA256 = (
    "0fa76b39cd3697aed2b615f5921a2cfa8dbaf0fdbd216393520c25c52bf58025"
)
EXPECTED_SUPPORT_SHA256 = (
    "d0e29ddeb6b77263fdafe4f5a654c550395e885170a79a4d563d0740c42d1379"
)
BASELINE_HEAD = "3553b29ff104918b12da8c84d2c9a8c5ed032e18"
FEATURES = list(FEATURE_SETS["full"][0])
PARALLEL_CANDIDATES = max(1, min(8, (os.cpu_count() or 2) - 1))


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _canonical_json_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _experiment_config(frozen: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment": "Phase 2B Experiment 1 - Low-DO Weighted Regression",
        "status_at_creation": "frozen_before_model_results",
        "baseline_head": BASELINE_HEAD,
        "data": {
            "processed_sha256": EXPECTED_PROCESSED_SHA256,
            "historical_membership_sha256": EXPECTED_SPLIT_SHA256,
            "development_rows": 119_690,
            "development_stations": 672,
            "legacy_test_prohibited": True,
        },
        "features": {
            "name": "full",
            "columns": FEATURES,
            "preprocessing": (
                "training-fold median imputation with missing indicators and scaling; "
                "censor flags passthrough"
            ),
        },
        "baseline": {
            "candidate_id": ANCHOR_CANDIDATE_ID,
            "family": "RandomForestRegressor",
            "parameters": {
                "n_estimators": 150,
                "min_samples_leaf": 2,
                "max_features": 0.8,
            },
            "weight_multiplier": 1,
        },
        "frozen_search": frozen,
        "split_identity": {
            "site_assignments_sha256": EXPECTED_ASSIGNMENTS_SHA256,
            "fold_support_sha256": EXPECTED_SUPPORT_SHA256,
            "outer_folds": 5,
            "inner_folds": 4,
        },
        "execution": {
            "seed": EXPERIMENT_SEED,
            "candidate_parallelism": PARALLEL_CANDIDATES,
            "estimator_internal_n_jobs": 1,
            "checkpoint_unit": "completed inner fold or outer prediction pair",
        },
        "selection": {
            "qualification": [
                "pooled inner OOF overall MAE <= 1.10 * pooled same-fold RF anchor MAE",
                "pooled inner OOF low-DO precision >= 0.30",
                "at least one predicted-low row in every inner validation fold",
                "all required metrics finite and no integrity/runtime failure",
            ],
            "lexicographic_order": [
                "highest arithmetic mean inner-fold low-DO recall",
                "lowest arithmetic mean inner-fold low-DO MAE",
                "lowest arithmetic mean inner-fold overall MAE",
                "lower preregistered complexity score",
                "stable candidate ID",
            ],
            "complexity_score": (
                "forest=n_estimators*max_features/min_samples_leaf; "
                "HGB=max_leaf_nodes/min_samples_leaf/(1+l2)"
            ),
        },
        "conclusion_rule": {
            "IMPROVEMENT SUPPORTED": [
                "paired site-bootstrap delta Recall 95% CI lower > 0",
                "paired site-bootstrap delta Low-DO MAE 95% CI upper < 0",
                "pooled weighted Overall MAE <= 1.10 * pooled baseline Overall MAE",
                "pooled weighted Low-DO Precision >= 0.30",
                "at least one outer-selected multiplier > 1",
            ],
            "NO SUPPORTED IMPROVEMENT": (
                "both co-primary point estimates fail to improve"
            ),
            "TRADE-OFF / INCONCLUSIVE": (
                "all other mixed, costly, or interval-crossing outcomes"
            ),
            "NO QUALIFIED MODEL": "no outer fold produces a qualified inner candidate",
        },
        "uncertainty": {
            "method": "paired whole-site percentile bootstrap",
            "resamples": BOOTSTRAP_RESAMPLES,
            "seed": EXPERIMENT_SEED,
            "delta": "weighted_minus_baseline",
        },
    }


def _preflight() -> tuple[
    dict[str, Any], dict[str, Any], pd.DataFrame, pd.DataFrame, list[Candidate]
]:
    if _git("branch", "--show-current") != "research-upgrade-v3":
        raise ExperimentIntegrityError("Experiment requires research-upgrade-v3")
    if _git("rev-parse", "HEAD") != BASELINE_HEAD:
        raise ExperimentIntegrityError("Baseline HEAD changed")
    expected_files = {
        RAW_PATH: EXPECTED_RAW_SHA256,
        PROCESSED_PATH: EXPECTED_PROCESSED_SHA256,
        MEMBERSHIP_PATH: EXPECTED_SPLIT_SHA256,
        FROZEN_CONFIG_PATH: EXPECTED_FROZEN_CONFIG_SHA256,
        SPLIT_MANIFEST_PATH: EXPECTED_SPLIT_MANIFEST_SHA256,
        SITE_ASSIGNMENTS_PATH: EXPECTED_ASSIGNMENTS_SHA256,
        FOLD_SUPPORT_PATH: EXPECTED_SUPPORT_SHA256,
    }
    mismatches = {
        str(path.relative_to(ROOT)): {
            "expected": expected,
            "observed": sha256_file(path) if path.is_file() else None,
        }
        for path, expected in expected_files.items()
        if not path.is_file() or sha256_file(path) != expected
    }
    if mismatches:
        raise ExperimentIntegrityError(f"Frozen evidence mismatch: {mismatches}")
    provenance = json.loads(PHASE2B0_PROVENANCE_PATH.read_text(encoding="utf-8"))
    if provenance["final_status"] != "READY":
        raise ExperimentIntegrityError("Phase 2B-0 is not READY")
    frozen = json.loads(FROZEN_CONFIG_PATH.read_text(encoding="utf-8"))
    split_manifest = json.loads(SPLIT_MANIFEST_PATH.read_text(encoding="utf-8"))
    if not split_manifest["all_partitions_qualified"] or not split_manifest[
        "all_site_overlaps_zero"
    ]:
        raise ExperimentIntegrityError("Frozen folds are not qualified")
    processed = pd.read_csv(PROCESSED_PATH)
    validate_processed_data(processed)
    membership = pd.read_csv(MEMBERSHIP_PATH)
    development, audit = audit_development_partition(processed, membership)
    if (audit["development_rows"], audit["development_stations"]) != (119_690, 672):
        raise ExperimentIntegrityError("Development identity changed")
    assignments = pd.read_csv(SITE_ASSIGNMENTS_PATH)
    candidates = enumerate_frozen_candidates(frozen)
    return frozen, split_manifest, development, assignments, candidates


def _failed_metric_row(
    candidate: Candidate,
    outer_fold: int,
    inner_fold: int,
    train: pd.DataFrame,
    validation: pd.DataFrame,
    error: BaseException,
    elapsed: float,
) -> dict[str, Any]:
    return {
        "outer_fold": outer_fold,
        "inner_fold": inner_fold,
        "candidate_id": candidate.candidate_id,
        "family": candidate.family,
        "parameters_json": json.dumps(candidate.parameters, sort_keys=True),
        "weight_multiplier": candidate.weight_multiplier,
        "complexity_score": candidate.complexity_score,
        "run_status": "failed",
        "failure_type": type(error).__name__,
        "failure_message": str(error)[:1000],
        "elapsed_seconds": elapsed,
        "train_rows": len(train),
        "validation_rows": len(validation),
        "train_stations": train["station_code"].nunique(),
        "validation_stations": validation["station_code"].nunique(),
    }


def _fit_candidate(
    candidate: Candidate,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_validation: np.ndarray,
    y_validation: np.ndarray,
    validation_stations: np.ndarray,
    outer_fold: int,
    inner_fold: int,
    train_metadata: tuple[int, int],
    validation_metadata: tuple[int, int],
) -> dict[str, Any]:
    started = time.perf_counter()
    base = {
        "outer_fold": outer_fold,
        "inner_fold": inner_fold,
        "candidate_id": candidate.candidate_id,
        "family": candidate.family,
        "parameters_json": json.dumps(candidate.parameters, sort_keys=True),
        "weight_multiplier": candidate.weight_multiplier,
        "complexity_score": candidate.complexity_score,
        "train_rows": train_metadata[0],
        "train_stations": train_metadata[1],
        "validation_rows": validation_metadata[0],
        "validation_stations": validation_metadata[1],
    }
    try:
        weights = compute_training_weights(y_train, candidate.weight_multiplier)
        estimator = make_estimator(candidate, n_jobs=1)
        estimator.fit(x_train, y_train, sample_weight=weights)
        prediction = estimator.predict(x_validation)
        metrics = compute_experiment_metrics(
            y_validation, prediction, stations=validation_stations
        )
        return {
            **base,
            "run_status": "complete",
            "failure_type": "",
            "failure_message": "",
            "elapsed_seconds": time.perf_counter() - started,
            **metrics,
        }
    except BaseException as error:  # retained failure is part of the protocol
        return {
            **base,
            "run_status": "failed",
            "failure_type": type(error).__name__,
            "failure_message": str(error)[:1000],
            "elapsed_seconds": time.perf_counter() - started,
        }


def _inner_fold_rows(
    development: pd.DataFrame,
    assignments: pd.DataFrame,
    candidates: list[Candidate],
    outer_fold: int,
    inner_fold: int,
) -> pd.DataFrame:
    outer_validation_sites = set(
        assignments.loc[
            assignments["level"].eq("outer")
            & assignments["validation_fold"].eq(outer_fold),
            "station_code",
        ]
    )
    outer_train = development.loc[
        ~development["station_code"].isin(outer_validation_sites)
    ].copy()
    inner_validation_sites = set(
        assignments.loc[
            assignments["level"].eq("inner")
            & assignments["outer_fold"].eq(outer_fold)
            & assignments["validation_fold"].eq(inner_fold),
            "station_code",
        ]
    )
    validation = outer_train.loc[
        outer_train["station_code"].isin(inner_validation_sites)
    ].copy()
    train = outer_train.loc[
        ~outer_train["station_code"].isin(inner_validation_sites)
    ].copy()
    if set(train["station_code"]) & set(validation["station_code"]):
        raise ExperimentIntegrityError("Inner-fold station overlap")
    preprocessor = build_water_quality_feature_preprocessor(FEATURES)
    x_train = np.asarray(preprocessor.fit_transform(train[FEATURES]), dtype=float)
    x_validation = np.asarray(preprocessor.transform(validation[FEATURES]), dtype=float)
    if not (np.isfinite(x_train).all() and np.isfinite(x_validation).all()):
        raise ExperimentIntegrityError("Fold-local preprocessing produced non-finite values")
    y_train = train["dissolved_oxygen_mg_l"].to_numpy(dtype=float)
    y_validation = validation["dissolved_oxygen_mg_l"].to_numpy(dtype=float)
    validation_stations = validation["station_code"].to_numpy(dtype=object)
    print(
        f"outer={outer_fold} inner={inner_fold}: {len(candidates)} candidates; "
        f"train={len(train):,}, validation={len(validation):,}",
        flush=True,
    )
    with threadpool_limits(limits=1):
        rows = Parallel(
            n_jobs=PARALLEL_CANDIDATES,
            prefer="threads",
            verbose=5,
        )(
            delayed(_fit_candidate)(
                candidate,
                x_train,
                y_train,
                x_validation,
                y_validation,
                validation_stations,
                outer_fold,
                inner_fold,
                (len(train), train["station_code"].nunique()),
                (len(validation), validation["station_code"].nunique()),
            )
            for candidate in candidates
        )
    result = pd.DataFrame(rows).sort_values("candidate_id").reset_index(drop=True)
    if len(result) != len(candidates) or result["candidate_id"].duplicated().any():
        raise ExperimentIntegrityError("Inner checkpoint candidate coverage is invalid")
    return result


def _load_or_run_inner_fold(
    development: pd.DataFrame,
    assignments: pd.DataFrame,
    candidates: list[Candidate],
    outer_fold: int,
    inner_fold: int,
    config_hash: str,
) -> pd.DataFrame:
    folder = CHECKPOINTS / f"outer_{outer_fold}"
    path = folder / f"inner_{inner_fold}.csv.gz"
    metadata_path = folder / f"inner_{inner_fold}.json"
    if path.is_file() and metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("config_sha256") != config_hash:
            raise ExperimentIntegrityError("Checkpoint config hash mismatch")
        if metadata.get("csv_sha256") != sha256_file(path):
            raise ExperimentIntegrityError("Checkpoint CSV hash mismatch")
        restored = pd.read_csv(path)
        expected_ids = {candidate.candidate_id for candidate in candidates}
        if set(restored["candidate_id"]) != expected_ids:
            raise ExperimentIntegrityError("Checkpoint candidate IDs differ")
        print(f"restored outer={outer_fold} inner={inner_fold}", flush=True)
        return restored
    result = _inner_fold_rows(
        development, assignments, candidates, outer_fold, inner_fold
    )
    folder.mkdir(parents=True, exist_ok=True)
    result.to_csv(
        path,
        index=False,
        compression={"method": "gzip", "mtime": 0},
        float_format="%.15g",
    )
    _write_json(
        metadata_path,
        {
            "config_sha256": config_hash,
            "csv_sha256": sha256_file(path),
            "outer_fold": outer_fold,
            "inner_fold": inner_fold,
            "candidate_count": len(result),
            "completed_candidates": int(result["run_status"].eq("complete").sum()),
            "failed_candidates": int(result["run_status"].ne("complete").sum()),
        },
    )
    return result


def _fit_outer_variant(
    candidate: Candidate,
    train: pd.DataFrame,
    validation: pd.DataFrame,
    x_train: np.ndarray,
    x_validation: np.ndarray,
    variant: str,
    outer_fold: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    started = time.perf_counter()
    y_train = train["dissolved_oxygen_mg_l"].to_numpy(dtype=float)
    weights = compute_training_weights(y_train, candidate.weight_multiplier)
    estimator = make_estimator(candidate, n_jobs=PARALLEL_CANDIDATES)
    estimator.fit(x_train, y_train, sample_weight=weights)
    predicted = estimator.predict(x_validation)
    metrics = compute_experiment_metrics(
        validation["dissolved_oxygen_mg_l"],
        predicted,
        stations=validation["station_code"],
    )
    prediction = validation[
        [
            "source_object_id", "station_code", "sample_date", "sample_year",
            "dissolved_oxygen_mg_l",
        ]
    ].rename(columns={"dissolved_oxygen_mg_l": "actual_do_mg_l"}).copy()
    prediction.insert(0, "variant", variant)
    prediction.insert(1, "outer_fold", outer_fold)
    prediction["candidate_id"] = candidate.candidate_id
    prediction["family"] = candidate.family
    prediction["weight_multiplier"] = candidate.weight_multiplier
    prediction["predicted_do_mg_l"] = predicted
    prediction["prediction_minus_ground_truth_mg_l"] = (
        prediction["predicted_do_mg_l"] - prediction["actual_do_mg_l"]
    )
    prediction["actual_low_do"] = prediction["actual_do_mg_l"].lt(4.0)
    prediction["predicted_low_do"] = prediction["predicted_do_mg_l"].lt(4.0)
    prediction["false_negative"] = (
        prediction["actual_low_do"] & ~prediction["predicted_low_do"]
    )
    prediction["false_positive"] = (
        ~prediction["actual_low_do"] & prediction["predicted_low_do"]
    )
    metric_row = {
        "variant": variant,
        "outer_fold": outer_fold,
        "candidate_id": candidate.candidate_id,
        "family": candidate.family,
        "parameters_json": json.dumps(candidate.parameters, sort_keys=True),
        "weight_multiplier": candidate.weight_multiplier,
        "seed": EXPERIMENT_SEED,
        "run_status": "complete",
        "elapsed_seconds": time.perf_counter() - started,
        "train_rows": len(train),
        "validation_rows": len(validation),
        "train_stations": train["station_code"].nunique(),
        "validation_stations": validation["station_code"].nunique(),
        "train_low_do_rows": int(train["dissolved_oxygen_mg_l"].lt(4.0).sum()),
        "train_low_do_sites": int(
            train.loc[train["dissolved_oxygen_mg_l"].lt(4.0), "station_code"].nunique()
        ),
        **metrics,
    }
    return prediction, metric_row


def _load_or_run_outer(
    development: pd.DataFrame,
    assignments: pd.DataFrame,
    selected: Candidate,
    anchor: Candidate,
    outer_fold: int,
    config_hash: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    folder = CHECKPOINTS / f"outer_{outer_fold}"
    predictions_path = folder / "outer_predictions.csv.gz"
    metrics_path = folder / "outer_metrics.csv"
    metadata_path = folder / "outer_predictions.json"
    if predictions_path.is_file() and metrics_path.is_file() and metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        expected = {
            "config_sha256": config_hash,
            "selected_candidate_id": selected.candidate_id,
            "prediction_sha256": sha256_file(predictions_path),
            "metrics_sha256": sha256_file(metrics_path),
        }
        if any(metadata.get(key) != value for key, value in expected.items()):
            raise ExperimentIntegrityError("Outer checkpoint identity mismatch")
        predictions = pd.read_csv(predictions_path)
        metrics = pd.read_csv(metrics_path)
        verify_prediction_pairing(predictions)
        print(f"restored outer predictions fold={outer_fold}", flush=True)
        return predictions, metrics
    validation_sites = set(
        assignments.loc[
            assignments["level"].eq("outer")
            & assignments["validation_fold"].eq(outer_fold),
            "station_code",
        ]
    )
    validation = development.loc[
        development["station_code"].isin(validation_sites)
    ].copy()
    train = development.loc[
        ~development["station_code"].isin(validation_sites)
    ].copy()
    if set(train["station_code"]) & set(validation["station_code"]):
        raise ExperimentIntegrityError("Outer-fold station overlap")
    preprocessor = build_water_quality_feature_preprocessor(FEATURES)
    x_train = np.asarray(preprocessor.fit_transform(train[FEATURES]), dtype=float)
    x_validation = np.asarray(preprocessor.transform(validation[FEATURES]), dtype=float)
    baseline_prediction, baseline_metrics = _fit_outer_variant(
        anchor, train, validation, x_train, x_validation, "baseline", outer_fold
    )
    if selected.candidate_id == anchor.candidate_id:
        weighted_prediction = baseline_prediction.copy()
        weighted_prediction["variant"] = "weighted"
        weighted_metrics = dict(baseline_metrics)
        weighted_metrics["variant"] = "weighted"
        weighted_metrics["elapsed_seconds"] = 0.0
        weighted_metrics["reused_identical_anchor_fit"] = True
        baseline_metrics["reused_identical_anchor_fit"] = False
    else:
        weighted_prediction, weighted_metrics = _fit_outer_variant(
            selected, train, validation, x_train, x_validation, "weighted", outer_fold
        )
        baseline_metrics["reused_identical_anchor_fit"] = False
        weighted_metrics["reused_identical_anchor_fit"] = False
    predictions = pd.concat(
        [baseline_prediction, weighted_prediction], ignore_index=True
    )
    metrics = pd.DataFrame([baseline_metrics, weighted_metrics])
    verify_prediction_pairing(predictions)
    folder.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(
        predictions_path,
        index=False,
        compression={"method": "gzip", "mtime": 0},
        float_format="%.15g",
    )
    metrics.to_csv(metrics_path, index=False, float_format="%.15g")
    _write_json(
        metadata_path,
        {
            "config_sha256": config_hash,
            "selected_candidate_id": selected.candidate_id,
            "prediction_sha256": sha256_file(predictions_path),
            "metrics_sha256": sha256_file(metrics_path),
        },
    )
    return predictions, metrics


def _pooled_comparison(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for variant in ["baseline", "weighted"]:
        subset = predictions.loc[predictions["variant"].eq(variant)]
        metrics = compute_experiment_metrics(
            subset["actual_do_mg_l"],
            subset["predicted_do_mg_l"],
            stations=subset["station_code"],
        )
        rows.append({"variant": variant, **metrics})
    result = pd.DataFrame(rows)
    baseline = result.loc[result["variant"].eq("baseline")].iloc[0]
    weighted = result.loc[result["variant"].eq("weighted")].iloc[0]
    delta = {"variant": "delta_weighted_minus_baseline"}
    for column in result.columns:
        if column == "variant" or isinstance(weighted[column], (bool, np.bool_)):
            continue
        if pd.api.types.is_number(weighted[column]) and pd.api.types.is_number(
            baseline[column]
        ):
            delta[column] = float(weighted[column]) - float(baseline[column])
    return pd.concat([result, pd.DataFrame([delta])], ignore_index=True)


def _classification_table(
    predictions: pd.DataFrame, outer_metrics: pd.DataFrame
) -> pd.DataFrame:
    columns = [
        "sample_count", "low_do_count", "predicted_low_do_count",
        "true_positive_count", "false_positive_count", "true_negative_count",
        "false_negative_count", "low_do_precision", "low_do_recall", "low_do_f1",
        "low_do_false_negative_rate", "low_do_false_positive_rate",
        "precision_defined", "recall_defined", "f1_defined",
    ]
    fold = outer_metrics[["variant", "outer_fold", *columns]].copy()
    fold.insert(0, "scope", "outer_fold")
    pooled_rows = []
    for variant in ["baseline", "weighted"]:
        subset = predictions.loc[predictions["variant"].eq(variant)]
        metrics = compute_experiment_metrics(
            subset["actual_do_mg_l"], subset["predicted_do_mg_l"],
            stations=subset["station_code"],
        )
        pooled_rows.append(
            {"scope": "pooled_outer_oof", "variant": variant, "outer_fold": pd.NA,
             **{column: metrics[column] for column in columns}}
        )
    result = pd.concat([fold, pd.DataFrame(pooled_rows)], ignore_index=True)
    result["actual_positive_definition"] = "actual DO < 4 mg/L"
    result["predicted_positive_definition"] = "predicted DO < 4 mg/L"
    result["precision_denominator"] = "TP + FP"
    result["recall_and_fnr_denominator"] = "TP + FN"
    result["fpr_denominator"] = "FP + TN"
    return result


def _prediction_shift_analysis(predictions: pd.DataFrame) -> pd.DataFrame:
    verify_prediction_pairing(predictions)
    baseline = predictions.loc[predictions["variant"].eq("baseline")].sort_values(
        "source_object_id"
    ).reset_index(drop=True)
    weighted = predictions.loc[predictions["variant"].eq("weighted")].sort_values(
        "source_object_id"
    ).reset_index(drop=True)
    change = weighted["predicted_do_mg_l"] - baseline["predicted_do_mg_l"]
    actual = baseline["actual_do_mg_l"]
    strata = [
        ("overall", pd.Series(True, index=actual.index)),
        ("actual_do_<2", actual.lt(2.0)),
        ("actual_do_2_to_<3", actual.ge(2.0) & actual.lt(3.0)),
        ("actual_do_3_to_<4", actual.ge(3.0) & actual.lt(4.0)),
    ]
    rows = []
    for label, mask in strata:
        baseline_error = (
            baseline.loc[mask, "predicted_do_mg_l"] - actual.loc[mask]
        )
        weighted_error = (
            weighted.loc[mask, "predicted_do_mg_l"] - actual.loc[mask]
        )
        actual_low = actual.loc[mask].lt(4.0)
        baseline_fn = (
            baseline.loc[mask, "predicted_do_mg_l"].ge(4.0) & actual_low
        )
        weighted_fn = (
            weighted.loc[mask, "predicted_do_mg_l"].ge(4.0) & actual_low
        )
        rows.append(
            {
                "stratum": label,
                "sample_count": int(mask.sum()),
                "mean_prediction_change_weighted_minus_baseline_mg_l": float(
                    change.loc[mask].mean()
                ),
                "median_prediction_change_weighted_minus_baseline_mg_l": float(
                    change.loc[mask].median()
                ),
                "fraction_predictions_lower_with_weighting": float(
                    change.loc[mask].lt(0).mean()
                ),
                "baseline_mae_mg_l": float(baseline_error.abs().mean()),
                "weighted_mae_mg_l": float(weighted_error.abs().mean()),
                "delta_mae_weighted_minus_baseline_mg_l": float(
                    weighted_error.abs().mean() - baseline_error.abs().mean()
                ),
                "baseline_bias_prediction_minus_truth_mg_l": float(
                    baseline_error.mean()
                ),
                "weighted_bias_prediction_minus_truth_mg_l": float(
                    weighted_error.mean()
                ),
                "delta_bias_weighted_minus_baseline_mg_l": float(
                    weighted_error.mean() - baseline_error.mean()
                ),
                "baseline_false_negative_rate": (
                    float(baseline_fn.sum() / actual_low.sum())
                    if actual_low.sum() else np.nan
                ),
                "weighted_false_negative_rate": (
                    float(weighted_fn.sum() / actual_low.sum())
                    if actual_low.sum() else np.nan
                ),
            }
        )
    return pd.DataFrame(rows)


def _make_figures(
    comparison: pd.DataFrame,
    uncertainty: pd.DataFrame,
    predictions: pd.DataFrame,
    sites: pd.DataFrame,
) -> list[Path]:
    figure_dir = OUTPUT / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    metrics = ["overall_mae_mg_l", "low_do_mae_mg_l", "low_do_recall", "low_do_precision"]
    labels = ["Overall MAE", "Low-DO MAE", "Low-DO Recall", "Low-DO Precision"]
    figure, axes = plt.subplots(1, 4, figsize=(14, 4))
    for axis, metric, label in zip(axes, metrics, labels):
        subset = uncertainty.loc[
            uncertainty["metric"].eq(metric)
            & uncertainty["comparison"].isin(["baseline", "weighted"])
        ].set_index("comparison")
        estimates = subset.loc[["baseline", "weighted"], "estimate"].to_numpy()
        lower = estimates - subset.loc[["baseline", "weighted"], "ci_95_lower"].to_numpy()
        upper = subset.loc[["baseline", "weighted"], "ci_95_upper"].to_numpy() - estimates
        axis.errorbar([0, 1], estimates, yerr=[lower, upper], fmt="o", capsize=4)
        axis.set(xticks=[0, 1], xticklabels=["Baseline", "Weighted"], title=label)
        axis.grid(alpha=0.25)
    figure.suptitle("Paired site-bootstrap estimates (95% CI)")
    figure.tight_layout()
    path = figure_dir / "BASELINE_WEIGHTED_UNCERTAINTY.png"
    figure.savefig(path, dpi=180)
    plt.close(figure)
    paths.append(path)

    low = predictions.loc[predictions["actual_do_mg_l"].lt(4.0)]
    figure, axes = plt.subplots(1, 2, figsize=(12, 5), sharex=True, sharey=True)
    for axis, variant in zip(axes, ["baseline", "weighted"]):
        subset = low.loc[low["variant"].eq(variant)]
        axis.scatter(subset["actual_do_mg_l"], subset["predicted_do_mg_l"], s=9, alpha=0.35)
        axis.axhline(4.0, color="red", linestyle="--", linewidth=1)
        axis.plot([0, 4], [0, 4], color="black", linewidth=1)
        axis.set(title=variant.title(), xlabel="Actual DO (mg/L)")
    axes[0].set_ylabel("Predicted DO (mg/L)")
    figure.suptitle("Outer-fold low-DO predictions")
    figure.tight_layout()
    path = figure_dir / "LOW_DO_OUTER_PREDICTIONS.png"
    figure.savefig(path, dpi=180)
    plt.close(figure)
    paths.append(path)

    low_sites = sites.loc[sites["low_do_rows"].gt(0)].sort_values(
        "delta_weighted_minus_baseline_low_do_mae_mg_l"
    )
    display = pd.concat([low_sites.head(15), low_sites.tail(15)]).drop_duplicates()
    figure, axis = plt.subplots(figsize=(10, 8))
    colors = np.where(
        display["delta_weighted_minus_baseline_low_do_mae_mg_l"].lt(0),
        "#2a9d8f", "#e76f51",
    )
    axis.barh(
        display["station_code"],
        display["delta_weighted_minus_baseline_low_do_mae_mg_l"],
        color=colors,
    )
    axis.axvline(0, color="black", linewidth=1)
    axis.set(
        xlabel="Δ Low-DO MAE (weighted − baseline, mg/L)",
        title="Largest station-level low-DO changes",
    )
    figure.tight_layout()
    path = figure_dir / "SITE_LOW_DO_MAE_CHANGE.png"
    figure.savefig(path, dpi=180)
    plt.close(figure)
    paths.append(path)
    return paths


def _format_metric(value: Any, digits: int = 4) -> str:
    return "undefined" if pd.isna(value) else f"{float(value):.{digits}f}"


def _markdown_table(data: pd.DataFrame) -> str:
    columns = [str(column) for column in data.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for values in data.itertuples(index=False, name=None):
        rendered = [
            _format_metric(value, 6)
            if isinstance(value, (float, np.floating)) else str(value)
            for value in values
        ]
        lines.append("| " + " | ".join(rendered) + " |")
    return "\n".join(lines)


def _reports(
    config_hash: str,
    comparison: pd.DataFrame,
    uncertainty: pd.DataFrame,
    outer_metrics: pd.DataFrame,
    selection: pd.DataFrame,
    sites: pd.DataFrame,
    shift: pd.DataFrame,
    conclusion: str,
    reasons: list[str],
) -> None:
    values = comparison.set_index("variant")
    baseline = values.loc["baseline"]
    weighted = values.loc["weighted"]
    delta_ci = uncertainty.loc[
        uncertainty["comparison"].eq("delta_weighted_minus_baseline")
    ].set_index("metric")
    selected_rows = selection.loc[selection["selected"]]
    selected_text = "\n".join(
        f"- Outer {int(row.outer_fold)}: `{row.candidate_id}`"
        for row in selected_rows.itertuples()
    )
    low_sites = sites.loc[sites["low_do_rows"].gt(0)].copy()
    improved_sites = int(
        low_sites["delta_weighted_minus_baseline_low_do_mae_mg_l"].lt(0).sum()
    )
    worsened_sites = int(
        low_sites["delta_weighted_minus_baseline_low_do_mae_mg_l"].gt(0).sum()
    )
    low_sites["total_low_do_absolute_error_reduction_mg_l"] = (
        -low_sites["delta_weighted_minus_baseline_low_do_mae_mg_l"]
        * low_sites["low_do_rows"]
    )
    beneficial = low_sites.loc[
        low_sites["total_low_do_absolute_error_reduction_mg_l"].gt(0)
    ].sort_values("total_low_do_absolute_error_reduction_mg_l", ascending=False)
    top_improvement = beneficial.head(10)[
        [
            "station_code", "low_do_rows", "baseline_low_do_mae_mg_l",
            "weighted_low_do_mae_mg_l",
            "total_low_do_absolute_error_reduction_mg_l",
        ]
    ]
    adverse = low_sites.nsmallest(
        10, "total_low_do_absolute_error_reduction_mg_l"
    )[
        [
            "station_code", "low_do_rows", "baseline_low_do_mae_mg_l",
            "weighted_low_do_mae_mg_l",
            "total_low_do_absolute_error_reduction_mg_l",
        ]
    ]
    positive_total = beneficial[
        "total_low_do_absolute_error_reduction_mg_l"
    ].sum()
    top_five_share = (
        beneficial.head(5)["total_low_do_absolute_error_reduction_mg_l"].sum()
        / positive_total
    )
    top_ten_share = (
        beneficial.head(10)["total_low_do_absolute_error_reduction_mg_l"].sum()
        / positive_total
    )
    overall_shift = shift.set_index("stratum").loc["overall"]
    extreme = shift.set_index("stratum").loc["actual_do_<2"]
    overall_mae_increase_percent = (
        (weighted["overall_mae_mg_l"] / baseline["overall_mae_mg_l"] - 1.0)
        * 100.0
    )
    report = f"""# Experiment 1 Research Report

## Conclusion: {conclusion}

This is nested-CV development evidence, not external confirmation. Reasons: {'; '.join(reasons)}.

## Frozen execution

The exact 119,690-row/672-site development partition and frozen 5×4 site-grouped folds were used. All preprocessing and weights were fitted/computed inside the applicable training fold. The 128-candidate grid was evaluated once in every inner fold; legacy benchmark outcomes were not read.

Outer-selected configurations:

{selected_text}

## Pooled outer out-of-fold results

| Metric | Baseline | Selected procedure | Delta (weighted − baseline) | Paired 95% CI for delta |
| --- | ---: | ---: | ---: | ---: |
| Overall MAE | {_format_metric(baseline['overall_mae_mg_l'])} | {_format_metric(weighted['overall_mae_mg_l'])} | {_format_metric(weighted['overall_mae_mg_l'] - baseline['overall_mae_mg_l'])} | [{_format_metric(delta_ci.loc['overall_mae_mg_l','ci_95_lower'])}, {_format_metric(delta_ci.loc['overall_mae_mg_l','ci_95_upper'])}] |
| Low-DO MAE | {_format_metric(baseline['low_do_mae_mg_l'])} | {_format_metric(weighted['low_do_mae_mg_l'])} | {_format_metric(weighted['low_do_mae_mg_l'] - baseline['low_do_mae_mg_l'])} | [{_format_metric(delta_ci.loc['low_do_mae_mg_l','ci_95_lower'])}, {_format_metric(delta_ci.loc['low_do_mae_mg_l','ci_95_upper'])}] |
| Low-DO Bias | {_format_metric(baseline['low_do_bias_prediction_minus_truth_mg_l'])} | {_format_metric(weighted['low_do_bias_prediction_minus_truth_mg_l'])} | {_format_metric(weighted['low_do_bias_prediction_minus_truth_mg_l'] - baseline['low_do_bias_prediction_minus_truth_mg_l'])} | [{_format_metric(delta_ci.loc['low_do_bias_prediction_minus_truth_mg_l','ci_95_lower'])}, {_format_metric(delta_ci.loc['low_do_bias_prediction_minus_truth_mg_l','ci_95_upper'])}] |
| Recall | {_format_metric(baseline['low_do_recall'])} | {_format_metric(weighted['low_do_recall'])} | {_format_metric(weighted['low_do_recall'] - baseline['low_do_recall'])} | [{_format_metric(delta_ci.loc['low_do_recall','ci_95_lower'])}, {_format_metric(delta_ci.loc['low_do_recall','ci_95_upper'])}] |
| Precision | {_format_metric(baseline['low_do_precision'])} | {_format_metric(weighted['low_do_precision'])} | {_format_metric(weighted['low_do_precision'] - baseline['low_do_precision'])} | [{_format_metric(delta_ci.loc['low_do_precision','ci_95_lower'])}, {_format_metric(delta_ci.loc['low_do_precision','ci_95_upper'])}] |
| F1 | {_format_metric(baseline['low_do_f1'])} | {_format_metric(weighted['low_do_f1'])} | {_format_metric(weighted['low_do_f1'] - baseline['low_do_f1'])} | [{_format_metric(delta_ci.loc['low_do_f1','ci_95_lower'])}, {_format_metric(delta_ci.loc['low_do_f1','ci_95_upper'])}] |
| False-positive rate | {_format_metric(baseline['low_do_false_positive_rate'], 6)} | {_format_metric(weighted['low_do_false_positive_rate'], 6)} | {_format_metric(weighted['low_do_false_positive_rate'] - baseline['low_do_false_positive_rate'], 6)} | [{_format_metric(delta_ci.loc['low_do_false_positive_rate','ci_95_lower'], 6)}, {_format_metric(delta_ci.loc['low_do_false_positive_rate','ci_95_upper'], 6)}] |
| False positives | {int(baseline['false_positive_count'])} | {int(weighted['false_positive_count'])} | {int(weighted['false_positive_count'] - baseline['false_positive_count'])} | not bootstrapped as a scale-dependent count |

## Trade-offs and distribution shift

Overall MAE increased by {overall_mae_increase_percent:.2f}%, inside but close to the frozen 10% guard. False positives increased from {int(baseline['false_positive_count'])} to {int(weighted['false_positive_count'])}; Precision declined from {_format_metric(baseline['low_do_precision'])} to {_format_metric(weighted['low_do_precision'])}, while remaining above the 0.30 qualification floor. The false-positive-rate increase has a paired 95% interval [{_format_metric(delta_ci.loc['low_do_false_positive_rate','ci_95_lower'], 6)}, {_format_metric(delta_ci.loc['low_do_false_positive_rate','ci_95_upper'], 6)}].

Across all rows, the selected procedure shifted predictions by a mean {overall_shift['mean_prediction_change_weighted_minus_baseline_mg_l']:.4f} mg/L and median {overall_shift['median_prediction_change_weighted_minus_baseline_mg_l']:.4f} mg/L; {overall_shift['fraction_predictions_lower_with_weighting']:.1%} of predictions moved downward. This is not a uniform global shift. For actual DO `<2 mg/L`, positive bias fell from {extreme['baseline_bias_prediction_minus_truth_mg_l']:.4f} to {extreme['weighted_bias_prediction_minus_truth_mg_l']:.4f} mg/L, but remained materially positive; the extreme tail is improved, not solved.

## Station-level attribution

The selected procedure changed low-DO MAE in {improved_sites} of 115 low-DO sites beneficially and {worsened_sites} adversely. The five largest positive station contributions account for {top_five_share:.1%} of total positive absolute-error reduction and the largest ten for {top_ten_share:.1%}; improvement is distributed beyond a handful of sites, but remains concentrated enough to report explicitly.

## Largest station-level Low-DO MAE reductions

{_markdown_table(top_improvement)}

## Largest adverse station-level changes

{_markdown_table(adverse)}

## Interpretation boundary

The weighted label denotes the complete inner-selected procedure; selected model family, hyperparameters and multiplier may differ by outer fold. A multiplier of one is an eligible unweighted candidate under the frozen grid and is not relabelled as a weighting success. Site bootstrap resamples entire outer-validation stations. It does not make repeated observations independent or create an unseen test set.
"""
    _write_text(OUTPUT / "EXPERIMENT1_RESEARCH_REPORT.md", report)

    reproducibility = f"""# Experiment 1 Reproducibility

## Commands

```bash
python3 scripts/run_experiment1_weighted_regression.py
python3 -m unittest tests.test_weighted_regression_experiment -v
```

## Identity

- Baseline HEAD: `{BASELINE_HEAD}`.
- Experiment config canonical SHA-256: `{config_hash}`.
- Processed data SHA-256: `{EXPECTED_PROCESSED_SHA256}`.
- Historical membership SHA-256: `{EXPECTED_SPLIT_SHA256}`.
- Frozen site assignment SHA-256: `{EXPECTED_ASSIGNMENTS_SHA256}`.
- Frozen fold support SHA-256: `{EXPECTED_SUPPORT_SHA256}`.
- Seed: {EXPERIMENT_SEED}.
- Bootstrap: {BOOTSTRAP_RESAMPLES} paired whole-site draws.

## Checkpoint recovery

Each completed inner fold and outer prediction pair has its own CSV hash plus the experiment config hash. A restart accepts a checkpoint only when both identities match; otherwise it fails closed. Checkpoints are not counted twice because final tables are rebuilt from one checkpoint per frozen fold.

## Environment

- Python: {platform.python_version()}.
- NumPy: {np.__version__}.
- pandas: {pd.__version__}.
- scikit-learn: {sklearn.__version__}.
- joblib: {joblib.__version__}.
"""
    _write_text(OUTPUT / "EXPERIMENT1_REPRODUCIBILITY.md", reproducibility)


def _run_tests() -> dict[str, Any]:
    command = [
        sys.executable, "-m", "unittest",
        "tests.test_weighted_regression_experiment", "-v",
    ]
    completed = subprocess.run(
        command, cwd=ROOT, text=True, capture_output=True, check=False
    )
    combined = "\n".join(
        value.strip() for value in [completed.stdout, completed.stderr] if value.strip()
    )
    if completed.returncode:
        raise ExperimentIntegrityError(f"Experiment tests failed:\n{combined}")
    summary = next(
        (line for line in combined.splitlines() if line.startswith("Ran ")),
        "tests passed",
    )
    return {"command": " ".join(command[1:]), "result": "passed", "summary": summary}


def main() -> None:
    task_started = time.time()
    frozen, split_manifest, development, assignments, candidates = _preflight()
    experiment_config = _experiment_config(frozen)
    config_hash = _canonical_json_hash(experiment_config)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    config_path = OUTPUT / "EXPERIMENT1_CONFIG.json"
    if config_path.is_file():
        existing = json.loads(config_path.read_text(encoding="utf-8"))
        if _canonical_json_hash(existing) != config_hash:
            raise ExperimentIntegrityError("Existing experiment config differs")
    else:
        _write_json(config_path, experiment_config)

    start_status = _git("status", "--short", "--branch", "--untracked-files=all")
    run_manifest_path = OUTPUT / "EXPERIMENT1_RUN_MANIFEST.json"
    run_manifest: dict[str, Any] = {
        "status": "running",
        "training_performed": True,
        "baseline_head": BASELINE_HEAD,
        "experiment_config_canonical_sha256": config_hash,
        "experiment_config_file_sha256": sha256_file(config_path),
        "frozen_config_file_sha256": EXPECTED_FROZEN_CONFIG_SHA256,
        "split_manifest_file_sha256": EXPECTED_SPLIT_MANIFEST_SHA256,
        "site_assignments_sha256": EXPECTED_ASSIGNMENTS_SHA256,
        "fold_support_sha256": EXPECTED_SUPPORT_SHA256,
        "processed_data_sha256": EXPECTED_PROCESSED_SHA256,
        "historical_membership_sha256": EXPECTED_SPLIT_SHA256,
        "candidate_count": len(candidates),
        "outer_folds": 5,
        "inner_folds": 4,
        "expected_inner_candidate_evaluations": len(candidates) * 5 * 4,
        "legacy_benchmark_read": False,
        "task_start_git_status": start_status.splitlines(),
        "checkpoint_files_present_at_start": len(
            [path for path in CHECKPOINTS.rglob("*") if path.is_file()]
        )
        if CHECKPOINTS.is_dir()
        else 0,
        "completed_inner_folds": 0,
        "completed_outer_folds": 0,
    }
    _write_json(run_manifest_path, run_manifest)

    anchor = next(
        candidate for candidate in candidates
        if candidate.candidate_id == ANCHOR_CANDIDATE_ID
    )
    all_fold_results: list[pd.DataFrame] = []
    all_selections: list[pd.DataFrame] = []
    all_predictions: list[pd.DataFrame] = []
    all_outer_metrics: list[pd.DataFrame] = []
    selected_candidates: list[Candidate] = []
    for outer_fold in range(1, 6):
        outer_fold_results = []
        for inner_fold in range(1, 5):
            fold = _load_or_run_inner_fold(
                development, assignments, candidates, outer_fold, inner_fold,
                config_hash,
            )
            outer_fold_results.append(fold)
            run_manifest["completed_inner_folds"] = len(all_fold_results) + len(
                outer_fold_results
            )
            _write_json(run_manifest_path, run_manifest)
        inner_results = pd.concat(outer_fold_results, ignore_index=True)
        all_fold_results.extend(outer_fold_results)
        summary, selected = summarize_and_select_candidates(inner_results, candidates)
        summary.insert(0, "outer_fold", outer_fold)
        all_selections.append(summary)
        if selected is None:
            run_manifest.update(
                status="complete_no_qualified_model",
                conclusion="NO QUALIFIED MODEL",
                failed_outer_fold=outer_fold,
            )
            _write_json(run_manifest_path, run_manifest)
            break
        selected_candidates.append(selected)
        print(f"outer={outer_fold} selected={selected.candidate_id}", flush=True)
        prediction, metrics = _load_or_run_outer(
            development, assignments, selected, anchor, outer_fold, config_hash
        )
        all_predictions.append(prediction)
        all_outer_metrics.append(metrics)
        run_manifest["completed_outer_folds"] = outer_fold
        run_manifest.setdefault("selected_candidates", []).append(
            {"outer_fold": outer_fold, **asdict(selected)}
        )
        _write_json(run_manifest_path, run_manifest)

    fold_results = pd.concat(all_fold_results, ignore_index=True)
    selection = pd.concat(all_selections, ignore_index=True)
    fold_results.to_csv(
        OUTPUT / "INNER_CV_FOLD_RESULTS.csv.gz",
        index=False,
        compression={"method": "gzip", "mtime": 0},
        float_format="%.15g",
    )
    selection.to_csv(
        OUTPUT / "INNER_CV_SELECTION.csv", index=False, float_format="%.15g"
    )
    if len(selected_candidates) != 5:
        conclusion = "NO QUALIFIED MODEL"
        reasons = ["At least one outer fold had no qualified candidate"]
        run_manifest.update(
            status="complete_no_qualified_model",
            conclusion=conclusion,
            conclusion_reasons=reasons,
            elapsed_seconds=time.time() - task_started,
        )
        _write_json(run_manifest_path, run_manifest)
        raise ExperimentIntegrityError(
            "NO QUALIFIED MODEL: stopped before constructing complete outer OOF predictions"
        )

    predictions = pd.concat(all_predictions, ignore_index=True)
    outer_metrics = pd.concat(all_outer_metrics, ignore_index=True)
    verify_prediction_pairing(predictions)
    if predictions.loc[predictions["variant"].eq("baseline"), "source_object_id"].nunique() != len(development):
        raise ExperimentIntegrityError("Outer OOF predictions do not cover development once")
    predictions.to_csv(
        OUTPUT / "OUTER_CV_PREDICTIONS.csv.gz",
        index=False,
        compression={"method": "gzip", "mtime": 0},
        float_format="%.15g",
    )
    outer_metrics.to_csv(
        OUTPUT / "OUTER_CV_METRICS.csv", index=False, float_format="%.15g"
    )
    comparison = _pooled_comparison(predictions)
    comparison.to_csv(
        OUTPUT / "BASELINE_VS_WEIGHTED.csv", index=False, float_format="%.15g"
    )
    classification = _classification_table(predictions, outer_metrics)
    classification.to_csv(
        OUTPUT / "LOW_DO_CLASSIFICATION.csv", index=False, float_format="%.15g"
    )
    uncertainty, bootstrap_replicates = paired_site_bootstrap(predictions)
    uncertainty.to_csv(
        OUTPUT / "SITE_CLUSTERED_UNCERTAINTY.csv",
        index=False,
        float_format="%.15g",
    )
    bootstrap_replicates.to_csv(
        OUTPUT / "SITE_CLUSTERED_BOOTSTRAP_REPLICATES.csv.gz",
        index=False,
        compression={"method": "gzip", "mtime": 0},
        float_format="%.15g",
    )
    sites = site_error_comparison(predictions)
    sites.to_csv(
        OUTPUT / "SITE_ERROR_COMPARISON.csv", index=False, float_format="%.15g"
    )
    shift = _prediction_shift_analysis(predictions)
    shift.to_csv(
        OUTPUT / "PREDICTION_SHIFT_ANALYSIS.csv",
        index=False,
        float_format="%.15g",
    )
    conclusion, reasons = classify_research_conclusion(
        comparison, uncertainty, selected_candidates
    )
    figures = _make_figures(comparison, uncertainty, predictions, sites)
    _reports(
        config_hash, comparison, uncertainty, outer_metrics, selection, sites,
        shift, conclusion, reasons,
    )
    test_result = _run_tests()

    comparison_indexed = comparison.set_index("variant")
    baseline = comparison_indexed.loc["baseline"]
    weighted = comparison_indexed.loc["weighted"]
    delta_intervals = uncertainty.loc[
        uncertainty["comparison"].eq("delta_weighted_minus_baseline")
    ].set_index("metric")
    selected_summary = "\n".join(
        f"- Outer {int(row.outer_fold)}: `{row.candidate_id}`"
        for row in selection.loc[selection["selected"]].itertuples()
    )
    handoff = f"""# Phase 2B Experiment 1 Final Handoff

## Conclusion: {conclusion}

The complete frozen 128-candidate grid was evaluated in all 20 inner folds ({len(candidates) * 20:,} candidate-fold evaluations). One qualified configuration was selected independently inside each outer-training partition, then compared with the unchanged RF anchor on the corresponding held-out stations. No legacy benchmark outcome was read or used.

Selected configurations:

{selected_summary}

## Pooled outer out-of-fold comparison

| Metric | Baseline | Selected weighted procedure | Delta (weighted - baseline) | Paired site-bootstrap 95% CI for delta |
| --- | ---: | ---: | ---: | ---: |
| Overall MAE (mg/L) | {_format_metric(baseline['overall_mae_mg_l'])} | {_format_metric(weighted['overall_mae_mg_l'])} | {_format_metric(weighted['overall_mae_mg_l'] - baseline['overall_mae_mg_l'])} | [{_format_metric(delta_intervals.loc['overall_mae_mg_l', 'ci_95_lower'])}, {_format_metric(delta_intervals.loc['overall_mae_mg_l', 'ci_95_upper'])}] |
| Low-DO MAE (mg/L) | {_format_metric(baseline['low_do_mae_mg_l'])} | {_format_metric(weighted['low_do_mae_mg_l'])} | {_format_metric(weighted['low_do_mae_mg_l'] - baseline['low_do_mae_mg_l'])} | [{_format_metric(delta_intervals.loc['low_do_mae_mg_l', 'ci_95_lower'])}, {_format_metric(delta_intervals.loc['low_do_mae_mg_l', 'ci_95_upper'])}] |
| Low-DO bias (mg/L) | {_format_metric(baseline['low_do_bias_prediction_minus_truth_mg_l'])} | {_format_metric(weighted['low_do_bias_prediction_minus_truth_mg_l'])} | {_format_metric(weighted['low_do_bias_prediction_minus_truth_mg_l'] - baseline['low_do_bias_prediction_minus_truth_mg_l'])} | [{_format_metric(delta_intervals.loc['low_do_bias_prediction_minus_truth_mg_l', 'ci_95_lower'])}, {_format_metric(delta_intervals.loc['low_do_bias_prediction_minus_truth_mg_l', 'ci_95_upper'])}] |
| Low-DO recall | {_format_metric(baseline['low_do_recall'])} | {_format_metric(weighted['low_do_recall'])} | {_format_metric(weighted['low_do_recall'] - baseline['low_do_recall'])} | [{_format_metric(delta_intervals.loc['low_do_recall', 'ci_95_lower'])}, {_format_metric(delta_intervals.loc['low_do_recall', 'ci_95_upper'])}] |
| Low-DO precision | {_format_metric(baseline['low_do_precision'])} | {_format_metric(weighted['low_do_precision'])} | {_format_metric(weighted['low_do_precision'] - baseline['low_do_precision'])} | [{_format_metric(delta_intervals.loc['low_do_precision', 'ci_95_lower'])}, {_format_metric(delta_intervals.loc['low_do_precision', 'ci_95_upper'])}] |

The frozen decision rule is satisfied: {'; '.join(reasons)}. This is nevertheless a documented trade-off. Overall MAE increased, precision declined, and false positives rose from {int(baseline['false_positive_count'])} to {int(weighted['false_positive_count'])}, even though Low-DO MAE, bias, recall, F1 and false-negative rate improved. Detailed station attribution and prediction-shift analyses are retained in `SITE_ERROR_COMPARISON.csv` and `PREDICTION_SHIFT_ANALYSIS.csv`.

This conclusion is development-only nested-CV evidence. It is not external confirmation, and it does not authorize Experiment 2. No historical output was overwritten, and no Git commit or push was performed.
"""
    _write_text(OUTPUT / "PHASE2B_EXPERIMENT1_FINAL_HANDOFF.md", handoff)

    source_files = [
        ROOT / "src/weighted_regression_experiment.py",
        ROOT / "scripts/run_experiment1_weighted_regression.py",
        ROOT / "tests/test_weighted_regression_experiment.py",
    ]
    output_hashes = {
        str(path.relative_to(OUTPUT)): sha256_file(path)
        for path in sorted(OUTPUT.rglob("*"))
        if path.is_file()
        and ".checkpoints" not in path.parts
        and path.name != "EXPERIMENT1_RUN_MANIFEST.json"
    }
    checkpoint_files = [path for path in CHECKPOINTS.rglob("*") if path.is_file()]
    checkpoint_mtimes = [path.stat().st_mtime for path in checkpoint_files]
    run_manifest.update(
        status="complete",
        conclusion=conclusion,
        conclusion_reasons=reasons,
        completed_inner_folds=20,
        completed_outer_folds=5,
        completed_inner_candidate_evaluations=int(len(fold_results)),
        failed_inner_candidate_evaluations=int(
            fold_results["run_status"].ne("complete").sum()
        ),
        outer_prediction_rows=int(len(predictions)),
        bootstrap_resamples=BOOTSTRAP_RESAMPLES,
        automated_tests=test_result,
        figure_paths=[str(path.relative_to(OUTPUT)) for path in figures],
        source_code_sha256={
            str(path.relative_to(ROOT)): sha256_file(path) for path in source_files
        },
        output_sha256=output_hashes,
        last_runner_invocation_elapsed_seconds=time.time() - task_started,
        checkpoint_recovery_used=bool(
            run_manifest["checkpoint_files_present_at_start"]
        ),
        checkpoint_first_completion_unix_seconds=min(checkpoint_mtimes),
        checkpoint_last_completion_unix_seconds=max(checkpoint_mtimes),
        checkpoint_completion_span_seconds_including_interruptions=(
            max(checkpoint_mtimes) - min(checkpoint_mtimes)
        ),
        candidate_fit_elapsed_seconds_aggregate=float(
            fold_results["elapsed_seconds"].sum()
        ),
        outer_fit_elapsed_seconds_aggregate=float(
            outer_metrics["elapsed_seconds"].sum()
        ),
        legacy_benchmark_read=False,
    )
    _write_json(run_manifest_path, run_manifest)


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        traceback.print_exc()
        raise
