"""Persisted user settings via configparser.

Stored at the platform config dir (see utils.platform_utils.config_dir),
e.g. ~/.config/pixelpal/config.ini on Linux.
"""

from __future__ import annotations

import configparser
import os
import threading
from dataclasses import dataclass, field
from typing import Any

from pixelpal.utils.platform_utils import config_dir

CONFIG_FILENAME = "config.ini"

DEFAULTS: dict[str, dict[str, str]] = {
    "window": {
        "pos_x": "100",
        "pos_y": "100",
        "character": "cat",
    },
    "eyes": {
        "tick_rate_fps": "45",
    },
    "mood": {
        "enabled": "true",
        "cpu_signal": "true",
        "idle_time_signal": "true",
        "battery_signal": "true",
        "git_watch_signal": "false",
        "git_watch_repo": "",
        "idle_sleepy_minutes": "10",
    },
    "ears": {
        "audio_reactive": "false",
    },
    "reminders": {
        "enabled": "true",
    },
    "ollama": {
        "enabled": "false",
        "host": "http://localhost:11434",
        "model": "llama3.2",
    },
    "activity_tracker": {
        "enabled": "true",
    },
    "multipet": {
        "enabled": "false",
        "glance_distance_px": "600",
    },
}


class ConfigStore:
    """Thread-safe wrapper around a configparser.ConfigParser on disk."""

    def __init__(self, path: str | None = None) -> None:
        self._lock = threading.Lock()
        self.path = path or os.path.join(config_dir(), CONFIG_FILENAME)
        self._parser = configparser.ConfigParser()
        self._load_defaults()
        self._load_from_disk()

    def _load_defaults(self) -> None:
        for section, values in DEFAULTS.items():
            self._parser[section] = dict(values)

    def _load_from_disk(self) -> None:
        if os.path.exists(self.path):
            self._parser.read(self.path)

    def save(self) -> None:
        with self._lock:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as fh:
                self._parser.write(fh)

    # -- typed getters -----------------------------------------------
    def get(self, section: str, key: str, fallback: str | None = None) -> str:
        return self._parser.get(section, key, fallback=fallback)

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        return self._parser.getint(section, key, fallback=fallback)

    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        return self._parser.getfloat(section, key, fallback=fallback)

    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        return self._parser.getboolean(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: Any) -> None:
        with self._lock:
            if not self._parser.has_section(section):
                self._parser.add_section(section)
            self._parser.set(section, key, str(value))

    def set_and_save(self, section: str, key: str, value: Any) -> None:
        self.set(section, key, value)
        self.save()


@dataclass
class WindowState:
    pos_x: int
    pos_y: int
    character: str


def load_window_state(store: ConfigStore) -> WindowState:
    return WindowState(
        pos_x=store.get_int("window", "pos_x", 100),
        pos_y=store.get_int("window", "pos_y", 100),
        character=store.get("window", "character", "cat"),
    )


def save_window_state(store: ConfigStore, state: WindowState) -> None:
    store.set("window", "pos_x", state.pos_x)
    store.set("window", "pos_y", state.pos_y)
    store.set("window", "character", state.character)
    store.save()
