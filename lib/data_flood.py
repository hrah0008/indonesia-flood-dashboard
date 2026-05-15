"""
lib/data_flood.py
=================
Typed, cached loaders for the Flood-menu data files produced by nb12.

Directory layout consumed (National view only):

    public/data/flood/
    └── national/
        ├── kpis.json
        ├── annual_series.json
        ├── regency_table.parquet
        └── insight.json

    public/data/geo/
    ├── regencies.geojson
    ├── provinces.geojson
    ├── regencies_lookup.json
    └── provinces_lookup.json

Streamlit caches each loader for the session — same file is parsed once
even if multiple components on the same page read it.

Province/regency drill-down loaders have been removed for this build.
Re-add `load_province_*` and `list_available_provinces` from git history
if Province/Regency pages are built later.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


# Resolve project root from this file's location: lib/data_flood.py → ../
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_FLOOD_DIR    = _PROJECT_ROOT / "public" / "data" / "flood"


# ─────────────────────────────────────────────────────────────────────
# Low-level JSON / parquet readers
# ─────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _read_json(path_str: str) -> Any:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(
            f"Data file missing: {path.relative_to(_PROJECT_ROOT)}\n"
            f"Run nb12 (build_dashboard_data_flood) and copy outputs to "
            f"public/data/flood/."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def _read_parquet(path_str: str) -> pd.DataFrame:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(
            f"Data file missing: {path.relative_to(_PROJECT_ROOT)}\n"
            f"Run nb12 and copy outputs to public/data/flood/."
        )
    return pd.read_parquet(path)


# ─────────────────────────────────────────────────────────────────────
# National-level loaders — used by pages/1_Flood.py
# ─────────────────────────────────────────────────────────────────────
def load_national_kpis() -> dict:
    """The KPI strip payload — see nb12 STEP 3a for field list.

    Expected fields include:
        n_regencies, n_provinces, total_events, total_deaths,
        total_missing, total_injured, total_houses,
        avg_fsi_percent, avg_freq_annual, avg_hci_annual, avg_pdi_annual,
        morans_i, morans_p, knn_k,
        n_hot_spots, n_mk_sig_freq,
        trend_direction, mk_tau, mk_p_hr, mk_slope_pct,
        year_min, year_max
    """
    return _read_json(str(_FLOOD_DIR / "national" / "kpis.json"))


def load_national_annual() -> dict:
    """Year-by-year aggregates — list of years + parallel arrays per metric.

    Expected keys: years, events, deaths, missing, injured,
                    houses_flooded, houses_damaged,
                    fsi_percent, hci_total, pdi_total
    """
    return _read_json(str(_FLOOD_DIR / "national" / "annual_series.json"))


def load_national_regency_table() -> pd.DataFrame:
    """Per-regency table — 514 rows × ranking columns.

    Expected columns include:
        kemendagri_kab_code, kemendagri_kab_name,
        kemendagri_prov_code, kemendagri_prov_name,
        event_count, deaths, missing, injured,
        house_flooded, house_damaged,
        FSI, FSI_percent, FSI_tier,
        gi_cat_FSI, confirmed_hot_FSI,
        mk_sig_event_count, mk_sig_HCI, mk_sig_PDI,
        centroid_lat, centroid_lon
    """
    return _read_parquet(str(_FLOOD_DIR / "national" / "regency_table.parquet"))


def load_national_insight() -> dict:
    """Auto-generated narrative bullets and headline statistics."""
    try:
        return _read_json(str(_FLOOD_DIR / "national" / "insight.json"))
    except FileNotFoundError:
        # Insight is decorative — page should still render without it
        return {"bullets": [], "headline": ""}


# ─────────────────────────────────────────────────────────────────────
# Geo loaders — used by choropleth components
# ─────────────────────────────────────────────────────────────────────
_GEO_DIR = _PROJECT_ROOT / "public" / "data" / "geo"


def load_regencies_geojson() -> dict:
    """The 514-regency GeoJSON FeatureCollection (web resolution)."""
    return _read_json(str(_GEO_DIR / "regencies.geojson"))


def load_provinces_geojson() -> dict:
    """The 38-province dissolved GeoJSON."""
    return _read_json(str(_GEO_DIR / "provinces.geojson"))


def load_regencies_lookup() -> dict:
    """Map kemendagri_kab_code → {name, prov_code, prov_name, centroid_lat, centroid_lon}."""
    return _read_json(str(_GEO_DIR / "regencies_lookup.json"))


def load_provinces_lookup() -> dict:
    """Map kemendagri_prov_code → {name, n_regencies, centroid_lat, centroid_lon}."""
    return _read_json(str(_GEO_DIR / "provinces_lookup.json"))


# ─────────────────────────────────────────────────────────────────────
# Diagnostic — surface missing files in a friendly way
# ─────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def assert_data_present() -> tuple[bool, list[str]]:
    """Check every file the National tab needs. Returns (ok, missing_paths).
    Cached for the session — files don't appear or disappear at runtime.
    """
    required = [
        _FLOOD_DIR / "national" / "kpis.json",
        _FLOOD_DIR / "national" / "annual_series.json",
        _FLOOD_DIR / "national" / "regency_table.parquet",
        _GEO_DIR   / "regencies.geojson",
    ]
    missing = [str(p.relative_to(_PROJECT_ROOT)) for p in required if not p.exists()]
    return (len(missing) == 0, missing)

# ─────────────────────────────────────────────────────────────────────
# Province- and regency-level loaders REMOVED — National view only.
# Re-add later if Province/Regency drill-down pages are built.
# ─────────────────────────────────────────────────────────────────────
