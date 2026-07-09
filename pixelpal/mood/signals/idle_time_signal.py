"""Idle-time signal: fires SLEEPY after N minutes of no input.

Reads the shared aggregate activity counter maintained by
features.activity_tracker (event counts only — never key values, see
that module's docstring for the privacy stance) rather than polling
input devices itself, so there's exactly one place in the codebase
that touches pynput.
"""

from __future__ import annotations

import time

from pixelpal.features.activity_tracker import ActivityTracker
from pixelpal.mood.signals.base import MoodEvent, MoodSignal, SignalReading


class IdleTimeSignal(MoodSignal):
    key = "idle_time_signal"

    def __init__(self, tracker: ActivityTracker, idle_minutes: float = 10.0) -> None:
        self.tracker = tracker
        self.idle_seconds = idle_minutes * 60.0
        self._was_idle = False

    def poll(self) -> SignalReading:
        seconds_since_activity = time.monotonic() - self.tracker.last_activity_time

        if not self._was_idle and seconds_since_activity >= self.idle_seconds:
            self._was_idle = True
            return SignalReading(MoodEvent.IDLE_TIMEOUT)

        if self._was_idle and seconds_since_activity < 1.0:
            self._was_idle = False
            return SignalReading(MoodEvent.ACTIVITY_RESUMED)

        return SignalReading(MoodEvent.NONE)
