"""
components/kpi_strip.py
=======================
Renders a row of KPI cards. Each card has:
  - small uppercase label (JetBrains Mono)
  - prominent value (serif)
  - optional sublabel (smaller, muted)
  - optional `highlight=True` flag -> indigo accent bar on the left edge

IMPORTANT - formatting rule
---------------------------
Streamlit's markdown renderer treats multi-line indented HTML inside
st.markdown() as a code block, which causes raw HTML fragments like '">'
to leak into the rendered output. To prevent this, ALL inline `style`
attributes here are written on a SINGLE LINE.
"""

from typing import Iterable, Mapping

import streamlit as st

from lib.colors import (
    INK, MUTED, HAIRLINE, CARD_BG, INDIGO,
    FONT_DISPLAY, FONT_MONO,
)


def render_kpi_strip(items: Iterable[Mapping]) -> None:
    items = list(items)
    if not items:
        return
    cols = st.columns(len(items), gap="small")
    for col, item in zip(cols, items):
        with col:
            _render_card(item)


def _render_card(item: Mapping) -> None:
    label     = item.get("label", "")
    value     = item.get("value", "-")
    sublabel  = item.get("sublabel", "")
    highlight = item.get("highlight", False)
    tone      = item.get("tone", None)

    accent_bar = f"box-shadow:inset 3px 0 0 0 {INDIGO};" if highlight else ""

    tone_color = {
        "red":   "#a32d2d",
        "green": "#3b6d11",
        "amber": "#d97706",
    }.get(tone, INK)

    card_style = (
        f"background:{CARD_BG};border:1px solid {HAIRLINE};"
        f"border-radius:6px;padding:14px 16px;min-height:96px;{accent_bar}"
    )
    label_style = (
        f"font-family:{FONT_MONO};font-size:9.5px;font-weight:600;"
        f"letter-spacing:0.10em;text-transform:uppercase;color:{MUTED};"
        f"margin-bottom:6px;"
    )
    value_style = (
        f"font-family:{FONT_DISPLAY};font-size:24px;font-weight:600;"
        f"color:{tone_color};line-height:1.1;"
    )
    sublabel_style = (
        f"font-family:{FONT_MONO};font-size:10px;color:{MUTED};"
        f"letter-spacing:0.04em;margin-top:4px;"
    )

    sublabel_html = (
        f'<div style="{sublabel_style}">{sublabel}</div>' if sublabel else ""
    )

    html = (
        f'<div style="{card_style}">'
        f'<div style="{label_style}">{label}</div>'
        f'<div style="{value_style}">{value}</div>'
        f'{sublabel_html}'
        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)
