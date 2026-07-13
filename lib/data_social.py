"""
lib/data_social.py
==================
Cached loaders for the Social-menu data files produced by nb14.

    public/data/social/
    ├── national/
    │   ├── regency_table.parquet   # 514 regencies: poverty_avg, tpt_avg + keys
    │   ├── kpis.json               # 6 descriptive KPIs (point-%)
    │   ├── annual_series.json      # national poverty+tpt+fsi per year
    │   └── correlation.json        # descriptive flood-vs-outcome correlations
    └── provinces/
        └── {slug}/annual_series.json   # per-province poverty+tpt+fsi per year

Social indicators are descriptive point-percentages (poverty headcount %,
open-unemployment/TPT %), averaged 2016-2025. FSI is joined at runtime from
the Flood regency table (single-sourced), exactly like the Economic menu.
"""

from __future__ import annotations

import re as _re
from pathlib import Path

import pandas as pd
import streamlit as st

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SOC_DIR      = _PROJECT_ROOT / "public" / "data" / "social"
_FLOOD_DIR    = _PROJECT_ROOT / "public" / "data" / "flood"


@st.cache_data(show_spinner=False)
def _read_parquet(path_str: str) -> pd.DataFrame:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(
            f"Data file missing: {path.relative_to(_PROJECT_ROOT)}\n"
            f"Run nb14 (build_dashboard_social) and copy outputs to "
            f"public/data/social/national/."
        )
    return pd.read_parquet(path)


def load_national_social_table() -> pd.DataFrame:
    """Per-regency social table: poverty_avg, tpt_avg + keys (from nb14)."""
    return _read_parquet(str(_SOC_DIR / "national" / "regency_table.parquet"))


@st.cache_data(show_spinner=False)
def load_social_choropleth_table() -> pd.DataFrame:
    """Social table joined to Flood FSI + centroids for the map.

    Returns poverty_avg + tpt_avg with FSI_index, centroid_lat, centroid_lon
    merged from the Flood regency table (FSI single-sourced). Regencies missing
    from the Flood table keep NaN FSI/centroids.
    """
    soc = load_national_social_table()

    flood_path = _FLOOD_DIR / "national" / "regency_table.parquet"
    if not flood_path.exists():
        soc["FSI_index"]    = pd.NA
        soc["centroid_lat"] = pd.NA
        soc["centroid_lon"] = pd.NA
        return soc

    flood = pd.read_parquet(flood_path)
    keep = ["kemendagri_kab_code", "FSI_index", "centroid_lat", "centroid_lon"]
    keep = [c for c in keep if c in flood.columns]
    return soc.merge(flood[keep], on="kemendagri_kab_code", how="left")


@st.cache_data(show_spinner=False)
def load_national_social_kpis() -> list:
    """Six descriptive social KPIs (list of dicts) for the KPI strip."""
    import json
    path = _SOC_DIR / "national" / "kpis.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Data file missing: {path.relative_to(_PROJECT_ROOT)}\n"
            f"Run nb14 (STEP 3) and copy outputs to public/data/social/national/."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_national_social_series() -> dict:
    """National annual series (FSI + poverty + unemployment per year) for the
    Social line chart. From nb14 STEP 4."""
    import json
    path = _SOC_DIR / "national" / "annual_series.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Data file missing: {path.relative_to(_PROJECT_ROOT)}\n"
            f"Run nb14 (STEP 4) and copy outputs to public/data/social/national/."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_social_fsi_table(top_n: int = 10) -> pd.DataFrame:
    """Top-N regencies by FSI with their social profile (poverty, tpt), built
    at runtime by joining the social table with the FSI composite from the
    FLOOD regency table (single-sourced, matches the Flood page).

    Returns: regency | province | fsi | poverty_avg | tpt_avg.
    """
    soc = load_national_social_table()
    flood_path = _FLOOD_DIR / "national" / "regency_table.parquet"
    if not flood_path.exists():
        raise FileNotFoundError(
            f"Flood regency table missing: {flood_path.relative_to(_PROJECT_ROOT)}\n"
            f"Build the Flood dashboard data first (nb12)."
        )
    flood = pd.read_parquet(flood_path)[["kemendagri_kab_code", "FSI_index"]]
    merged = soc.merge(flood, on="kemendagri_kab_code", how="left")
    merged = merged.sort_values("FSI_index", ascending=False).head(top_n)
    out = merged[["kemendagri_kab_name", "kemendagri_prov_name",
                  "FSI_index", "poverty_avg", "tpt_avg"]].copy()
    out.columns = ["regency", "province", "fsi", "poverty_avg", "tpt_avg"]
    return out.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_social_correlation() -> dict:
    """Descriptive bivariate correlation matrix (flood dims vs
    poverty/unemployment) from nb14 STEP 5."""
    import json
    path = _SOC_DIR / "national" / "correlation.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Data file missing: {path.relative_to(_PROJECT_ROOT)}\n"
            f"Run nb14 (STEP 5) and copy outputs to public/data/social/national/."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ═════════════════════════════════════════════════════════════════════════
# Province-level loaders (Province tab) — mirror the Economic menu
# ═════════════════════════════════════════════════════════════════════════
def _prov_slug(name: str) -> str:
    """Province name -> folder slug (matches nb14 STEP 6 + Economic menu)."""
    return _re.sub(r"[^A-Za-z0-9]+", "_", str(name)).strip("_")


@st.cache_data(show_spinner=False)
def list_social_provinces() -> list:
    """Province names in BPS/Kemendagri geographic order (by province code)."""
    tbl = load_national_social_table().copy()
    if "kemendagri_prov_name" not in tbl.columns:
        return []
    tbl["_prov_code"] = tbl["kemendagri_kab_code"].astype(str).str[:2]
    order = (tbl.groupby("kemendagri_prov_name")["_prov_code"].first()
             .sort_values())
    return order.index.tolist()


@st.cache_data(show_spinner=False)
def load_province_social_table(prov_name: str) -> pd.DataFrame:
    """National social table filtered to one province (poverty_avg, tpt_avg + keys)."""
    tbl = load_national_social_table()
    return tbl[tbl["kemendagri_prov_name"] == prov_name].reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_province_social_choropleth(prov_name: str) -> pd.DataFrame:
    """Province social table joined to Flood FSI + centroids (for the map)."""
    full = load_social_choropleth_table()
    return full[full["kemendagri_prov_name"] == prov_name].reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_province_social_kpis(prov_name: str) -> list:
    """Six descriptive KPIs computed for a single province (point-%)."""
    sub = load_province_social_table(prov_name)
    if sub.empty:
        return []
    pov_avg = float(sub["poverty_avg"].mean())
    tpt_avg = float(sub["tpt_avg"].mean())
    low_pov  = sub.loc[sub["poverty_avg"].idxmin()]
    low_tpt  = sub.loc[sub["tpt_avg"].idxmin()]
    high_pov = sub.loc[sub["poverty_avg"].idxmax()]
    high_tpt = sub.loc[sub["tpt_avg"].idxmax()]
    return [
        {"label": "Avg Poverty Rate", "value": f"{pov_avg:.2f}%",
         "sublabel": f"{prov_name} · mean 2016-2025", "tone": "amber"},
        {"label": "Avg Unemployment (TPT)", "value": f"{tpt_avg:.2f}%",
         "sublabel": "Open unemployment, mean 2016-2025", "tone": "amber"},
        {"label": "Lowest-Poverty Regency", "value": f"{low_pov['poverty_avg']:.2f}%",
         "sublabel": f"{low_pov['kemendagri_kab_name']} · mean 2016-2025", "tone": "green"},
        {"label": "Lowest-Unemployment Regency", "value": f"{low_tpt['tpt_avg']:.2f}%",
         "sublabel": f"{low_tpt['kemendagri_kab_name']} · mean 2016-2025", "tone": "green"},
        {"label": "Highest-Poverty Regency", "value": f"{high_pov['poverty_avg']:.2f}%",
         "sublabel": f"{high_pov['kemendagri_kab_name']} · mean 2016-2025", "highlight": True},
        {"label": "Highest-Unemployment Regency", "value": f"{high_tpt['tpt_avg']:.2f}%",
         "sublabel": f"{high_tpt['kemendagri_kab_name']} · mean 2016-2025", "highlight": True},
    ]


@st.cache_data(show_spinner=False)
def load_province_social_series(prov_name: str) -> dict:
    """Per-province annual series (poverty+unemployment+FSI) from nb14 STEP 6."""
    import json
    path = _SOC_DIR / "provinces" / _prov_slug(prov_name) / "annual_series.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Data file missing: {path.relative_to(_PROJECT_ROOT)}\n"
            f"Run nb14 (STEP 6) and copy social/provinces/ to "
            f"public/data/social/provinces/."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def list_province_social_regencies(prov_name: str) -> list:
    """List regencies in a province as [{code, name}], sorted by FSI desc when
    available (most flood-affected first), else by name."""
    sub = load_province_social_choropleth(prov_name)
    if sub.empty:
        return []
    if "FSI_index" in sub.columns and sub["FSI_index"].notna().any():
        sub = sub.sort_values("FSI_index", ascending=False)
    else:
        sub = sub.sort_values("kemendagri_kab_name")
    return [{"code": str(r["kemendagri_kab_code"]), "name": r["kemendagri_kab_name"]}
            for _, r in sub.iterrows()]


@st.cache_data(show_spinner=False)
def load_regency_social_kpis(kab_code: str) -> list:
    """Three descriptive KPIs for one regency: avg poverty, avg unemployment, FSI."""
    tbl = load_social_choropleth_table()
    row = tbl[tbl["kemendagri_kab_code"].astype(str) == str(kab_code)]
    if row.empty:
        return []
    r = row.iloc[0]
    fsi = r.get("FSI_index")
    fsi_val = f"{float(fsi):.1f}" if pd.notna(fsi) else "—"
    return [
        {"label": "Avg Poverty Rate", "value": f"{float(r['poverty_avg']):.2f}%",
         "sublabel": "Mean 2016-2025", "tone": "amber"},
        {"label": "Avg Unemployment (TPT)", "value": f"{float(r['tpt_avg']):.2f}%",
         "sublabel": "Open unemployment, mean 2016-2025", "tone": "amber"},
        {"label": "Flood Severity (FSI)", "value": fsi_val,
         "sublabel": "Composite severity, 0-100", "highlight": True},
    ]


@st.cache_data(show_spinner=False)
def load_regency_social_series(kab_code: str) -> dict:
    """Per-regency annual series (poverty+unemployment+FSI) from nb14 STEP 7."""
    import json
    path = _SOC_DIR / "regencies" / f"{kab_code}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Data file missing: {path.relative_to(_PROJECT_ROOT)}\n"
            f"Run nb14 (STEP 7) and copy social/regencies/ to "
            f"public/data/social/regencies/."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_regency_social_benchmark(kab_code: str) -> dict:
    """Benchmark one regency against its province and the nation, plus its rank
    within the province. Computed at runtime from the national table (no extra
    data files). Returns:
        {
          "regency": {"poverty": .., "tpt": ..},
          "province": {"name": str, "poverty": .., "tpt": ..},
          "national": {"poverty": .., "tpt": ..},
          "rank": {"poverty": (pos, n), "tpt": (pos, n)},   # 1 = highest
        }
    """
    tbl = load_national_social_table()
    row = tbl[tbl["kemendagri_kab_code"].astype(str) == str(kab_code)]
    if row.empty:
        return {}
    r = row.iloc[0]
    prov = r["kemendagri_prov_name"]
    prov_df = tbl[tbl["kemendagri_prov_name"] == prov]

    # rank within province (1 = highest rate, i.e. worst)
    pov_sorted = prov_df.sort_values("poverty_avg", ascending=False).reset_index(drop=True)
    tpt_sorted = prov_df.sort_values("tpt_avg",     ascending=False).reset_index(drop=True)
    n = len(prov_df)
    pov_pos = int(pov_sorted.index[
        pov_sorted["kemendagri_kab_code"].astype(str) == str(kab_code)][0]) + 1
    tpt_pos = int(tpt_sorted.index[
        tpt_sorted["kemendagri_kab_code"].astype(str) == str(kab_code)][0]) + 1

    return {
        "regency":  {"poverty": float(r["poverty_avg"]), "tpt": float(r["tpt_avg"])},
        "province": {"name": prov,
                     "poverty": float(prov_df["poverty_avg"].mean()),
                     "tpt": float(prov_df["tpt_avg"].mean())},
        "national": {"poverty": float(tbl["poverty_avg"].mean()),
                     "tpt": float(tbl["tpt_avg"].mean())},
        "rank": {"poverty": (pov_pos, n), "tpt": (tpt_pos, n)},
    }