"""The main pet window: frameless, translucent, always-on-top, composing
body/eye/head-tilt/ear/expression layers on top of one loaded char pack.

This is the one place that wires together rendering/, mood/, charpack/,
and features/ — every individual module stays generic/testable, and
this class is the "glue".
"""

from __future__ import annotations

import os

from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget

from pixelpal.charpack.loader import LoadedCharPack
from pixelpal.core.config_store import ConfigStore, WindowState, save_window_state
from pixelpal.core.context_menu import build_context_menu
from pixelpal.core.drag import DragController
from pixelpal.mood.audio_level import create_audio_monitor
from pixelpal.mood.state_machine import MoodEngine, MoodState
from pixelpal.rendering.body_layer import BodyLayer
from pixelpal.rendering.ear_layer import EarLayer
from pixelpal.rendering.expression_layer import ExpressionLayer
from pixelpal.rendering.eye_layer import EyeLayer
from pixelpal.rendering.head_tilt import HeadTiltController
from pixelpal.utils.platform_utils import supports_translucent_background

MOOD_TICK_MS = 1000


class OverlayWindow(QWidget):
    def __init__(
        self,
        pack: LoadedCharPack,
        config_store: ConfigStore,
        mood_engine: MoodEngine | None = None,
    ) -> None:
        super().__init__()
        self.pack = pack
        self.config_store = config_store
        self.mood_engine = mood_engine or MoodEngine()

        self._configure_window_flags()
        self._drag = DragController(self)

        self._build_layers()
        self._restore_position()

        self._mood_timer = QTimer(self)
        self._mood_timer.timeout.connect(self._on_mood_tick)
        self._mood_timer.start(MOOD_TICK_MS)

        self._on_quit_callback = None
        self._on_switch_character_callback = None
        self._on_open_reminders_callback = None
        self._on_open_ollama_settings_callback = None
        self._on_open_chat_callback = None
        self._on_install_char_pack_callback = None

    # -- window setup --------------------------------------------------
    def _configure_window_flags(self) -> None:
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )

        if supports_translucent_background():
            self.setAttribute(Qt.WA_TranslucentBackground)
        else:
            # Degraded fallback for compositor-less X11: no true
            # translucency, so we clip the window to the sprite's
            # silhouette instead of showing a black box (see
            # _apply_silhouette_mask, called after the body pixmap loads).
            self.setAttribute(Qt.WA_TranslucentBackground, False)

        self.setAttribute(Qt.WA_ShowWithoutActivating)

    def _build_layers(self) -> None:
        cfg = self.pack.config

        self.body_layer = BodyLayer(self.pack.body_path(), cfg.wait_seconds, parent=self)
        self.body_layer.move(0, 0)

        size = self.body_layer.sizeHint()
        self.resize(size)
        self.body_layer.resize(size)

        tick_fps = self.config_store.get_int("eyes", "tick_rate_fps", 45)
        self.eye_layer = EyeLayer(
            cfg.eyes.left,
            cfg.eyes.right,
            self.pack.pupil_path(),
            self.pack.closed_eye_path(),
            parent=self,
            tick_rate_fps=tick_fps,
        )
        self.eye_layer.move(0, 0)
        self.eye_layer.resize(size)
        self.eye_layer.raise_()

        self.head_tilt_controller: HeadTiltController | None = None
        if cfg.head_tilt.enabled:
            self.head_tilt_controller = HeadTiltController(
                target=self.body_layer,
                config=cfg.head_tilt,
                reference_widget=self,
            )

        self.expression_layer = ExpressionLayer(
            {mood: self.pack.expression_anchor(mood) for mood in cfg.expressions},
            parent=self,
        )
        self.expression_layer.raise_()

        self.ear_layer = None
        if cfg.ears.enabled and self.config_store.get_bool("ears", "audio_reactive", False):
            monitor = create_audio_monitor(enabled=True)
            self.ear_layer = EarLayer(self.body_layer, monitor)

        if not supports_translucent_background():
            self._apply_silhouette_mask()

    def _apply_silhouette_mask(self) -> None:
        pixmap = self.body_layer.pixmap()
        if pixmap and not pixmap.isNull():
            self.setMask(pixmap.mask())

    def _restore_position(self) -> None:
        x = self.config_store.get_int("window", "pos_x", 100)
        y = self.config_store.get_int("window", "pos_y", 100)
        self.move(x, y)

    def _save_position(self) -> None:
        pos = self.pos()
        state = WindowState(pos_x=pos.x(), pos_y=pos.y(), character=self.pack.config.name)
        save_window_state(self.config_store, state)

    # -- mouse interaction ----------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag.handle_mouse_press(event)
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag.handle_mouse_move(event)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        was_drag = self._drag.handle_mouse_release(event)
        if was_drag:
            self._save_position()
        event.accept()

    def contextMenuEvent(self, event) -> None:  # noqa: N802, ANN001
        menu = build_context_menu(
            self,
            available_characters=self._available_characters,
            current_character=self.pack.config.name,
            on_switch_character=self._emit_switch_character,
            on_open_reminders=self._emit_open_reminders,
            on_open_ollama_settings=self._emit_open_ollama_settings,
            on_open_chat=self._emit_open_chat,
            on_toggle_mood_debug=self._on_force_mood,
            on_install_char_pack=self._emit_install_char_pack,
            on_quit=self._emit_quit,
        )
        menu.exec(event.globalPos())

    # -- callback wiring (main.py sets these) ----------------------------
    available_characters_provider = None

    @property
    def _available_characters(self) -> list[tuple[str, str]]:
        if self.available_characters_provider:
            return self.available_characters_provider()
        return [(self.pack.config.name, self.pack.config.display_name)]

    def set_callbacks(
        self,
        on_quit=None,
        on_switch_character=None,
        on_open_reminders=None,
        on_open_ollama_settings=None,
        on_open_chat=None,
        on_install_char_pack=None,
    ) -> None:
        self._on_quit_callback = on_quit
        self._on_switch_character_callback = on_switch_character
        self._on_open_reminders_callback = on_open_reminders
        self._on_open_ollama_settings_callback = on_open_ollama_settings
        self._on_open_chat_callback = on_open_chat
        self._on_install_char_pack_callback = on_install_char_pack

    def _emit_quit(self) -> None:
        self._save_position()
        if self._on_quit_callback:
            self._on_quit_callback()

    def _emit_switch_character(self, name: str) -> None:
        if self._on_switch_character_callback:
            self._on_switch_character_callback(name)

    def _emit_open_reminders(self) -> None:
        if self._on_open_reminders_callback:
            self._on_open_reminders_callback()

    def _emit_open_ollama_settings(self) -> None:
        if self._on_open_ollama_settings_callback:
            self._on_open_ollama_settings_callback()

    def _emit_open_chat(self) -> None:
        if self._on_open_chat_callback:
            self._on_open_chat_callback()

    def _emit_install_char_pack(self) -> None:
        if self._on_install_char_pack_callback:
            self._on_install_char_pack_callback()

    # -- mood wiring -----------------------------------------------------
    def _on_force_mood(self, state: MoodState) -> None:
        self.mood_engine.force_state(state)
        self._apply_mood(state)

    def _on_mood_tick(self) -> None:
        state = self.mood_engine.tick()
        self._apply_mood(state)

    def _apply_mood(self, state: MoodState) -> None:
        self.eye_layer.set_eyes_closed(state == MoodState.SLEEPY)
        self.expression_layer.set_mood(state)

    def closeEvent(self, event) -> None:  # noqa: N802, ANN001
        self.eye_layer.stop()
        self.body_layer.stop()
        if self.head_tilt_controller:
            self.head_tilt_controller.stop()
        if self.ear_layer:
            self.ear_layer.stop()
        super().closeEvent(event)
