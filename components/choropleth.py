"""
components/choropleth.py
========================
Plotly Mapbox choropleth — Indonesian regencies coloured by FSI tier.

HOVER STRUCTURE (3-tier causal chain)
-------------------------------------
The hover tells the FSI methodology story in three layers:

  1. FSI Score (0–100, cluster-weighted composite)
       ↑ derived from
  2. Z-scored dimensions (Z_freq, Z_HCI, Z_PDI)
       ↑ Z-scoring of
  3. Raw counts (events, casualties, houses)

This is what makes the cluster-weighted FSI methodology legible — a reader
can verify why a regency scores what it does, not just see the composite
number. HCI and PDI are visible HERE (not as final-form indices but as
their Z-scored dimension counterparts) which is the empirical basis for
the cluster-weighted methodology.

DISPLAY NOTE
------------
FSI Score is on a 0–100 scale (min-max rescaling), NOT a percentage.
Hover uses "X.XX / 100" to make the relative-score nature explicit.
"""

from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.colors import FSI_COLORS, FSI_TIER_ORDER, MUTED, FONT_BODY


def _prepare_dataframe(reg_df: pd.DataFrame) -> pd.DataFrame:
    """Cast key to string so it matches GeoJSON feature.properties.

    Gracefully handles missing columns when reg_df comes from the
    province-level regency_table.parquet (which has a thinner schema
    than the national table — no Z-dimensions, no prov_name, etc.).
    """
    df = reg_df.copy()
    if "kemendagri_kab_code" in df.columns:
        df["kemendagri_kab_code"] = df["kemendagri_kab_code"].astype(str)
    # Fill Z-dimensions with 0 if missing (graceful degradation for
    # legacy parquets that don't have them yet, AND for province scope)
    for c in ["Z_freq", "Z_HCI", "Z_PDI"]:
        if c not in df.columns:
            df[c] = 0.0
        else:
            df[c] = df[c].fillna(0.0)
    # Fill prov_name (national has it; province scope often doesn't)
    if "kemendagri_prov_name" not in df.columns:
        df["kemendagri_prov_name"] = ""
    # Fill house_damaged (national has it; province parquet doesn't)
    if "house_damaged" not in df.columns:
        df["house_damaged"] = 0
    return df


def render_fsi_choropleth(
    reg_df: pd.DataFrame,
    geojson: dict,
    height: int = 520,
    key: Optional[str] = None,
    on_select: Optional[str] = None,
    mapbox_zoom: float = 4.0,
    mapbox_center: Optional[dict] = None,
):
    """
    Render an FSI-tier choropleth of regencies.

    Parameters
    ----------
    reg_df : pd.DataFrame
        Regency rows with at least: kemendagri_kab_code, FSI_tier, FSI_index,
        event_count, deaths, missing, injured, house_flooded. Other columns
        (Z_freq, Z_HCI, Z_PDI, kemendagri_prov_name, house_damaged) are
        used in hover if present; gracefully filled with defaults otherwise.
    geojson : dict
        GeoJSON FeatureCollection. Features must have
        properties.kemendagri_kab_code matching reg_df values.
    height : int
        Pixel height of the map.
    key : str
        Streamlit widget key — required when on_select is set.
    on_select : str | None
        Pass "rerun" to enable click selection. Streamlit's native plotly
        on_select API (1.35+). When set, function returns the event so
        the caller can read event.selection.points.
    mapbox_zoom : float
        Initial zoom level. 4.0 = whole Indonesia (default).
        ~6.5 for a single province like Jawa Tengah.
    mapbox_center : dict | None
        Override map center {"lat": ..., "lon": ...}. Defaults to
        Indonesia centroid.
    """
    df = _prepare_dataframe(reg_df)

    tier_to_idx = {t: i for i, t in enumerate(reversed(FSI_TIER_ORDER))}
    df["_tier_idx"] = df["FSI_tier"].map(tier_to_idx).fillna(0).astype(int)

    n = len(FSI_TIER_ORDER)
    ordered_colors = [FSI_COLORS[t] for t in reversed(FSI_TIER_ORDER)]
    colorscale = []
    for i, color in enumerate(ordered_colors):
        lo = i / n
        hi = (i + 1) / n
        colorscale.append([lo, color])
        colorscale.append([hi, color])

    # Customdata layout (3-tier hover — see module docstring):
    #   0: kab_name           1: prov_name
    #   2: FSI_index        3: FSI_tier
    #   4: Z_freq             5: Z_HCI            6: Z_PDI
    #   7: event_count        8: deaths           9: missing
    #  10: injured           11: house_flooded   12: house_damaged
    #  13: kab_code           ← appended for click handler payload
    customdata = df[
        ["kemendagri_kab_name", "kemendagri_prov_name",
         "FSI_index", "FSI_tier",
         "Z_freq", "Z_HCI", "Z_PDI",
         "event_count", "deaths", "missing", "injured",
         "house_flooded", "house_damaged",
         "kemendagri_kab_code"]
    ].values

    # Hover template — 3 tiers separated by visual section labels.
    # Use raw · (Unicode middot) NOT &middot; — Plotly does not decode
    # HTML entities in hovertemplate.
    hovertemplate = (
        "<b>%{customdata[0]}</b><br>"
        "<span style='color:#888'>%{customdata[1]}</span><br>"
        # Tier 1: composite FSI Score
        "FSI Score: <b>%{customdata[2]:.2f} / 100</b> · %{customdata[3]}<br>"
        # Tier 2: Z-scored dimensions (the FSI building blocks)
        "<span style='color:#666;font-size:10.5px;'>"
        "Z-scored dimensions:</span><br>"
        "<span style='color:#444'>Freq:</span> %{customdata[4]:+.2f} · "
        "<span style='color:#444'>HCI:</span> %{customdata[5]:+.2f} · "
        "<span style='color:#444'>PDI:</span> %{customdata[6]:+.2f}<br>"
        # Tier 3: raw counts (cumulative 2016-2025)
        "<span style='color:#666;font-size:10.5px;'>"
        "Cumulative 2016–2025:</span><br>"
        "<span style='color:#444'>Events:</span> %{customdata[7]:,}<br>"
        "<span style='color:#444'>Human cost:</span> "
        "%{customdata[8]:,} dead · %{customdata[9]:,} missing · "
        "%{customdata[10]:,} injured<br>"
        "<span style='color:#444'>Houses:</span> "
        "%{customdata[11]:,} flooded · %{customdata[12]:,} damaged"
        "<extra></extra>"
    )

    fig = go.Figure(
        go.Choroplethmapbox(
            geojson=geojson,
            locations=df["kemendagri_kab_code"],
            featureidkey="properties.kemendagri_kab_code",
            z=df["_tier_idx"],
            zmin=0,
            zmax=n - 1,
            colorscale=colorscale,
            marker=dict(line=dict(width=0.3, color="rgba(255,255,255,0.6)")),
            customdata=customdata,
            hovertemplate=hovertemplate,
            showscale=False,
        )
    )

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=mapbox_zoom,
        mapbox_center=mapbox_center or {"lat": -2.5, "lon": 117.5},
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        font=dict(family=FONT_BODY, size=11, color="#1f2937"),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#e5e7eb",
            font=dict(family=FONT_BODY, size=12, color="#1f2937"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # Two render paths: with or without click selection.
    # NOTE on `width`: in Streamlit 1.50+, passing `width="stretch"` triggers
    # a (false-positive) kwargs deprecation warning. `stretch` is the default
    # behavior, so we just omit the parameter.
    if on_select:
        event = st.plotly_chart(
            fig,
            key=key,
            on_select=on_select,
            selection_mode="points",
            config={"displayModeBar": False, "scrollZoom": True},
        )
        _render_tier_legend()
        return event
    else:
        st.plotly_chart(
            fig,
            key=key,
            config={"displayModeBar": False, "scrollZoom": True},
        )
        _render_tier_legend()
        return None


def _render_tier_legend() -> None:
    """Compact custom legend for the FSI tier scale."""
    chips = "".join(
        f"<div style='display:inline-flex;align-items:center;gap:6px;"
        f"margin-right:14px;'>"
        f"<span style='display:inline-block;width:10px;height:10px;"
        f"border-radius:2px;background:{FSI_COLORS[t]};'></span>"
        f"<span style='font-family:{FONT_BODY};font-size:11px;color:#1f2937;'>{t}</span>"
        f"</div>"
        for t in FSI_TIER_ORDER
    )
    st.markdown(
        f"<div style='margin-top:6px;color:{MUTED};font-size:10.5px;'>"
        f"<span style='margin-right:14px;'>FSI Score tier:</span>{chips}</div>",
        unsafe_allow_html=True,
    )


def compute_province_view(
    reg_df: pd.DataFrame,
    geojson: dict,
    padding: float = 0.10,
) -> tuple[dict, float]:
    """Compute mapbox center + zoom that fits the bounding box of all
    regencies present in reg_df. Used to zoom the choropleth into a
    single province.

    Returns (center_dict, zoom_float).
    """
    # Find features whose kemendagri_kab_code matches reg_df
    kab_codes = set(reg_df["kemendagri_kab_code"].astype(str).values)
    lats, lons = [], []
    for feat in geojson.get("features", []):
        props = feat.get("properties", {})
        if str(props.get("kemendagri_kab_code")) not in kab_codes:
            continue
        # Walk the geometry to extract all coordinates
        geom = feat.get("geometry", {})
        coords = geom.get("coordinates", [])
        gtype = geom.get("type", "")
        if gtype == "Polygon":
            for ring in coords:
                for pt in ring:
                    # Handle both [lon, lat] and [lon, lat, z] points
                    lons.append(pt[0])
                    lats.append(pt[1])
        elif gtype == "MultiPolygon":
            for poly in coords:
                for ring in poly:
                    for pt in ring:
                        lons.append(pt[0])
                        lats.append(pt[1])
    if not lats:
        # Fallback to Indonesia-wide
        return {"lat": -2.5, "lon": 117.5}, 4.0

    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)
    lat_center = (lat_min + lat_max) / 2
    lon_center = (lon_min + lon_max) / 2

    # Compute zoom from bounding-box span. Mapbox zoom is logarithmic;
    # this approximation works well between zoom 4 (Indonesia) and zoom 9
    # (single small province).
    lat_span = (lat_max - lat_min) * (1 + padding)
    lon_span = (lon_max - lon_min) * (1 + padding)
    max_span = max(lat_span, lon_span, 0.01)
    # zoom 4 = ~30 degrees span; zoom 9 = ~1 degree span; log2 mapping
    import math
    zoom = max(4.0, min(9.0, math.log2(30.0 / max_span) + 4.0))

    return {"lat": lat_center, "lon": lon_center}, zoom

    