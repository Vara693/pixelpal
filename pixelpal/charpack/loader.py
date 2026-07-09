"""Loads a character pack folder into a validated CharPackConfig + asset paths."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from pixelpal.charpack.schema import CharPackConfig, CharPackValidationError, parse_config

CONFIG_FILENAME = "config.json"


class CharPackLoadError(ValueError):
    """Raised when a char pack folder can't be loaded (missing files, bad json)."""


@dataclass
class LoadedCharPack:
    config: CharPackConfig
    root_dir: str

    def asset_path(self, relative: str) -> str:
        return os.path.join(self.root_dir, relative)

    def body_path(self) -> str:
        return self.asset_path(self.config.body)

    def pupil_path(self) -> str:
        return self.asset_path(self.config.eyes.pupil)

    def closed_eye_path(self) -> str | None:
        if self.config.eyes.closed:
            return self.asset_path(self.config.eyes.closed)
        return None

    def expression_path(self, mood: str) -> str | None:
        rel = self.config.expressions.get(mood)
        return self.asset_path(rel) if rel else None


def _read_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise CharPackLoadError(f"Invalid JSON in {path}: {exc}") from exc
    except OSError as exc:
        raise CharPackLoadError(f"Could not read {path}: {exc}") from exc


def _verify_assets_exist(pack: LoadedCharPack) -> None:
    missing = []
    for label, path in [
        ("body", pack.body_path()),
        ("eyes.pupil", pack.pupil_path()),
    ]:
        if not os.path.isfile(path):
            missing.append(f"{label} -> {path}")

    closed = pack.closed_eye_path()
    if closed and not os.path.isfile(closed):
        missing.append(f"eyes.closed -> {closed}")

    for mood, rel in pack.config.expressions.items():
        full = pack.asset_path(rel)
        if not os.path.isfile(full):
            missing.append(f"expressions.{mood} -> {full}")

    if missing:
        raise CharPackLoadError(
            "Char pack '"
            + pack.config.name
            + "' is missing referenced asset file(s):\n  "
            + "\n  ".join(missing)
        )


def load_char_pack(directory: str, verify_assets: bool = True) -> LoadedCharPack:
    """Load and validate a char pack from a directory.

    Raises CharPackLoadError / CharPackValidationError on any problem.
    """
    if not os.path.isdir(directory):
        raise CharPackLoadError(f"Char pack directory does not exist: {directory}")

    config_path = os.path.join(directory, CONFIG_FILENAME)
    if not os.path.isfile(config_path):
        raise CharPackLoadError(f"Missing {CONFIG_FILENAME} in {directory}")

    raw = _read_json(config_path)
    try:
        parsed = parse_config(raw)
    except CharPackValidationError as exc:
        raise CharPackLoadError(f"{directory}: {exc}") from exc

    pack = LoadedCharPack(config=parsed, root_dir=directory)
    if verify_assets:
        _verify_assets_exist(pack)
    return pack


def discover_char_packs(chars_dir: str) -> list[LoadedCharPack]:
    """Load every valid char pack found directly under chars_dir.

    Invalid packs are skipped (not raised) so one broken folder doesn't
    take down the whole app; callers that want strict behavior should
    call load_char_pack() directly instead.
    """
    packs: list[LoadedCharPack] = []
    if not os.path.isdir(chars_dir):
        return packs

    for entry in sorted(os.listdir(chars_dir)):
        full = os.path.join(chars_dir, entry)
        if not os.path.isdir(full):
            continue
        try:
            packs.append(load_char_pack(full))
        except (CharPackLoadError, CharPackValidationError):
            continue
    return packs
