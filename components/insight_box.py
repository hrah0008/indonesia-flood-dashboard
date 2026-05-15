"""
components/insight_box.py
=========================
Bordered panel for the page's "synthesis" section.
All inline `style` attributes are SINGLE-LINE.
"""

from typing import Iterable, Optional

import streamlit as st

from lib.colors import (
    INK, MUTED, HAIRLINE, INDIGO, AMBER, GREEN, CARD_BG,
    FONT_DISPLAY, FONT_BODY, FONT_MONO,
)


_VARIANT_BORDERS = {
    "info":    INDIGO,
    "warning": AMBER,
    "success": GREEN,
}


def render_insight_box(
    bullets: Iterable[str],
    title: Optional[str] = None,
    kicker: str = "Statistical evidence",
    variant: str = "info",
) -> None:
    bullets = [b for b in bullets if b]
    if not bullets:
        return

    border_color = _VARIANT_BORDERS.get(variant, INDIGO)

    box_style = (
        f"background:{CARD_BG};border:1px solid {HAIRLINE};"
        f"border-left:3px solid {border_color};border-radius:6px;"
        f"padding:14px 16px;"
    )
    kicker_style = (
        f"font-family:{FONT_MONO};font-size:9.5px;font-weight:600;"
        f"letter-spacing:0.10em;text-transform:uppercase;color:{MUTED};"
        f"margin-bottom:4px;"
    )
    title_style = (
        f"font-family:{FONT_DISPLAY};font-size:15px;font-weight:600;"
        f"color:{INK};margin:0 0 10px 0;"
    )
    li_style = (
        f"font-family:{FONT_BODY};font-size:12.5px;color:{INK};"
        f"line-height:1.65;margin-bottom:8px;"
    )
    ul_style = "padding-left:18px;margin:0;"

    items_html = "".join(
        f'<li style="{li_style}">{b}</li>' for b in bullets
    )
    title_html = (
        f'<h4 style="{title_style}">{title}</h4>' if title else ""
    )
    kicker_html = (
        f'<div style="{kicker_style}">{kicker}</div>' if kicker else ""
    )

    html = (
        f'<div style="{box_style}">'
        f'{kicker_html}'
        f'{title_html}'
        f'<ul style="{ul_style}">{items_html}</ul>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
