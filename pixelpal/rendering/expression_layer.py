"""Mood-driven expression overlay (mouth/brow sprite swap).

Purely optional per char pack — only moods present in the pack's
`expressions` dict get a visible overlay; anything else (including
IDLE) just shows no overlay, letting the base body art carry it.

Each mood's overlay carries its own (x, y) anchor — the point on the
body art (e.g. the mouth) where that sprite should be centered — so
overlays land in the right place instead of defaulting to the
window's top-left corner.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QWidget

from pixelpal.mood.state_machine import MoodState


class ExpressionLayer(QLabel):
    def __init__(
        self,
        expression_anchors: dict[str, tuple[str, float, float]],
        parent: QWidget | None = None,
    ) -> None:
        """expression_anchors: mood -> (full_path, x, y)."""
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._pixmaps: dict[str, QPixmap] = {}
        self._anchors: dict[str, tuple[float, float]] = {}
        for mood, (path, x, y) in expression_anchors.items():
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self._pixmaps[mood] = pixmap
                self._anchors[mood] = (x, y)

        self.clear()

    def set_mood(self, mood: MoodState) -> None:
        pixmap = self._pixmaps.get(mood.value)
        if pixmap is None:
            self.setPixmap(QPixmap())
            self.hide()
            return

        x, y = self._anchors.get(mood.value, (0.0, 0.0))
        self.setPixmap(pixmap)
        self.resize(pixmap.size())
        self.move(int(x - pixmap.width() / 2), int(y - pixmap.height() / 2))
        self.show()
