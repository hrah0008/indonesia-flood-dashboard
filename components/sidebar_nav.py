"""
components/sidebar_nav.py
=========================
Custom sidebar navigation for the FloodX dashboard.
- FloodX brand at top: SVG icon + "FloodX" wordmark on ONE line, both clickable
- Tagline below: plain text, not clickable
- Grouped nav: ANALYSIS / EVIDENCE
- Blue text on active item

ICON SET (curated for research-grade dashboard)
------------------------------------------------
Analysis group — concrete domain icons:
  - Flood            : water_drop      (perfect semantic match)
  - Economic Impact  : account_balance (macroeconomic indicators)
  - Social Impact    : diversity_3     (community / inclusion)
Evidence group — analytical / output icons:
  - Analytical Framework : query_stats (statistical investigation)
  - Predictive Outlook   : insights    (forecasting / foresight)
  - Policy Brief         : fact_check  (evidence-based recommendation)
"""

import streamlit as st
from pathlib import Path

from lib.colors import (
    INK, MUTED, HAIRLINE, INDIGO,
    FONT_DISPLAY, FONT_BODY, FONT_MONO,
)


_BRAND_SVG = (
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
    'stroke-linejoin="round" style="flex-shrink:0;vertical-align:middle;">'
    '<path d="M2 8c2 0 2-1.5 4-1.5S8 8 10 8s2-1.5 4-1.5S16 8 18 8s2-1.5 4-1.5"/>'
    '<path d="M2 13c2 0 2-1.5 4-1.5S8 13 10 13s2-1.5 4-1.5S16 13 18 13s2-1.5 4-1.5"/>'
    '<path d="M2 18c2 0 2-1.5 4-1.5S8 18 10 18s2-1.5 4-1.5S16 18 18 18s2-1.5 4-1.5"/>'
    '</svg>'
)


_NAV_GROUPS = [
    {
        "section": "Analysis",
        "items": [
            # Domain-concrete icons — what the page is about
            {"page": "pages/1_Flood.py",    "label": "Flood",            "icon": ":material/water_drop:"},
            {"page": "pages/2_Economic.py", "label": "Economic Impact",  "icon": ":material/account_balance:"},
            {"page": "pages/3_Social.py",   "label": "Social Impact",    "icon": ":material/diversity_3:"},
        ],
    },
    {
        "section": "Evidence",
        "items": [
            # Analytical / output icons — what the page produces
            {"page": "pages/4_Analytical_Framework.py", "label": "Analytical Framework", "icon": ":material/query_stats:"},
            {"page": "pages/5_Predictive_Outlook.py",   "label": "Predictive Outlook",   "icon": ":material/insights:"},
            {"page": "pages/6_Policy_Brief.py",         "label": "Policy Brief",         "icon": ":material/fact_check:"},
        ],
    },
]


def _inject_css() -> None:
    css = f"""
<style>
/* Belt-and-braces: hide the auto-nav even if config.toml wasn't updated */
[data-testid="stSidebarNav"] {{ display: none !important; }}
[data-testid="stSidebarNavItems"] {{ display: none !important; }}

[data-testid="stSidebar"] {{
    background: #ffffff;
    border-right: 1px solid {HAIRLINE};
}}
[data-testid="stSidebar"] > div:first-child {{ padding-top: 1rem; }}

/* Nav page_links */
[data-testid="stSidebar"] [data-testid="stPageLink"] {{ margin: 1px 0; }}
[data-testid="stSidebar"] [data-testid="stPageLink"] a {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    border-radius: 6px;
    font-family: {FONT_BODY} !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    line-height: 1.2;
    color: {INK} !important;
    text-decoration: none !important;
    transition: color 120ms ease, background 120ms ease;
}}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{
    background: #f5f5f4;
    color: {INK} !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink"] a span[data-testid="stIconMaterial"] {{
    font-size: 18px !important;
    color: inherit !important;
}}

/* ACTIVE — blue text, no background */
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {{
    color: {INDIGO} !important;
    font-weight: 600 !important;
    background: transparent !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"]:hover {{
    background: transparent !important;
    color: {INDIGO} !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"]
    span[data-testid="stIconMaterial"] {{
    color: {INDIGO} !important;
}}

/* === BRAND BLOCK === */
/* The brand row is a single <a> with SVG + text inline. */
.fx-brand-link {{
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    padding: 4px 12px 0 12px !important;
    color: {INK} !important;
    text-decoration: none !important;
    line-height: 1 !important;
    transition: color 120ms ease;
}}
.fx-brand-link:hover {{
    color: {INDIGO} !important;
    text-decoration: none !important;
}}
.fx-brand-link .fx-brand-icon {{
    color: {INDIGO};
    display: inline-flex;
    line-height: 0;
}}
.fx-brand-link .fx-brand-text {{
    font-family: {FONT_DISPLAY};
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.01em;
    line-height: 1;
}}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)


def _render_brand() -> None:
    """SVG icon + 'FloodX' on ONE line, the whole row is one <a> link."""
    # Use a real HTML anchor pointing to the app root. Streamlit treats
    # "/" as the main page (app.py), so this routes correctly without
    # showing the auto-nav.
    st.markdown(
        f'<a href="/" target="_self" class="fx-brand-link">'
        f'<span class="fx-brand-icon">{_BRAND_SVG}</span>'
        f'<span class="fx-brand-text">FloodX</span>'
        f'</a>',
        unsafe_allow_html=True,
    )

    # Tagline — plain text, not clickable
    tagline_style = (
        f"font-family:{FONT_BODY};font-size:11px;color:{MUTED};"
        f"padding:4px 12px 0 12px;line-height:1.45;"
    )
    st.markdown(
        f'<div style="{tagline_style}">'
        f'Indonesia Flood Impact Dashboard &middot; 2016&ndash;2025'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Divider beneath brand
    st.markdown(
        f'<div style="height:1px;background:{HAIRLINE};margin:14px 12px 10px 12px;"></div>',
        unsafe_allow_html=True,
    )


def _render_section_header(text: str) -> None:
    style = (
        f"font-family:{FONT_MONO};font-size:9.5px;font-weight:600;"
        f"letter-spacing:0.14em;text-transform:uppercase;color:{MUTED};"
        f"padding:10px 12px 4px 12px;"
    )
    st.markdown(f'<div style="{style}">{text}</div>', unsafe_allow_html=True)


def _render_disabled_row(item: dict, reason: str = "Soon") -> None:
    row_style = (
        f"display:flex;align-items:center;gap:10px;"
        f"padding:8px 12px;margin:1px 0;border-radius:6px;"
        f"font-family:{FONT_BODY};font-size:13.5px;font-weight:500;"
        f"line-height:1.2;color:{MUTED};opacity:0.55;cursor:not-allowed;"
    )
    icon_placeholder_style = (
        f"display:inline-block;width:18px;height:18px;"
        f"border-radius:50%;border:1.5px dashed {MUTED};flex-shrink:0;"
    )
    badge_style = (
        f"font-family:{FONT_MONO};font-size:8.5px;font-weight:600;"
        f"letter-spacing:0.08em;text-transform:uppercase;color:{MUTED};"
        f"background:#f3f4f6;padding:1px 6px;border-radius:8px;"
        f"margin-left:auto;"
    )
    st.markdown(
        f'<div style="{row_style}">'
        f'<span style="{icon_placeholder_style}"></span>'
        f'<span style="flex:1;">{item["label"]}</span>'
        f'<span style="{badge_style}">{reason}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_sidebar_nav() -> None:
    _inject_css()
    _render_brand()

    project_root = Path(__file__).resolve().parent.parent

    for group in _NAV_GROUPS:
        _render_section_header(group["section"])
        for item in group["items"]:
            page_path = project_root / item["page"]
            if page_path.exists():
                try:
                    st.page_link(item["page"], label=item["label"], icon=item["icon"])
                except Exception:
                    _render_disabled_row(item, reason="(unavailable)")
            else:
                _render_disabled_row(item, reason="Soon")

    # Bottom divider + footer
    st.markdown(
        f'<div style="height:1px;background:{HAIRLINE};margin:14px 12px;"></div>',
        unsafe_allow_html=True,
    )
    footer_style = (
        f"padding:0 12px;font-family:{FONT_MONO};font-size:9.5px;"
        f"color:{MUTED};letter-spacing:0.06em;line-height:1.7;"
    )
    st.markdown(
        f'<div style="{footer_style}">'
        f'BNPB events &middot; 514 regencies<br>'
        f'2016&ndash;2025'
        f'</div>',
        unsafe_allow_html=True,
    )