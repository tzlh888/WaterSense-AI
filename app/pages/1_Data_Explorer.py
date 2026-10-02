"""Interactive exploration of the processed monitoring dataset."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from utils.app_helpers import configure_page, render_disclaimer, render_page_intro
from utils.data_loader import load_app_table, load_explorer_sample


configure_page("Data Explorer")
render_page_intro(
    "Verified monitoring records",
    "Data Explorer",
    "Explore the processed observations used for modelling. Filters and charts are descriptive; correlations and temporal patterns do not demonstrate causation.",
)
render_disclaimer()

try:
    data = load_explorer_sample()
    summary = load_app_table("dataset_summary.csv").set_index("metric")["value"].to_dict()
    yearly = load_app_table("yearly_summary.csv")
    monthly = load_app_table("monthly_summary.csv")
    missing = load_app_table("missingness_summary.csv")
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

VARIABLES = {
    "Dissolved oxygen (mg/L)": "dissolved_oxygen_mg_l",
    "BOD (mg/L)": "bod_mg_l",
    "Ammonia as N (mg/L)": "ammonia_n_mg_l",
    "Nitrite as N (mg/L)": "nitrite_n_mg_l",
    "Nitrate as N (mg/L)": "nitrate_n_mg_l",
    "Soluble reactive phosphorus (mg/L)": "soluble_reactive_phosphorus_mg_l",
    "pH (pH units)": "ph",
    "Alkalinity (mg/L)": "alkalinity_mg_l",
    "Conductivity (µS/cm)": "conductivity_us_cm",
    "Suspended solids (mg/L)": "suspended_solids_mg_l",
}

with st.sidebar:
    st.header("Explorer filters")
    years = st.slider(
        "Sampling years",
        min_value=int(data["sample_year"].min()),
        max_value=int(data["sample_year"].max()),
        value=(int(data["sample_year"].min()), int(data["sample_year"].max())),
    )
    stations = sorted(data["station_code"].unique())
    selected_stations = st.multiselect(
        "Optional station filter",
        options=stations,
        placeholder="Search station codes…",
        help="Leave empty to include all eligible stations.",
    )
    selected_label = st.selectbox("Measurement", options=list(VARIABLES))

filtered = data[data["sample_year"].between(*years)]
if selected_stations:
    filtered = filtered[filtered["station_code"].isin(selected_stations)]

summary_items = [
    ("Modelling observations", f"{int(summary['modelling_observations']):,}"),
    ("Eligible stations", f"{int(summary['eligible_stations']):,}"),
    ("Time coverage", "1990–2024"),
    ("Plotting sample", f"{len(filtered):,} rows"),
]
for start in (0, 2):
    summary_columns = st.columns(2)
    for column, (label, value) in zip(summary_columns, summary_items[start:start + 2]):
        column.metric(label, value)

if filtered.empty:
    st.warning("No observations match the current filters.")
    st.stop()

selected_feature = VARIABLES[selected_label]
chart_sample = filtered
st.caption(
    "Interactive distributions, station filters and previews use a reproducible sample of real observations. "
    "Annual/monthly summaries and missingness use exact aggregates from all 151,031 modelling observations."
)

left, right = st.columns(2)
with left:
    st.subheader(f"Distribution: {selected_label}")
    figure = px.histogram(
        chart_sample,
        x=selected_feature,
        nbins=60,
        labels={selected_feature: selected_label},
        color_discrete_sequence=["#176B5B"],
    )
    figure.update_layout(yaxis_title="Observations", showlegend=False)
    st.plotly_chart(figure, width="stretch")
with right:
    if selected_stations:
        st.subheader("Sample records per year")
        annual_counts = filtered.groupby("sample_year").size().reset_index(name="records")
    else:
        st.subheader("Sampling records per year")
        annual_counts = yearly[yearly["sample_year"].between(*years)][["sample_year", "records"]]
    figure = px.line(
        annual_counts,
        x="sample_year",
        y="records",
        markers=True,
        labels={"sample_year": "Year", "records": "Records"},
        color_discrete_sequence=["#176B5B"],
    )
    st.plotly_chart(figure, width="stretch")

left, right = st.columns(2)
with left:
    st.subheader("Dissolved oxygen through time")
    if selected_stations:
        annual_do = filtered.groupby("sample_year")["dissolved_oxygen_mg_l"].agg(["median", "mean"]).reset_index()
    else:
        annual_do = yearly[yearly["sample_year"].between(*years)].rename(
            columns={"median_do_mg_l": "median", "mean_do_mg_l": "mean"}
        )
    melted = annual_do.melt(id_vars=["sample_year"], value_vars=["median", "mean"], var_name="summary", value_name="do_mg_l")
    figure = px.line(
        melted,
        x="sample_year",
        y="do_mg_l",
        color="summary",
        labels={"sample_year": "Year", "do_mg_l": "Dissolved oxygen (mg/L)", "summary": "Statistic"},
        color_discrete_map={"median": "#176B5B", "mean": "#7D5A3A"},
    )
    st.plotly_chart(figure, width="stretch")
with right:
    st.subheader("Monthly dissolved oxygen")
    if not selected_stations and years == (int(data["sample_year"].min()), int(data["sample_year"].max())):
        monthly_chart = monthly
    else:
        monthly_chart = filtered.groupby("sample_month")["dissolved_oxygen_mg_l"].agg(
            median_do_mg_l="median", mean_do_mg_l="mean"
        ).reset_index()
    figure = px.line(
        monthly_chart,
        x="sample_month",
        y="median_do_mg_l",
        markers=True,
        labels={"sample_month": "Month", "median_do_mg_l": "Median dissolved oxygen (mg/L)"},
        color_discrete_sequence=["#176B5B"],
    )
    figure.update_xaxes(dtick=1)
    st.plotly_chart(figure, width="stretch")

st.subheader("Missing measurements")
measurement_columns = list(VARIABLES.values())
label_by_feature = {feature: label for label, feature in VARIABLES.items()}
missing["Measurement"] = missing["feature"].map(label_by_feature)
missing = missing.rename(columns={"missing_percent": "Missing percent"}).sort_values("Missing percent", ascending=True)
figure = px.bar(
    missing,
    x="Missing percent",
    y="Measurement",
    orientation="h",
    labels={"Missing percent": "Missing observations (%)"},
    color_discrete_sequence=["#6D8F87"],
)
st.plotly_chart(figure, width="stretch")

with st.expander("Correlation matrix", expanded=False):
    st.caption("Pearson correlations describe linear association among available numeric pairs; they do not establish causation.")
    correlation_sample = filtered[measurement_columns].sample(n=min(20_000, len(filtered)), random_state=42)
    correlation = correlation_sample.corr()
    short_labels = [label.split(" (")[0] for label in VARIABLES]
    correlation.index = short_labels
    correlation.columns = short_labels
    figure = px.imshow(correlation, zmin=-1, zmax=1, color_continuous_scale="RdBu_r", text_auto=".2f", aspect="auto")
    figure.update_layout(coloraxis_colorbar_title="Pearson r")
    st.plotly_chart(figure, width="stretch")

with st.expander("Preview filtered records", expanded=False):
    preview_columns = ["station_code", "sample_date", "dissolved_oxygen_mg_l", selected_feature]
    preview_columns = list(dict.fromkeys(preview_columns))
    st.dataframe(filtered[preview_columns].head(200), width="stretch", hide_index=True)
    st.caption("Preview limited to 200 rows from the reproducible plotting sample.")
