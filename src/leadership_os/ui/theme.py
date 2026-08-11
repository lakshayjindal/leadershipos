"""Theme — Apple-style design tokens for Leadership OS (light + dark).

Design language (see DESIGN.md):
- Light, museum-gallery aesthetic: white / parchment surfaces, pure-black
  global nav, and a single Action Blue (#0066cc) for every interactive element.
- Dark mode mirrors the same system: near-black surfaces, white ink, and
  Sky Link Blue (#2997ff) as the interactive accent on dark.
- No decorative gradients or shadows on chrome. The color change between
  light and dark tiles IS the divider.
- Typography: SF Pro Display / SF Pro Text with system-ui fallback
  (Inter is the closest open-source substitute). Body copy at 17px,
  weight ladder 300 / 400 / 600 / 700 (500 is deliberately absent).
- Radii: sm 8px for compact utility, lg 18px for utility cards, pill for
  CTAs and search inputs. Nothing in between except the rare md 11px.
- Buttons press with transform scale(0.95) — the system micro-interaction.

Mode handling:
- Widgets must reference colors as ``Theme.<TOKEN>`` (e.g. ``Theme.INK``)
  or ``Theme.color("success")`` so values resolve from the ACTIVE palette
  at widget build time. Import-time constants are provided for backwards
  compatibility but reflect the light palette.
- Call ``Theme.set_mode("light" | "dark")`` to switch the active palette.
"""

from __future__ import annotations

from typing import ClassVar

import flet as ft

# ─── Apple-style Light Palette ────────────────────────────────────────

# Canonical tokens from DESIGN.md (light)
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

# Dark chrome (sidebar shell — stable dark in BOTH modes)
CHROME = "#1d1d1f"              # Sidebar shell background
CHROME_ACTIVE = "#3a3a3c"       # Sidebar active pill

# ─── Dark Palette (Apple dark system) ────────────────────────────────

DARK = {
    # Surfaces
    "CANVAS": "#1c1c1e",                # Card surface (secondarySystemBackground)
    "PARCHMENT": "#000000",             # App canvas — pure black
    "PEARL": "#2c2c2e",                 # Elevated card surface
    "INK": "#f5f5f7",                   # Primary text — white
    "INK_MUTED_80": "#d1d1d6",
    "INK_MUTED_48": "#8e8e93",
    "BODY_MUTED": "#98989f",
    "HAIRLINE": "#3a3a3c",              # Hairline borders on dark
    "DIVIDER_SOFT": "#2c2c2e",
    "PRIMARY": "#2997ff",               # Sky Link Blue — interactive on dark
    "PRIMARY_FOCUS": "#4aa8ff",
    "PRIMARY_ON_DARK": "#2997ff",
    "ON_PRIMARY": "#ffffff",
    "ON_DARK": "#ffffff",
    "BLACK": "#000000",
    "TILE_1": "#272729",
    "TILE_2": "#2a2a2c",
    "TILE_3": "#252527",
    "CHIP": "#48484a",

    # Semantic
    "SUCCESS": "#30d158",
    "WARNING": "#ff9f0a",
    "ERROR": "#ff453a",

    # Tints
    "TINT_ERROR": "#ff453a33",
    "TINT_PRIMARY": "#2997ff33",

    # Grays (dark label ladder)
    "GRAY_1": "#f5f5f7",
    "GRAY_2": "#d1d1d6",
    "GRAY_3": "#8e8e93",
    "GRAY_4": "#636366",
    "GRAY_5": "#48484a",

    # Dark chrome (stable)
    "CHROME": "#1c1c1e",
    "CHROME_ACTIVE": "#2c2c2e",

    # Semantic lowercase aliases (for Theme.color("success") etc.)
    "primary": "#2997ff",
    "primary_light": "#4aa8ff",
    "primary_dark": "#0a84ff",
    "success": "#30d158",
    "warning": "#ff9f0a",
    "error": "#ff453a",
    "background": "#000000",
    "surface": "#1c1c1e",
    "surface_light": "#2c2c2e",
    "surface_hover": "#2c2c2e",
    "border": "#3a3a3c",
    "border_focus": "#4aa8ff",
    "text_primary": "#f5f5f7",
    "text_secondary": "#d1d1d6",
    "text_muted": "#8e8e93",
    "text_disabled": "#636366",
}

# ─── Light palette (all tokens + legacy aliases) ─────────────────────

LIGHT = {
    "CANVAS": CANVAS,
    "PARCHMENT": PARCHMENT,
    "PEARL": PEARL,
    "INK": INK,
    "INK_MUTED_80": INK_MUTED_80,
    "INK_MUTED_48": INK_MUTED_48,
    "BODY_MUTED": BODY_MUTED,
    "HAIRLINE": HAIRLINE,
    "DIVIDER_SOFT": DIVIDER_SOFT,
    "PRIMARY": PRIMARY,
    "PRIMARY_FOCUS": PRIMARY_FOCUS,
    "PRIMARY_ON_DARK": PRIMARY_ON_DARK,
    "ON_PRIMARY": ON_PRIMARY,
    "ON_DARK": ON_DARK,
    "BLACK": BLACK,
    "TILE_1": TILE_1,
    "TILE_2": TILE_2,
    "TILE_3": TILE_3,
    "CHIP": CHIP,
    "SUCCESS": SUCCESS,
    "WARNING": WARNING,
    "ERROR": ERROR,
    "TINT_ERROR": TINT_ERROR,
    "TINT_PRIMARY": TINT_PRIMARY,
    "GRAY_1": GRAY_1,
    "GRAY_2": GRAY_2,
    "GRAY_3": GRAY_3,
    "GRAY_4": GRAY_4,
    "GRAY_5": GRAY_5,
    "CHROME": CHROME,
    "CHROME_ACTIVE": CHROME_ACTIVE,

    # Legacy semantic aliases
    "background": PARCHMENT,
    "surface": CANVAS,
    "surface_light": PEARL,
    "surface_hover": DIVIDER_SOFT,
    "border": HAIRLINE,
    "border_focus": PRIMARY_FOCUS,
    "text_primary": INK,
    "text_secondary": GRAY_2,
    "text_muted": GRAY_3,
    "text_disabled": GRAY_4,
    "priority_critical": "#ff3b30",
    "priority_high": "#ff9500",
    "priority_medium": "#ffcc00",
    "priority_low": GRAY_3,
    "accent_sky": "#2997ff",
    "accent_purple": "#af52de",
    "accent_pink": "#ff2d55",
    "accent_orange": "#ff9500",
    "accent_teal": "#30b0c7",
    "primary": PRIMARY,
    "primary_light": PRIMARY_FOCUS,
    "primary_dark": "#0055b3",
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
    "text_white": (0.114, 0.114, 0.122, 1),     # #1d1d1f ink
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


def text_style(
    size: float,
    weight: ft.FontWeight = ft.FontWeight.W_400,
    color: str | None = None,
    letter_spacing: float | None = None,
    family: str = FONT_TEXT,
) -> ft.TextStyle:
    """Build a TextStyle following the design-doc type scale.

    ``color`` defaults to the active palette's ink.
    """
    return ft.TextStyle(
        size=size,
        weight=weight,
        color=color if color is not None else Theme.INK,
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


# ─── Theme (mode-aware) ───────────────────────────────────────────────

_PALETTES: dict[str, dict] = {"light": LIGHT, "dark": DARK}


class _ThemeMeta(type):
    """Metaclass so ``Theme.<TOKEN>`` resolves from the active palette."""

    def __getattr__(cls, name: str):
        palette = Theme._active_palette()
        if name in palette:
            return palette[name]
        raise AttributeError(f"{cls.__name__}.{name}")


class Theme(metaclass=_ThemeMeta):
    """Mode-aware theme constants and helpers.

    Attribute access (``Theme.INK``) and ``Theme.color("success")`` both
    resolve from the ACTIVE palette (light or dark). Call ``Theme.set_mode``
    to switch palettes — rebuilt widgets pick up the new colors.
    """

    _mode: ClassVar[str] = "light"
    dark: ClassVar[dict] = DARK          # full dark palette
    light: ClassVar[dict] = LIGHT        # full light palette
    spacing: ClassVar[dict[str, int]] = SPACING
    radius: ClassVar[dict[str, int]] = RADIUS
    heights: ClassVar[dict[str, int]] = HEIGHTS
    priority_labels: ClassVar[dict[str, str]] = PRIORITY_LABELS
    priority_rgba: ClassVar[dict[str, tuple]] = PRIORITY_RGBA

    @classmethod
    def set_mode(cls, mode: str) -> None:
        """Switch the active palette ("light" or "dark")."""
        cls._mode = "dark" if str(mode).lower() == "dark" else "light"

    @classmethod
    def mode(cls) -> str:
        """Return the active mode name."""
        return cls._mode

    @classmethod
    def _active_palette(cls) -> dict:
        return _PALETTES[cls._mode]

    @classmethod
    def color(cls, name: str) -> str:
        """Get a color hex value by name from the active palette."""
        return cls._active_palette().get(name, "#000000")

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
        return cls.color("primary")

    @classmethod
    def success_rgba_str(cls) -> str:
        return cls.color("success")

    @classmethod
    def error_rgba_str(cls) -> str:
        return cls.color("error")

    @classmethod
    def text_primary_str(cls) -> str:
        return cls.color("text_primary")

    @classmethod
    def text_secondary_str(cls) -> str:
        return cls.color("text_secondary")

    @classmethod
    def text_dim_str(cls) -> str:
        return cls.color("text_muted")

    @classmethod
    def text_muted_str(cls) -> str:
        return cls.color("text_muted")

    @classmethod
    def surface_str(cls) -> str:
        return cls.color("surface")

    @classmethod
    def card_str(cls) -> str:
        return cls.color("surface")

    @classmethod
    def card_alt_str(cls) -> str:
        return cls.color("surface_light")

    @classmethod
    def bg_str(cls) -> str:
        return cls.color("background")


# Module-level convenience instance (legacy)
theme = Theme()


# ─── Flet Theme Builder ───────────────────────────────────────────────

def build_flet_theme() -> ft.Theme:
    """Build a Flet Theme matching the ACTIVE Apple-style palette.

    Compatible with Flet 0.86+ — uses ft.Colors (uppercase) and avoids
    removed parameters like Theme.brightness and ColorScheme.background.
    The page's theme_mode should be kept in sync via app.py.
    """
    pal = Theme._active_palette()
    return ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        color_scheme=ft.ColorScheme(
            primary=pal["PRIMARY"],
            on_primary=pal["ON_PRIMARY"],
            secondary=pal["PRIMARY_FOCUS"],
            surface=pal["CANVAS"],
            on_surface=pal["INK"],
            error=pal["ERROR"],
            surface_tint=pal["PRIMARY"],
        ),
        text_theme=ft.TextTheme(
            headline_large=ft.TextStyle(
                size=40,
                weight=ft.FontWeight.W_600,
                color=pal["INK"],
                font_family=FONT_DISPLAY,
            ),
            headline_medium=ft.TextStyle(
                size=28,
                weight=ft.FontWeight.W_600,
                color=pal["INK"],
                font_family=FONT_DISPLAY,
            ),
            title_medium=ft.TextStyle(
                size=17,
                weight=ft.FontWeight.W_600,
                color=pal["INK"],
                font_family=FONT_TEXT,
            ),
            title_small=ft.TextStyle(
                size=14,
                weight=ft.FontWeight.W_600,
                color=pal["INK"],
                font_family=FONT_TEXT,
            ),
            body_medium=ft.TextStyle(
                size=14,
                color=pal["INK"],
                font_family=FONT_TEXT,
            ),
            body_small=ft.TextStyle(
                size=12,
                color=pal["GRAY_2"],
                font_family=FONT_TEXT,
            ),
            label_large=ft.TextStyle(
                size=14,
                weight=ft.FontWeight.W_600,
                color=pal["INK"],
                font_family=FONT_TEXT,
            ),
            label_medium=ft.TextStyle(
                size=12,
                weight=ft.FontWeight.W_600,
                color=pal["INK"],
                font_family=FONT_TEXT,
            ),
            label_small=ft.TextStyle(
                size=10,
                weight=ft.FontWeight.W_400,
                color=pal["GRAY_3"],
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
