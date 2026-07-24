# Indonesia Flood Dashboard

A Streamlit dashboard analysing the spatial, temporal, and socioeconomic
outcomes associated with flooding in Indonesia from 2016 to 2025, drawn from
BNPB disaster records and BPS socioeconomic statistics, covering 514 regencies
across 38 provinces.

The dashboard accompanies the master's thesis *Regional Socioeconomic Outcomes
of Flooding in Indonesia: A Spatiotemporal Analysis* (Monash University).

## Menus

| Page | Content |
|---|---|
| Landing | Hero + menu cards |
| **Flood** | National / Province / Regency — KPI strip · cluster + FSI choropleth · annual trend · Top-10 rankings · Key Findings |
| **Economic Impact** | National + Province — KPIs · growth + FSI choropleth · annual line chart · sector flood-effect bars · top-FSI table · quadrant scatter · Key Findings |
| **Social Impact** | Poverty and unemployment — KPIs · choropleth · annual series · Key Findings |
| **Analytical Framework** | Methodology reference across three tabs: spatial diagnostics (K-means, FSI, Moran's I, Gi*), temporal trend (Mann-Kendall), and causal & predictive methods (panel FE, XGBoost, SHAP) |
| **Model Evaluation** | Predictive evaluation for RQ2 — three-stage performance (train / validation / test), SHAP beeswarm, flood-vs-control importance, and the flood share of predictive importance, for growth, the 17 sectors, poverty, and unemployment |

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

### A note on Model Evaluation

This menu reports **how well flooding predicts** each outcome — it does not
forecast. The models show near-zero out-of-sample predictive power for flooding,
so presenting projections would misrepresent what the data supports. The menu
leads with the **flood share of importance** rather than total R², because total
R² mixes flooding with the control variables: for poverty the R² is high, but
SHAP attributes roughly 87 % of it to population and schooling, not to flooding.

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
│   ├── 3_Social.py                 Poverty + unemployment view
│   ├── 4_Analytical_Framework.py   Methodology reference (3 tabs)
│   └── 5_Model_Evaluation.py       RQ2 predictive evaluation (Economic / Social tabs)
├── lib/
│   ├── colors.py                   Design tokens + palettes
│   ├── format.py                   Number formatting helpers
│   ├── data_flood.py               Cached loaders for the Flood data
│   ├── data_economic.py            Cached loaders for the Economic data
│   └── data_social.py              Cached loaders for the Social data
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
│   ├── economic/
│   │   ├── national/               regency_table.parquet + kpis/annual/sector JSON
│   │   └── provinces/{name}/       per-province annual series (38 folders)
│   ├── social/                     Poverty + unemployment series and rankings
│   └── model/                      Model Evaluation: economic.json, social.json, index.json
│       └── img/                    SHAP beeswarm plots (PNG, one per outcome)
├── .python-version                 Pins Python 3.11 for Streamlit Cloud
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
| `public/data/geo/` | GeoJSON for 38 provinces and 514 regencies, plus lookup metadata | nb12 |
| `public/data/flood/national/` | Flood KPIs, annual series, regency ranking (FSI, K-means cluster, interior points) | nb13 |
| `public/data/economic/` | Per-regency growth + 17 sector growth, KPIs, annual series, sector flood effects, province series | nb14 |
| `public/data/social/` | Poverty and unemployment series, KPIs, rankings | nb15 |
| `public/data/model/` | Three-stage metrics, SHAP importance, flood share, and beeswarm PNGs for every RQ2 outcome | nb16 |

All files use Kemendagri administrative codes as the join key at the dashboard
boundary; the analysis pipeline itself uses BPS codes internally. FSI is sourced
only from the Flood data — the Economic and Social pages join to it at runtime so
the index stays single-sourced and identical across pages.

## Indicator definitions

**FSI — Flood Severity Index.** A cluster-weighted composite of three
log-normalised dimensions:

| Dimension | Inputs | Weight |
|---|---|---|
| Event frequency | log1p(event count) | 0.3062 (30.6 %) |
| Human Cost Index (HCI) | log1p(deaths) + log1p(missing) + log1p(injured) | 0.3697 (37.0 %) |
| Property Damage Index (PDI) | log1p(houses flooded) + log1p(houses damaged) + log1p(public buildings damaged) | 0.3241 (32.4 %) |

Weights are derived empirically as normalised k-means η² (w_d = η²_d / Σ η²) from
the A3 specification (3-dimensional, z-scored, n = 514), following FEMA NRI
methodology. Each dimension is the sum of its log1p-transformed components, so HCI
and PDI are already on a log scale when entered into the index. K-means weighting
is used rather than PCA because it is directly interpretable — dimensions that
most separate high- from low-severity regencies receive greater weight — and
because the dimensions are correlated (event–PDI r ≈ 0.81), which would cause
correlation-based weights to double-count overlapping information.

**Flood typology (K-means A3).** Regencies are grouped into three descriptive
clusters used as the primary categorical system on the map and tables: **Low
Impact**, **Catastrophic**, and **Frequent-Contained**.

**Gi\* (Getis-Ord local statistic).** Identifies regencies significantly clustered
with similarly high (Hot) or low (Cold) values, at 90 / 95 / 99 % confidence.
Spatial weights use k-nearest-neighbour distances (k = 5) between regency
**interior representative points** rather than geometric centroids: for enclave
geometries such as Kabupaten Cirebon, which surrounds the separate unit of Kota
Cirebon, the geometric centroid falls outside its own polygon and produces
incorrect neighbour assignments.

**Mann-Kendall.** Tests for monotonic trend in annual indicators per regency.
National p-values are Hamed-Rao corrected; per-regency results are
Benjamini-Hochberg FDR-corrected at α = 0.05.

**Economic growth.** Year-on-year growth of regency GRDP at constant 2010 prices
(ADHK). The headline `growth_avg` is the mean annual growth 2016–2025 per regency
(not cumulative, not CAGR).

**RQ2 — panel regression.** A two-way fixed-effects panel relates each annual
outcome to three contemporaneous flood dimensions (event count, HCI, PDI),
controlling for log population and mean years of schooling, with regency and year
effects. Sector-level effects are tested across 17 sectors with Benjamini-Hochberg
FDR correction and graded by standard-error consistency: **robust** if significant
under both clustered and Driscoll-Kraay SE, **suggestive** if only one. Effects
are within-regency associations, not causal monetary losses.

**RQ2 — XGBoost and SHAP.** A gradient-boosted model tests whether the same flood
variables can *predict* each outcome out-of-sample. It is tuned by GroupKFold
cross-validation on 2016–2022, selected on 2023, and evaluated once on the
untouched 2024–2025 test set against a naive mean baseline. SHAP (TreeExplainer)
decomposes each prediction into per-feature contributions, which yields the
**flood share** — the proportion of predictive importance carried by the flood
variables, as distinct from the controls.

## Design notes

- **Significance ≠ predictability.** Fixed effects and XGBoost answer different
  questions. A flood effect can be statistically significant yet too small to
  predict out-of-sample; the dashboard reports both, and the Model Evaluation menu
  makes the distinction explicit.
- **Flood share over total R².** Total R² mixes flooding with the controls, so the
  Model Evaluation menu leads with the flood share and tags a control-driven R² as
  such.
- **Interior points, not centroids.** Regency map markers and spatial weights use
  `representative_point()`, which is guaranteed to fall inside the polygon.
- **Map drill-down.** The Province choropleth zooms to the selected province via a
  computed centre/zoom (`compute_province_view`).
- **Quadrant scatter.** The Province FSI-vs-growth scatter splits at the province
  median FSI and median growth — a descriptive cross-regency view, not the causal
  within-regency estimate.
- **FSI single-sourced.** The Economic and Social pages never recompute FSI; they
  join the Flood regency table at runtime so the index and ranking match the Flood
  page.

## License

Released for academic and policy-research use. Disaster records sourced from BNPB;
socioeconomic indicators from BPS Statistics Indonesia.
