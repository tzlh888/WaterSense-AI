"""WaterSense AI landing page."""

from __future__ import annotations

from utils.app_helpers import configure_page, render_disclaimer, render_page_intro

import streamlit as st


configure_page("Home")
render_page_intro(
    "Educational environmental machine learning",
    "WaterSense AI",
    "Evaluating Spatial and Temporal Generalization in Machine-Learning-Based Dissolved Oxygen Prediction",
)
render_disclaimer()

metric_items = [
    ("Raw observations", "178,680", "Rows in the official export."),
    ("Time coverage", "1990–2024", "Observed sampling years."),
    ("Raw stations", "1,311", "Unique station codes in the raw export."),
    ("Holdout MAE", "0.831 mg/L", "Measured on 168 stations absent from training."),
]
for start in (0, 2):
    metric_columns = st.columns(2)
    for column, (label, value, help_text) in zip(metric_columns, metric_items[start:start + 2]):
        column.metric(label, value, help=help_text)

st.divider()
left, right = st.columns([1.45, 1])
with left:
    st.header("Research Question")
    st.markdown(
        "> How well can machine-learning models predict dissolved oxygen and generalize across unseen monitoring stations and future time periods?"
    )
    st.write(
        "This reproducible machine-learning study evaluates random rows, unseen monitoring stations, "
        "future years and future years at unseen stations using a fixed Random Forest. "
        "Its secondary question is where predictions fail even when average errors appear acceptable. "
        "Model Performance contains the new results and limitations. The interactive estimator retains the "
        "Phase 4 model selected by grouped cross-validation and evaluated on 168 held-out stations."
    )
with right:
    st.markdown(
        '<div class="ws-card"><strong>Validated model context</strong><br><br>'
        'Group-CV MAE: 0.880 ± 0.035 mg/L<br>'
        'Final holdout RMSE: 1.291 mg/L<br>'
        'Final holdout R²: 0.539<br>'
        'Train/test station overlap: 0</div>',
        unsafe_allow_html=True,
    )

st.subheader("Project workflow")
step_items = ["Government monitoring data", "Data preparation", "Group-aware validation", "Machine learning", "Error analysis", "Interactive estimation"]
for start in (0, 3):
    step_columns = st.columns(3)
    for column, index, label in zip(step_columns, range(start + 1, start + 4), step_items[start:start + 3]):
        column.markdown(f'<div class="ws-step"><strong>{index:02d}</strong><br>{label}</div>', unsafe_allow_html=True)

st.header("What the result does—and does not—mean")
col1, col2 = st.columns(2)
with col1:
    st.success(
        "The available chemistry and sampling-date context contain predictive information for estimating contemporaneous dissolved oxygen at held-out Northern Ireland monitoring stations."
    )
with col2:
    st.warning(
        "Observed prediction errors are larger at unusually low and high dissolved-oxygen values. The model does not determine safety, forecast unknown future conditions, or establish causes."
    )

scope = st.columns(2)
scope[0].metric("Modelling observations", "151,031", help="Rows with a usable dissolved-oxygen target.")
scope[1].metric("Eligible modelling stations", "840", help="Stations represented after target filtering.")

st.header("Explore the project")
st.write(
    "Use the pages in the sidebar to explore the processed monitoring data, enter a river-water sample, inspect model performance, and understand how the research design evolved."
)
