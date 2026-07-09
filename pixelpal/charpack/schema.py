"""Validation for a character pack's config.json.

Deliberately dependency-light (no pydantic requirement) so char pack
validation can run in tests without pulling in extra packages. Only
`name`, `body`, and `eyes` are required — everything else is optional
per-character, matching PROJECT_STRUCTURE.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class CharPackValidationError(ValueError):
    """Raised when a config.json fails schema validation."""


@dataclass
class EyeSocket:
    x: float
    y: float
    radius: float
    damping: float = 0.15


@dataclass
class EyesConfig:
    left: EyeSocket
    right: EyeSocket
    pupil: str
    closed: str | None = None


@dataclass
class HeadTiltConfig:
    enabled: bool = False
    max_degrees: float = 6.0
    pivot_x: float = 0.0
    pivot_y: float = 0.0


@dataclass
class EarsConfig:
    enabled: bool = False


@dataclass
class CharPackConfig:
    name: str
    display_name: str
    body: str
    wait_seconds: float
    eyes: EyesConfig
    head_tilt: HeadTiltConfig
    ears: EarsConfig
    expressions: dict[str, str] = field(default_factory=dict)


def _require(d: dict, key: str, ctx: str) -> Any:
    if key not in d:
        raise CharPackValidationError(f"Missing required field '{key}' in {ctx}")
    return d[key]


def _require_number(d: dict, key: str, ctx: str) -> float:
    value = _require(d, key, ctx)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise CharPackValidationError(f"Field '{key}' in {ctx} must be a number")
    return float(value)


def _parse_eye_socket(d: dict, ctx: str) -> EyeSocket:
    if not isinstance(d, dict):
        raise CharPackValidationError(f"{ctx} must be an object")
    return EyeSocket(
        x=_require_number(d, "x", ctx),
        y=_require_number(d, "y", ctx),
        radius=_require_number(d, "radius", ctx),
        damping=float(d.get("damping", 0.15)),
    )


def _parse_eyes(d: dict) -> EyesConfig:
    if not isinstance(d, dict):
        raise CharPackValidationError("'eyes' must be an object")
    left = _parse_eye_socket(_require(d, "left", "eyes"), "eyes.left")
    right = _parse_eye_socket(_require(d, "right", "eyes"), "eyes.right")
    pupil = _require(d, "pupil", "eyes")
    if not isinstance(pupil, str):
        raise CharPackValidationError("'eyes.pupil' must be a string")
    closed = d.get("closed")
    if closed is not None and not isinstance(closed, str):
        raise CharPackValidationError("'eyes.closed' must be a string if present")
    return EyesConfig(left=left, right=right, pupil=pupil, closed=closed)


def _parse_head_tilt(d: dict | None) -> HeadTiltConfig:
    if not d:
        return HeadTiltConfig(enabled=False)
    if not isinstance(d, dict):
        raise CharPackValidationError("'head_tilt' must be an object")
    enabled = bool(d.get("enabled", False))
    max_degrees = float(d.get("max_degrees", 6.0))
    pivot = d.get("pivot", {}) or {}
    if not isinstance(pivot, dict):
        raise CharPackValidationError("'head_tilt.pivot' must be an object")
    return HeadTiltConfig(
        enabled=enabled,
        max_degrees=max_degrees,
        pivot_x=float(pivot.get("x", 0.0)),
        pivot_y=float(pivot.get("y", 0.0)),
    )


def _parse_ears(d: dict | None) -> EarsConfig:
    if not d:
        return EarsConfig(enabled=False)
    if not isinstance(d, dict):
        raise CharPackValidationError("'ears' must be an object")
    return EarsConfig(enabled=bool(d.get("enabled", False)))


def _parse_expressions(d: dict | None) -> dict[str, str]:
    if not d:
        return {}
    if not isinstance(d, dict):
        raise CharPackValidationError("'expressions' must be an object")
    for key, value in d.items():
        if not isinstance(value, str):
            raise CharPackValidationError(
                f"'expressions.{key}' must be a string path"
            )
    return dict(d)


def parse_config(raw: dict) -> CharPackConfig:
    """Validate and parse a raw config.json dict into a CharPackConfig.

    Raises CharPackValidationError with a human-readable message on any
    schema violation.
    """
    if not isinstance(raw, dict):
        raise CharPackValidationError("config.json root must be an object")

    name = _require(raw, "name", "config.json")
    if not isinstance(name, str) or not name.strip():
        raise CharPackValidationError("'name' must be a non-empty string")

    body = _require(raw, "body", "config.json")
    if not isinstance(body, str) or not body.strip():
        raise CharPackValidationError("'body' must be a non-empty string")

    eyes = _parse_eyes(_require(raw, "eyes", "config.json"))

    return CharPackConfig(
        name=name,
        display_name=str(raw.get("display_name", name.title())),
        body=body,
        wait_seconds=float(raw.get("wait_seconds", 5.0)),
        eyes=eyes,
        head_tilt=_parse_head_tilt(raw.get("head_tilt")),
        ears=_parse_ears(raw.get("ears")),
        expressions=_parse_expressions(raw.get("expressions")),
    )
