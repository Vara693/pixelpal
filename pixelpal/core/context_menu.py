"""Right-click context menu: switch char, mood debug toggle, reminder
settings, Ollama chat settings, open chat, quit.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QMenu, QWidget

from pixelpal.mood.state_machine import MoodState


def build_context_menu(
    parent: QWidget,
    available_characters: list[tuple[str, str]],  # (name, display_name)
    current_character: str,
    on_switch_character: Callable[[str], None],
    on_open_reminders: Callable[[], None],
    on_open_ollama_settings: Callable[[], None],
    on_open_chat: Callable[[], None],
    on_toggle_mood_debug: Callable[[MoodState], None],
    on_install_char_pack: Callable[[], None],
    on_quit: Callable[[], None],
    mood_debug_enabled: bool = False,
) -> QMenu:
    menu = QMenu(parent)

    char_menu = menu.addMenu("Switch character")
    for name, display_name in available_characters:
        action = char_menu.addAction(display_name)
        action.setCheckable(True)
        action.setChecked(name == current_character)
        action.triggered.connect(lambda checked=False, n=name: on_switch_character(n))
    char_menu.addSeparator()
    char_menu.addAction("Install char pack...").triggered.connect(on_install_char_pack)

    menu.addSeparator()

    mood_menu = menu.addMenu("Mood debug")
    mood_menu.setEnabled(True)
    for state in MoodState:
        action = mood_menu.addAction(f"Force: {state.value}")
        action.triggered.connect(lambda checked=False, s=state: on_toggle_mood_debug(s))

    menu.addSeparator()

    menu.addAction("Reminders...").triggered.connect(on_open_reminders)
    menu.addAction("Ollama chat settings...").triggered.connect(on_open_ollama_settings)
    menu.addAction("Open chat").triggered.connect(on_open_chat)

    menu.addSeparator()
    menu.addAction("Quit PixelPal").triggered.connect(on_quit)

    return menu
