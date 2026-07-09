"""Mood state machine, driven by pluggable MoodSignal sources.

The state machine itself has zero knowledge of *how* a signal detects
things (CPU, battery, git, ...) — it only reacts to the MoodEvent
values each signal's poll() returns. This is what lets new signal
sources be added without any change here (see signals/base.py).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum

from pixelpal.mood.signals.base import MoodEvent, MoodSignal


class MoodState(str, Enum):
    IDLE = "idle"
    ALERT = "alert"
    SLEEPY = "sleepy"
    HAPPY = "happy"
    WORRIED = "worried"
    EXCITED = "excited"


# How long a transient state (ALERT, HAPPY, EXCITED) holds before
# fading back to IDLE if nothing else supersedes it, in seconds.
TRANSIENT_STATE_HOLD_SECONDS: dict[MoodState, float] = {
    MoodState.ALERT: 4.0,
    MoodState.HAPPY: 6.0,
    MoodState.EXCITED: 5.0,
}

# Sticky states persist until an explicit "resolved" event clears them
# (e.g. WORRIED from low battery clears on BATTERY_OK, not on a timer).
STICKY_STATES = {MoodState.WORRIED, MoodState.SLEEPY}


@dataclass
class MoodTransition:
    to_state: MoodState
    reason: MoodEvent


# Maps an incoming event to the state it requests, and whether that
# request is allowed to override a currently-sticky state.
_EVENT_TO_STATE: dict[MoodEvent, MoodTransition] = {
    MoodEvent.CPU_SPIKE: MoodTransition(MoodState.ALERT, MoodEvent.CPU_SPIKE),
    MoodEvent.BATTERY_LOW: MoodTransition(MoodState.WORRIED, MoodEvent.BATTERY_LOW),
    MoodEvent.IDLE_TIMEOUT: MoodTransition(MoodState.SLEEPY, MoodEvent.IDLE_TIMEOUT),
    MoodEvent.GIT_COMMIT: MoodTransition(MoodState.HAPPY, MoodEvent.GIT_COMMIT),
    MoodEvent.BUILD_FAILED: MoodTransition(MoodState.WORRIED, MoodEvent.BUILD_FAILED),
}

# Events that clear a specific sticky state back to IDLE.
_RESOLVING_EVENTS: dict[MoodEvent, MoodState] = {
    MoodEvent.BATTERY_OK: MoodState.WORRIED,
    MoodEvent.ACTIVITY_RESUMED: MoodState.SLEEPY,
}


class MoodEngine:
    """Owns the current MoodState and evaluates signal readings against it.

    Usage: construct with a list of MoodSignal instances, then call
    tick() periodically (e.g. from a QTimer in the app). tick() polls
    every signal, applies transition rules, and returns the current
    MoodState (which may be unchanged).
    """

    def __init__(self, signals: list[MoodSignal] | None = None) -> None:
        self.signals: list[MoodSignal] = signals or []
        self.state: MoodState = MoodState.IDLE
        self._state_entered_at: float = time.monotonic()
        self._sticky_reason: MoodEvent | None = None

    def add_signal(self, signal: MoodSignal) -> None:
        signal.start()
        self.signals.append(signal)

    def _set_state(self, new_state: MoodState, reason: MoodEvent) -> None:
        if new_state == self.state:
            return
        self.state = new_state
        self._state_entered_at = time.monotonic()
        self._sticky_reason = reason if new_state in STICKY_STATES else None

    def _seconds_in_state(self) -> float:
        return time.monotonic() - self._state_entered_at

    def _apply_event(self, event: MoodEvent) -> None:
        if event == MoodEvent.NONE:
            return

        # Resolving events (BATTERY_OK, ACTIVITY_RESUMED) clear a
        # matching sticky state back to idle.
        resolved_state = _RESOLVING_EVENTS.get(event)
        if resolved_state is not None:
            if self.state == resolved_state:
                self._set_state(MoodState.IDLE, event)
            return

        transition = _EVENT_TO_STATE.get(event)
        if transition is None:
            return

        # A currently-sticky state (WORRIED/SLEEPY) is only overridden
        # by another sticky-worthy event, never by a transient one,
        # so e.g. a CPU blip doesn't visually interrupt "low battery".
        if self.state in STICKY_STATES and transition.to_state not in STICKY_STATES:
            return

        self._set_state(transition.to_state, transition.reason)

    def _expire_transient_state(self) -> None:
        hold = TRANSIENT_STATE_HOLD_SECONDS.get(self.state)
        if hold is not None and self._seconds_in_state() >= hold:
            self._set_state(MoodState.IDLE, MoodEvent.NONE)

    def tick(self) -> MoodState:
        for signal in self.signals:
            reading = signal.poll()
            self._apply_event(reading.event)

        self._expire_transient_state()
        return self.state

    def force_state(self, state: MoodState) -> None:
        """Manual override, used by the debug toggle in the context menu."""
        self._set_state(state, MoodEvent.NONE)
