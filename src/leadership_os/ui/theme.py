"""Theme — Apple-style light design tokens for Leadership OS.

Design language (see DESIGN.md):
- Light, museum-gallery aesthetic: white / parchment surfaces, pure-black
  global nav, and a single Action Blue (#0066cc) for every interactive element.
- No decorative gradients or shadows on chrome. The color change between
  light and dark tiles IS the divider.
- Typography: SF Pro Display / SF Pro Text with system-ui fallback
  (Inter is the closest open-source substitute). Body copy at 17px,
  weight ladder 300 / 400 / 600 / 700 (500 is deliberately absent).
- Radii: sm 8px for compact utility, lg 18px for utility cards, pill for
  CTAs and search inputs. Nothing in between except the rare md 11px.
- Buttons press with transform scale(0.95) — the system micro-interaction.
"""

from __future__ import annotations

from typing import ClassVar

import flet as ft

# ─── Apple-style Light Palette ────────────────────────────────────────

# Canonical tokens from DESIGN.md
CANVAS = "#ffffff"              # Pure white canvas
PARCHMENT = "#f5f5f7"           # Apple signature off-white
PEARL = "#fafafc"               # Near-white secondary button fill
INK = "#1d1d1f"                 # Near-black ink — all text on light surfaces
INK_MUTED_80 = "#333333"        # Body on pearl buttons
INK_MUTED_48 = "#7a7a7a"        # Disabled text / fine print
BODY_MUTED = "#cccccc"          # Secondary copy on dark surfaces
HAIRLINE = "#e0e0e0"            # 1px card / utility borders
DIVIDER_SOFT = "#f0f0f0"        # Soft ring / divider tone
PRIMARY = "#0066cc"             # Action Blue — THE interactive color
PRIMARY_FOCUS = "#0071e3"       # Focus ring blue
PRIMARY_ON_DARK = "#2997ff"     # Sky Link Blue — links on dark tiles
ON_PRIMARY = "#ffffff"          # Text on Action Blue
ON_DARK = "#ffffff"             # Text on dark tiles
BLACK = "#000000"               # Global nav / true void
TILE_1 = "#272729"              # Primary dark tile
TILE_2 = "#2a2a2c"              # Micro-step lighter dark tile
TILE_3 = "#252527"              # Micro-step darker dark tile
CHIP = "#d2d2d7"                # Translucent gray chip

# Semantic (light-surface tuned)
SUCCESS = "#34c759"             # Apple green
WARNING = "#ff9500"             # Apple orange
ERROR = "#ff3b30"               # Apple red

# Translucent tints (light-surface tuned, for chips/tints on light bg)
TINT_ERROR = "#ff3b301f"        # Red tint — Quit button, destructive chips
TINT_PRIMARY = "#0066cc14"      # Blue tint — selected chips, ghost actions

# Secondary grays (Apple label hierarchy)
GRAY_1 = "#1d1d1f"              # Primary label = ink
GRAY_2 = "#6e6e73"              # Secondary label
GRAY_3 = "#86868b"              # Tertiary label
GRAY_4 = "#aeaeb2"              # Quaternary label
GRAY_5 = "#d1d1d6"              # Quaternary faint / placeholder

# ─── Compat palette (old keys → light values) ─────────────────────────
# The key names are preserved so existing `Theme.color("background")`
# style lookups keep working; values now follow the Apple light system.

LIGHT = {
    "background": PARCHMENT,            # App canvas — parchment
    "surface": CANVAS,                  # Card / panel surface — white
    "surface_light": PEARL,             # Elevated surface — pearl
    "surface_hover": DIVIDER_SOFT,      # Hover state
    "border": HAIRLINE,                 # Hairline borders
    "border_focus": PRIMARY_FOCUS,      # Focus border

    # Text
    "text_primary": INK,                # Primary text — near-black
    "text_secondary": GRAY_2,           # Secondary text
    "text_muted": GRAY_3,               # Muted text — metadata
    "text_disabled": GRAY_4,            # Disabled text

    # Priority colors (task categorization — decoration only)
    "priority_critical": "#ff3b30",
    "priority_high": "#ff9500",
    "priority_medium": "#ffcc00",
    "priority_low": GRAY_3,

    # Accent sticker palette (decorative)
    "accent_sky": "#2997ff",
    "accent_purple": "#af52de",
    "accent_pink": "#ff2d55",
    "accent_orange": "#ff9500",
    "accent_teal": "#30b0c7",

    # Semantic
    "primary": PRIMARY,                 # Action Blue — the single accent
    "primary_light": PRIMARY_FOCUS,     # Lighter blue — hover/focus
    "primary_dark": "#0055b3",          # Darker blue — pressed states
    "success": SUCCESS,
    "warning": WARNING,
    "error": ERROR,

    # UI element colors (as flet-compatible rgba tuples 0-1)
    "bg_main": (0.961, 0.961, 0.969, 1),        # #f5f5f7 parchment
    "bg_surface": (1.0, 1.0, 1.0, 1),           # #ffffff
    "bg_card": (1.0, 1.0, 1.0, 1),              # #ffffff
    "bg_card_alt": (0.980, 0.980, 0.988, 1),    # #fafafc pearl
    "bg_input": (1.0, 1.0, 1.0, 1),             # #ffffff
    "accent_blue": (0.0, 0.4, 0.8, 1),          # #0066cc
    "accent_green": (0.204, 0.780, 0.349, 1),   # #34c759
    "accent_red": (1.0, 0.231, 0.188, 1),       # #ff3b30
    "text_white": (0.114, 0.114, 0.122, 1),     # #1d1d1f ink (was white on dark)
    "text_dim": (0.431, 0.431, 0.451, 1),       # #6e6e73
    "text_muted_dim": (0.525, 0.525, 0.545, 1), # #86868b
}

# ─── Dark tile palette (for dark accents — global nav, overlay) ──────
DARK_TILES = {
    "black": BLACK,
    "tile_1": TILE_1,
    "tile_2": TILE_2,
    "tile_3": TILE_3,
    "body_muted": BODY_MUTED,
    "primary_on_dark": PRIMARY_ON_DARK,
}

# ─── Spacing Tokens (base unit 8px) ──────────────────────────────────

SPACING: dict[str, int] = {
    "xxs": 4,
    "xs": 8,
    "sm": 12,
    "md": 17,
    "lg": 24,
    "xl": 32,
    "xxl": 48,
    "section": 80,
}

# ─── Border Radius Tokens ────────────────────────────────────────────

RADIUS: dict[str, int] = {
    "xs": 5,
    "sm": 8,
    "md": 11,
    "lg": 18,
    "pill": 9999,
    "full": 9999,
}

# ─── Component Heights ───────────────────────────────────────────────

HEIGHTS: dict[str, int] = {
    "global_nav": 44,
    "status_bar": 22,
    "sidebar_item": 34,
    "task_card": 48,
    "button": 36,
    "button_small": 28,
    "input": 36,
    "divider": 1,
}

# ─── Typography Tokens ───────────────────────────────────────────────

FONT_DISPLAY = "system-ui, -apple-system, sans-serif"
FONT_TEXT = "system-ui, -apple-system, sans-serif"
FONT_MONO = "Roboto Mono"

# Text style factory helpers (SF Pro / system-ui substitute)
def text_style(
    size: float,
    weight: ft.FontWeight = ft.FontWeight.W_400,
    color: str = INK,
    letter_spacing: float | None = None,
    family: str = FONT_TEXT,
) -> ft.TextStyle:
    """Build a TextStyle following the design-doc type scale."""
    return ft.TextStyle(
        size=size,
        weight=weight,
        color=color,
        font_family=family,
        letter_spacing=letter_spacing,
    )


# ─── Priority styling helpers ─────────────────────────────────────────

PRIORITY_LABELS = {
    "critical": "CRITICAL",
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
}

PRIORITY_RGBA = {
    "critical": (1.0, 0.231, 0.188, 1),   # #ff3b30
    "high": (1.0, 0.584, 0.0, 1),         # #ff9500
    "medium": (1.0, 0.8, 0.0, 1),         # #ffcc00
    "low": (0.525, 0.525, 0.545, 1),      # #86868b
}


# ─── Flet Theme Builder ───────────────────────────────────────────────

def build_flet_theme() -> ft.Theme:
    """Build a Flet Theme matching the Apple-style light design system.

    Compatible with Flet 0.86+ — uses ft.Colors (uppercase) and avoids
    removed parameters like Theme.brightness and ColorScheme.background.
    Light mode is set via page.theme_mode in app.py.
    """
    return ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        color_scheme=ft.ColorScheme(
            primary=PRIMARY,
            on_primary=ON_PRIMARY,
            secondary=PRIMARY_FOCUS,
            surface=CANVAS,
            on_surface=INK,
            error=ERROR,
            surface_tint=PRIMARY,
        ),
        text_theme=ft.TextTheme(
            headline_large=ft.TextStyle(
                size=40,
                weight=ft.FontWeight.W_600,
                color=INK,
                font_family=FONT_DISPLAY,
            ),
            headline_medium=ft.TextStyle(
                size=28,
                weight=ft.FontWeight.W_600,
                color=INK,
                font_family=FONT_DISPLAY,
            ),
            title_medium=ft.TextStyle(
                size=17,
                weight=ft.FontWeight.W_600,
                color=INK,
                font_family=FONT_TEXT,
            ),
            title_small=ft.TextStyle(
                size=14,
                weight=ft.FontWeight.W_600,
                color=INK,
                font_family=FONT_TEXT,
            ),
            body_medium=ft.TextStyle(
                size=14,
                color=INK,
                font_family=FONT_TEXT,
            ),
            body_small=ft.TextStyle(
                size=12,
                color=GRAY_2,
                font_family=FONT_TEXT,
            ),
            label_large=ft.TextStyle(
                size=14,
                weight=ft.FontWeight.W_600,
                color=INK,
                font_family=FONT_TEXT,
            ),
            label_medium=ft.TextStyle(
                size=12,
                weight=ft.FontWeight.W_600,
                color=INK,
                font_family=FONT_TEXT,
            ),
            label_small=ft.TextStyle(
                size=10,
                weight=ft.FontWeight.W_400,
                color=GRAY_3,
                font_family=FONT_TEXT,
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
    """Theme constants and helpers for Leadership OS (Apple light system)."""

    dark: ClassVar[dict[str, str]] = LIGHT  # kept for API compatibility
    light: ClassVar[dict[str, str]] = LIGHT
    spacing: ClassVar[dict[str, int]] = SPACING
    radius: ClassVar[dict[str, int]] = RADIUS
    heights: ClassVar[dict[str, int]] = HEIGHTS
    priority_labels: ClassVar[dict[str, str]] = PRIORITY_LABELS
    priority_rgba: ClassVar[dict[str, tuple]] = PRIORITY_RGBA

    @classmethod
    def color(cls, name: str) -> str:
        """Get a color hex value by name."""
        return cls.light.get(name, "#000000")

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
        """Convert hex color to flet color string, preserving alpha if present."""
        if len(hex_color) in (7, 9) and hex_color[0] == "#":
            return hex_color
        return hex_color

    @classmethod
    def focus_rgba_str(cls) -> str:
        """Get focus/primary accent as hex string for Flet."""
        return PRIMARY

    @classmethod
    def success_rgba_str(cls) -> str:
        """Get success green as hex string for Flet."""
        return SUCCESS

    @classmethod
    def error_rgba_str(cls) -> str:
        """Get error red as hex string for Flet."""
        return ERROR

    @classmethod
    def text_primary_str(cls) -> str:
        return INK

    @classmethod
    def text_secondary_str(cls) -> str:
        return GRAY_2

    @classmethod
    def text_dim_str(cls) -> str:
        return GRAY_3

    @classmethod
    def text_muted_str(cls) -> str:
        return GRAY_3

    @classmethod
    def surface_str(cls) -> str:
        return CANVAS

    @classmethod
    def card_str(cls) -> str:
        return CANVAS

    @classmethod
    def card_alt_str(cls) -> str:
        return PEARL

    @classmethod
    def bg_str(cls) -> str:
        return PARCHMENT


# Module-level convenience instance
theme = Theme()
