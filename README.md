# Indonesia Flood Dashboard

A Streamlit dashboard analysing the spatial, temporal, and **economic** impact
of flooding in Indonesia from 2016 to 2025, drawn from BNPB disaster records and
BPS socioeconomic statistics, covering 514 regencies across 38 provinces.

## What's available

| Page | Status | Content |
|---|---|---|
| Landing | ✅ Live | Hero + menu cards |
| **Flood** | ✅ Live | National / Province / Regency — KPI strip · cluster + FSI choropleth · annual trend · Top-10 rankings · Key Findings |
| **Economic Impact** | ✅ Live | National + Province — KPIs · growth + FSI choropleth · annual line chart · sector flood-effect bars · top-FSI table · quadrant scatter · Key Findings |
| Social Impact | 🕒 Soon | — |
| **Analytical Framework** | ✅ Live | Methodology reference (Moran's I, Gi*, MK, FSI, panel FE) |
| Predictive Outlook | 🕒 Soon | — |
| Policy Brief | 🕒 Soon | — |

### Economic Impact — detail

**National tab.** KPI strip (avg growth, avg total GRDP, fastest/slowest sector,
significant flood driver from the RQ2 panel) · two-layer choropleth (growth
saturation + FSI bubbles) · dual-axis annual line chart (growth + FSI, with 17
toggleable sector lines) · sector flood-effect bars (significant β from the panel
regression, graded robust/suggestive) · top-10 most flood-affected regencies ·
Key Findings narrative.

**Province tab.** Province selector (ordered by region code) · four descriptive
KPIs including the highest-average-growth regency · choropleth zoomed to the
province · annual line chart · quadrant scatter (FSI vs growth, split at province
medians) · per-regency sector-growth table. The Province tab is descriptive only
— the flood regression is run at the national level.

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
│   ├── 1_Flood.py                  National / Province / Regency flood view
│   ├── 2_Economic.py               National + Province economic view
│   └── 4_Analytical_Framework.py   Methodology reference
├── lib/
│   ├── colors.py                   Design tokens + palettes
│   ├── format.py                   Number formatting helpers
│   ├── data_flood.py               Cached loaders for the Flood data
│   └── data_economic.py            Cached loaders for the Economic data
├── components/
│   ├── sidebar_nav.py              Custom sidebar with FloodX brand
│   ├── section_header.py           Page + section title styling
│   ├── kpi_strip.py                Top KPI row
│   ├── choropleth.py               Plotly choropleth + economic variant + province view
│   ├── line_chart.py               Multi-series line, sector-impact bars, quadrant scatter
│   ├── ranking_table.py            Ranking + FSI + per-regency sector tables
│   └── insight_box.py              Key Findings narrative box
├── public/data/                    Committed to the repo (Streamlit Cloud reads from here)
│   ├── geo/                        GeoJSON for 514 regencies + 38 provinces
│   ├── flood/national/             KPIs + annual series + regency parquet
│   └── economic/
│       ├── national/               regency_table.parquet + kpis/annual/sector JSON
│       └── provinces/{name}/       per-province annual series (38 folders)
├── .streamlit/config.toml          Theme + nav config
├── requirements.txt
└── README.md
```

## Data pipeline

The dashboard does not run analysis itself — it consumes static files produced
upstream by the thesis notebooks, then committed under `public/data/` so that
Streamlit Cloud can read them directly from the repository.

| Folder | Contents | Source notebook |
|---|---|---|
| `public/data/geo/` | GeoJSON for 38 provinces and 514 regencies, plus lookup metadata | nb11 |
| `public/data/flood/national/` | Flood KPIs, annual series, regency ranking (FSI, K-means cluster, centroids) | nb12 |
| `public/data/economic/` | Per-regency growth + 17 sector growth, KPIs, annual series, sector flood effects, province series | nb13 |

All files use Kemendagri administrative codes as the join key. FSI is sourced
only from the Flood data; the Economic pages join to it at runtime so the index
stays single-sourced and identical across pages.

## Indicator definitions

**FSI — Flood Severity Index.** A cluster-weighted composite of three
log-normalised dimensions:

| Dimension | Inputs | Weight |
|---|---|---|
| Event frequency | log1p(event count) | 0.3062 (30.6%) |
| Human Cost Index (HCI) | log1p(deaths) + log1p(missing) + log1p(injured) | 0.3697 (37.0%) |
| Property Damage Index (PDI) | log1p(houses flooded) + log1p(houses damaged) + log1p(public buildings damaged) | 0.3241 (32.4%) |

Weights are derived empirically as normalised k-means η² (w_d = η²_d / Σ η²)
from the A3 specification (3-dimensional, z-scored, n=514), following FEMA NRI
methodology. Each dimension is the sum of its log1p-transformed components, so
HCI and PDI are already on a log scale when entered into the index.

**Flood typology (K-means A3).** Regencies are grouped into three descriptive
clusters used as the primary categorical system on the map and tables:
**Low Impact**, **Catastrophic**, and **Frequent-Contained**.

**Gi\* (Getis-Ord local statistic).** Identifies regencies significantly
clustered with similarly high (Hot) or low (Cold) values, at 90 / 95 / 99 %
confidence.

**Mann-Kendall.** Tests for monotonic trend in annual indicators per regency
(Theil-Sen slope). National p-values are Hamed-Rao corrected; per-regency
results are Benjamini-Hochberg FDR-corrected at α = 0.05.

**Economic growth.** Year-on-year growth of regency GRDP at constant 2010 prices
(ADHK). The headline `growth_avg` is the mean annual growth 2016-2025 per regency
(not cumulative, not CAGR).

**RQ2 panel regression.** A fixed-effects panel relates annual GRDP growth to
three contemporaneous (same-year) flood dimensions (event count, HCI, PDI).
Sector-level effects are tested across 17 sectors with Benjamini-Hochberg FDR
correction and graded by standard-error consistency (robust if significant under
both clustered and Driscoll-Kraay SE; suggestive if only one). Effects are
within-regency associations, not causal monetary losses.

## Design notes

- **Map drill-down.** The Province choropleth zooms to the selected province via
  a computed centre/zoom (`compute_province_view`).
- **Quadrant scatter.** The Province FSI-vs-growth scatter splits at the province
  median FSI and median growth — a descriptive cross-regency view, not the causal
  within-regency estimate.
- **FSI single-sourced.** The Economic pages never recompute FSI; they join the
  Flood regency table at runtime so the index and ranking match the Flood page.

## License

Released for academic and policy-research use. Disaster records sourced from
BNPB; socioeconomic indicators from BPS Statistics Indonesia.
