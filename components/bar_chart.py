"""
components/bar_chart.py
=======================
Bar-chart components (moved out of line_chart.py for clarity):
  • render_sector_impact_bar   — significant flood effects by sector x dimension
  • render_composition_stacked — GRDP sector composition over time (stacked)
"""

import streamlit as st
import plotly.graph_objects as go

from lib.colors import HAIRLINE, FONT_BODY


def render_sector_impact_bar(
    impact: dict,
    height: int = 460,
    key: str = "sector_impact_bar",
) -> None:
    """Horizontal bar chart of significant sector flood effects.

    Bars are sector×dimension coefficients (beta) that reached significance.
    Evidence grade is encoded by colour saturation:
      • robust (**)      — full colour (significant under BOTH SE)
      • suggestive (~)   — pale / outline (significant under ONE SE only)
    Bars diverge from 0: positive = flood linked to higher sector growth
    (e.g. reconstruction), negative = lower growth.

    impact : dict from load_national_sector_impact()
    """
    if not impact or not impact.get("bars"):
        st.info("No significant sector effects to display.")
        return

    bars = impact["bars"]

    # dimension colour families (consistent with the Flood SERIES palette)
    DIM_COLOR = {
        "event": {"robust": "#0c447c", "suggestive": "#9db8d6"},  # blue
        "HCI":   {"robust": "#a32d2d", "suggestive": "#e0a5a4"},  # red
        "PDI":   {"robust": "#b45309", "suggestive": "#e8c79a"},  # amber
    }

    # build label "Sector · dim" and colour per bar
    labels = [f"{b['sector']} · {b['dimension']}" for b in bars]
    betas  = [b["beta"] for b in bars]
    colors = [DIM_COLOR.get(b["dimension"], {}).get(b["grade"], "#9ca3af") for b in bars]
    flags  = [b["flag"] for b in bars]
    grades = [b["grade"] for b in bars]

    # reverse so the strongest (first in list) sits on top
    labels, betas, colors, flags, grades = (
        labels[::-1], betas[::-1], colors[::-1], flags[::-1], grades[::-1]
    )

    fig = go.Figure(go.Bar(
        x=betas, y=labels, orientation="h",
        marker=dict(color=colors,
                    line=dict(width=1.0, color="#374151")),
        customdata=list(zip(flags, grades)),
        hovertemplate=("%{y}<br>\u03b2 = %{x:.3f}"
                       "<br>%{customdata[1]} (%{customdata[0]})<extra></extra>"),
    ))
    fig.add_vline(x=0, line_width=1, line_color="#9ca3af")

    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=10, b=0),
        font=dict(family=FONT_BODY, color="#1f2937", size=12),
        xaxis=dict(title="Coefficient (\u03b2) — effect on sector growth",
                   zeroline=True, zerolinecolor="#9ca3af",
                   showgrid=True, gridcolor=HAIRLINE),
        yaxis=dict(title="", automargin=True),
        showlegend=False,
        bargap=0.35,
    )

    st.plotly_chart(
        fig,
        key=key,
        config={"displayModeBar": False},
    )

    # honest legend + NS note
    st.caption(
        f"**Full colour** = robust (significant under both clustered & "
        f"Driscoll\u2013Kraay SE); **pale** = suggestive (one SE only). "
        f"Blue = flood frequency · red = human cost · amber = physical damage. "
        f"{impact.get('note', '')}"
    )


def render_composition_stacked(
    composition: dict,
    mode: str = "rupiah",
    height: int = 460,
    key: str = "composition_stacked",
) -> None:
    """Stacked bar of sector composition over time for one regency.

    One bar per year, stacked by all 17 sectors. Two modes:
      • 'rupiah'  — absolute GRDP level (bar height = total GRDP, grows)
      • 'share'   — 100% stacked (each bar = 100%, shows structural shift)

    composition : dict with keys sectors / years / levels / totals
                  (from the regency series JSON, nb13 STEP 8).
    """
    if not composition or "levels" not in composition:
        st.info("No composition data for this regency.")
        return

    sectors = composition["sectors"]
    years = composition["years"]
    levels = composition["levels"]
    totals = composition.get("totals", [])

    # 17-colour qualitative palette (distinct, print-safe-ish)
    PALETTE = [
        "#3b6d11", "#6aa121", "#9fce6a", "#c7e29b", "#185fa5", "#4a8fce",
        "#8bbce4", "#dc6b2f", "#f2a25c", "#f6c89a", "#8c4a9e", "#b884c9",
        "#b5651d", "#d99a5b", "#6b7280", "#a8b0bd", "#d4af37",
    ]

    fig = go.Figure()
    for i, sec in enumerate(sectors):
        vals = levels.get(sec, [0] * len(years))
        if mode == "share":
            y = [round(v / t * 100, 2) if t else 0 for v, t in zip(vals, totals)]
            hover = "%{x}<br>" + sec + ": %{y:.1f}%<extra></extra>"
        else:
            y = vals
            hover = "%{x}<br>" + sec + ": Rp %{y:,.0f}<extra></extra>"
        fig.add_trace(go.Bar(
            x=[str(yr) for yr in years], y=y, name=sec,
            marker=dict(color=PALETTE[i % len(PALETTE)], line=dict(width=0)),
            hovertemplate=hover,
        ))

    y_title = "Share of GRDP (%)" if mode == "share" else "GRDP (constant 2010 prices)"
    fig.update_layout(
        barmode="stack",
        height=height,
        margin=dict(l=0, r=0, t=10, b=0),
        font=dict(family=FONT_BODY, color="#1f2937", size=12),
        xaxis=dict(title="", showgrid=False, type="category",
                   tickmode="array", tickvals=[str(yr) for yr in years]),
        yaxis=dict(title=y_title, showgrid=True, gridcolor=HAIRLINE,
                   range=[0, 100] if mode == "share" else None),
        legend=dict(orientation="h", yanchor="top", y=-0.08, xanchor="left", x=0,
                    font=dict(size=10)),
        hovermode="closest",
    )
    st.plotly_chart(fig, key=key, config={"displayModeBar": False})
