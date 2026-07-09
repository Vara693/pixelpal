"""When another pet is nearby, briefly glance toward it instead of the
cursor. Isolated from core/ so multipet can be deleted/disabled
entirely with zero effect on single-pet operation.
"""

from __future__ import annotations

import random
import time

from pixelpal.multipet.registry import PetRecord, PetRegistry
from pixelpal.utils.geometry import Point, within_glance_range

GLANCE_DURATION_SECONDS = 2.5
GLANCE_CHANCE_PER_CHECK = 0.15  # avoid glancing literally every tick two pets are near


class GlanceController:
    """Decides, on each check(), whether the eye layer should target
    another pet's position instead of the live cursor for the next
    couple of seconds.
    """

    def __init__(self, registry: PetRegistry, glance_distance_px: float) -> None:
        self.registry = registry
        self.glance_distance_px = glance_distance_px
        self._glancing_until: float = 0.0
        self._glance_target: Point | None = None

    def is_glancing(self) -> bool:
        return time.monotonic() < self._glancing_until

    def current_target(self) -> Point | None:
        return self._glance_target if self.is_glancing() else None

    def check(self, my_global_pos: Point) -> None:
        if self.is_glancing():
            return

        nearby = self._find_nearby(my_global_pos)
        if not nearby:
            return

        if random.random() > GLANCE_CHANCE_PER_CHECK:
            return

        target = random.choice(nearby)
        self._glance_target = Point(float(target.x), float(target.y))
        self._glancing_until = time.monotonic() + GLANCE_DURATION_SECONDS

    def _find_nearby(self, my_global_pos: Point) -> list[PetRecord]:
        others = self.registry.others()
        return [
            o for o in others
            if within_glance_range(my_global_pos, Point(float(o.x), float(o.y)), self.glance_distance_px)
        ]
