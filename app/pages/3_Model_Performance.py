"""Transparent presentation of executed validation and error results."""

from __future__ import annotations

from pathlib import Path
import sys

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from utils.app_helpers import configure_page, render_disclaimer, render_page_intro
from utils.data_loader import load_app_table, load_result_table


configure_page("Model Performance")
render_page_intro(
    "Executed validation results",
    "Model Performance",
    "From baseline models to grouped validation, feature refinement and the final error analysis.",
)
render_disclaimer()

st.header("1. Baseline models")
st.write(
    "Simple references establish whether model complexity adds useful predictive information. "
    "Lower mean absolute error (MAE) is better."
)
baseline = load_result_table("baseline_results.csv").copy()
baseline["MAE (mg/L)"] = baseline["mae"]
figure = px.bar(
    baseline.sort_values("MAE (mg/L)"),
    x="model",
    y="MAE (mg/L)",
    color="model",
    labels={"model": "Model"},
    color_discrete_sequence=["#176B5B", "#5F8E85", "#A4BDB7", "#B7791F"],
)
figure.update_layout(showlegend=False)
st.plotly_chart(figure, width="stretch")

st.header("2. Why grouped validation matters")
validation = st.columns(3)
validation[0].metric("Training stations", "672")
validation[1].metric("Final test stations", "168")
validation[2].metric("Station overlap", "0")
st.markdown(
    '<div class="ws-note"><strong>Unseen-location test.</strong> Every observation from one station stayed '
    "together. The model was therefore tested on monitoring locations it had not seen during training.</div>",
    unsafe_allow_html=True,
)
st.caption(
    "Five-fold GroupKFold inside the training stations supported model and feature selection. "
    "The final test stations were not used for that selection."
)

st.header("3. Feature-set refinement")
feature_sets = load_result_table("feature_set_comparison.csv").copy()
labels = {
    "A_core_chemistry": "Core chemistry",
    "B_extended_chemistry": "Extended chemistry",
    "C_core_plus_temporal": "Core + temporal",
    "D_extended_plus_temporal": "Extended + temporal",
}
feature_sets["Feature set"] = feature_sets["feature_set"].map(labels)
figure = px.bar(
    feature_sets,
    x="Feature set",
    y="cv_mae_mean",
    error_y="cv_mae_std",
    labels={"cv_mae_mean": "Five-fold group-CV MAE (mg/L)"},
    color_discrete_sequence=["#176B5B"],
)
st.plotly_chart(figure, width="stretch")
st.caption(
    "Temporal context improved prediction more than extended chemistry alone. This is a predictive result, "
    "not evidence that season causes dissolved oxygen to change."
)

st.header("4. Final model")
final_metrics = [
    ("Holdout MAE", "0.831 mg/L"),
    ("Holdout RMSE", "1.291 mg/L"),
    ("Holdout R²", "0.539"),
    ("Phase 3 MAE reduction", "29.6%"),
]
for start in (0, 2):
    columns = st.columns(2)
    for column, (label, value) in zip(columns, final_metrics[start:start + 2]):
        column.metric(label, value)
st.caption(
    "These metrics use 31,341 observations from 168 stations absent from training. "
    "The selected model was chosen using training-station cross-validation, not these holdout results."
)

st.header("5. Error analysis")
st.write("Overall MAE hides an important weakness: the middle of the target distribution is predicted more reliably than its extremes.")
tail = load_result_table("error_by_target_range_phase4.csv")
display_order = ["overall", "lowest_10_percent", "25_to_75_percent", "highest_10_percent"]
tail = tail.set_index("range").loc[display_order].reset_index()
tail["Target range"] = tail["range"].map({
    "overall": "Overall",
    "lowest_10_percent": "Lowest 10%",
    "25_to_75_percent": "Central 25–75%",
    "highest_10_percent": "Highest 10%",
})
figure = px.bar(
    tail,
    x="Target range",
    y="mae_mg_l",
    labels={"mae_mg_l": "Holdout MAE (mg/L)"},
    color="Target range",
    color_discrete_sequence=["#176B5B", "#B7791F", "#6D8F87", "#8A5A44"],
)
figure.update_layout(showlegend=False)
st.plotly_chart(figure, width="stretch")
warning_columns = st.columns(2)
warning_columns[0].warning("Lowest 10%: MAE 1.812 mg/L; 89.964% were overpredicted.")
warning_columns[1].warning("Highest 10%: MAE 1.396 mg/L; 94.831% were underpredicted.")
st.write(
    "The model tends to move unusually low estimates upward and unusually high estimates downward. "
    "This regression-toward-the-middle pattern remains a central limitation."
)

st.header("6. Actual versus predicted")
plot_data = load_app_table("holdout_prediction_sample.csv.gz")
figure = px.scatter(
    plot_data,
    x="actual_do_mg_l",
    y="predicted_do_mg_l",
    opacity=0.25,
    labels={"actual_do_mg_l": "Actual dissolved oxygen (mg/L)", "predicted_do_mg_l": "Predicted dissolved oxygen (mg/L)"},
    color_discrete_sequence=["#176B5B"],
)
lower = min(plot_data["actual_do_mg_l"].min(), plot_data["predicted_do_mg_l"].min())
upper = max(plot_data["actual_do_mg_l"].max(), plot_data["predicted_do_mg_l"].max())
figure.add_trace(go.Scatter(x=[lower, upper], y=[lower, upper], mode="lines", name="Exact agreement", line={"color": "#333", "dash": "dash"}))
st.plotly_chart(figure, width="stretch")
st.caption(
    "A reproducible 5,000-row sample of the saved holdout predictions is shown for browser performance. "
    "The dashed line marks exact agreement; distance from it is prediction error."
)

st.subheader("Prediction compression by actual-DO decile")
bins = load_result_table("do_prediction_bins.csv")
figure = go.Figure()
figure.add_trace(go.Scatter(x=bins["mean_actual_do_mg_l"], y=bins["mean_predicted_do_mg_l"], mode="lines+markers", name="Decile means", line={"color": "#176B5B"}))
lower = min(bins["mean_actual_do_mg_l"].min(), bins["mean_predicted_do_mg_l"].min())
upper = max(bins["mean_actual_do_mg_l"].max(), bins["mean_predicted_do_mg_l"].max())
figure.add_trace(go.Scatter(x=[lower, upper], y=[lower, upper], mode="lines", name="Exact agreement", line={"color": "#333", "dash": "dash"}))
figure.update_layout(xaxis_title="Mean actual DO (mg/L)", yaxis_title="Mean predicted DO (mg/L)")
st.plotly_chart(figure, width="stretch")

with st.expander("How to read MAE, RMSE and R²"):
    st.markdown(
        "- **MAE** is the average absolute error in mg/L and is the primary metric.\n"
        "- **RMSE** gives larger errors more influence.\n"
        "- **R²** compares predictions with a mean-prediction reference; it is not percentage accuracy."
    )
