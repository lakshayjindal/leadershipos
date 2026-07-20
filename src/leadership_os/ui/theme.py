"""Theme — custom color palette, typography, and design tokens for Leadership OS.

Design philosophy (inspired by DESIGN.md Notion analysis):
- Calm, minimal, professional — a dark, warm canvas rather than clinical black
- Near-white type on deep background for high contrast without harshness
- Single structural accent (calm blue) reserved for CTAs and active states
- Multi-color sticker palette for priority/task categorization (decoration only)
- Hairline borders and barely-there elevation instead of heavy shadows
- Generous 8px-based spacing with tight border radii

Supports dark theme (default).
"""

from __future__ import annotations

from typing import ClassVar

# ─── Dark Theme Colors ────────────────────────────────────────────────

DARK = {
    "background": "#1A1A2E",       # Deep dark background (warm dark)
    "surface": "#232340",          # Card/panel surface
    "surface_light": "#2D2D50",    # Elevated surface
    "surface_hover": "#33335a",    # Hover state
    "border": "#3A3A5C",           # Subtle borders / hairlines
    "border_focus": "#4A6FA5",     # Focus border

    # Text
    "text_primary": "#E8E8F0",     # Primary text — high contrast
    "text_secondary": "#9898B8",   # Secondary text — muted
    "text_muted": "#6868A0",       # Muted text — metadata
    "text_disabled": "#4a4a78",    # Disabled text

    # Priority colors
    "priority_critical": "#E05555",
    "priority_high": "#E0A055",
    "priority_medium": "#E0D055",
    "priority_low": "#9898B8",

    # Accent sticker palette (decorative)
    "accent_sky": "#62aef0",
    "accent_purple": "#b388d6",
    "accent_pink": "#ff80ab",
    "accent_orange": "#ffab40",
    "accent_teal": "#4db6ac",
    "accent_green": "#81c784",
    
    # Primary
    "primary": "#4A6FA5",          # Calm blue — current task, active states
    "primary_light": "#6B8FC5",    # Lighter blue — hover states
    "primary_dark": "#3A5A8A",     # Darker blue — pressed states
    "success": "#5B9A6B",          # Muted green — completed
    "warning": "#C4A35A",          # Warm amber — approaching deadlines
    "error": "#C45B5B",            # Soft red — overdue, errors
}

# ─── Typography Scale ─────────────────────────────────────────────────

TYPOGRAPHY: dict[str, tuple[int, str, float]] = {
    "display_1":     (36, "700", -0.5),    # Hero timer display
    "display_2":     (28, "700", -0.25),   # Large numbers (timer)
    "h1":            (20, "700", 0),        # Page title (Application Title)
    "h2":            (18, "600", 0),        # Section title
    "h3":            (16, "600", 0),        # Card title
    "h4":            (14, "500", 0),        # Task title
    "body":          (13, "400", 0),        # Body text
    "body_small":    (12, "400", 0),        # Secondary text
    "caption":       (11, "300", 0),        # Metadata
    "button":        (13, "500", 0),        # Button label
    "eyebrow":       (10, "600", 0.5),      # Small labels / badges
    "timer":         (36, "700", -0.5),     # Timer display (mono)
    "timer_small":   (24, "700", -0.25),    # Small timer
}

# ─── Spacing Tokens ───────────────────────────────────────────────────

SPACING: dict[str, int] = {
    "xxs":  2,
    "xs":   4,
    "sm":   8,
    "md":   12,
    "lg":   16,
    "xl":   24,
    "xxl":  32,
    "xxxl": 48,
}

# ─── Border Radius Tokens ─────────────────────────────────────────────

RADIUS: dict[str, int] = {
    "xs":    2,
    "sm":    4,
    "md":    6,
    "lg":    8,
    "xl":    12,
    "pill":  9999,
}

# ─── Component Heights ────────────────────────────────────────────────

HEIGHTS: dict[str, int] = {
    "top_bar":      48,
    "status_bar":   28,
    "sidebar_item": 40,
    "task_card":    56,
    "button":       36,
    "button_small": 28,
    "input":        36,
    "divider":      1,
}


# ─── Theme Helper ─────────────────────────────────────────────────────


class Theme:
    """Theme constants and helpers for Leadership OS.

    Provides hex color values, spacing tokens, and typography settings
    that can be used from Python code. KV files use direct hex values.
    """

    dark: ClassVar[dict[str, str]] = DARK
    typography: ClassVar[dict[str, tuple[int, str, float]]] = TYPOGRAPHY
    spacing: ClassVar[dict[str, int]] = SPACING
    radius: ClassVar[dict[str, int]] = RADIUS
    heights: ClassVar[dict[str, int]] = HEIGHTS

    @classmethod
    def color(cls, name: str) -> str:
        """Get a color value by name."""
        return cls.dark.get(name, "#000000")

    @classmethod
    def text(cls, name: str) -> str:
        """Get a text color by name."""
        return cls.color(f"text_{name}")

    @classmethod
    def priority(cls, level: str) -> str:
        """Get the RGBA hex color for a priority level."""
        return cls.dark.get(f"priority_{level}", cls.dark["text_secondary"])

    @classmethod
    def to_rgba(cls, hex_color: str) -> tuple[float, float, float, float]:
        """Convert a hex color string to an RGBA tuple (0.0-1.0)."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            hex_color = f"{hex_color}ff"
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        a = int(hex_color[6:8], 16) / 255.0
        return (r, g, b, a)

    @classmethod
    def apply_to_app(cls, app) -> None:
        """Apply the Leadership OS theme to a KivyMD MDApp instance.

        Sets up theme_style and primary palette on app.theme_cls.
        Call during app build().
        """
        theme_cls = app.theme_cls
        theme_cls.primary_palette = "Indigo"
        theme_cls.theme_style = "Dark"


# Module-level convenience instance
theme = Theme()
