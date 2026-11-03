#!/usr/bin/env python3
"""Recompute frozen evidence and generate the WaterSense portfolio extension."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.portfolio_analysis import (  # noqa: E402
    PERIOD_LABELS,
    break_even_ratio,
    confusion_counts,
    cost_scenarios,
    regression_summary,
    sha256_file,
    station_concentration,
    temporal_summary,
    verify_regression_identity,
)


REGRESSION_PATH = ROOT / "research_upgrade_v3/experiment1_weighted_regression/OUTER_CV_PREDICTIONS.csv.gz"
CLASSIFIER_PATH = ROOT / "research_upgrade_v4_candidate/WATERSENSE_CLASSIFIER_OOF_PREDICTIONS.csv.gz"
EXPECTED_HASHES = {
    REGRESSION_PATH: "b779effb1bb1f2d8333d7818b606d566ee52af7a199c8368ec674e2404767697",
    CLASSIFIER_PATH: "a96e0dac77ff7b94e73cfa52f6acf33587a04eb80c85095e433c1aa6d42e324b",
}
RESEARCH_DIR = ROOT / "research_extension"
FIGURE_DIR = ROOT / "figures"
AUDIT_DIR = ROOT / "audits"


def verify_hashes() -> dict[str, str]:
    observed = {str(path.relative_to(ROOT)): sha256_file(path) for path in EXPECTED_HASHES}
    for path, expected in EXPECTED_HASHES.items():
        if observed[str(path.relative_to(ROOT))] != expected:
            raise ValueError(f"Frozen evidence hash mismatch: {path.relative_to(ROOT)}")
    return observed


def load_and_verify() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    hashes = verify_hashes()
    regression = pd.read_csv(REGRESSION_PATH)
    verify_regression_identity(regression)
    classifier = pd.read_csv(CLASSIFIER_PATH)
    baseline = regression.loc[regression["variant"].eq("baseline")].copy()
    left = baseline[
        ["source_object_id", "station_code", "sample_date", "outer_fold", "actual_do_mg_l"]
    ].sort_values("source_object_id").reset_index(drop=True)
    right = classifier[
        ["source_object_id", "station_code", "sample_date", "outer_fold", "dissolved_oxygen_mg_l"]
    ].sort_values("source_object_id").reset_index(drop=True)
    if len(left) != 119_690 or len(classifier) != 119_690:
        raise ValueError("Unexpected frozen development row count")
    for column in ["source_object_id", "station_code", "sample_date", "outer_fold"]:
        if not left[column].equals(right[column]):
            raise ValueError(f"V3/V4 identity mismatch in {column}")
    if not np.allclose(left["actual_do_mg_l"], right["dissolved_oxygen_mg_l"]):
        raise ValueError("V3/V4 target mismatch")
    if classifier["source_object_id"].duplicated().any():
        raise ValueError("Duplicate classifier source identity")
    classifier_actual = classifier["dissolved_oxygen_mg_l"] < 4
    if not classifier_actual.astype(int).equals(classifier["actual_low_do"].astype(int)):
        raise ValueError("Classifier low-DO labels do not match strict threshold")
    return regression, classifier, hashes


def make_figures(
    concentration: pd.DataFrame,
    temporal: pd.DataFrame,
    model_counts: dict[str, dict[str, int]],
) -> None:
    FIGURE_DIR.mkdir(exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    x = np.arange(1, len(concentration) + 1) / len(concentration)
    ax.plot(x, concentration["cumulative_event_share"], color="#0B7285", linewidth=2.5)
    ax.plot([0, 1], [0, 1], linestyle="--", color="#868E96", linewidth=1)
    ax.set(
        xlabel="Share of low-DO stations, ordered by event count",
        ylabel="Cumulative share of measured low-DO events",
        title="Low-oxygen observations are concentrated across stations",
        xlim=(0, 1),
        ylim=(0, 1),
    )
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "low_do_station_concentration.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4), sharey=False)
    colors = {"baseline": "#495057", "weighted": "#0B7285"}
    for variant, data in temporal.groupby("variant", sort=False):
        ordered = data.set_index("period").loc[PERIOD_LABELS]
        axes[0].plot(
            PERIOD_LABELS,
            ordered["pooled_mae_mg_l"],
            marker="o",
            linewidth=2,
            label=variant.capitalize(),
            color=colors[variant],
        )
        axes[1].plot(
            PERIOD_LABELS,
            ordered["balanced_station_macro_mae_mg_l"],
            marker="o",
            linewidth=2,
            label=variant.capitalize(),
            color=colors[variant],
        )
    axes[0].set_title("All observations in each period")
    axes[0].set_ylabel("MAE (mg/L)")
    axes[1].set_title("Same 173 stations across periods")
    for ax in axes:
        ax.set_xlabel("Measurement period")
        ax.tick_params(axis="x", rotation=25)
    axes[0].legend(frameon=False)
    fig.suptitle("Descriptive time slices—not prospective temporal validation", y=1.03)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "temporal_robustness.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    ratios = np.logspace(-1, 2, 300)
    fig, ax = plt.subplots(figsize=(7.4, 4.7))
    palette = {
        "V3 baseline": "#495057",
        "V3 selected procedure": "#0B7285",
        "V4 classifier": "#E67700",
    }
    for model, counts in model_counts.items():
        costs = ratios * counts["fn"] + counts["fp"]
        ax.plot(ratios, costs, label=model, color=palette[model], linewidth=2)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set(
        xlabel="Hypothetical false-negative / false-positive cost ratio",
        ylabel="Relative cost = ratio × FN + FP",
        title="Preferred rule depends on an explicit error-cost assumption",
    )
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "decision_tradeoffs.png", dpi=180)
    plt.close(fig)


def write_report(
    regression_metrics: dict[str, dict[str, float | int]],
    concentration_summary: dict[str, float | int],
    temporal: pd.DataFrame,
    model_counts: dict[str, dict[str, int]],
    breakpoints: dict[str, float],
) -> None:
    baseline = regression_metrics["baseline"]
    weighted = regression_metrics["weighted"]
    early = temporal.loc[
        temporal["variant"].eq("baseline") & temporal["period"].eq("1990–1999")
    ].iloc[0]
    recent = temporal.loc[
        temporal["variant"].eq("baseline") & temporal["period"].eq("2020–2024")
    ].iloc[0]
    report = f"""# Station reliability, time slices, and decision trade-offs

## Status

**EXPLORATORY / DEVELOPMENT-ONLY.** This report recomputes frozen V3 and V4
outer out-of-fold predictions. It does not train a model or provide independent
external validation.

## Reconstruction result

Both V3 variants contain {baseline['rows']:,} unique observations from
{baseline['stations']} stations, with identical identities, targets, dates, and
outer folds. Each station occurs in exactly one outer fold. The strict low-DO
definition is measured `DO < 4 mg/L`.

| Quantity | V3 baseline | V3 selected procedure |
|---|---:|---:|
| Overall MAE (mg/L) | {baseline['mae_mg_l']:.4f} | {weighted['mae_mg_l']:.4f} |
| Low-DO MAE (mg/L) | {baseline['low_do_mae_mg_l']:.4f} | {weighted['low_do_mae_mg_l']:.4f} |
| Recall | {baseline['recall']:.4f} | {weighted['recall']:.4f} |
| Precision | {baseline['precision']:.4f} | {weighted['precision']:.4f} |
| False negatives | {baseline['fn']} | {weighted['fn']} |
| False positives | {baseline['fp']} | {weighted['fp']} |

The procedure improves the rare-event objectives but worsens overall MAE and
false alarms. It must not be summarized as an unqualified model improvement.

## Finding 1 — effective rare-event evidence is much smaller than 758 rows

The 758 measured low-DO observations occur at only
{concentration_summary['stations_with_low_do']} of 672 development stations.
{concentration_summary['stations_with_one_event']} stations contain exactly one
event. The largest station supplies {concentration_summary['top_1_share']:.1%}
of all events; the largest five supply {concentration_summary['top_5_share']:.1%},
and the largest ten {concentration_summary['top_10_share']:.1%}. The event-share
Herfindahl index is {concentration_summary['hhi']:.4f}, equivalent to only
{concentration_summary['effective_station_count']:.1f} equally represented
stations.

This does not invalidate the row-level metrics. It changes their interpretation:
758 dependent observations are not 758 independent replications, and station-
clustered uncertainty is essential.

![Cumulative low-DO event concentration](../figures/low_do_station_concentration.png)

## Finding 2 — time-band improvement is descriptive, not forecasting evidence

Baseline pooled MAE is {early['pooled_mae_mg_l']:.3f} mg/L in 1990–1999 and
{recent['pooled_mae_mg_l']:.3f} mg/L in 2020–2024. The same direction appears
when macro-averaging the {int(recent['balanced_stations'])} stations represented
in all four periods ({early['balanced_station_macro_mae_mg_l']:.3f} to
{recent['balanced_station_macro_mae_mg_l']:.3f} mg/L). That sensitivity check
shows that changing site membership alone does not explain the pattern.

It still cannot identify a temporal cause: the models were trained using other
rows from all eras, monitoring practice and case mix can change, and no 2025+
period was held prospectively untouched.

![Time-slice sensitivity analysis](../figures/temporal_robustness.png)

## Finding 3 — model preference is a decision problem

With hypothetical cost `r × FN + FP`, the V3 selected procedure becomes less
costly than the V3 baseline only when a false negative is valued above
**{breakpoints['weighted_vs_baseline']:.3f}** false positives. The V4 classifier
becomes less costly than V3 selected only above **{breakpoints['classifier_vs_weighted']:.3f}**,
and less costly than the V3 baseline only above **{breakpoints['classifier_vs_baseline']:.3f}**.

| Rule | FN | FP |
|---|---:|---:|
| V3 baseline | {model_counts['V3 baseline']['fn']} | {model_counts['V3 baseline']['fp']} |
| V3 selected procedure | {model_counts['V3 selected procedure']['fn']} | {model_counts['V3 selected procedure']['fp']} |
| V4 classifier | {model_counts['V4 classifier']['fn']} | {model_counts['V4 classifier']['fp']} |

These breakpoints are arithmetic consequences of the saved development
confusion matrices. They are not recommended operational costs.

![Hypothetical decision-cost curves](../figures/decision_tradeoffs.png)

## Scientific conclusion

The strongest defensible contribution is a reliability result, not a deployment
claim: group-aware development evidence shows that rare low-oxygen detection can
be improved only by accepting measurable costs elsewhere, and the apparent
amount of rare-event evidence shrinks substantially after respecting its station
concentration. Independent external confirmation and an application-defined
cost policy remain necessary.
"""
    (RESEARCH_DIR / "RELIABILITY_AND_ROBUSTNESS_REPORT.md").write_text(report, encoding="utf-8")


def main() -> None:
    RESEARCH_DIR.mkdir(exist_ok=True)
    AUDIT_DIR.mkdir(exist_ok=True)
    regression, classifier, input_hashes = load_and_verify()
    regression_metrics = {
        variant: regression_summary(group)
        for variant, group in regression.groupby("variant", sort=False)
    }
    concentration, concentration_summary = station_concentration(regression)
    temporal, temporal_meta = temporal_summary(regression)
    classifier_counts = confusion_counts(
        classifier["actual_low_do"], classifier["predicted_low_do"]
    )
    model_counts = {
        "V3 baseline": {key: int(regression_metrics["baseline"][key]) for key in ["fn", "fp"]},
        "V3 selected procedure": {key: int(regression_metrics["weighted"][key]) for key in ["fn", "fp"]},
        "V4 classifier": {key: classifier_counts[key] for key in ["fn", "fp"]},
    }
    breakpoints = {
        "weighted_vs_baseline": break_even_ratio(
            model_counts["V3 baseline"], model_counts["V3 selected procedure"]
        ),
        "classifier_vs_weighted": break_even_ratio(
            model_counts["V3 selected procedure"], model_counts["V4 classifier"]
        ),
        "classifier_vs_baseline": break_even_ratio(
            model_counts["V3 baseline"], model_counts["V4 classifier"]
        ),
    }
    concentration.to_csv(RESEARCH_DIR / "station_low_do_concentration.csv", index=False)
    temporal.to_csv(RESEARCH_DIR / "temporal_robustness.csv", index=False)
    cost_scenarios(model_counts).to_csv(RESEARCH_DIR / "decision_cost_scenarios.csv", index=False)
    make_figures(concentration, temporal, model_counts)
    write_report(regression_metrics, concentration_summary, temporal, model_counts, breakpoints)
    verification = {
        "status": "PASS",
        "analysis_class": "EXPLORATORY_DEVELOPMENT_ONLY",
        "training_performed": False,
        "input_hashes": input_hashes,
        "identity_checks": {
            "v3_variant_membership_identical": True,
            "v3_station_outer_fold_disjoint": True,
            "v3_v4_membership_identical": True,
            "strict_low_do_definition_verified": True,
        },
        "regression_metrics": regression_metrics,
        "classifier_confusion": classifier_counts,
        "station_concentration": concentration_summary,
        "temporal": temporal_meta,
        "break_even_cost_ratios": breakpoints,
    }
    (AUDIT_DIR / "verification_summary.json").write_text(
        json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    outputs = [
        RESEARCH_DIR / "station_low_do_concentration.csv",
        RESEARCH_DIR / "temporal_robustness.csv",
        RESEARCH_DIR / "decision_cost_scenarios.csv",
        RESEARCH_DIR / "RELIABILITY_AND_ROBUSTNESS_REPORT.md",
        FIGURE_DIR / "low_do_station_concentration.png",
        FIGURE_DIR / "temporal_robustness.png",
        FIGURE_DIR / "decision_tradeoffs.png",
        AUDIT_DIR / "verification_summary.json",
    ]
    manifest = {
        "schema": "watersense-portfolio-extension-v1",
        "generated_from_frozen_predictions": True,
        "files": {str(path.relative_to(ROOT)): sha256_file(path) for path in outputs},
    }
    (RESEARCH_DIR / "ARTIFACT_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": "PASS", "outputs": len(outputs) + 1}, sort_keys=True))


if __name__ == "__main__":
    main()
