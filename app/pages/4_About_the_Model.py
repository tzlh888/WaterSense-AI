"""Scientific context, development story, and accessible glossary."""

from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from utils.app_helpers import configure_page, render_disclaimer, render_page_intro


configure_page("About the Model")
render_page_intro(
    "Research context and limitations",
    "About the Model",
    "How the dataset, prediction task, validation design and scientific constraints shaped WaterSense AI.",
)
render_disclaimer()

st.header("Research question and evaluation scope")
st.write(
    "How well can machine-learning models predict dissolved oxygen and generalize across unseen monitoring stations and future time periods? "
    "The Model Performance page compares random rows, station groups, and training through 2018 with "
    "2019–2021 calibration and 2022–2024 testing, plus a spatiotemporal holdout trained through 2021 "
    "and tested on 2022–2024 observations at entirely excluded stations. It also reports ablation, error analysis, prediction "
    "interval coverage, and distribution shift. The deployed estimator retains the verified Phase 4 artifact."
)
st.warning(
    "Predictions do not directly measure dissolved oxygen and must not replace field or laboratory measurements. "
    "Validation metrics apply to specific evaluation designs, not universal performance. Unseen stations, later "
    "years and unusual chemistry may be less reliable; environmental relationships can change over time. "
    "The data are observational and predictive importance is not evidence of causation."
)

left, right = st.columns(2)
with left:
    st.header("Dataset")
    st.write(
        "**River Water Quality Monitoring 1990–2024 — All Parameters**, published by the Northern Ireland Environment Agency / DAERA through OpenDataNI. The raw export contains 178,680 observations from 1,311 stations; 151,031 observations from 840 stations were eligible for modelling."
    )
    st.caption(
        "Contains public sector information licensed under the UK Open Government Licence v3.0. "
        "Source and licence links are provided in the repository dataset documentation."
    )
    st.header("Target")
    st.write(
        "Dissolved oxygen in mg/L, retained as an original continuous measurement. The model estimates DO for the same sampling context represented by the inputs."
    )
    st.header("Why regression?")
    st.write(
        "The dataset contains no official Safe, Moderate, High Risk, ecological-status or compliance label. Regression preserves the measured target instead of inventing unsupported categories."
    )
with right:
    st.header("Data challenges")
    st.markdown(
        "- missing measurements with uneven coverage\n"
        "- values reported below or above laboratory limits\n"
        "- repeated observations from the same stations\n"
        "- irregular sampling across 35 years\n"
        "- unusual values that are not verified errors\n"
        "- no water temperature or flow measurement"
    )
    st.header("Validation")
    st.write(
        "Five-fold GroupKFold was used inside 672 training stations. A separate holdout contained 168 unseen stations and 31,341 observations, with zero station overlap. Preprocessing was fitted separately inside each training fold."
    )
    st.header("Final model")
    st.write(
        "Random Forest with 150 trees, minimum leaf size 2, 80% feature sampling and random seed 42. The fitted preprocessing and model are loaded together from the verified Phase 4 artifact."
    )

st.header("Explainability")
st.write(
    "Held-out permutation importance shows how much error increases when a feature’s information is disrupted. Partial dependence visualises global model behaviour. Neither method identifies physical causes. SHAP was deliberately excluded because the global explanation objective was already satisfied without adding dependency complexity."
)

st.header("Limitations")
limitations = st.columns(3)
limitations[0].markdown("**Missing physical context**\n\nNo water temperature or flow measurements are available.")
limitations[1].markdown("**Bounded generalization**\n\nThe evidence covers Northern Ireland rivers and contemporaneous estimation only.")
limitations[2].markdown("**Extreme-value weakness**\n\nLow and high observed DO values are often predicted closer to the middle.")
st.markdown(
    "The model has no causal, regulatory, safety, medical, public-health or future-forecasting validation. "
    "Later-year testing still uses contemporaneous chemistry. The research study evaluates separate calibrated "
    "residual intervals; the estimator's historical error percentiles remain descriptive summaries. "
    "Missing temperature, flow and catchment context may limit performance."
)

st.header("How the Project Evolved")
evolution_items = [
    ("Initial idea", "Water-quality risk classification"),
    ("Problem", "No defensible Safe / Moderate / High labels"),
    ("Decision", "Avoid invented thresholds"),
    ("Reframed task", "Continuous dissolved-oxygen regression"),
    ("Research path", "Censoring → leakage → grouped validation → errors → refinement"),
]
for start, width in ((0, 3), (3, 2)):
    evolution = st.columns(width)
    for column, (heading, body) in zip(evolution, evolution_items[start:start + width]):
        column.markdown(f'<div class="ws-step"><strong>{heading}</strong><br><br>{body}</div>', unsafe_allow_html=True)

st.header("Educational Glossary")
definitions = {
    "Regression": "Predicting a continuous numeric outcome, such as dissolved oxygen in mg/L.",
    "MAE": "Mean absolute error: the average size of prediction errors, ignoring direction, in the target unit.",
    "RMSE": "Root mean squared error: an error metric that gives larger mistakes more influence.",
    "R²": "A comparison with predicting the mean target. It is not percentage accuracy.",
    "Censoring": "A measurement reported only as below or above a laboratory reporting limit rather than as an exact concentration.",
    "Data leakage": "Information enters training that would not legitimately be available when evaluating a new case.",
    "GroupKFold": "Cross-validation that keeps every observation from one station together in either training or validation for each fold.",
    "Random Forest": "An ensemble that averages many decision trees to model nonlinear patterns more stably than a single tree.",
    "Permutation importance": "The increase in held-out error when one feature’s information is shuffled.",
    "Regression toward the mean": "Here, unusually low DO is often predicted too high and unusually high DO too low.",
}
for term, definition in definitions.items():
    with st.expander(term):
        st.write(definition)

st.header("Development transparency")
st.write(
    "AI-assisted coding tools were used during implementation and debugging. Project design, dataset selection, modelling decisions, validation strategy, interpretation and documentation were reviewed and directed by the project author."
)
