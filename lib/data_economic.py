"""
lib/data_economic.py
====================
Typed, cached loaders for the Economic-menu data files produced by nb13.

Directory layout consumed (National view, choropleth stage):

    public/data/economic/
    └── national/
        └── regency_table.parquet   # 514 regencies: growth_avg + 17 sector growth + keys

FSI + centroids are NOT duplicated here. Per the chosen design (Option A),
the Economic choropleth joins this table to the Flood regency table
(public/data/flood/national/regency_table.parquet) on kemendagri_kab_code
at runtime to pull FSI_index, centroid_lat, centroid_lon. FSI stays
single-sourced in the Flood data.

Streamlit caches each loader for the session.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

# Resolve project root: lib/data_economic.py -> ../
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ECON_DIR     = _PROJECT_ROOT / "public" / "data" / "economic"
_FLOOD_DIR    = _PROJECT_ROOT / "public" / "data" / "flood"


@st.cache_data(show_spinner=False)
def _read_parquet(path_str: str) -> pd.DataFrame:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(
            f"Data file missing: {path.relative_to(_PROJECT_ROOT)}\n"
            f"Run nb13 (build_dashboard_economic) and copy outputs to "
            f"public/data/economic/national/."
        )
    return pd.read_parquet(path)


# ─────────────────────────────────────────────────────────────────────
# National-level loaders — used by pages/2_Economic.py
# ─────────────────────────────────────────────────────────────────────
def load_national_economic_table() -> pd.DataFrame:
    """Per-regency economic table from nb13.

    Columns:
        kemendagri_kab_code, kemendagri_kab_name, kemendagri_prov_name,
        growth_avg,                       # mean GRDP growth 2016-2025 (choropleth saturation)
        <sector>_growth_avg × 17          # per-sector mean growth
    """
    return _read_parquet(str(_ECON_DIR / "national" / "regency_table.parquet"))


@st.cache_data(show_spinner=False)
def load_economic_choropleth_table() -> pd.DataFrame:
    """Economic growth table joined to Flood FSI + centroids for the map.

    Returns the economic table with FSI_index, centroid_lat, centroid_lon
    merged in from the Flood regency table (Option A: FSI single-sourced).
    Regencies missing from the Flood table keep NaN FSI/centroids.
    """
    econ = load_national_economic_table()

    flood_path = _FLOOD_DIR / "national" / "regency_table.parquet"
    if not flood_path.exists():
        # Map can still colour by growth; FSI dots will simply be absent.
        econ["FSI_index"]    = pd.NA
        econ["centroid_lat"] = pd.NA
        econ["centroid_lon"] = pd.NA
        return econ

    flood = pd.read_parquet(flood_path)
    keep = ["kemendagri_kab_code", "FSI_index", "centroid_lat", "centroid_lon"]
    keep = [c for c in keep if c in flood.columns]
    merged = econ.merge(flood[keep], on="kemendagri_kab_code", how="left")
    return merged


@st.cache_data(show_spinner=False)
def load_national_economic_kpis() -> list:
    """National economic KPI items (list of dicts) for the KPI strip.

    Each item: {label, value, sublabel, tone?} — shape consumed directly by
    components/kpi_strip.render_kpi_strip().
    """
    import json
    path = _ECON_DIR / "national" / "kpis.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Data file missing: {path.relative_to(_PROJECT_ROOT)}\n"
            f"Run nb13 (STEP 3) and copy outputs to public/data/economic/national/."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_national_economic_series() -> dict:
    """National annual series for the Economic line chart (from nb13 STEP 4).

    Shape:
        {
          "years": [...],
          "default_series": ["fsi", "growth"],
          "series":  {"fsi": {...}, "growth": {...}},   # headline lines
          "sectors": {"<Sector>": {"values": [...]}, ...}  # 17, toggleable
        }
    """
    import json
    path = _ECON_DIR / "national" / "annual_series.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Data file missing: {path.relative_to(_PROJECT_ROOT)}\n"
            f"Run nb13 (STEP 4) and copy outputs to public/data/economic/national/."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_national_sector_impact() -> dict:
    """Significant sector×dimension flood effects (from nb13 STEP 5 / fit_9b.json).

    Shape: {bars:[{sector,dimension,beta,flag,grade,...}],
            n_significant, n_not_significant, n_total, note, ...}
    """
    import json
    path = _ECON_DIR / "national" / "sector_impact.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Data file missing: {path.relative_to(_PROJECT_ROOT)}\n"
            f"Run nb13 (STEP 5, needs fit_9b.json) and copy outputs to "
            f"public/data/economic/national/."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_national_fsi_table(top_n: int = 10) -> pd.DataFrame:
    """Top-N regencies by FSI — built at RUNTIME by joining the economic
    profile (growth_avg + top_sectors) with the FSI composite from the FLOOD
    regency table, so FSI matches the Flood page exactly (single source).

    Returns a DataFrame: regency | province | fsi | growth_avg | top_sectors.
    """
    # economic profile (growth + top sectors) from nb13
    econ = load_national_economic_table()          # has growth_avg, top_sectors, keys

    # FSI composite from the FLOOD regency table (same file the Flood page uses)
    flood_path = _PROJECT_ROOT / "public" / "data" / "flood" / "national" / "regency_table.parquet"
    if not flood_path.exists():
        raise FileNotFoundError(
            f"Flood regency table missing: {flood_path.relative_to(_PROJECT_ROOT)}\n"
            f"Build the Flood dashboard data first (nb12) — the Economic FSI table "
            f"reuses its FSI composite to stay consistent."
        )
    flood = pd.read_parquet(flood_path)[["kemendagri_kab_code", "FSI_index"]]

    merged = econ.merge(flood, on="kemendagri_kab_code", how="left")
    merged = merged.sort_values("FSI_index", ascending=False).head(top_n)

    out = merged[["kemendagri_kab_name", "kemendagri_prov_name",
                  "FSI_index", "growth_avg", "top_sectors"]].copy()
    out.columns = ["regency", "province", "fsi", "growth_avg", "top_sectors"]
    return out.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_national_economic_insight() -> dict:
    """Key-insight narrative (title + bullets) from nb13 STEP 6."""
    import json
    path = _ECON_DIR / "national" / "insight.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Data file missing: {path.relative_to(_PROJECT_ROOT)}\n"
            f"Run nb13 (STEP 6) and copy outputs to public/data/economic/national/."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def list_economic_provinces() -> list:
    """Province names ordered by region code (Aceh 11, Sumatera Utara 12, ...),
    i.e. the geographic ordering used by BPS/Kemendagri rather than alphabetical.
    The 2-digit province code is the first two digits of kemendagri_kab_code.
    """
    econ = load_national_economic_table().copy()
    econ["_prov_code"] = econ["kemendagri_kab_code"].astype(str).str[:2]
    order = (econ.groupby("kemendagri_prov_name")["_prov_code"].first()
                 .sort_values())
    return order.index.tolist()


@st.cache_data(show_spinner=False)
def load_province_economic_kpis(prov_name: str) -> list:
    """Four descriptive KPIs for one province (no regression output):
    avg growth, fastest sector, slowest sector, and the top regency by growth.
    All computed at runtime from the national regency table.
    """
    econ = load_national_economic_table()
    sub = econ[econ["kemendagri_prov_name"] == prov_name]
    if len(sub) == 0:
        return []

    sector_cols = [c for c in sub.columns
                   if c.endswith("_growth_avg") and c != "growth_avg"]
    sec_means = sub[sector_cols].mean()

    def _sec_label(col):
        return col.replace("_growth_avg", "").replace("_", " ").title()

    fastest = sec_means.idxmax()
    slowest = sec_means.idxmin()
    top_reg = sub.loc[sub["growth_avg"].idxmax()]

    return [
        {"label": "Avg Growth (Province)",
         "value": f"{sub['growth_avg'].mean():.2f}%",
         "sublabel": f"Mean annual, {len(sub)} regencies", "tone": "green"},
        {"label": "Fastest-Growing Sector",
         "value": f"{sec_means[fastest]:.2f}%",
         "sublabel": f"{_sec_label(fastest)} · descriptive", "tone": "green"},
        {"label": "Slowest-Growing Sector",
         "value": f"{sec_means[slowest]:.2f}%",
         "sublabel": f"{_sec_label(slowest)} · descriptive", "tone": "amber"},
        {"label": "Highest Avg Growth (Regency)",
         "value": f"{top_reg['growth_avg']:.2f}%",
         "sublabel": f"{top_reg['kemendagri_kab_name']} · mean annual 2016-2025",
         "highlight": True},
    ]


@st.cache_data(show_spinner=False)
def load_province_choropleth_table(prov_name: str) -> pd.DataFrame:
    """Choropleth table for ONE province: the national economic choropleth
    table (growth + FSI joined) filtered to the regencies of `prov_name`.
    Reuses load_economic_choropleth_table so FSI stays single-sourced.
    """
    full = load_economic_choropleth_table()      # growth + FSI, all 514
    sub = full[full["kemendagri_prov_name"] == prov_name].copy()
    return sub.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_province_economic_series(prov_name: str) -> dict:
    """Province annual series (growth + FSI + 17 sectors per year) for the
    Province line chart. Same shape as the National series, so it renders with
    the same render_economic_line_chart component. From nb13 STEP 7.
    """
    import json, re
    slug = re.sub(r"[^A-Za-z0-9]+", "_", str(prov_name)).strip("_")
    path = _ECON_DIR / "provinces" / slug / "annual_series.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Province series missing: {path.relative_to(_PROJECT_ROOT)}\n"
            f"Run nb13 (STEP 7) and copy economic/provinces/ to "
            f"public/data/economic/provinces/."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_province_scatter(prov_name: str) -> pd.DataFrame:
    """Per-regency FSI vs growth for one province (scatter).
    Returns: regency | FSI_index | growth_avg | cluster (if available).
    FSI + cluster joined from the Flood regency table (single-sourced).
    """
    econ = load_national_economic_table()
    sub = econ[econ["kemendagri_prov_name"] == prov_name].copy()

    flood_path = _FLOOD_DIR / "national" / "regency_table.parquet"
    if flood_path.exists():
        flood = pd.read_parquet(flood_path)
        # FSI + any cluster/label column we can find
        cluster_col = next(
            (c for c in flood.columns
             if c.lower() in ("cluster_label", "kmeans_cluster", "cluster",
                              "impact_cluster", "cluster_name")),
            None,
        )
        keep = ["kemendagri_kab_code", "FSI_index"]
        if cluster_col:
            keep.append(cluster_col)
        keep = [c for c in keep if c in flood.columns]
        sub = sub.merge(flood[keep], on="kemendagri_kab_code", how="left")
        if cluster_col and cluster_col != "cluster":
            sub = sub.rename(columns={cluster_col: "cluster"})
    else:
        sub["FSI_index"] = pd.NA

    cols = ["kemendagri_kab_name", "FSI_index", "growth_avg"]
    if "cluster" in sub.columns:
        cols.append("cluster")
    out = sub[cols].copy()
    out = out.rename(columns={"kemendagri_kab_name": "regency"})
    return out.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_province_sector_table(prov_name: str) -> pd.DataFrame:
    """Per-regency table for one province: growth_avg + all 17 sector growth
    (consistent with Y = growth). From the national economic table, filtered.
    """
    econ = load_national_economic_table()
    sub = econ[econ["kemendagri_prov_name"] == prov_name].copy()
    sector_cols = [c for c in sub.columns
                   if c.endswith("_growth_avg") and c != "growth_avg"]
    cols = ["kemendagri_kab_name", "growth_avg"] + sector_cols
    out = sub[cols].copy().rename(columns={"kemendagri_kab_name": "regency"})
    return out.sort_values("growth_avg", ascending=False).reset_index(drop=True)