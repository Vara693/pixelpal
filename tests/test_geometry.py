import math

import pytest

from pixelpal.utils.geometry import (
    Point,
    angle_to,
    clamp,
    damped_step,
    distance,
    head_tilt_angle,
    pupil_offset,
    within_glance_range,
)


def test_distance_basic():
    assert distance(Point(0, 0), Point(3, 4)) == pytest.approx(5.0)


def test_angle_to_right_is_zero():
    origin = Point(0, 0)
    assert angle_to(origin, Point(10, 0)) == pytest.approx(0.0)


def test_angle_to_up_is_positive_quarter_pi():
    origin = Point(0, 0)
    # screen y grows downward; "up" on screen means smaller y
    assert angle_to(origin, Point(0, -10)) == pytest.approx(math.pi / 2)


def test_clamp_within_range():
    assert clamp(5, 0, 10) == 5


def test_clamp_below_range():
    assert clamp(-5, 0, 10) == 0


def test_clamp_above_range():
    assert clamp(15, 0, 10) == 10


def test_clamp_handles_swapped_bounds():
    assert clamp(5, 10, 0) == 5


def test_pupil_offset_cursor_at_center_is_zero():
    center = Point(50, 50)
    offset = pupil_offset(center, Point(50, 50), socket_radius=10)
    assert offset.x == pytest.approx(0.0)
    assert offset.y == pytest.approx(0.0)


def test_pupil_offset_far_cursor_clamped_to_radius():
    center = Point(0, 0)
    offset = pupil_offset(center, Point(1000, 0), socket_radius=5)
    assert distance(Point(0, 0), offset) == pytest.approx(5.0, abs=1e-6)
    assert offset.x == pytest.approx(5.0, abs=1e-6)
    assert offset.y == pytest.approx(0.0, abs=1e-6)


def test_pupil_offset_near_cursor_proportional_not_clamped():
    center = Point(0, 0)
    # cursor is only 2px away, radius is 10 -> pupil should sit ~2px out, not snap to 10
    offset = pupil_offset(center, Point(2, 0), socket_radius=10)
    assert distance(Point(0, 0), offset) == pytest.approx(2.0, abs=1e-6)


def test_damped_step_moves_partway_toward_target():
    current = Point(0, 0)
    target = Point(10, 0)
    stepped = damped_step(current, target, damping=0.5)
    assert stepped.x == pytest.approx(5.0)


def test_damped_step_full_damping_snaps():
    current = Point(0, 0)
    target = Point(10, 5)
    stepped = damped_step(current, target, damping=1.0)
    assert stepped.x == pytest.approx(10.0)
    assert stepped.y == pytest.approx(5.0)


def test_damped_step_zero_damping_stays_put():
    current = Point(3, 3)
    target = Point(10, 10)
    stepped = damped_step(current, target, damping=0.0)
    assert stepped.x == pytest.approx(3.0)
    assert stepped.y == pytest.approx(3.0)


def test_damped_step_clamps_out_of_range_damping():
    current = Point(0, 0)
    target = Point(10, 0)
    stepped = damped_step(current, target, damping=5.0)  # should clamp to 1.0
    assert stepped.x == pytest.approx(10.0)


def test_head_tilt_angle_center_cursor_is_zero():
    pivot = Point(50, 50)
    angle = head_tilt_angle(pivot, Point(50, 999), max_degrees=6.0)
    assert angle == pytest.approx(0.0)


def test_head_tilt_angle_clamped_to_max_degrees():
    pivot = Point(0, 0)
    angle = head_tilt_angle(pivot, Point(100000, 0), max_degrees=6.0, reference_distance=400.0)
    assert angle == pytest.approx(6.0)


def test_head_tilt_angle_negative_side():
    pivot = Point(0, 0)
    angle = head_tilt_angle(pivot, Point(-200, 0), max_degrees=6.0, reference_distance=400.0)
    assert angle == pytest.approx(-3.0)


def test_within_glance_range_true_when_close():
    assert within_glance_range(Point(0, 0), Point(100, 0), threshold=200) is True


def test_within_glance_range_false_when_far():
    assert within_glance_range(Point(0, 0), Point(1000, 0), threshold=200) is False
