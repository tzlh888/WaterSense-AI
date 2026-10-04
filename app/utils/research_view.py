"""Read-only presentation of completed full-data research runs."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from .app_helpers import PROJECT_ROOT

RESEARCH_DIR = PROJECT_ROOT / "research_outputs"


def research_available() -> bool:
    """Never display smoke, partial or unfinished runs as release evidence."""
    manifest = RESEARCH_DIR / "manifest.json"
    if not manifest.is_file():
        return False
    metadata = json.loads(manifest.read_text())
    return (metadata.get("status") == "complete" and metadata.get("experiment") == "all"
            and metadata.get("config", {}).get("fast") is False)


def render_research_results() -> None:
    st.header("WaterSense AI — Research results")
    st.caption("Evaluating Spatial and Temporal Generalization in Machine-Learning-Based Dissolved Oxygen Prediction")
    if not research_available():
        st.info("The completed research comparison is not available in this checkout. Historical Phase 4 results remain below.")
        return
    st.write("The same fixed Random Forest and feature pipeline were refitted for random rows, unseen stations, future years, and future years at unseen stations. These research fits do not replace the estimator's saved Phase 4 model.")
    low_path = RESEARCH_DIR / "tables/spatiotemporal_error_by_do_range.csv"
    if low_path.exists():
        low = pd.read_csv(low_path).set_index("do_range").loc["<4"]
        predictions = pd.read_csv(RESEARCH_DIR / "predictions/spatiotemporal.csv.gz",
                                  usecols=["actual", "predicted"])
        low_predictions = predictions[predictions.actual < 4]
        count = int(low_predictions.predicted.gt(low_predictions.actual).sum())
        st.info(f"Low-oxygen reliability: in the spatiotemporal test set, {count} of "
                f"{int(low.sample_count)} observations below 4 mg/L were overpredicted, with MAE "
                f"{low.mae:.4f} mg/L. This small subgroup is a warning signal, not evidence of a "
                "universal systematic bias. Good average performance does not imply uniform reliability.")

    def table(name, columns=None):
        frame = pd.read_csv(RESEARCH_DIR / "tables" / f"{name}.csv")
        st.dataframe(frame if columns is None else frame[columns], hide_index=True, width="stretch")

    def figure(name):
        st.image(str(RESEARCH_DIR / "figures" / f"{name}.png"), width="stretch")

    validation, ablation, errors, reliability, shift = st.tabs(
        ["Validation Strategy", "Feature Ablation", "Error Analysis", "Model Reliability", "Importance and Shift"])
    with validation:
        st.write("Each split answers a different generalization question; their metrics should not be interpreted as directly interchangeable measures of model quality.")
        st.caption("Random rows: familiar-site interpolation-like evaluation. Unseen stations: transfer to excluded monitoring locations. Future years: later observations. Spatiotemporal Holdout: later observations at excluded stations.")
        table("validation_comparison", ["strategy", "mae", "rmse", "r2", "test_rows", "test_stations", "station_overlap"])
        figure("validation_strategy_comparison")
        st.caption("Future years: fit through 2018, reserve 2019–2021 for calibration, test 2022–2024. Test-time chemistry is available: this is later-period estimation, not forecasting unknown future measurements.")
        st.caption("Spatiotemporal Holdout: seed 42 selects 20% of stations observed in both periods; fit other stations through 2021 and test held-out stations in 2022–2024. Zero station overlap; training-only preprocessing. Point predictions only, without interval calibration. The longer training horizon and different station/target populations limit direct comparison with the temporal model.")
        inventory_path = RESEARCH_DIR / "tables/spatiotemporal_station_inventory.csv"
        if inventory_path.exists():
            inventory = pd.read_csv(inventory_path)
            eligible = int(inventory.eligible.sum())
            heldout = int(inventory.held_out.sum())
            historical = int(inventory.eligibility_reason.eq("historical_only").sum())
            st.caption(f"The {eligible} continuing stations are eligible for holdout selection, not the entire "
                       f"training population: {eligible-heldout} remaining continuing stations plus "
                       f"{historical} historical-only stations give {eligible-heldout+historical} training stations.")
        st.warning("This is a retrospective study: the fixed settings were selected previously using grouped data across all years. The historical station holdout was already inspected. Station grouping is not geographic-distance or catchment separation.")
    with ablation:
        table("ablation_results", ["feature_set", "number_of_features", "transformed_features", "mae", "rmse", "r2", "cv_mae_mean", "cv_mae_std"])
        figure("feature_ablation")
        st.caption("Feature sets are ranked by training Group-CV MAE. Fold SD is not a confidence interval. Core and core_date omit missingness and censor flags; full also adds extended chemistry.")
    with errors:
        table("do_range_error", ["do_range", "sample_count", "mae", "rmse", "bias"])
        figure("error_by_do_range")
        figure("predicted_vs_actual")
        figure("error_by_year")
        figure("temporal_mae_by_year")
        figure("station_error_distribution")
        with st.expander("Station reliability and sample counts"):
            table("station_extremes", ["station_code", "rank_group", "sample_count", "mae", "rmse", "mean_actual", "mean_predicted"])
        st.caption("Station ranking uses at least 20 test observations. DO bins are descriptive, not safety categories. Positive bias (actual minus predicted) means underprediction.")
    with reliability:
        table("uncertainty_results")
        figure("uncertainty_coverage")
        st.write("Separate calibration residuals define approximate 90% prediction intervals, not measurement confidence intervals. Coverage and width are measured on different test observations. The station interval uses a separate model fitted without calibration stations; the temporal interval uses the pre-2019 model.")
        st.warning("Repeated measurements and temporal change can violate exchangeability. These empirical intervals are not guaranteed for individual stations or extreme conditions and do not replace direct DO measurement. Their widths are not applied to the app's differently fitted estimator.")
        low_coverage = pd.read_csv(RESEARCH_DIR / "tables/coverage_by_do_station.csv").set_index("do_range")
        if "<4" in low_coverage.index:
            low = low_coverage.loc["<4"]
            st.warning(f"Low-oxygen limitation: station-test interval coverage below 4 mg/L is {low.empirical_coverage:.2%} across {int(low.sample_count)} observations. Overall coverage conceals this weakness.")
        with st.expander("Coverage by observed DO range"):
            table("coverage_by_do_station")
            table("coverage_by_do_temporal")
    with shift:
        figure("feature_importance")
        st.caption("Feature importance reflects predictive association, not causal influence. Correlated features may substitute for one another.")
        figure("distribution_shift")
        table("distribution_shift_contrasts")
        st.caption("Median/IQR and standardized mean differences describe recorded distribution changes. They do not establish causes of prediction errors.")
    st.download_button("Download full research report", (RESEARCH_DIR / "reports/RESEARCH_RESULTS.md").read_text(),
                       file_name="WaterSense_RESEARCH_RESULTS.md", mime="text/markdown")
