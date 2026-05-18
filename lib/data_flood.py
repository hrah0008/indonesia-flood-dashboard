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
        avg_FSI_index, avg_freq_annual, avg_hci_annual, avg_pdi_annual,
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
                    FSI_index, hci_total, pdi_total
    """
    return _read_json(str(_FLOOD_DIR / "national" / "annual_series.json"))


def load_national_regency_table() -> pd.DataFrame:
    """Per-regency table — 514 rows × ranking columns.

    Expected columns include:
        kemendagri_kab_code, kemendagri_kab_name,
        kemendagri_prov_code, kemendagri_prov_name,
        event_count, deaths, missing, injured,
        house_flooded, house_damaged,
        FSI, FSI_index, FSI_tier,
        gi_cat_FSI, confirmed_hot_FSI,
        mk_sig_FSI, mk_sig_HCI, mk_sig_PDI,
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

# ─────────────────────────────────────────────────────────────────────
# Province-level loaders (Stage 1 — Province tab)
# ─────────────────────────────────────────────────────────────────────
def _province_dir(prov_code: str) -> Path:
    return _FLOOD_DIR / "provinces" / str(prov_code)


@st.cache_data(show_spinner=False)
def load_province_kpis(prov_code: str) -> dict:
    """Read provinces/{prov_code}/kpis.json — dict with prov_code, prov_name,
    n_regencies, total_events, total_deaths, avg_FSI_index, n_hot_spots,
    n_catastrophic, n_mk_sig_freq, year_min, year_max, etc.
    """
    return _read_json(str(_province_dir(prov_code) / "kpis.json"))


@st.cache_data(show_spinner=False)
def load_province_annual(prov_code: str) -> dict:
    """Read provinces/{prov_code}/annual_series.json — raw-count time series
    (events, deaths, houses_flooded, FSI_index) by year.
    """
    return _read_json(str(_province_dir(prov_code) / "annual_series.json"))


@st.cache_data(show_spinner=False)
def load_province_regency_table(prov_code: str) -> pd.DataFrame:
    """Read provinces/{prov_code}/regency_table.parquet — one row per regency
    in the province with FSI, FSI_index, FSI_tier, gi_cat_FSI, etc.
    """
    return _read_parquet(str(_province_dir(prov_code) / "regency_table.parquet"))

@st.cache_data(show_spinner=False)
def load_province_scatter(prov_code: str) -> pd.DataFrame:
    """Read provinces/{prov_code}/scatter.parquet — one row per regency with
    FSI_index (x), gi_z_FSI (y), category (URGENT/EMERGING/CONFIRMED/STABLE),
    mk_sig_FSI (bool). Built by nb12 cell 5 section 4d."""
    return _read_parquet(str(_province_dir(prov_code) / "scatter.parquet"))

@st.cache_data(show_spinner=False)
def load_province_insight(prov_code: str) -> dict:
    """Read provinces/{prov_code}/insight.json. Returns {} if missing."""
    path = _province_dir(prov_code) / "insight.json"
    if not path.exists():
        return {}
    return _read_json(str(path))


@st.cache_data(show_spinner=False)
def list_available_provinces() -> list[dict]:
    """Return list of {code, name} for available provinces, sorted by name.
    Fast path reads provinces/_index.json (one file).
    Fallback scans 38 sub-folders.
    """
    prov_dir = _FLOOD_DIR / "provinces"
    if not prov_dir.exists():
        return []

    index_path = prov_dir / "_index.json"
    if index_path.exists():
        try:
            with open(index_path, encoding="utf-8") as f:
                data = json.load(f)
            entries = data.get("provinces") if isinstance(data, dict) else data
            if isinstance(entries, list):
                out = [
                    {"code": str(e.get("code", e.get("prov_code", ""))),
                     "name": e.get("name", e.get("prov_name", ""))}
                    for e in entries
                    if e.get("code") or e.get("prov_code")
                ]
                out.sort(key=lambda d: d["code"])
                return out
        except Exception:
            pass

    out = []
    for p in sorted(prov_dir.iterdir()):
        if not p.is_dir():
            continue
        try:
            with open(p / "kpis.json", encoding="utf-8") as f:
                k = json.load(f)
            out.append({"code": str(k.get("prov_code", p.name)),
                         "name": k.get("prov_name", p.name)})
        except Exception:
            continue
    out.sort(key=lambda d: d["code"])
    return out

# ─────────────────────────────────────────────────────────────────────
# Regency-level loader (single JSON per regency)
# ─────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_regency_bundle(kab_code: str) -> dict:
    """Read regencies/{kab_code}.json — a single bundle containing:
        kpis            : dict with totals, FSI, Gi*, MK flags
        annual          : per-year time series
        monthly_heatmap : 10y × 12m FSI grid
        avg_monthly     : 12-month seasonal profile
    Built by nb12 Step 5.
    """
    return _read_json(str(_FLOOD_DIR / "regencies" / f"{kab_code}.json"))