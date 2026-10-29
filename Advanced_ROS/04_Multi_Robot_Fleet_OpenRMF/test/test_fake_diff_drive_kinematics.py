"""Unit tests for the pure kinematics in fake_diff_drive (no ROS graph needed)."""
import math

import pytest

from amr_adv04.fake_diff_drive import integrate_pose, wheel_rates, yaw_to_quaternion


def test_straight_line():
    x, y, yaw = integrate_pose(0.0, 0.0, 0.0, 0.5, 0.0, 2.0)
    assert (x, y, yaw) == pytest.approx((1.0, 0.0, 0.0))


def test_straight_line_heading_90deg():
    x, y, yaw = integrate_pose(1.0, 2.0, math.pi / 2, 0.5, 0.0, 2.0)
    assert (x, y) == pytest.approx((1.0, 3.0))


def test_quarter_circle_is_exact():
    # v = 0.5 m/s, w = 0.5 rad/s -> radius 1 m; pi seconds = 90 deg turn
    x, y, yaw = integrate_pose(0.0, 0.0, 0.0, 0.5, 0.5, math.pi)
    assert (x, y, yaw) == pytest.approx((1.0, 1.0, math.pi / 2))


def test_many_small_steps_equal_one_big_step():
    pose = (0.0, 0.0, 0.0)
    for _ in range(100):
        pose = integrate_pose(*pose, 0.3, -0.4, 0.05)
    assert pose == pytest.approx(integrate_pose(0.0, 0.0, 0.0, 0.3, -0.4, 5.0))


def test_spin_in_place_wheels_opposite():
    left, right = wheel_rates(0.0, 1.0, 0.08, 0.24)
    assert left == pytest.approx(-1.5)
    assert right == pytest.approx(1.5)


def test_forward_wheels_equal():
    left, right = wheel_rates(0.4, 0.0, 0.08, 0.24)
    assert left == pytest.approx(5.0) and right == pytest.approx(5.0)


def test_yaw_quaternion_unit_norm():
    for yaw in (-3.0, -1.0, 0.0, 0.7, 3.1):
        q = yaw_to_quaternion(yaw)
        assert sum(c * c for c in q) == pytest.approx(1.0)
        assert 2 * math.atan2(q[2], q[3]) == pytest.approx(yaw)
