"""SettingsScreen — full settings page for Leadership OS (Flet).

Provides tabbed configuration for: Work Schedule, UI, Journaling,
Keyboard Shortcuts, and Startup behavior.

Uses ConfigManager for read/write and emits CONFIG_CHANGED on save.
"""

from __future__ import annotations

import flet as ft

from leadership_os.config.config_manager import ConfigManager
from leadership_os.core.event_bus import CONFIG_CHANGED, EventBus

# ─── Helpers ──────────────────────────────────────────────────────────


def _section_label(text: str) -> ft.Text:
    return ft.Text(text, color="#747496", size=10, weight=ft.FontWeight.W_700)


def _setting_row(
    label: str,
    control: ft.Control,
    description: str = "",
) -> ft.Column:
    """Build a labeled setting row with optional description."""
    controls: list[ft.Control] = [
        ft.Row(
            controls=[
                ft.Text(label, color="#E8E8F0", size=13),
                ft.Container(expand=True),
                control,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    ]
    if description:
        controls.append(
            ft.Text(description, color="#5A5A80", size=10)
        )
    return ft.Column(spacing=2, controls=controls)


def _divider() -> ft.Divider:
    return ft.Divider(height=1, color="#2D2D4A25")


def _save_button(on_click) -> ft.Button:
    return ft.Button(
        content=ft.Text("Save Settings", size=13, color="white"),
        bgcolor="#4A6FA5",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=on_click,
    )


# ─── Main Builder ─────────────────────────────────────────────────────


def build_settings_screen(
    config: ConfigManager,
    event_bus: EventBus,
    on_close,
) -> ft.Container:
    """Build the full settings screen.

    Args:
        config: ConfigManager instance for read/write.
        event_bus: EventBus to emit CONFIG_CHANGED on save.
        on_close: Callback to return to the main view.

    Returns:
        A Container containing the complete settings screen.
    """

    # ── Initialize field refs from current config ──────────────────
    work = config.get_section("work_schedule")
    ui = config.get_section("ui")
    journaling = config.get_section("journaling")
    keyboard = config.get_section("keyboard")
    startup = config.get_section("startup")

    # Work Schedule fields
    start_time = ft.Ref[ft.TextField]()
    end_time = ft.Ref[ft.TextField]()
    lunch_time = ft.Ref[ft.TextField]()
    dinner_time = ft.Ref[ft.TextField]()

    # UI fields
    theme_dropdown = ft.Ref[ft.Dropdown]()
    overlay_opacity = ft.Ref[ft.Slider]()
    show_overlay = ft.Ref[ft.Switch]()

    # Journaling fields
    vault_path = ft.Ref[ft.TextField]()
    journal_dir = ft.Ref[ft.TextField]()

    # Startup fields
    minimize_to_tray = ft.Ref[ft.Switch]()
    restore_session = ft.Ref[ft.Switch]()

    # Keyboard shortcut fields
    kb_create = ft.Ref[ft.TextField]()
    kb_complete = ft.Ref[ft.TextField]()
    kb_pause = ft.Ref[ft.TextField]()
    kb_break = ft.Ref[ft.TextField]()
    kb_end_break = ft.Ref[ft.TextField]()
    kb_review = ft.Ref[ft.TextField]()
    kb_cmd_palette = ft.Ref[ft.TextField]()

    # ── Save handler ──────────────────────────────────────────────

    def on_save(e):
        """Persist all settings and emit config_changed."""
        # Work schedule
        config.set_section("work_schedule", {
            "start_time": start_time.current.value,
            "end_time": end_time.current.value,
            "lunch_time": lunch_time.current.value,
            "dinner_time": dinner_time.current.value,
        })

        # UI
        config.set_section("ui", {
            "theme": theme_dropdown.current.value,
            "overlay_opacity": float(overlay_opacity.current.value),
            "show_overlay": show_overlay.current.value,
        })

        # Journaling
        config.set_section("journaling", {
            "vault_path": vault_path.current.value,
            "journal_dir": journal_dir.current.value,
        })

        # Keyboard
        config.set_section("keyboard", {
            "create_task": kb_create.current.value,
            "complete_task": kb_complete.current.value,
            "pause_task": kb_pause.current.value,
            "start_break": kb_break.current.value,
            "end_break": kb_end_break.current.value,
            "end_day": kb_review.current.value,
            "command_palette": kb_cmd_palette.current.value,
        })

        # Startup
        config.set_section("startup", {
            "minimize_to_tray": minimize_to_tray.current.value,
            "restore_previous_session": restore_session.current.value,
        })

        config.save()
        event_bus.emit(CONFIG_CHANGED, {"source": "settings_screen"})

        # Show brief snackbar
        if e.page:
            e.page.show_snack_bar(
                ft.SnackBar(
                    ft.Text("Settings saved", color="white", size=13),
                    bgcolor="#66A66B",
                    duration=2000,
                )
            )

    def on_reset(e):
        """Reset all settings to defaults."""
        config.reset()
        event_bus.emit(CONFIG_CHANGED, {"source": "settings_screen", "reset": True})
        if on_close:
            on_close()

    # ── Tab 1: Work Schedule ──────────────────────────────────────

    work_schedule_tab = ft.Container(
        padding=20,
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text("Work Schedule", color="#E8E8F0", size=16, weight=ft.FontWeight.W_700),
                _divider(),
                _setting_row(
                    "Start Time",
                    ft.TextField(
                        ref=start_time,
                        value=work.get("start_time", "09:00"),
                        width=80,
                        height=36,
                        text_size=13,
                        border=ft.InputBorder.OUTLINE,
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        color="#E8E8F0",
                        dense=True,
                    ),
                    "When your workday typically begins",
                ),
                _setting_row(
                    "End Time",
                    ft.TextField(
                        ref=end_time,
                        value=work.get("end_time", "18:00"),
                        width=80,
                        height=36,
                        text_size=13,
                        border=ft.InputBorder.OUTLINE,
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        color="#E8E8F0",
                        dense=True,
                    ),
                    "When your workday typically ends",
                ),
                _setting_row(
                    "Lunch Time",
                    ft.TextField(
                        ref=lunch_time,
                        value=work.get("lunch_time", "13:00"),
                        width=80,
                        height=36,
                        text_size=13,
                        border=ft.InputBorder.OUTLINE,
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        color="#E8E8F0",
                        dense=True,
                    ),
                    "Your usual lunch break time",
                ),
                _setting_row(
                    "Dinner Time",
                    ft.TextField(
                        ref=dinner_time,
                        value=work.get("dinner_time", "19:00"),
                        width=80,
                        height=36,
                        text_size=13,
                        border=ft.InputBorder.OUTLINE,
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        color="#E8E8F0",
                        dense=True,
                    ),
                    "Your usual dinner time",
                ),
            ],
        ),
    )

    # ── Tab 2: UI ─────────────────────────────────────────────────

    ui_tab = ft.Container(
        padding=20,
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text("Interface", color="#E8E8F0", size=16, weight=ft.FontWeight.W_700),
                _divider(),
                _setting_row(
                    "Theme",
                    ft.Dropdown(
                        ref=theme_dropdown,
                        value=ui.get("theme", "dark"),
                        width=120,
                        height=36,
                        options=[
                            ft.dropdown.Option("dark", "Dark"),
                            ft.dropdown.Option("light", "Light"),
                            ft.dropdown.Option("system", "System"),
                        ],
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        color="#E8E8F0",
                        text_size=13,
                        dense=True,
                    ),
                    "Application color theme",
                ),
                _setting_row(
                    "Overlay Opacity",
                    ft.Slider(
                        ref=overlay_opacity,
                        value=float(ui.get("overlay_opacity", 0.85)),
                        min=0.1,
                        max=1.0,
                        divisions=9,
                        width=160,
                        active_color="#4A6FA5",
                    ),
                    "Transparency of the floating overlay window",
                ),
                _setting_row(
                    "Show Overlay",
                    ft.Switch(
                        ref=show_overlay,
                        value=bool(ui.get("show_overlay", True)),
                        active_color="#4A6FA5",
                    ),
                    "Show floating overlay window during work",
                ),
            ],
        ),
    )

    # ── Tab 3: Journaling ─────────────────────────────────────────

    journaling_tab = ft.Container(
        padding=20,
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text("Journaling", color="#E8E8F0", size=16, weight=ft.FontWeight.W_700),
                _divider(),
                _setting_row(
                    "Obsidian Vault Path",
                    ft.TextField(
                        ref=vault_path,
                        value=journaling.get("vault_path", "~/Documents/Obsidian"),
                        width=280,
                        height=36,
                        text_size=13,
                        border=ft.InputBorder.OUTLINE,
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        color="#E8E8F0",
                        dense=True,
                    ),
                    "Root path of your Obsidian vault",
                ),
                _setting_row(
                    "Journal Directory",
                    ft.TextField(
                        ref=journal_dir,
                        value=journaling.get("journal_dir", "Daily Notes"),
                        width=200,
                        height=36,
                        text_size=13,
                        border=ft.InputBorder.OUTLINE,
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        color="#E8E8F0",
                        dense=True,
                    ),
                    "Subdirectory for daily journal files",
                ),
            ],
        ),
    )

    # ── Tab 4: Keyboard ───────────────────────────────────────────

    keyboard_tab = ft.Container(
        padding=20,
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Text("Keyboard Shortcuts", color="#E8E8F0", size=16, weight=ft.FontWeight.W_700),
                _divider(),
                _setting_row(
                    "Create Task",
                    ft.TextField(
                        ref=kb_create,
                        value=keyboard.get("create_task", "ctrl+n"),
                        width=140,
                        height=36,
                        text_size=13,
                        border=ft.InputBorder.OUTLINE,
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        color="#E8E8F0",
                        dense=True,
                    ),
                ),
                _setting_row(
                    "Complete Task",
                    ft.TextField(
                        ref=kb_complete,
                        value=keyboard.get("complete_task", "ctrl+enter"),
                        width=140,
                        height=36,
                        text_size=13,
                        border=ft.InputBorder.OUTLINE,
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        color="#E8E8F0",
                        dense=True,
                    ),
                ),
                _setting_row(
                    "Pause/Resume Task",
                    ft.TextField(
                        ref=kb_pause,
                        value=keyboard.get("pause_task", "ctrl+space"),
                        width=140,
                        height=36,
                        text_size=13,
                        border=ft.InputBorder.OUTLINE,
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        color="#E8E8F0",
                        dense=True,
                    ),
                ),
                _setting_row(
                    "Start Break",
                    ft.TextField(
                        ref=kb_break,
                        value=keyboard.get("start_break", "ctrl+b"),
                        width=140,
                        height=36,
                        text_size=13,
                        border=ft.InputBorder.OUTLINE,
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        color="#E8E8F0",
                        dense=True,
                    ),
                ),
                _setting_row(
                    "End Break",
                    ft.TextField(
                        ref=kb_end_break,
                        value=keyboard.get("end_break", "ctrl+shift+b"),
                        width=140,
                        height=36,
                        text_size=13,
                        border=ft.InputBorder.OUTLINE,
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        color="#E8E8F0",
                        dense=True,
                    ),
                ),
                _setting_row(
                    "End-of-Day Review",
                    ft.TextField(
                        ref=kb_review,
                        value=keyboard.get("end_day", "ctrl+e"),
                        width=140,
                        height=36,
                        text_size=13,
                        border=ft.InputBorder.OUTLINE,
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        color="#E8E8F0",
                        dense=True,
                    ),
                ),
                _setting_row(
                    "Command Palette",
                    ft.TextField(
                        ref=kb_cmd_palette,
                        value=keyboard.get("command_palette", "ctrl+k"),
                        width=140,
                        height=36,
                        text_size=13,
                        border=ft.InputBorder.OUTLINE,
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        color="#E8E8F0",
                        dense=True,
                    ),
                ),
            ],
        ),
    )

    # ── Tab 5: Startup ────────────────────────────────────────────

    startup_tab = ft.Container(
        padding=20,
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text("Startup Behavior", color="#E8E8F0", size=16, weight=ft.FontWeight.W_700),
                _divider(),
                _setting_row(
                    "Minimize to System Tray",
                    ft.Switch(
                        ref=minimize_to_tray,
                        value=bool(startup.get("minimize_to_tray", True)),
                        active_color="#4A6FA5",
                    ),
                    "Minimize to tray instead of closing when window is closed",
                ),
                _setting_row(
                    "Restore Previous Session",
                    ft.Switch(
                        ref=restore_session,
                        value=bool(startup.get("restore_previous_session", True)),
                        active_color="#4A6FA5",
                    ),
                    "Automatically restore your previous session on startup",
                ),
            ],
        ),
    )

    # ── Assemble ──────────────────────────────────────────────────

    tab_views = [
        work_schedule_tab,
        ui_tab,
        journaling_tab,
        keyboard_tab,
        startup_tab,
    ]

    active_tab_content = ft.Container(content=tab_views[0], expand=True)
    tab_button_refs: list[ft.Ref[ft.Container]] = [ft.Ref[ft.Container]() for _ in tab_views]

    tab_labels = [
        ("Work", ft.Icons.ACCESS_TIME),
        ("UI", ft.Icons.PALETTE),
        ("Journal", ft.Icons.BOOK),
        ("Keys", ft.Icons.KEYBOARD),
        ("Startup", ft.Icons.POWER_SETTINGS_NEW),
    ]

    def _select_tab(index: int):
        for i, ref in enumerate(tab_button_refs):
            if ref.current:
                ref.current.bgcolor = "#2D2D4A60" if i == index else "transparent"
        active_tab_content.content = tab_views[index]
        active_tab_content.update()

    def _tab_button(label: str, icon, index: int) -> ft.Container:
        return ft.Container(
            ref=tab_button_refs[index],
            padding=ft.Padding(10, 6, 10, 6),
            border_radius=6,
            bgcolor="#2D2D4A60" if index == 0 else "transparent",
            content=ft.Row(
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, size=14, color="#9898B8"),
                    ft.Text(label, color="#E8E8F0", size=12),
                ],
            ),
            on_click=lambda _, idx=index: _select_tab(idx),
        )

    tab_bar = ft.Container(
        padding=ft.Padding(8, 8, 8, 8),
        content=ft.Row(
            spacing=4,
            alignment=ft.MainAxisAlignment.START,
            controls=[_tab_button(label, icon, i) for i, (label, icon) in enumerate(tab_labels)],
        ),
    )

    return ft.Container(
        expand=True,
        bgcolor="#0D0D1A",
        padding=0,
        content=ft.Column(
            spacing=0,
            controls=[
                # Header
                ft.Container(
                    height=52,
                    padding=ft.Padding(20, 0, 16, 0),
                    content=ft.Row(
                        controls=[
                            ft.Text("Settings", color="#E8E8F0", size=18, weight=ft.FontWeight.W_700),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=18,
                                icon_color="#747496",
                                on_click=lambda _: on_close(),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                # Tabs
                tab_bar,
                # Active tab content
                active_tab_content,
                # Action buttons
                ft.Container(
                    padding=ft.Padding(20, 12, 20, 16),
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.TextButton(
                                content=ft.Text("Reset to Defaults", color="#C45B5B"),
                                on_click=on_reset,
                            ),
                            ft.Container(expand=True),
                            ft.TextButton(
                                content=ft.Text("Cancel", color="#9898B8"),
                                on_click=lambda _: on_close(),
                            ),
                            _save_button(on_click=on_save),
                        ],
                    ),
                ),
            ],
        ),
    )
