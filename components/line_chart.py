"""
components/line_chart.py
========================
Annual time-series line chart with togglable series.

NEW IN THIS REVISION
--------------------
Default display is the **three FSI dimensions + composite**, all rescaled
to 0-100 so they're visually comparable on one axis:

    event_index — frequency dimension (events per year, rescaled)
    hci_index   — Human Cost Index (annual total, rescaled)
    pdi_index   — Property Damage Index (annual total, rescaled)
    fsi_index   — FSI Score composite (annual mean, rescaled)

This tells the "three dimensions" story — the same dimensions that drive
the FSI map colour and the cluster-weighted methodology — over time.

Raw counts (events, deaths, houses_*, fasum_damaged) remain togglable for
users who want absolute numbers, but they're not the default view.

The legacy y-axis label ("% of period total") is replaced with "Indexed
0-100 (each series rescaled to its own min-max range)" so users don't
mistake this for a share-of-total percentage.
"""

from typing import Optional

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from lib.colors import (
    SERIES_COLORS, SERIES_LABELS,
    SERIES_DEFAULT_HEADLINE,
    MUTED, HAIRLINE, FONT_BODY,
)


def render_annual_line_chart(
    annual: dict,
    default_series: Optional[list[str]] = None,
    height: int = 440,
    key: str = "national_line",
) -> None:
    """
    Render the National-tab annual line chart.

    Default view: the four headline indexed series — event_index, hci_index,
    pdi_index, fsi_index — telling the "three FSI dimensions + composite"
    story on a common 0-100 axis.

    Parameters
    ----------
    annual : dict
        Output of `load_national_annual()` — a dict-of-lists keyed by
        "years" + series names matching keys in SERIES_LABELS.
    default_series : list[str], optional
        Override the default-shown series. If None, uses
        SERIES_DEFAULT_HEADLINE (the four indexed dimensions).
    height : int
        Chart height in pixels.
    key : str
        Streamlit widget key (must be unique per page).
    """
    if not annual or "years" not in annual:
        st.info("No annual data available.")
        return

    df = pd.DataFrame(annual)
    if "years" in df.columns and "year" not in df.columns:
        df = df.rename(columns={"years": "year"})
    if "year" not in df.columns:
        st.warning("Annual data missing 'year' / 'years' column.")
        return
    df = df.sort_values("year")

    # All series present in the data AND known in SERIES_LABELS
    available = [k for k in SERIES_LABELS.keys() if k in df.columns]
    if not available:
        st.warning("No recognised series in annual data.")
        return

    # Default selection — the four headline indexed series, falling back
    # to whatever's available if data is from an older nb12 run
    if default_series is None:
        default_series = [s for s in SERIES_DEFAULT_HEADLINE if s in available]
    if not default_series:
        # Last-resort fallback
        default_series = available[:4]

    # ── UI — multiselect with sensible defaults ─────────────────────
    selected = st.multiselect(
        "Variables to display",
        options=available,
        default=default_series,
        format_func=lambda k: SERIES_LABELS.get(k, k),
        key=key,
        label_visibility="collapsed",
        help=(
            "Headline series (Event frequency · HCI · PDI · FSI Score) are "
            "rescaled to 0-100 for visual comparison. Raw-count series "
            "(Deaths, Houses flooded, etc.) are in absolute units."
        ),
    )

    if not selected:
        st.info("Select at least one variable.")
        return

    # ── Determine if all selected series are indexed (0-100 scale) ──
    # If yes, the y-axis is "Indexed 0-100"; otherwise we can't put them
    # on the same scale meaningfully, so we show absolute units and warn.
    indexed_series = {"event_index", "hci_index", "pdi_index", "fsi_index"}
    selected_set = set(selected)
    all_indexed = bool(selected_set) and selected_set.issubset(indexed_series)
    mixed = (selected_set & indexed_series) and not all_indexed

    # ── Build chart ─────────────────────────────────────────────────
    fig = go.Figure()
    for s in selected:
        is_indexed = s in indexed_series
        # Use raw · NOT &middot; — Plotly hovertemplate does not decode entities
        hover_unit = " / 100" if is_indexed else ""
        fig.add_trace(
            go.Scatter(
                x=df["year"],
                y=df[s],
                mode="lines+markers",
                name=SERIES_LABELS.get(s, s),
                line=dict(
                    color=SERIES_COLORS.get(s, "#888"),
                    width=2.6 if s == "fsi_index" else 2.0,
                    dash="solid" if s != "fsi_index" else "solid",
                ),
                marker=dict(size=7 if s == "fsi_index" else 6,
                            line=dict(width=1, color="white")),
                hovertemplate=(
                    f"<b>{SERIES_LABELS.get(s, s)}</b><br>"
                    f"%{{x}}: %{{y:.2f}}{hover_unit}<extra></extra>"
                ),
            )
        )

    # Y-axis label depends on the selection
    if all_indexed:
        y_title = "Indexed 0-100 (each series rescaled to its own range)"
    elif mixed:
        y_title = "Mixed units · indexed (0-100) and raw counts"
    else:
        y_title = "Raw counts (absolute units)"

    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=20, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family=FONT_BODY, size=12, color="#1f2937"),
        xaxis=dict(
            title="",
            showgrid=False,
            tickfont=dict(size=11, color=MUTED),
            linecolor=HAIRLINE,
            dtick=1,
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(size=10.5, color=MUTED)),
            gridcolor=HAIRLINE,
            zerolinecolor=HAIRLINE,
            tickfont=dict(size=11, color=MUTED),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=11),
        ),
        hovermode="x unified",
    )

    st.plotly_chart(
        fig,
        config={"displayModeBar": False},
    )

    # Mixed-units gentle warning
    if mixed:
        st.markdown(
            f"<div style='font-family:{FONT_BODY};font-size:10.5px;"
            f"color:{MUTED};margin-top:4px;padding:6px 10px;"
            f"background:#fef3c7;border-left:3px solid #d97706;'>"
            "Mixed scales selected — indexed 0-100 series and raw-count "
            "series share one y-axis. Visual comparison may be misleading; "
            "consider showing them separately."
            "</div>",
            unsafe_allow_html=True,
        )


# ─── Backward-compat alias ────────────────────────────────────────────
# Older code paths may import `render_line_chart`. Accept both names.
def render_line_chart(
    annual_data,
    default_series: Optional[list[str]] = None,
    height: int = 360,
    key: str = "line_chart",
) -> None:
    """Backward-compat wrapper for old API (list of dicts)."""
    # Convert list-of-dicts → dict-of-lists if needed
    if isinstance(annual_data, list):
        if not annual_data:
            st.info("No annual data available.")
            return
        keys = annual_data[0].keys()
        annual = {k: [r.get(k) for r in annual_data] for k in keys}
    else:
        annual = annual_data
    render_annual_line_chart(
        annual=annual,
        default_series=default_series,
        height=height,
        key=key,
    )


# ═════════════════════════════════════════════════════════════════════════
# Economic line chart — dual-axis (growth % left, FSI index right)
# + toggleable 17-sector growth lines
# ═════════════════════════════════════════════════════════════════════════
def render_economic_line_chart(
    annual: dict,
    height: int = 440,
    key: str = "economic_line",
) -> None:
    """National Economic line chart.

    Default lines: average GRDP growth (%) on the LEFT axis and FSI (0-100)
    on the RIGHT axis — two scales, so a dual axis keeps both readable.
    The 17 sector growth series can be toggled on via a multiselect; they
    share the left (%) axis with average growth.

    Parameters
    ----------
    annual : dict
        Output of load_national_economic_series():
        {years, default_series, series:{fsi,growth}, sectors:{<name>:{values}}}
    """
    if not annual or "years" not in annual:
        st.info("No annual economic data available.")
        return

    years = annual["years"]
    series = annual.get("series", {})
    sectors = annual.get("sectors", {})

    GROWTH_COLOR = "#0c447c"   # deep blue (headline series family)
    FSI_COLOR    = "#dc2626"   # red (flood context, matches Flood HCI tone)
    SECTOR_COLOR = "#9ca3af"   # muted grey for toggled sector lines

    # ── Sector toggle (off by default; growth + FSI shown by default) ────
    sel_sectors = st.multiselect(
        "Add sector growth lines",
        options=sorted(sectors.keys()),
        default=[],
        key=f"{key}_sectors",
        help="Overlay individual sector growth (%) on the left axis.",
    )

    fig = go.Figure()

    # growth (left axis)
    if "growth" in series:
        fig.add_trace(go.Scatter(
            x=years, y=series["growth"]["values"], mode="lines+markers",
            name="Avg GRDP growth (%)", line=dict(color=GROWTH_COLOR, width=2.5),
            marker=dict(size=5), yaxis="y1",
            hovertemplate="%{x}: %{y:.2f}%<extra>Avg growth</extra>",
        ))

    # FSI (right axis)
    if "fsi" in series:
        fig.add_trace(go.Scatter(
            x=years, y=series["fsi"]["values"], mode="lines+markers",
            name="FSI (0-100)", line=dict(color=FSI_COLOR, width=2.5, dash="dot"),
            marker=dict(size=5), yaxis="y2",
            hovertemplate="%{x}: %{y:.1f}<extra>FSI</extra>",
        ))

    # toggled sector lines (left axis, muted)
    for sec in sel_sectors:
        fig.add_trace(go.Scatter(
            x=years, y=sectors[sec]["values"], mode="lines",
            name=sec, line=dict(color=SECTOR_COLOR, width=1.2),
            opacity=0.8, yaxis="y1",
            hovertemplate="%{x}: %{y:.2f}%<extra>" + sec + "</extra>",
        ))

    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=10, b=0),
        font=dict(family=FONT_BODY, color="#1f2937"),
        xaxis=dict(title="", showgrid=False, dtick=1),
        yaxis=dict(title="Growth (%)", showgrid=True, gridcolor=HAIRLINE,
                   zeroline=True, zerolinecolor="#d1d5db"),
        yaxis2=dict(title="FSI (0-100)", overlaying="y", side="right",
                    showgrid=False, range=[0, max(series.get("fsi", {}).get("values", [100]) + [1]) * 1.2]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
    )

    st.plotly_chart(
        fig,
        key=key,
        config={"displayModeBar": False},
    )


# ═════════════════════════════════════════════════════════════════════════
# Sector impact bar chart — significant flood effects by sector × dimension
# (robust vs suggestive, diverging from 0) — from nb9b
# ═════════════════════════════════════════════════════════════════════════
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


# ═════════════════════════════════════════════════════════════════════════
# Province scatter — FSI vs growth per regency (descriptive, coloured)
# ═════════════════════════════════════════════════════════════════════════
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