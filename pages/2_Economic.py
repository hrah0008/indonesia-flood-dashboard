"""
pages/2_Economic.py
===================
Economic menu — National / Province / Regency views.
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
    list_economic_regencies,
    get_regency_code,
    load_regency_economic_kpis,
    load_regency_economic_series,
)
from lib.data_flood import load_regencies_geojson
from components.choropleth import (
    render_economic_choropleth,
    render_economic_legend,
    compute_province_view,
)
from components.kpi_strip import render_kpi_strip
from components.line_chart import render_economic_line_chart
from components.bar_chart import render_sector_impact_bar, render_composition_stacked
from components.scatter_plot import render_province_scatter
from components.ranking_table import (
    render_economic_fsi_table, render_province_sector_table,
)
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
    title="Regional economic growth and flood severity",
    description=(
        "How regional GRDP growth (2016-2025) relates spatially to flood "
        "severity (FSI). Growth is shown by colour saturation; FSI by bubble size."
    ),
)

# ─── Load shared data ─────────────────────────────────────────────────
try:
    reg_df  = load_economic_choropleth_table()
    geojson = load_regencies_geojson()
except FileNotFoundError as e:
    st.error(f"Could not load economic data: {e}")
    st.stop()

tab_national, tab_province, tab_regency = st.tabs(["National", "Province", "Regency"])

# ═════════════════════════════════════════════════════════════════════
# TAB 1 — NATIONAL
# ═════════════════════════════════════════════════════════════════════
with tab_national:

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

    render_section_header(
        kicker="Spatial · descriptive",
        title=f"GRDP growth and FSI — {fmt_int(reg_df['kemendagri_kab_code'].nunique())} regencies",
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
        st.markdown(
                "<div style='font-size:11px;color:#6b7280;"
                "text-transform:uppercase;letter-spacing:0.05em;"
                "margin-bottom:6px;margin-top:8px;'>Map layers</div>",
                unsafe_allow_html=True,
            )
        show_growth = st.checkbox(
            "Growth saturation", value=True, key="toggle_growth_econ",
            help="Polygon fill by average GRDP growth 2016-2025",
        )
        show_fsi = st.checkbox(
            "FSI bubble overlay", value=True, key="toggle_fsi_econ",
            help="Bubble size proportional to FSI severity (sqrt scale, 0-100)",
        )
       
        # Section: Legend (vertical layout, stacked below toggles)
        st.markdown(
                "<div style='font-size:11px;color:#6b7280;"
                "text-transform:uppercase;letter-spacing:0.05em;"
                "margin-top:14px;margin-bottom:6px;'>Legend</div>",
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

    st.divider()

    render_section_header(
        kicker="Temporal · descriptive",
        title="Economic growth and flood severity over time",
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
            kicker="Flood severity · descriptive",
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

        f"<strong>At the sector level the effects are more heterogeneous.</strong> "
        f"Significance was assessed after Benjamini&ndash;Hochberg (BH-FDR) "
        f"correction across 17 sectors, then graded by standard-error consistency: "
        f"effects significant under <em>both</em> clustered and Driscoll&ndash;Kraay "
        f"SE are <strong>robust</strong>; those under only one are "
        f"<strong>suggestive</strong>. The flood block is jointly significant in 11 "
        f"of 17 sectors. Three tentative transmission channels emerge. First, higher "
        f"flood <em>frequency</em> is associated with stronger growth in recovery-linked "
        f"sectors &mdash; robustly for <em>trade</em> and <em>health</em>, and more "
        f"weakly (suggestive) for <em>construction</em> and business services. Second, "
        f"higher flood-related <em>human cost</em> is associated with weaker growth in "
        f"service sectors, with <em>education</em> the only robust case (accommodation "
        f"and a few others are suggestive). Third, <em>physical damage</em> shows only "
        f"<em>suggestive</em> negative effects in mining and manufacturing (significant "
        f"under Driscoll&ndash;Kraay only, not robust). For two sectors (electricity, "
        f"real estate) the flood block is jointly significant but no single dimension "
        f"is, so the effect cannot be attributed to a specific channel.",

        f"<strong>Reading a sector coefficient.</strong> The education-services "
        f"sector shows a robust coefficient of &beta; = &minus;0.13 for flood human "
        f"cost &mdash; the clearest sector result, significant under both SEs after "
        f"BH-FDR. Because the flood variable is logged and growth is in percentage "
        f"points, this is a semi-elasticity: in years when a regency experiences "
        f"higher flood-related human costs, education-services GRDP grows about 0.13 "
        f"percentage points slower &mdash; consistent with reduced activity in "
        f"education services around flood events (e.g. delayed government education "
        f"spending and lower private-provider output, the two components of this GRDP "
        f"sector). Several caveats apply. (a) Estimates are <em>associations</em> from "
        f"a fixed-effects panel, not causal effects. (b) Coefficients describe annual "
        f"changes in growth <em>rates</em>, not monetary losses. (c) This is the GRDP "
        f"of education <em>services</em>, not educational quality or access. "
        f"(d) Most results are dimension-dependent and many are only suggestive: of 51 "
        f"sector&ndash;dimension combinations only 11 are significant (3 robust under "
        f"both SEs, the rest under one), and 40 (78%) show no significant relationship "
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
# TAB 2 — PROVINCE (descriptive)
# ═════════════════════════════════════════════════════════════════════
with tab_province:
    provinces = list_economic_provinces()
    if not provinces:
        st.warning("No province data available.")
        st.stop()

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
            label="Province", options=provinces, index=default_idx,
            key="_province_dropdown_econ", label_visibility="collapsed",
        )
    st.session_state["selected_province_econ"] = prov_name

    st.markdown(
        f'<div style="font-family:{FONT_DISPLAY};font-size:20px;'
        f'font-weight:600;color:{INK};margin:18px 0 14px 0;">{prov_name}</div>',
        unsafe_allow_html=True,
    )

    # KPI strip
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

    # Choropleth (zoomed to province)
    st.divider()
    render_section_header(
        kicker="Spatial · descriptive",
        title=f"GRDP growth and FSI — {prov_name}",
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
            st.markdown(
                "<div style='font-size:11px;color:#6b7280;"
                "text-transform:uppercase;letter-spacing:0.05em;"
                "margin-bottom:6px;margin-top:8px;'>Map layers</div>",
                unsafe_allow_html=True,
            )
            p_show_growth = st.checkbox("Growth saturation", value=True, key="toggle_growth_prov")
            p_show_fsi = st.checkbox("FSI bubble overlay", value=True, key="toggle_fsi_prov")
             # Section: Legend (vertical layout, stacked below toggles)
            st.markdown(
                "<div style='font-size:11px;color:#6b7280;"
                "text-transform:uppercase;letter-spacing:0.05em;"
                "margin-top:14px;margin-bottom:6px;'>Legend</div>",
                unsafe_allow_html=True,
            )
            render_economic_legend(
                show_growth=p_show_growth, show_fsi_dots=p_show_fsi,
                growth_min=float(prov_df["growth_avg"].min()),
                growth_max=float(prov_df["growth_avg"].max()),
                layout="vertical",
            )
        with pc1:
            try:
                _view = compute_province_view(prov_df, geojson)
                center, zoom = _view[0], _view[1]
                render_economic_choropleth(
                    reg_df=prov_df, geojson=geojson,
                    key=f"economic_choropleth_prov_{prov_name}",
                    mapbox_zoom=zoom, mapbox_center=center,
                    show_growth=p_show_growth, show_fsi_dots=p_show_fsi,
                )
            except Exception as e:
                st.error(f"Could not render province choropleth.\n\n`{e}`")

    # Line chart
    st.divider()
    render_section_header(
        kicker="Temporal · descriptive",
        title=f"Growth and flood severity over time — {prov_name}",
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

    # Quadrant scatter
    st.divider()
    render_section_header(
        kicker="Spatial · descriptive",
        title=f"FSI vs growth across regencies — {prov_name}",
        description=(
            "Each dot is a regency, split into four quadrants at the province's "
            "median FSI and median growth. Lower-right (high flood, low growth) "
            "flags regencies to watch; upper-left (low flood, high growth) are "
            "thriving. Descriptive, not causal."
        ),
    )
    try:
        scatter_df = load_province_scatter(prov_name)
        render_province_scatter(scatter_df, prov_name=prov_name,
                                key=f"province_scatter_{prov_name}")
    except Exception as e:
        st.warning(f"Scatter not available: {e}")

    # Per-regency sector table
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


# ═════════════════════════════════════════════════════════════════════
# TAB 3 — REGENCY (descriptive; single-regency drill-down)
# ═════════════════════════════════════════════════════════════════════
with tab_regency:
    provinces_r = list_economic_provinces()
    if not provinces_r:
        st.warning("No province data available.")
        st.stop()

    rc1, rc2 = st.columns(2)
    with rc1:
        prov_r = st.selectbox("Province", options=provinces_r, key="_province_dropdown_reg")
    regencies_r = list_economic_regencies(prov_r)
    with rc2:
        regency_r = st.selectbox("Regency", options=regencies_r, key="_regency_dropdown_reg")

    st.markdown(
        f'<div style="font-family:{FONT_DISPLAY};font-size:20px;'
        f'font-weight:600;color:{INK};margin:18px 0 14px 0;">{regency_r}'
        f'<span style="font-size:13px;color:{MUTED};font-weight:400;"> · {prov_r}</span></div>',
        unsafe_allow_html=True,
    )

    # KPI strip (avg growth, fastest, slowest, FSI + cluster)
    try:
        reg_kpis = load_regency_economic_kpis(prov_r, regency_r)
        render_kpi_strip(reg_kpis)
        st.markdown(
            f'<div style="font-family:{FONT_MONO};font-size:10px;color:{MUTED};'
            f'letter-spacing:0.04em;margin-top:8px;text-align:center;">'
            f'{regency_r} &middot; GRDP growth 2016&ndash;2025 &middot; '
            f'descriptive profile (no flood regression at regency level)'
            f'</div>',
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.warning(f"Regency KPIs not available: {e}")

    # Choropleth — single regency, same style as Province
    st.divider()
    render_section_header(
        kicker="Spatial · descriptive",
        title=f"GRDP growth and FSI — {regency_r}",
        description=(
            "<strong>This regency only.</strong> Polygon fill shows its average "
            "GRDP growth 2016-2025; the blue bubble shows its Flood Severity "
            "Index (FSI)."
        ),
    )
    try:
        prov_tbl = load_province_choropleth_table(prov_r)
        reg_only = prov_tbl[prov_tbl["kemendagri_kab_name"] == regency_r].copy()
        if len(reg_only):
            rc_map, rc_leg = st.columns([3, 1])
            with rc_leg:
                st.markdown(
                "<div style='font-size:11px;color:#6b7280;"
                "text-transform:uppercase;letter-spacing:0.05em;"
                "margin-bottom:6px;margin-top:8px;'>Map layers</div>",
                unsafe_allow_html=True,
                )
                r_show_growth = st.checkbox("Growth saturation", value=True, key="toggle_growth_reg")
                r_show_fsi = st.checkbox("FSI bubble overlay", value=True, key="toggle_fsi_reg")
                # Section: Legend (vertical layout, stacked below toggles)
                st.markdown(
                        "<div style='font-size:11px;color:#6b7280;"
                        "text-transform:uppercase;letter-spacing:0.05em;"
                        "margin-top:14px;margin-bottom:6px;'>Legend</div>",
                        unsafe_allow_html=True,
                )
                render_economic_legend(
                    show_growth=r_show_growth, show_fsi_dots=r_show_fsi,
                    growth_min=float(reg_only["growth_avg"].min()),
                    growth_max=float(reg_only["growth_avg"].max()),
                    layout="vertical",
                )
            with rc_map:
                _view = compute_province_view(reg_only, geojson)
                center, zoom = _view[0], _view[1]
                render_economic_choropleth(
                    reg_df=reg_only, geojson=geojson,
                    key=f"economic_choropleth_reg_{regency_r}",
                    mapbox_zoom=zoom + 1.5, mapbox_center=center,
                    show_growth=r_show_growth, show_fsi_dots=r_show_fsi,
                )
        else:
            st.info("No map data for this regency.")
    except Exception as e:
        st.error(f"Could not render regency map.\n\n`{e}`")

    # Line chart
    st.divider()
    render_section_header(
        kicker="Temporal · descriptive",
        title=f"Growth and flood severity over time — {regency_r}",
        description=(
            "<strong>GRDP growth (%)</strong> (left axis) and "
            "<strong>FSI (0-100)</strong> (right axis), 2016-2025. "
            "Add sector growth lines with the selector below."
        ),
    )
    reg_series = None
    try:
        reg_code = get_regency_code(prov_r, regency_r)
        reg_series = load_regency_economic_series(reg_code)
        render_economic_line_chart(reg_series, key=f"economic_line_reg_{reg_code}")
        st.caption(
            "GRDP at constant 2010 prices (ADHK). Year-on-year growth; "
            "sector lines start 2017."
        )
    except (FileNotFoundError, KeyError) as e:
        st.warning(f"Regency series not available yet: {e}")

    # ── Economic structure — sector composition over time (stacked) ───
    st.divider()

    _comp = (reg_series or {}).get("composition")

    render_section_header(
        kicker="Structural · descriptive",
        title=f"Economic structure over time — {regency_r}",
        description=(
            "<strong>Sector composition by year</strong>, all 17 sectors stacked "
            "(GRDP at constant 2010 prices). Toggle between absolute Rupiah "
            "(bar height = total GRDP, so you see the economy grow) and 100% share "
            "(each bar = 100%, so you see the structure shift). This complements "
            "the growth trend above &mdash; structure versus rate of change."
        ),
    )

    if _comp:
        mode_label = st.radio(
            "Composition mode",
            options=["Rupiah (absolute)", "Share (100%)"],
            horizontal=True,
            key="stacked_mode_reg",
            label_visibility="collapsed",
        )
        mode = "rupiah" if mode_label.startswith("Rupiah") else "share"
        render_composition_stacked(_comp, mode=mode,
                                   key=f"composition_stacked_{regency_r}_{mode}")
        st.caption(
            "GRDP value added by sector (constant 2010 prices, ADHK). "
            "Composition (structure) is distinct from growth (rate of change)."
        )
    else:
        st.info("Composition data not available for this regency.")