"""Optional sound-reactive ear twitch.

Off by default (must be opted in via char pack's `ears.enabled` AND
the user's `[ears] audio_reactive` setting). Uses mood.audio_level for
a lightweight amplitude poll — not full audio capture/recording.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QLabel, QWidget

from pixelpal.mood.audio_level import AudioLevelMonitor

TWITCH_THRESHOLD = 0.35
TWITCH_COOLDOWN_MS = 400


class EarLayer(QWidget):
    """Wraps a QLabel ear sprite and nudges its rotation/offset on peaks.

    Kept intentionally simple: a "twitch" is a brief rotate-and-settle
    animation rather than continuous audio-driven motion, so it reads
    as a reaction rather than jitter.
    """

    def __init__(self, ear_label: QLabel, monitor: AudioLevelMonitor, poll_ms: int = 80) -> None:
        super().__init__(ear_label.parentWidget())
        self.ear_label = ear_label
        self.monitor = monitor
        self._on_cooldown = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_poll)
        self._timer.start(poll_ms)

    def _on_poll(self) -> None:
        if self._on_cooldown:
            return

        level = self.monitor.current_level()
        if level >= TWITCH_THRESHOLD:
            self._twitch()

    def _twitch(self) -> None:
        self._on_cooldown = True

        anim = QPropertyAnimation(self.ear_label, b"pos")
        start = self.ear_label.pos()
        nudged = start + type(start)(0, -4)

        anim.setDuration(90)
        anim.setStartValue(start)
        anim.setKeyValueAt(0.5, nudged)
        anim.setEndValue(start)
        anim.setEasingCurve(QEasingCurve.OutInQuad)
        anim.start()
        self._anim = anim  # keep a reference alive

        QTimer.singleShot(TWITCH_COOLDOWN_MS, self._clear_cooldown)

    def _clear_cooldown(self) -> None:
        self._on_cooldown = False

    def stop(self) -> None:
        self._timer.stop()
