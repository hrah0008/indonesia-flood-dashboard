"""
pages/1_Flood.py
================
Flood menu — National view (single page, no scope drill-down).

Content
-------
1. Page header (kicker + title + description)
2. KPI strip — 7 KPIs: avg events/casualties/houses per year, Moran's I,
   hot spots, MK-significant regencies, national trend direction
3. FSI choropleth — 514 regencies, coloured by FSI tier (static map)
4. Annual line chart — FSI dimensions + composite, 2016–2025
5. Top 10 regencies — three views: severity / hot spots / rising trend
6. Key Findings — narrative interpretation of the evidence
7. Footnote — methodology references

Reads from nb12 output:
    public/data/flood/national/{kpis,annual_series,insight}.json
    public/data/flood/national/regency_table.parquet
    public/data/geo/regencies.geojson  (from nb11)
"""

import traceback

import streamlit as st

from lib.data_flood import (
    load_national_kpis,
    load_national_annual,
    load_national_regency_table,
    load_regencies_geojson,
    load_province_kpis,
    load_province_annual,
    load_province_regency_table,
    load_province_scatter,
    load_province_insight,
    load_regency_bundle,
    list_available_provinces,
    assert_data_present,
)
from lib.colors import INK, MUTED, FONT_DISPLAY, FONT_MONO, FONT_BODY
from lib.format import (
    fmt_int, fmt_decimal, fmt_pvalue, fmt_compact, fmt_signed_pct,
)

from components.section_header import render_page_header, render_section_header
from components.kpi_strip       import render_kpi_strip
from components.choropleth      import render_fsi_choropleth, compute_province_view
from components.line_chart      import render_annual_line_chart
from components.ranking_table import (
    render_top10_fsi,
    render_top10_hotspots,
    render_top10_mk,
    compute_top10_overlaps,
    render_table_caption,
)
from components.insight_box     import render_insight_box
from components.sidebar_nav     import render_sidebar_nav


st.set_page_config(
    page_title="Flood — Indonesia Flood Dashboard",
    page_icon=":droplet:",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── Page-scoped CSS — readability column for description prose ──────
st.markdown("""
<style>
  /* Readability column for description prose */
  section.main div[data-testid="stMarkdownContainer"] > p {
    max-width: 760px;
    line-height: 1.55;
  }
  section.main div[data-testid="stMarkdownContainer"] > ul > li,
  section.main div[data-testid="stMarkdownContainer"] > ol > li {
    max-width: 760px;
  }
  /* Tab list — matches Analytical Framework page */
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
  div[data-baseweb="tab-highlight"] { display: none !important; }
  /* Defensive: prevent 0-height tab panel cutting off Plotly */
  div[data-baseweb="tab-panel"] { min-height: 1px; }
</style>
""", unsafe_allow_html=True)

# Sidebar nav (shared component)
with st.sidebar:
    render_sidebar_nav()


# ─────────────────────────────────────────────────────────────────────
# Page header
# ─────────────────────────────────────────────────────────────────────
render_page_header(
    menu_label="Analysis · Flood",
    title="Flood impact across Indonesia",
    description=(
        "Spatial and temporal analysis of flood frequency, human cost, "
        "and property damage from 2016 to 2025."
    ),
)


# ─────────────────────────────────────────────────────────────────────
# Required-data check (cached — runs once per session)
# ─────────────────────────────────────────────────────────────────────
ok, missing = assert_data_present()
if not ok:
    st.error(
        "**Required data files are missing.**\n\n"
        "Expected files (run nb12 then copy outputs to public/data/):\n\n"
        + "\n".join(f"- `{m}`" for m in missing)
    )
    st.stop()


# ─────────────────────────────────────────────────────────────────────
# Load all data up front (each loader cached for the session)
# ─────────────────────────────────────────────────────────────────────
try:
    k       = load_national_kpis()
    annual  = load_national_annual()
    reg_df  = load_national_regency_table()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()
except Exception as e:
    st.error(f"Could not load national data: {e}")
    st.stop()

try:
    geo = load_regencies_geojson()
except FileNotFoundError:
    geo = None

# ─────────────────────────────────────────────────────────────────────
# Three tabs — matches Analytical Framework page
# ─────────────────────────────────────────────────────────────────────
tab_national, tab_province, tab_regency = st.tabs([
    "National", "Province", "Regency",
])

# ═════════════════════════════════════════════════════════════════════
# TAB 1 — NATIONAL
# ═════════════════════════════════════════════════════════════════════
with tab_national:
   
    # ─────────────────────────────────────────────────────────────────────
    # KPI strip — volume + statistical summary
    # ─────────────────────────────────────────────────────────────────────
    n_years = (k.get("year_max", 2025) - k.get("year_min", 2016)) + 1
    avg_events_yr     = (k.get("total_events", 0)  or 0) / n_years
    avg_casualties_yr = (
        ((k.get("total_deaths", 0)  or 0) +
        (k.get("total_missing", 0) or 0) +
        (k.get("total_injured", 0) or 0)) / n_years
    )
    avg_houses_yr     = (k.get("total_houses", 0)  or 0) / n_years

    render_kpi_strip([
        {"label": "Avg events / year",
        "value": fmt_int(avg_events_yr),
        "sublabel": "Nationwide flood events"},
        {"label": "Avg casualties / year",
        "value": fmt_int(avg_casualties_yr),
        "sublabel": "Deaths + missing + injured",
        "tone": "red"},
        {"label": "Avg houses / year",
        "value": fmt_compact(avg_houses_yr),
        "sublabel": "Flooded + damaged"},
        {"label": "Moran's I (FSI)",
        "value": fmt_decimal(k.get("morans_i")),
        "sublabel": fmt_pvalue(k.get("morans_p")),
        "highlight": True},
        {"label": "Hot spots",
        "value": fmt_int(k.get("n_hot_spots")),
        "sublabel": "Gi* sig (p < 0.10)"},
        {"label": "MK sig (FSI)",
        "value": fmt_int(k.get("n_mk_sig_freq")),
        "sublabel": "rising or declining"},
        {"label": "National trend",
        "value": k.get("trend_direction", "—"),
        "sublabel": (
            f"τ = {fmt_decimal(k.get('mk_tau'), 2)} · "
            f"{fmt_signed_pct(k.get('mk_slope_pct'))}/yr"
        ),
        "tone": "red" if k.get("trend_direction") == "Increasing" else None},
    ])

    st.markdown(
        f'<div style="font-family:{FONT_MONO};font-size:10px;color:{MUTED};'
        f'letter-spacing:0.04em;margin-top:8px;text-align:center;">'
        f'Across {fmt_int(k.get("n_regencies"))} regencies in '
        f'{fmt_int(k.get("n_provinces"))} provinces &middot; '
        f'cumulative {fmt_int(k.get("total_events"))} events recorded'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.divider()


    # ─────────────────────────────────────────────────────────────────────
    # Choropleth — FSI by regency (static, no click handler)
    # ─────────────────────────────────────────────────────────────────────
    render_section_header(
        kicker="Spatial · descriptive",
        title=f"FSI Score by regency — {fmt_int(k.get('n_regencies'))} units",
        description=(
            "<strong>Flood Severity Index Score</strong> &mdash; cumulative "
            "2016&ndash;2025 burden per regency on a 0&ndash;100 relative scale "
            "(not a percentage). Tier classes: "
            "<strong>Catastrophic &ge;75</strong>, High 50&ndash;75, "
            "Moderate 25&ndash;50, Low &lt;25. "
            "See <strong>Analytical Framework</strong> menu for full methodology."
        ),
    )

    if geo is None:
        st.warning(
            "GeoJSON file `public/data/geo/regencies.geojson` is missing. "
            "Run nb11 (build_dashboard_geo) and copy `web/regencies.geojson` "
            "to that path."
        )
    else:
        # No on_select — static choropleth. Avoids the silent-render
        # interaction observed when on_select="rerun" is combined with
        # lazy-rendering parents (st.tabs etc).
        try:
            render_fsi_choropleth(
                reg_df=reg_df,
                geojson=geo,
                height=520,
                key="national_choropleth",
            )
        except Exception as e:
            st.error(
                f"**Could not render the choropleth.**\n\n"
                f"`{type(e).__name__}`: {e}\n\n"
                f"Check that `regency_table.parquet` has these columns: "
                f"`kemendagri_kab_code`, `kemendagri_kab_name`, "
                f"`FSI_tier`, `FSI_index`, `event_count`, `deaths`, "
                f"`missing`, `injured`, `house_flooded`."
            )
            with st.expander("Traceback (for debugging)"):
                st.code(traceback.format_exc(), language="python")


    # ─────────────────────────────────────────────────────────────────────
    # Annual line chart
    # ─────────────────────────────────────────────────────────────────────
    render_section_header(
        kicker="Temporal · descriptive",
        title=f"Annual trend {k.get('year_min')}&ndash;{k.get('year_max')}",
        description=(
            "The three FSI dimensions &mdash; event frequency, HCI, PDI "
            "&mdash; alongside the composite FSI Score, each rescaled to "
            "0&ndash;100 for visual comparison. Raw counts togglable. "
            "See <strong>Analytical Framework</strong> for dimension definitions."
        ),
    )
    render_annual_line_chart(
        annual=annual,
        height=440,
        key="national_line",
    )


    # ─────────────────────────────────────────────────────────────────────
    # Top 10 regencies — three views
    # ─────────────────────────────────────────────────────────────────────
    render_section_header(
        kicker="Operational priority",
        title="Top 10 regencies — three views",
        description=(
            "Three rankings on three statistical bases. "
            "<strong>Severity</strong> by cumulative FSI. "
            "<strong>Hot spots</strong> by Gi* spatial clustering. "
            "<strong>Rising FSI</strong> by Mann-Kendall &tau; on annual FSI. "
            "Regencies appearing in more than one list warrant the strongest "
            "policy attention. See <strong>Analytical Framework</strong> for "
            "the statistical detail."
        ),
    )

    overlaps = compute_top10_overlaps(reg_df, top_n=10)

    col_fsi, col_hot, col_mk = st.columns(3, gap="medium")
    with col_fsi:
        render_top10_fsi(reg_df, top_n=10)
        render_table_caption(
            f"<strong>{overlaps['fsi_hot']}</strong> also appear in Hot Spots; "
            f"<strong>{overlaps['fsi_mk']}</strong> also appear in Mann-Kendall."
        )
    with col_hot:
        render_top10_hotspots(reg_df, top_n=10)
        render_table_caption(
            f"High-value regencies surrounded by similarly high-value "
            f"neighbours (Gi* significant). "
            f"<strong>{overlaps['hot_mk']}</strong> also appear in Mann-Kendall."
        )
    with col_mk:
        render_top10_mk(reg_df, top_n=10)
        render_table_caption(
            "Regencies with a statistically significant rising trend in "
            "integrated FSI Score (Mann-Kendall on annual FSI with log-weighted "
            "composite, Hamed-Rao autocorrelation correction; Benjamini-Hochberg "
            "FDR &alpha; = 0.05; ranked by Kendall&rsquo;s &tau;)."
        )


        # ─────────────────────────────────────────────────────────────────────
    # Key Findings — narrative interpretation (Method A primary)
    # ─────────────────────────────────────────────────────────────────────
    render_section_header(
        kicker="Diagnostic synthesis",
        title="Key Findings",
        description=(
            "Narrative interpretation of the spatial and temporal evidence "
            "presented above."
        ),
    )

    bullets = [
        # ── Bullet 1: Spatial clustering (Phase 1) ─────────────────────────
        f"<strong>Flood burden is spatially clustered, not randomly distributed.</strong> "
        f"Global Moran's I = <strong>{fmt_decimal(k.get('morans_i'))}</strong> "
        f"({fmt_pvalue(k.get('morans_p'))}) confirms that high-FSI regencies "
        f"are concentrated near other high-FSI regencies. The clustering is "
        f"strong enough to reject the null of spatial randomness with very "
        f"high confidence, indicating Indonesia's flood vulnerability has "
        f"identifiable regional structure rather than scattered local incidents.",

        # ── Bullet 2: Hot-spot vs severity ranking distinction (Phase 2) ──
        f"<strong>Aceh province dominates the hot-spot map; isolated high-FSI "
        f"regencies do not.</strong> Of <strong>{fmt_int(k.get('n_hot_spots'))} "
        f"Gi*-significant hot spots</strong> (p &lt; 0.10), the strongest 10 "
        f"are all in Aceh &mdash; reflecting a province-wide cluster where "
        f"moderate-to-high-FSI regencies reinforce each other spatially. "
        f"Notably, regencies with very high individual FSI but surrounded by "
        f"lower-FSI neighbours (e.g. Kabupaten Jayapura, Papua) do not appear "
        f"in the hot-spot list. The two rankings answer different policy "
        f"questions: severity ranking identifies individual high-burden units; "
        f"hot-spot analysis identifies regional clusters where coordinated "
        f"provincial-scale response is most warranted.",

        # ── Bullet 3: National trend (Phase 3 — national MK) ──────────────
        f"<strong>Indonesia overall is on a worsening trajectory.</strong> "
        f"National-aggregate Mann-Kendall on the log-weighted FSI composite "
        f"reports a <strong>{k.get('trend_direction', 'changing').lower()}</strong> "
        f"trend at <strong>{fmt_signed_pct(k.get('mk_slope_pct'))}</strong> per "
        f"year (&tau; = {fmt_decimal(k.get('mk_tau'), 2)}, "
        f"{fmt_pvalue(k.get('mk_p_hr'))}, Hamed-Rao autocorrelation-corrected). "
        f"The national signal is robust because aggregation across "
        f"<strong>{fmt_int(k.get('n_regencies'))}</strong> regencies averages "
        f"out random year-to-year noise, leaving the underlying trend "
        f"visible. This is the strongest single statistical finding in the "
        f"analysis.",

        # ── Bullet 4: Per-regency trend findings (Phase 3 — per-regency MK) ──
        f"<strong>Per-regency trend confirmation is statistically conservative "
        f"by design.</strong> After Benjamini-Hochberg FDR correction "
        f"(&alpha; = 0.05), <strong>{fmt_int(k.get('n_mk_sig_freq'))} "
        f"of {fmt_int(k.get('n_regencies'))} regencies</strong> show a "
        f"statistically significant FSI trend &mdash; "
        f"<strong>{fmt_int(k.get('n_mk_sig_inc', 0))} trending upward</strong> "
        f"(emerging flood-risk locations) and "
        f"<strong>{fmt_int(k.get('n_mk_sig_dec', 0))} trending downward</strong> "
        f"(potential mitigation success cases). The seven worsening regencies "
        f"span <em>Sulawesi</em> (Sinjai, Morowali, Bone Bolango, Pinrang), "
        f"<em>Sumatera</em> (Pasaman), <em>Java</em> (Brebes), and "
        f"<em>Nusa Tenggara</em> (Dompu) &mdash; geographically diverse, "
        f"showing the climate-stress signal is national in scope. "
        f"Most regencies remain statistically inconclusive (not confirmed "
        f"stable) due to the inherent limit of a 10-year observation window "
        f"at the individual-regency level. The confirmed rising regencies "
        f"are high-priority targets for preventive intervention <em>before</em> "
        f"impacts intensify further.",
    ]

    variant = "warning" if k.get("trend_direction") == "Increasing" else "info"

    render_insight_box(
        bullets=bullets,
        title="RQ1 evidence base",
        kicker="Narrative interpretation",
        variant=variant,
    )


with tab_province:
    # ── Province dropdown ──────────────────────────────────────────
    provinces = list_available_provinces()

    if not provinces:
        st.warning(
            "No province data available. Ennsure `public/data/flood/provinces/` is populated."
        )
        st.stop()

    codes  = [p["code"] for p in provinces]
    labels = [p["name"] for p in provinces]

    # Default to a previously-clicked province (set by National tab click),
    # otherwise the first one in alphabetical order (Aceh).
    default_idx = 0
    if "selected_province" in st.session_state:
        cur = st.session_state["selected_province"]
        if cur in codes:
            default_idx = codes.index(cur)

    col_label, col_dropdown, _ = st.columns([2, 4, 6])
    with col_label:
        st.markdown(
            f'<div style="font-family:{FONT_BODY};font-size:13px;'
            f'color:{INK};line-height:38px;font-weight:500;">'
            f'Selected province'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_dropdown:
        chosen_label = st.selectbox(
            label="Province",
            options=labels,
            index=default_idx,
            key="_province_dropdown",
            label_visibility="collapsed",
        )
    prov_code = codes[labels.index(chosen_label)]
    st.session_state["selected_province"] = prov_code

    # ── Load province data ─────────────────────────────────────────
    try:
        k_p       = load_province_kpis(prov_code)
        annual_p  = load_province_annual(prov_code)
        reg_df_p  = load_province_regency_table(prov_code)
        insight_p = load_province_insight(prov_code)
    except FileNotFoundError as e:
        st.error(f"**Province data missing for code `{prov_code}`.**\n\n{e}")
        st.stop()
    except Exception as e:
        st.error(f"Could not load province data: {e}")
        st.stop()

    prov_name = k_p.get("prov_name", chosen_label)

    # Province name header
    st.markdown(
        f'<div style="font-family:{FONT_DISPLAY};font-size:20px;'
        f'font-weight:600;color:{INK};margin:18px 0 14px 0;">'
        f'{prov_name}</div>',
        unsafe_allow_html=True,
    )
    # ── Province KPI strip (descriptive) ───────────────────────────
    n_years_p = (k_p.get("year_max", 2025) - k_p.get("year_min", 2016)) + 1
    avg_events_p_yr = (k_p.get("total_events", 0) or 0) / max(n_years_p, 1)
    avg_casualties_p_yr = (
        ((k_p.get("total_deaths", 0)  or 0) +
         (k_p.get("total_missing", 0) or 0) +
         (k_p.get("total_injured", 0) or 0)) / max(n_years_p, 1)
    )
    avg_houses_p_yr = (k_p.get("total_houses", 0) or 0) / max(n_years_p, 1)

    render_kpi_strip([
        {"label": "Avg events / year",
         "value": fmt_int(avg_events_p_yr),
         "sublabel": "Province flood events"},
        {"label": "Avg casualties / year",
         "value": fmt_int(avg_casualties_p_yr),
         "sublabel": "Deaths + missing + injured",
         "tone": "red"},
        {"label": "Avg houses / year",
         "value": fmt_compact(avg_houses_p_yr),
         "sublabel": "Flooded + damaged"},
        {"label": "Hot spots",
         "value": fmt_int(k_p.get("n_hot_spots")),
         "sublabel": f"of {fmt_int(k_p.get('n_regencies'))} regencies"},
        {"label": "MK rising",
         "value": fmt_int(k_p.get("n_mk_sig_freq")),
         "sublabel": "Significantly increasing events",
         "tone": "red" if (k_p.get("n_mk_sig_freq") or 0) > 0 else None},
    ])
    st.divider()

    # ── Choropleth (descriptive) ───────────────────────────────────
    render_section_header(
        kicker="Spatial · descriptive",
        title=f"FSI Score across {prov_name}",
        description=(
            "<strong>FSI Min&ndash;Max 2016&ndash;2025</strong> for each regency "
            "in the current province, zoomed to the provincial bounding box. "
            "Same tier classes as the national view."
        ),
    )

    if geo is None:
        st.warning("GeoJSON missing — cannot render the province map.")
    else:
        try:
            center, zoom = compute_province_view(reg_df_p, geo)
            render_fsi_choropleth(
                reg_df=reg_df_p,
                geojson=geo,
                height=460,
                key=f"prov_choropleth_{prov_code}",
                mapbox_zoom=zoom,
                mapbox_center=center,
            )
        except Exception as e:
            st.error(f"Province choropleth failed: {e}")
            with st.expander("Traceback"):
                import traceback
                st.code(traceback.format_exc(), language="python")
    
    # ── Annual line chart (descriptive) — matches National schema ──
    render_section_header(
        kicker="Temporal · descriptive",
        title=f"Annual trend {k_p.get('year_min', 2016)}\u2013{k_p.get('year_max', 2025)}",
        description=(
            "FSI Score alongside its three dimensions &mdash; frequency, "
            f"HCI, PDI &mdash; for {prov_name}. Each rescaled to 0&ndash;100 "
            "for visual comparison. Raw counts togglable."
        ),
    )
    try:
        render_annual_line_chart(
            annual=annual_p,
            height=440,
            key=f"prov_line_{prov_code}",
        )
    except Exception as e:
        st.warning(f"Could not render province line chart: {e}")

    # ── Scatter (analytical) — 2×2 quadrant policy matrix ──────────
    render_section_header(
        kicker="Spatial · analytical",
        title="Severity × spatial clustering — policy quadrants",
        description=(
            "Each regency plotted by cumulative FSI Score (x) against Gi* "
            "z-score (y). Two reference lines split the chart into four "
            "policy quadrants: "
            "<strong style='color:#dc2626'>URGENT</strong> (FSI&gt;50 &amp; hot, "
            "p&lt;0.10), "
            "<strong style='color:#ea580c'>WATCH</strong> (clustering forming), "
            "<strong style='color:#2563eb'>ISOLATED SEVERE</strong> (severe but "
            "no neighbours), "
            "<strong style='color:#64748b'>LOW PRIORITY</strong> (neither). "
            "Ringed points have a statistically significant rising trend "
            "(Mann-Kendall on event frequency)."
        ),
    )

    # Quadrant thresholds (matches your supervisor-approved spec)
    FSI_SPLIT = 50.0
    GI_SPLIT  = 1.65   # ≈ critical z at p < 0.10 (one-tailed)

    QUADRANT_COLORS = {
        "URGENT":          "#dc2626",   # red    — top-right
        "WATCH":           "#ea580c",   # orange — top-left
        "ISOLATED SEVERE": "#2563eb",   # blue   — bottom-right
        "LOW PRIORITY":    "#64748b",   # grey   — bottom-left
    }

    def _quadrant(fsi, gi_z):
        hot     = gi_z > GI_SPLIT
        severe  = fsi  > FSI_SPLIT
        if hot and severe:        return "URGENT"
        if hot and not severe:    return "WATCH"
        if severe and not hot:    return "ISOLATED SEVERE"
        return "LOW PRIORITY"

    try:
        scatter_df = load_province_scatter(prov_code)

        if scatter_df.empty:
            st.info("No regencies to plot for this province.")
        else:
            import plotly.express as px

            # Classify into quadrants
            scatter_df = scatter_df.copy()
            scatter_df["quadrant"] = [
                _quadrant(f, g) for f, g in
                zip(scatter_df["FSI_index"], scatter_df["gi_z_FSI"])
            ]

            fig = px.scatter(
                scatter_df,
                x="FSI_index",
                y="gi_z_FSI",
                color="quadrant",
                color_discrete_map=QUADRANT_COLORS,
                category_orders={
                    "quadrant": ["URGENT", "WATCH", "ISOLATED SEVERE", "LOW PRIORITY"],
                },
                hover_name="kemendagri_kab_name",
                hover_data={
                    "FSI_index":         ":.2f",
                    "gi_z_FSI":            ":.2f",
                    "quadrant":            True,
                    "mk_sig_FSI":  True,
                },
                height=480,
            )
            fig.update_traces(marker=dict(size=11, line=dict(width=0)))

            # Rings around MK-significant regencies
            ringed = scatter_df[scatter_df["mk_sig_FSI"] == True]
            if len(ringed) > 0:
                fig.add_scatter(
                    x=ringed["FSI_index"],
                    y=ringed["gi_z_FSI"],
                    mode="markers",
                    marker=dict(
                        size=18, color="rgba(0,0,0,0)",
                        line=dict(color="#0f172a", width=2),
                    ),
                    name="MK rising trend",
                    hoverinfo="skip",
                    showlegend=True,
                )

            # ── Quadrant divider lines (the 2×2 grid) ─────────────────
            # Vertical line at FSI = 50
            fig.add_vline(
                x=FSI_SPLIT,
                line_dash="dash",
                line_color="#9ca3af",
                line_width=1.5,
                annotation_text=f"FSI = {FSI_SPLIT:.0f}",
                annotation_position="bottom right",
                annotation_font=dict(size=10, color="#6b7280"),
            )
            # Horizontal line at Gi* z = 1.65
            fig.add_hline(
                y=GI_SPLIT,
                line_dash="dash",
                line_color="#9ca3af",
                line_width=1.5,
                annotation_text=f"Gi* z = {GI_SPLIT:.2f} · p<0.10",
                annotation_position="top right",
                annotation_font=dict(size=10, color="#6b7280"),
            )

            # ── Subtle quadrant background fills (helps readability) ──
            # Get axis ranges to fill correctly
            x_min = min(scatter_df["FSI_index"].min() - 5, 0)
            x_max = max(scatter_df["FSI_index"].max() + 5, 100)
            y_min = scatter_df["gi_z_FSI"].min() - 0.5
            y_max = scatter_df["gi_z_FSI"].max() + 0.5

            # Q1 URGENT (top-right) — red tint
            fig.add_shape(
                type="rect", x0=FSI_SPLIT, x1=x_max, y0=GI_SPLIT, y1=y_max,
                fillcolor="rgba(220, 38, 38, 0.05)", line_width=0, layer="below",
            )
            # Q2 WATCH (top-left) — orange tint
            fig.add_shape(
                type="rect", x0=x_min, x1=FSI_SPLIT, y0=GI_SPLIT, y1=y_max,
                fillcolor="rgba(234, 88, 12, 0.04)", line_width=0, layer="below",
            )
            # Q4 ISOLATED SEVERE (bottom-right) — blue tint
            fig.add_shape(
                type="rect", x0=FSI_SPLIT, x1=x_max, y0=y_min, y1=GI_SPLIT,
                fillcolor="rgba(37, 99, 235, 0.04)", line_width=0, layer="below",
            )
            # Q3 LOW PRIORITY (bottom-left) — no fill (neutral)

            # ── Corner labels for the 4 quadrants ─────────────────────
            # Placed just inside each quadrant
            for label, x_pos, y_pos, color, xanchor in [
                ("URGENT",          x_max - 1,  y_max - 0.2, "#dc2626", "right"),
                ("WATCH",           x_min + 1,  y_max - 0.2, "#ea580c", "left"),
                ("ISOLATED SEVERE", x_max - 1,  y_min + 0.2, "#2563eb", "right"),
                ("LOW PRIORITY",    x_min + 1,  y_min + 0.2, "#64748b", "left"),
            ]:
                fig.add_annotation(
                    x=x_pos, y=y_pos, text=label,
                    showarrow=False,
                    xanchor=xanchor, yanchor="middle",
                    font=dict(family="Inter, sans-serif",
                              size=10, color=color),
                    opacity=0.45,
                )

            fig.update_layout(
                xaxis=dict(
                    title="FSI Score (0–100)",
                    range=[x_min, x_max],
                    gridcolor="#f1f5f9", showline=True, linecolor="#e5e7eb",
                    zeroline=False,
                ),
                yaxis=dict(
                    title="Gi* z-score",
                    range=[y_min, y_max],
                    gridcolor="#f1f5f9", showline=True, linecolor="#e5e7eb",
                    zeroline=False,
                ),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0,
                    title_text="",
                ),
                margin=dict(l=0, r=0, t=20, b=0),
                font=dict(family="Inter, sans-serif", size=11, color="#1f2937"),
                hoverlabel=dict(bgcolor="white", bordercolor="#e5e7eb"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(
                fig,
                key=f"prov_scatter_{prov_code}",
                config={"displayModeBar": False},
            )

            # ── Quadrant summary table below the chart ─────────────────
            from collections import Counter
            counts = Counter(scatter_df["quadrant"])
            order = ["URGENT", "WATCH", "ISOLATED SEVERE", "LOW PRIORITY"]
            chips = "  ".join(
                f"<span style='display:inline-block;padding:3px 10px;"
                f"border-radius:10px;background:{QUADRANT_COLORS[q]}15;"
                f"color:{QUADRANT_COLORS[q]};font-family:Inter,sans-serif;"
                f"font-size:11px;font-weight:600;letter-spacing:0.02em;"
                f"margin-right:6px;'>"
                f"{q}: {counts.get(q, 0)}</span>"
                for q in order
            )
            st.markdown(
                f"<div style='margin-top:10px;'>{chips}</div>",
                unsafe_allow_html=True,
            )

    except FileNotFoundError:
        st.info(
            f"Scatter data not available for {prov_name}. "
            "Re-run nb12 to generate `scatter.parquet` for this province."
        )
    except Exception as e:
        st.warning(f"Could not render scatter: {e}")
        import traceback
        with st.expander("Traceback"):
            st.code(traceback.format_exc(), language="python")
    
# ═════════════════════════════════════════════════════════════════════
# TAB 3 — REGENCY  (single regency, zoomed)
# ═════════════════════════════════════════════════════════════════════
with tab_regency:
    # ── Filter cascade: pick province first, then regency ──────────
    # Two dropdowns make the 514-regency list manageable. The province
    # default follows whatever was last selected on the Province tab.
    provinces_r = list_available_provinces()

    if not provinces_r:
        st.warning(
            "No regency data available. Run nb12 and ensure "
            "`public/data/flood/provinces/` is populated."
        )
        st.stop()

    codes_r  = [p["code"] for p in provinces_r]
    labels_r = [p["name"] for p in provinces_r]

    default_prov_idx = 0
    if "selected_province" in st.session_state:
        cur_p = st.session_state["selected_province"]
        if cur_p in codes_r:
            default_prov_idx = codes_r.index(cur_p)

    col_p_label, col_p_dropdown, col_k_label, col_k_dropdown = st.columns(
        [1.2, 3, 1.2, 3], gap="medium"
    )

    with col_p_label:
        st.markdown(
            f'<div style="font-family:{FONT_BODY};font-size:13px;'
            f'color:{INK};line-height:38px;font-weight:500;">'
            f'Province</div>',
            unsafe_allow_html=True,
        )
    with col_p_dropdown:
        chosen_prov_label = st.selectbox(
            label="Province",
            options=labels_r,
            index=default_prov_idx,
            key="_regency_tab_province",
            label_visibility="collapsed",
        )
    prov_code_r = codes_r[labels_r.index(chosen_prov_label)]

    # ── Load the province's regency table so we can list its regencies ──
    try:
        prov_regs = load_province_regency_table(prov_code_r)
    except Exception as e:
        st.error(f"Could not load regency list for province {prov_code_r}: {e}")
        st.stop()

    if prov_regs.empty:
        st.info("No regencies found in this province.")
        st.stop()

    # Build the regency dropdown — sorted by FSI descending so the most
    # severe regency in the province is the default (most thesis-relevant)
    regs_sorted = prov_regs.sort_values("FSI", ascending=False).reset_index(drop=True)
    kab_codes  = regs_sorted["kemendagri_kab_code"].astype(str).tolist()
    kab_labels = regs_sorted["kemendagri_kab_name"].tolist()

    # If user previously selected a regency, default to it. Otherwise
    # default to the most-severe regency in the province.
    default_kab_idx = 0
    if "selected_regency" in st.session_state:
        cur_k = st.session_state["selected_regency"]
        if cur_k in kab_codes:
            default_kab_idx = kab_codes.index(cur_k)

    with col_k_label:
        st.markdown(
            f'<div style="font-family:{FONT_BODY};font-size:13px;'
            f'color:{INK};line-height:38px;font-weight:500;">'
            f'Regency</div>',
            unsafe_allow_html=True,
        )
    with col_k_dropdown:
        chosen_kab_label = st.selectbox(
            label="Regency",
            options=kab_labels,
            index=default_kab_idx,
            key="_regency_tab_kab",
            label_visibility="collapsed",
        )
    kab_code = kab_codes[kab_labels.index(chosen_kab_label)]
    st.session_state["selected_regency"] = kab_code

    # ── Pull the single-row dataframe for this regency ──────────────
    reg_row_df = regs_sorted[regs_sorted["kemendagri_kab_code"].astype(str) == kab_code].copy()

    if reg_row_df.empty:
        st.warning("Selected regency not found in province data.")
        st.stop()

    reg_row = reg_row_df.iloc[0]
    kab_name = reg_row["kemendagri_kab_name"]

    # ── Header: regency name + key indicators ──────────────────────
    st.markdown(
        f'<div style="font-family:{FONT_DISPLAY};font-size:20px;'
        f'font-weight:600;color:{INK};margin:18px 0 4px 0;">'
        f'{kab_name}</div>'
        f'<div style="font-family:{FONT_MONO};font-size:10.5px;color:{MUTED};'
        f'letter-spacing:0.04em;margin-bottom:14px;">'
        f'{chosen_prov_label} &middot; rank {int(reg_row.get("rank_in_province", 0))} '
        f'of {len(regs_sorted)} in province'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Regency KPI strip (descriptive) ────────────────────────────
    try:
        reg_bundle = load_regency_bundle(kab_code)
        k_r = reg_bundle.get("kpis", {})
    except FileNotFoundError:
        # Fall back to the row from the province table if the per-regency
        # JSON wasn't built (rare — only if nb12 Step 5 didn't run)
        k_r = {
            "total_events":  int(reg_row.get("event_count", 0) or 0),
            "total_deaths":  int(reg_row.get("deaths", 0) or 0),
            "total_missing": int(reg_row.get("missing", 0) or 0),
            "total_injured": int(reg_row.get("injured", 0) or 0),
            "total_houses":  int(reg_row.get("house_flooded", 0) or 0),
        }

    # 10-year period (same convention as National/Province)
    n_years_r = 10
    avg_events_r_yr     = (k_r.get("total_events", 0)  or 0) / n_years_r
    avg_casualties_r_yr = (
        ((k_r.get("total_deaths", 0)  or 0) +
         (k_r.get("total_missing", 0) or 0) +
         (k_r.get("total_injured", 0) or 0)) / n_years_r
    )
    avg_houses_r_yr     = (k_r.get("total_houses", 0)  or 0) / n_years_r

    render_kpi_strip([
        {"label": "Avg events / year",
         "value": fmt_int(avg_events_r_yr),
         "sublabel": "Regency flood events"},
        {"label": "Avg casualties / year",
         "value": fmt_int(avg_casualties_r_yr),
         "sublabel": "Deaths + missing + injured",
         "tone": "red"},
        {"label": "Avg houses / year",
         "value": fmt_compact(avg_houses_r_yr),
         "sublabel": "Flooded + damaged"},
    ])

    st.divider()

    # ── Choropleth (descriptive) ───────────────────────────────────
    render_section_header(
        kicker="Spatial · descriptive",
        title=f"FSI Score — {kab_name}",
        description=(
            f"<strong>FSI Min&ndash;Max 2016&ndash;2025</strong> for {kab_name}, "
            f"shown on the same tier colour scale as the National and "
            f"Province views. Tier: "
            f"<strong>{reg_row.get('FSI_tier', '?')}</strong> "
            f"(FSI Score {fmt_decimal(reg_row.get('FSI_index'), 1)}/100). "
            f"Gi* category: <strong>{reg_row.get('gi_cat_FSI', '?')}</strong>."
        ),
    )

    if geo is None:
        st.warning("GeoJSON missing — cannot render the regency map.")
    else:
        try:
            # Reuse compute_province_view — works on any 1+ feature subset
            center, zoom = compute_province_view(reg_row_df, geo, padding=0.40)
            render_fsi_choropleth(
                reg_df=reg_row_df,
                geojson=geo,
                height=460,
                key=f"reg_choropleth_{kab_code}",
                mapbox_zoom=zoom,
                mapbox_center=center,
            )
        except Exception as e:
            st.error(f"Regency choropleth failed: {e}")
            import traceback
            with st.expander("Traceback"):
                st.code(traceback.format_exc(), language="python") 
    # ── Annual line chart (descriptive) ────────────────────────────
    render_section_header(
        kicker="Temporal · descriptive",
        title=f"Annual trend — {kab_name}",
        description=(
            "FSI Score and its three dimensions &mdash; frequency, HCI, PDI "
            f"&mdash; for {kab_name}, year by year. Each series rescaled to "
            "0&ndash;100 within this regency for visual comparison. "
            "Raw counts togglable via the legend."
        ),
    )

    try:
        # reg_bundle was loaded earlier (in the KPI strip section).
        # Its 'annual' sub-dict now has the same schema as Province / National
        # (after the nb12 Cell 6 refinement).
        annual_r = reg_bundle.get("annual", {})

        if annual_r and annual_r.get("years"):
            render_annual_line_chart(
                annual=annual_r,
                height=420,
                key=f"reg_line_{kab_code}",
            )
        else:
            st.info(
                f"No annual time series available for {kab_name}. "
                "Re-run nb12 to regenerate per-regency annual data."
            )
    except Exception as e:
        st.warning(f"Could not render regency line chart: {e}")
        import traceback
        with st.expander("Traceback"):
            st.code(traceback.format_exc(), language="python")
            
    # ── Monthly heatmap + Avg monthly profile (descriptive) ─────────
    render_section_header(
        kicker="Temporal · descriptive",
        title=f"Seasonal pattern — {kab_name}",
        description=(
            "<strong>Left:</strong> FSI Score for every month from 2016 to "
            "2025 &mdash; reveals year-to-year extremes and any shift in "
            "seasonal timing. "
            "<strong>Right:</strong> 10-year average FSI by month of year "
            "&mdash; the typical seasonal profile. "
            "Darker / taller cells mean higher flood severity."
        ),
    )

    try:
        import plotly.graph_objects as go

        # reg_bundle was loaded earlier (in the KPI strip section)
        heat = reg_bundle.get("monthly_heatmap", {})
        avg_monthly = reg_bundle.get("avg_monthly", [])

        years_m  = heat.get("years", [])
        months_m = heat.get("months", list(range(1, 13)))
        values_m = heat.get("values", [])

        has_heatmap = bool(years_m) and bool(values_m)
        has_bar     = bool(avg_monthly) and any(v > 0 for v in avg_monthly)

        # Two columns — heatmap takes ~2/3 width, bar chart ~1/3
        col_heat, col_bar = st.columns([2, 1], gap="medium")

        MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        # ── HEATMAP ─────────────────────────────────────────────────
        with col_heat:
            if not has_heatmap:
                st.info("No monthly data available for this regency.")
            else:
                # Single-hue blue scale (light = low, dark = high FSI)
                # — matches the National/Province tier palette family
                fig_heat = go.Figure(go.Heatmap(
                    z=values_m,
                    x=[MONTH_LABELS[m - 1] for m in months_m],
                    y=[str(y) for y in years_m],
                    colorscale=[
                        [0.0,  "#f8fafc"],
                        [0.25, "#bfdbfe"],
                        [0.5,  "#60a5fa"],
                        [0.75, "#2563eb"],
                        [1.0,  "#1e3a8a"],
                    ],
                    zmin=0,
                    hovertemplate=(
                        "<b>%{y} %{x}</b><br>"
                        "FSI Score: %{z:.2f} / 100"
                        "<extra></extra>"
                    ),
                    colorbar=dict(
                        title=dict(text="FSI", side="right",
                                   font=dict(size=10)),
                        thickness=10,
                        len=0.85,
                        tickfont=dict(size=9),
                    ),
                    xgap=1,
                    ygap=1,
                ))
                fig_heat.update_layout(
                    height=320,
                    margin=dict(l=0, r=0, t=10, b=0),
                    font=dict(family="Inter, sans-serif", size=10,
                              color="#1f2937"),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(side="bottom", tickfont=dict(size=10)),
                    yaxis=dict(autorange="reversed",
                               tickmode="array",
                               tickvals=[str(y) for y in years_m],
                               tickfont=dict(size=10),),
                    hoverlabel=dict(bgcolor="white", bordercolor="#e5e7eb"),
                )
                st.plotly_chart(
                    fig_heat,
                    key=f"reg_heatmap_{kab_code}",
                    config={"displayModeBar": False},
                )

        # ── BAR CHART (avg monthly) ────────────────────────────────
        with col_bar:
            if not has_bar:
                st.info("No seasonal profile available.")
            else:
                # Identify the peak month for emphasis colour
                max_val = max(avg_monthly)
                bar_colors = [
                    "#1e3a8a" if v == max_val else "#93c5fd"
                    for v in avg_monthly
                ]

                fig_bar = go.Figure(go.Bar(
                    x=MONTH_LABELS,
                    y=avg_monthly,
                    marker=dict(color=bar_colors,
                                line=dict(width=0)),
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Avg FSI: %{y:.2f} / 100"
                        "<extra></extra>"
                    ),
                ))
                fig_bar.update_layout(
                    height=320,
                    margin=dict(l=0, r=0, t=10, b=0),
                    font=dict(family="Inter, sans-serif", size=10,
                              color="#1f2937"),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(tickfont=dict(size=10), showline=True,
                               linecolor="#e5e7eb"),
                    yaxis=dict(title="Avg FSI", title_font=dict(size=10),
                               tickfont=dict(size=10),
                               gridcolor="#f1f5f9",
                               showline=True, linecolor="#e5e7eb",
                               zeroline=False),
                    hoverlabel=dict(bgcolor="white", bordercolor="#e5e7eb"),
                )
                st.plotly_chart(
                    fig_bar,
                    key=f"reg_bar_{kab_code}",
                    config={"displayModeBar": False},
                )

    except Exception as e:
        st.warning(f"Could not render monthly views: {e}")
        import traceback
        with st.expander("Traceback"):
            st.code(traceback.format_exc(), language="python")   