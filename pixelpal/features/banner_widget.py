"""Animated banner shown when a reminder fires — slides across the top
of the screen, holds briefly, then slides out and self-destructs.
"""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QPoint, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QApplication, QWidget

BANNER_HEIGHT = 56
BANNER_PADDING_X = 24
HOLD_MS = 3500
SLIDE_MS = 500


class BannerWidget(QWidget):
    def __init__(self, message: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.message = message

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self._font = QFont()
        self._font.setPointSize(11)
        self._font.setBold(True)

        metrics = QFontMetrics(self._font)
        text_width = metrics.horizontalAdvance(self.message)
        self._width = text_width + BANNER_PADDING_X * 2
        self.resize(self._width, BANNER_HEIGHT)

        self._final_y = 24
        self._start_pos: QPoint | None = None
        self._end_pos: QPoint | None = None

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(QColor(30, 30, 40, 235))
        painter.setPen(QColor(255, 255, 255, 40))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)

        painter.setFont(self._font)
        painter.setPen(QColor(255, 255, 255, 255))
        painter.drawText(self.rect(), Qt.AlignCenter, self.message)

    def show_and_animate(self) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        centered_x = (screen.width() - self._width) // 2

        self._start_pos = QPoint(centered_x, -BANNER_HEIGHT - 10)
        self._end_pos = QPoint(centered_x, self._final_y)

        self.move(self._start_pos)
        self.show()

        self._slide_in = QPropertyAnimation(self, b"pos")
        self._slide_in.setDuration(SLIDE_MS)
        self._slide_in.setStartValue(self._start_pos)
        self._slide_in.setEndValue(self._end_pos)
        self._slide_in.setEasingCurve(QEasingCurve.OutCubic)
        self._slide_in.start()

        QTimer.singleShot(SLIDE_MS + HOLD_MS, self._slide_out)

    def _slide_out(self) -> None:
        self._slide_out_anim = QPropertyAnimation(self, b"pos")
        self._slide_out_anim.setDuration(SLIDE_MS)
        self._slide_out_anim.setStartValue(self._end_pos)
        self._slide_out_anim.setEndValue(self._start_pos)
        self._slide_out_anim.setEasingCurve(QEasingCurve.InCubic)
        self._slide_out_anim.finished.connect(self.close)
        self._slide_out_anim.start()
