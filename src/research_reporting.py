"""Figures and a data-driven Markdown report for the research runner."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .research_config import FEATURE_SETS, GROUP


def markdown_table(frame: pd.DataFrame) -> str:
    """Render Markdown without an optional tabulate dependency."""
    def cell(value):
        if isinstance(value, (float, np.floating)):
            return f"{value:.4f}" if np.isfinite(value) else "—"
        return str(value).replace("|", "\\|")
    lines = ["| " + " | ".join(map(str, frame.columns)) + " |",
             "| " + " | ".join(["---"] * len(frame.columns)) + " |"]
    lines += ["| " + " | ".join(cell(v) for v in row) + " |" for row in frame.itertuples(index=False, name=None)]
    return "\n".join(lines)


def create_figures(runner) -> None:
    """Use all evaluation rows for summaries; only dense scatter plots sample."""
    tables, predictions = runner.tables, runner.predictions
    destination = runner.output / "figures"
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "savefig.dpi": 240})

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(destination / f"{name}.png", bbox_inches="tight")
        plt.close(fig)

    if "validation_comparison" in tables:
        data = tables["validation_comparison"]
        fig, ax = plt.subplots(figsize=(10, 4.5))
        x = np.arange(len(data))
        ax.bar(x - .18, data.mae, .36, label="MAE", color="#176B5B")
        ax.bar(x + .18, data.rmse, .36, label="RMSE", color="#B7791F")
        ax.set(xticks=x, xticklabels=data.strategy.str.replace("Spatiotemporal Holdout", "Spatiotemporal\nHoldout"), ylabel="Error (mg/L)",
               title="Fixed Random Forest: validation strategies", ylim=(0, None))
        ax.legend(); save(fig, "validation_strategy_comparison")
    if "ablation_results" in tables:
        data = tables["ablation_results"]
        fig, ax = plt.subplots(figsize=(8, 4.5))
        x = np.arange(len(data))
        ax.bar(x - .18, data.mae, .36, label="Station holdout", color="#176B5B")
        ax.bar(x + .18, data.cv_mae_mean, .36, yerr=data.cv_mae_std,
               capsize=3, label="Group CV ± fold SD", color="#749AB6")
        ax.set(xticks=x, xticklabels=data.feature_set, ylabel="MAE (mg/L)",
               title="Feature ablation: fixed model parameters", ylim=(0, None))
        ax.legend(); save(fig, "feature_ablation")
    for table, filename, title in (("yearly_error", "error_by_year", "Unseen-station error by year"),
                                   ("temporal_yearly_error", "temporal_mae_by_year", "Future-test error by year")):
        if table not in tables:
            continue
        data = tables[table]
        fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
        axes[0].plot(data.sample_year, data.mae, marker="o", label="MAE", color="#176B5B")
        axes[0].plot(data.sample_year, data.rmse, label="RMSE", color="#B7791F")
        axes[0].set(title=title, ylabel="Error (mg/L)", ylim=(0, None)); axes[0].legend()
        axes[1].bar(data.sample_year, data.sample_count, color="#749AB6")
        axes[1].set(xlabel="Sampling year", ylabel="Test observations", ylim=(0, None))
        save(fig, filename)
    if "do_range_error" in tables:
        data = tables["do_range_error"]
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].bar(data.do_range, data.mae, color="#176B5B")
        axes[0].set(ylabel="MAE (mg/L)", xlabel="Actual DO (mg/L)", ylim=(0, None))
        axes[1].bar(data.do_range, data.bias, color="#B7791F")
        axes[1].axhline(0, color="black", linewidth=.8)
        axes[1].set(ylabel="Mean actual − predicted (mg/L)", xlabel="Actual DO (mg/L)")
        for x, row in enumerate(data.itertuples()):
            axes[0].text(x, row.mae, f"n={row.sample_count:,}", ha="center", va="bottom", fontsize=8)
        axes[0].margins(y=.18)
        fig.suptitle("Station holdout: descriptive DO ranges (not safety categories)")
        save(fig, "error_by_do_range")
    if "grouped" in predictions:
        data = predictions["grouped"]
        sample = data.sample(n=min(len(data), 8000), random_state=runner.config.seed)
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.scatter(sample.actual, sample.predicted, s=5, alpha=.18, color="#176B5B")
        bounds = [min(data.actual.min(), data.predicted.min()), max(data.actual.max(), data.predicted.max())]
        ax.plot(bounds, bounds, "--", color="black", linewidth=1)
        ax.set(xlim=bounds, ylim=bounds, xlabel="Actual DO (mg/L)", ylabel="Predicted DO (mg/L)",
               title=f"Unseen stations: {len(sample):,}-row display sample")
        ax.set_aspect("equal"); save(fig, "predicted_vs_actual")
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.scatter(sample.predicted, sample.residual, s=5, alpha=.2, color="#176B5B")
        ax.axhline(0, linestyle="--", color="black")
        ax.set(xlabel="Predicted DO (mg/L)", ylabel="Actual − predicted (mg/L)", title="Station holdout residuals")
        save(fig, "residual_vs_predicted")
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].hist(data.residual, bins=70, color="#176B5B")
        axes[0].set(xlabel="Actual − predicted (mg/L)", ylabel="Observations")
        axes[1].hist(data.absolute_error, bins=70, color="#B7791F")
        axes[1].set(xlabel="Absolute error (mg/L)", ylabel="Observations")
        fig.suptitle("Station holdout: all residuals (untrimmed)")
        save(fig, "residual_distribution")
    if "station_error" in tables:
        data = tables["station_error"]
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].hist(data[data.ranking_eligible].mae, bins=25, color="#176B5B")
        axes[0].set(xlabel="Station MAE (mg/L)", ylabel="Stations", title=f"Stations with n ≥ {runner.config.minimum_station_samples}")
        axes[1].scatter(data.sample_count, data.mae, c=data.ranking_eligible, cmap="winter", alpha=.7, s=14)
        axes[1].set(xlabel="Test observations at station", ylabel="MAE (mg/L)", title="All test stations")
        save(fig, "station_error_distribution")
    if "feature_importance" in tables:
        data = tables["feature_importance"].head(12).sort_values("mae_increase_mean")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(data.feature, data.mae_increase_mean, xerr=data.mae_increase_std, color="#176B5B")
        ax.axvline(0, color="black", linewidth=.8)
        ax.set(xlabel="MAE increase after permutation (mg/L), ± repeat SD",
               title="Held-out predictive importance (not causation)")
        save(fig, "feature_importance")
    if "uncertainty_results" in tables:
        data = tables["uncertainty_results"]
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].bar(data.experiment, data.empirical_coverage, color="#176B5B")
        axes[0].axhline(runner.config.coverage, linestyle="--", color="black", label="Nominal coverage")
        axes[0].set(ylabel="Empirical coverage", ylim=(0, 1)); axes[0].legend()
        axes[1].bar(data.experiment, data.mean_interval_width, color="#749AB6")
        axes[1].set(ylabel="Mean interval width (mg/L)", ylim=(0, None))
        save(fig, "uncertainty_coverage")
    if "distribution_shift" in tables:
        data = tables["distribution_shift"]
        features = data.feature.unique()
        fig, axes = plt.subplots(2, 3, figsize=(13, 8))
        for ax, feature in zip(axes.flat, features):
            part = data[data.feature == feature]
            for j, row in enumerate(part.itertuples()):
                ax.plot([row.q25, row.q75], [j, j], linewidth=4, color="#749AB6")
                ax.scatter(row.median, j, color="#176B5B", zorder=3)
            ax.set(yticks=range(len(part)), yticklabels=part.partition, title=feature,
                   xlabel="Recorded feature scale: median and IQR")
        save(fig, "distribution_shift")


def write_report(runner, manifest: dict, table_names=None) -> str:
    """Report computed or checksum-verified tables; optionally limit table exports."""
    t, c, d = runner.tables, runner.config, manifest["dataset"]
    lines = ["# WaterSense AI", "",
             "**Evaluating Spatial and Temporal Generalization in Machine-Learning-Based Dissolved Oxygen Prediction**", "",
             "**SMOKE RUN — not research evidence.**" if c.fast else "**Full-data fixed-protocol experiment.**",
             "", "## Research question", "",
             "How well can machine-learning models predict dissolved oxygen and generalize across unseen monitoring stations and future time periods? "
             "Where does the model fail, even when aggregate metrics appear acceptable?",
             "", "## Dataset", "",
             f"NIEA/DAERA public river monitoring: {d['raw_rows']:,} raw observations, {d['raw_columns']} columns, "
             f"{d['raw_stations']:,} original stations; {d['processed_rows']:,} eligible observations from "
             f"{d['processed_stations']:,} stations, {d['first_date']} to {d['last_date']}. "
             f"This run used {manifest['executed_rows']:,} observations.", "",
             "Target: original measured `DO_mg_l_`, renamed `dissolved_oxygen_mg_l` (mg/L). "
             "Rows with missing or qualified targets are excluded by the unchanged cleaning function. "
             "No safety labels or ecological thresholds are inferred.", "",
             "## Methodology and evaluation boundaries", "",
             f"Random Forest: {c.n_estimators} trees, minimum leaf size {c.min_samples_leaf}, "
             f"max_features={c.max_features}, seed={c.seed}. All strategies use these fixed settings. "
             "Median imputation and scaling are fitted only on the respective training partition. "
             "Censor flags pass through unchanged; numeric reporting limits are retained. "
             "Station ID, target qualifiers and location metadata are never predictors.", "",
             "Full inputs: " + ", ".join(f"`{f}`" for f in FEATURE_SETS['full'][0]) + ".", "",
             "Random splitting uses 80%/20% rows. Station splitting uses 80%/20% station groups and reproduces "
             "the historical Phase 4 holdout. Station grouping measures transfer to unseen locations in this network, "
             "not distance-blocked or catchment-disjoint extrapolation. Nearby stations can remain related.", "",
             f"Chronological training ends in {c.train_end_year}; {c.train_end_year+1}–{c.validation_end_year} "
             f"is reserved for calibration; {c.validation_end_year+1} onward is the final future test. "
             "No shuffling or refitting on calibration rows occurs. Chemistry is still measured in the test year: "
             "this evaluates future-period contemporaneous estimation, not a forecast with unknown future inputs.", "",
             "**Retrospective design limitation:** model parameters and the full feature set were previously selected "
             "in Phase 4 using grouped data spanning all years. This study freezes that choice; it does not claim "
             "a historically untouched model-selection process for the future years. Grouped holdout results were "
             "also already inspected in earlier phases. New test results are descriptive re-evaluations, not a "
             "fresh confirmatory external benchmark. No new tuning is performed.", "",
             "## Validation strategies", ""]
    def table(name, columns=None):
        if name in t:
            frame = t[name] if columns is None else t[name][columns]
            lines.extend([markdown_table(frame), ""])
    def figure(name, caption):
        path = runner.output / "figures" / f"{name}.png"
        if path.exists():
            lines.extend([f"![{caption}](../figures/{name}.png)", ""])
    table("validation_comparison", ["strategy", "mae", "rmse", "r2", "train_rows", "test_rows", "train_stations", "test_stations", "station_overlap"])
    if "validation_differences" in t:
        diff = t["validation_differences"].iloc[0]
        lines += [f"Grouped minus random MAE: {diff.group_minus_random_mae:.4f} mg/L "
                  f"({diff.mae_degradation_percent:.2f}% relative change); R² difference: {diff.group_minus_random_r2:.4f}.", "",
                  ("Random splitting appears optimistic in this run. Observations from the same monitoring "
                   "locations occur on both sides, so repeated-site similarity may contribute; this does not "
                   "demonstrate causal leakage." if diff.group_minus_random_mae > 0 else
                   "This run does not show lower random-split MAE. Random splitting should not automatically be "
                   "called optimistic when the measured comparison does not support that claim."), "",
                  "Test populations and training sizes differ. These contrasts do not isolate a causal effect of "
                  "split choice, and one seed does not establish uncertainty across possible partitions.", ""]
    figure("validation_strategy_comparison", "Validation strategy comparison")
    table("temporal_target_distribution")
    table("temporal_yearly_error", ["sample_year", "sample_count", "mae", "rmse", "bias"])
    if "validation_comparison" in t and "Future years" in set(t["validation_comparison"].strategy):
        future = t["validation_comparison"].set_index("strategy").loc["Future years"]
        lines += [f"Future-test MAE is {future.mae:.4f} mg/L with bias {future.bias:.4f} mg/L. "
                  f"{int(future.station_overlap)} of {int(future.test_stations)} test stations also occur in temporal training. "
                  "Better future-test performance would not establish robustness everywhere: station composition, "
                  "target variability and the amount of training data differ from the station-held-out test.", ""]
    figure("temporal_mae_by_year", "Future-year error and counts")
    if "spatiotemporal_validation" in t:
        s = t["spatiotemporal_validation"].iloc[0]
        inventory = t["spatiotemporal_station_inventory"]
        counts = inventory.eligibility_reason.value_counts()
        parts = manifest["splits"]["spatiotemporal"]
        lines += ["## Spatiotemporal Generalization", "",
                  "This point-prediction experiment evaluates simultaneous shift in monitoring location and time period. "
                  "Eligibility requires at least one retained observation through 2021 and at least one in the future period. "
                  "No minimum beyond presence in both periods is imposed: this avoids outcome-driven station filtering, "
                  "but does not ensure precise individual-station estimates. The station inventory records observation counts, "
                  "years represented, first/last year, historical/future counts, eligibility reason and selection for every station.", "",
                  f"There are {int(s.eligible_stations)} eligible continuing stations, "
                  f"{int(counts.get('historical_only', 0))} historical-only stations and "
                  f"{int(counts.get('future_only', 0))} future-only stations. "
                  f"A sorted eligible-station list is partitioned by sklearn train_test_split, seed {int(s.seed)}, "
                  f"test fraction {s.heldout_station_fraction:.0%} (rounded up to {int(s.test_stations)} stations). "
                  "All observations from selected stations are excluded from fitting. Historical-only stations are retained "
                  "on the training side; future-only stations are not eligible for this continuing-station test. "
                  f"The {int(s.eligible_stations)} eligible stations are specifically the holdout-selection population, "
                  f"not the complete training population: {int(s.eligible_stations-s.test_stations)} non-held-out "
                  f"continuing stations plus {int(counts.get('historical_only', 0))} historical-only stations "
                  f"give {int(s.train_stations)} training stations.", "",
                  f"Training: {int(s.train_rows):,} observations / {int(s.train_stations)} stations, "
                  f"{s.train_first_date} to {s.train_last_date}. Test: {int(s.test_rows):,} observations / "
                  f"{int(s.test_stations)} stations, {s.test_first_date} to {s.test_last_date}. "
                  f"Unused held-out historical rows: {parts['unused_heldout_history']['rows']:,}; "
                  f"unused future rows at other stations: {parts['unused_other_future']['rows']:,}. "
                  "All four roles are saved in the split-membership artifact; no discarded rows are hidden.", "",
                  "Station overlap is asserted to be zero; max(train date) < min(test date) is asserted. "
                  "The unchanged 25-feature pipeline fits imputation/scaling only on historical training stations. "
                  "Fixed hyperparameters are reused, without tuning, model selection, feature selection or calibration "
                  "on the new test. Uncertainty intervals are intentionally omitted: this point-only fit uses historical "
                  "data through 2021, whereas the unchanged temporal model trains through 2018 and reserves 2019–2021 "
                  "for calibration. Thus training horizons/sizes differ; this is not a controlled isolation of spatial shift.", ""]
        table("spatiotemporal_validation", ["mae", "rmse", "r2", "median_absolute_error",
                                            "p90_absolute_error", "p95_absolute_error",
                                            "train_target_mean", "test_target_mean",
                                            "train_target_median", "test_target_median",
                                            "train_low_do_fraction", "test_low_do_fraction"])
        comparison = t["validation_comparison"].set_index("strategy")
        if {"Future years", "Unseen stations"}.issubset(comparison.index):
            lines += [f"Spatiotemporal MAE minus future-year MAE: "
                      f"{s.mae-comparison.loc['Future years', 'mae']:+.4f} mg/L; "
                      f"minus unseen-station MAE: {s.mae-comparison.loc['Unseen stations', 'mae']:+.4f} mg/L. "
                      "These measured contrasts describe different test populations, not causal effects of the split.", ""]
        table("validation_target_distribution")
        distributions = t["validation_target_distribution"].set_index("strategy")
        new_distribution = distributions.loc["Spatiotemporal Holdout"]
        grouped_distribution = distributions.loc["Unseen stations"]
        lines += [f"The spatiotemporal test has target SD {new_distribution['std']:.3f} mg/L "
                  f"versus {grouped_distribution['std']:.3f} in the grouped test; "
                  f"{new_distribution['fraction_8–<12']:.2%} versus "
                  f"{grouped_distribution['fraction_8–<12']:.2%} lie in the 8–<12 range. "
                  "This greater concentration in a comparatively low-error range may contribute to lower overall MAE. "
                  f"However, low-DO prevalence is actually higher ({new_distribution['fraction_<4']:.2%} "
                  f"versus {grouped_distribution['fraction_<4']:.2%}), so fewer low-DO cases proportionally "
                  "cannot explain the improvement. These summaries do not isolate the contribution of distribution differences.", ""]
        lines += ["Fractions use the same half-open bins: <4, 4–<8, 8–<12 and ≥12 mg/L. "
                  "These are descriptive ranges, not risk classes. Target mean/median/SD and bin prevalence can "
                  "help assess population difficulty, but do not fully explain differences in performance.", ""]
        table("spatiotemporal_error_by_do_range", ["do_range", "sample_count", "mae", "rmse", "bias", "small_sample"])
        low = t["spatiotemporal_error_by_do_range"].set_index("do_range").loc["<4"]
        if low.sample_count > 0:
            lines += [f"Below 4 mg/L, MAE is {low.mae:.4f} mg/L across {int(low.sample_count)} observations; "
                      f"mean actual-minus-predicted bias is {low.bias:.4f} mg/L. "
                      "Negative bias indicates average overprediction. Low aggregate error must not be read as "
                      "reliable low-oxygen estimation. This small-subgroup finding is a warning signal, "
                      "not evidence of a universal systematic bias.", ""]
            prediction_path = runner.output / "predictions/spatiotemporal.csv.gz"
            if prediction_path.exists():
                observed = pd.read_csv(prediction_path, usecols=["actual", "predicted"])
                observed = observed[observed.actual < 4]
                overpredicted = int(observed.predicted.gt(observed.actual).sum())
                lines += [f"Saved spatiotemporal predictions confirm that {overpredicted} of "
                          f"{len(observed)} observations below 4 mg/L were overpredicted in this test set.", ""]
        lines += [f"Bins with fewer than {c.minimum_station_samples} observations are flagged as small samples "
                  "(a descriptive warning, not a statistical precision guarantee). Empty bins have no error estimate.", ""]
        table("spatiotemporal_shift", ["feature", "train_median", "test_median", "train_iqr", "test_iqr",
                                        "standardized_mean_difference"])
        lines += ["The six features come from the existing grouped-test importance ranking; they are used only "
                  "for descriptive shift summaries, not predictor selection. The model still uses all 25 inputs. "
                  "Standardized mean differences use the existing pooled within-partition SD definition. "
                  "All original comparison scores and predictions were reused from checksum-verified outputs when "
                  "this experiment was added standalone; a fresh all-experiment run computes them normally.", "",
                  "**Limitations:** the randomly held-out subset may not represent all unseen stations. Requiring "
                  "availability in both periods introduces station-selection effects and excludes newly appearing sites. "
                  "Spatial and temporal shifts are not independent; environmental conditions and sampling schedules "
                  "may differ across station groups. One holdout is less stable than repeated grouped evaluation, "
                  "and row-weighted errors emphasize frequently sampled stations. The evidence remains specific to "
                  "Northern Ireland, with the previously disclosed retrospective model-selection limitation. "
                  "Repeated spatiotemporal resampling is future work, not an experiment performed here.", "",
                  "Reproduce only the new experiment with "
                  "`python scripts/run_research_experiments.py --experiment spatiotemporal --output research_runs/spatiotemporal-reproduction`. "
                  "It verifies and reuses the released baseline outputs and fits only one research model.", ""]
    lines += ["## Feature ablation", "",
              "Core is six measured chemistry variables with median imputation and no missingness/censor flags. "
              "Core+indicators adds the ten existing core censor flags and training-learned missingness indicators. "
              "Core+date adds two cyclical day-of-year features without indicators. Full adds extended chemistry, "
              "all fourteen censor flags, date context and missingness indicators. Full therefore changes multiple "
              "components; these four configurations are not a complete factorial experiment.", "",
              f"The same station holdout and {c.cv_folds} grouped training folds are used for every configuration. "
              "Input and transformed feature counts are both reported. Fold SD is descriptive variation, not a confidence interval. "
              "The best configuration is ranked by training Group-CV MAE, not by final-test MAE.", ""]
    table("ablation_results", ["feature_set", "number_of_features", "transformed_features", "mae", "rmse", "r2", "cv_mae_mean", "cv_mae_std"])
    if "ablation_results" in t:
        ranked = t["ablation_results"].sort_values("cv_mae_mean")
        ablations = t["ablation_results"].set_index("feature_set")
        lines += [f"Lowest Group-CV MAE: **{ranked.iloc[0].feature_set}**, "
                  f"{ranked.iloc[0].cv_mae_mean:.4f} ± {ranked.iloc[0].cv_mae_std:.4f} mg/L. "
                  "Small differences should not be treated as established improvements without repeat splits or paired uncertainty estimates.", ""]
        lines += [f"Compared with core-only Group-CV MAE, indicators reduce MAE by "
                  f"{ablations.loc['core', 'cv_mae_mean']-ablations.loc['core_indicators', 'cv_mae_mean']:.4f} mg/L; "
                  f"cyclical date features reduce it by "
                  f"{ablations.loc['core', 'cv_mae_mean']-ablations.loc['core_date', 'cv_mae_mean']:.4f} mg/L. "
                  "These are descriptive differences under the fixed protocol.", ""]
    figure("feature_ablation", "Ablation and training Group CV")
    lines += ["## Error analysis", "", "Residual = actual − predicted; positive bias means underprediction. "
              "DO bins (<4, 4–<8, 8–<12, ≥12 mg/L) are descriptive concentration ranges, not safety standards.", ""]
    table("do_range_error", ["do_range", "sample_count", "mae", "rmse", "bias"])
    table("error_summary", ["sample_count", "mae", "median_absolute_error", "p90_absolute_error", "p95_absolute_error", "bias"])
    if "do_range_error" in t:
        errors = t["do_range_error"].set_index("do_range")
        if {"<4", "8–<12", "≥12"}.issubset(errors.index):
            lines += [f"MAE below 4 mg/L is {errors.loc['<4', 'mae']:.3f} mg/L "
                      f"(n={int(errors.loc['<4', 'sample_count'])}), compared with "
                      f"{errors.loc['8–<12', 'mae']:.3f} in the 8–<12 range and "
                      f"{errors.loc['≥12', 'mae']:.3f} at ≥12. The low/high biases are "
                      f"{errors.loc['<4', 'bias']:.3f} and {errors.loc['≥12', 'bias']:.3f} mg/L respectively. "
                      "The signs identify overprediction or underprediction without assigning a cause.", ""]
    figure("error_by_do_range", "Error by dissolved oxygen range")
    figure("predicted_vs_actual", "Predicted versus actual with equal axes")
    figure("residual_vs_predicted", "Residual versus predicted")
    figure("residual_distribution", "Residual and absolute error distributions")
    figure("error_by_year", "Station holdout errors across years")
    lines += [f"Station ranking requires n ≥ {c.minimum_station_samples}; all stations remain in the overall evaluation. "
              "This is a descriptive minimum, not proof that 20 observations yield a stable estimate. "
              "Equal-weight station correlations below are exploratory associations, not explanations. "
              "Unusual-feature fraction uses training-only 1st/99th percentile limits among observed measurements. "
              "Largest-year fraction measures temporal concentration; recent fraction uses years ≥2019.", ""]
    table("station_extremes", [GROUP, "rank_group", "sample_count", "mae", "rmse", "mean_actual", "mean_predicted"])
    table("station_associations")
    figure("station_error_distribution", "Station error distribution and sample sizes")
    lines += ["## Uncertainty and reliability", "",
              "Absolute residuals on a separate calibration set define radius q at order statistic "
              "ceil((n+1) × 0.9). Intervals are prediction ± q without clipping. Station calibration reserves "
              "20% of the training stations and fits a separate model on the remaining stations. Its test stations "
              "are the unchanged grouped holdout. Temporal calibration uses 2019–2021 with the pre-2019 model. "
              "Neither interval radius uses final-test residuals. Test coverage is evaluated only after calibration.", "",
              "This is a conformal-style residual baseline. Ordinary marginal coverage guarantees require "
              "exchangeability, which repeated measurements and temporal shift can violate. Coverage here is "
              "empirical, observation-weighted and not guaranteed for each station or target range. "
              "The interval quantifies empirical predictive uncertainty under the available validation distribution. "
              "It is not a substitute for direct dissolved-oxygen measurement. See "
              "[Angelopoulos & Bates](https://arxiv.org/abs/2107.07511).", ""]
    table("uncertainty_results")
    table("coverage_by_do_station")
    table("coverage_by_do_temporal")
    for key in ("station", "temporal"):
        name = f"coverage_by_do_{key}"
        if name in t and "<4" in set(t[name].do_range):
            low = t[name].set_index("do_range").loc["<4"]
            lines += [f"**{key.capitalize()} low-DO coverage:** {low.empirical_coverage:.1%} "
                      f"among {int(low.sample_count)} observations below 4 mg/L. "
                      "Overall coverage must not be interpreted as reliable coverage of low-oxygen cases.", ""]
    figure("uncertainty_coverage", "Empirical interval coverage and width")
    lines += ["These intervals belong to the separately fitted research models. The app retains its original "
              "Phase 4 point-estimate artifact, so research radii are not attached to individual app predictions.", "",
              "## Feature importance and distribution shift", "",
              f"Permutation importance uses {c.permutation_repeats} repeats on up to {c.permutation_rows:,} "
              "fixed-seed held-out observations, with the fitted pipeline held fixed. Error bars are repeat SD, "
              "not inferential confidence intervals. Correlated predictors can share/substitute importance. "
              "Feature importance reflects predictive association, not causal influence.", ""]
    if "feature_importance" in t:
        lines += [markdown_table(t["feature_importance"].head(12)), ""]
    figure("feature_importance", "Permutation importance")
    lines += ["Six top-ranked inputs are described using median, IQR, mean, SD and missing fraction in both "
              "training populations and their respective tests. Standardized mean differences use pooled "
              "within-partition SD. These summaries describe shift; they do not establish why errors change. "
              "Changing environmental conditions, monitoring practice, station composition and covariate shift "
              "are hypotheses to investigate, not demonstrated causes.", ""]
    table("distribution_shift_contrasts")
    figure("distribution_shift", "Feature medians and interquartile ranges")
    if "spatiotemporal_validation" in t and "validation_comparison" in t:
        values = t["validation_comparison"].set_index("strategy")
        lines += ["## Research Conclusion", "",
                  f"Aggregate MAE ranged from {values.mae.min():.4f} to {values.mae.max():.4f} mg/L "
                  "across the reported validation settings. The results are broadly comparable in scale, "
                  "but this is not a statistical equivalence claim. Each split answers a different generalization "
                  "question; their metrics should not be interpreted as directly interchangeable measures of model quality. "
                  "The random-versus-grouped comparison above does not justify assuming random-split optimism.", "",
                  "Temporal and spatiotemporal holdouts produced relatively low aggregate errors in these particular "
                  "test populations. Different target distributions, station composition and training horizons prevent "
                  "attributing the differences to split design alone or claiming universal robustness. "
                  "Rare low-oxygen observations remained substantially harder; the small spatiotemporal subgroup "
                  "is a warning signal rather than definitive evidence of general systematic bias.", "",
                  "The separately calibrated research prediction intervals also had substantially poorer low-DO "
                  "coverage than aggregate coverage. They describe predictive uncertainty, not measurement "
                  "confidence intervals, and do not replace field measurement. Together, these findings illustrate "
                  "why aggregate metrics alone are insufficient for assessing environmental prediction reliability. "
                  "Understanding where the model fails is at least as important as improving a headline score.", ""]
    lines += ["## Limitations", "",
              "- Prediction does not replace field measurements or laboratory analysis.\n"
              "- The observational dataset cannot identify causal environmental mechanisms.\n"
              "- The geographic scope is the Northern Ireland monitoring network; station separation is not catchment separation.\n"
              "- Distribution shift can degrade performance; validation scores do not guarantee universal performance.\n"
              "- Water temperature and flow/discharge are absent from the current predictors.\n"
              "- Sampling is irregular and historical monitoring practices may change over time.\n"
              "- Interval validity depends on calibration assumptions; overall coverage can conceal extreme-value failures.\n"
              "- Fixed parameters were selected previously; retrospective comparisons are not independent prospective validation.\n"
              "- A single random/group split and row-weighted metrics can underrepresent small stations.", "",
              "## Future work", "",
              "Investigate rainfall, water temperature, discharge, weather and catchment characteristics through "
              "new data linkage; they are not claimed to be current inputs. Evaluate external catchments and "
              "geographic distance blocks, repeated grouped splits, time-respecting model selection, group-aware "
              "calibration, and distribution-shift detection.", "",
              "## Reproducibility", "",
              "Run `python scripts/run_research_experiments.py --experiment all --output research_runs/reproduction` "
              "with a new or empty output directory. "
              "The manifest records configuration, source/data hashes, versions, split counts and output checksums. "
              "Compressed predictions include source row IDs and all split memberships. "
              "Original model and Phase 3/4 result hashes are verified unchanged. "
              "Partial experiments and smoke runs use separate directories and do not replace this full report.", ""]
    report = "\n".join(lines)
    (runner.output / "reports/RESEARCH_RESULTS.md").write_text(report)
    for name, frame in t.items():
        if table_names is None or name in table_names:
            (runner.output / "reports" / f"{name}.md").write_text(markdown_table(frame) + "\n")
    return report


def refresh_report(output) -> None:
    """Regenerate prose from verified saved results without refitting models."""
    import json
    from types import SimpleNamespace
    from pathlib import Path
    from .research_config import ResearchConfig
    from .research_experiments import sha256

    output = Path(output)
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("status") != "complete":
        raise ValueError("Only a completed experiment can regenerate its report.")
    for name, expected in manifest["output_hashes"].items():
        if sha256(output / name) != expected:
            raise ValueError(f"Stored output checksum mismatch: {name}")
    config = ResearchConfig(**{key: value for key, value in manifest["config"].items()
                               if key in ResearchConfig.__dataclass_fields__})
    runner = SimpleNamespace(output=output, config=config, tables={
        name: pd.read_csv(output / "tables" / f"{name}.csv")
        for name in manifest["generated_tables"]})
    write_report(runner, manifest)
    manifest["report_source_sha256"] = sha256(Path(__file__))
    manifest["output_hashes"] = {str(p.relative_to(output)): sha256(p) for p in sorted(output.rglob("*"))
                                 if p.is_file() and p != manifest_path}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
