"""
components/ranking_table.py
===========================
Three Top-10 mini-table renderers for the National tab of the Flood page.

Definitions (each table answers a different policy question):

  1. render_top10_fsi(df)        — Top 10 regencies with HIGHEST FSI Score
                                    (composite severity; all regencies eligible)

  2. render_top10_hotspots(df)   — Top 10 regencies with HIGHEST Gi* z-score
                                    among regencies classified as Hot 99/95/90.
                                    Cold and Not-significant are EXCLUDED.

  3. render_top10_mk(df)         — Top 10 regencies with HIGHEST positive τ
                                    among regencies that are MK-significant.
                                    "Trend INCREASING" only.

DISPLAY NOTE — FSI Score, NOT percentage
----------------------------------------
The `FSI_percent` column from nb12 is a 0-100 MIN-MAX RESCALE of the
Z-score composite. It is NOT a percentage (no denominator). Displays here
use `fmt_score` to render values as "89.65 / 100" rather than "89.65%",
matching the academic critique that "%" without a denominator is
semantically misleading.

When fewer than 10 regencies pass a filter, the table shows ONLY the
matching rows (honest — no padding). A small "Showing X of Y" caption
sits under each title.

All HTML uses single-line inline styles so Streamlit's markdown renderer
doesn't treat multi-line indented HTML as code blocks.
"""

import pandas as pd
import streamlit as st

from lib.colors import (
    FSI_COLORS, GI_COLORS, MK_BADGE,
    INK, MUTED, HAIRLINE, INDIGO,
    FONT_DISPLAY, FONT_BODY, FONT_MONO,
)
from lib.format import fmt_int, fmt_decimal, fmt_score, fmt_score_only


# ─────────────────────────────────────────────────────────────────────
# Filters used by tables 2 and 3
# ─────────────────────────────────────────────────────────────────────
_HOT_CATS = ("Hot 99%", "Hot 95%", "Hot 90%")


def _filter_hot(reg_df: pd.DataFrame) -> pd.DataFrame:
    """Keep only regencies classified as Gi* Hot at any confidence level."""
    if "gi_cat_FSI" not in reg_df.columns:
        return reg_df.iloc[0:0]
    return reg_df[reg_df["gi_cat_FSI"].isin(_HOT_CATS)].copy()


def _filter_mk_increasing(reg_df: pd.DataFrame) -> pd.DataFrame:
    """Keep only regencies with significantly INCREASING event-count trend."""
    if "mk_tau_event" not in reg_df.columns or "mk_sig_event_count" not in reg_df.columns:
        return reg_df.iloc[0:0]
    mask = (reg_df["mk_sig_event_count"].astype(bool)) & (reg_df["mk_tau_event"] > 0)
    return reg_df[mask].copy()


# ─────────────────────────────────────────────────────────────────────
# Chip builders
# ─────────────────────────────────────────────────────────────────────
def _chip(label: str, fg: str, bg: str, font_size: int = 10) -> str:
    style = (
        f"display:inline-block;padding:2px 8px;border-radius:10px;"
        f"font-family:{FONT_MONO};font-size:{font_size}px;font-weight:600;"
        f"letter-spacing:0.04em;color:{fg};background:{bg};white-space:nowrap;"
    )
    return f'<span style="{style}">{label}</span>'


def _fsi_tier_chip(tier: str) -> str:
    color = FSI_COLORS.get(tier, "#888888")
    bg = {
        "Catastrophic": "#fee2e2",
        "High":         "#fee2e2",
        "Moderate":     "#fef3c7",
        "Low":          "#dcfce7",
    }.get(tier, "#f3f4f6")
    return _chip(tier, color, bg)


def _gi_chip(gi_cat: str) -> str:
    if not isinstance(gi_cat, str) or gi_cat in ("Not significant", "Not sig."):
        return _chip("Not sig.", MUTED, "#f3f4f6")
    color = GI_COLORS.get(gi_cat, "#666666")
    bg = "#fee2e2" if "Hot" in gi_cat else "#dbeafe"
    return _chip(gi_cat, color, bg)


def _mk_up_chip() -> str:
    b = MK_BADGE["increasing"]
    return _chip(b["label"], b["fg"], b["bg"])


# ─────────────────────────────────────────────────────────────────────
# Mini-card structural helpers
# ─────────────────────────────────────────────────────────────────────
def _mini_card_header(label: str, title: str, count_caption: str = "") -> str:
    head_style = (
        f"padding:10px 12px 8px;border-bottom:1px solid {HAIRLINE};"
        f"background:#fafafa;"
    )
    label_style = (
        f"font-family:{FONT_MONO};font-size:9.5px;font-weight:600;"
        f"letter-spacing:0.10em;text-transform:uppercase;color:{MUTED};"
    )
    title_style = (
        f"font-family:{FONT_DISPLAY};font-size:14px;font-weight:600;"
        f"color:{INK};margin-top:2px;"
    )
    count_style = (
        f"font-family:{FONT_MONO};font-size:9.5px;color:{MUTED};"
        f"letter-spacing:0.04em;margin-top:3px;"
    )
    count_block = (
        f'<div style="{count_style}">{count_caption}</div>'
        if count_caption else ""
    )
    return (
        f'<div style="{head_style}">'
        f'<div style="{label_style}">{label}</div>'
        f'<div style="{title_style}">{title}</div>'
        f'{count_block}'
        f'</div>'
    )


def _mini_card_open(label: str, title: str, count_caption: str = "") -> str:
    card_style = (
        f"background:white;border:1px solid {HAIRLINE};"
        f"border-radius:6px;overflow:hidden;"
    )
    return (
        f'<div style="{card_style}">'
        f'{_mini_card_header(label, title, count_caption)}'
    )


def _mini_row(rank: int, name: str, prov: str, score_html: str,
              context: str = "") -> str:
    row_style = (
        f"display:grid;grid-template-columns:24px 1fr auto;gap:8px;"
        f"padding:8px 12px;align-items:center;"
        f"border-bottom:1px solid {HAIRLINE};font-size:12px;"
    )
    rank_style = (
        f"font-family:{FONT_MONO};font-size:10.5px;font-weight:600;"
        f"color:{MUTED};text-align:right;"
    )
    name_style = (
        f"font-family:{FONT_DISPLAY};font-size:12.5px;font-weight:600;"
        f"color:{INK};line-height:1.2;"
    )
    prov_style = (
        f"font-family:{FONT_BODY};font-size:10px;font-weight:400;color:{MUTED};"
    )
    context_block = (
        f'<div style="font-family:{FONT_MONO};font-size:9.5px;color:{MUTED};'
        f'margin-top:2px;letter-spacing:0.02em;">{context}</div>'
        if context else ""
    )
    return (
        f'<div style="{row_style}">'
        f'<span style="{rank_style}">{rank}</span>'
        f'<div>'
        f'<div style="{name_style}">{name}</div>'
        f'<div style="{prov_style}">{prov}</div>'
        f'{context_block}'
        f'</div>'
        f'<div style="text-align:right;">{score_html}</div>'
        f'</div>'
    )


def _empty_state(message: str) -> str:
    style = (
        f"padding:24px 16px;text-align:center;color:{MUTED};"
        f"font-family:{FONT_BODY};font-size:12px;line-height:1.55;"
    )
    return f'<div style="{style}">{message}</div>'


# ─────────────────────────────────────────────────────────────────────
# 1) Top 10 by FSI Score — composite severity (all regencies eligible)
# ─────────────────────────────────────────────────────────────────────
def render_top10_fsi(reg_df: pd.DataFrame, top_n: int = 10) -> None:
    total = len(reg_df)
    df = reg_df.sort_values("FSI_percent", ascending=False).head(top_n).reset_index(drop=True)
    shown = len(df)
    count_caption = f"Showing {shown} of {total} regencies"

    rows_html = []
    for i, r in df.iterrows():
        score_html = (
            f'<div style="font-family:{FONT_DISPLAY};font-size:13px;'
            f'font-weight:600;color:{INK};">{fmt_score(r.get("FSI_percent"), 2)}</div>'
            f'<div style="margin-top:3px;">{_fsi_tier_chip(r.get("FSI_tier", "-"))}</div>'
        )
        context = (
            f'{fmt_int(r.get("event_count"))} events &middot; '
            f'{fmt_int(r.get("deaths"))} deaths'
        )
        rows_html.append(_mini_row(
            rank=i + 1,
            name=r.get("kemendagri_kab_name", "-"),
            prov=r.get("kemendagri_prov_name", "-"),
            score_html=score_html,
            context=context,
        ))

    html = (
        _mini_card_open("Severity ranking",
                        f"Top {top_n} by FSI Score",
                        count_caption)
        + ("".join(rows_html) if rows_html else _empty_state("No regencies available."))
        + '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# 2) Top 10 hot spots — by Gi* z-score, filtered to Hot only
# ─────────────────────────────────────────────────────────────────────
def render_top10_hotspots(reg_df: pd.DataFrame, top_n: int = 10) -> None:
    if "gi_z_FSI" not in reg_df.columns:
        st.info("gi_z_FSI column missing — cannot rank by hot-spot strength.")
        return

    hot = _filter_hot(reg_df)
    total_hot = len(hot)
    df = hot.sort_values("gi_z_FSI", ascending=False).head(top_n).reset_index(drop=True)
    shown = len(df)

    if total_hot == 0:
        count_caption = "No Gi* hot spots in the data"
    else:
        count_caption = f"Showing {shown} of {total_hot} hot spots"

    rows_html = []
    for i, r in df.iterrows():
        z = r.get("gi_z_FSI")
        z_label = fmt_decimal(z, 2) if z is not None and not pd.isna(z) else "—"
        score_html = (
            f'<div style="font-family:{FONT_DISPLAY};font-size:13px;'
            f'font-weight:600;color:{INK};">z = {z_label}</div>'
            f'<div style="margin-top:3px;">'
            f'{_gi_chip(r.get("gi_cat_FSI", "Not sig."))}'
            f'</div>'
        )
        # Context line: events + FSI score (compact "X.X" not "X.X%")
        context = (
            f'{fmt_int(r.get("event_count"))} events &middot; '
            f'FSI {fmt_score_only(r.get("FSI_percent"), 1)}'
        )
        rows_html.append(_mini_row(
            rank=i + 1,
            name=r.get("kemendagri_kab_name", "-"),
            prov=r.get("kemendagri_prov_name", "-"),
            score_html=score_html,
            context=context,
        ))

    body = ("".join(rows_html) if rows_html
            else _empty_state(
                "No regencies meet the Gi* hot-spot threshold "
                "(Hot 90% / 95% / 99%)."
            ))

    html = (
        _mini_card_open("Spatial clustering",
                        f"Top {top_n} hot spots",
                        count_caption)
        + body
        + '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# 3) Top 10 by MK — filtered to significantly INCREASING only
# ─────────────────────────────────────────────────────────────────────
def render_top10_mk(reg_df: pd.DataFrame, top_n: int = 10) -> None:
    if "mk_tau_event" not in reg_df.columns or "mk_sig_event_count" not in reg_df.columns:
        st.info(
            "MK τ column missing from data. Re-run nb12 with the τ-export "
            "patch (cell 4 STEP 3c)."
        )
        return

    worsening = _filter_mk_increasing(reg_df)
    total_worsen = len(worsening)
    df = worsening.sort_values("mk_tau_event", ascending=False).head(top_n).reset_index(drop=True)
    shown = len(df)

    if total_worsen == 0:
        count_caption = "No regencies show rising FSI Score"
    else:
        count_caption = f"Showing {shown} of {total_worsen} regencies with rising FSI"

    rows_html = []
    for i, r in df.iterrows():
        tau = r.get("mk_tau_event")
        slope = r.get("mk_slope_event")
        tau_label = (f"↑ τ = {tau:+.2f}"
                     if tau is not None and not pd.isna(tau)
                     else "—")
        # slope % IS a real percentage (rate of change per year, with units)
        slope_label = (f"{slope:+.2f}%/yr"
                       if slope is not None and not pd.isna(slope) else "")

        score_html = (
            f'<div style="font-family:{FONT_DISPLAY};font-size:13px;'
            f'font-weight:600;color:{INK};">{tau_label}</div>'
            f'<div style="margin-top:3px;">{_mk_up_chip()}</div>'
        )
        # Context: slope %/yr · FSI score (NOT percentage)
        context = (
            f'{slope_label} &middot; FSI {fmt_score_only(r.get("FSI_percent"), 1)}'
            if slope_label
            else f'FSI {fmt_score_only(r.get("FSI_percent"), 1)}'
        )
        rows_html.append(_mini_row(
            rank=i + 1,
            name=r.get("kemendagri_kab_name", "-"),
            prov=r.get("kemendagri_prov_name", "-"),
            score_html=score_html,
            context=context,
        ))

    body = ("".join(rows_html) if rows_html
            else _empty_state(
                "No regencies show a statistically significant rising trend "
                "in integrated FSI Score (Mann-Kendall on annual "
                "FSI_temporal_pct, Hamed-Rao corrected, BH-FDR &alpha; = 0.05)."
            ))

    html = (
        _mini_card_open("Temporal trend",
                        f"Top {top_n} by rising FSI Score",
                        count_caption)
        + body
        + '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# Overlap helper — uses the same filters as the renderers
# ─────────────────────────────────────────────────────────────────────
def compute_top10_overlaps(reg_df: pd.DataFrame, top_n: int = 10) -> dict:
    """Returns set intersections between the three Top-N lists, using the
    SAME filters that the renderers apply. So 'X regencies in all 3 lists'
    matches exactly what's visible in the tables."""
    fsi_top = reg_df.nlargest(top_n, "FSI_percent")
    fsi_set = set(fsi_top["kemendagri_kab_code"])

    if "gi_z_FSI" in reg_df.columns:
        hot = _filter_hot(reg_df)
        hot_top = hot.nlargest(top_n, "gi_z_FSI")
        hot_set = set(hot_top["kemendagri_kab_code"])
    else:
        hot_set = set()

    if "mk_tau_event" in reg_df.columns:
        worsen = _filter_mk_increasing(reg_df)
        mk_top = worsen.nlargest(top_n, "mk_tau_event")
        mk_set = set(mk_top["kemendagri_kab_code"])
    else:
        mk_set = set()

    triple = fsi_set & hot_set & mk_set
    names_all = (
        reg_df[reg_df["kemendagri_kab_code"].isin(triple)]
        ["kemendagri_kab_name"].tolist()
    )

    return {
        "fsi_set":      fsi_set,
        "hot_set":      hot_set,
        "mk_set":       mk_set,
        "in_all_three": len(triple),
        "fsi_hot":      len(fsi_set & hot_set),
        "fsi_mk":       len(fsi_set & mk_set),
        "hot_mk":       len(hot_set & mk_set),
        "names_all":    names_all,
    }


def render_table_caption(text: str) -> None:
    style = (
        f"font-family:{FONT_BODY};font-size:11px;color:{MUTED};"
        f"line-height:1.5;margin:8px 4px 0 4px;"
    )
    st.markdown(f'<div style="{style}">{text}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# Backward-compatible wide ranking table (kept for any legacy callers)
# ─────────────────────────────────────────────────────────────────────
def render_ranking_table(rows_df: pd.DataFrame, top_n: int = 10) -> None:
    """Original wide FSI-only ranking table. Use the three new mini-table
    renderers above instead."""
    if rows_df is None or len(rows_df) == 0:
        st.info("No ranking data available.")
        return

    df = rows_df.sort_values("FSI_percent", ascending=False).head(top_n).reset_index(drop=True)

    rank_style = (
        f"padding:10px 8px;font-family:{FONT_MONO};font-size:11px;"
        f"color:{MUTED};font-weight:600;width:32px;text-align:right;"
    )
    cell_style = "padding:10px 8px;"
    name_style = (
        f"font-family:{FONT_DISPLAY};font-size:13px;"
        f"font-weight:600;color:{INK};line-height:1.25;"
    )
    prov_style = f"font-family:{FONT_BODY};font-size:10.5px;color:{MUTED};"
    fsi_cell_style = (
        f"padding:10px 8px;text-align:right;font-family:{FONT_DISPLAY};"
        f"font-size:14px;font-weight:600;color:{INK};"
    )
    num_cell_style = (
        f"padding:10px 8px;text-align:right;font-family:{FONT_MONO};"
        f"font-size:11px;color:{INK};"
    )
    row_style = f"border-bottom:1px solid {HAIRLINE};"

    rows_html = []
    for i, r in df.iterrows():
        mk_sig = bool(r.get("mk_sig_event_count", False))
        tau = r.get("mk_tau_event")
        mk_chip_html = (
            _mk_up_chip() if (mk_sig and tau is not None and not pd.isna(tau) and tau > 0)
            else _chip(MK_BADGE["no_trend"]["label"],
                       MK_BADGE["no_trend"]["fg"],
                       MK_BADGE["no_trend"]["bg"])
        )
        row_html = (
            f'<tr style="{row_style}">'
            f'<td style="{rank_style}">{i + 1}</td>'
            f'<td style="{cell_style}">'
            f'<div style="{name_style}">{r.get("kemendagri_kab_name", "-")}</div>'
            f'<div style="{prov_style}">{r.get("kemendagri_prov_name", "-")}</div>'
            f'</td>'
            f'<td style="{fsi_cell_style}">{fmt_score(r.get("FSI_percent"), 2)}</td>'
            f'<td style="{cell_style}">{_fsi_tier_chip(r.get("FSI_tier", "-"))}</td>'
            f'<td style="{cell_style}">{_gi_chip(r.get("gi_cat_FSI", "Not significant"))}</td>'
            f'<td style="{cell_style}">{mk_chip_html}</td>'
            f'<td style="{num_cell_style}">{fmt_int(r.get("event_count"))}</td>'
            f'<td style="{num_cell_style}">{fmt_int(r.get("deaths"))}</td>'
            f'</tr>'
        )
        rows_html.append(row_html)

    header_style = (
        f"font-family:{FONT_MONO};font-size:9.5px;font-weight:600;"
        f"letter-spacing:0.10em;text-transform:uppercase;color:{MUTED};"
        f"text-align:left;padding:8px 8px;border-bottom:1px solid {HAIRLINE};"
    )
    header_right_style = header_style + "text-align:right;"
    table_style = (
        f"width:100%;border-collapse:collapse;background:white;"
        f"border:1px solid {HAIRLINE};border-radius:6px;overflow:hidden;"
    )

    # Column header "FSI Score" (was "FSI %") — consistent with score, not percentage
    table_html = (
        f'<table style="{table_style}">'
        f'<thead><tr>'
        f'<th style="{header_right_style}width:32px;">#</th>'
        f'<th style="{header_style}">Regency</th>'
        f'<th style="{header_right_style}">FSI Score</th>'
        f'<th style="{header_style}">Tier</th>'
        f'<th style="{header_style}">Gi*</th>'
        f'<th style="{header_style}">MK</th>'
        f'<th style="{header_right_style}">Events</th>'
        f'<th style="{header_right_style}">Deaths</th>'
        f'</tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        f'</table>'
    )
    st.markdown(table_html, unsafe_allow_html=True)
