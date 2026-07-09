"""Local registry of active pet instances, backed by a JSON file in the
runtime dir. Each running PixelPal process writes its own position on
a timer and prunes stale entries (crashed/killed processes) by mtime.

Deliberately file-based rather than a real socket server: it's simpler,
cross-platform, and degrades to true no-op single-pet mode (zero
overhead) when multipet is disabled — see PROJECT_STRUCTURE.md notes.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass

from pixelpal.utils.platform_utils import runtime_dir

REGISTRY_FILENAME = "active_pets.json"
STALE_AFTER_SECONDS = 15.0


@dataclass
class PetRecord:
    pet_id: str
    character: str
    x: int
    y: int
    updated_at: float


class PetRegistry:
    def __init__(self, registry_path: str | None = None) -> None:
        self.pet_id = str(uuid.uuid4())
        self.path = registry_path or os.path.join(runtime_dir(), REGISTRY_FILENAME)

    def _read_all(self) -> dict[str, dict]:
        if not os.path.isfile(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return {}

    def _write_all(self, records: dict[str, dict]) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp_path = self.path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(records, fh)
        os.replace(tmp_path, self.path)

    def update_self(self, character: str, x: int, y: int) -> None:
        records = self._read_all()
        records[self.pet_id] = {
            "character": character,
            "x": x,
            "y": y,
            "updated_at": time.time(),
        }
        self._prune_stale(records)
        self._write_all(records)

    def remove_self(self) -> None:
        records = self._read_all()
        records.pop(self.pet_id, None)
        self._write_all(records)

    def _prune_stale(self, records: dict[str, dict]) -> None:
        now = time.time()
        stale = [
            pid for pid, r in records.items()
            if now - r.get("updated_at", 0) > STALE_AFTER_SECONDS
        ]
        for pid in stale:
            records.pop(pid, None)

    def others(self) -> list[PetRecord]:
        records = self._read_all()
        self._prune_stale(records)
        return [
            PetRecord(pet_id=pid, character=r["character"], x=r["x"], y=r["y"], updated_at=r["updated_at"])
            for pid, r in records.items()
            if pid != self.pet_id
        ]
