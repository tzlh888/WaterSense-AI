"""Shared visual and text helpers for the Streamlit interface."""

from __future__ import annotations

from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DISCLAIMER = (
    "WaterSense AI is an educational machine-learning prototype. It estimates "
    "dissolved oxygen from monitoring measurements and should not be used as a "
    "substitute for laboratory analysis, professional environmental assessment, "
    "regulatory monitoring, or safety decisions."
)


def configure_page(title: str) -> None:
    """Apply consistent page configuration and restrained scientific styling."""
    st.set_page_config(
        page_title=f"{title} | WaterSense AI",
        page_icon="💧",
        layout="wide",
        initial_sidebar_state="auto",
    )
    st.markdown(
        """
        <style>
        /* Small, stable visual layer: spacing, reusable cards and narrow-screen type. */
        .block-container {max-width: 1220px; padding-top: 2.2rem; padding-bottom: 4rem;}
        h1, h2, h3 {letter-spacing: -0.02em; line-height: 1.18;}
        h2 {margin-top: 1.6rem;}
        [data-testid="stMetric"] {
            border: 1px solid #d9e5e2;
            border-radius: 10px;
            padding: 0.85rem 1rem;
            background: #fbfdfc;
        }
        .ws-kicker {color: #176b5b; font-weight: 650; text-transform: uppercase;
            letter-spacing: .08em; font-size: .78rem; margin-bottom: .25rem;}
        .ws-lead {font-size: 1.15rem; line-height: 1.65; color: #38514c; max-width: 850px;}
        .ws-card {border: 1px solid #d9e5e2; border-radius: 10px; padding: 1rem 1.1rem;
            background: #fbfdfc; min-height: 110px;}
        .ws-step {border-top: 3px solid #176b5b; padding: .8rem .45rem 0 .45rem;}
        .ws-disclaimer {border-left: 4px solid #b7791f; background: #fffaf0;
            padding: .9rem 1rem; border-radius: 4px; color: #5f461a; margin: 1rem 0 1.5rem 0;}
        .ws-note {border-left: 4px solid #176b5b; background: #f3f7f6;
            padding: .8rem 1rem; border-radius: 4px;}
        div[data-testid="stDataFrame"] {border: 1px solid #e4ecea; border-radius: 8px;}
        @media (max-width: 700px) {
            .block-container {padding: 1.25rem 1rem 3rem;}
            h1 {font-size: 2rem !important;}
            .ws-lead {font-size: 1rem; line-height: 1.5;}
            [data-testid="stMetricValue"] {font-size: 1.65rem;}
            .ws-card {min-height: 0;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.page_link("app.py", label="Home")
        st.page_link("pages/1_Data_Explorer.py", label="Data Explorer")
        st.page_link("pages/2_AI_Estimator.py", label="Dissolved Oxygen Estimator")
        st.page_link("pages/3_Model_Performance.py", label="Model Performance")
        st.page_link("pages/4_About_the_Model.py", label="About the Model")
        st.divider()


def render_disclaimer() -> None:
    """Display the persistent scientific-use disclaimer."""
    st.markdown(f'<div class="ws-disclaimer"><strong>Scientific-use notice.</strong> {DISCLAIMER}</div>', unsafe_allow_html=True)


def render_page_intro(kicker: str, title: str, description: str) -> None:
    """Render a consistent page heading."""
    st.markdown(f'<div class="ws-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="ws-lead">{description}</div>', unsafe_allow_html=True)


def humanise_feature(feature: str) -> str:
    """Return concise public labels for model feature names."""
    labels = {
        "bod_mg_l": "BOD",
        "ammonia_n_mg_l": "Ammonia as N",
        "nitrite_n_mg_l": "Nitrite as N",
        "nitrate_n_mg_l": "Nitrate as N",
        "soluble_reactive_phosphorus_mg_l": "Soluble reactive phosphorus",
        "ph": "pH",
        "alkalinity_mg_l": "Alkalinity",
        "conductivity_us_cm": "Conductivity",
        "suspended_solids_mg_l": "Suspended solids",
        "day_of_year_sin": "Day-of-year sine",
        "day_of_year_cos": "Day-of-year cosine",
    }
    if feature in labels:
        return labels[feature]
    return feature.replace("_is_", " — ").replace("_", " ").title()
