"""Drag-to-move mixin: tracks mousePress offset, applies it on mouseMove.

Isolated as a small helper class (rather than baked into
overlay_window.py) so the offset-tracking math is easy to reason about
and reuse if other draggable widgets are added later (e.g. the chat
window).
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget


class DragController:
    def __init__(self, window: QWidget) -> None:
        self.window = window
        self._drag_offset: QPoint | None = None
        self._did_drag = False

    def handle_mouse_press(self, event: QMouseEvent) -> None:
        if event.button() != Qt.LeftButton:
            return
        self._drag_offset = event.globalPosition().toPoint() - self.window.pos()
        self._did_drag = False

    def handle_mouse_move(self, event: QMouseEvent) -> None:
        if self._drag_offset is None:
            return
        new_pos = event.globalPosition().toPoint() - self._drag_offset
        self.window.move(new_pos)
        self._did_drag = True

    def handle_mouse_release(self, event: QMouseEvent) -> bool:
        """Returns True if this release ends a drag (vs. a plain click)."""
        was_drag = self._did_drag
        self._drag_offset = None
        self._did_drag = False
        return was_drag
