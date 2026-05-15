"""
components/section_header.py
============================
Typographic header used above charts and at the top of pages.
All inline `style` attributes are SINGLE-LINE to prevent Streamlit
from treating multi-line HTML as a code block.
"""

import streamlit as st

from lib.colors import INK, MUTED, FONT_DISPLAY, FONT_MONO


def render_section_header(
    kicker: str,
    title: str,
    description: str = "",
    title_size_px: int = 18,
) -> None:
    kicker_style = (
        f"font-family:{FONT_MONO};font-size:10px;font-weight:600;"
        f"letter-spacing:0.10em;text-transform:uppercase;color:{MUTED};"
    )
    title_style = (
        f"font-family:{FONT_DISPLAY};font-size:{title_size_px}px;"
        f"font-weight:600;color:{INK};margin:2px 0 0 0;line-height:1.25;"
    )
    desc_style = (
        f"font-size:12.5px;color:{MUTED};line-height:1.5;"
        f"max-width:860px;margin-top:2px;"
    )
    wrap_style = "margin:4px 0 12px 0;"

    desc_html = (
        f'<div style="{desc_style}">{description}</div>' if description else ""
    )

    html = (
        f'<div style="{wrap_style}">'
        f'<div style="{kicker_style}">{kicker}</div>'
        f'<h3 style="{title_style}">{title}</h3>'
        f'{desc_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_page_header(menu_label: str, title: str, description: str) -> None:
    kicker_style = (
        f"font-family:{FONT_MONO};font-size:10.5px;font-weight:600;"
        f"letter-spacing:0.12em;text-transform:uppercase;color:{MUTED};"
    )
    title_style = (
        f"font-family:{FONT_DISPLAY};font-size:30px;font-weight:600;"
        f"color:{INK};margin:4px 0 6px 0;line-height:1.2;"
    )
    desc_style = (
        f"font-size:13px;color:{MUTED};max-width:860px;line-height:1.55;"
    )
    html = (
        f'<div style="margin-bottom:16px;">'
        f'<div style="{kicker_style}">Menu &mdash; {menu_label}</div>'
        f'<h1 style="{title_style}">{title}</h1>'
        f'<div style="{desc_style}">{description}</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
