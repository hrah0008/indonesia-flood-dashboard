"""
app.py
======
Indonesia Flood Pattern Analysis Dashboard
Data loaded from Google Drive
"""

import os
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import gdown

# ═════════════════════════════════════════════════════════
# PAGE CONFIG
# ═════════════════════════════════════════════════════════

st.set_page_config(
    page_title = "Indonesia Flood Dashboard",
    page_icon  = "🌊",
    layout     = "wide",
)

# ═════════════════════════════════════════════════════════
# GOOGLE DRIVE FILE IDs
# ═════════════════════════════════════════════════════════

DRIVE_FILES = {
    "regency_centroids.xlsx"  : "15YSPe2SYGMfF1mhQQNtNTLMbl08SQMlW",   # ← replace
    "shp_to_bps_lookup.csv"  : "17LZ8IqtXKoxMr4S5QVYDmUfwIIn3aiUL",   # ← replace
    "Kab_Kota_with_BPS.gpkg" : "1tCK9eMXbRWKsVLcU0-Nd1CSC8ZIGqa0e",   # ← replace
}    

# ═════════════════════════════════════════════════════════
# DOWNLOAD HELPER
# ═════════════════════════════════════════════════════════

def download_file(filename: str, file_id: str) -> str:
    os.makedirs("data", exist_ok=True)
    filepath = f"data/{filename}"
    if not os.path.exists(filepath):
        url = f"https://drive.google.com/uc?id={file_id}"
        with st.spinner(f"Downloading {filename}..."):
            gdown.download(url, filepath, quiet=False)
        st.success(f"✓ {filename} ready")
    return filepath

# ═════════════════════════════════════════════════════════
# LOAD DATA
# ═════════════════════════════════════════════════════════

@st.cache_data
def load_centroids() -> pd.DataFrame:
    path = download_file(
        "regency_centroids.xlsx",
        DRIVE_FILES["regency_centroids.xlsx"],
    )
    return pd.read_excel(path, sheet_name="Regency Centroids")


@st.cache_data
def load_lookup() -> pd.DataFrame:
    path = download_file(
        "shp_to_bps_lookup.csv",
        DRIVE_FILES["shp_to_bps_lookup.csv"],
    )
    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            return pd.read_csv(
                path,
                encoding     = encoding,
                on_bad_lines = "skip",
                engine       = "python",
            )
        except Exception:
            continue
    return pd.DataFrame()


@st.cache_data
def load_gpkg() -> gpd.GeoDataFrame:
    path = download_file(
        "Kab_Kota_with_BPS.gpkg",
        DRIVE_FILES["Kab_Kota_with_BPS.gpkg"],
    )
    return gpd.read_file(path)

# ═════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════

st.title("🌊 Indonesia Flood Pattern Analysis 2016–2025")
st.markdown(
    "Spatial and temporal analysis of flood patterns across "
    "514 Indonesian regencies · Data source: BNPB · "
    "Monash University Master Thesis"
)
st.divider()

# ═════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════

st.sidebar.title("⚙️ Settings")
show_polygon = st.sidebar.checkbox(
    "Show polygon map",
    value = False,
    help  = "Downloads 325MB — takes a few minutes"
)

# ═════════════════════════════════════════════════════════
# LOAD SMALL FILES FIRST
# ═════════════════════════════════════════════════════════

centroids = load_centroids()
lookup    = load_lookup()

# ═════════════════════════════════════════════════════════
# METRICS
# ═════════════════════════════════════════════════════════

st.subheader("📊 Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Regencies", f"{len(centroids):,}")
col2.metric("Total Provinces", f"{centroids['bps_prov_name'].nunique()}")
col3.metric("Lookup Records",  f"{len(lookup):,}")
col4.metric("Study Period",    "2016 – 2025")
st.divider()

# ═════════════════════════════════════════════════════════
# BUBBLE MAP — fast, no gpkg needed
# ═════════════════════════════════════════════════════════

st.subheader("📍 Regency Locations — Bubble Map")

fig = px.scatter_geo(
    centroids,
    lat        = "centroid_lat",
    lon        = "centroid_lon",
    hover_name = "bps_kab_name",
    hover_data = {
        "bps_prov_name": True,
        "centroid_lat" : False,
        "centroid_lon" : False,
    },
    color      = "bps_prov_name",
    title      = "514 Indonesian Regencies by Province",
    scope      = "asia",
)
fig.update_layout(
    geo = dict(
        center           = dict(lat=-2.5, lon=118),
        projection_scale = 4,
        showland         = True,
        landcolor        = "#f0f0f0",
        showocean        = True,
        oceancolor       = "#d0e8f0",
        showcoastlines   = True,
        coastlinecolor   = "gray",
    ),
    height     = 550,
    showlegend = False,
    margin     = dict(l=0, r=0, t=40, b=0),
)
st.plotly_chart(fig, width="stretch")
st.divider()

# ═════════════════════════════════════════════════════════
# POLYGON MAP — optional, loads gpkg
# ═════════════════════════════════════════════════════════

if show_polygon:
    st.subheader("🗺️ Polygon Map — Regency Boundaries")
    st.warning("⚠️ Downloading 325MB — please wait...")

    gdf = load_gpkg()
    st.success(f"✓ Loaded {len(gdf)} regency polygons")

    fig2 = px.choropleth(
        gdf,
        geojson   = gdf.geometry.__geo_interface__,
        locations = gdf.index,
        color     = "bps_prov_name",
        title     = "Indonesia Regency Boundaries",
    )
    fig2.update_geos(fitbounds="locations", visible=False)
    fig2.update_layout(
        height     = 550,
        showlegend = False,
        margin     = dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig2, width="stretch")
    st.divider()

# ═════════════════════════════════════════════════════════
# DATA PREVIEW
# ═════════════════════════════════════════════════════════

st.subheader("📋 Data Preview")
tab1, tab2 = st.tabs(["📌 Regency Centroids", "🔗 SHP Lookup"])

with tab1:
    st.markdown(f"**{len(centroids):,} regencies**")
    st.dataframe(centroids, width="stretch", height=400)

with tab2:
    st.markdown(f"**{len(lookup):,} records**")
    st.dataframe(lookup, width="stretch", height=400)

# ═════════════════════════════════════════════════════════
# FOOTER
# ═════════════════════════════════════════════════════════

st.divider()
st.caption(
    "Hesti Rahmawati · 34855564 · Monash University · "
    "Supervisor: Dr. Derry Tanti Wijaya · ITI5126 · 2026"
)