"""
pages/2_Economic.py
===================
Economic menu — National view.
"""

import streamlit as st

from lib.colors import INK, MUTED, HAIRLINE, FONT_DISPLAY, FONT_BODY, FONT_MONO
from lib.format import fmt_int, fmt_pct

from components.section_header import render_page_header, render_section_header
from components.sidebar_nav    import render_sidebar_nav

from lib.data_economic import (
    load_economic_choropleth_table,
    load_national_economic_kpis,
    load_national_economic_series,
    load_national_sector_impact,
    load_national_fsi_table,
    list_economic_provinces,
    load_province_economic_kpis,
    load_province_choropleth_table, 
    load_province_economic_series,
    load_province_scatter,
    load_province_sector_table, 
)
from lib.data_flood import load_regencies_geojson

from components.choropleth import (
    render_economic_choropleth, 
    render_economic_legend,
    compute_province_view, 
)
from components.kpi_strip import render_kpi_strip
from components.line_chart import (
    render_economic_line_chart, 
    render_sector_impact_bar, 
    render_province_scatter,
)
from components.ranking_table import render_economic_fsi_table, render_province_sector_table
from components.insight_box import render_insight_box


st.set_page_config(
    page_title="FloodX — Economic",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    render_sidebar_nav()

render_page_header(
    menu_label="Economic Impact",
    title="Regional economic growth & flood severity",
    description=(
        "How regional GRDP growth (2016-2025) relates spatially to flood "
        "severity (FSI). Growth is shown by colour saturation; FSI by bubble size."
    ),
)

# ─── Load data ────────────────────────────────────────────────────────
try:
    reg_df  = load_economic_choropleth_table()
    geojson = load_regencies_geojson()
except FileNotFoundError as e:
    st.error(f"Could not load economic data: {e}")
    st.stop()

tab_national, tab_province = st.tabs(["National", "Province"])

with tab_national:

    # ── KPI strip ────────────────────────────────────────────────────
    try:
        kpis = load_national_economic_kpis()
        render_kpi_strip(kpis)
        st.markdown(
            f'<div style="font-family:{FONT_MONO};font-size:10px;color:{MUTED};'
            f'letter-spacing:0.04em;margin-top:8px;text-align:center;">'
            f'Across {fmt_int(reg_df["kemendagri_kab_code"].nunique())} regencies &middot; '
            f'GRDP growth 2016&ndash;2025 &middot; flood effect from RQ2 fixed-effects model'
            f'</div>',
            unsafe_allow_html=True,
        )
    except FileNotFoundError as e:
        st.warning(f"KPIs not available yet: {e}")

    st.divider()

    # ── Choropleth ───────────────────────────────────────────────────
    render_section_header(
        kicker="Spatial · analytical",
        title=f"GRDP growth & FSI — {fmt_int(reg_df['kemendagri_kab_code'].nunique())} regencies",
        description=(
            "<strong>Two-layer spatial map.</strong> "
            "Polygon fill shows <strong>average GRDP growth 2016-2025</strong> "
            "as a continuous colour saturation (deeper = higher growth; no zone split). "
            "Blue bubbles show <strong>Flood Severity Index (FSI)</strong>, size "
            "proportional to severity (sqrt scaling, 0-100). "
            "Reading the two together shows whether high-flood regencies coincide "
            "with lower or higher growth."
        ),
    )

    c1, c2 = st.columns([3, 1])
    with c2:
        show_growth = st.checkbox(
            "Growth saturation", value=True, key="toggle_growth_econ",
            help="Polygon fill by average GRDP growth 2016-2025",
        )
        show_fsi = st.checkbox(
            "FSI bubble overlay", value=True, key="toggle_fsi_econ",
            help="Bubble size proportional to FSI severity (sqrt scale, 0-100)",
        )
        st.markdown(
            f"<div style='font-family:{FONT_MONO};font-size:11px;color:{MUTED};"
            f"text-transform:uppercase;letter-spacing:0.05em;"
            f"margin-top:14px;margin-bottom:6px;'>Legend</div>",
            unsafe_allow_html=True,
        )
        render_economic_legend(
            show_growth=show_growth,
            show_fsi_dots=show_fsi,
            growth_min=float(reg_df["growth_avg"].min()),
            growth_max=float(reg_df["growth_avg"].max()),
            layout="vertical",
        )

    with c1:
        try:
            render_economic_choropleth(
                reg_df=reg_df,
                geojson=geojson,
                key="economic_choropleth",
                show_growth=show_growth,
                show_fsi_dots=show_fsi,
            )
        except Exception as e:
            st.error(
                f"**Could not render the choropleth.**\n\n"
                f"Check that `regency_table.parquet` has `growth_avg` and that "
                f"the GeoJSON `kemendagri_kab_code` matches.\n\n`{e}`"
            )

    st.caption(
        "Growth = mean annual GRDP growth 2016-2025 per regency. "
        "FSI joined from the Flood dataset (single-sourced)."
    )

    # ── Line chart ───────────────────────────────────────────────────
    st.divider()

    render_section_header(
        kicker="Temporal · descriptive",
        title="Economic growth & flood severity over time",
        description=(
            "<strong>Average GRDP growth (%)</strong> on the left axis and "
            "<strong>FSI (0-100)</strong> on the right axis, 2016-2025. "
            "Add individual sector growth lines with the selector below."
        ),
    )

    try:
        econ_series = load_national_economic_series()
        render_economic_line_chart(econ_series, key="economic_national_line")
        st.caption(
            "GRDP at constant 2010 prices (ADHK). Year-on-year growth; "
            "average economic growth is available from 2016, individual sector "
            "lines start 2017 (year-on-year change needs a prior year)."
        )
    except FileNotFoundError as e:
        st.warning(f"Annual series not available yet: {e}")

    # ── Bar chart + table (two columns) ──────────────────────────────
    st.divider()

    col_bar, col_tbl = st.columns([1, 1], gap="large")

    with col_bar:
        render_section_header(
            kicker="Sectoral · analytical",
            title="Sector flood effects",
            description=(
                "Significant sector-level flood effects (β) from the RQ2 panel "
                "regression · colour = evidence strength"
            ),
        )
        try:
            impact = load_national_sector_impact()
            render_sector_impact_bar(impact, key="economic_sector_bar")
        except FileNotFoundError as e:
            st.warning(f"Sector impact not available yet: {e}")

    with col_tbl:
        render_section_header(
            kicker="Flood severity · analytical",
            title="Most flood-affected regencies",
            description=(
                "Top 10 by FSI with their economic profile · showing 10 of 514"
            ),
        )
        try:
            fsi_table = load_national_fsi_table()
            render_economic_fsi_table(fsi_table)
        except FileNotFoundError as e:
            st.warning(f"FSI table not available yet: {e}")

    # ── Key findings (mirrors Flood "Diagnostic synthesis") ──────────
    render_section_header(
        kicker="Diagnostic synthesis",
        title="Key Findings",
        description=(
            "Narrative interpretation of the national economic evidence "
            "presented above."
        ),
    )

    _driver = next((it for it in kpis if it.get("label") == "Significant Flood Driver"), None)
    _driver_txt = (
        f"<strong>{_driver['value']}</strong> ({_driver['sublabel']})"
        if _driver else "physical damage (PDI), a small effect"
    )

    bullets = [
        # 1 — aggregate / national (annual)
        f"<strong>National impact is limited and annual, not cumulative.</strong> "
        f"The estimated effects represent <em>annual</em> impacts: each coefficient "
        f"captures how flooding in a particular year is associated with economic "
        f"growth in that <em>same</em> year, rather than cumulative losses over "
        f"multiple years. At the aggregate level, the impact of flooding on overall "
        f"GRDP growth is small. Among the three flood dimensions, only physical "
        f"damage has a statistically significant effect ({_driver_txt}); flood "
        f"frequency and human cost are not significant. The coefficient is a "
        f"semi-elasticity: a one-unit increase in logged physical damage is "
        f"associated with roughly a 0.022 percentage-point reduction in annual GRDP "
        f"growth. Flooding therefore does not broadly depress regional economic "
        f"performance, and its aggregate effects are relatively small.",

        # 2 — sectoral, evidence standard + three channels
        f"<strong>At the sector level the effects are more heterogeneous.</strong> "
        f"Statistical significance was evaluated after controlling for multiple "
        f"testing across 17 sectors using the Benjamini&ndash;Hochberg False "
        f"Discovery Rate (BH-FDR) procedure. Evidence was then graded by the "
        f"consistency of alternative standard errors: effects significant under "
        f"<em>both</em> clustered and Driscoll&ndash;Kraay SE are <strong>robust</strong>; "
        f"those confirmed by only one method are <strong>suggestive</strong>. Three "
        f"transmission channels emerge. First, higher flood <em>frequency</em> is "
        f"associated with stronger growth in recovery- and reconstruction-linked "
        f"sectors, particularly trade, health, and construction. Second, increases "
        f"in flood-related <em>human cost</em> are associated with weaker growth in "
        f"service-oriented sectors, with education showing the strongest and most "
        f"robust evidence. Third, <em>physical damage</em> produces modest negative "
        f"effects in capital-intensive sectors such as mining and manufacturing.",

        # 3 — reading a beta in depth + caveats
        f"<strong>Reading a sector coefficient.</strong> The education-services "
        f"sector shows a robust coefficient of &beta; = &minus;0.13 for flood human "
        f"cost. Because the flood variable is logged and growth is in percentage "
        f"points, this is a semi-elasticity: in years when a regency experiences "
        f"higher flood-related human costs, the education-services sector grows about "
        f"0.13 percentage points slower &mdash; consistent with reduced economic "
        f"activity in education services around flood events (for instance delayed "
        f"government education spending and lower private-provider output, the two "
        f"components of this GRDP sector). Several caveats apply. "
        f"(a) The estimates are <em>associations</em> from a fixed-effects panel and "
        f"do not establish causation. (b) The coefficients describe annual changes in "
        f"growth <em>rates</em>, not monetary losses or cumulative damages. (c) The "
        f"education variable is the GRDP of the education-<em>services</em> sector, not "
        f"educational quality or access. Overall, flooding's impact is limited and "
        f"dimension-dependent: of 51 sector&ndash;dimension combinations, only 11 are "
        f"significant while the remaining 40 (78%) show no significant relationship "
        f"&mdash; so the results do not support estimating monetary losses at the "
        f"regency level.",
    ]

    render_insight_box(
        bullets=bullets,
        title="RQ2 evidence base",
        kicker="Narrative interpretation",
        variant="info",
    )


# ═════════════════════════════════════════════════════════════════════
# TAB 2 — PROVINCE (descriptive; no regression output)
# ═════════════════════════════════════════════════════════════════════
with tab_province:
    provinces = list_economic_provinces()

    if not provinces:
        st.warning("No province data available.")
        st.stop()

    # default to a previously-clicked province if set, else first
    default_idx = 0
    if "selected_province_econ" in st.session_state:
        cur = st.session_state["selected_province_econ"]
        if cur in provinces:
            default_idx = provinces.index(cur)

    col_label, col_dropdown, _ = st.columns([2, 4, 6])
    with col_label:
        st.markdown(
            f'<div style="font-family:{FONT_BODY};font-size:13px;'
            f'color:{INK};line-height:38px;font-weight:500;">Selected province</div>',
            unsafe_allow_html=True,
        )
    with col_dropdown:
        prov_name = st.selectbox(
            label="Province",
            options=provinces,
            index=default_idx,
            key="_province_dropdown_econ",
            label_visibility="collapsed",
        )
    st.session_state["selected_province_econ"] = prov_name

    st.markdown(
        f'<div style="font-family:{FONT_DISPLAY};font-size:20px;'
        f'font-weight:600;color:{INK};margin:18px 0 14px 0;">{prov_name}</div>',
        unsafe_allow_html=True,
    )

    # ── Province KPI strip (descriptive — no regression) ─────────────
    try:
        prov_kpis = load_province_economic_kpis(prov_name)
        render_kpi_strip(prov_kpis)
        st.markdown(
            f'<div style="font-family:{FONT_MONO};font-size:10px;color:{MUTED};'
            f'letter-spacing:0.04em;margin-top:8px;text-align:center;">'
            f'{prov_name} &middot; GRDP growth 2016&ndash;2025 &middot; '
            f'descriptive economic profile (no flood regression at province level)'
            f'</div>',
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.warning(f"Province KPIs not available: {e}")

    # ── Province choropleth (zoomed to the province, like Flood) ──────
    st.divider()

    render_section_header(
        kicker="Spatial · descriptive",
        title=f"GRDP growth & FSI — {prov_name}",
        description=(
            "<strong>Two-layer spatial map, zoomed to this province.</strong> "
            "Polygon fill shows <strong>average GRDP growth 2016-2025</strong> "
            "per regency; blue bubbles show <strong>Flood Severity Index (FSI)</strong>, "
            "sized by severity."
        ),
    )

    try:
        prov_df = load_province_choropleth_table(prov_name)
    except Exception as e:
        prov_df = None
        st.warning(f"Province map data not available: {e}")

    if prov_df is not None and len(prov_df):
        pc1, pc2 = st.columns([3, 1])
        with pc2:
            p_show_growth = st.checkbox(
                "Growth saturation", value=True, key="toggle_growth_prov",
            )
            p_show_fsi = st.checkbox(
                "FSI bubble overlay", value=True, key="toggle_fsi_prov",
            )
            st.markdown(
                f"<div style='font-family:{FONT_MONO};font-size:11px;color:{MUTED};"
                f"text-transform:uppercase;letter-spacing:0.05em;"
                f"margin-top:14px;margin-bottom:6px;'>Legend</div>",
                unsafe_allow_html=True,
            )
            render_economic_legend(
                show_growth=p_show_growth,
                show_fsi_dots=p_show_fsi,
                growth_min=float(prov_df["growth_avg"].min()),
                growth_max=float(prov_df["growth_avg"].max()),
                layout="vertical",
            )

        with pc1:
            try:
                _view = compute_province_view(prov_df, geojson)
                center, zoom = _view[0], _view[1]
                render_economic_choropleth(
                    reg_df=prov_df,
                    geojson=geojson,
                    key=f"economic_choropleth_prov_{prov_name}",
                    mapbox_zoom=zoom,
                    mapbox_center=center,
                    show_growth=p_show_growth,
                    show_fsi_dots=p_show_fsi,
                )
            except Exception as e:
                st.error(f"Could not render province choropleth.\n\n`{e}`")


    # ── Province line chart (growth + FSI over time) ──────────────────
    st.divider()

    render_section_header(
        kicker="Temporal · descriptive",
        title=f"Growth & flood severity over time — {prov_name}",
        description=(
            "<strong>Average GRDP growth (%)</strong> (left axis) and "
            "<strong>FSI (0-100)</strong> (right axis) for this province, "
            "2016-2025. Add sector growth lines with the selector below."
        ),
    )

    try:
        prov_series = load_province_economic_series(prov_name)
        render_economic_line_chart(prov_series, key=f"economic_line_prov_{prov_name}")
        st.caption(
            "GRDP at constant 2010 prices (ADHK). Year-on-year growth, "
            "averaged across the province's regencies; sector lines start 2017."
        )
    except FileNotFoundError as e:
        st.warning(f"Province series not available yet: {e}")

    # ── Province quadrant scatter: FSI vs growth per regency ──────────
    st.divider()

    render_section_header(
        kicker="Spatial · descriptive",
        title=f"FSI vs growth across regencies — {prov_name}",
        description=(
            "Each dot is a regency, split into four quadrants at the province's "
            "median FSI and median growth. The lower-right (high flood, low "
            "growth) flags regencies to watch; upper-left (low flood, high "
            "growth) are thriving. Descriptive, not causal."
        ),
    )

    try:
        scatter_df = load_province_scatter(prov_name)
        render_province_scatter(scatter_df, prov_name=prov_name,
                                key=f"province_scatter_{prov_name}")
    except Exception as e:
        st.warning(f"Scatter not available: {e}")

    # ── Province per-regency sector table (17 sector growth) ──────────
    st.divider()

    render_section_header(
        kicker="Sectoral · descriptive",
        title=f"Sector growth by regency — {prov_name}",
        description=(
            "Mean annual growth (%) per regency, overall and by sector "
            "(constant 2010 prices). Sorted by overall growth."
        ),
    )

    try:
        sector_tbl = load_province_sector_table(prov_name)
        render_province_sector_table(sector_tbl)
    except Exception as e:
        st.warning(f"Sector table not available: {e}")