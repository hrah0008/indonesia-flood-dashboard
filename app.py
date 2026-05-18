"""
app.py
======
Landing page for the Indonesia Flood Dashboard (Streamlit Multi-Page App).

Streamlit auto-discovers files in pages/ and adds them to the sidebar
in numeric-prefix order. This file (app.py) is the home page.

NOTE on HTML
------------
All inline style attributes are written on a SINGLE LINE. Streamlit's
markdown renderer treats multi-line indented HTML as a code block, which
leaks raw fragments like '">' into the rendered output.
"""

import streamlit as st

from lib.colors import (
    INK, MUTED, HAIRLINE, PAPER, INDIGO, OCEAN, GREEN,
    FONT_DISPLAY, FONT_BODY, FONT_MONO,
)
from components.sidebar_nav import render_sidebar_nav


st.set_page_config(
    page_title="FloodX — Indonesia Flood and Socioeconomic Impact Dashboard",
    page_icon=":droplet:",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────────────────────────────
# Global CSS — only place where multi-line CSS is fine because it lives
# inside <style> tags, not in inline attributes.
# ─────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] {{ font-family: {FONT_BODY}; color: {INK}; }}
.main {{ background: {PAPER}; }}
h1, h2, h3, h4 {{ font-family: {FONT_DISPLAY}; }}
[data-testid="stSidebar"] {{ background: #ffffff; border-right: 1px solid {HAIRLINE}; }}
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {{
    font-family: {FONT_BODY}; font-size: 13px;
}}
footer {{ visibility: hidden; }}
#MainMenu {{ visibility: hidden; }}
.block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1400px; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {HAIRLINE}; }}
.stTabs [data-baseweb="tab"] {{
    font-family: {FONT_MONO}; font-size: 11px; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase;
    color: {MUTED}; padding: 8px 16px;
}}
.stTabs [aria-selected="true"] {{ color: {INK}; border-bottom: 2px solid {INDIGO}; }}
.stCheckbox label {{ font-family: {FONT_BODY}; font-size: 12px; color: {INK}; }}
</style>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────
# Sidebar — brand + custom nav (FloodX, blue when active)
# ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar_nav()


# ─────────────────────────────────────────────────────────────────────
# Landing — hero
# ─────────────────────────────────────────────────────────────────────
hero_kicker = (
    f"font-family:{FONT_MONO};font-size:11px;font-weight:600;"
    f"letter-spacing:0.14em;text-transform:uppercase;color:{MUTED};"
    f"margin-bottom:8px;"
)
hero_title = (
    f"font-family:{FONT_DISPLAY};font-size:40px;font-weight:600;"
    f"color:{INK};margin:0;line-height:1.15;letter-spacing:-0.01em;"
)
hero_desc = (
    f"font-size:16px;color:{MUTED};margin-top:12px;"
    f"max-width:780px;line-height:1.6;"
)
st.markdown(
    f'<div style="margin:8px 0 24px 0;">'
    f'<div style="{hero_kicker}">Indonesia &middot; 2016&ndash;2025</div>'
    f'<h1 style="{hero_title}">Regional Socioeconomic Impacts of Flooding in Indonesia: A Spatiotemporal Analysis Using Administrative Disaster Records, 2016–2025.</h1>'
    f'<div style="{hero_desc}">A spatial and temporal analysis of Indonesia’s flood exposure, highlighting '
    f'where flooding impacts are most severe and how these patterns evolve over time. '
    f'Insights are presented at the national, provincial, and regency levels using '
    f'BNPB disaster records.'
    f'</div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────
# Menu cards
# ─────────────────────────────────────────────────────────────────────
def _menu_card(kicker: str, title: str, body: str, status: str = "live") -> str:
    if status == "live":
        chip_label, chip_fg, chip_bg = "Available now", GREEN, "#ecf6e3"
    else:
        chip_label, chip_fg, chip_bg = "Coming soon", OCEAN, "#e0e7ff"

    chip_style = (
        f"display:inline-block;padding:2px 8px;border-radius:10px;"
        f"font-family:{FONT_MONO};font-size:9.5px;font-weight:600;"
        f"letter-spacing:0.08em;text-transform:uppercase;"
        f"color:{chip_fg};background:{chip_bg};"
    )
    card_style = (
        f"background:#ffffff;border:1px solid {HAIRLINE};"
        f"border-radius:8px;padding:18px 20px;height:100%;"
    )
    head_style = (
        f"display:flex;justify-content:space-between;align-items:flex-start;"
        f"margin-bottom:8px;"
    )
    kicker_style = (
        f"font-family:{FONT_MONO};font-size:9.5px;font-weight:600;"
        f"letter-spacing:0.10em;text-transform:uppercase;color:{MUTED};"
    )
    title_style = (
        f"font-family:{FONT_DISPLAY};font-size:18px;font-weight:600;"
        f"color:{INK};margin:4px 0 8px 0;line-height:1.25;"
    )
    body_style = f"font-size:12.5px;color:{MUTED};line-height:1.6;"

    return (
        f'<div style="{card_style}">'
        f'<div style="{head_style}">'
        f'<div style="{kicker_style}">{kicker}</div>'
        f'<span style="{chip_style}">{chip_label}</span>'
        f'</div>'
        f'<div style="{title_style}">{title}</div>'
        f'<div style="{body_style}">{body}</div>'
        f'</div>'
    )


menu_kicker = (
    f"font-family:{FONT_MONO};font-size:10px;font-weight:600;"
    f"letter-spacing:0.12em;text-transform:uppercase;color:{MUTED};margin-top:24px;"
)
menu_title = (
    f"font-family:{FONT_DISPLAY};font-size:22px;font-weight:600;"
    f"color:{INK};margin:4px 0 16px 0;"
)


# Footer
footer_style = (
    f"margin-top:48px;padding-top:16px;border-top:1px solid {HAIRLINE};"
    f"font-family:{FONT_MONO};font-size:10px;color:{MUTED};letter-spacing:0.08em;"
)
st.markdown(
    f'<div style="{footer_style}">Data sources &middot; BNPB DIBI &middot; '
    f'BPS Statistics Indonesia</div>',
    unsafe_allow_html=True,
)
