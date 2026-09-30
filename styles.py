"""
Design tokens for the widget's iOS-inspired look.

The whole point of the card is that its background *is* the weather
report: the gradient and icon tint change with the condition and the
time of day rather than staying a fixed decorative color. Everything
below is deliberately centralized so the palette can be re-tuned in one
place.
"""
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QLinearGradient, QFontDatabase, QFont

# ---------------------------------------------------------------------------
# Color tokens
# ---------------------------------------------------------------------------
TEXT_PRIMARY = "#F5F7FA"
TEXT_SECONDARY = "rgba(245, 247, 250, 0.78)"
TEXT_TERTIARY = "rgba(245, 247, 250, 0.55)"

# top / bottom stops for each "<condition>_<day|night>" gradient
PALETTES = {
    "clear_day":   ("#55ACEC", "#1C5FA8"),
    "clear_night": ("#1B2340", "#05070E"),
    "cloud_day":   ("#8CA3C2", "#4E617C"),
    "cloud_night": ("#3A4258", "#14171F"),
    "rain_day":    ("#5B7C9B", "#2B3E52"),
    "rain_night":  ("#2E3D52", "#12181F"),
    "snow_day":    ("#C3D3E4", "#8598AE"),
    "snow_night":  ("#47536A", "#1C222E"),
    "storm_day":   ("#544B78", "#211D33"),
    "storm_night": ("#322C4A", "#111022"),
    "fog_day":     ("#A9B4BE", "#717C87"),
    "fog_night":   ("#3C424B", "#1A1D22"),
}
DEFAULT_PALETTE = ("#4E617C", "#232C38")

# Icon tint per weather family (independent of day/night so a sun always
# reads as gold, rain always reads as pale blue, etc.)
ICON_COLORS = {
    "clear": "#FFC759",
    "cloud": "#F0F3F7",
    "rain":  "#9AD1FF",
    "snow":  "#FFFFFF",
    "storm": "#FFD766",
    "fog":   "#E7ECF1",
}
DEFAULT_ICON_COLOR = "#F0F3F7"

# ---------------------------------------------------------------------------
# Typography — Segoe UI Variable ships with Windows 11, Segoe UI with
# Windows 10; both are close in spirit to iOS's SF Pro (humanist,
# geometric, tall x-height) without bundling a font we're not licensed
# to redistribute.
# ---------------------------------------------------------------------------
def pick_font_family() -> str:
    families = set(QFontDatabase.families())
    for candidate in ("Segoe UI Variable Display", "Segoe UI Variable", "Segoe UI"):
        if candidate in families:
            return candidate
    return QFont().defaultFamily()


def make_gradient(width: int, height: int, palette_key: str) -> QLinearGradient:
    top_hex, bottom_hex = PALETTES.get(palette_key, DEFAULT_PALETTE)
    gradient = QLinearGradient(QPointF(0, 0), QPointF(width * 0.25, height))
    gradient.setColorAt(0.0, QColor(top_hex))
    gradient.setColorAt(1.0, QColor(bottom_hex))
    return gradient


def icon_color_for(icon_color_key: str) -> str:
    return ICON_COLORS.get(icon_color_key, DEFAULT_ICON_COLOR)


def label_qss(size: int, weight: int = QFont.Normal, color: str = TEXT_PRIMARY, spacing: float = None) -> str:
    """Small helper so widget code stays declarative."""
    css_weight = {
        QFont.Thin: 100, QFont.Light: 300, QFont.Normal: 400,
        QFont.DemiBold: 600, QFont.Bold: 700,
    }.get(weight, 400)
    letter_spacing = f"letter-spacing: {spacing}px;" if spacing is not None else ""
    return (
        "background: transparent; border: none; "
        f"color: {color}; font-size: {size}px; font-weight: {css_weight}; {letter_spacing}"
    )
