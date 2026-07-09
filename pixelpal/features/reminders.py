"""Scheduled one-shot and daily reminders.

Pure scheduling logic lives here (no Qt) so it's testable; the visual
banner that crosses the screen when a reminder fires lives in
features/banner_widget.py and is wired up by whatever owns the
QTimer (core/overlay_window.py or main.py).
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, time as dt_time, timedelta
from typing import Callable

from pixelpal.utils.platform_utils import config_dir

REMINDERS_FILENAME = "reminders.json"


@dataclass
class Reminder:
    id: str
    message: str
    kind: str  # "once" or "daily"
    # "once": ISO datetime string. "daily": "HH:MM" string.
    when: str
    enabled: bool = True
    last_fired_date: str | None = None  # ISO date, used to dedupe "daily" firings

    def as_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Reminder":
        return Reminder(**d)


def _reminders_path() -> str:
    return os.path.join(config_dir(), REMINDERS_FILENAME)


def load_reminders(path: str | None = None) -> list[Reminder]:
    path = path or _reminders_path()
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        return [Reminder.from_dict(r) for r in raw]
    except (OSError, json.JSONDecodeError, TypeError):
        return []


def save_reminders(reminders: list[Reminder], path: str | None = None) -> None:
    path = path or _reminders_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([r.as_dict() for r in reminders], fh, indent=2)


def add_daily_reminder(message: str, hour: int, minute: int, reminders: list[Reminder]) -> Reminder:
    reminder = Reminder(
        id=str(uuid.uuid4()),
        message=message,
        kind="daily",
        when=f"{hour:02d}:{minute:02d}",
    )
    reminders.append(reminder)
    return reminder


def add_one_shot_reminder(message: str, when: datetime, reminders: list[Reminder]) -> Reminder:
    reminder = Reminder(
        id=str(uuid.uuid4()),
        message=message,
        kind="once",
        when=when.isoformat(timespec="minutes"),
    )
    reminders.append(reminder)
    return reminder


class ReminderScheduler:
    """Checked periodically (e.g. every 30s via QTimer) to see if any
    reminder should fire right now. Framework-agnostic: fire_callback
    is any `Callable[[Reminder], None]`, so the Qt banner widget is
    just one possible consumer.
    """

    def __init__(self, reminders: list[Reminder], fire_callback: Callable[[Reminder], None]):
        self.reminders = reminders
        self.fire_callback = fire_callback

    def check(self, now: datetime | None = None) -> None:
        now = now or datetime.now()
        today = now.date().isoformat()

        for reminder in self.reminders:
            if not reminder.enabled:
                continue

            if reminder.kind == "once":
                try:
                    target = datetime.fromisoformat(reminder.when)
                except ValueError:
                    continue
                if now >= target and reminder.last_fired_date != today:
                    reminder.last_fired_date = today
                    reminder.enabled = False  # one-shot: don't fire again
                    self.fire_callback(reminder)

            elif reminder.kind == "daily":
                try:
                    hh, mm = (int(x) for x in reminder.when.split(":"))
                    target_time = dt_time(hour=hh, minute=mm)
                except ValueError:
                    continue
                if now.time() >= target_time and reminder.last_fired_date != today:
                    reminder.last_fired_date = today
                    self.fire_callback(reminder)
