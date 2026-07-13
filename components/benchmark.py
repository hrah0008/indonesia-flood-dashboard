"""
components/benchmark.py
=======================
Benchmark visual for a single regency: horizontal bars comparing the regency's
rate against its province average and the national average, plus a rank badge
showing its position within the province. Built for the Social Regency tab,
where comparison-across-regencies views (scatter, ranking tables) don't apply.
"""

import streamlit as st

from lib.colors import INK, MUTED, FONT_BODY, FONT_MONO


def _bar_row(label: str, value: float, vmax: float, color: str,
             emphasis: bool = False) -> str:
    """One labelled horizontal bar (single-line inline styles)."""
    pct = 0 if vmax <= 0 else max(2, min(100, value / vmax * 100))
    weight = "600" if emphasis else "400"
    name_color = INK if emphasis else MUTED
    val_color = INK if emphasis else MUTED
    return (
        f'<div style="margin-bottom:9px;">'
        f'<div style="display:flex;justify-content:space-between;font-family:{FONT_BODY};'
        f'font-size:12.5px;margin-bottom:3px;">'
        f'<span style="color:{name_color};font-weight:{weight};">{label}</span>'
        f'<span style="color:{val_color};font-weight:{weight};">{value:.2f}%</span></div>'
        f'<div style="height:8px;background:#eef0f2;border-radius:4px;">'
        f'<div style="height:8px;width:{pct:.0f}%;background:{color};border-radius:4px;"></div>'
        f'</div></div>'
    )


def _panel(title: str, reg_val: float, prov_val: float, prov_name: str,
           nat_val: float, rank: tuple, reg_color: str, mid_color: str) -> str:
    vmax = max(reg_val, prov_val, nat_val) * 1.05
    pos, n = rank
    # relative position text vs province average
    diff = reg_val - prov_val
    if abs(diff) < 0.05:
        rel = f"On par with the {prov_name} average"
        rel_color = MUTED
    elif diff < 0:
        rel = f"{abs(diff):.2f} pts below the {prov_name} average"
        rel_color = "#3b6d11"
    else:
        rel = f"{abs(diff):.2f} pts above the {prov_name} average"
        rel_color = "#a32d2d"

    bars = (
        _bar_row("This regency", reg_val, vmax, reg_color, emphasis=True)
        + _bar_row(f"{prov_name} average", prov_val, vmax, mid_color)
        + _bar_row("National average", nat_val, vmax, "#b4b2a9")
    )
    return (
        f'<div style="background:#fafafa;border-radius:12px;padding:14px 16px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
        f'<span style="font-family:{FONT_BODY};font-size:13px;color:{MUTED};">{title}</span>'
        f'<span style="font-family:{FONT_MONO};font-size:11px;color:{INK};'
        f'background:#eef0f2;padding:2px 8px;border-radius:8px;">rank #{pos} of {n}</span>'
        f'</div>'
        f'{bars}'
        f'<div style="font-family:{FONT_BODY};font-size:11.5px;color:{rel_color};margin-top:10px;">{rel}</div>'
        f'</div>'
    )


def render_regency_benchmark(bench: dict) -> None:
    """Two side-by-side benchmark panels (poverty + unemployment) for a regency.

    `bench` is the output of load_regency_social_benchmark(). Rank #1 = highest
    rate in the province (i.e. worst); shown as a mono badge per panel.
    """
    if not bench:
        st.info("Benchmark data not available for this regency.")
        return

    reg = bench["regency"]
    prov = bench["province"]
    nat = bench["national"]
    rank = bench["rank"]

    col_pov, col_tpt = st.columns(2, gap="medium")
    with col_pov:
        st.markdown(
            _panel("Poverty rate (avg 2016–2025)",
                   reg["poverty"], prov["poverty"], prov["name"], nat["poverty"],
                   rank["poverty"], "#a32d2d", "#f09595"),
            unsafe_allow_html=True,
        )
    with col_tpt:
        st.markdown(
            _panel("Unemployment / TPT (avg 2016–2025)",
                   reg["tpt"], prov["tpt"], prov["name"], nat["tpt"],
                   rank["tpt"], "#ba7517", "#ef9f27"),
            unsafe_allow_html=True,
        )

    st.caption(
        "Bars compare this regency's average rate against its province and the "
        "national average. Rank is the regency's position within its province "
        "(#1 = highest rate). Descriptive context, not a flood effect."
    )
