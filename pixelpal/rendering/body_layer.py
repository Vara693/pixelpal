"""Body layer: static-hold -> play-once -> return-to-static idle cycle.

Rather than looping the GIF forever (which reads as "video clip"), the
default idle behavior holds on frame 0, plays the movie through once
every `wait_seconds`, then returns to the held frame — giving an idle
breathing/tail-flick feel instead of constant motion.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, QTimer, Qt
from PySide6.QtGui import QMovie, QPixmap
from PySide6.QtWidgets import QLabel, QWidget


class BodyLayer(QLabel):
    def __init__(self, body_path: str, wait_seconds: float, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setScaledContents(False)

        self._wait_ms = max(1, int(wait_seconds * 1000))
        self._is_gif = body_path.lower().endswith(".gif")

        if self._is_gif:
            self._movie = QMovie(body_path)
            self._movie.setCacheMode(QMovie.CacheAll)
            self._movie.jumpToFrame(0)
            self.setMovie(self._movie)
            self._movie.frameChanged.connect(self._on_frame_changed)

            self._cycle_timer = QTimer(self)
            self._cycle_timer.setSingleShot(True)
            self._cycle_timer.timeout.connect(self._play_once)
            self._cycle_timer.start(self._wait_ms)
        else:
            pixmap = QPixmap(body_path)
            self.setPixmap(pixmap)
            self._movie = None
            self._cycle_timer = None

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt override
        if self._movie is not None:
            return self._movie.currentPixmap().size()
        pixmap = self.pixmap()
        return pixmap.size() if pixmap else QSize(64, 64)

    def _play_once(self) -> None:
        if self._movie is None:
            return
        self._movie.jumpToFrame(0)
        self._movie.setPaused(False)
        self._movie.start()

    def _on_frame_changed(self, frame_number: int) -> None:
        if self._movie is None:
            return
        # QMovie with loopCount() == 0 (default: infinite) never fires
        # a "finished" signal for GIFs without an explicit loop count
        # metadata field, so detect "reached the last frame" manually
        # and pause there instead of looping forever.
        if frame_number == self._movie.frameCount() - 1:
            self._movie.setPaused(True)
            self._cycle_timer.start(self._wait_ms)

    def stop(self) -> None:
        if self._cycle_timer is not None:
            self._cycle_timer.stop()
        if self._movie is not None:
            self._movie.stop()
