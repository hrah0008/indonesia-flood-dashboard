"""
lib/format.py
=============
Number formatting helpers — keeps the dashboard's voice consistent.
All number-to-string conversions go through these so any change is one-shot.

NOTE on FSI display
-------------------
`fmt_pct` is for genuine percentages (growth rate, poverty rate, etc.)
where the value has a clear denominator. For the FSI it would be
misleading (FSI is a min-max rescaled index, NOT a share of any total) —
use `fmt_score()` instead, which displays "X.XX / 100" to make the
relative-score nature explicit.
"""


def fmt_int(n) -> str:
    """13030 → '13,030'"""
    if n is None:
        return "—"
    try:
        return f"{int(round(float(n))):,}"
    except (ValueError, TypeError):
        return "—"


def fmt_pct(n, decimals: int = 1) -> str:
    """14.7 → '14.7%'

    Use ONLY for genuine percentages (growth, unemployment, share-of-total).
    Do NOT use for the FSI — use fmt_score() instead because FSI has no
    denominator and "%" creates misinterpretation."""
    if n is None:
        return "—"
    try:
        return f"{float(n):.{decimals}f}%"
    except (ValueError, TypeError):
        return "—"


def fmt_score(n, decimals: int = 2) -> str:
    """89.65 → '89.65 / 100'

    For relative index scores (FSI, vulnerability indices, etc.) where the
    0-100 range comes from min-max rescaling rather than a true percentage.
    The "/ 100" suffix makes the relative-score nature explicit and avoids
    the semantic confusion of calling it a percentage."""
    if n is None:
        return "—"
    try:
        return f"{float(n):.{decimals}f} / 100"
    except (ValueError, TypeError):
        return "—"


def fmt_score_only(n, decimals: int = 2) -> str:
    """89.65 → '89.65'  (no '/ 100' suffix)

    For tight contexts (small chips, narrow columns) where the
    "/ 100" implication is already clear from the surrounding text."""
    if n is None:
        return "—"
    try:
        return f"{float(n):.{decimals}f}"
    except (ValueError, TypeError):
        return "—"


def fmt_decimal(n, decimals: int = 3) -> str:
    """0.087 → '0.087'"""
    if n is None:
        return "—"
    try:
        return f"{float(n):.{decimals}f}"
    except (ValueError, TypeError):
        return "—"


def fmt_pvalue(p) -> str:
    """0.0008 → 'p < 0.001'  ·  0.018 → 'p = 0.018'"""
    if p is None:
        return "—"
    try:
        p = float(p)
    except (ValueError, TypeError):
        return "—"
    if p < 0.001:
        return "p < 0.001"
    return f"p = {p:.3f}"


def fmt_sig(p) -> str:
    """Significance star annotation."""
    if p is None:
        return ""
    try:
        p = float(p)
    except (ValueError, TypeError):
        return ""
    if p < 0.001:
        return "★★★"
    if p < 0.01:
        return "★★"
    if p < 0.05:
        return "★"
    return ""


def fmt_compact(n) -> str:
    """1234567 → '1.2M'  ·  13030 → '13.0K'"""
    if n is None:
        return "—"
    try:
        n = float(n)
    except (ValueError, TypeError):
        return "—"
    if abs(n) >= 1e9:
        return f"{n / 1e9:.1f}B"
    if abs(n) >= 1e6:
        return f"{n / 1e6:.1f}M"
    if abs(n) >= 1e3:
        return f"{n / 1e3:.1f}K"
    return f"{n:.0f}"


def fmt_signed_pct(n, decimals: int = 2) -> str:
    """-0.5 → '-0.50%' · 0.8 → '+0.80%'  (used for Theil-Sen slopes).

    Slopes ARE genuine percentages (rate of change per year), so the "%"
    here is semantically correct."""
    if n is None:
        return "—"
    try:
        return f"{float(n):+.{decimals}f}%"
    except (ValueError, TypeError):
        return "—"


def fmt_month(m: int) -> str:
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    try:
        m = int(m)
    except (ValueError, TypeError):
        return "—"
    return months[m - 1] if 1 <= m <= 12 else str(m)
