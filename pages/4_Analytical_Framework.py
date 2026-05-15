"""
pages/4_Analytical_Framework.py
================================
Analytical Framework menu — methodology reference for RQ1 and RQ2.

Layout (3 tabs, static cards):

  Tab 1 — Spatial diagnostics
    1. FSI construction (foundation — used by Moran's I and Gi*)
    2. Global Moran's I
    3. Hot/cold spot map (Gi*)

  Tab 2 — Temporal trend
    4. Mann-Kendall trend test
    5. Theil-Sen slope estimator

  Tab 3 — Causal & Predictive (placeholder for future RQ2 work)
    6. Panel regression formula
    7. Assumption diagnostics (7 tests)
    8. XGBoost predictor
    9. Performance metrics
    10. SHAP attribution
    11. Feature importance bars
    12. Synthesis pipeline diagram

Cards are static (no expand/collapse) — methodology is always visible.
Density: short narrative (1-2 sentences) + key statistics + reference.
"""

import streamlit as st

from lib.colors import (
    INK, MUTED, HAIRLINE, INDIGO,
    FONT_DISPLAY, FONT_BODY, FONT_MONO,
)

from components.section_header import render_page_header, render_section_header
from components.sidebar_nav    import render_sidebar_nav


st.set_page_config(
    page_title="FloodX — Analytical Framework",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── Page-scoped CSS — readability column + custom tab styling ──────
st.markdown("""
<style>
  /* Readability column for description prose */
  section.main div[data-testid="stMarkdownContainer"] > p {
    max-width: 760px;
    line-height: 1.55;
  }
  section.main div[data-testid="stMarkdownContainer"] > ul > li {
    max-width: 760px;
  }
  /* Tab list — professional spacing */
  div[data-baseweb="tab-list"] {
    gap: 8px !important;
    border-bottom: 2px solid #e5e7eb !important;
    margin-bottom: 18px !important;
  }
  button[data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    color: #6b7280 !important;
    padding: 10px 22px !important;
    letter-spacing: 0.01em !important;
    transition: color 120ms ease;
  }
  button[data-baseweb="tab"]:hover {
    color: #374151 !important;
  }
  button[data-baseweb="tab"][aria-selected="true"] {
    color: #1e3a8a !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #1e3a8a !important;
    margin-bottom: -2px !important;
  }
  /* Hide Streamlit's default tab highlight bar (we use our own underline) */
  div[data-baseweb="tab-highlight"] {
    display: none !important;
  }
</style>
""", unsafe_allow_html=True)


# Sidebar nav
with st.sidebar:
    render_sidebar_nav()


# ─────────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────────
render_page_header(
    menu_label="Evidence · Analytical Framework",
    title="Analytical Framework",
    description=(
        "Statistical and machine-learning methods underpinning RQ1 and "
        "RQ2. Three tabs organise the methodology by analytical question: "
        "spatial diagnostics, temporal trend, and causal &amp; predictive "
        "analysis."
    ),
)


# ─────────────────────────────────────────────────────────────────────
# Reusable static card renderer
# ─────────────────────────────────────────────────────────────────────
def render_method_card(
    phase: str,
    title: str,
    rq_tag: str,
    narrative: str,
    stats_html: str,
    reference: str = "",
    placeholder: bool = False,
):
    """A static methodology card. Renders title, RQ chip, narrative,
    statistics block, and optional reference. No expand/collapse."""

    chip_bg = {
        "RQ1": "#e0e7ff",
        "RQ2": "#fef3c7",
        "RQ1 + RQ2": "#dbeafe",
    }.get(rq_tag, "#f3f4f6")
    chip_fg = {
        "RQ1": "#3730a3",
        "RQ2": "#92400e",
        "RQ1 + RQ2": "#1e3a8a",
    }.get(rq_tag, MUTED)

    placeholder_chip = (
        f'<span style="display:inline-block;padding:2px 8px;border-radius:10px;'
        f'font-family:{FONT_MONO};font-size:9.5px;font-weight:600;'
        f'letter-spacing:0.04em;color:{MUTED};background:#f3f4f6;'
        f'margin-left:6px;">PLACEHOLDER</span>'
        if placeholder else ''
    )

    card_html = (
        f'<div style="background:white;border:1px solid {HAIRLINE};'
        f'border-radius:8px;padding:16px 20px;margin-bottom:12px;">'
        f'<div style="display:flex;align-items:flex-start;justify-content:space-between;'
        f'gap:10px;margin-bottom:6px;">'
        f'<div style="font-family:{FONT_MONO};font-size:9.5px;font-weight:600;'
        f'letter-spacing:0.10em;text-transform:uppercase;color:{MUTED};">'
        f'{phase}'
        f'</div>'
        f'<div>'
        f'<span style="display:inline-block;padding:2px 8px;border-radius:10px;'
        f'font-family:{FONT_MONO};font-size:9.5px;font-weight:600;'
        f'letter-spacing:0.04em;color:{chip_fg};background:{chip_bg};">'
        f'{rq_tag}'
        f'</span>'
        f'{placeholder_chip}'
        f'</div>'
        f'</div>'
        f'<div style="font-family:{FONT_DISPLAY};font-size:16px;font-weight:600;'
        f'color:{INK};margin-bottom:8px;line-height:1.3;">'
        f'{title}'
        f'</div>'
        f'<div style="font-family:{FONT_BODY};font-size:12.5px;color:{INK};'
        f'line-height:1.6;margin-bottom:10px;max-width:720px;">'
        f'{narrative}'
        f'</div>'
        f'<div style="font-family:{FONT_MONO};font-size:11.5px;color:{INK};'
        f'background:#fafaf9;border:1px solid {HAIRLINE};border-radius:6px;'
        f'padding:10px 14px;line-height:1.7;">'
        f'{stats_html}'
        f'</div>'
    )
    if reference:
        card_html += (
            f'<div style="font-family:{FONT_BODY};font-size:10.5px;font-style:italic;'
            f'color:{MUTED};margin-top:8px;line-height:1.5;">'
            f'{reference}'
            f'</div>'
        )
    card_html += '</div>'

    st.markdown(card_html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# Master overview — pipeline breadcrumb (above the tabs)
# ─────────────────────────────────────────────────────────────────────
render_section_header(
    kicker="Method index",
    title="Statistical and ML methods",
    description=(
        "Pipeline: FSI &rarr; Moran's I &rarr; Gi* &rarr; Mann-Kendall &rarr; "
        "Theil-Sen &rarr; Panel FE &rarr; XGBoost &rarr; SHAP. "
        "Three tabs organise the cards by analytical question."
    ),
)

st.markdown(
    f'<div style="background:white;border:1px solid {HAIRLINE};border-radius:8px;'
    f'padding:14px 18px;margin-top:6px;margin-bottom:18px;">'
    f'<div style="font-family:{FONT_MONO};font-size:10px;font-weight:600;'
    f'letter-spacing:0.08em;text-transform:uppercase;color:{MUTED};">'
    f'Pipeline overview'
    f'</div>'
    f'<div style="font-family:{FONT_DISPLAY};font-size:15px;font-weight:600;'
    f'color:{INK};margin-top:4px;line-height:1.4;">'
    f'FSI &nbsp;&rarr;&nbsp; Moran\'s I &nbsp;&rarr;&nbsp; Gi* &nbsp;&rarr;&nbsp; '
    f'Mann-Kendall &nbsp;&rarr;&nbsp; Theil-Sen &nbsp;&rarr;&nbsp; '
    f'Panel FE &nbsp;&rarr;&nbsp; XGBoost &nbsp;&rarr;&nbsp; SHAP'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────
# THREE TABS
# ─────────────────────────────────────────────────────────────────────
tab_spatial, tab_temporal, tab_causal = st.tabs([
    "Spatial diagnostics",
    "Temporal trend",
    "Causal & Predictive",
])


# ═════════════════════════════════════════════════════════════════════
# TAB 1 — SPATIAL DIAGNOSTICS  (FSI · Moran's I · Gi*)
# ═════════════════════════════════════════════════════════════════════
with tab_spatial:
    st.markdown(
        f'<div style="font-family:{FONT_BODY};font-size:12.5px;color:{MUTED};'
        f'line-height:1.55;margin-bottom:14px;max-width:760px;">'
        f'How is flood severity distributed across the 514 regencies? '
        f'The FSI composite is constructed first, then spatial autocorrelation '
        f'(Moran\'s I) and local clustering (Gi*) are tested on the cumulative FSI.'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Card 1: FSI construction (foundation) ────────────────────────
    render_method_card(
        phase="Phase 1 · Foundation",
        title="FSI construction (cluster-weighted composite)",
        rq_tag="RQ1",
        narrative=(
            "Combines three flood-burden dimensions &mdash; event frequency, "
            "Human Cost Index (HCI), and Property Damage Index (PDI) &mdash; "
            "into a single per-regency severity index. Dimension weights are "
            "empirically derived from k-means &eta;&sup2; (not assumed equal)."
        ),
        stats_html=(
            "<strong>Formula</strong><br>"
            "FSI = w<sub>freq</sub> &middot; Z<sub>freq</sub> + "
            "w<sub>HCI</sub> &middot; Z<sub>HCI</sub> + "
            "w<sub>PDI</sub> &middot; Z<sub>PDI</sub><br>"
            "<br>"
            "<strong>Dimensions</strong> (log-summed raw counts, then Z-scored)<br>"
            "&nbsp;&nbsp;Z<sub>freq</sub> = log(event_count + 1)<br>"
            "&nbsp;&nbsp;Z<sub>HCI</sub>&nbsp;&nbsp; = log(deaths+1) + log(missing+1) + log(injured+1)<br>"
            "&nbsp;&nbsp;Z<sub>PDI</sub>&nbsp;&nbsp; = log(houses_flooded+1) + log(houses_damaged+1) + log(fasum+1)<br>"
            "<br>"
            "<strong>Weights</strong> (k-means &eta;&sup2;-normalised, k=3)<br>"
            "&nbsp;&nbsp;w<sub>freq</sub> = 0.302 &middot; "
            "w<sub>HCI</sub> = 0.360 &middot; "
            "w<sub>PDI</sub> = 0.338<br>"
            "<br>"
            "<strong>Display</strong>&nbsp;&nbsp; FSI_percent = min-max(FSI) &times; 100, "
            "range [0, 100]<br>"
            "<strong>Tiers</strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; "
            "Catastrophic &ge;75 &middot; High 50&ndash;75 &middot; "
            "Moderate 25&ndash;50 &middot; Low &lt;25<br>"
            "<br>"
            "<strong>Two forms</strong><br>"
            "&nbsp;&nbsp;Cumulative Z-scored FSI&nbsp;&rarr;&nbsp; spatial tests "
            "(Moran/Gi*)<br>"
            "&nbsp;&nbsp;FSI_temporal_pct&nbsp;&rarr;&nbsp; trend test (Mann-Kendall)"
        ),
        reference="Cutter et al. (2003). Social Vulnerability to Environmental Hazards. SSQ 84(2): 242&ndash;261.",
    )

    # ── Card 2: Global Moran's I ─────────────────────────────────────
    render_method_card(
        phase="Phase 2 · Spatial test",
        title="Global Moran's I",
        rq_tag="RQ1",
        narrative=(
            "Tests whether high-FSI regencies cluster geographically rather "
            "than being randomly distributed. Rejection of the null indicates "
            "statistically significant spatial autocorrelation."
        ),
        stats_html=(
            "<strong>Formula</strong><br>"
            "I = (N / W) &middot; "
            "&Sigma;<sub>i</sub>&Sigma;<sub>j</sub> w<sub>ij</sub>(x<sub>i</sub>&minus;x&#772;)(x<sub>j</sub>&minus;x&#772;) "
            "/ &Sigma;<sub>i</sub>(x<sub>i</sub>&minus;x&#772;)&sup2;<br>"
            "<br>"
            "<strong>Input</strong>&nbsp;&nbsp; Cumulative Z-scored FSI, 514 regencies, 2016&ndash;2025<br>"
            "<strong>Weights</strong>&nbsp; KNN k=5, row-standardised (each row sums to 1)<br>"
            "<strong>Significance</strong>&nbsp; Permutation test, 999 random shuffles<br>"
            "<br>"
            "<strong>Result</strong><br>"
            "&nbsp;&nbsp;I&nbsp;&nbsp;&nbsp;&nbsp;= <span style='color:#3730a3;font-weight:600;'>0.335</span><br>"
            "&nbsp;&nbsp;p-value = <span style='color:#3730a3;font-weight:600;'>&lt; 0.001</span> "
            "(999 permutations)<br>"
            "&nbsp;&nbsp;&rarr; Strong positive spatial autocorrelation confirmed."
        ),
        reference="Moran, P. A. P. (1950). Notes on Continuous Stochastic Phenomena. Biometrika 37(1/2): 17&ndash;23.",
    )

    # ── Card 3: Gi* hot spots ────────────────────────────────────────
    render_method_card(
        phase="Phase 3 · Spatial map",
        title="Hot/cold spot map (Getis-Ord Gi*)",
        rq_tag="RQ1",
        narrative=(
            "Identifies WHERE the spatial clustering is located &mdash; "
            "which individual regencies form statistically significant hot or "
            "cold zones. Per-regency z-score quantifies how much the regency "
            "and its neighbours deviate from the national mean."
        ),
        stats_html=(
            "<strong>Formula</strong><br>"
            "Gi*<sub>i</sub> = "
            "(&Sigma;<sub>j</sub> w<sub>ij</sub>x<sub>j</sub> &minus; "
            "x&#772; &middot; &Sigma;<sub>j</sub> w<sub>ij</sub>) "
            "/ (s &middot; "
            "&radic;[(N &middot; &Sigma;<sub>j</sub> w<sub>ij</sub>&sup2; &minus; "
            "(&Sigma;<sub>j</sub> w<sub>ij</sub>)&sup2;) / (N&minus;1)])<br>"
            "<br>"
            "<strong>Input</strong>&nbsp;&nbsp; Same FSI + KNN k=5 (binary weights, NOT row-standardised)<br>"
            "<br>"
            "<strong>Categorisation</strong> (z-score thresholds)<br>"
            "&nbsp;&nbsp;z &gt; 2.576 &rarr; Hot 99% (p&lt;0.01)<br>"
            "&nbsp;&nbsp;z &gt; 1.960 &rarr; Hot 95% (p&lt;0.05)<br>"
            "&nbsp;&nbsp;z &gt; 1.645 &rarr; Hot 90% (p&lt;0.10)<br>"
            "&nbsp;&nbsp;z &lt; &minus;1.645 &rarr; Cold 90% / 95% / 99% (mirror)<br>"
            "<br>"
            "<strong>Result</strong><br>"
            "&nbsp;&nbsp;Hot 99% = <span style='color:#3730a3;font-weight:600;'>12 regencies</span> &middot; "
            "Hot 95% = <span style='color:#3730a3;font-weight:600;'>19</span> &middot; "
            "Hot 90% = <span style='color:#3730a3;font-weight:600;'>29</span><br>"
            "&nbsp;&nbsp;<strong>Total significant: 60 regencies</strong> "
            "(strongest 10 all in Aceh province)"
        ),
        reference="Getis &amp; Ord (1992). The Analysis of Spatial Association by Use of Distance Statistics. Geographical Analysis 24(3): 189&ndash;206.",
    )


# ═════════════════════════════════════════════════════════════════════
# TAB 2 — TEMPORAL TREND  (Mann-Kendall · Theil-Sen)
# ═════════════════════════════════════════════════════════════════════
with tab_temporal:
    st.markdown(
        f'<div style="font-family:{FONT_BODY};font-size:12.5px;color:{MUTED};'
        f'line-height:1.55;margin-bottom:14px;max-width:760px;">'
        f'How is each regency&rsquo;s flood burden changing over 2016&ndash;2025? '
        f'Mann-Kendall tests trend significance (yes/no); Theil-Sen estimates '
        f'the magnitude of annual change.'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Card 4: Mann-Kendall trend test ──────────────────────────────
    render_method_card(
        phase="Phase 4 · Trend test",
        title="Mann-Kendall trend test",
        rq_tag="RQ1",
        narrative=(
            "Non-parametric test for monotonic trends in each regency&rsquo;s "
            "annual FSI_temporal_pct over 2016&ndash;2025. No distributional "
            "assumption; robust to outliers and zero-inflation. Hamed-Rao "
            "correction handles serial autocorrelation; Benjamini-Hochberg FDR "
            "controls multiple-testing false discoveries."
        ),
        stats_html=(
            "<strong>Test statistic</strong><br>"
            "S = &Sigma;<sub>i&lt;j</sub> sign(y<sub>j</sub> &minus; y<sub>i</sub>)<br>"
            "Kendall&rsquo;s &tau; = S / (n(n&minus;1)/2),&nbsp;&nbsp;range [&minus;1, +1]<br>"
            "<br>"
            "<strong>Input</strong>&nbsp;&nbsp; FSI_temporal_pct annual series, "
            "n=10 per regency, 514 regencies<br>"
            "<strong>Method</strong>&nbsp; Hamed-Rao modification "
            "(autocorrelation-corrected variance)<br>"
            "<strong>FDR</strong>&nbsp;&nbsp;&nbsp;&nbsp; Benjamini-Hochberg, &alpha; = 0.05, applied per variable<br>"
            "<br>"
            "<strong>Result (per-regency, after FDR)</strong><br>"
            "&nbsp;&nbsp;Confirmed rising&nbsp;&nbsp;&nbsp;= <span style='color:#3730a3;font-weight:600;'>7 regencies</span><br>"
            "&nbsp;&nbsp;Confirmed falling&nbsp;= <span style='color:#3730a3;font-weight:600;'>2 regencies</span><br>"
            "&nbsp;&nbsp;Inconclusive&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; = 505 regencies (NOT confirmed stable)<br>"
            "<br>"
            "<strong>Result (national aggregate)</strong><br>"
            "&nbsp;&nbsp;&tau; = <span style='color:#3730a3;font-weight:600;'>0.60</span> "
            "&middot; Hamed-Rao p = <span style='color:#3730a3;font-weight:600;'>&lt; 0.001</span><br>"
            "&nbsp;&nbsp;&rarr; Indonesia overall is rising (strong signal due to "
            "noise averaging across 514 regencies)."
        ),
        reference=(
            "Mann (1945) Econometrica 13:245&ndash;259 &middot; "
            "Hamed &amp; Rao (1998) J. Hydrology 204:182&ndash;196 &middot; "
            "Benjamini &amp; Hochberg (1995) JRSS B 57(1):289&ndash;300."
        ),
    )

    # ── Card 5: Theil-Sen slope estimator ────────────────────────────
    render_method_card(
        phase="Phase 5 · Trend slope",
        title="Theil-Sen slope estimator",
        rq_tag="RQ1",
        narrative=(
            "Estimates the annual rate of change as the median of all "
            "pairwise slopes between observations. Pairs naturally with "
            "Mann-Kendall &mdash; same monotonic-trend assumption, robust to "
            "outliers, no Gaussian-residuals requirement."
        ),
        stats_html=(
            "<strong>Estimator</strong><br>"
            "slope<sub>ij</sub> = (y<sub>j</sub> &minus; y<sub>i</sub>) / "
            "(t<sub>j</sub> &minus; t<sub>i</sub>),&nbsp;&nbsp;for all i&lt;j<br>"
            "Theil-Sen = <strong>median</strong>(slope<sub>ij</sub>)<br>"
            "<br>"
            "<strong>Pair count</strong>&nbsp;&nbsp;&nbsp; "
            "n(n&minus;1)/2 = 45 pairwise slopes per regency (n=10 years)<br>"
            "<strong>Confidence interval</strong>&nbsp; 95% Mood (1950) bracket on the median slope<br>"
            "<br>"
            "<strong>Reporting unit</strong><br>"
            "&nbsp;&nbsp;slope_pct = (theil_slope / value<sub>2025</sub>) &times; 100<br>"
            "&nbsp;&nbsp;Interpretation: % change per year, relative to 2025 baseline<br>"
            "<br>"
            "<strong>Used for</strong><br>"
            "&nbsp;&nbsp;Projection: 2027, 2030 values where MK is FDR-significant<br>"
            "&nbsp;&nbsp;Ranking: dashboard &ldquo;Top 10 by rising FSI&rdquo; "
            "sorts by &tau;, displays slope_pct"
        ),
        reference="Sen, P. K. (1968). Estimates of the Regression Coefficient Based on Kendall&rsquo;s Tau. JASA 63(324): 1379&ndash;1389.",
    )


# ═════════════════════════════════════════════════════════════════════
# TAB 3 — CAUSAL & PREDICTIVE  (placeholder for RQ2 work)
# ═════════════════════════════════════════════════════════════════════
with tab_causal:
    st.markdown(
        f'<div style="font-family:{FONT_BODY};font-size:12.5px;color:{MUTED};'
        f'line-height:1.55;margin-bottom:14px;max-width:760px;">'
        f'How do flood patterns translate into socioeconomic outcomes, and '
        f'what drives the prediction? Six methodological cards plus a '
        f'synthesis pipeline. <em>Content placeholder &mdash; full methodology '
        f'to be added as the RQ2 pipeline is implemented.</em>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Card 6: Panel regression ─────────────────────────────────────
    render_method_card(
        phase="Step 1 · Specification",
        title="Panel regression formula",
        rq_tag="RQ2",
        placeholder=True,
        narrative=(
            "Two-way fixed-effects panel regression linking flood indicators "
            "(FSI, event_count) to socioeconomic outcomes (GRDP growth, "
            "poverty rate, unemployment rate / TPT)."
        ),
        stats_html=(
            "<strong>Planned specification (placeholder)</strong><br>"
            "Y<sub>it</sub> = &alpha;<sub>i</sub> + &lambda;<sub>t</sub> + "
            "&beta;<sub>1</sub>&middot;FSI<sub>it</sub> + "
            "&beta;<sub>2</sub>&middot;X<sub>it</sub> + &epsilon;<sub>it</sub><br>"
            "<br>"
            "Where Y<sub>it</sub> = socioeconomic outcome for regency i in year t,<br>"
            "&alpha;<sub>i</sub> = regency fixed effect, "
            "&lambda;<sub>t</sub> = year fixed effect,<br>"
            "&beta;<sub>1</sub> = flood-impact coefficient (parameter of interest)<br>"
            "<br>"
            "<em>To be detailed: regressor list, lag structure, clustered SE, sample, robustness.</em>"
        ),
    )

    # ── Card 7: Assumption tests ─────────────────────────────────────
    render_method_card(
        phase="Step 2 · Diagnostics",
        title="Assumption diagnostics (7 tests)",
        rq_tag="RQ2",
        placeholder=True,
        narrative=(
            "Panel-data assumption checks: multicollinearity, model "
            "specification, autocorrelation, heteroskedasticity, "
            "cross-sectional dependence, unit roots, coefficient stability."
        ),
        stats_html=(
            "<strong>Planned diagnostic suite (placeholder)</strong><br>"
            "&nbsp;1. Variance Inflation Factor (VIF) &mdash; multicollinearity<br>"
            "&nbsp;2. Hausman test &mdash; fixed vs random effects<br>"
            "&nbsp;3. Wooldridge test &mdash; first-order serial correlation<br>"
            "&nbsp;4. Pesaran CD test &mdash; cross-sectional dependence<br>"
            "&nbsp;5. Breusch-Pagan &mdash; heteroskedasticity<br>"
            "&nbsp;6. Im-Pesaran-Shin &mdash; panel unit root<br>"
            "&nbsp;7. CUSUM &mdash; coefficient stability<br>"
            "<br>"
            "<em>To be filled with real test statistics when RQ2 regression runs.</em>"
        ),
    )

    # ── Card 8: XGBoost ──────────────────────────────────────────────
    render_method_card(
        phase="Step 3 · ML",
        title="XGBoost &mdash; function approximator",
        rq_tag="RQ2",
        placeholder=True,
        narrative=(
            "Gradient-boosted regression trees for non-linear prediction of "
            "socioeconomic outcomes. Captures interaction and threshold effects "
            "that linear panel regression cannot."
        ),
        stats_html=(
            "<strong>Planned model (placeholder)</strong><br>"
            "XGBoost (Chen &amp; Guestrin 2016) &mdash; gradient boosting on "
            "regression trees.<br>"
            "<br>"
            "<strong>Configuration (TBD)</strong><br>"
            "&nbsp;&nbsp;Hyperparameter grid: max_depth, eta, n_estimators<br>"
            "&nbsp;&nbsp;Train/validation/test split: 70/15/15<br>"
            "&nbsp;&nbsp;Cross-validation: 5-fold on the train set<br>"
            "&nbsp;&nbsp;Targets: GRDP growth, poverty rate, TPT<br>"
            "<br>"
            "<em>To be filled with real model details when RQ2 ML pipeline runs.</em>"
        ),
    )

    # ── Card 9: Performance metrics ──────────────────────────────────
    render_method_card(
        phase="Step 3 · Metrics",
        title="Performance metrics",
        rq_tag="RQ2",
        placeholder=True,
        narrative=(
            "Out-of-sample evaluation: variance explained (R&sup2;), "
            "absolute error magnitude (RMSE, MAE), and prediction interval "
            "coverage."
        ),
        stats_html=(
            "<strong>Planned metrics (placeholder)</strong><br>"
            "&nbsp;&nbsp;R&sup2; (out-of-sample) &mdash; variance explained<br>"
            "&nbsp;&nbsp;RMSE &mdash; root mean squared error<br>"
            "&nbsp;&nbsp;MAE&nbsp;&nbsp;&nbsp; &mdash; mean absolute error<br>"
            "&nbsp;&nbsp;Coverage &mdash; % of test obs within prediction intervals<br>"
            "<br>"
            "<em>To be filled with real metric values when RQ2 ML pipeline runs.</em>"
        ),
    )

    # ── Card 10: SHAP ────────────────────────────────────────────────
    render_method_card(
        phase="Step 4 · Attribution",
        title="SHAP attribution",
        rq_tag="RQ2",
        placeholder=True,
        narrative=(
            "Shapley-value decomposition: each model prediction is "
            "decomposed into per-feature contributions, providing locally "
            "faithful additive explanations for black-box ML predictions."
        ),
        stats_html=(
            "<strong>Decomposition (placeholder)</strong><br>"
            "f(x) = &phi;<sub>0</sub> + "
            "&Sigma;<sub>j</sub> &phi;<sub>j</sub>(x)<br>"
            "<br>"
            "Where &phi;<sub>j</sub>(x) is the Shapley contribution of "
            "feature j for input x.<br>"
            "<br>"
            "<strong>Why SHAP for this thesis</strong>: bridges XGBoost prediction "
            "with causal interpretation by quantifying which flood indicators "
            "drive predictions per regency.<br>"
            "<br>"
            "<em>To be filled with real SHAP outputs when RQ2 ML pipeline runs.</em>"
        ),
        reference="Lundberg &amp; Lee (2017). A Unified Approach to Interpreting Model Predictions. NeurIPS.",
    )

    # ── Card 11: Feature importance ──────────────────────────────────
    render_method_card(
        phase="Step 4 · Bar chart",
        title="Feature importance bars",
        rq_tag="RQ2",
        placeholder=True,
        narrative=(
            "Global ranking of feature importance using mean absolute SHAP "
            "values. Identifies which flood indicators most influence the "
            "predictive model overall."
        ),
        stats_html=(
            "<strong>Metric (placeholder)</strong><br>"
            "importance<sub>j</sub> = (1/N) &middot; "
            "&Sigma;<sub>i=1..N</sub> |&phi;<sub>j</sub>(x<sub>i</sub>)|<br>"
            "<br>"
            "Bar chart sorted descending by mean |SHAP|. Identifies whether "
            "FSI, event_count, HCI, PDI, or specific sub-components carry the "
            "most predictive weight.<br>"
            "<br>"
            "<em>To be filled with real importance rankings when RQ2 ML pipeline runs.</em>"
        ),
    )

    # ── Synthesis card (placeholder) ─────────────────────────────────
    st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
    placeholder_card_style = (
        f"background:white;border:2px dashed {HAIRLINE};border-radius:8px;"
        f"padding:36px 24px;text-align:center;margin-bottom:24px;"
    )
    st.markdown(
        f'<div style="{placeholder_card_style}">'
        f'<div style="font-family:{FONT_MONO};font-size:10px;font-weight:600;'
        f'letter-spacing:0.10em;text-transform:uppercase;color:{MUTED};">'
        f'Synthesis &middot; pipeline diagram'
        f'</div>'
        f'<div style="font-family:{FONT_DISPLAY};font-size:17px;font-weight:600;'
        f'color:{INK};margin-top:6px;">'
        f'How the trained XGBoost is applied at 2030'
        f'</div>'
        f'<div style="font-family:{FONT_BODY};font-size:12.5px;color:{MUTED};'
        f'margin-top:10px;max-width:540px;margin-left:auto;margin-right:auto;'
        f'line-height:1.55;">'
        f'Placeholder. The pipeline visualisation will show how Phase 3 '
        f'projections (2027/2030 FSI values) feed into the trained XGBoost '
        f'model to predict socioeconomic outcomes, with SHAP attribution '
        f'identifying dominant drivers per regency. '
        f'<br><br>'
        f'<span style="color:{INDIGO};font-weight:600;">RQ1 + RQ2</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="margin-top:18px;padding-top:16px;border-top:1px solid {HAIRLINE};'
    f'font-family:{FONT_MONO};font-size:9.5px;color:{MUTED};'
    f'letter-spacing:0.04em;line-height:1.6;">'
    f'Study period &middot; 2016&ndash;2025 (10 years) &middot; '
    f'N regencies &middot; 514 &middot; '
    f'Spatial weights &middot; KNN k=5 &middot; '
    f'FSI weights &middot; w_freq=0.302, w_HCI=0.360, w_PDI=0.338 (k-means &eta;&sup2;) &middot; '
    f'Significance &middot; BH-FDR &alpha;=0.05'
    f'</div>',
    unsafe_allow_html=True,
)
