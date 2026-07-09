"""Plugin interface for mood signal sources.

New signal sources (e.g. a future "Pomodoro timer ended" signal) can be
added by subclassing MoodSignal without touching state_machine.py at all
— the state machine only ever talks to this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class MoodEvent(str, Enum):
    """Events a signal can propose to the state machine.

    The state machine decides whether/how to act on a proposed event;
    signals don't set state directly, they just report what they see.
    """

    CPU_SPIKE = "cpu_spike"
    CPU_NORMAL = "cpu_normal"
    BATTERY_LOW = "battery_low"
    BATTERY_OK = "battery_ok"
    IDLE_TIMEOUT = "idle_timeout"
    ACTIVITY_RESUMED = "activity_resumed"
    GIT_COMMIT = "git_commit"
    BUILD_FAILED = "build_failed"
    NONE = "none"


@dataclass(frozen=True)
class SignalReading:
    event: MoodEvent
    detail: str = ""


class MoodSignal(ABC):
    """Base class for a pluggable mood signal source.

    Implementations should be cheap to poll — `poll()` is called
    periodically (see state_machine.MoodEngine) from the main/UI
    thread's timer loop by default, or from a background thread if the
    signal is expensive (subclasses document this themselves).
    """

    #: Unique key used in config.ini / settings UI to enable/disable this signal.
    key: str = "base"

    def start(self) -> None:
        """Called once when the signal source is enabled. Optional to override."""

    def stop(self) -> None:
        """Called once when the signal source is disabled. Optional to override."""

    @abstractmethod
    def poll(self) -> SignalReading:
        """Return the current reading. Called on a timer by MoodEngine."""
        raise NotImplementedError
