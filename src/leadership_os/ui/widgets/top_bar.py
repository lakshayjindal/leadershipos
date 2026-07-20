"""TopBar — top navigation bar.

Displays the Leadership OS brand, and right-side action buttons
(search, settings, command palette).

Design: Slim bar with a primary-colored brand accent block on the left.
"""

from __future__ import annotations

import logging
from pathlib import Path

from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout

from leadership_os.ui.theme import theme

logger = logging.getLogger(__name__)

# Load KV is embedded in main.kv — no separate file needed for TopBar


class TopBar(BoxLayout):
    """Top navigation bar with brand and action buttons."""

    current_screen = StringProperty("today")

    # Callbacks
    on_search = ObjectProperty(lambda: None)
    on_settings = ObjectProperty(lambda: None)
    on_command_palette = ObjectProperty(lambda: None)
