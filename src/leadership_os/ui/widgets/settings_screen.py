"""SettingsScreen — full settings page for Leadership OS (Flet).

Provides tabbed configuration for: Work Schedule, UI, Journaling,
Keyboard Shortcuts, and Startup behavior.

Uses ConfigManager for read/write and emits CONFIG_CHANGED on save.
"""

from __future__ import annotations

import flet as ft

from leadership_os.config.config_manager import ConfigManager
from leadership_os.core.event_bus import CONFIG_CHANGED, EventBus
from leadership_os.ui.theme import Theme

# ─── Helpers ──────────────────────────────────────────────────────────


def _section_label(text: str) -> ft.Text:
    return ft.Text(text, color=Theme.GRAY_3, size=10, weight=ft.FontWeight.W_700)


def _setting_row(
    label: str,
    control: ft.Control,
    description: str = "",
) -> ft.Column:
    """Build a labeled setting row with optional description."""
    controls: list[ft.Control] = [
        ft.Row(
            controls=[
                ft.Text(label, color=Theme.INK, size=13),
                ft.Container(expand=True),
                control,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    ]
    if description:
        controls.append(
            ft.Text(description, color=Theme.GRAY_4, size=10)
        )
    return ft.Column(spacing=2, controls=controls)


def _divider() -> ft.Divider:
    return ft.Divider(height=1, color=Theme.HAIRLINE)


def _save_button(on_click) -> ft.Button:
    return ft.Button(
        content=ft.Text("Save Settings", size=13, color=Theme.ON_PRIMARY),
        bgcolor=Theme.PRIMARY,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Theme.radius["pill"])),
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
            e.page.snack_bar = ft.SnackBar(
                content=ft.Text("Settings saved", color="white", size=13),
                bgcolor=Theme.color("success"),
                duration=2000,
            )
            e.page.snack_bar.open = True
            e.page.update()

    def on_reset(e):
        """Reset all settings to defaults."""
        config.reset()
        event_bus.emit(CONFIG_CHANGED, {"source": "settings_screen", "reset": True})
        if on_close:
            on_close()

    # ── Tab 1: Work Schedule ──────────────────────────────────────

    def _input_field(ref, value: str, width: int, hint: str = "") -> ft.TextField:
        """Build a light-styled input field used across settings tabs."""
        return ft.TextField(
            ref=ref,
            value=value,
            width=width,
            height=36,
            text_size=13,
        border=ft.InputBorder.OUTLINE,
        border_color=Theme.HAIRLINE,
        focused_border_color=Theme.PRIMARY,
        bgcolor=Theme.CANVAS,
        color=Theme.INK,
        dense=True,
        hint_text=hint,
    )

    work_schedule_tab = ft.Container(
        padding=20,
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text("Work Schedule", color=Theme.INK, size=16, weight=ft.FontWeight.W_700),
                _divider(),
                _setting_row(
                    "Start Time",
                    _input_field(start_time, work.get("start_time", "09:00"), 80),
                    "When your workday typically begins",
                ),
                _setting_row(
                    "End Time",
                    _input_field(end_time, work.get("end_time", "18:00"), 80),
                    "When your workday typically ends",
                ),
                _setting_row(
                    "Lunch Time",
                    _input_field(lunch_time, work.get("lunch_time", "13:00"), 80),
                    "Your usual lunch break time",
                ),
                _setting_row(
                    "Dinner Time",
                    _input_field(dinner_time, work.get("dinner_time", "19:00"), 80),
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
                ft.Text("Interface", color=Theme.INK, size=16, weight=ft.FontWeight.W_700),
                _divider(),
                _setting_row(
                    "Theme",
                    ft.Dropdown(
                        ref=theme_dropdown,
                        value=ui.get("theme", "light"),
                        width=120,
                        height=36,
                        options=[
                            ft.dropdown.Option("dark", "Dark"),
                            ft.dropdown.Option("light", "Light"),
                            ft.dropdown.Option("system", "System"),
                        ],
                        border_color=Theme.HAIRLINE,
                        focused_border_color=Theme.PRIMARY,
                        bgcolor=Theme.CANVAS,
                        color=Theme.INK,
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
                        active_color=Theme.PRIMARY,
                    ),
                    "Transparency of the floating overlay window",
                ),
                _setting_row(
                    "Show Overlay",
                    ft.Switch(
                        ref=show_overlay,
                        value=bool(ui.get("show_overlay", True)),
                        active_color=Theme.PRIMARY,
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
                ft.Text("Journaling", color=Theme.INK, size=16, weight=ft.FontWeight.W_700),
                _divider(),
                _setting_row(
                    "Obsidian Vault Path",
                    _input_field(vault_path, journaling.get("vault_path", "~/Documents/Obsidian"), 280),
                    "Root path of your Obsidian vault",
                ),
                _setting_row(
                    "Journal Directory",
                    _input_field(journal_dir, journaling.get("journal_dir", "Daily Notes"), 200),
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
                ft.Text("Keyboard Shortcuts", color=Theme.INK, size=16, weight=ft.FontWeight.W_700),
                _divider(),
                _setting_row(
                    "Create Task",
                    _input_field(kb_create, keyboard.get("create_task", "ctrl+n"), 140),
                ),
                _setting_row(
                    "Complete Task",
                    _input_field(kb_complete, keyboard.get("complete_task", "ctrl+enter"), 140),
                ),
                _setting_row(
                    "Pause/Resume Task",
                    _input_field(kb_pause, keyboard.get("pause_task", "ctrl+space"), 140),
                ),
                _setting_row(
                    "Start Break",
                    _input_field(kb_break, keyboard.get("start_break", "ctrl+b"), 140),
                ),
                _setting_row(
                    "End Break",
                    _input_field(kb_end_break, keyboard.get("end_break", "ctrl+shift+b"), 140),
                ),
                _setting_row(
                    "End-of-Day Review",
                    _input_field(kb_review, keyboard.get("end_day", "ctrl+e"), 140),
                ),
                _setting_row(
                    "Command Palette",
                    _input_field(kb_cmd_palette, keyboard.get("command_palette", "ctrl+k"), 140),
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
                ft.Text("Startup Behavior", color=Theme.INK, size=16, weight=ft.FontWeight.W_700),
                _divider(),
                _setting_row(
                    "Minimize to System Tray",
                    ft.Switch(
                        ref=minimize_to_tray,
                        value=bool(startup.get("minimize_to_tray", True)),
                        active_color=Theme.PRIMARY,
                    ),
                    "Minimize to tray instead of closing when window is closed",
                ),
                _setting_row(
                    "Restore Previous Session",
                    ft.Switch(
                        ref=restore_session,
                        value=bool(startup.get("restore_previous_session", True)),
                        active_color=Theme.PRIMARY,
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
                ref.current.bgcolor = Theme.PARCHMENT if i == index else "transparent"
        active_tab_content.content = tab_views[index]
        active_tab_content.update()

    def _tab_button(label: str, icon, index: int) -> ft.Container:
        return ft.Container(
            ref=tab_button_refs[index],
            padding=ft.Padding(10, 6, 10, 6),
            border_radius=Theme.radius["sm"],
            bgcolor=Theme.PARCHMENT if index == 0 else "transparent",
            content=ft.Row(
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, size=14, color=Theme.GRAY_3 if index == 0 else Theme.GRAY_2),
                    ft.Text(label, color=Theme.INK if index == 0 else Theme.GRAY_2, size=12),
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
        bgcolor=Theme.PARCHMENT,
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
                            ft.Text("Settings", color=Theme.INK, size=18, weight=ft.FontWeight.W_700),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=18,
                                icon_color=Theme.GRAY_3,
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
                                content=ft.Text("Reset to Defaults", color=Theme.color("error")),
                                on_click=on_reset,
                            ),
                            ft.Container(expand=True),
                            ft.TextButton(
                                content=ft.Text("Cancel", color=Theme.GRAY_3),
                                on_click=lambda _: on_close(),
                            ),
                            _save_button(on_click=on_save),
                        ],
                    ),
                ),
            ],
        ),
    )
