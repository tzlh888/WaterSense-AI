#!/usr/bin/env python3
"""Recompute the Phase 2A low-DO reliability package from saved predictions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from src.low_do_reliability import (  # noqa: E402
    BOOTSTRAP_RESAMPLES,
    BOOTSTRAP_SEED,
    LOW_DO_THRESHOLD_MG_L,
    aggregate_repeated_observations,
    compute_low_do_metrics,
    low_do_site_analysis,
    normalise_prediction_columns,
    sha256_file,
    site_clustered_bootstrap,
    spearman_feature_associations,
    stratified_metrics,
)


PREDICTION_SOURCES = {
    "station_grouped_holdout": "results/phase4_holdout_predictions.csv",
    "temporal_2022_2024": "research_outputs/predictions/temporal.csv.gz",
    "spatiotemporal_seed_42": "research_outputs/predictions/spatiotemporal.csv.gz",
    "repeated_spatiotemporal_appearances": (
        "research_outputs_v2/predictions/repeated_spatiotemporal_predictions.csv.gz"
    ),
    "spatial_basin_holdout": (
        "research_outputs_v2/predictions/spatial_basin_predictions.csv.gz"
    ),
}
FROZEN_ARTIFACT_SOURCES = {
    "environment_lock": "requirements.txt",
    "historical_protocol": "docs/research_protocol.md",
    "split_summary": "results/split_summary.json",
    "phase4_summary": "results/phase4_summary.json",
    "v1_manifest": "research_outputs/manifest.json",
    "spatiotemporal_validation_summary": (
        "research_outputs/tables/spatiotemporal_validation.csv"
    ),
    "validation_target_distribution": (
        "research_outputs/tables/validation_target_distribution.csv"
    ),
    "v2_manifest": "research_outputs_v2/manifests/v2_manifest.json",
    "selected_model": "models/phase4_selected_model.joblib",
}
FEATURE_COLUMNS = [
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


def _write_csv(data: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(path, index=False, float_format="%.10g")


def _fmt(value: object, digits: int = 3) -> str:
    if value is None or pd.isna(value):
        return "undefined"
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    return f"{float(value):.{digits}f}"


def _markdown_table(data: pd.DataFrame) -> str:
    """Render a small Markdown table without an optional tabulate dependency."""
    columns = [str(column) for column in data.columns]
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for values in data.itertuples(index=False, name=None):
        rows.append("| " + " | ".join(_fmt(value) if isinstance(value, (float, np.floating)) else str(value) for value in values) + " |")
    return "\n".join(rows)


def _make_figures(
    holdout: pd.DataFrame, site_table: pd.DataFrame, uncertainty: pd.DataFrame, output: Path
) -> None:
    figure_dir = output / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    low = holdout[holdout["actual_do_mg_l"] < LOW_DO_THRESHOLD_MG_L]

    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    ax.scatter(
        holdout["actual_do_mg_l"],
        holdout["predicted_do_mg_l"],
        s=8,
        alpha=0.12,
        label="All holdout observations",
    )
    ax.scatter(
        low["actual_do_mg_l"],
        low["predicted_do_mg_l"],
        s=18,
        alpha=0.7,
        color="#c43c39",
        label="Ground truth <4 mg/L",
    )
    bounds = [
        min(holdout["actual_do_mg_l"].min(), holdout["predicted_do_mg_l"].min()),
        max(holdout["actual_do_mg_l"].max(), holdout["predicted_do_mg_l"].max()),
    ]
    ax.plot(bounds, bounds, "--", color="black", linewidth=1, label="Ideal")
    ax.axvline(4, color="#c43c39", linewidth=1, linestyle=":")
    ax.axhline(4, color="#c43c39", linewidth=1, linestyle=":")
    ax.set(
        title="Station-grouped legacy holdout: actual vs predicted DO",
        xlabel="Ground-truth DO (mg/L)",
        ylabel="Predicted DO (mg/L)",
    )
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(figure_dir / "LOW_DO_ACTUAL_VS_PREDICTED.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.hist(low["prediction_minus_ground_truth_mg_l"], bins=30, color="#4c78a8")
    ax.axvline(0, linestyle="--", color="black", linewidth=1)
    ax.set(
        title="Low-DO residual distribution",
        xlabel="Prediction − ground truth (mg/L)",
        ylabel="Observations",
    )
    fig.tight_layout()
    fig.savefig(figure_dir / "LOW_DO_RESIDUAL_DISTRIBUTION.png", dpi=180)
    plt.close(fig)

    plot_sites = site_table.head(20).sort_values(
        "low_do_bias_prediction_minus_truth_mg_l"
    )
    fig, ax = plt.subplots(figsize=(8.2, 7.0))
    sizes = 25 + 15 * np.sqrt(plot_sites["low_do_count"])
    ax.scatter(
        plot_sites["low_do_bias_prediction_minus_truth_mg_l"],
        plot_sites["station_code"],
        s=sizes,
        color="#f58518",
    )
    ax.axvline(0, linestyle="--", color="black", linewidth=1)
    ax.set(
        title="Top 20 station contributions to low-DO absolute error",
        xlabel="Station mean prediction − ground truth (mg/L); marker size ∝ low-DO n",
        ylabel="Station code",
    )
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(figure_dir / "LOW_DO_SITE_ERROR.png", dpi=180)
    plt.close(fig)

    metrics_to_plot = [
        ("low_do_mae_mg_l", "Low-DO MAE (mg/L)"),
        ("low_do_false_negative_rate", "False-negative rate"),
    ]
    partitions = [
        "station_grouped_holdout",
        "temporal_2022_2024",
        "spatiotemporal_seed_42",
        "spatial_basin_holdout",
        "repeated_spatiotemporal_unique_mean_prediction",
    ]
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.5), sharey=True)
    y = np.arange(len(partitions))
    for ax, (metric, title) in zip(axes, metrics_to_plot, strict=True):
        view = (
            uncertainty[uncertainty["metric"].eq(metric)]
            .set_index("partition")
            .loc[partitions]
        )
        x = view["estimate"].to_numpy(float)
        lower = np.maximum(0.0, x - view["ci_95_lower"].to_numpy(float))
        upper = np.maximum(0.0, view["ci_95_upper"].to_numpy(float) - x)
        ax.errorbar(x, y, xerr=np.vstack([lower, upper]), fmt="o", capsize=3)
        ax.set(title=title, xlabel="Estimate and 95% percentile CI")
        ax.grid(axis="x", alpha=0.2)
    axes[0].set_yticks(y, partitions)
    fig.suptitle("Site-clustered bootstrap uncertainty", fontsize=14)
    fig.tight_layout()
    fig.savefig(figure_dir / "LOW_DO_SITE_CLUSTERED_UNCERTAINTY.png", dpi=180)
    plt.close(fig)


def _report(
    metrics: pd.DataFrame,
    uncertainty: pd.DataFrame,
    site_table: pd.DataFrame,
    yearly: pd.DataFrame,
    associations: pd.DataFrame,
) -> str:
    grouped = metrics.loc[metrics["partition"] == "station_grouped_holdout"].iloc[0]
    repeated = metrics.loc[
        metrics["partition"] == "repeated_spatiotemporal_appearances"
    ].iloc[0]
    unique = metrics.loc[
        metrics["partition"] == "repeated_spatiotemporal_unique_mean_prediction"
    ].iloc[0]
    grouped_ci = uncertainty[
        uncertainty["partition"].eq("station_grouped_holdout")
    ].set_index("metric")
    top = site_table.head(5)
    top_share = top["absolute_error_share"].sum()
    strongest = associations.assign(
        strength=associations["spearman_with_absolute_error"].abs()
    ).sort_values("strength", ascending=False).head(5)
    strongest_table = _markdown_table(
        strongest[
            [
                "feature",
                "nonmissing_count",
                "missing_fraction",
                "spearman_with_absolute_error",
            ]
        ]
    )
    invalid_table = _markdown_table(
        uncertainty.loc[
            uncertainty["invalid_resamples"] > 0,
            ["partition", "metric", "valid_resamples", "invalid_resamples"],
        ]
    )
    return f"""# WaterSense Low-DO Reliability Report

**Generated from saved predictions only:** no model fitting or selection was performed.  
**Positive class:** ground-truth DO `< 4 mg/L`; predicted positive: prediction `< 4 mg/L`.  
**Primary detailed view:** the previously inspected station-grouped holdout; it is a legacy benchmark, not a new independent holdout.

## Executive finding

The deployed regression is not reliable for low-oxygen detection on the saved legacy evaluations. On the station-grouped holdout, overall MAE is **{_fmt(grouped['overall_mae_mg_l'])} mg/L**, but low-DO MAE rises to **{_fmt(grouped['low_do_mae_mg_l'])} mg/L** and mean low-DO bias (prediction − truth) is **+{_fmt(grouped['low_do_bias_prediction_minus_truth_mg_l'])} mg/L**. Recall is **{_fmt(grouped['low_do_recall'])}** ({int(grouped['true_positive_count'])}/{int(grouped['low_do_count'])}); the false-negative rate is **{_fmt(grouped['low_do_false_negative_rate'])}** ({int(grouped['false_negative_count'])}/{int(grouped['low_do_count'])}). Precision is **{_fmt(grouped['low_do_precision'])}** ({int(grouped['true_positive_count'])}/{int(grouped['predicted_low_do_count'])}).

The direction is consistent with systematic overestimation of true low values. This is a confirmed descriptive finding for the saved predictions, not evidence of a causal mechanism or prospective generalisation.

## Denominators and metric rules

- Regression metrics use every row in the named saved-prediction partition.
- Low-DO MAE/RMSE/bias use rows whose ground truth is strictly below 4 mg/L.
- Recall = TP/(TP+FN); FNR = FN/(TP+FN); precision = TP/(TP+FP); F1 = 2TP/(2TP+FP+FN).
- If a partition has zero predicted positives, precision and F1 are stored as missing/undefined, never silently replaced with zero. If it has zero actual positives, recall and FNR are undefined. Each bootstrap metric reports its valid and invalid resample counts.
- Bias is always prediction minus ground truth; positive values mean overprediction.

## Independent evidence and repeated appearances

The repeated spatiotemporal file contains **{int(repeated['low_do_count'])} low-DO appearances**, but only **{int(unique['low_do_count'])} unique low-DO source observations** at **{int(unique['low_do_station_count'])} stations**. The same source observation appears under multiple split seeds, so appearances share both measured outcomes and modelling context. They cannot be treated as {int(repeated['low_do_count'])} independent observations. The unique-observation view averages predictions across an observation's appearances before station-clustered bootstrap; this reduces duplication but still does not create a new holdout.

## Site-clustered uncertainty

The station-grouped low-DO MAE 95% interval is **[{_fmt(grouped_ci.loc['low_do_mae_mg_l','ci_95_lower'])}, {_fmt(grouped_ci.loc['low_do_mae_mg_l','ci_95_upper'])}] mg/L**; low-DO bias is **[{_fmt(grouped_ci.loc['low_do_bias_prediction_minus_truth_mg_l','ci_95_lower'])}, {_fmt(grouped_ci.loc['low_do_bias_prediction_minus_truth_mg_l','ci_95_upper'])}] mg/L**; FNR is **[{_fmt(grouped_ci.loc['low_do_false_negative_rate','ci_95_lower'])}, {_fmt(grouped_ci.loc['low_do_false_negative_rate','ci_95_upper'])}]**. Bootstrap draws whole sites with replacement using seed {BOOTSTRAP_SEED} and {BOOTSTRAP_RESAMPLES:,} replicates. Only {int(grouped['low_do_station_count'])} holdout sites contain low-DO observations, so intervals remain sensitive to which rare sites appear; the bootstrap quantifies sampling instability within this observed station population, not external validity.

Resamples with undefined metrics are excluded only from that metric's percentile calculation and explicitly counted:

{invalid_table}

## Error concentration and distribution

The five largest station contributors account for **{top_share:.1%}** of station-grouped low-DO absolute error. Their identifiers and metrics are in `LOW_DO_SITE_ANALYSIS.csv`; this concentration is descriptive and partly reflects unequal observation counts.

Years differ in low-DO support and error; `LOW_DO_YEAR_ANALYSIS.csv` reports denominators rather than presenting unstable small-year estimates as equivalent. The strongest exploratory feature/error correlations are:

{strongest_table}

These are statistical associations within low-DO holdout rows. They do not establish that changing a chemical measurement would change model error. Missingness is evaluated separately in `LOW_DO_MISSINGNESS_ANALYSIS.csv`.

## Training support and evidence gaps

The raw source CSV and processed modelling table are absent from the public checkout. Therefore exact training-set low-DO counts and row-level target membership cannot be freshly verified here. The saved `spatiotemporal_validation.csv` reports a training low-DO fraction of **0.005994 (0.5994%)** for its 120,955-row training partition. This is clear aggregate evidence of severe rarity in that historical partition, but remains saved metadata rather than a fresh row-level reconstruction. Feature associations can be computed for the full station holdout because that saved table includes features; comparable attribution is unavailable for prediction files that retain only identifiers, dates, actuals, and predictions.

Potential measurement anomalies are listed as review candidates in `LOW_DO_EXTREME_CASES.csv`. Saved predictions alone cannot determine whether an extreme value is a sensor/measurement error, a genuine event, or an underrepresented regime.

## Interpretation classes

- **Confirmed finding:** saved predictions substantially overpredict true low DO and miss most `<4 mg/L` cases across all recorded validation regimes.
- **Statistical association:** site, year, feature value, and missingness summaries identify concentration or correlation with error in the legacy holdout.
- **Hypothesis requiring further testing:** low-DO rarity, omitted hydrologic/context features, censoring, temporal shift, or measurement problems may cause the failure. Causal attribution requires eligible development data and prospectively frozen evaluation.
"""


def _failure_report(metrics: pd.DataFrame, site_table: pd.DataFrame) -> str:
    grouped = metrics.loc[metrics["partition"] == "station_grouped_holdout"].iloc[0]
    top = site_table.head(10)[
        [
            "station_code",
            "low_do_count",
            "false_negative_count",
            "low_do_mae_mg_l",
            "low_do_bias_prediction_minus_truth_mg_l",
            "absolute_error_share",
        ]
    ]
    top_table = _markdown_table(top)
    return f"""# Low-DO Failure Analysis

## Confirmed findings

- In the station-grouped legacy holdout, {int(grouped['false_negative_count'])} of {int(grouped['low_do_count'])} true low-DO observations are false negatives (FNR {_fmt(grouped['low_do_false_negative_rate'])}).
- Mean prediction minus truth on true low-DO rows is +{_fmt(grouped['low_do_bias_prediction_minus_truth_mg_l'])} mg/L; the error is overwhelmingly in the unsafe overprediction direction.
- Error is not uniformly distributed across stations. The leading station contributions are:

{top_table}

`LOW_DO_FALSE_NEGATIVES.csv` preserves row identifiers, station/date, actual, prediction, error, and available feature missingness so every listed failure can be traced to a saved historical prediction.

## Statistical associations

- `LOW_DO_YEAR_ANALYSIS.csv` compares years while retaining low-DO counts and site counts.
- `LOW_DO_FEATURE_ASSOCIATIONS.csv` reports Spearman associations with absolute error and signed bias. These are exploratory, unadjusted, and based only on low-DO rows.
- `LOW_DO_MISSINGNESS_ANALYSIS.csv` compares error by row-level feature missingness. Missingness may proxy period, station, laboratory practice, or chemistry; it is not proven causal.
- `LOW_DO_SITE_ANALYSIS.csv` reports each site's contribution to total low-DO absolute and squared error. Large shares can result from more observations, larger per-row errors, or both.

## Hypotheses requiring further testing

1. Low-DO rarity may cause regression-to-the-centre and weak threshold recall.
2. Missing hydrologic, meteorological, depth, flow, or event context may limit transfer to low-oxygen regimes.
3. Some extreme rows may be genuine events, censoring artifacts, or measurement problems; raw records and provenance are needed to adjudicate them.
4. Year/site associations may reflect distribution shift rather than stable effects.

No item in this section is promoted to a causal conclusion. Phase 2B must test preregistered interventions only within development stations.
"""


def run(repository_root: Path, output: Path) -> None:
    loaded: dict[str, pd.DataFrame] = {}
    evidence_rows = []
    for name, relative in PREDICTION_SOURCES.items():
        path = repository_root / relative
        if not path.is_file():
            raise FileNotFoundError(f"Required saved predictions are missing: {relative}")
        loaded[name] = normalise_prediction_columns(pd.read_csv(path))
        evidence_rows.append(
            {
                "role": "saved_predictions",
                "partition": name,
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    for role, relative in FROZEN_ARTIFACT_SOURCES.items():
        path = repository_root / relative
        if not path.is_file():
            raise FileNotFoundError(f"Required frozen artifact is missing: {relative}")
        evidence_rows.append(
            {
                "role": role,
                "partition": "not_applicable",
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    repeated_unique = aggregate_repeated_observations(
        loaded["repeated_spatiotemporal_appearances"]
    )
    loaded["repeated_spatiotemporal_unique_mean_prediction"] = repeated_unique

    metric_rows = []
    for name, frame in loaded.items():
        row = compute_low_do_metrics(frame)
        row["partition"] = name
        row["evidence_status"] = "legacy_benchmark"
        row["independence_note"] = (
            "dependent appearances across repeated split seeds; descriptive only"
            if name == "repeated_spatiotemporal_appearances"
            else (
                "one row per source ID; predictions averaged across appearances"
                if name == "repeated_spatiotemporal_unique_mean_prediction"
                else "rows clustered within station; use site-clustered interval"
            )
        )
        metric_rows.append(row)
    metrics = pd.DataFrame(metric_rows)

    bootstrap_rows = []
    for name, frame in loaded.items():
        if name == "repeated_spatiotemporal_appearances":
            continue
        result = site_clustered_bootstrap(frame)
        summary = result.summary.copy()
        summary.insert(0, "partition", name)
        bootstrap_rows.append(summary)
    uncertainty = pd.concat(bootstrap_rows, ignore_index=True)

    holdout = loaded["station_grouped_holdout"]
    site_table = low_do_site_analysis(holdout)
    site_table.insert(0, "partition", "station_grouped_holdout")
    concentration_bins = pd.cut(
        holdout["actual_do_mg_l"],
        bins=[-np.inf, 4.0, 8.0, 12.0, np.inf],
        right=False,
        labels=["<4", "4-<8", "8-<12", ">=12"],
    )
    by_concentration = stratified_metrics(
        holdout, concentration_bins, stratum_name="ground_truth_do_bin"
    )
    by_year = stratified_metrics(
        holdout, holdout["sample_year"], stratum_name="sample_year"
    ).sort_values("sample_year")

    feature_associations = spearman_feature_associations(holdout, FEATURE_COLUMNS)
    feature_frame = holdout[[c for c in FEATURE_COLUMNS if c in holdout]]
    holdout = holdout.copy()
    holdout["feature_missing_count"] = feature_frame.isna().sum(axis=1)
    holdout["feature_missing_fraction"] = feature_frame.isna().mean(axis=1)
    missingness_group = pd.cut(
        holdout["feature_missing_fraction"],
        bins=[-0.001, 0.0, 0.25, 0.5, 1.0],
        labels=["none", "(0,0.25]", "(0.25,0.5]", "(0.5,1]"],
    )
    missingness = stratified_metrics(
        holdout, missingness_group, stratum_name="feature_missingness_group"
    )
    low = holdout[holdout["actual_do_mg_l"] < LOW_DO_THRESHOLD_MG_L].copy()
    missing_spearman = low["feature_missing_fraction"].corr(
        low["absolute_error_mg_l"], method="spearman"
    )
    missingness["low_do_spearman_missing_fraction_vs_absolute_error"] = (
        missing_spearman
    )
    false_negatives = low[low["predicted_do_mg_l"] >= LOW_DO_THRESHOLD_MG_L].copy()
    trace_columns = [
        "source_object_id",
        "station_code",
        "sample_date",
        "sample_year",
        "actual_do_mg_l",
        "predicted_do_mg_l",
        "prediction_minus_ground_truth_mg_l",
        "absolute_error_mg_l",
        "feature_missing_count",
        "feature_missing_fraction",
    ] + [c for c in FEATURE_COLUMNS if c in false_negatives]
    false_negatives = false_negatives[trace_columns].sort_values(
        "absolute_error_mg_l", ascending=False
    )
    extreme_cases = low[trace_columns].sort_values(
        "absolute_error_mg_l", ascending=False
    ).head(30)

    _write_csv(metrics, output / "LOW_DO_METRICS.csv")
    _write_csv(site_table, output / "LOW_DO_SITE_ANALYSIS.csv")
    _write_csv(uncertainty, output / "LOW_DO_UNCERTAINTY.csv")
    _write_csv(by_concentration, output / "LOW_DO_CONCENTRATION_BINS.csv")
    _write_csv(by_year, output / "LOW_DO_YEAR_ANALYSIS.csv")
    _write_csv(feature_associations, output / "LOW_DO_FEATURE_ASSOCIATIONS.csv")
    _write_csv(missingness, output / "LOW_DO_MISSINGNESS_ANALYSIS.csv")
    _write_csv(false_negatives, output / "LOW_DO_FALSE_NEGATIVES.csv")
    _write_csv(extreme_cases, output / "LOW_DO_EXTREME_CASES.csv")
    _write_csv(repeated_unique, output / "REPEATED_SPLIT_UNIQUE_OBSERVATIONS.csv")
    _write_csv(pd.DataFrame(evidence_rows), output / "EVIDENCE_MANIFEST.csv")
    _make_figures(holdout, site_table, uncertainty, output)

    (output / "LOW_DO_RELIABILITY_REPORT.md").write_text(
        _report(metrics, uncertainty, site_table, by_year, feature_associations),
        encoding="utf-8",
    )
    (output / "LOW_DO_FAILURE_ANALYSIS.md").write_text(
        _failure_report(metrics, site_table), encoding="utf-8"
    )
    run_record = {
        "status": "complete",
        "training_performed": False,
        "threshold_mg_l": LOW_DO_THRESHOLD_MG_L,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "prediction_sources": PREDICTION_SOURCES,
        "outputs": {
            str(path.relative_to(output)): sha256_file(path)
            for path in sorted(output.rglob("*"))
            if path.is_file() and path.name != "RUN_MANIFEST.json"
        },
    }
    (output / "RUN_MANIFEST.json").write_text(
        json.dumps(run_record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository-root", type=Path, default=REPOSITORY_ROOT, help="WaterSense root"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPOSITORY_ROOT / "research_upgrade_v3",
        help="New Phase 2A output directory",
    )
    args = parser.parse_args()
    run(args.repository_root.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
