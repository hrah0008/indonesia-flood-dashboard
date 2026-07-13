"""
components/scatter_plot.py
==========================
Scatter-plot components (moved out of line_chart.py for clarity):
  • render_province_scatter — severity x spatial-clustering policy quadrants
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from lib.colors import FONT_BODY


def render_province_scatter(
    df: "pd.DataFrame",
    prov_name: str = "",
    height: int = 460,
    key: str = "province_scatter",
) -> None:
    """Quadrant scatter: one dot per regency, X = FSI, Y = avg growth.

    Median lines (province FSI median, province growth median) split the plot
    into four descriptive quadrants. Dots are coloured by cluster if a
    'cluster' column exists, otherwise by growth (diverging). This is a
    DESCRIPTIVE cross-regency view, not the causal within-regency estimate.

    df : columns regency | FSI_index | growth_avg | [cluster]
    """
    if df is None or len(df) == 0:
        st.info("No regency data for this province.")
        return

    d = df.dropna(subset=["FSI_index", "growth_avg"]).copy()
    if len(d) < 3:
        st.info("Too few regencies with FSI data for a quadrant view.")
        return

    # median split lines (robust to outliers)
    fsi_med = float(d["FSI_index"].median())
    grw_med = float(d["growth_avg"].median())
    x_min, x_max = d["FSI_index"].min(), d["FSI_index"].max()
    y_min, y_max = d["growth_avg"].min(), d["growth_avg"].max()
    x_pad = (x_max - x_min) * 0.12 + 1e-6
    y_pad = (y_max - y_min) * 0.12 + 1e-6
    x_lo, x_hi = x_min - x_pad, x_max + x_pad
    y_lo, y_hi = y_min - y_pad, y_max + y_pad

    fig = go.Figure()

    # quadrant shading (very light) — high-FSI/low-growth = concern
    fig.add_shape(type="rect", x0=fsi_med, x1=x_hi, y0=y_lo, y1=grw_med,
                  fillcolor="#fde2e1", opacity=0.35, line_width=0, layer="below")
    fig.add_shape(type="rect", x0=x_lo, x1=fsi_med, y0=grw_med, y1=y_hi,
                  fillcolor="#e6f0da", opacity=0.35, line_width=0, layer="below")

    # median split lines
    fig.add_vline(x=fsi_med, line_width=1, line_dash="dash", line_color="#9ca3af")
    fig.add_hline(y=grw_med, line_width=1, line_dash="dash", line_color="#9ca3af")

    # points — colour by cluster if present, else by growth
    if "cluster" in d.columns and d["cluster"].notna().any():
        CLUSTER_COLOR = {
            "Low Impact": "#84cc16",
            "Catastrophic": "#dc2626",
            "Frequent-Contained": "#f59e0b",
        }
        for clab, grp in d.groupby("cluster"):
            fig.add_trace(go.Scatter(
                x=grp["FSI_index"], y=grp["growth_avg"], mode="markers",
                name=str(clab),
                marker=dict(size=10, color=CLUSTER_COLOR.get(str(clab), "#6b7280"),
                            line=dict(width=0.5, color="#374151")),
                text=grp["regency"],
                hovertemplate="%{text}<br>FSI %{x:.1f} · growth %{y:.2f}%<extra></extra>",
            ))
        show_legend = True
    else:
        fig.add_trace(go.Scatter(
            x=d["FSI_index"], y=d["growth_avg"], mode="markers",
            marker=dict(
                size=10, color=d["growth_avg"],
                colorscale=[[0, "#a32d2d"], [0.5, "#ffffff"], [1, "#3b6d11"]],
                cmid=0, showscale=True,
                colorbar=dict(title="Growth %", thickness=12, len=0.6),
                line=dict(width=0.5, color="#374151"),
            ),
            text=d["regency"],
            hovertemplate="%{text}<br>FSI %{x:.1f} · growth %{y:.2f}%<extra></extra>",
        ))
        show_legend = False

    # quadrant corner labels
    _ann = dict(showarrow=False, font=dict(size=10, color="#6b7280"),
                xref="x", yref="y")
    fig.add_annotation(x=x_hi, y=y_lo, text="High flood · low growth",
                       xanchor="right", yanchor="bottom", **_ann)
    fig.add_annotation(x=x_hi, y=y_hi, text="High flood · high growth",
                       xanchor="right", yanchor="top", **_ann)
    fig.add_annotation(x=x_lo, y=y_hi, text="Low flood · high growth",
                       xanchor="left", yanchor="top", **_ann)
    fig.add_annotation(x=x_lo, y=y_lo, text="Low flood · low growth",
                       xanchor="left", yanchor="bottom", **_ann)

    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=10, b=0),
        font=dict(family=FONT_BODY, color="#1f2937", size=12),
        xaxis=dict(title="Flood Severity Index (FSI)", showgrid=False,
                   range=[x_lo, x_hi]),
        yaxis=dict(title="Avg GRDP growth (%)", showgrid=False,
                   range=[y_lo, y_hi]),
        showlegend=show_legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="closest",
    )

    st.plotly_chart(fig, key=key, config={"displayModeBar": False})
    st.caption(
        f"Dashed lines split the province at its median FSI ({fsi_med:.1f}) and "
        f"median growth ({grw_med:.2f}%), giving four descriptive quadrants. "
        f"This is a cross-regency correlation within the province, not a causal "
        f"estimate; thresholds are relative and with few regencies the grouping "
        f"can shift."
    )


# ═════════════════════════════════════════════════════════════════════════
# Social quadrant scatter — FSI vs a social outcome (poverty OR unemployment)
# ═════════════════════════════════════════════════════════════════════════
def render_social_scatter(
    df: "pd.DataFrame",
    metric: str = "tpt",
    prov_name: str = "",
    height: int = 420,
    key: str = "social_scatter",
) -> None:
    """Quadrant scatter: one dot per regency, X = FSI, Y = a social rate.

    Unlike the Economic scatter (growth: higher = better), social outcomes are
    "higher = worse" (more poverty / unemployment), so the CONCERN quadrant is
    high-FSI / high-rate (top-right), shaded red. Median lines split the plot.
    This is a DESCRIPTIVE cross-regency view, not a causal estimate — the
    regression finds flooding is not a robust driver of these outcomes.

    df     : columns regency | FSI_index | poverty_avg | tpt_avg
    metric : "tpt" (unemployment) or "poverty"
    """
    col   = "tpt_avg" if metric == "tpt" else "poverty_avg"
    label = "Unemployment (TPT) %" if metric == "tpt" else "Poverty rate %"
    DOT   = "#b5651d" if metric == "tpt" else "#a32d2d"

    if df is None or len(df) == 0:
        st.info("No regency data for this province.")
        return
    d = df.dropna(subset=["FSI_index", col]).copy()
    if len(d) < 3:
        st.info("Too few regencies with FSI data for a quadrant view.")
        return

    # regency-name column may be 'regency' (fsi table) or 'kemendagri_kab_name'
    # (choropleth table) — pick whichever is present.
    name_col = ("regency" if "regency" in d.columns
                else "kemendagri_kab_name" if "kemendagri_kab_name" in d.columns
                else None)
    d["_name"] = d[name_col] if name_col else ""

    fsi_med = float(d["FSI_index"].median())
    out_med = float(d[col].median())
    x_min, x_max = d["FSI_index"].min(), d["FSI_index"].max()
    y_min, y_max = d[col].min(), d[col].max()
    x_pad = (x_max - x_min) * 0.12 + 1e-6
    y_pad = (y_max - y_min) * 0.12 + 1e-6
    x_lo, x_hi = x_min - x_pad, x_max + x_pad
    y_lo, y_hi = y_min - y_pad, y_max + y_pad

    fig = go.Figure()

    # concern = high FSI + high (bad) rate = TOP-RIGHT, light red
    fig.add_shape(type="rect", x0=fsi_med, x1=x_hi, y0=out_med, y1=y_hi,
                  fillcolor="#fde2e1", opacity=0.35, line_width=0, layer="below")
    # least concern = low FSI + low rate = BOTTOM-LEFT, light green
    fig.add_shape(type="rect", x0=x_lo, x1=fsi_med, y0=y_lo, y1=out_med,
                  fillcolor="#e6f0da", opacity=0.35, line_width=0, layer="below")

    fig.add_vline(x=fsi_med, line_width=1, line_dash="dash", line_color="#9ca3af")
    fig.add_hline(y=out_med, line_width=1, line_dash="dash", line_color="#9ca3af")

    fig.add_trace(go.Scatter(
        x=d["FSI_index"], y=d[col], mode="markers",
        marker=dict(size=10, color=DOT, opacity=0.85,
                    line=dict(width=0.5, color="#374151")),
        text=d["_name"],
        hovertemplate="%{text}<br>FSI %{x:.1f} · " + label + " %{y:.2f}<extra></extra>",
    ))

    _ann = dict(showarrow=False, font=dict(size=10, color="#6b7280"),
                xref="x", yref="y")
    fig.add_annotation(x=x_hi, y=y_hi, text="High flood · high rate",
                       xanchor="right", yanchor="top", **_ann)
    fig.add_annotation(x=x_hi, y=y_lo, text="High flood · low rate",
                       xanchor="right", yanchor="bottom", **_ann)
    fig.add_annotation(x=x_lo, y=y_hi, text="Low flood · high rate",
                       xanchor="left", yanchor="top", **_ann)
    fig.add_annotation(x=x_lo, y=y_lo, text="Low flood · low rate",
                       xanchor="left", yanchor="bottom", **_ann)

    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=10, b=0),
        font=dict(family=FONT_BODY, color="#1f2937", size=12),
        xaxis=dict(title="Flood Severity Index (FSI)", showgrid=False, range=[x_lo, x_hi]),
        yaxis=dict(title=label, showgrid=False, range=[y_lo, y_hi]),
        showlegend=False, hovermode="closest",
    )
    st.plotly_chart(fig, key=key, config={"displayModeBar": False})
    st.caption(
        f"Dashed lines split at the province median FSI ({fsi_med:.1f}) and "
        f"median {label.lower()} ({out_med:.2f}). The red corner (high flood + "
        f"high rate) flags regencies where both coincide &mdash; a descriptive "
        f"spatial coincidence, not a causal link (the regression finds no robust "
        f"flood effect on social outcomes)."
    )