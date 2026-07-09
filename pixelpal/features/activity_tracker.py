"""Aggregate input activity tracking, via pynput.

PRIVACY STANCE (also documented in README.md): this module records
*only* monotonically increasing counters (key-press count, click
count) and a "last activity" timestamp. It never stores, logs, or
transmits which keys were pressed, any typed text, or clipboard
content. There is no keylogging here — the only thing being measured
is "did something happen recently", used purely to drive the sleepy
mood signal.

Listeners run in pynput's own background thread; poll last_activity_time
from the UI thread as often as you like, it's just a float.
"""

from __future__ import annotations

import threading
import time


class ActivityTracker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.last_activity_time: float = time.monotonic()
        self.key_press_count: int = 0
        self.click_count: int = 0
        self._keyboard_listener = None
        self._mouse_listener = None
        self._running = False

    def _on_key_press(self, key) -> None:  # noqa: ANN001 - pynput callback signature
        with self._lock:
            self.key_press_count += 1
            self.last_activity_time = time.monotonic()

    def _on_click(self, x, y, button, pressed) -> None:  # noqa: ANN001
        if not pressed:
            return
        with self._lock:
            self.click_count += 1
            self.last_activity_time = time.monotonic()

    def _on_move(self, x, y) -> None:  # noqa: ANN001
        # Mouse motion still counts as "activity" for idle-time purposes,
        # but is not tallied into click_count (it's not a click).
        with self._lock:
            self.last_activity_time = time.monotonic()

    def start(self) -> None:
        if self._running:
            return
        try:
            from pynput import keyboard, mouse
        except Exception:
            # pynput can fail to init in headless/sandboxed CI
            # environments; degrade gracefully instead of crashing the
            # whole app, since the idle signal simply won't fire.
            self._running = False
            return

        self._keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
        self._mouse_listener = mouse.Listener(on_click=self._on_click, on_move=self._on_move)
        self._keyboard_listener.start()
        self._mouse_listener.start()
        self._running = True

    def stop(self) -> None:
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        if self._mouse_listener:
            self._mouse_listener.stop()
        self._running = False

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "key_press_count": self.key_press_count,
                "click_count": self.click_count,
                "seconds_since_activity": time.monotonic() - self.last_activity_time,
            }
