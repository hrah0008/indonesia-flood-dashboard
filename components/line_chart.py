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


def render_economic_line_chart(
    annual: dict,
    height: int = 440,
    key: str = "economic_line",
) -> None:
    """National Economic line chart.

    A single multiselect ("Variables to display") controls every series —
    average GRDP growth (%), FSI (0-100), and the 17 sector growth lines —
    consistent with the Flood and Social line charts. Growth (left axis) and
    FSI (right axis) are shown by default; sectors are opt-in. Growth and the
    sector lines share the left (%) axis; FSI uses the right axis.

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

    # ── Unified option catalogue: headline (growth, FSI) + 17 sectors ────
    # key -> label, used by the single multiselect below.
    LABELS = {}
    if "growth" in series:
        LABELS["growth"] = "Avg GRDP growth (%)"
    if "fsi" in series:
        LABELS["fsi"] = "FSI (0-100)"
    for sec in sorted(sectors.keys()):
        LABELS[f"sector::{sec}"] = sec        # prefix avoids name clashes

    available = list(LABELS.keys())
    # default = headline series only (growth + FSI), sectors opt-in
    default_series = [k for k in ("growth", "fsi") if k in LABELS]

    # ── Single multiselect — matches Flood / Social ──────────────────────
    selected = st.multiselect(
        "Variables to display",
        options=available,
        default=default_series,
        format_func=lambda k: LABELS.get(k, k),
        key=key,
        label_visibility="collapsed",
        help=("Average GRDP growth (%) and the 17 sector growth lines share the "
              "left axis; FSI (0-100) uses the right axis. Growth + FSI shown by "
              "default; add sectors as needed."),
    )
    if not selected:
        st.info("Select at least one variable to display.")
        return

    fig = go.Figure()

    # growth (left axis)
    if "growth" in selected and "growth" in series:
        fig.add_trace(go.Scatter(
            x=years, y=series["growth"]["values"], mode="lines+markers",
            name="Avg GRDP growth (%)", line=dict(color=GROWTH_COLOR, width=2.5),
            marker=dict(size=5), yaxis="y1",
            hovertemplate="%{x}: %{y:.2f}%<extra>Avg growth</extra>",
        ))

    # FSI (right axis)
    if "fsi" in selected and "fsi" in series:
        fig.add_trace(go.Scatter(
            x=years, y=series["fsi"]["values"], mode="lines+markers",
            name="FSI (0-100)", line=dict(color=FSI_COLOR, width=2.5, dash="dot"),
            marker=dict(size=5), yaxis="y2",
            hovertemplate="%{x}: %{y:.1f}<extra>FSI</extra>",
        ))

    # toggled sector lines (left axis, muted)
    for k in selected:
        if not k.startswith("sector::"):
            continue
        sec = k.split("::", 1)[1]
        fig.add_trace(go.Scatter(
            x=years, y=sectors[sec]["values"], mode="lines",
            name=sec, line=dict(color=SECTOR_COLOR, width=1.2),
            opacity=0.8, yaxis="y1",
            hovertemplate="%{x}: %{y:.2f}%<extra>" + sec + "</extra>",
        ))

    show_y2 = "fsi" in selected
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=10, b=0),
        font=dict(family=FONT_BODY, color="#1f2937"),
        xaxis=dict(title="", showgrid=False,
                   tickmode="array", tickvals=list(years)),
        yaxis=dict(title="Growth (%)", showgrid=True, gridcolor=HAIRLINE,
                   zeroline=True, zerolinecolor="#d1d5db"),
        yaxis2=dict(title="FSI (0-100)", overlaying="y", side="right",
                    showgrid=False, visible=show_y2,
                    range=[0, max(series.get("fsi", {}).get("values", [100]) + [1]) * 1.2]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
    )

    st.plotly_chart(fig, key=f"{key}_fig", config={"displayModeBar": False})


def render_social_line_chart(annual: dict, height: int = 440,
                             key: str = "social_line") -> None:
    """National social trend: poverty% + unemployment% on the left axis,
    FSI (0-100) on the right axis, 2016-2025. From nb14 STEP 4 shape.

    A multiselect box above the chart lets the user choose which series to
    display (default: all three) — consistent with the Flood and Economic
    line charts. Series values follow the {"values": [...]} contract.
    """
    if not annual or "years" not in annual:
        st.info("No annual social data.")
        return
    years = annual["years"]
    series = annual.get("series", {})

    COLORS = {"poverty": "#a32d2d", "unemployment": "#b5651d", "fsi": "#185FA5"}
    LABELS = {"poverty": "Poverty rate", "unemployment": "Unemployment (TPT)",
              "fsi": "Flood Severity (FSI)"}
    AXIS   = {"poverty": "y", "unemployment": "y", "fsi": "y2"}

    # series actually present in the data
    available = [k for k in ["poverty", "unemployment", "fsi"] if k in series]
    default_series = annual.get("default_series", available)

    # ── UI — multiselect with sensible defaults (matches Flood/Economic) ──
    selected = st.multiselect(
        "Variables to display",
        options=available,
        default=[s for s in default_series if s in available],
        format_func=lambda k: LABELS.get(k, k),
        key=key,
        label_visibility="collapsed",
        help=("Poverty & unemployment are point-% (left axis); FSI is the "
              "flood-severity index 0-100 (right axis). Descriptive national "
              "means, not a controlled relationship."),
    )
    if not selected:
        st.info("Select at least one variable to display.")
        return

    fig = go.Figure()
    for kk in selected:
        vals = series[kk]["values"]
        is_fsi = kk == "fsi"
        unit = "/100" if is_fsi else "%"
        fig.add_trace(go.Scatter(
            x=years, y=vals, mode="lines+markers",
            name=LABELS[kk], yaxis=AXIS[kk],
            line=dict(color=COLORS[kk], width=2.5, dash="dot" if is_fsi else "solid"),
            marker=dict(size=6),
            hovertemplate=f"%{{x}}<br>{LABELS[kk]}: %{{y:.2f}}{unit}<extra></extra>",
        ))

    show_y2 = "fsi" in selected
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=10, b=0),
        font=dict(family=FONT_BODY, color="#1f2937", size=12),
        xaxis=dict(title="", showgrid=False, tickmode="array", tickvals=list(years)),
        yaxis=dict(title="Poverty / Unemployment (%)", showgrid=True,
                   gridcolor=HAIRLINE, side="left"),
        yaxis2=dict(title="FSI (0-100)", overlaying="y", side="right",
                    showgrid=False, visible=show_y2),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
    )
    st.plotly_chart(fig, key=f"{key}_fig", config={"displayModeBar": False})
