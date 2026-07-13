"""
pages/3_Social.py
=================
Social menu — National view (poverty & unemployment vs flood severity).

Layout mirrors the Flood page: a wide map column + a narrow control column
holding the "Map layers" toggles and the "Legend". Regression evidence is
summarised narratively in Key Findings; the maps are DESCRIPTIVE averages
of the raw point-percentages (NOT the log-scale regression variables).
"""

import traceback

import streamlit as st
import pandas as pd

from lib.colors import INK, MUTED, FONT_DISPLAY, FONT_BODY, FONT_MONO
from lib.format import fmt_int

from components.section_header import render_page_header, render_section_header
from components.sidebar_nav    import render_sidebar_nav

from lib.data_social import (
    load_social_choropleth_table,
    load_national_social_kpis,
    load_national_social_series,
    load_social_fsi_table,
    load_social_correlation,
    list_social_provinces,
    load_province_social_choropleth,
    load_province_social_kpis,
    load_province_social_series,
    list_province_social_regencies,
    load_regency_social_kpis,
    load_regency_social_series,
    load_regency_social_benchmark,
)
from lib.data_flood import load_regencies_geojson
from components.choropleth import render_social_choropleth, render_social_legend, compute_province_view
from components.line_chart import render_social_line_chart
from components.correlation import render_social_correlation_heatmap
from components.scatter_plot import render_social_scatter
from components.benchmark import render_regency_benchmark
from components.ranking_table import render_social_fsi_table
from components.kpi_strip import render_kpi_strip
from components.insight_box import render_insight_box


st.set_page_config(
    page_title="Social — Indonesia Flood Dashboard",
    page_icon=":busts_in_silhouette:",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    render_sidebar_nav()

render_page_header(
    menu_label="Analysis · Social",
    title="Poverty, unemployment & flood severity",
    description=(
        "Spatial relationship between regional poverty, open-unemployment (TPT), "
        "and flood severity (FSI) from 2016 to 2025. Rates are descriptive "
        "averages (point-%); flood regression evidence is summarised in Key Findings."
    ),
)

try:
    reg_df  = load_social_choropleth_table()
    geo     = load_regencies_geojson()
except FileNotFoundError as e:
    st.error(f"Could not load social data: {e}")
    st.stop()

tab_national, tab_province, tab_regency = st.tabs(["National", "Province", "Regency"])

# ═════════════════════════════════════════════════════════════════════
# TAB 1 — NATIONAL
# ═════════════════════════════════════════════════════════════════════
with tab_national:

    # ── KPI strip (6 descriptive point-% KPIs) ─────────────────────────
    try:
        kpis = load_national_social_kpis()
        render_kpi_strip(kpis)
        st.markdown(
            f'<div style="font-family:{FONT_MONO};font-size:10px;color:{MUTED};'
            f'letter-spacing:0.04em;margin-top:8px;text-align:center;">'
            f'Across {fmt_int(reg_df["kemendagri_kab_code"].nunique())} regencies &middot; '
            f'poverty and unemployment, average 2016&ndash;2025 (point-%)'
            f'</div>',
            unsafe_allow_html=True,
        )
    except FileNotFoundError as e:
        st.warning(f"KPIs not available yet: {e}")

    st.divider()

    # ── Choropleth — social rate fill + FSI dot overlay ────────────────
    render_section_header(
        kicker="Spatial · descriptive",
        title=f"Social outcomes & severity — {fmt_int(reg_df['kemendagri_kab_code'].nunique())} regencies",
        description=(
            "<strong>Two-layer spatial map.</strong> "
            "Polygon fill shows the chosen social rate &mdash; "
            "<strong>average unemployment (TPT)</strong> by default, or "
            "<strong>average poverty</strong> &mdash; as point-% (deeper = higher). "
            "Blue dot overlay shows Flood Severity Index (FSI), with size "
            "proportional to severity (sqrt scaling, 0&ndash;100 scale). "
            "Unemployment is shown by default because it is the social outcome "
            "where flooding shows the stronger statistical signal. "
            "Toggle layers via the checkboxes on the right."
        ),
    )

    if geo is None:
        st.warning(
            "GeoJSON file `public/data/geo/regencies.geojson` is missing. "
            "Run nb11 (build_dashboard_geo) and copy `web/regencies.geojson` "
            "to that path."
        )
    else:
        # Map layout: 4 cols map | 1.3 cols controls + legend (matches Flood)
        col_map_n, col_ctrl_n = st.columns([4, 1.3])

        with col_ctrl_n:
            # Section: Map layers toggles
            st.markdown(
                "<div style='font-size:11px;color:#6b7280;"
                "text-transform:uppercase;letter-spacing:0.05em;"
                "margin-bottom:6px;margin-top:8px;'>Map layers</div>",
                unsafe_allow_html=True,
            )

            # Social fill toggle, with the metric choice indented beneath it
            # so the unemployment/poverty options read as part of "Social fill".
            show_metric_n = st.checkbox(
                "Social rate fill",
                value=True,
                help="Polygon fill by average unemployment or poverty 2016-2025 (point-%)",
                key="toggle_metric_social",
            )
            # Indented sub-option: which social rate fills the polygons
            sub_l, sub_r = st.columns([0.12, 0.88])
            with sub_r:
                metric_label = st.radio(
                    "Rate",
                    options=["Unemployment rate", "Poverty rate"],
                    index=0,                       # default = unemployment
                    key="social_metric_choice",
                    label_visibility="collapsed",
                    disabled=not show_metric_n,
                )
            metric = "tpt" if metric_label.startswith("Unemployment") else "poverty"

            show_fsi_dots_n = st.checkbox(
                "FSI dot overlay",
                value=True,
                help="Dot size proportional to FSI severity (sqrt scale, 0-100)",
                key="toggle_fsi_dots_social",
            )

            # Section: Legend (vertical layout, stacked below toggles)
            st.markdown(
                "<div style='font-size:11px;color:#6b7280;"
                "text-transform:uppercase;letter-spacing:0.05em;"
                "margin-top:14px;margin-bottom:6px;'>Legend</div>",
                unsafe_allow_html=True,
            )
            col = "tpt_avg" if metric == "tpt" else "poverty_avg"
            render_social_legend(
                metric=metric,
                show_metric=show_metric_n,
                show_fsi_dots=show_fsi_dots_n,
                vmin=float(reg_df[col].min()),
                vmax=float(reg_df[col].max()),
            )

        with col_map_n:
            try:
                render_social_choropleth(
                    reg_df=reg_df,
                    geojson=geo,
                    metric=metric,
                    height=520,
                    key=f"social_choropleth_{metric}",
                    show_metric=show_metric_n,
                    show_fsi_dots=show_fsi_dots_n,
                )
            except Exception as e:
                st.error(
                    f"**Could not render the choropleth.**\n\n"
                    f"`{type(e).__name__}`: {e}\n\n"
                    f"Check that `regency_table.parquet` has `poverty_avg`, "
                    f"`tpt_avg`, and that the GeoJSON `kemendagri_kab_code` matches."
                )
                with st.expander("Traceback (for debugging)"):
                    st.code(traceback.format_exc(), language="python")

    st.caption(
        "Poverty = headcount %, unemployment = open-unemployment rate (TPT), "
        "both the average of yearly point-% values 2016-2025 per regency "
        "(not the log-scale regression variables). FSI joined from the Flood "
        "dataset (single-sourced)."
    )

    st.divider()

    # ── Annual trend line — poverty + unemployment (left) vs FSI (right) ──
    render_section_header(
        kicker="Temporal · descriptive",
        title="Annual trend 2016–2025",
        description=(
            "National poverty and open-unemployment (TPT) rates on the left axis "
            "against average Flood Severity (FSI, dotted) on the right. If "
            "flooding drove these social outcomes, the lines would move together; "
            "the regression in Key Findings is the formal test."
        ),
    )
    try:
        annual_s = load_national_social_series()
        render_social_line_chart(annual=annual_s, height=440, key="social_national_line")
    except FileNotFoundError as e:
        st.warning(f"Annual series not available: {e}")
    except Exception as e:
        st.warning(f"Could not render social line chart: {e}")

    st.divider()

    # ── Correlation heatmap (left) + Most flood-affected table (right) ──
    render_section_header(
        kicker="Spatial · descriptive",
        title="Flood vs social outcomes — correlations & most-affected regencies",
        description=(
            "<strong>Left:</strong> bivariate correlations between flood "
            "dimensions (event frequency, human cost, physical damage) plus "
            "socioeconomic context (mean years schooling, log population) and "
            "the two social outcomes. <strong>Right:</strong> the ten "
            "highest-FSI regencies with their poverty and unemployment. "
            "Correlations are <em>descriptive</em> &mdash; not controlled "
            "regression effects."
        ),
    )
    col_heat, col_tbl = st.columns([1, 1], gap="medium")
    with col_heat:
        try:
            corr = load_social_correlation()
            render_social_correlation_heatmap(corr=corr, height=300, key="social_corr")
            st.caption(
                f"Pearson r, pooled panel (n={corr.get('n', '')}). FSI excluded "
                f"(weighted composite of the three flood dimensions). Poverty "
                f"correlates most with schooling and population &mdash; not flood "
                f"&mdash; consistent with the regression finding of no robust flood effect."
            )
        except FileNotFoundError as e:
            st.warning(f"Correlation data not available: {e}")
        except Exception as e:
            st.warning(f"Could not render correlation heatmap: {e}")
    with col_tbl:
        try:
            fsi_tbl = load_social_fsi_table(top_n=10)
            render_social_fsi_table(fsi_tbl)
        except FileNotFoundError as e:
            st.warning(f"FSI table not available: {e}")
        except Exception as e:
            st.warning(f"Could not render FSI table: {e}")

    st.divider()

    # ── Key Findings — social regression evidence (RQ2 social) ─────────
    render_section_header(
        kicker="Diagnostic synthesis",
        title="Key Findings",
        description=(
            "Narrative interpretation of the social regression evidence (RQ2 social)."
        ),
    )

    bullets = [
        f"<strong>Flooding shows no robust association with poverty.</strong> "
        f"In the fixed-effects panel (controlling for population and education), the "
        f"flood block (frequency, human cost, physical damage) is not jointly "
        f"significant for the poverty rate under the preferred Driscoll&ndash;Kraay "
        f"standard errors, and no individual flood dimension is significant. The "
        f"apparent significance of the whole model is driven by population, a control, "
        f"not by flooding. We therefore do not conclude a flood effect on poverty.",

        f"<strong>Evidence for unemployment is weak and not robust.</strong> "
        f"For open unemployment (TPT), the flood block is at most suggestive: any "
        f"joint significance is sensitive to the choice of standard errors and "
        f"specification, no single dimension is individually significant, and the "
        f"within-R&sup2; is effectively zero, indicating the model explains almost "
        f"none of the within-regency variation. This is consistent with annual, "
        f"aggregated administrative data being insensitive to short-lived flood shocks.",

        f"<strong>How to read these maps.</strong> The colours show descriptive "
        f"average rates, not flood effects; a high-unemployment regency that also has "
        f"large FSI bubbles is a spatial coincidence to investigate, not evidence of "
        f"causation. The regression above is the basis for any causal-style claim, and "
        f"it finds flooding is not a robust driver of either social outcome at the "
        f"annual regency level &mdash; in contrast to the economic results, where "
        f"physical damage does significantly reduce aggregate GRDP growth.",
    ]

    render_insight_box(
        bullets=bullets,
        title="RQ2 social evidence base",
        kicker="Narrative interpretation",
        variant="info",
    )

# ═════════════════════════════════════════════════════════════════════
# TAB 2 — PROVINCE
# ═════════════════════════════════════════════════════════════════════
with tab_province:

    provinces = list_social_provinces()
    if not provinces:
        st.warning("No province data available.")
        st.stop()

    default_idx = 0
    if "selected_province_social" in st.session_state:
        cur = st.session_state["selected_province_social"]
        if cur in provinces:
            default_idx = provinces.index(cur)

    col_label, col_dd, _ = st.columns([2, 4, 6])
    with col_label:
        st.markdown(
            f'<div style="font-family:{FONT_BODY};font-size:13px;color:{INK};'
            f'line-height:38px;font-weight:500;">Selected province</div>',
            unsafe_allow_html=True,
        )
    with col_dd:
        prov_name = st.selectbox(
            "Province", options=provinces, index=default_idx,
            key="_social_province_dropdown", label_visibility="collapsed",
        )
    st.session_state["selected_province_social"] = prov_name

    try:
        reg_df_p = load_province_social_choropleth(prov_name)
    except Exception as e:
        st.error(f"Could not load province social data: {e}")
        st.stop()

    st.markdown(
        f'<div style="font-family:{FONT_DISPLAY};font-size:20px;'
        f'font-weight:600;color:{INK};margin:18px 0 14px 0;">{prov_name}</div>',
        unsafe_allow_html=True,
    )

    # ── KPI strip (province scope) ─────────────────────────────────────
    try:
        kpis_p = load_province_social_kpis(prov_name)
        render_kpi_strip(kpis_p)
        st.markdown(
            f'<div style="font-family:{FONT_MONO};font-size:10px;color:{MUTED};'
            f'letter-spacing:0.04em;margin-top:8px;text-align:center;">'
            f'{fmt_int(len(reg_df_p))} regencies in {prov_name} &middot; '
            f'poverty and unemployment, average 2016&ndash;2025 (point-%)'
            f'</div>',
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.warning(f"Province KPIs not available: {e}")

    st.divider()

    # ── Choropleth (zoomed to province) ────────────────────────────────
    render_section_header(
        kicker="Spatial · descriptive",
        title=f"Social outcomes & severity — {prov_name}",
        description=(
            "<strong>Two-layer spatial map</strong> zoomed to the province. "
            "Polygon fill shows the chosen social rate (unemployment by default, "
            "or poverty) as point-%; blue dots show FSI sized by severity. "
            "Toggle layers on the right."
        ),
    )

    if geo is None:
        st.warning("GeoJSON missing — cannot render the province map.")
    else:
        col_map_p, col_ctrl_p = st.columns([4, 1.3])

        with col_ctrl_p:
            st.markdown(
                "<div style='font-size:11px;color:#6b7280;"
                "text-transform:uppercase;letter-spacing:0.05em;"
                "margin-bottom:6px;margin-top:8px;'>Map layers</div>",
                unsafe_allow_html=True,
            )
            show_metric_p = st.checkbox(
                "Social rate fill", value=True,
                key=f"toggle_metric_social_prov_{prov_name}",
            )
            sub_l, sub_r = st.columns([0.12, 0.88])
            with sub_r:
                metric_label_p = st.radio(
                    "Rate", options=["Unemployment rate", "Poverty rate"],
                    index=0, key=f"social_metric_prov_{prov_name}",
                    label_visibility="collapsed", disabled=not show_metric_p,
                )
            metric_p = "tpt" if metric_label_p.startswith("Unemployment") else "poverty"
            show_fsi_dots_p = st.checkbox(
                "FSI dot overlay", value=True,
                key=f"toggle_fsi_social_prov_{prov_name}",
            )

            st.markdown(
                "<div style='font-size:11px;color:#6b7280;"
                "text-transform:uppercase;letter-spacing:0.05em;"
                "margin-top:14px;margin-bottom:6px;'>Legend</div>",
                unsafe_allow_html=True,
            )
            col_p = "tpt_avg" if metric_p == "tpt" else "poverty_avg"
            render_social_legend(
                metric=metric_p, show_metric=show_metric_p,
                show_fsi_dots=show_fsi_dots_p,
                vmin=float(reg_df_p[col_p].min()),
                vmax=float(reg_df_p[col_p].max()),
            )

        with col_map_p:
            try:
                _view = compute_province_view(reg_df_p, geo)
                center, zoom = _view[0], _view[1]
                render_social_choropleth(
                    reg_df=reg_df_p, geojson=geo, metric=metric_p,
                    height=520, key=f"social_choropleth_prov_{prov_name}_{metric_p}",
                    mapbox_zoom=zoom, mapbox_center=center,
                    show_metric=show_metric_p, show_fsi_dots=show_fsi_dots_p,
                )
            except Exception as e:
                st.error(f"**Could not render the choropleth.**\n\n`{e}`")
                with st.expander("Traceback (for debugging)"):
                    st.code(traceback.format_exc(), language="python")

    st.divider()

    # ── Annual line chart (province scope) ─────────────────────────────
    render_section_header(
        kicker="Temporal · descriptive",
        title=f"Annual trend — {prov_name}",
        description=(
            "Province-average poverty and unemployment (left, point-%) against "
            "average Flood Severity (FSI, dotted, right). Descriptive means."
        ),
    )
    try:
        annual_sp = load_province_social_series(prov_name)
        render_social_line_chart(annual=annual_sp, height=440,
                                 key=f"social_line_prov_{prov_name}")
    except FileNotFoundError as e:
        st.warning(f"Province annual series not available: {e}")
    except Exception as e:
        st.warning(f"Could not render province line chart: {e}")

    st.divider()

    # ── Quadrant scatters (two views) + regency table below ───────────
    render_section_header(
        kicker="Spatial · descriptive",
        title=f"Flood severity vs social outcomes — {prov_name}",
        description=(
            "Each dot is a regency, split into four quadrants at the province "
            "median FSI and median rate. The red corner (high flood + high rate) "
            "flags where both coincide. <strong>Descriptive only</strong> &mdash; "
            "the regression finds flooding is not a robust driver of either outcome."
        ),
    )

    col_tpt, col_pov = st.columns(2, gap="large")
    with col_tpt:
        st.markdown(
            f"<div style='font-family:{FONT_BODY};font-size:13px;font-weight:600;"
            f"color:{INK};margin-bottom:4px;'>FSI vs Unemployment (TPT)</div>",
            unsafe_allow_html=True,
        )
        try:
            render_social_scatter(reg_df_p, metric="tpt", prov_name=prov_name,
                                  height=420, key=f"social_scatter_tpt_{prov_name}")
        except Exception as e:
            st.warning(f"Could not render unemployment scatter: {e}")
    with col_pov:
        st.markdown(
            f"<div style='font-family:{FONT_BODY};font-size:13px;font-weight:600;"
            f"color:{INK};margin-bottom:4px;'>FSI vs Poverty</div>",
            unsafe_allow_html=True,
        )
        try:
            render_social_scatter(reg_df_p, metric="poverty", prov_name=prov_name,
                                  height=420, key=f"social_scatter_pov_{prov_name}")
        except Exception as e:
            st.warning(f"Could not render poverty scatter: {e}")

    st.divider()

    # ── Regency table (full width, sorted by FSI desc) ─────────────────
    render_section_header(
        kicker="Tabular data",
        title=f"Regency-level data — {prov_name}",
        description=(
            f"Average poverty and unemployment (point-%, 2016&ndash;2025) with "
            f"flood severity for all regencies in {prov_name}. Sorted by FSI "
            f"(most flood-affected first); click a header to re-sort, or use the "
            f"table toolbar to download."
        ),
    )
    tbl = (reg_df_p.sort_values("FSI_index", ascending=False).reset_index(drop=True)
           if "FSI_index" in reg_df_p.columns else reg_df_p.reset_index(drop=True))
    display_df = pd.DataFrame({
        "Regency":         tbl["kemendagri_kab_name"].values,
        "FSI (0–100)":     (tbl["FSI_index"].round(1).values
                            if "FSI_index" in tbl.columns else [None] * len(tbl)),
        "Poverty %":       tbl["poverty_avg"].round(2).values,
        "Unemployment %":  tbl["tpt_avg"].round(2).values,
    })
    st.dataframe(
        display_df, width="stretch", hide_index=True,
        height=min(420, 45 + 36 * len(display_df)),
    )


# ═════════════════════════════════════════════════════════════════════
# TAB 3 — REGENCY
# ═════════════════════════════════════════════════════════════════════
with tab_regency:

    provinces_r = list_social_provinces()
    if not provinces_r:
        st.warning("No regency data available.")
        st.stop()

    # Province → Regency cascade
    default_prov_idx = 0
    if "selected_province_social" in st.session_state:
        cur_p = st.session_state["selected_province_social"]
        if cur_p in provinces_r:
            default_prov_idx = provinces_r.index(cur_p)

    col_pl, col_pd, col_kl, col_kd = st.columns([1.2, 3, 1.2, 3], gap="medium")
    with col_pl:
        st.markdown(
            f'<div style="font-family:{FONT_BODY};font-size:13px;color:{INK};'
            f'line-height:38px;font-weight:500;">Province</div>',
            unsafe_allow_html=True,
        )
    with col_pd:
        prov_name_r = st.selectbox(
            "Province", options=provinces_r, index=default_prov_idx,
            key="_social_regency_province", label_visibility="collapsed",
        )

    regs = list_province_social_regencies(prov_name_r)
    if not regs:
        st.info("No regencies found in this province.")
        st.stop()
    kab_codes  = [r["code"] for r in regs]
    kab_labels = [r["name"] for r in regs]

    default_kab_idx = 0
    if "selected_regency_social" in st.session_state:
        cur_k = st.session_state["selected_regency_social"]
        if cur_k in kab_codes:
            default_kab_idx = kab_codes.index(cur_k)

    with col_kl:
        st.markdown(
            f'<div style="font-family:{FONT_BODY};font-size:13px;color:{INK};'
            f'line-height:38px;font-weight:500;">Regency</div>',
            unsafe_allow_html=True,
        )
    with col_kd:
        chosen_kab_label = st.selectbox(
            "Regency", options=kab_labels, index=default_kab_idx,
            key="_social_regency_kab", label_visibility="collapsed",
        )
    kab_code = kab_codes[kab_labels.index(chosen_kab_label)]
    st.session_state["selected_regency_social"] = kab_code

    # Regency name header
    st.markdown(
        f'<div style="font-family:{FONT_DISPLAY};font-size:20px;'
        f'font-weight:600;color:{INK};margin:18px 0 14px 0;">{chosen_kab_label}</div>',
        unsafe_allow_html=True,
    )

    # ── KPI strip (3: avg poverty, avg unemployment, FSI) ──────────────
    try:
        kpis_r = load_regency_social_kpis(kab_code)
        render_kpi_strip(kpis_r)
        st.markdown(
            f'<div style="font-family:{FONT_MONO};font-size:10px;color:{MUTED};'
            f'letter-spacing:0.04em;margin-top:8px;text-align:center;">'
            f'{chosen_kab_label} &middot; {prov_name_r} &middot; '
            f'average 2016&ndash;2025 (point-%)'
            f'</div>',
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.warning(f"Regency KPIs not available: {e}")

    st.divider()

    # ── Choropleth (zoomed to the single regency) ──────────────────────
    render_section_header(
        kicker="Spatial · descriptive",
        title=f"Social outcomes & severity — {chosen_kab_label}",
        description=(
            "<strong>Two-layer spatial map</strong> zoomed to the regency. "
            "Polygon fill shows the chosen social rate (unemployment by default, "
            "or poverty); blue dot shows FSI sized by severity."
        ),
    )

    reg_row_df = reg_df[reg_df["kemendagri_kab_code"].astype(str) == str(kab_code)].copy()

    if geo is None:
        st.warning("GeoJSON missing — cannot render the regency map.")
    elif reg_row_df.empty:
        st.info("Selected regency not found in the map data.")
    else:
        col_map_r, col_ctrl_r = st.columns([4, 1.3])

        with col_ctrl_r:
            st.markdown(
                "<div style='font-size:11px;color:#6b7280;"
                "text-transform:uppercase;letter-spacing:0.05em;"
                "margin-bottom:6px;margin-top:8px;'>Map layers</div>",
                unsafe_allow_html=True,
            )
            show_metric_r = st.checkbox(
                "Social rate fill", value=True,
                key=f"toggle_metric_social_reg_{kab_code}",
            )
            sub_l, sub_r = st.columns([0.12, 0.88])
            with sub_r:
                metric_label_r = st.radio(
                    "Rate", options=["Unemployment rate", "Poverty rate"],
                    index=0, key=f"social_metric_reg_{kab_code}",
                    label_visibility="collapsed", disabled=not show_metric_r,
                )
            metric_r = "tpt" if metric_label_r.startswith("Unemployment") else "poverty"
            show_fsi_dots_r = st.checkbox(
                "FSI dot overlay", value=True,
                key=f"toggle_fsi_social_reg_{kab_code}",
            )

            st.markdown(
                "<div style='font-size:11px;color:#6b7280;"
                "text-transform:uppercase;letter-spacing:0.05em;"
                "margin-top:14px;margin-bottom:6px;'>Legend</div>",
                unsafe_allow_html=True,
            )
            col_r = "tpt_avg" if metric_r == "tpt" else "poverty_avg"
            render_social_legend(
                metric=metric_r, show_metric=show_metric_r,
                show_fsi_dots=show_fsi_dots_r,
                vmin=float(reg_row_df[col_r].min()),
                vmax=float(reg_row_df[col_r].max()),
            )

        with col_map_r:
            try:
                _view = compute_province_view(reg_row_df, geo, padding=0.40)
                center, zoom = _view[0], _view[1]
                render_social_choropleth(
                    reg_df=reg_row_df, geojson=geo, metric=metric_r,
                    height=520, key=f"social_choropleth_reg_{kab_code}_{metric_r}",
                    mapbox_zoom=zoom, mapbox_center=center,
                    show_metric=show_metric_r, show_fsi_dots=show_fsi_dots_r,
                )
            except Exception as e:
                st.error(f"**Could not render the choropleth.**\n\n`{e}`")
                with st.expander("Traceback (for debugging)"):
                    st.code(traceback.format_exc(), language="python")

    st.divider()

    # ── Annual line chart (regency scope) ──────────────────────────────
    render_section_header(
        kicker="Temporal · descriptive",
        title=f"Annual trend — {chosen_kab_label}",
        description=(
            "Regency poverty and unemployment (left, point-%) against Flood "
            "Severity (FSI, dotted, right), year by year. Descriptive."
        ),
    )
    try:
        annual_sr = load_regency_social_series(kab_code)
        render_social_line_chart(annual=annual_sr, height=440,
                                 key=f"social_line_reg_{kab_code}")
    except FileNotFoundError as e:
        st.warning(f"Regency annual series not available: {e}")
    except Exception as e:
        st.warning(f"Could not render regency line chart: {e}")

    # ── Benchmark vs province & national + rank badge ──────────────────
    render_section_header(
        kicker="Comparative · descriptive",
        title="How this regency compares",
        description=(
            "The regency's average poverty and unemployment against its province "
            "and the national average, with its rank inside the province. Context "
            "for the single-regency figures above &mdash; not a flood effect."
        ),
    )
    try:
        bench = load_regency_social_benchmark(kab_code)
        render_regency_benchmark(bench)
    except Exception as e:
        st.warning(f"Benchmark not available: {e}")

    st.divider()