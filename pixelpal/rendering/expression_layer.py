"""Mood-driven expression overlay (mouth/brow sprite swap).

Purely optional per char pack — only moods present in the pack's
`expressions` dict get a visible overlay; anything else (including
IDLE) just shows no overlay, letting the base body art carry it.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QWidget

from pixelpal.mood.state_machine import MoodState


class ExpressionLayer(QLabel):
    def __init__(self, expression_paths: dict[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._pixmaps: dict[str, QPixmap] = {}
        for mood, path in expression_paths.items():
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self._pixmaps[mood] = pixmap

        self.clear()

    def set_mood(self, mood: MoodState) -> None:
        pixmap = self._pixmaps.get(mood.value)
        if pixmap is None:
            self.setPixmap(QPixmap())
            self.hide()
            return

        self.setPixmap(pixmap)
        self.resize(pixmap.size())
        self.show()
