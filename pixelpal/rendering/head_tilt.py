"""Optional whole-head rotation toward the cursor.

Purely additive: when a char pack doesn't enable head_tilt, this
module is simply never instantiated by overlay_window.py. When
enabled, it rotates the *entire* body layer a few degrees around a
configured pivot point, giving a more analog feel than eye movement
alone.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtGui import QCursor, QTransform
from PySide6.QtWidgets import QLabel, QWidget

from pixelpal.charpack.schema import HeadTiltConfig
from pixelpal.utils.geometry import Point, clamp, head_tilt_angle


class HeadTiltController:
    """Applies a QTransform rotation to a target QLabel (the body layer)."""

    def __init__(
        self,
        target: QLabel,
        config: HeadTiltConfig,
        reference_widget: QWidget,
        tick_rate_fps: int = 30,
    ) -> None:
        self.target = target
        self.config = config
        self.reference_widget = reference_widget
        self._current_angle = 0.0

        self._timer = QTimer(target)
        self._timer.timeout.connect(self._on_tick)
        interval_ms = int(1000 / max(1, tick_rate_fps))
        self._timer.start(interval_ms)

    def _on_tick(self) -> None:
        global_cursor = QCursor.pos()
        local = self.reference_widget.mapFromGlobal(global_cursor)
        cursor_local = Point(float(local.x()), float(local.y()))
        pivot = Point(self.config.pivot_x, self.config.pivot_y)

        target_angle = head_tilt_angle(pivot, cursor_local, self.config.max_degrees)
        # Simple damping to match the pupils' smoothness rather than snapping.
        self._current_angle = clamp(
            self._current_angle + (target_angle - self._current_angle) * 0.12,
            -self.config.max_degrees,
            self.config.max_degrees,
        )

        transform = QTransform()
        transform.translate(self.config.pivot_x, self.config.pivot_y)
        transform.rotate(self._current_angle)
        transform.translate(-self.config.pivot_x, -self.config.pivot_y)
        # Note: pixmap-level rotation is intentionally left to the
        # caller via QGraphicsRotation/QLabel styling in richer
        # setups; storing the transform here keeps this class
        # framework-agnostic-ish and testable for its angle math while
        # overlay_window.py owns actual paint wiring.
        self.target.setProperty("head_tilt_transform", transform)
        self.target.update()

    def stop(self) -> None:
        self._timer.stop()
