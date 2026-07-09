"""Generic cursor-tracking eye/pupil rendering.

This is the app's core differentiator: pupils are positioned every
frame using the pure math in utils.geometry (angle + clamped socket
radius + damped interpolation) so movement looks organic. This module
never references a specific animal — it only reads eye-socket
coordinates from the char pack's config.json, so it works unmodified
for any correctly-structured character.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtGui import QCursor, QPixmap
from PySide6.QtWidgets import QWidget

from pixelpal.charpack.schema import EyeSocket
from pixelpal.utils.geometry import Point, damped_step, pupil_offset


class EyeState:
    """Tracks one eye socket's current (damped) pupil position."""

    def __init__(self, socket: EyeSocket) -> None:
        self.socket = socket
        self.current_offset = Point(0.0, 0.0)
        self.eyes_closed = False

    def step(self, cursor_local: Point) -> None:
        socket_center = Point(self.socket.x, self.socket.y)
        target = pupil_offset(socket_center, cursor_local, self.socket.radius)
        self.current_offset = damped_step(self.current_offset, target, self.socket.damping)

    def render_position(self) -> Point:
        return Point(
            self.socket.x + self.current_offset.x,
            self.socket.y + self.current_offset.y,
        )


class EyeLayer(QWidget):
    """Transparent overlay widget that paints pupils on top of the body layer.

    `tick_rate_fps` controls the QTimer driving position updates —
    kept configurable per non-functional requirement of a tunable,
    CPU-conscious tick rate (default target 30-60fps).
    """

    def __init__(
        self,
        left_socket: EyeSocket,
        right_socket: EyeSocket,
        pupil_pixmap_path: str,
        closed_pixmap_path: str | None,
        parent: QWidget | None = None,
        tick_rate_fps: int = 45,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.left = EyeState(left_socket)
        self.right = EyeState(right_socket)

        self._pupil_pixmap = QPixmap(pupil_pixmap_path)
        self._closed_pixmap = QPixmap(closed_pixmap_path) if closed_pixmap_path else None
        self._eyes_closed = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self.set_tick_rate(tick_rate_fps)

    def set_tick_rate(self, fps: int) -> None:
        fps = max(1, min(fps, 120))
        interval_ms = int(1000 / fps)
        self._timer.start(interval_ms)

    def set_eyes_closed(self, closed: bool) -> None:
        """Used by the mood system (e.g. SLEEPY state half-closes eyes)."""
        self._eyes_closed = closed
        self.update()

    def _on_tick(self) -> None:
        global_cursor = QCursor.pos()
        local = self.mapFromGlobal(global_cursor)
        cursor_local = Point(float(local.x()), float(local.y()))

        self.left.step(cursor_local)
        self.right.step(cursor_local)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override
        from PySide6.QtGui import QPainter

        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if self._eyes_closed and self._closed_pixmap is not None and not self._closed_pixmap.isNull():
            self._paint_eye(painter, self._closed_pixmap, self.left.socket)
            self._paint_eye(painter, self._closed_pixmap, self.right.socket)
            return

        if self._pupil_pixmap.isNull():
            return

        self._paint_pupil(painter, self.left)
        self._paint_pupil(painter, self.right)

    def _paint_pupil(self, painter, eye: EyeState) -> None:  # noqa: ANN001
        pos = eye.render_position()
        w = self._pupil_pixmap.width()
        h = self._pupil_pixmap.height()
        painter.drawPixmap(QPoint(int(pos.x - w / 2), int(pos.y - h / 2)), self._pupil_pixmap)

    def _paint_eye(self, painter, pixmap, socket: EyeSocket) -> None:  # noqa: ANN001
        w = pixmap.width()
        h = pixmap.height()
        painter.drawPixmap(QPoint(int(socket.x - w / 2), int(socket.y - h / 2)), pixmap)

    def stop(self) -> None:
        self._timer.stop()
