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
