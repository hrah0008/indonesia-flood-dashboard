"""
lib/colors.py
=============
Centralised design tokens.

FSI TIER NOTE
-------------
nb6 assigns 4 tiers on the min-max scaled FSI_percent:
    Catastrophic   FSI_percent >= 75
    High           50 <= FSI_percent < 75
    Moderate       25 <= FSI_percent < 50
    Low            FSI_percent < 25
"""

# ── Brand neutrals ────────────────────────────────────────────────────
INK          = "#0f1419"
BODY_TEXT    = "#1f2937"
MUTED        = "#6b7280"
HAIRLINE     = "#e5e7eb"
PAPER        = "#fafaf9"
CARD_BG      = "#ffffff"

# ── Brand colors ──────────────────────────────────────────────────────
INDIGO       = "#1e3a8a"
INDIGO_LIGHT = "#3b82f6"
OCEAN        = "#0c447c"

# ── Semantic colors ───────────────────────────────────────────────────
RED          = "#a32d2d"
RED_BRIGHT   = "#dc2626"
RED_LIGHT    = "#fcebeb"
AMBER        = "#d97706"
AMBER_LIGHT  = "#fff8e1"
GREEN        = "#3b6d11"
GREEN_LIGHT  = "#ecf6e3"
PLUM         = "#6b21a8"
RUST         = "#9a3412"

# ── FSI 4-tier scale (matches nb6) ────────────────────────────────────
FSI_COLORS = {
    "Catastrophic": "#7f1d1d",
    "High":         "#dc2626",
    "Moderate":     "#f59e0b",
    "Low":          "#84cc16",
}

FSI_LABELS = {
    "Catastrophic": "Catastrophic",
    "High":         "High",
    "Moderate":     "Moderate",
    "Low":          "Low",
}

FSI_TIER_ORDER = ["Catastrophic", "High", "Moderate", "Low"]


def fsi_color(tier: str) -> str:
    return FSI_COLORS.get(tier, "#cccccc")


# ── Gi* palette ───────────────────────────────────────────────────────
GI_COLORS = {
    "Hot 99%":         "#7f1d1d",
    "Hot 95%":         "#dc2626",
    "Hot 90%":         "#f59e0b",
    "Not significant": "#d3d1c7",
    "Cold 90%":        "#a8c8e8",
    "Cold 95%":        "#5b9bd5",
    "Cold 99%":        "#0c447c",
}

# ── Mann-Kendall badges ───────────────────────────────────────────────
MK_BADGE = {
    "increasing": {"label": "↑ Worsening",  "fg": "#7f1d1d", "bg": "#fcebeb"},
    "decreasing": {"label": "↓ Improving",  "fg": "#3b6d11", "bg": "#ecf6e3"},
    "no_trend":   {"label": "— No trend",    "fg": "#6b7280", "bg": "#f3f4f6"},
}


# ── Annual time-series line colors ────────────────────────────────────
# Two tiers of series:
#   HEADLINE — the three FSI dimensions + composite, all rescaled to 0-100.
#              This is what the line chart shows by default and tells the
#              "FSI methodology" story (event_index, hci_index, pdi_index,
#              fsi_index).
#   RAW      — original-units counts kept for users who want absolute
#              numbers (events, deaths, houses_flooded, etc).
SERIES_COLORS = {
    # Headline indexed (0-100) series — the FSI building blocks
    "event_index":    "#0c447c",   # deep blue   — frequency
    "hci_index":      "#dc2626",   # red          — human cost
    "pdi_index":      "#f59e0b",   # amber        — property damage
    "fsi_index":      "#0f1419",   # ink          — composite
    # Raw count series — legacy / absolute view
    "events":         "#0c447c",
    "deaths":         "#a32d2d",
    "missing":        "#9a3412",
    "injured":        "#e24b4a",
    "houses_flooded": "#185fa5",
    "houses_damaged": "#6b21a8",
    "fasum_damaged":  "#0e7490",
    "fsi_percent":    "#0f1419",
    "hci_total":      "#dc2626",
    "pdi_total":      "#f59e0b",
}

SERIES_LABELS = {
    # Headline indexed series — the three FSI dimensions + composite
    "event_index":    "Event frequency",
    "hci_index":      "Human Cost Index",
    "pdi_index":      "Property Damage Index",
    "fsi_index":      "FSI Score (composite)",
    # Raw count series
    "events":         "Events (raw)",
    "deaths":         "Deaths",
    "missing":        "Missing",
    "injured":        "Injured",
    "houses_flooded": "Houses flooded",
    "houses_damaged": "Houses damaged",
    "fasum_damaged":  "Public facilities damaged",
    "fsi_percent":    "FSI Score",
    "hci_total":      "HCI total",
    "pdi_total":      "PDI total",
}

# Default series shown when the line chart first loads — the four
# headline indexed series that tell the FSI dimensions story.
SERIES_DEFAULT_HEADLINE = ["event_index", "hci_index", "pdi_index", "fsi_index"]


# ── Typography ────────────────────────────────────────────────────────
FONT_DISPLAY = "Georgia, 'Lora', 'Source Serif Pro', serif"
FONT_BODY    = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
FONT_MONO    = "'JetBrains Mono', 'SF Mono', Menlo, monospace"
