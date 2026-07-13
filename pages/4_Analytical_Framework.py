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

  Tab 3 — Causal & Predictive (RQ2: FE + XGBoost + SHAP)
    5. Two-way fixed-effects panel regression (inference)
    6. XGBoost gradient-boosting model (prediction)
    7. SHAP feature attribution
    8. Synthesis: how the two lenses fit together

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
        "spatial diagnostics, temporal trend, causal and predictive "
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
        "Pipeline: K-means &rarr; FSI &rarr; Moran's I &rarr; Gi* &rarr; "
        "Mann-Kendall &rarr; Panel FE &rarr; XGBoost &rarr; SHAP. "
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
    f'K-means &nbsp;&rarr;&nbsp; FSI &nbsp;&rarr;&nbsp; Moran\'s I &nbsp;&rarr;&nbsp; Gi* &nbsp;&rarr;&nbsp; '
    f'Mann-Kendall &nbsp;&rarr;&nbsp; '
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
        f'K-means clustering first identifies typological groups and derives the '
        f'FSI dimension weights. The FSI composite is then constructed, and '
        f'spatial autocorrelation (Moran\'s I) and local clustering (Gi*) '
        f'are tested on the cumulative FSI.'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Card 1: K-means clustering typology (NEW) ───────────────────
    render_method_card(
        phase="Phase 0 · Foundation",
        title="K-means cluster typology (k=3)",
        rq_tag="RQ1",
        narrative=(
            "Groups 514 regencies into k=3 K-means clusters based on "
            "standardised flood-burden dimensions (frequency, casualty, damage). "
            "Two outputs feed the rest of the pipeline: (1) cluster labels — used "
            "as the primary categorical typology in the dashboard map, and "
            "(2) &eta;&sup2; (eta-squared) of each dimension across clusters — "
            "normalised to produce the FSI weights below."
        ),
        stats_html=(
            "<strong>Algorithm</strong>&nbsp;&nbsp; K-means++ (scikit-learn), "
            "k=3, n_init=20, random_state fixed for reproducibility<br>"
            "<strong>Input</strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; "
            "Z-standardised (log_event, HCI, PDI) matrix, n=514<br>"
            "<strong>Validation</strong>&nbsp; Silhouette score, "
            "bootstrap cluster stability (BCV)<br>"
            "<br>"
            "<strong>Cluster profile</strong> (raw composite-dimension means)<br>"
            "&nbsp;&nbsp;<span style='color:#0F6E56;font-weight:600;'>&#9646;</span> "
            "<strong>Low Impact</strong>&nbsp; (n=170)<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp; <em style='color:#6b7280;'>Low across all dimensions</em><br>"
            "&nbsp;&nbsp;&nbsp;&nbsp; log_event=1.76 &middot; HCI=0.67 &middot; PDI=7.95<br>"
            "&nbsp;&nbsp;<span style='color:#A32D2D;font-weight:600;'>&#9646;</span> "
            "<strong>Catastrophic</strong>&nbsp; (n=68)<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp; <em style='color:#6b7280;'>Extreme casualty (HCI), high damage</em><br>"
            "&nbsp;&nbsp;&nbsp;&nbsp; log_event=3.28 &middot; HCI=7.60 &middot; PDI=20.23<br>"
            "&nbsp;&nbsp;<span style='color:#854F0B;font-weight:600;'>&#9646;</span> "
            "<strong>Frequent-Contained</strong>&nbsp; (n=276)<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp; <em style='color:#6b7280;'>High frequency, contained casualty, moderate damage</em><br>"
            "&nbsp;&nbsp;&nbsp;&nbsp; log_event=3.39 &middot; HCI=1.65 &middot; PDI=15.87<br>"
            "<br>"
            "<strong>Derived FSI weights</strong> (&eta;&sup2;-normalised)<br>"
            "&nbsp;&nbsp;w<sub>freq</sub> = <span style='color:#3730a3;font-weight:600;'>0.3062</span> "
            "(frequency)<br>"
            "&nbsp;&nbsp;w<sub>HCI</sub>&nbsp;&nbsp; = <span style='color:#3730a3;font-weight:600;'>0.3697</span> "
            "(casualty &mdash; strongest discriminator)<br>"
            "&nbsp;&nbsp;w<sub>PDI</sub>&nbsp;&nbsp; = <span style='color:#3730a3;font-weight:600;'>0.3241</span> "
            "(property damage)<br>"
            "<br>"
            "<strong>Naming convention</strong>&nbsp; The label "
            "&lsquo;Catastrophic&rsquo; refers to the cluster (extreme casualty "
            "profile), NOT a severity threshold. The earlier 4-tier FSI "
            "classification (Catastrophic/High/Moderate/Low) has been retired "
            "to eliminate semantic conflict."
        ),
        
    )

    # ── Card 2: FSI construction (foundation) ────────────────────────
    render_method_card(
        phase="Phase 1 · Composite",
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
            "<strong>Pre-Z dimensions</strong> (log-summed raw counts)<br>"
            "&nbsp;&nbsp;log_event = log(event_count + 1)<br>"
            "&nbsp;&nbsp;HCI&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; = log(deaths+1) + log(missing+1) + log(injured+1)<br>"
            "&nbsp;&nbsp;PDI&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; = log(houses_flooded+1) + log(houses_damaged+1) + log(fasum+1)<br>"
            "<br>"
            "<strong>Z-standardisation</strong> (pooled across 5,140 regency-years)<br>"
            "&nbsp;&nbsp;Z<sub>freq</sub> = pooled_zscore(log_event)<br>"
            "&nbsp;&nbsp;Z<sub>HCI</sub>&nbsp;&nbsp; = pooled_zscore(HCI)<br>"
            "&nbsp;&nbsp;Z<sub>PDI</sub>&nbsp;&nbsp; = pooled_zscore(PDI)<br>"
            "<br>"
            "<strong>Weights</strong> (k-means &eta;&sup2;-normalised, k=3 &mdash; from Card 1)<br>"
            "&nbsp;&nbsp;w<sub>freq</sub> = <span style='color:#3730a3;font-weight:600;'>0.3062</span> &middot; "
            "w<sub>HCI</sub> = <span style='color:#3730a3;font-weight:600;'>0.3697</span> &middot; "
            "w<sub>PDI</sub> = <span style='color:#3730a3;font-weight:600;'>0.3241</span><br>"
            "<br>"
            "<strong>Display scale</strong>&nbsp;&nbsp; FSI_index = min-max(FSI) &times; 100, "
            "range [0, 100]&nbsp;&nbsp;<em style='color:#6b7280;'>"
            "(visualisation only &mdash; preserves rank order)</em><br>"
            "<br>"
            "<strong>Two forms (dual-FSI design)</strong><br>"
            "&nbsp;&nbsp;<strong>Form 1</strong> &mdash; Z-weighted FSI = w &middot; Z(log_x)<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&rarr; Phase 1&ndash;2: Moran's I, Gi* (spatial autocorrelation)<br>"
            "&nbsp;&nbsp;<strong>Form 2</strong> &mdash; Log-weighted FSI<sub>log</sub> = w &middot; log_x<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&rarr; Phase 3: Mann-Kendall (temporal trend)<br>"
            "<br>"
            "Both forms share identical cluster weights. Form 2 omits the "
            "Z-standardisation step to preserve year-over-year magnitude "
            "that Mann-Kendall is designed to detect."
        ),
        
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
            "&nbsp;&nbsp;I&nbsp;&nbsp;&nbsp;&nbsp;= <span style='color:#3730a3;font-weight:600;'>0.3347</span><br>"
            "&nbsp;&nbsp;p-value = <span style='color:#3730a3;font-weight:600;'>&lt; 0.001</span> "
            "(999 permutations)<br>"
            "&nbsp;&nbsp;&rarr; Strong positive spatial autocorrelation confirmed."
        ),
        
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
            "&nbsp;&nbsp;<strong>Total significant hot spots: "
            "<span style='color:#3730a3;font-weight:600;'>60 regencies</span></strong> "
            "(p &lt; 0.10)<br>"
            "&nbsp;&nbsp;Strongest 10 all concentrated in Aceh province "
            "&mdash; the dominant regional cluster."
        ),
        
    )


# ═════════════════════════════════════════════════════════════════════
# TAB 2 — TEMPORAL TREND  (Mann-Kendall)
# ═════════════════════════════════════════════════════════════════════
with tab_temporal:
    st.markdown(
        f'<div style="font-family:{FONT_BODY};font-size:12.5px;color:{MUTED};'
        f'line-height:1.55;margin-bottom:14px;max-width:760px;">'
        f'How is each regency&rsquo;s flood burden changing over 2016&ndash;2025? '
        f'Mann-Kendall tests whether each regency&rsquo;s flood burden shows a '
        f'significant monotonic trend over 2016&ndash;2025.'
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
            "annual log-weighted FSI<sub>log</sub> (Form 2) over 2016&ndash;2025. "
            "No distributional assumption; robust to outliers and zero-inflation. "
            "The log-weighted form preserves year-over-year magnitude, which "
            "Mann-Kendall is designed to detect. Hamed-Rao correction handles "
            "serial autocorrelation; Benjamini-Hochberg FDR controls "
            "multiple-testing false discoveries."
        ),
        stats_html=(
            "<strong>Test statistic</strong><br>"
            "S = &Sigma;<sub>i&lt;j</sub> sign(y<sub>j</sub> &minus; y<sub>i</sub>)<br>"
            "Kendall&rsquo;s &tau; = S / (n(n&minus;1)/2),&nbsp;&nbsp;range [&minus;1, +1]<br>"
            "<br>"
            "<strong>Input</strong>&nbsp;&nbsp; FSI<sub>log</sub> annual series, "
            "n=10 per regency, 514 regencies<br>"
            "<strong>Method</strong>&nbsp; Hamed-Rao modification "
            "(autocorrelation-corrected variance)<br>"
            "<strong>FDR</strong>&nbsp;&nbsp;&nbsp;&nbsp; Benjamini-Hochberg, &alpha; = 0.05, applied per variable<br>"
            "<br>"
            "<strong>Result (per-regency, after FDR)</strong><br>"
            "&nbsp;&nbsp;Confirmed rising&nbsp;&nbsp;&nbsp;&nbsp; = <span style='color:#3730a3;font-weight:600;'>7 regencies</span><br>"
            "&nbsp;&nbsp;Confirmed declining = <span style='color:#3730a3;font-weight:600;'>2 regencies</span><br>"
            "&nbsp;&nbsp;Inconclusive&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; = 505 regencies (NOT confirmed stable)<br>"
            "<br>"
            "<strong>Result (national aggregate)</strong><br>"
            "&nbsp;&nbsp;&tau; = <span style='color:#3730a3;font-weight:600;'>0.60</span> "
            "&middot; Hamed-Rao p = <span style='color:#3730a3;font-weight:600;'>&lt; 0.001</span><br>"
            "&nbsp;&nbsp;&rarr; Indonesia overall is rising (strong signal due to "
            "noise averaging across 514 regencies)."
        ),
        
    )


# ═════════════════════════════════════════════════════════════════════
# TAB 3 — CAUSAL & PREDICTIVE  (RQ2: FE + XGBoost + SHAP)
# ═════════════════════════════════════════════════════════════════════
with tab_causal:
    st.markdown(
        f'<div style="font-family:{FONT_BODY};font-size:12.5px;color:{MUTED};'
        f'line-height:1.55;margin-bottom:14px;max-width:760px;">'
        f'How do flood patterns translate into socioeconomic outcomes, and '
        f'what drives the prediction? Two complementary lenses: fixed-effects '
        f'panel regression for causal inference (does flooding have a '
        f'significant effect?) and XGBoost with SHAP for predictive evaluation '
        f'(can flooding predict the outcome, and which features drive it?). '
        f'Full per-outcome results are in the Model Evaluation menu.'
        f'</div>',
        unsafe_allow_html=True,
    )

    # -- Card: Two-way fixed-effects panel regression --
    render_method_card(
        phase="Phase 5 - Causal inference",
        title="Two-way fixed-effects panel regression",
        rq_tag="RQ2",
        narrative=(
            "Estimates the association between flood exposure and each "
            "socioeconomic outcome while absorbing time-invariant regency "
            "characteristics (entity effects) and common national shocks "
            "(year effects). Clustered standard errors account for "
            "within-regency correlation. This is the inferential model: it "
            "tests whether flood coefficients are statistically significant, "
            "not whether they predict out-of-sample."
        ),
        stats_html=(
            "<strong>Specification</strong><br>"
            "Y<sub>it</sub> = &beta;<sub>1</sub>&middot;FloodFreq<sub>it</sub> + "
            "&beta;<sub>2</sub>&middot;FloodSeverity<sub>it</sub> + "
            "&gamma;&middot;X<sub>it</sub> + &alpha;<sub>i</sub> + "
            "&delta;<sub>t</sub> + &epsilon;<sub>it</sub><br>"
            "<br>"
            "<strong>Terms</strong><br>"
            "&nbsp;&nbsp;&alpha;<sub>i</sub> = regency fixed effects (time-invariant traits)<br>"
            "&nbsp;&nbsp;&delta;<sub>t</sub> = year fixed effects (national shocks, climate)<br>"
            "&nbsp;&nbsp;X<sub>it</sub> = controls (log population, mean years schooling)<br>"
            "<br>"
            "<strong>Estimator</strong>&nbsp; PanelOLS (linearmodels), "
            "entity + time effects, clustered SE by regency<br>"
            "<strong>Outcomes</strong>&nbsp; GRDP growth, poverty rate, "
            "unemployment (TPT); 17 sector growth rates<br>"
            "<br>"
            "<strong>Headline result (growth)</strong><br>"
            "&nbsp;&nbsp;PDI (physical damage): &beta; = "
            "<span style='color:#3730a3;font-weight:600;'>-0.022</span>, "
            "p = <span style='color:#3730a3;font-weight:600;'>0.019</span> "
            "(significant &amp; negative)<br>"
            "&nbsp;&nbsp;Flood-block joint Wald p = "
            "<span style='color:#3730a3;font-weight:600;'>0.003</span><br>"
            "&nbsp;&nbsp;Poverty: flood block NOT significant (cleanest null)<br>"
            "&nbsp;&nbsp;Unemployment: fragile (DK-only, signs flip)"
        ),
        
    )

    # -- Card: XGBoost predictive model --
    render_method_card(
        phase="Phase 6 - Prediction",
        title="XGBoost gradient-boosting model",
        rq_tag="RQ2",
        narrative=(
            "Gradient-boosted regression trees test whether flood exposure "
            "can PREDICT each outcome out-of-sample, capturing any non-linear "
            "or threshold effects a linear model would miss. Tuned by grouped "
            "cross-validation; evaluated on an untouched 2024-25 test set "
            "against a naive mean baseline. This answers a different question "
            "from FE: predictability, not significance."
        ),
        stats_html=(
            "<strong>Algorithm</strong>&nbsp; XGBoost regressor "
            "(squared-error objective), 324-combination grid search<br>"
            "<strong>Validation</strong>&nbsp; GroupKFold by regency "
            "(no regency in both train and test fold)<br>"
            "<strong>Split</strong>&nbsp;&nbsp;&nbsp;&nbsp; train 2016-2022 / "
            "validation 2023 / test 2024-2025 (temporal)<br>"
            "<strong>Metrics</strong>&nbsp; R&sup2;, RMSE, MAE + naive baseline; "
            "bootstrap R&sup2; 95% CI<br>"
            "<br>"
            "<strong>Headline result</strong><br>"
            "&nbsp;&nbsp;Growth test-R&sup2; = "
            "<span style='color:#3730a3;font-weight:600;'>&asymp; 0 (negative)</span> "
            "- predictions collapse to the mean<br>"
            "&nbsp;&nbsp;Poverty test-R&sup2; = "
            "<span style='color:#3730a3;font-weight:600;'>+0.40</span>, but "
            "driven by controls (flood share 13%)<br>"
            "&nbsp;&nbsp;Across 17 sectors: no sector is both FE-significant "
            "and XGBoost-predictive<br>"
            "<br>"
            "<strong>Key reading</strong>&nbsp; significance &ne; "
            "predictability - a real but small linear effect need not "
            "translate into out-of-sample predictive power."
        ),
        
    )

    # -- Card: SHAP attribution --
    render_method_card(
        phase="Phase 7 - Attribution",
        title="SHAP feature attribution",
        rq_tag="RQ2",
        narrative=(
            "Decomposes each XGBoost prediction into additive per-feature "
            "contributions grounded in cooperative game theory (Shapley "
            "values). SHAP answers which features the model relies on and in "
            "what direction - here it reveals that where predictive power "
            "exists (e.g. poverty), it comes from control variables, not "
            "flooding (flood share 13-15%). SHAP is interpretation, not a "
            "model that learns: it inherits the quality of the tuned XGBoost."
        ),
        stats_html=(
            "<strong>Method</strong>&nbsp; TreeExplainer (exact SHAP for tree "
            "ensembles)<br>"
            "<strong>Additivity</strong>&nbsp; prediction = base value + "
            "&Sigma; SHAP(feature)<br>"
            "<strong>Views</strong>&nbsp;&nbsp;&nbsp;&nbsp; beeswarm (per-obs "
            "beeswarm), bar (mean|SHAP| importance), waterfall (single obs)<br>"
            "<br>"
            "<strong>Flood share of importance</strong><br>"
            "&nbsp;&nbsp;Growth = <span style='color:#3730a3;font-weight:600;'>~64%</span> "
            "of a tiny total (importance &ne; effect)<br>"
            "&nbsp;&nbsp;Poverty = <span style='color:#3730a3;font-weight:600;'>13%</span> "
            "(schooling &amp; population dominate)<br>"
            "&nbsp;&nbsp;Unemployment = <span style='color:#3730a3;font-weight:600;'>~15%</span><br>"
            "<br>"
            "<strong>Base value</strong>&nbsp; &asymp; training-mean outcome; "
            "predictions stay near it &rarr; consistent with R&sup2; &asymp; 0."
        ),

    )

    # -- Synthesis pipeline card --
    st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
    synth_style = (
        f"background:white;border:1px solid {HAIRLINE};border-radius:8px;"
        f"padding:24px;margin-bottom:24px;"
    )
    st.markdown(
        f'<div style="{synth_style}">'
        f'<div style="font-family:{FONT_MONO};font-size:10px;font-weight:600;'
        f'letter-spacing:0.10em;text-transform:uppercase;color:{MUTED};">'
        f'Synthesis &middot; how the two lenses fit together'
        f'</div>'
        f'<div style="font-family:{FONT_DISPLAY};font-size:16px;font-weight:600;'
        f'color:{INK};margin-top:6px;margin-bottom:10px;">'
        f'FE (inference) + XGBoost/SHAP (prediction)'
        f'</div>'
        f'<div style="font-family:{FONT_BODY};font-size:12.5px;color:{INK};'
        f'line-height:1.6;max-width:720px;">'
        f'Fixed effects identifies whether flooding has a statistically '
        f'significant effect (e.g. physical damage lowers growth). XGBoost then '
        f'tests whether that effect is strong enough to predict outcomes for '
        f'unseen years - it is not. SHAP explains why: flood features contribute '
        f'little, and where R&sup2; is high (poverty) the signal comes from '
        f'structural controls, not flooding. The two methods converge on one '
        f'honest conclusion - <strong>flooding is significantly associated with '
        f'some outcomes but is not a strong predictor of them</strong>.'
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
    f'FSI weights &middot; w_freq=0.3062, w_HCI=0.3697, w_PDI=0.3241 (k-means &eta;&sup2;) &middot; '
    f'Significance &middot; BH-FDR &alpha;=0.05'
    f'</div>',
    unsafe_allow_html=True,
)