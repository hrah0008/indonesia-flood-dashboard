"""
components/correlation.py
=========================
Correlation-matrix visual (moved out of line_chart.py for clarity):
  • render_social_correlation_heatmap — descriptive bivariate correlations
    between flood dimensions / context and the social outcomes.
"""

import streamlit as st
import plotly.graph_objects as go

from lib.colors import FONT_BODY


def render_social_correlation_heatmap(corr: dict, height: int = 300,
                                      key: str = "social_corr") -> None:
    """Heatmap of bivariate correlations: flood dims + controls (x) vs
    poverty/unemployment (y). DESCRIPTIVE, not controlled effects."""
    if not corr or "matrix" not in corr:
        st.info("No correlation data.")
        return
    x = corr["x_labels"]; y = corr["y_labels"]; z = corr["matrix"]

    fig = go.Figure(go.Heatmap(
        z=z, x=x, y=y,
        colorscale=[[0, "#a32d2d"], [0.5, "#ffffff"], [1, "#185FA5"]],
        zmid=0, zmin=-1, zmax=1,
        text=[[f"{v:+.2f}" for v in row] for row in z],
        texttemplate="%{text}",
        textfont=dict(size=12),
        hovertemplate="%{y} vs %{x}<br>r = %{z:.3f}<extra></extra>",
        colorbar=dict(title="r", thickness=10, len=0.9, tickfont=dict(size=9)),
        xgap=2, ygap=2,
    ))
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=10, b=0),
        font=dict(family=FONT_BODY, color="#1f2937", size=11),
        xaxis=dict(side="bottom", tickangle=-20),
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig, key=key, config={"displayModeBar": False})
