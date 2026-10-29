"""Unit tests for the pure differential-drive kinematics (no ROS graph needed)."""
import math

import pytest
from amr_week06.kinematics import (forward_kinematics, integrate_euler, integrate_exact,
                                   integrate_midpoint, inverse_kinematics, normalize_angle,
                                   yaw_to_quaternion)

L, R = 0.24, 0.08


def simulate(integrator, v, omega, duration, dt):
    x = y = th = 0.0
    for _ in range(round(duration / dt)):
        x, y, th = integrator(x, y, th, v, omega, dt)
    return x, y, th


def test_ik_straight_line_wheels_equal():
    wl, wr = inverse_kinematics(0.5, 0.0, 0.30, 0.10)
    assert wl == pytest.approx(5.0) and wr == pytest.approx(5.0)


def test_ik_spin_in_place_wheels_opposite():
    wl, wr = inverse_kinematics(0.0, 2.0, 0.30, 0.10)
    # v_R = +0.30 m/s, v_L = -0.30 m/s -> +-3 rad/s; CCW turn: right wheel faster
    assert wr == pytest.approx(3.0) and wl == pytest.approx(-3.0)


def test_fk_known_values():
    v, omega = forward_kinematics(2.5, 5.0, L, R)  # v_L = 0.2, v_R = 0.4 m/s
    assert v == pytest.approx(0.3)
    assert omega == pytest.approx(0.2 / L)


@pytest.mark.parametrize('v, omega', [(0.2, 0.0), (0.0, 0.5), (0.4, 0.2), (-0.3, -1.1)])
def test_fk_of_ik_is_identity(v, omega):
    assert forward_kinematics(*inverse_kinematics(v, omega, L, R), L, R) == pytest.approx(
        (v, omega))


@pytest.mark.parametrize('integrator', [integrate_euler, integrate_midpoint, integrate_exact])
def test_straight_line(integrator):
    x, y, th = simulate(integrator, 0.2, 0.0, 5.0, 0.05)
    assert x == pytest.approx(1.0) and y == pytest.approx(0.0, abs=1e-12)
    assert th == pytest.approx(0.0)


@pytest.mark.parametrize('integrator', [integrate_euler, integrate_midpoint, integrate_exact])
def test_spin_in_place(integrator):
    x, y, th = simulate(integrator, 0.0, 0.5, math.pi, math.pi / 60)  # quarter turn
    assert (x, y) == pytest.approx((0.0, 0.0), abs=1e-12)
    assert th == pytest.approx(math.pi / 2)


def test_exact_arc_quarter_circle():
    # v = 0.5, omega = 0.5 -> radius 1 m; after a quarter turn the robot is at (1, 1)
    x, y, th = integrate_exact(0.0, 0.0, 0.0, 0.5, 0.5, math.pi)
    assert (x, y, th) == pytest.approx((1.0, 1.0, math.pi / 2))


def test_midpoint_much_closer_to_exact_arc_than_euler():
    v, omega = 0.4, 0.8
    T = 0.75 * 2 * math.pi / omega  # three quarters of a circle
    dt = T / 120
    exact = simulate(integrate_exact, v, omega, T, dt)
    mid = simulate(integrate_midpoint, v, omega, T, dt)
    eul = simulate(integrate_euler, v, omega, T, dt)
    err_mid = math.dist(exact[:2], mid[:2])
    err_eul = math.dist(exact[:2], eul[:2])
    assert exact[:2] == pytest.approx((-0.5, 0.5))     # R = 0.5 m, 270 deg CCW
    assert err_mid < 1e-3                             # midpoint: only the chord-length error
    assert err_eul > 10 * err_mid                     # Euler drifts sideways


def test_midpoint_error_shrinks_quadratically():
    v, omega, T = 0.4, 0.8, 2.0
    exact = integrate_exact(0, 0, 0, v, omega, T)

    def err(dt):
        return math.dist(exact[:2], simulate(integrate_midpoint, v, omega, T, dt)[:2])
    assert err(0.05) / err(0.1) == pytest.approx(0.25, rel=0.05)


def test_yaw_to_quaternion():
    assert yaw_to_quaternion(0.0) == pytest.approx((0, 0, 0, 1))
    assert yaw_to_quaternion(math.pi) == pytest.approx((0, 0, 1, 0), abs=1e-12)
    q = yaw_to_quaternion(0.7)
    assert sum(c * c for c in q) == pytest.approx(1.0)


def test_normalize_angle():
    assert normalize_angle(3 * math.pi / 2) == pytest.approx(-math.pi / 2)
    assert normalize_angle(-3 * math.pi / 2) == pytest.approx(math.pi / 2)
