"""
pages/5_Model_Evaluation.py
===========================
Model Evaluation menu — how well can flooding PREDICT socioeconomic outcomes?

Two tabs:
  - Economic : overall GRDP growth + a selector for the 17 sectors
  - Social   : poverty + unemployment

Each outcome shows three simple views plus a key-findings narrative:
  1. Three-stage metrics table (R² / RMSE / MAE + naive baseline)
  2. SHAP beeswarm (real SHAP plot, PNG from nb16)
  3. SHAP importance bar chart (flood vs control)

This is model EVALUATION, not forecasting: the study is observational and the
evidence shows flooding is a weak predictor. Views are built so a weak model
cannot be mistaken for a strong predictor.

Data: public/data/model/ (built by nb16_build_dashboard_model.ipynb)
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from lib.colors import INK, MUTED, HAIRLINE, INDIGO, FONT_DISPLAY, FONT_BODY, FONT_MONO
from components.section_header import render_page_header, render_section_header
from components.sidebar_nav import render_sidebar_nav


st.set_page_config(
    page_title="FloodX — Model Evaluation",
    page_icon=":microscope:",
    layout="wide",
    initial_sidebar_state="expanded",
)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_MODEL_DIR = _PROJECT_ROOT / "public" / "data" / "model"


@st.cache_data(show_spinner=False)
def _read_json(name):
    with open(_MODEL_DIR / name) as f:
        return json.load(f)


# ─── Reusable renderer for one outcome ────────────────────────────────
def render_outcome(data):
    """Three simple views + narrative for one outcome dict."""
    # 1. Three-stage metrics table
    st.markdown("**1 · Performance — R², RMSE, MAE across the three stages**")
    df = pd.DataFrame(data["stages"])
    df.columns = ["Stage", "R²", "RMSE", "MAE"]
    st.dataframe(
        df.style.format({"R²": "{:+.3f}", "RMSE": "{:.3f}", "MAE": "{:.3f}"}),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "Tuned on training years, selected on 2023, evaluated once on 2024–25. "
        "The naive baseline predicts the training mean. **Note:** this R² reflects "
        "the *full* model (flood + control variables together), so a high R² does "
        "not by itself mean flooding predicts the outcome — see the flood share "
        "below for flooding's actual contribution."
    )

    col_l, col_r = st.columns(2)

    # 2. SHAP beeswarm (PNG)
    with col_l:
        st.markdown("**2 · SHAP beeswarm**")
        png = _MODEL_DIR / data["beeswarm"]
        if png.exists():
            st.image(str(png), width="stretch")
        else:
            st.info("Beeswarm image not found — re-run nb16.")
        st.caption(
            "Each dot is one regency. Position = SHAP value (impact on the "
            "prediction); colour = feature value (red high, blue low)."
        )

    # 3. Importance bar
    with col_r:
        st.markdown("**3 · Feature importance (flood vs control)**")
        imp = pd.DataFrame(data["importance"])
        imp = imp.set_index("label")["importance"]
        st.bar_chart(imp)
        fshare = data["flood_share"]
        st.caption(
            f"Flood share of importance: **{fshare:.0f}%** "
            f"(control {100-fshare:.0f}%). This is flooding's actual contribution "
            f"to the prediction. A high total R² with a low flood share means the "
            f"model predicts using controls (population, schooling), not flooding."
        )

    # Key findings narrative
    render_section_header(
        kicker="Key findings",
        title="FE vs XGBoost — what it means",
    )
    st.markdown(data["narrative"])


# ═════════════════════════════════════════════════════════════════════
with st.sidebar:
    render_sidebar_nav()

render_page_header(
    menu_label="Model Evaluation",
    title="Can flooding predict socioeconomic outcomes?",
    description=(
        "An honest evaluation of how well flood exposure predicts regional "
        "outcomes using XGBoost and SHAP — model evaluation, not a forecast."
    ),
)

try:
    index = _read_json("index.json")
    economic = _read_json("economic.json")
    social = _read_json("social.json")
except FileNotFoundError:
    st.error(
        "Model-evaluation data not found. Run nb16_build_dashboard_model.ipynb "
        "and copy its output to public/data/model/."
    )
    st.stop()

# Overview banner (replaces a numeric KPI strip). A numeric R2 KPI could
# mislead: total R2 mixes flood + controls, so a high R2 does not mean
# flooding predicts. A plain-language intro is clearer; the per-outcome
# "Key findings" below carry the actual conclusions.
_banner_style = (
    f"background:#fafaf9;border:1px solid {HAIRLINE};border-left:3px solid {INDIGO};"
    f"border-radius:8px;padding:16px 20px;margin-bottom:8px;"
)
_banner_html = (
    f'<div style="{_banner_style}">'
    f'<div style="font-family:{FONT_MONO};font-size:10px;font-weight:600;'
    f'letter-spacing:0.10em;text-transform:uppercase;color:{MUTED};">'
    f'Overview</div>'
    f'<div style="font-family:{FONT_BODY};font-size:14px;color:{INK};'
    f'line-height:1.6;margin-top:6px;max-width:820px;">'
    f'This menu evaluates whether flood exposure can <strong>predict</strong> '
    f'socioeconomic outcomes, using XGBoost tested on unseen 2024&ndash;2025 '
    f'data and SHAP to attribute predictions to individual features. Two tabs '
    f'organise the outcomes: <strong>Economic</strong> (overall GRDP growth and '
    f'the 17 sectors) and <strong>Social</strong> (poverty and unemployment). '
    f'Each outcome shows the model&rsquo;s performance, a SHAP beeswarm, a '
    f'feature-importance breakdown, and a short read of what it means. '
    f'When reading the results, note that total R&sup2; reflects the full model '
    f'(flood <em>and</em> control variables), so the <strong>flood share</strong> '
    f'is what isolates flooding&rsquo;s own contribution.'
    f'</div></div>'
)
st.markdown(_banner_html, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════
tab_econ, tab_social = st.tabs(["Economic", "Social"])

# ─── TAB 1 — ECONOMIC ─────────────────────────────────────────────────
with tab_econ:
    render_section_header(
        kicker="Economic · GRDP growth",
        title="Overall growth",
    )
    render_outcome(economic["overall"])

    st.markdown("---")
    render_section_header(
        kicker="Economic · by sector",
        title="Sector growth (select one of 17)",
    )
    sectors = economic["sectors"]
    sector_names = sorted(sectors.keys())
    pretty = {s: s.replace("_", " ").title() for s in sector_names}
    pick = st.selectbox(
        "Sector",
        sector_names,
        format_func=lambda s: pretty[s],
    )
    render_outcome(sectors[pick])

# ─── TAB 2 — SOCIAL ───────────────────────────────────────────────────
with tab_social:
    render_section_header(
        kicker="Social · poverty",
        title="Poverty rate",
    )
    render_outcome(social["poverty"])

    st.markdown("---")
    render_section_header(
        kicker="Social · unemployment",
        title="Unemployment (TPT)",
    )
    render_outcome(social["tpt"])