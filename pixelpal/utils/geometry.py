"""Pure geometry helpers used by the rendering engine.

Everything in this module is a plain function with no Qt / OS dependency,
so it can be unit tested in isolation (see tests/test_geometry.py).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    x: float
    y: float


def angle_to(origin: Point, target: Point) -> float:
    """Return the angle in radians from origin to target.

    0 rad points along +x (right), increasing counter-clockwise in
    standard math convention. Screen y grows downward, so we negate dy
    to keep the angle intuitive (up is positive).
    """
    dx = target.x - origin.x
    dy = origin.y - target.y
    return math.atan2(dy, dx)


def distance(a: Point, b: Point) -> float:
    return math.hypot(b.x - a.x, b.y - a.y)


def clamp(value: float, lo: float, hi: float) -> float:
    if lo > hi:
        lo, hi = hi, lo
    return max(lo, min(hi, value))


def pupil_offset(
    socket_center: Point,
    cursor: Point,
    socket_radius: float,
) -> Point:
    """Compute the raw (undamped) pupil offset from the socket center.

    The pupil is pulled toward the cursor direction but clamped so it
    never leaves the socket's radius — i.e. it slides around the inside
    edge of the eye rather than flying off toward a far-away cursor.
    """
    dx = cursor.x - socket_center.x
    dy = cursor.y - socket_center.y
    dist = math.hypot(dx, dy)

    if dist < 1e-6:
        return Point(0.0, 0.0)

    # Scale factor: full radius once the cursor is farther than the
    # radius itself, otherwise proportional to how close it already is.
    scale = min(1.0, dist / max(socket_radius, 1e-6))
    nx = dx / dist
    ny = dy / dist

    return Point(nx * socket_radius * scale, ny * socket_radius * scale)


def damped_step(current: Point, target: Point, damping: float) -> Point:
    """Move `current` a fraction `damping` of the way toward `target`.

    damping is expected in (0, 1]. Smaller values = smoother/slower
    pupil movement (more "analog" feel); 1.0 snaps instantly.
    """
    d = clamp(damping, 0.0, 1.0)
    return Point(
        current.x + (target.x - current.x) * d,
        current.y + (target.y - current.y) * d,
    )


def head_tilt_angle(
    pivot: Point,
    cursor: Point,
    max_degrees: float,
    reference_distance: float = 400.0,
) -> float:
    """Compute a clamped head-tilt angle (degrees) toward the cursor.

    The horizontal offset from the pivot is mapped linearly to a tilt
    angle, clamped to +/- max_degrees, so the head never over-rotates
    for cursors far off to one side.
    """
    dx = cursor.x - pivot.x
    ratio = clamp(dx / max(reference_distance, 1e-6), -1.0, 1.0)
    return ratio * max_degrees


def within_glance_range(a: Point, b: Point, threshold: float) -> bool:
    """Used by multipet.glance_behavior to decide if two pets are close."""
    return distance(a, b) <= threshold
