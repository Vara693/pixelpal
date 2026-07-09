"""Opt-in signal: watches a repo for new commits, and optionally a build/test
log file for failure markers.

This is poll-based (checks `git rev-parse HEAD` and log mtimes) rather
than using OS-level filesystem watchers, to keep the dependency list
small and behavior identical across platforms. Off by default; must be
explicitly enabled with a repo path in settings.
"""

from __future__ import annotations

import os
import subprocess

from pixelpal.mood.signals.base import MoodEvent, MoodSignal, SignalReading

FAILURE_MARKERS = ("FAILED", "BUILD FAILED", "Error:", "error:", "Traceback (most recent call last)")


class GitWatchSignal(MoodSignal):
    key = "git_watch_signal"

    def __init__(self, repo_path: str, build_log_path: str | None = None) -> None:
        self.repo_path = repo_path
        self.build_log_path = build_log_path
        self._last_head: str | None = None
        self._last_log_mtime: float | None = None

    def start(self) -> None:
        self._last_head = self._current_head()
        if self.build_log_path and os.path.isfile(self.build_log_path):
            self._last_log_mtime = os.path.getmtime(self.build_log_path)

    def _current_head(self) -> str | None:
        if not os.path.isdir(self.repo_path):
            return None
        try:
            result = subprocess.run(
                ["git", "-C", self.repo_path, "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=2.0,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _check_build_log(self) -> SignalReading | None:
        if not self.build_log_path or not os.path.isfile(self.build_log_path):
            return None

        mtime = os.path.getmtime(self.build_log_path)
        if self._last_log_mtime is not None and mtime <= self._last_log_mtime:
            return None
        self._last_log_mtime = mtime

        try:
            with open(self.build_log_path, "r", encoding="utf-8", errors="ignore") as fh:
                tail = fh.read()[-4000:]
        except OSError:
            return None

        if any(marker in tail for marker in FAILURE_MARKERS):
            return SignalReading(MoodEvent.BUILD_FAILED)
        return None

    def poll(self) -> SignalReading:
        build_reading = self._check_build_log()
        if build_reading is not None:
            return build_reading

        current = self._current_head()
        if current and current != self._last_head:
            self._last_head = current
            return SignalReading(MoodEvent.GIT_COMMIT, detail=current[:8])

        return SignalReading(MoodEvent.NONE)
