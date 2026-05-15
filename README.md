# Indonesia Flood Dashboard

A Streamlit dashboard analysing the spatial and temporal patterns of flooding
in Indonesia from 2016 to 2025, drawn from BNPB disaster records and BPS
socioeconomic statistics, covering 514 regencies across 38 provinces.

**Current build: National view only.** Province and Regency drill-down,
Economic Impact, Social Impact, Predictive Outlook, and Policy Brief
pages are placeholders (sidebar items disabled until built).

## What's available

| Page | Status | Content |
|---|---|---|
| Landing | ✅ Live | Hero + 6 menu cards (1 live, 5 coming soon) |
| **Flood** | ✅ Live | KPI strip · FSI choropleth · annual trend · Top-10 rankings · Key Findings |
| Economic Impact | 🕒 Soon | — |
| Social Impact | 🕒 Soon | — |
| **Analytical Framework** | ✅ Live | Methodology reference (Moran's I, Gi*, MK, FSI) |
| Predictive Outlook | 🕒 Soon | — |
| Policy Brief | 🕒 Soon | — |

## Running locally

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Project structure

```
indonesia-flood-dashboard/
├── app.py                          Landing page + global theme
├── pages/
│   ├── 1_Flood.py                  National view: KPIs + map + line + top 10s
│   └── 4_Analytical_Framework.py   Methodology reference (3 tabs)
├── lib/
│   ├── colors.py                   Design tokens + palettes
│   ├── format.py                   Number formatting helpers
│   └── data_flood.py               Cached loaders (national + geo only)
├── components/
│   ├── sidebar_nav.py              Custom sidebar with FloodX brand
│   ├── section_header.py           Page + section title styling
│   ├── kpi_strip.py                Top KPI row
│   ├── choropleth.py               Plotly Mapbox choropleth (static)
│   ├── line_chart.py               Plotly multi-series with toggles
│   ├── ranking_table.py            Top-10 ranking tables
│   └── insight_box.py              Key Findings narrative box
├── public/data/                    NOT in repo (gitignored, large)
│   ├── geo/                        GeoJSON for 514 regencies + 38 provinces
│   └── flood/national/             KPIs + annual + parquet + insight
├── .streamlit/config.toml          Theme + nav config
├── requirements.txt
└── README.md
```

## Data pipeline

The dashboard does not run analysis itself — it consumes static files
produced upstream:

| Folder | Contents | Source |
|---|---|---|
| `public/data/geo/` | GeoJSON for 38 provinces and 514 regencies, plus lookup metadata | nb11 (build_dashboard_geo) |
| `public/data/flood/national/` | KPI strip values, annual time series, regency ranking, narrative | nb12 (build_dashboard_data_flood) |

All files use Kemendagri administrative codes as the join key.

## Indicator definitions

**FSI — Flood Severity Index.** A cluster-weighted composite of three
log-normalised dimensions:

| Dimension | Inputs | Weight |
|---|---|---|
| Event frequency | Number of recorded events | 0.302 |
| Human Cost Index (HCI) | log(deaths) + log(missing) + log(injured) | 0.360 |
| Property Damage Index (PDI) | log(houses flooded) + log(houses damaged) + log(public buildings damaged) | 0.338 |

Weights are derived empirically by k-means η&sup2; (FEMA NRI methodology).

**FSI tiers** (from national distribution): Catastrophic / High / Moderate / Low.

**Gi\* (Getis-Ord local statistic).** Identifies regencies that are
significantly clustered with similarly high (Hot) or low (Cold) values, at
90 / 95 / 99 % confidence.

**Mann-Kendall.** Tests for monotonic trend in annual indicators per
regency. Theil-Sen estimator quantifies the slope. National-level p-values
are Hamed-Rao corrected for autocorrelation. Per-regency results are
Benjamini-Hochberg FDR-corrected at α = 0.05.

## Design notes

- **No drill-down on the map.** The choropleth is static (no `on_select`)
  to avoid a known Plotly + Streamlit interaction that can cause silent
  render failures on some Windows + Plotly version combinations.
- **No scope selector.** Drill-down to Province/Regency removed for this
  build — re-add as a separate page later when ready.
- **Plotly pinned to 5.24.1.** The last stable version before the
  `Choroplethmapbox` deprecation in Plotly 6.x.

## License

Released for academic and policy-research use. Disaster records sourced
from BNPB; socioeconomic indicators from BPS Statistics Indonesia.
