"""Theme — custom color palette, typography, and design tokens for Leadership OS.

Design philosophy:
- Calm, minimal, professional — a dark, warm canvas rather than clinical black
- Near-white type on deep background for high contrast without harshness
- Single structural accent (calm blue) reserved for CTAs and active states
- Multi-color priority palette for task categorization (decoration only)
- Hairline borders and barely-there elevation instead of heavy shadows
- Generous spacing with tight border radii

Supports dark theme (default).
"""

from __future__ import annotations

from typing import ClassVar

import flet as ft

# ─── Dark Theme Colors ────────────────────────────────────────────────

DARK = {
    "background": "#0D0D1A",       # Deepest dark background
    "surface": "#14142A",          # Card/panel surface
    "surface_light": "#1A1A36",    # Elevated surface
    "surface_hover": "#202042",    # Hover state
    "border": "#2D2D4A",           # Subtle borders / hairlines
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
    "priority_low": "#6868A0",

    # Accent sticker palette (decorative)
    "accent_sky": "#62aef0",
    "accent_purple": "#b388d6",
    "accent_pink": "#ff80ab",
    "accent_orange": "#ffab40",
    "accent_teal": "#4db6ac",
    "accent_green": "#81c784",

    # Semantic
    "primary": "#4A6FA5",          # Calm blue — current task, active states
    "primary_light": "#6B8FC5",    # Lighter blue — hover states
    "primary_dark": "#3A5A8A",     # Darker blue — pressed states
    "success": "#5B9A6B",          # Muted green — completed
    "warning": "#C4A35A",          # Warm amber — approaching deadlines
    "error": "#C45B5B",            # Soft red — overdue, errors

    # UI element colors (as flet-compatible rgba tuples 0-1)
    "bg_main": (0.051, 0.051, 0.102, 1),       # #0D0D1A
    "bg_surface": (0.078, 0.078, 0.141, 1),     # #14142A
    "bg_card": (0.094, 0.094, 0.165, 1),         # #181830
    "bg_card_alt": (0.082, 0.082, 0.149, 1),     # #15152B
    "bg_input": (0.102, 0.102, 0.18, 1),          # #1A1A2E
    "accent_blue": (0.29, 0.435, 0.647, 1),       # #4A6FA5
    "accent_green": (0.4, 0.65, 0.45, 1),         # #66A66B
    "accent_red": (0.769, 0.357, 0.357, 1),       # #C45B5B
    "text_white": (0.91, 0.91, 0.94, 1),          # #E8E8F0
    "text_dim": (0.455, 0.455, 0.6, 1),           # #747496
    "text_muted_dim": (0.353, 0.353, 0.502, 1),   # #5A5A80
}

# ─── Spacing Tokens ───────────────────────────────────────────────────

SPACING: dict[str, int] = {
    "xxs": 2,
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32,
    "xxxl": 48,
}

# ─── Border Radius Tokens ─────────────────────────────────────────────

RADIUS: dict[str, int] = {
    "xs": 2,
    "sm": 4,
    "md": 6,
    "lg": 8,
    "xl": 12,
    "pill": 9999,
}

# ─── Component Heights ────────────────────────────────────────────────

HEIGHTS: dict[str, int] = {
    "top_bar": 48,
    "status_bar": 22,
    "sidebar_item": 34,
    "task_card": 48,
    "button": 36,
    "button_small": 28,
    "input": 36,
    "divider": 1,
}

# ─── Priority styling helpers ─────────────────────────────────────────

PRIORITY_LABELS = {
    "critical": "CRITICAL",
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
}

PRIORITY_RGBA = {
    "critical": (0.878, 0.333, 0.333, 1),
    "high": (0.878, 0.627, 0.333, 1),
    "medium": (0.878, 0.816, 0.333, 1),
    "low": (0.408, 0.408, 0.627, 1),
}


# ─── Flet Theme Builder ───────────────────────────────────────────────


def build_flet_theme() -> ft.Theme:
    """Build a Flet Theme matching the Leadership OS dark palette.

    Compatible with Flet 0.86+ — uses ft.Colors (uppercase) and avoids
    removed parameters like Theme.brightness and ColorScheme.background.
    Dark/light mode is handled via page.theme_mode in app.py.
    """
    return ft.Theme(
        color_scheme_seed=ft.Colors.INDIGO,
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.INDIGO_400,
            on_primary=ft.Colors.WHITE,
            secondary=ft.Colors.PURPLE_300,
            surface="#14142A",
            on_surface="#E0E0E0",
            error=ft.Colors.RED_300,
            surface_tint=ft.Colors.INDIGO_400,
        ),
        text_theme=ft.TextTheme(
            headline_large=ft.TextStyle(
                font_family="Roboto Mono",
                size=72,
                weight=ft.FontWeight.W_700,
                color=ft.Colors.INDIGO_400,
            ),
            headline_medium=ft.TextStyle(
                size=18,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.GREY_200,
            ),
            title_medium=ft.TextStyle(
                size=15,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.GREY_200,
            ),
            title_small=ft.TextStyle(
                size=13,
                weight=ft.FontWeight.W_500,
                color=ft.Colors.GREY_200,
            ),
            body_medium=ft.TextStyle(
                size=13,
                color=ft.Colors.GREY_300,
            ),
            body_small=ft.TextStyle(
                size=11,
                color=ft.Colors.GREY_400,
            ),
            label_large=ft.TextStyle(
                size=14,
                weight=ft.FontWeight.W_500,
            ),
            label_medium=ft.TextStyle(
                size=12,
                weight=ft.FontWeight.W_500,
            ),
            label_small=ft.TextStyle(
                size=10,
                weight=ft.FontWeight.W_400,
                color=ft.Colors.GREY_500,
            ),
        ),
        scrollbar_theme=ft.ScrollbarTheme(
            thickness=2,
        ),
    )


def hex_to_flet(hex_color: str) -> str:
    """Pass through hex color string for Flet (Flet accepts hex strings)."""
    return hex_color


def rgba_to_hex(r: float, g: float, b: float, a: float = 1.0) -> str:
    """Convert RGBA 0-1 float tuple to hex string for Flet."""
    r_int = int(r * 255)
    g_int = int(g * 255)
    b_int = int(b * 255)
    a_int = int(a * 255)
    if a_int < 255:
        return f"#{r_int:02x}{g_int:02x}{b_int:02x}{a_int:02x}"
    return f"#{r_int:02x}{g_int:02x}{b_int:02x}"


def rgba_str(r: float, g: float, b: float, a: float = 1.0) -> str:
    """Convert RGBA 0-1 float tuple to flet-compatible hex string."""
    return rgba_to_hex(r, g, b, a)


# ─── Theme Constants ──────────────────────────────────────────────────


class Theme:
    """Theme constants and helpers for Leadership OS."""

    dark: ClassVar[dict[str, str]] = DARK
    spacing: ClassVar[dict[str, int]] = SPACING
    radius: ClassVar[dict[str, int]] = RADIUS
    heights: ClassVar[dict[str, int]] = HEIGHTS
    priority_labels: ClassVar[dict[str, str]] = PRIORITY_LABELS
    priority_rgba: ClassVar[dict[str, tuple]] = PRIORITY_RGBA

    @classmethod
    def color(cls, name: str) -> str:
        """Get a color hex value by name."""
        return cls.dark.get(name, "#000000")

    @classmethod
    def text(cls, name: str) -> str:
        """Get a text color by name."""
        return cls.color(f"text_{name}")

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
    def to_flet_color(cls, hex_color: str) -> str:
        """Convert dark theme hex to flet color string, preserving alpha if present."""
        if len(hex_color) == 9 and hex_color[0] == "#":
            return hex_color
        if len(hex_color) == 7 and hex_color[0] == "#":
            return hex_color
        # Already a named flet color
        return hex_color

    @classmethod
    def focus_rgba_str(cls) -> str:
        """Get focus/primary accent as hex string for Flet."""
        return "#4A6FA5"

    @classmethod
    def success_rgba_str(cls) -> str:
        """Get success green as hex string for Flet."""
        return "#66A66B"

    @classmethod
    def error_rgba_str(cls) -> str:
        """Get error red as hex string for Flet."""
        return "#C45B5B"

    @classmethod
    def text_primary_str(cls) -> str:
        return "#E8E8F0"

    @classmethod
    def text_secondary_str(cls) -> str:
        return "#9898B8"

    @classmethod
    def text_dim_str(cls) -> str:
        return "#747496"

    @classmethod
    def text_muted_str(cls) -> str:
        return "#5A5A80"

    @classmethod
    def surface_str(cls) -> str:
        return "#14142A"

    @classmethod
    def card_str(cls) -> str:
        return "#181830"

    @classmethod
    def card_alt_str(cls) -> str:
        return "#15152B"

    @classmethod
    def bg_str(cls) -> str:
        return "#0D0D1A"


# Module-level convenience instance
theme = Theme()
