import pytest

from pixelpal.charpack.schema import CharPackValidationError, parse_config

MINIMAL_VALID = {
    "name": "owl",
    "body": "body.gif",
    "eyes": {
        "left": {"x": 34, "y": 28, "radius": 4},
        "right": {"x": 58, "y": 28, "radius": 4},
        "pupil": "pupil.png",
    },
}

FULL_VALID = {
    "name": "fox",
    "display_name": "Fox",
    "body": "body.gif",
    "wait_seconds": 5,
    "eyes": {
        "left": {"x": 34, "y": 28, "radius": 4, "damping": 0.15},
        "right": {"x": 58, "y": 28, "radius": 4, "damping": 0.15},
        "pupil": "pupil.png",
        "closed": "eye_closed.png",
    },
    "head_tilt": {"enabled": True, "max_degrees": 6, "pivot": {"x": 46, "y": 40}},
    "ears": {"enabled": False},
    "expressions": {
        "happy": {"path": "expressions/happy.png", "x": 46, "y": 55},
        "worried": {"path": "expressions/worried.png", "x": 46, "y": 55},
        "sleepy": {"path": "expressions/sleepy.png", "x": 46, "y": 55},
    },
}


def test_minimal_valid_config_parses():
    config = parse_config(MINIMAL_VALID)
    assert config.name == "owl"
    assert config.display_name == "Owl"
    assert config.eyes.left.x == 34
    assert config.head_tilt.enabled is False
    assert config.expressions == {}


def test_full_valid_config_parses():
    config = parse_config(FULL_VALID)
    assert config.name == "fox"
    assert config.head_tilt.enabled is True
    assert config.head_tilt.max_degrees == 6
    assert config.head_tilt.pivot_x == 46
    assert config.eyes.closed == "eye_closed.png"
    assert config.expressions["happy"].path == "expressions/happy.png"
    assert config.expressions["happy"].x == 46
    assert config.expressions["happy"].y == 55


def test_missing_name_raises():
    bad = dict(MINIMAL_VALID)
    del bad["name"]
    with pytest.raises(CharPackValidationError):
        parse_config(bad)


def test_missing_body_raises():
    bad = dict(MINIMAL_VALID)
    del bad["body"]
    with pytest.raises(CharPackValidationError):
        parse_config(bad)


def test_missing_eyes_raises():
    bad = dict(MINIMAL_VALID)
    del bad["eyes"]
    with pytest.raises(CharPackValidationError):
        parse_config(bad)


def test_missing_eye_socket_field_raises():
    bad = {
        "name": "owl",
        "body": "body.gif",
        "eyes": {
            "left": {"x": 34, "y": 28},  # missing radius
            "right": {"x": 58, "y": 28, "radius": 4},
            "pupil": "pupil.png",
        },
    }
    with pytest.raises(CharPackValidationError):
        parse_config(bad)


def test_missing_pupil_raises():
    bad = {
        "name": "owl",
        "body": "body.gif",
        "eyes": {
            "left": {"x": 34, "y": 28, "radius": 4},
            "right": {"x": 58, "y": 28, "radius": 4},
        },
    }
    with pytest.raises(CharPackValidationError):
        parse_config(bad)


def test_non_numeric_eye_coordinate_raises():
    bad = {
        "name": "owl",
        "body": "body.gif",
        "eyes": {
            "left": {"x": "not-a-number", "y": 28, "radius": 4},
            "right": {"x": 58, "y": 28, "radius": 4},
            "pupil": "pupil.png",
        },
    }
    with pytest.raises(CharPackValidationError):
        parse_config(bad)


def test_empty_name_raises():
    bad = dict(MINIMAL_VALID)
    bad["name"] = "   "
    with pytest.raises(CharPackValidationError):
        parse_config(bad)


def test_root_must_be_object():
    with pytest.raises(CharPackValidationError):
        parse_config([])  # type: ignore[arg-type]


def test_expressions_values_must_be_strings():
    bad = dict(FULL_VALID)
    bad["expressions"] = {"happy": 123}
    with pytest.raises(CharPackValidationError):
        parse_config(bad)


def test_head_tilt_defaults_when_absent():
    minimal = dict(MINIMAL_VALID)
    config = parse_config(minimal)
    assert config.head_tilt.enabled is False
    assert config.head_tilt.max_degrees == 6.0
