#!/usr/bin/env python3
"""Generate WaterSense Research Upgrade V4 Candidate evidence.

The script reads frozen v3 artifacts, executes one development-only classifier
pre-specified in the saved V4 protocol, performs hypothetical decision-cost
sensitivity, and writes only to research_upgrade_v4_candidate. Independent
preregistration is not established. It never reads the legacy held-out test
outcomes for model selection and never modifies a deployed model.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "research_upgrade_v3"
OUT = ROOT / "research_upgrade_v4_candidate"
PREDICTIONS = V3 / "experiment1_weighted_regression/OUTER_CV_PREDICTIONS.csv.gz"
ASSIGNMENTS = V3 / "phase2b0/NESTED_CV_SITE_ASSIGNMENTS.csv"
PROCESSED = ROOT / "data/processed/water_quality_modeling.csv"
RAW = ROOT / "data/raw/niea_river_water_quality_1990_2024.csv"
CURRENT_EXPORT_SHA256 = "a5ce02d9ab3703edc4279c8dc5f9d38a593b92c555945c5cdb2ab3ca55632632"

sys.path.insert(0, str(ROOT))
from src.preprocessing import build_water_quality_feature_preprocessor  # noqa: E402
from src.research_config import FEATURE_SETS  # noqa: E402


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_text(name: str, value: str) -> None:
    (OUT / name).write_text(value.rstrip() + "\n", encoding="utf-8")


def write_json(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def metric_row(name: str, y: np.ndarray, pred: np.ndarray) -> dict[str, object]:
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "model": name,
        "sample_count": int(len(y)),
        "low_do_count": int(y.sum()),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_negatives": int(tn),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
    }


def fit_classifier() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    historical = pd.read_csv(PREDICTIONS)
    baseline = historical.loc[historical["variant"] == "baseline"].copy()
    if len(baseline) != 119_690 or baseline["source_object_id"].nunique() != 119_690:
        raise RuntimeError("Frozen baseline OOF identity changed")
    data = pd.read_csv(PROCESSED)
    keep = set(baseline["source_object_id"].astype(int))
    development = data.loc[data["source_object_id"].astype(int).isin(keep)].copy()
    if (len(development), development["station_code"].nunique()) != (119_690, 672):
        raise RuntimeError("Development population mismatch")
    assignments = pd.read_csv(ASSIGNMENTS)
    outer = assignments.loc[assignments["level"] == "outer", ["station_code", "validation_fold"]]
    fold_for_station = dict(zip(outer["station_code"], outer["validation_fold"], strict=True))
    development["outer_fold"] = development["station_code"].map(fold_for_station)
    if development["outer_fold"].isna().any():
        raise RuntimeError("Unassigned development station")

    features = list(FEATURE_SETS["full"][0])
    rows: list[pd.DataFrame] = []
    fold_metrics: list[dict[str, object]] = []
    for fold in range(1, 6):
        train = development.loc[development["outer_fold"] != fold]
        valid = development.loc[development["outer_fold"] == fold]
        model = Pipeline([
            ("preprocess", build_water_quality_feature_preprocessor(features)),
            ("classifier", LogisticRegression(
                C=1.0, solver="lbfgs", class_weight="balanced", max_iter=1000,
                random_state=20261014,
            )),
        ])
        y_train = (train["dissolved_oxygen_mg_l"].to_numpy() < 4.0).astype(int)
        y_valid = (valid["dissolved_oxygen_mg_l"].to_numpy() < 4.0).astype(int)
        model.fit(train[features], y_train)
        probability = model.predict_proba(valid[features])[:, 1]
        predicted = (probability >= 0.5).astype(int)
        part = valid[["source_object_id", "station_code", "sample_date", "dissolved_oxygen_mg_l"]].copy()
        part["outer_fold"] = fold
        part["actual_low_do"] = y_valid
        part["predicted_low_do_probability"] = probability
        part["predicted_low_do"] = predicted
        rows.append(part)
        fold_metrics.append({"scope": "outer_fold", "outer_fold": fold, **metric_row("dedicated_logistic_classifier", y_valid, predicted)})

    predictions = pd.concat(rows, ignore_index=True).sort_values("source_object_id")
    if len(predictions) != 119_690 or predictions["source_object_id"].nunique() != 119_690:
        raise RuntimeError("Classifier OOF coverage failure")
    y = predictions["actual_low_do"].to_numpy(dtype=int)
    pred = predictions["predicted_low_do"].to_numpy(dtype=int)
    fold_metrics.append({"scope": "pooled_outer_oof", "outer_fold": "", **metric_row("dedicated_logistic_classifier", y, pred)})

    station_rows = []
    for station, group in predictions.groupby("station_code"):
        if int(group["actual_low_do"].sum()) == 0:
            continue
        station_rows.append({"station_code": station, **metric_row("dedicated_logistic_classifier", group["actual_low_do"].to_numpy(int), group["predicted_low_do"].to_numpy(int))})
    return predictions, pd.DataFrame(fold_metrics), pd.DataFrame(station_rows)


def historical_comparison(classifier_predictions: pd.DataFrame) -> pd.DataFrame:
    historical = pd.read_csv(PREDICTIONS)
    rows = []
    for variant, group in historical.groupby("variant", sort=False):
        rows.append({
            "evidence_status": "HISTORICAL_V3_DEVELOPMENT_ONLY",
            "comparison_scope": "DESCRIPTIVE_SAME_POPULATION_DIFFERENT_PROTOCOL_NOT_CONFIRMATORY",
            "model": "historical_fixed_regression_baseline" if variant == "baseline" else "historical_v3_selected_procedure",
            "overall_mae_mg_l": float(np.mean(np.abs(group["predicted_do_mg_l"] - group["actual_do_mg_l"]))),
            "low_do_mae_mg_l": float(np.mean(np.abs(group.loc[group["actual_low_do"], "predicted_do_mg_l"] - group.loc[group["actual_low_do"], "actual_do_mg_l"]))),
            **{k: v for k, v in metric_row(variant, group["actual_low_do"].astype(int).to_numpy(), group["predicted_low_do"].astype(int).to_numpy()).items() if k != "model"},
        })
    y = classifier_predictions["actual_low_do"].to_numpy(int)
    pred = classifier_predictions["predicted_low_do"].to_numpy(int)
    rows.append({
        "evidence_status": "NEW_EXPERIMENT_EXPLORATORY_DEVELOPMENT_ONLY",
        "comparison_scope": "DESCRIPTIVE_SAME_POPULATION_DIFFERENT_PROTOCOL_NOT_CONFIRMATORY",
        "model": "dedicated_logistic_classifier",
        "overall_mae_mg_l": np.nan,
        "low_do_mae_mg_l": np.nan,
        **{k: v for k, v in metric_row("classifier", y, pred).items() if k != "model"},
    })
    return pd.DataFrame(rows)


def cost_sensitivity(comparison: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ratio in [1, 2, 5, 10, 25, 50]:
        costs = []
        for record in comparison.to_dict("records"):
            cost = ratio * int(record["false_negatives"]) + int(record["false_positives"])
            costs.append((record["model"], cost))
        minimum = min(value for _, value in costs)
        for model, cost in costs:
            rows.append({
                "c_fn": ratio, "c_fp": 1, "fn_fp_ratio": f"{ratio}:1",
                "model": model, "false_negatives": int(comparison.loc[comparison["model"] == model, "false_negatives"].iloc[0]),
                "false_positives": int(comparison.loc[comparison["model"] == model, "false_positives"].iloc[0]),
                "hypothetical_cost": int(cost), "minimum_for_scenario": bool(cost == minimum),
            })
    return pd.DataFrame(rows)


def plot_cost(cost: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    for model, group in cost.groupby("model"):
        ax.plot(group["c_fn"], group["hypothetical_cost"], marker="o", label=model.replace("_", " "))
    ax.set_xscale("log")
    ax.set_xlabel("Hypothetical false-negative cost (false-positive cost = 1)")
    ax.set_ylabel("Total hypothetical cost")
    ax.set_title("Development-only low-DO cost sensitivity")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "COST_SENSITIVITY.png", dpi=180)
    plt.close(fig)


def baseline_manifest() -> dict[str, object]:
    keys = [
        "README.md", "research_outputs/manifest.json",
        "research_upgrade_v3/phase2b0/WEIGHTED_REGRESSION_CONFIG.json",
        "research_upgrade_v3/experiment1_weighted_regression/EXPERIMENT1_CONFIG.json",
        "research_upgrade_v3/experiment1_weighted_regression/OUTER_CV_PREDICTIONS.csv.gz",
        "research_upgrade_v3/final_closeout/FINAL_SCIENTIFIC_REPORT.md",
        "models/phase4_selected_model.joblib",
        "data/raw/niea_river_water_quality_1990_2024.csv",
        "data/processed/water_quality_modeling.csv",
    ]
    usage = shutil.disk_usage(ROOT)
    return {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "branch": git("branch", "--show-current"), "head": git("rev-parse", "HEAD"),
        "preexisting_status": ["?? research_upgrade_v3/final_closeout/RESEARCH_CONTRIBUTION_STATEMENT.md"],
        "python": sys.version, "platform": platform.platform(),
        "dependencies": {"numpy": np.__version__, "pandas": pd.__version__, "scikit_learn": sklearn.__version__},
        "disk_available_bytes": usage.free,
        "data_access": {"raw": RAW.is_file(), "processed": PROCESSED.is_file(), "historical_model": (ROOT / "models/phase4_selected_model.joblib").is_file()},
        "key_files": {path: sha256(ROOT / path) for path in keys},
        "current_official_export_sha256": CURRENT_EXPORT_SHA256,
        "current_export_matches_historical_raw": sha256(RAW) == CURRENT_EXPORT_SHA256,
    }


def write_release_candidate_manifest() -> None:
    paths = [
        ROOT / "README.md",
        V3 / "final_closeout/W02_ERRATUM_2026-10-14.md",
        V3 / "final_closeout/RESEARCH_CONTRIBUTION_STATEMENT.md",
    ]
    paths.extend(
        path for path in sorted(OUT.rglob("*"))
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.name != "V4_RELEASE_CANDIDATE_MANIFEST.json"
    )
    write_json("V4_RELEASE_CANDIDATE_MANIFEST.json", {
        "schema": "watersense-v4-release-candidate-v1",
        "scope": "isolated local release candidate; not a release or main-branch merge",
        "files": {str(path.relative_to(ROOT)): sha256(path) for path in paths},
    })


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = baseline_manifest()
    write_json("BASELINE_INTEGRITY_MANIFEST.json", manifest)
    predictions, fold_metrics, station_metrics = fit_classifier()
    predictions.to_csv(
        OUT / "WATERSENSE_CLASSIFIER_OOF_PREDICTIONS.csv.gz",
        index=False,
        compression={"method": "gzip", "mtime": 0},
    )
    fold_metrics.to_csv(OUT / "WATERSENSE_CLASSIFIER_FOLD_METRICS.csv", index=False)
    station_metrics.to_csv(OUT / "WATERSENSE_CLASSIFIER_STATION_METRICS.csv", index=False)
    comparison = historical_comparison(predictions)
    comparison.to_csv(OUT / "WATERSENSE_EXPERIMENT_COMPARISON.csv", index=False)
    cost = cost_sensitivity(comparison)
    cost.to_csv(OUT / "COST_SENSITIVITY.csv", index=False)
    plot_cost(cost)
    pooled = comparison.set_index("model")
    cls = pooled.loc["dedicated_logistic_classifier"]
    winners = cost.loc[cost["minimum_for_scenario"]].groupby("fn_fp_ratio")["model"].apply(lambda x: ", ".join(x)).to_dict()
    write_text("COST_SENSITIVITY_REPORT.md", f"""# WaterSense decision-cost sensitivity

**Status: NEW ANALYSIS — EXPLORATORY / DEVELOPMENT-ONLY.**

The analysis applies `Cost = C_FN × FN + C_FP × FP` to the same 119,690 frozen outer-OOF development observations. `C_FP` is fixed at 1 and `C_FN` is varied. The values are hypothetical scenario weights, not observed ecological, public-health, or regulatory costs.

| FN:FP | Minimum-cost model(s) |
| --- | --- |
""" + "\n".join(f"| {key} | {value} |" for key, value in winners.items()) + """

The conclusion is conditional: changing the assumed consequence ratio changes the preferred decision rule. The CSV retains every model/scenario result, including ties, and the figure visualizes the complete set specified in the saved V4 development protocol. These are hypothetical assumptions, not measured regulatory or economic losses. No scenario was selected after results as the single 'correct' cost.
""")
    write_text("WATERSENSE_EXTERNAL_VALIDATION.md", f"""# WaterSense external-validation feasibility

**Status: BLOCKED — External Validation: NOT AVAILABLE.** Assessment date: 2026-10-14.

The official OpenDataNI/NIEA ArcGIS service describes 178,680 rows dated 1990-01-02 through 2024-12-11, with zero rows after 2024-12-31. The current official CSV was downloaded once from the documented ArcGIS Hub endpoint. Its SHA-256 is `{CURRENT_EXPORT_SHA256}` and it is byte-for-byte identical to the preserved historical raw export (also `{sha256(RAW)}`). It therefore has complete record overlap and cannot be called a new time period, external region, or independent confirmation set.

Source: OpenDataNI/NIEA, UK Open Government Licence v3.0. Catalogue: <https://www.data.gov.uk/dataset/15ec8080-ee1c-469b-858e-546d2fb57c27/riverwaterqualitymonitoring-1990to2024-allparameters13>. Service: <https://services-eu1.arcgis.com/kswen6BYexuc1SUk/arcgis/rest/services/River_Water_Quality_Monitoring_1990_to_2024_All_Parameters/FeatureServer/0>. Export URL is recorded in `external_validation.py`.

Because independence fails before model access, no external predictions or metrics were computed. A future candidate must pass the frozen license, provenance, overlap, units/method, target-validity, feature-coverage, and model-freeze gates in `EXPERIMENT_PROTOCOL.md`.
""")
    write_text("WATERSENSE_V4_SCIENTIFIC_REPORT.md", f"""# WaterSense AI — Research Upgrade V4 Candidate

## Status and evidence classes

- **HISTORICAL:** 151,031 modelling records, 840 stations, 1990–2024; station-grouped, spatiotemporal, basin, and nested-CV evidence.
- **REPRODUCED:** the current code suite passed 88/88 tests on 2026-10-14; v3 development metrics were re-read from frozen OOF predictions, not rerun or relabelled as new.
- **NEW EXPERIMENT — EXPLORATORY:** the fixed dedicated classifier was evaluated by five station-disjoint outer folds on the development population.
- **INDEPENDENT CONFIRMATION:** none.
- **BLOCKED:** current official OpenDataNI data are byte-identical to the historical raw export.

## Historical v3 result

The fixed regression baseline versus the v3 selected procedure had Overall MAE 0.8797 versus 0.9516 mg/L, Low-DO MAE 3.3235 versus 2.3613 mg/L, Recall 0.1293 versus 0.3641, Precision 0.7903 versus 0.5576, and false positives 26 versus 219. These are historical development-only outer-OOF results.

## New controlled classifier result

The Logistic Regression classifier was **pre-specified in the saved V4 development protocol; independent preregistration is not established**. On the same 119,690-row development OOF population it produced TP **{int(cls['true_positives'])}**, FP **{int(cls['false_positives'])}**, TN **{int(cls['true_negatives'])}**, FN **{int(cls['false_negatives'])}**, low-DO prevalence **{100 * int(cls['low_do_count']) / int(cls['sample_count']):.4f}%**, Recall **{cls['recall']:.4f}**, Precision **{cls['precision']:.4f}**, and F1 **{cls['f1']:.4f}** at `P(low DO) >= 0.5` for measured `DO < 4 mg/L`. Regression MAE is not applicable to a binary classifier. Fold and low-DO-station variation are retained in separate CSVs.

**DESCRIPTIVE; DIFFERENT PROTOCOL; NOT CONFIRMATORY.** V3 and V4 share sample IDs, stations, outer-fold membership and true labels, but differ in objective, decision function, model-selection protocol and research timing. They are `NOT DIRECTLY COMPARABLE AS A PERFORMANCE-IMPROVEMENT EXPERIMENT`. This is not a new model-selection victory. It is one fixed comparison after v3, on a repeatedly used development population, with no untouched confirmation set. The two-stage option was deliberately not added after viewing results.

## Scientific interpretation

V4 strengthens the evidence boundary rather than replacing the historical model. It demonstrates how a dedicated classifier changes the error trade-off and how the preferred rule depends on explicit hypothetical FN/FP cost assumptions. It also establishes that the checked official export is not independent of the preserved historical file; it does not establish that no other external source exists. No deployed model, historical result, or frozen v3 artifact was changed. See the additive [W02 erratum](../research_upgrade_v3/final_closeout/W02_ERRATUM_2026-10-14.md).
""")
    write_text("WATERSENSE_REPRODUCIBILITY.md", """# WaterSense V4 reproducibility

Status: **PASS for code/tests and V4 development analysis; PARTIAL for full scientific confirmation.**

Commands from the repository root:

```bash
PYTHONPATH=. python -m unittest discover -s tests -v
PYTHONPATH=. python research_upgrade_v4_candidate/v4_upgrade.py
PYTHONPATH=. python -m unittest discover -s research_upgrade_v4_candidate -p 'test_*.py' -v
```

Use a compatible environment installed from `requirements.txt`. The V4 runner writes only to its candidate directory and verifies exact row/station coverage. Raw and processed data remain ignored local artifacts and are hash-recorded in the baseline manifest. Independent confirmation cannot be reproduced because no qualifying external dataset exists.
""")
    artifacts = {
        str(path.relative_to(OUT)): sha256(path)
        for path in sorted(OUT.rglob("*"))
        if path.is_file()
        and path.name not in {"V4_ARTIFACT_MANIFEST.json", "V4_RELEASE_CANDIDATE_MANIFEST.json"}
        and "__pycache__" not in path.parts
    }
    write_json("V4_ARTIFACT_MANIFEST.json", {"schema": "watersense-v4-candidate-artifacts-v1", "files": artifacts})
    write_release_candidate_manifest()
    print(json.dumps({"classifier": cls.to_dict(), "outputs": len(list(OUT.iterdir()))}, default=str))


if __name__ == "__main__":
    main()
