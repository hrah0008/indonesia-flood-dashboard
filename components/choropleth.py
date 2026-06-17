"""
components/choropleth.py
========================
Dual-layer flood severity map using Plotly Mapbox:

  Layer 1 — Cluster typology (polygon fill, K-means A3 clusters)
    Colors:
      • Low Impact          → teal   (#9FE1CB)
      • Catastrophic        → red    (#F7C1C1)
      • Frequent-Contained  → amber  (#FAC775)

  Layer 2 — FSI severity (dot overlay, sqrt-scale size)
    Encoding:
      • Position: regency centroid (lat, lon)
      • Size:     sqrt scaling, radius range ~1.5-13 px
      • Color:    solid blue #185FA5 with opacity 0.75

Both layers are independently toggleable via the `show_cluster` and
`show_fsi_dots` parameters. Defaults: both ON.

HOVER STRUCTURE (3-tier causal chain) — PRESERVED FROM ORIGINAL
---------------------------------------------------------------
The hover tells the FSI methodology story:
  1. Cluster typology + FSI Score (0–100, A3 cluster-weighted composite)
       ↑ derived from
  2. Z-scored dimensions (Z_freq, Z_HCI, Z_PDI)
       ↑ Z-scoring of
  3. Raw counts (events, casualties, houses)

NOTE: FSI_tier was dropped upstream (nb12). The hover now reports the
FSI number (FSI_index, 0–100 continuous) directly instead of a
categorical tier label. No FSI_tier column is referenced anywhere.

REQUIRED COLUMNS IN reg_df
--------------------------
  Required (always):
    kemendagri_kab_code, FSI_index (or FSI_percent alias)
  Required for cluster layer (show_cluster=True):
    cluster_a3 (int 0/1/2), cluster_label (str)
  Required for FSI dot layer (show_fsi_dots=True):
    centroid_lat, centroid_lon
  Optional (used in hover when present):
    kemendagri_kab_name, kemendagri_prov_name,
    Z_freq, Z_HCI, Z_PDI,
    event_count, deaths, missing, injured, house_flooded, house_damaged
"""

from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Defensive import — fall back to hardcoded values if lib.colors lacks them
from lib.colors import (
    MUTED, FONT_BODY, INK,
    CLUSTER_COLORS, CLUSTER_BORDERS, CLUSTER_ORDER, CLUSTER_DESCRIPTIONS,
)


# Cluster palette (CLUSTER_COLORS, CLUSTER_BORDERS), order, and descriptions
# are all imported from lib/colors.py — single source of truth.

# ── FSI dot encoding ──────────────────────────────────────────────────────
FSI_DOT_COLOR   = "#185FA5"  # solid blue, contrasts with all 3 cluster colors
FSI_DOT_OPACITY = 0.6
FSI_DOT_MIN_R   = 1.5        # minimum radius (px) for FSI=0
FSI_DOT_MAX_R   = 13         # maximum radius (px) for FSI=100 (was 22 — too large at national zoom)


# ── Economic growth choropleth palette ────────────────────────────────────
# DIVERGING red → white → green, using the Flood family's red (#dc2626,
# "Catastrophic") and green (#84cc16 / #3b6d11, "Low Impact"/"Improving").
# Growth has BOTH negative and positive values, so a diverging scale is the
# correct encoding (sequential would hide the sign). White is pinned to
# growth = 0 via zmid=0 in the trace (NOT the midpoint of the data range),
# so red = shrinking economy, white = flat, green = growing.
GROWTH_COLORSCALE = [
    [0.00, "#a32d2d"],   # deep red    — strong contraction
    [0.25, "#e8908f"],   # soft red
    [0.50, "#ffffff"],   # white       — pinned to 0% via zmid=0
    [0.75, "#9fce6a"],   # soft green
    [1.00, "#3b6d11"],   # deep green  — strong growth (Flood "Improving" green)
]


# ═════════════════════════════════════════════════════════════════════════
# Internal helpers
# ═════════════════════════════════════════════════════════════════════════
def _prepare_dataframe(reg_df: pd.DataFrame, geojson: dict = None) -> pd.DataFrame:
    """Align kemendagri_kab_code type with geojson + fill missing optional cols.

    CRITICAL: Plotly's featureidkey matching requires EXACT type match
    between reg_df['kemendagri_kab_code'] and geojson properties.
    """
    df = reg_df.copy()

    if "kemendagri_kab_code" in df.columns:
        # Match type with geojson properties.kemendagri_kab_code
        if geojson and geojson.get("features"):
            sample = geojson["features"][0].get("properties", {}).get("kemendagri_kab_code")
            if isinstance(sample, int):
                df["kemendagri_kab_code"] = df["kemendagri_kab_code"].astype(int)
            else:
                df["kemendagri_kab_code"] = df["kemendagri_kab_code"].astype(str)
        else:
            df["kemendagri_kab_code"] = df["kemendagri_kab_code"].astype(str)

    # FSI number — canonical column from nb12 is FSI_index; accept FSI_percent
    # alias. Guarantee an FSI_index column exists so downstream code is simple.
    if "FSI_index" not in df.columns:
        if "FSI_percent" in df.columns:
            df["FSI_index"] = df["FSI_percent"]
        else:
            df["FSI_index"] = np.nan
    df["FSI_index"] = pd.to_numeric(df["FSI_index"], errors="coerce")

    for c in ["Z_freq", "Z_HCI", "Z_PDI"]:
        if c not in df.columns:
            df[c] = 0.0
        else:
            df[c] = df[c].fillna(0.0)

    if "kemendagri_prov_name" not in df.columns:
        df["kemendagri_prov_name"] = ""

    if "house_damaged" not in df.columns:
        df["house_damaged"] = 0

    # Cluster columns — required for cluster layer; default sentinel
    if "cluster_label" not in df.columns:
        df["cluster_label"] = "Unknown"
    if "cluster_a3" not in df.columns:
        df["cluster_a3"] = -1

    # Centroid columns — required for FSI dot layer
    for c in ["centroid_lat", "centroid_lon"]:
        if c not in df.columns:
            df[c] = np.nan

    return df


def _compute_dot_sizes(fsi_index: pd.Series) -> np.ndarray:
    """Map FSI_index (0-100) → marker radius (px) using sqrt scaling.

    sqrt scaling balances linear and log:
      FSI=0   → r=2
      FSI=25  → r=12
      FSI=50  → r=16
      FSI=100 → r=22
    """
    fsi = fsi_index.fillna(0).clip(0, 100) / 100.0
    return FSI_DOT_MIN_R + (FSI_DOT_MAX_R - FSI_DOT_MIN_R) * np.sqrt(fsi)


def _build_cluster_colorscale() -> list:
    """Build discrete Plotly colorscale mapping cluster index → fill color.

    Returns list of [position, color] pairs in Plotly colorscale format.
    """
    n = len(CLUSTER_ORDER)
    colorscale = []
    for i, label in enumerate(CLUSTER_ORDER):
        lo = i / n
        hi = (i + 1) / n
        col = CLUSTER_COLORS[label]
        colorscale.append([lo, col])
        colorscale.append([hi, col])
    return colorscale


# ═════════════════════════════════════════════════════════════════════════
# Main render function
# ═════════════════════════════════════════════════════════════════════════
def render_fsi_choropleth(
    reg_df: pd.DataFrame,
    geojson: dict,
    height: int = 520,
    key: Optional[str] = None,
    on_select: Optional[str] = None,
    mapbox_zoom: float = 4.0,
    mapbox_center: Optional[dict] = None,
    show_cluster: bool = True,
    show_fsi_dots: bool = True,
):
    """
    Render a dual-layer map: cluster typology + FSI severity dots.

    Parameters
    ----------
    reg_df : pd.DataFrame
        Regency rows. See REQUIRED COLUMNS in module docstring.
    geojson : dict
        GeoJSON FeatureCollection with properties.kemendagri_kab_code.
    height : int
        Pixel height of the map.
    key : str
        Streamlit widget key — required when on_select is set.
    on_select : str | None
        Pass "rerun" to enable click selection (Plotly on_select API).
    mapbox_zoom : float
        Initial zoom level. 4.0 = whole Indonesia.
    mapbox_center : dict | None
        Override map center {"lat": ..., "lon": ...}.
    show_cluster : bool
        Render the K-means cluster choropleth layer (default True).
    show_fsi_dots : bool
        Render the FSI severity dot overlay (default True).
    """
    df = _prepare_dataframe(reg_df, geojson=geojson)
    fig = go.Figure()

    # ─── Layer 1: K-means cluster choropleth ─────────────────────────────
    if show_cluster:
        label_to_idx = {lbl: i for i, lbl in enumerate(CLUSTER_ORDER)}
        df["_cluster_idx"] = (
            df["cluster_label"].map(label_to_idx).fillna(-1).astype(int)
        )

        cluster_df = df[df["_cluster_idx"] >= 0].copy()

        if len(cluster_df) > 0:
            colorscale = _build_cluster_colorscale()
            n_clusters = len(CLUSTER_ORDER)

            # Customdata — 13 fields + cluster_label (index 13).
            # FSI_tier removed: hover now reports FSI_index number directly.
            cluster_customdata = np.column_stack([
                cluster_df[
                    ["kemendagri_kab_name", "kemendagri_prov_name",
                     "FSI_index",
                     "Z_freq", "Z_HCI", "Z_PDI",
                     "event_count", "deaths", "missing", "injured",
                     "house_flooded", "house_damaged",
                     "kemendagri_kab_code"]
                ].values,
                cluster_df["cluster_label"].values  # index 13
            ])

            cluster_hover = (
                "<b>%{customdata[0]}</b><br>"
                "<span style='color:#888'>%{customdata[1]}</span><br>"
                "Cluster: <b>%{customdata[13]}</b><br>"
                "FSI Score: <b>%{customdata[2]:.2f} / 100</b><br>"
                "<span style='color:#666;font-size:10.5px;'>"
                "Z-scored dimensions:</span><br>"
                "<span style='color:#444'>Freq:</span> %{customdata[3]:+.2f} · "
                "<span style='color:#444'>HCI:</span> %{customdata[4]:+.2f} · "
                "<span style='color:#444'>PDI:</span> %{customdata[5]:+.2f}<br>"
                "<span style='color:#666;font-size:10.5px;'>"
                "Cumulative 2016–2025:</span><br>"
                "<span style='color:#444'>Events:</span> %{customdata[6]:,}<br>"
                "<span style='color:#444'>Human cost:</span> "
                "%{customdata[7]:,} dead · %{customdata[8]:,} missing · "
                "%{customdata[9]:,} injured<br>"
                "<span style='color:#444'>Houses:</span> "
                "%{customdata[10]:,} flooded · %{customdata[11]:,} damaged"
                "<extra></extra>"
            )

            fig.add_trace(go.Choroplethmapbox(
                geojson=geojson,
                locations=cluster_df["kemendagri_kab_code"],
                featureidkey="properties.kemendagri_kab_code",
                z=cluster_df["_cluster_idx"],
                zmin=0,
                zmax=n_clusters - 1,
                colorscale=colorscale,
                marker=dict(
                    line=dict(width=0.3, color="rgba(255,255,255,0.7)"),
                    opacity=0.75
                ),
                customdata=cluster_customdata,
                hovertemplate=cluster_hover,
                showscale=False,
                name="Cluster typology",
            ))

    # ─── Layer 2: FSI severity dot overlay ───────────────────────────────
    if show_fsi_dots:
        dot_df = df.dropna(subset=["centroid_lat", "centroid_lon"]).copy()
        # Drop sentinel (0,0) centroids
        dot_df = dot_df[
            (dot_df["centroid_lat"] != 0) | (dot_df["centroid_lon"] != 0)
        ]

        if len(dot_df) > 0:
            dot_sizes = _compute_dot_sizes(dot_df["FSI_index"])

            # FSI_tier removed: hover reports FSI_index number directly.
            dot_customdata = dot_df[
                ["kemendagri_kab_name", "kemendagri_prov_name",
                 "FSI_index",
                 "cluster_label",
                 "event_count", "deaths"]
            ].values

            dot_hover = (
                "<b>%{customdata[0]}</b><br>"
                "<span style='color:#888'>%{customdata[1]}</span><br>"
                "FSI: <b>%{customdata[2]:.2f} / 100</b><br>"
                "<span style='color:#666'>Cluster: %{customdata[3]}</span><br>"
                "<span style='color:#666'>Events: %{customdata[4]:,} · "
                "Deaths: %{customdata[5]:,}</span>"
                "<extra></extra>"
            )

            fig.add_trace(go.Scattermapbox(
                lat=dot_df["centroid_lat"],
                lon=dot_df["centroid_lon"],
                mode="markers",
                marker=dict(
                    size=dot_sizes,
                    color=FSI_DOT_COLOR,
                    opacity=FSI_DOT_OPACITY,
                    sizemode="diameter",
                ),
                customdata=dot_customdata,
                hovertemplate=dot_hover,
                hoverlabel=dict(bgcolor="white"),
                name="FSI severity",
            ))

    # ─── Layout ──────────────────────────────────────────────────────────
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=mapbox_zoom,
        mapbox_center=mapbox_center or {"lat": -2.5, "lon": 117.5},
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        showlegend=False,
        font=dict(family=FONT_BODY, size=11, color="#1f2937"),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#e5e7eb",
            font=dict(family=FONT_BODY, size=12, color="#1f2937"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # ─── Render via Streamlit + custom legend ────────────────────────────
    if on_select:
        event = st.plotly_chart(
            fig,
            key=key,
            on_select=on_select,
            selection_mode="points",
            config={"displayModeBar": False, "scrollZoom": True},
        )
        # Legend is now rendered separately by caller via render_legend()
        # to allow flexible positioning (right column, below map, etc).
        return event
    else:
        st.plotly_chart(
            fig,
            key=key,
            config={"displayModeBar": False, "scrollZoom": True},
        )
        return None


# ═════════════════════════════════════════════════════════════════════════
# Custom legend
# ═════════════════════════════════════════════════════════════════════════
def render_legend(
    show_cluster: bool = True,
    show_fsi_dots: bool = True,
    cluster_counts: dict = None,
    layout: str = "horizontal",
) -> None:
    """Render legend for cluster typology + FSI dot size scale.

    Public API: can be called from Streamlit page (e.g., 1_Flood.py)
    to render legend in any column/position.

    Parameters
    ----------
    show_cluster : bool
        Show cluster typology section
    show_fsi_dots : bool
        Show FSI dot size scale section
    cluster_counts : dict | None
        Optional dict of {label: count} to show n=XXX per cluster
    layout : str
        "horizontal" — 3-column grid (for full-width below map)
        "vertical"   — stacked single column (for narrow right column)
    """
    sections_html = []

    if show_cluster:
        total_n = sum(cluster_counts.values()) if cluster_counts else None

        # Build cluster cells (same for both layouts, just different grid)
        cluster_cells = []
        for lbl in CLUSTER_ORDER:
            count_str = (f" <span style='color:{MUTED};font-size:10.5px;'>"
                         f"(n={cluster_counts[lbl]})</span>"
                         if cluster_counts and lbl in cluster_counts else "")
            desc = CLUSTER_DESCRIPTIONS.get(lbl, "")
            cluster_cells.append(
                f"<div style='margin-bottom:5px;'>"
                f"  <div style='display:flex;align-items:center;gap:7px;margin-bottom:1px;'>"
                f"    <span style='display:inline-block;width:13px;height:13px;"
                f"border-radius:3px;background:{CLUSTER_COLORS[lbl]};"
                f"border:0.5px solid {CLUSTER_BORDERS[lbl]};flex-shrink:0;'></span>"
                f"    <span style='font-family:{FONT_BODY};font-size:12px;"
                f"font-weight:500;color:#1f2937;'>{lbl}</span>"
                f"    {count_str}"
                f"  </div>"
                f"  <div style='font-family:{FONT_BODY};font-size:10.5px;"
                f"color:{MUTED};padding-left:20px;line-height:1.3;'>{desc}</div>"
                f"</div>"
            )

        header_total = (f" — {total_n} regencies" if total_n else "")

        # Layout: 3-column grid (horizontal) or stacked column (vertical)
        if layout == "vertical":
            cells_wrapper = f"<div>{''.join(cluster_cells)}</div>"
        else:  # horizontal
            cells_wrapper = (
                f"<div style='display:grid;grid-template-columns:repeat(3,1fr);"
                f"gap:14px;'>{''.join(cluster_cells)}</div>"
            )

        sections_html.append(
            f"<div style='margin-bottom:10px;'>"
            f"<div style='font-family:{FONT_BODY};font-size:10.5px;color:{MUTED};"
            f"text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;'>"
            f"Cluster typology{header_total}:</div>"
            f"{cells_wrapper}"
            f"</div>"
        )

    if show_fsi_dots:
        dot_scale_svg = (
            "<svg width='180' height='28' style='vertical-align:middle;'>"
            f"<circle cx='12'  cy='14' r='3'  fill='{FSI_DOT_COLOR}' opacity='{FSI_DOT_OPACITY}'/>"
            f"<circle cx='52'  cy='14' r='7'  fill='{FSI_DOT_COLOR}' opacity='{FSI_DOT_OPACITY}'/>"
            f"<circle cx='100' cy='14' r='11' fill='{FSI_DOT_COLOR}' opacity='{FSI_DOT_OPACITY}'/>"
            f"<circle cx='158' cy='14' r='15' fill='{FSI_DOT_COLOR}' opacity='{FSI_DOT_OPACITY}'/>"
            "</svg>"
        )
        sections_html.append(
            f"<div style='display:inline-flex;align-items:center;gap:10px;"
            f"margin-top:2px;'>"
            f"<span style='color:{MUTED};font-size:10.5px;'>FSI severity:</span>"
            f"{dot_scale_svg}"
            f"<span style='color:{MUTED};font-size:10.5px;'>low → high</span>"
            f"</div>"
        )

    if sections_html:
        # Vertical layout (narrow side column) can be taller than the map and
        # get clipped — cap height and allow internal scroll so every cluster
        # (incl. Low Impact) and the dot scale stay reachable. Horizontal
        # layout (full-width, below map) needs no constraint.
        if layout == "vertical":
            wrapper_style = (
                "margin-top:8px;max-height:460px;overflow-y:auto;"
                "padding-right:4px;"
            )
        else:
            wrapper_style = "margin-top:8px;"

        st.markdown(
            f"<div style='{wrapper_style}'>"
            + "".join(sections_html)
            + "</div>",
            unsafe_allow_html=True,
        )


# ═════════════════════════════════════════════════════════════════════════
# Province-view helper (PRESERVED FROM ORIGINAL — unchanged)
# ═════════════════════════════════════════════════════════════════════════
def compute_province_view(
    reg_df: pd.DataFrame,
    geojson: dict,
    padding: float = 0.10,
) -> tuple[dict, float]:
    """Compute mapbox center + zoom that fits the bounding box of all
    regencies present in reg_df. Used to zoom the choropleth into a
    single province. Returns (center_dict, zoom_float).
    """
    kab_codes = set(reg_df["kemendagri_kab_code"].astype(str).values)
    lats, lons = [], []
    for feat in geojson.get("features", []):
        props = feat.get("properties", {})
        if str(props.get("kemendagri_kab_code")) not in kab_codes:
            continue
        geom = feat.get("geometry", {})
        coords = geom.get("coordinates", [])
        gtype = geom.get("type", "")
        if gtype == "Polygon":
            for ring in coords:
                for coord in ring:
                    # GeoJSON positions may carry a 3rd value (elevation/Z);
                    # take only lon/lat. Plain `for lon, lat in ring` raises
                    # "too many values to unpack" on [lon, lat, z] coords.
                    lon, lat = coord[0], coord[1]
                    lats.append(lat)
                    lons.append(lon)
        elif gtype == "MultiPolygon":
            for poly in coords:
                for ring in poly:
                    for coord in ring:
                        lon, lat = coord[0], coord[1]
                        lats.append(lat)
                        lons.append(lon)

    if not lats:
        return {"lat": -2.5, "lon": 117.5}, 4.0

    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)
    lat_center = (lat_min + lat_max) / 2
    lon_center = (lon_min + lon_max) / 2

    lat_span = (lat_max - lat_min) * (1 + padding)
    lon_span = (lon_max - lon_min) * (1 + padding)
    max_span = max(lat_span, lon_span, 0.01)
    import math
    zoom = max(4.0, min(9.0, math.log2(30.0 / max_span) + 4.0))

    return {"lat": lat_center, "lon": lon_center}, zoom

# ═════════════════════════════════════════════════════════════════════════
# Economic menu — growth saturation choropleth + FSI bubble overlay
# ═════════════════════════════════════════════════════════════════════════
def render_economic_choropleth(
    reg_df: pd.DataFrame,
    geojson: dict,
    height: int = 520,
    key: Optional[str] = None,
    mapbox_zoom: float = 4.0,
    mapbox_center: Optional[dict] = None,
    show_growth: bool = True,
    show_fsi_dots: bool = True,
):
    """Economic map: GRDP growth as continuous colour saturation + FSI bubbles.

    Mirrors the Flood map's two-layer feel and reuses the SAME blue family
    (GROWTH_COLORSCALE ends on the FSI-dot blue #185FA5) so the two menus look
    consistent. The polygon layer is a CONTINUOUS economic variable (growth),
    not the K-means cluster typology.

    Required columns in reg_df:
        kemendagri_kab_code, growth_avg          (polygon layer)
        FSI_index, centroid_lat, centroid_lon    (bubble layer)
    Optional (hover):
        kemendagri_kab_name, kemendagri_prov_name
    """
    df = reg_df.copy()
    df["kemendagri_kab_code"] = df["kemendagri_kab_code"].astype(str)

    fig = go.Figure()

    # ─── Layer 1: growth saturation choropleth ───────────────────────────
    if show_growth:
        cd = np.column_stack([
            df.get("kemendagri_kab_name", pd.Series([""] * len(df))).values,
            df.get("kemendagri_prov_name", pd.Series([""] * len(df))).values,
            df["growth_avg"].values,
        ])
        hover = (
            "<b>%{customdata[0]}</b><br>"
            "<span style='color:#888'>%{customdata[1]}</span><br>"
            "Avg growth 2016-2025: <b>%{customdata[2]:.2f}%</b>"
            "<extra></extra>"
        )
        fig.add_trace(go.Choroplethmapbox(
            geojson=geojson,
            locations=df["kemendagri_kab_code"],
            z=df["growth_avg"],
            featureidkey="properties.kemendagri_kab_code",
            colorscale=GROWTH_COLORSCALE,
            zmid=0,                      # pin white to 0% growth (diverging)
            marker_opacity=0.85,
            marker_line_width=0.3,
            marker_line_color="#ffffff",
            showscale=False,             # no in-map colorbar; the custom legend
                                         # below the checkboxes is the key (mirrors Flood)
            customdata=cd,
            hovertemplate=hover,
            name="Growth",
        ))

    # ─── Layer 2: FSI bubble overlay (identical styling to Flood map) ────
    if show_fsi_dots and {"centroid_lat", "centroid_lon", "FSI_index"}.issubset(df.columns):
        dots = df.dropna(subset=["centroid_lat", "centroid_lon", "FSI_index"]).copy()
        if len(dots) > 0:
            sizes = _compute_dot_sizes(dots["FSI_index"])
            dot_cd = np.column_stack([
                dots.get("kemendagri_kab_name", pd.Series([""] * len(dots))).values,
                dots["FSI_index"].values,
            ])
            fig.add_trace(go.Scattermapbox(
                lat=dots["centroid_lat"],
                lon=dots["centroid_lon"],
                mode="markers",
                marker=dict(size=sizes, color=FSI_DOT_COLOR, opacity=FSI_DOT_OPACITY),
                customdata=dot_cd,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "FSI: <b>%{customdata[1]:.1f} / 100</b>"
                    "<extra></extra>"
                ),
                name="FSI",
            ))

    # ─── Layout (match Flood map) ────────────────────────────────────────
    center = mapbox_center or {"lat": -2.5, "lon": 118.0}
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=mapbox_zoom,
        mapbox_center=center,
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        font=dict(family=FONT_BODY, color=INK),
    )

    st.plotly_chart(
        fig,
        key=key,
        config={"displayModeBar": False, "scrollZoom": True},
    )



# ═════════════════════════════════════════════════════════════════════════
# Economic legend — growth saturation gradient + FSI dot-size scale
# ═════════════════════════════════════════════════════════════════════════
def render_economic_legend(
    show_growth: bool = True,
    show_fsi_dots: bool = True,
    growth_min: float = None,
    growth_max: float = None,
    layout: str = "vertical",
) -> None:
    """Legend for the Economic choropleth: growth diverging gradient + FSI dots.

    Mirrors render_legend() (Flood) but the polygon section is a CONTINUOUS
    growth gradient (red→white→green), not the cluster typology.

    Parameters
    ----------
    show_growth : bool       show the growth gradient bar
    show_fsi_dots : bool     show the FSI dot-size scale
    growth_min, growth_max : float | None
        Optional data range to annotate the gradient ends (e.g. -1.3% .. +12.4%).
    layout : str             "vertical" (narrow column) or "horizontal".
    """
    sections_html = []

    if show_growth:
        # gradient bar built from the same stops as GROWTH_COLORSCALE
        stops = ", ".join(f"{c} {int(p*100)}%" for p, c in GROWTH_COLORSCALE)
        lo = f"{growth_min:+.1f}%" if growth_min is not None else "lower"
        hi = f"{growth_max:+.1f}%" if growth_max is not None else "higher"
        bar = (
            f"<div style='height:12px;width:180px;border-radius:3px;"
            f"background:linear-gradient(to right, {stops});"
            f"border:0.5px solid #d1d5db;'></div>"
        )
        sections_html.append(
            f"<div style='margin-bottom:10px;'>"
            f"<div style='font-family:{FONT_BODY};font-size:10.5px;color:{MUTED};"
            f"text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;'>"
            f"GRDP growth (avg 2016-2025):</div>"
            f"{bar}"
            f"<div style='display:flex;justify-content:space-between;width:180px;"
            f"font-family:{FONT_BODY};font-size:10px;color:{MUTED};margin-top:2px;'>"
            f"<span>{lo}</span><span>0%</span><span>{hi}</span></div>"
            f"<div style='font-family:{FONT_BODY};font-size:10px;color:{MUTED};"
            f"margin-top:3px;'>red = contracting · white = flat · green = growing</div>"
            f"</div>"
        )

    if show_fsi_dots:
        dot_scale_svg = (
            "<svg width='180' height='28' style='vertical-align:middle;'>"
            f"<circle cx='12'  cy='14' r='3'  fill='{FSI_DOT_COLOR}' opacity='{FSI_DOT_OPACITY}'/>"
            f"<circle cx='52'  cy='14' r='7'  fill='{FSI_DOT_COLOR}' opacity='{FSI_DOT_OPACITY}'/>"
            f"<circle cx='100' cy='14' r='11' fill='{FSI_DOT_COLOR}' opacity='{FSI_DOT_OPACITY}'/>"
            f"<circle cx='158' cy='14' r='15' fill='{FSI_DOT_COLOR}' opacity='{FSI_DOT_OPACITY}'/>"
            "</svg>"
        )
        sections_html.append(
            f"<div style='display:inline-flex;align-items:center;gap:10px;margin-top:2px;'>"
            f"<span style='color:{MUTED};font-size:10.5px;'>FSI severity:</span>"
            f"{dot_scale_svg}"
            f"<span style='color:{MUTED};font-size:10.5px;'>low → high</span>"
            f"</div>"
        )

    if sections_html:
        wrapper = ("margin-top:8px;max-height:460px;overflow-y:auto;padding-right:4px;"
                   if layout == "vertical" else "margin-top:8px;")
        st.markdown(f"<div style='{wrapper}'>" + "".join(sections_html) + "</div>",
                    unsafe_allow_html=True)