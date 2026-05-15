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
    assert_data_present,
)
from lib.colors import INK, MUTED, FONT_DISPLAY, FONT_MONO
from lib.format import (
    fmt_int, fmt_decimal, fmt_pvalue, fmt_compact, fmt_signed_pct,
)

from components.section_header import render_page_header, render_section_header
from components.kpi_strip       import render_kpi_strip
from components.choropleth      import render_fsi_choropleth
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
st.markdown(
    """
<style>
  section.main div[data-testid="stMarkdownContainer"] > p {
    max-width: 760px;
    line-height: 1.55;
  }
  section.main div[data-testid="stMarkdownContainer"] > ul > li,
  section.main div[data-testid="stMarkdownContainer"] > ol > li {
    max-width: 760px;
  }
</style>
""",
    unsafe_allow_html=True,
)


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
    {"label": "MK sig (events)",
     "value": fmt_int(k.get("n_mk_sig_freq")),
     "sublabel": f"of {fmt_int(k.get('n_regencies'))} regencies"},
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
            f"`FSI_tier`, `FSI_percent`, `event_count`, `deaths`, "
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
        "integrated FSI Score (Mann-Kendall on annual FSI_temporal_pct "
        "with Hamed-Rao autocorrelation correction; Benjamini-Hochberg "
        "FDR &alpha; = 0.05; ranked by Kendall&rsquo;s &tau;)."
    )


# ─────────────────────────────────────────────────────────────────────
# Key Findings — narrative interpretation
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
    f"<strong>Flood burden is spatially clustered, not randomly distributed.</strong> "
    f"Global Moran's I = <strong>{fmt_decimal(k.get('morans_i'))}</strong> "
    f"({fmt_pvalue(k.get('morans_p'))}) confirms that high-FSI regencies "
    f"are concentrated near other high-FSI regencies. The clustering is "
    f"strong enough to reject the null of spatial randomness with very "
    f"high confidence, indicating Indonesia's flood vulnerability has "
    f"identifiable regional structure rather than scattered local incidents.",

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

    f"<strong>Indonesia overall is on a worsening trajectory.</strong> "
    f"National-aggregate Mann-Kendall reports a "
    f"<strong>{k.get('trend_direction', 'changing').lower()}</strong> trend "
    f"at <strong>{fmt_signed_pct(k.get('mk_slope_pct'))}</strong> per year "
    f"(&tau; = {fmt_decimal(k.get('mk_tau'), 2)}, "
    f"{fmt_pvalue(k.get('mk_p_hr'))}, Hamed-Rao corrected). The national "
    f"signal is robust because aggregation across "
    f"<strong>{fmt_int(k.get('n_regencies'))}</strong> regencies averages "
    f"out random year-to-year noise, leaving the underlying trend "
    f"visible. This is the strongest single statistical finding in the "
    f"analysis.",

    f"<strong>Per-regency trend confirmation is statistically conservative "
    f"by design.</strong> Only <strong>{fmt_int(k.get('n_mk_sig_freq'))} "
    f"of {fmt_int(k.get('n_regencies'))} regencies</strong> show a "
    f"statistically significant rising FSI trend after Benjamini-Hochberg "
    f"FDR correction. This reflects the inherent limit of a 10-year "
    f"observation window applied to individual regencies &mdash; not an "
    f"absence of underlying change. Most regencies are statistically "
    f"inconclusive, not confirmed stable. The confirmed regencies "
    f"(in Sulawesi, Kalimantan, and Sumatera Barat) are emerging "
    f"flood-burden zones where the upward trend is strong enough to "
    f"overcome local noise &mdash; making them high-priority targets for "
    f"preventive intervention before they accumulate Java-scale damage.",
]

variant = "warning" if k.get("trend_direction") == "Increasing" else "info"

render_insight_box(
    bullets=bullets,
    title="RQ1 evidence base",
    kicker="Narrative interpretation",
    variant=variant,
)


# ─────────────────────────────────────────────────────────────────────
# Footnote
# ─────────────────────────────────────────────────────────────────────
footer_style = (
    f"margin-top:10px;font-family:{FONT_MONO};font-size:9.5px;"
    f"color:{MUTED};letter-spacing:0.04em;line-height:1.5;"
)
st.markdown(
    f'<div style="{footer_style}">'
    f'FSI weights &middot; w_freq = 0.302 &middot; w_HCI = 0.360 &middot; '
    f'w_PDI = 0.338 (k-means &eta;&sup2;)<br>'
    f'Spatial weights &middot; KNN k = {k.get("knn_k", 5)}<br>'
    f'Period &middot; {k.get("year_min")}&ndash;{k.get("year_max")}'
    f'</div>',
    unsafe_allow_html=True,
)
