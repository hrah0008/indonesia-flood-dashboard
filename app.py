"""
app.py
======
Indonesia Flood Pattern Analysis Dashboard
Data loaded from Google Drive — no local data folder needed
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
# ← replace FILE_ID_X with your actual IDs
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
    """
    Download file from Google Drive if not already cached.
    Returns local file path.
    """
    os.makedirs("data", exist_ok=True)
    filepath = f"data/{filename}"

    if not os.path.exists(filepath):
        url = f"https://drive.google.com/uc?id={file_id}"
        with st.spinner(f"Downloading {filename}..."):
            gdown.download(url, filepath, quiet=False)
        st.success(f"✓ {filename} ready")

    return filepath


# ═════════════════════════════════════════════════════════
# LOAD DATA FUNCTIONS
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
    # Try different separators and encodings
    for sep in [",", ";", "\t"]:
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(
                    path,
                    sep          = sep,
                    encoding     = encoding,
                    on_bad_lines = "skip",   # skip problematic lines
                    engine       = "python",
                )
                if len(df.columns) > 1:     # valid parse has multiple columns
                    st.info(f"Loaded with sep='{sep}', encoding='{encoding}', "
                            f"shape={df.shape}")
                    return df
            except Exception:
                continue
    # Last resort — read as plain text
    st.error("Could not parse CSV — check file format")
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
st.sidebar.markdown("---")
show_polygon = st.sidebar.checkbox(
    "Show polygon map",
    value   = False,
    help    = "Downloads 325MB GeoPackage from Google Drive"
)
st.sidebar.markdown("---")
st.sidebar.info(
    "**Data Sources**\n"
    "- BNPB Flood Records 2016–2025\n"
    "- BPS Regional Statistics\n"
    "- Kemendagri Administrative Boundaries"
)

# ═════════════════════════════════════════════════════════
# LOAD SMALL FILES
# ═════════════════════════════════════════════════════════

centroids = load_centroids()
lookup    = load_lookup()

# ═════════════════════════════════════════════════════════
# METRICS ROW
# ═════════════════════════════════════════════════════════

st.subheader("📊 Overview")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Regencies",  f"{len(centroids):,}")
col2.metric("Total Provinces",  f"{centroids['bps_prov_name'].nunique()}")
col3.metric("Lookup Records",   f"{len(lookup):,}")
col4.metric("Study Period",     "2016 – 2025")

st.divider()

# ═════════════════════════════════════════════════════════
# BUBBLE MAP — fast, uses centroids only
# ═════════════════════════════════════════════════════════

st.subheader("📍 Regency Locations — Bubble Map")

fig_bubble = px.scatter_geo(
    centroids,
    lat          = "centroid_lat",
    lon          = "centroid_lon",
    hover_name   = "bps_kab_name",
    hover_data   = {
        "bps_prov_name" : True,
        "centroid_lat"  : False,
        "centroid_lon"  : False,
    },
    color        = "bps_prov_name",
    title        = "514 Indonesian Regencies by Province",
    scope        = "asia",
)
fig_bubble.update_layout(
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
st.plotly_chart(fig_bubble, width="stretch")

st.divider()

# ═════════════════════════════════════════════════════════
# POLYGON MAP — optional, loads gpkg from Google Drive
# ═════════════════════════════════════════════════════════

if show_polygon:
    st.subheader("🗺️ Polygon Map — Regency Boundaries")
    st.warning(
        "⚠️ This downloads a 325MB file from Google Drive. "
        "Please wait — this only happens once per session."
    )

    gdf = load_gpkg()
    st.success(f"✓ GeoPackage loaded: {len(gdf)} regency polygons")

    fig_poly = px.choropleth(
        gdf,
        geojson   = gdf.geometry.__geo_interface__,
        locations = gdf.index,
        color     = "bps_prov_name",
        title     = "Indonesia Regency Boundaries by Province",
    )
    fig_poly.update_geos(
        fitbounds = "locations",
        visible   = False,
    )
    fig_poly.update_layout(
        height     = 550,
        showlegend = False,
        margin     = dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig_poly, use_container_width=True)

    st.divider()

# ═════════════════════════════════════════════════════════
# DATA PREVIEW
# ═════════════════════════════════════════════════════════

st.subheader("📋 Data Preview")

tab1, tab2 = st.tabs([
    "📌 Regency Centroids",
    "🔗 SHP to BPS Lookup",
])

with tab1:
    st.markdown(f"**{len(centroids):,} regencies** with centroid coordinates")
    st.dataframe(
        centroids,
        use_container_width = True,
        height              = 400,
    )

with tab2:
    st.markdown(f"**{len(lookup):,} records** linking SHP codes to BPS codes")
    st.dataframe(
        lookup,
        use_container_width = True,
        height              = 400,
    )

# ═════════════════════════════════════════════════════════
# FOOTER
# ═════════════════════════════════════════════════════════

st.divider()
st.caption(
    "Hesti Rahmawati · 34855564 · Monash University · "
    "Supervisor: Dr. Derry Tanti Wijaya · ITI5126 · 2026"
)