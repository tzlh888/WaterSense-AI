"""Interactive dissolved-oxygen estimator using the immutable Phase 4 pipeline."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

import numpy as np
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from utils.app_helpers import configure_page, humanise_feature, render_disclaimer, render_page_intro
from utils.data_loader import load_app_table, load_result_table, load_training_reference_data
from utils.model_input import (
    MEASUREMENT_FIELDS,
    QUALIFIER_LABELS,
    build_model_input,
    format_percentile_positions,
    input_percentile_positions,
    training_range_warnings,
)
from utils.model_loader import load_cached_model


configure_page("Dissolved Oxygen Estimator")
render_page_intro(
    "Verified Phase 4 pipeline",
    "Dissolved Oxygen Estimator",
    "Enter physicochemical measurements from a river-water sample. The model estimates dissolved oxygen for the same sampling context.",
)
render_disclaimer()

try:
    artifact = load_cached_model()
    training = load_training_reference_data()
    example = load_app_table("example_input.csv").iloc[0]
except (FileNotFoundError, ValueError) as exc:
    st.error(str(exc))
    st.stop()

medians = training[[field["feature"] for field in MEASUREMENT_FIELDS]].median()

if "sampling_date" not in st.session_state:
    st.session_state["sampling_date"] = date(2024, 6, 15)
for field in MEASUREMENT_FIELDS:
    feature = field["feature"]
    st.session_state.setdefault(f"value_{feature}", float(medians[feature]))
    st.session_state.setdefault(f"missing_{feature}", False)
    if len(field["qualifiers"]) > 1:
        st.session_state.setdefault(f"qualifier_{feature}", "exact")

if st.button(
    "Load example monitoring record",
    help="Loads one complete, uncensored observation from the verified training data.",
):
    st.session_state["sampling_date"] = example["sample_date"].date()
    for field in MEASUREMENT_FIELDS:
        feature = field["feature"]
        st.session_state[f"value_{feature}"] = float(example[feature])
        st.session_state[f"missing_{feature}"] = False
        if len(field["qualifiers"]) > 1:
            st.session_state[f"qualifier_{feature}"] = "exact"
    st.toast("Example monitoring record loaded.")
st.caption("The example is a real complete observation from the model-training stations; it is not labelled as safe or unsafe.")

st.markdown(
    '<div class="ws-note"><strong>Missing measurements.</strong> The fitted pipeline can impute unavailable values because missingness was represented during training. Predictions with incomplete measurements should still be interpreted cautiously.</div>',
    unsafe_allow_html=True,
)

with st.form("estimator_form"):
    st.subheader("Sampling context")
    sampling_date = st.date_input(
        "Sampling date",
        key="sampling_date",
        help="The date is converted into the same cyclical day-of-year features used during Phase 4.",
    )
    values: dict[str, float | None] = {}
    qualifiers: dict[str, str] = {}

    def render_fields(fields: tuple[dict, ...]) -> None:
        input_columns = st.columns(2)
        for index, field in enumerate(fields):
            feature = field["feature"]
            with input_columns[index % 2]:
                st.markdown(f"**{field['label']}** · {field['unit']}")
                st.caption(field["description"])
                unavailable = st.checkbox("Measurement unavailable", key=f"missing_{feature}")
                value = st.number_input(
                    f"Reported value ({field['unit']})",
                    format="%.4f",
                    disabled=unavailable,
                    key=f"value_{feature}",
                )
                values[feature] = None if unavailable else float(value)
                if len(field["qualifiers"]) > 1 and not unavailable:
                    qualifier = st.selectbox(
                        "Reporting qualifier",
                        options=field["qualifiers"],
                        format_func=lambda option: QUALIFIER_LABELS[option],
                        key=f"qualifier_{feature}",
                    )
                else:
                    qualifier = "exact"
                qualifiers[feature] = qualifier
                if qualifier != "exact":
                    st.caption("The number is retained as the reported limit, not the unknown true concentration.")

    st.subheader("Core chemistry")
    render_fields(MEASUREMENT_FIELDS[:6])
    st.subheader("Additional chemistry")
    render_fields(MEASUREMENT_FIELDS[6:])
    submitted = st.form_submit_button("Estimate Dissolved Oxygen", type="primary", width="stretch")

with st.expander("Why does the model ask for the date?"):
    st.write(
        "Seasonal context improved station-level validation. The date is converted to cyclical day-of-year sine and cosine values so December and January remain close in representation. This is contemporaneous context, not future forecasting."
    )

with st.expander("What does ‘below reporting limit’ mean?"):
    st.write(
        "A result such as <0.04 does not mean the concentration is exactly 0.04. It means the laboratory reported it below that limit. The model receives both the reported numeric limit and a qualifier flag; no half-limit substitution is performed."
    )

if submitted:
    try:
        model_row = build_model_input(values, qualifiers, sampling_date, artifact["feature_columns"])
        prediction = float(artifact["pipeline"].predict(model_row)[0])
        if not np.isfinite(prediction):
            raise ValueError("The model returned a non-finite prediction.")
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    st.divider()
    st.subheader("Estimated dissolved oxygen")
    st.metric("Model estimate", f"{prediction:.2f} mg/L")
    st.caption("This is a model estimate for the entered sampling context, not a laboratory result or safety determination.")

    range_warnings = training_range_warnings(model_row, training)
    if range_warnings:
        if len(range_warnings) == 1:
            st.warning("One entry is outside the range observed in the training dataset. This extrapolation should be interpreted with additional caution.")
        else:
            st.warning(f"{len(range_warnings)} entries are outside the ranges observed in the training dataset. Multiple extrapolations make this estimate especially uncertain.")
        for warning in range_warnings:
            st.write(
                f"- **{humanise_feature(warning['feature'])}:** {warning['value']:.4g}; observed training range {warning['minimum']:.4g}–{warning['maximum']:.4g}."
            )
    if model_row.isna().any(axis=None):
        st.info("At least one measurement was unavailable. The pipeline used medians learned from training data and its learned missingness representation.")

    st.warning(
        "The model was less accurate for unusually low and unusually high observed dissolved oxygen and tended to predict those observations closer to the middle of the distribution. A model estimate cannot reveal whether the unknown true DO is extreme."
    )

    st.header("Model Context")
    context = st.columns(3)
    context[0].metric("Station-grouped holdout MAE", "0.831 mg/L", help="31,341 observations from 168 stations absent from training.")
    context[1].metric("Group-CV MAE", "0.880 ± 0.035 mg/L", help="Five station-grouped folds inside training.")
    context[2].metric("Holdout R²", "0.539", help="Proportion of target variation explained relative to the holdout mean reference.")

    percentiles = load_result_table("error_percentiles.csv")
    percentiles = percentiles[percentiles["scope"] == "all_group_cv_validation_rows"].copy()
    percentiles["Validation observations"] = percentiles["percentile"].map(lambda value: f"{value:.0%}")
    percentiles["Absolute error at or below"] = percentiles["absolute_error_mg_l"].map(lambda value: f"{value:.3f} mg/L")
    st.subheader("Empirical validation-error summary")
    st.dataframe(percentiles[["Validation observations", "Absolute error at or below"]], hide_index=True, width="stretch")
    st.caption(
        "Across group-aware validation predictions, the stated proportion of absolute errors was approximately at or below each value. This is an empirical validation summary, not an individual confidence or prediction interval."
    )

    with st.expander("Where do my inputs sit in the training data?", expanded=False):
        positions = format_percentile_positions(
            input_percentile_positions(model_row, training)
        )
        if positions.empty:
            st.info("Training-distribution position is unavailable for the current inputs.")
        else:
            st.dataframe(positions, hide_index=True, width="stretch")
            st.caption("Percentiles describe rarity relative to recorded training measurements. Unusual does not mean unsafe or environmentally invalid.")

    st.header("How does the model use information?")
    importance = load_result_table("permutation_importance_phase4.csv").head(12).copy()
    importance["Feature"] = importance["input_feature"].map(humanise_feature)
    figure = px.bar(
        importance.sort_values("mae_increase_mean"),
        x="mae_increase_mean",
        y="Feature",
        orientation="h",
        error_x="mae_increase_std",
        labels={"mae_increase_mean": "Increase in held-out MAE after permutation (mg/L)"},
        color_discrete_sequence=["#176B5B"],
    )
    st.plotly_chart(figure, width="stretch")
    st.write(
        "Permutation importance measures how much held-out error increases when one feature’s information is disrupted. It is a global model result and does not explain this individual prediction. Importance describes predictive usefulness, not causality."
    )
