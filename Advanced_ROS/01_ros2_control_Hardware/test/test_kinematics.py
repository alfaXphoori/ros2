"""Unit tests for the diff-drive kinematics used in module 01 (README quiz, limits)."""
import math

import pytest

from amr_adv01.kinematics import (WHEEL_MAX_VELOCITY, forward_kinematics, inverse_kinematics,
                                  main, max_wheel_speed)


def test_quiz_answer_right_wheel():
    # README quiz: v = 0.5 m/s, w = 1.0 rad/s, r = 0.08 m, L = 0.24 m
    w_l, w_r = inverse_kinematics(0.5, 1.0, separation=0.24, radius=0.08)
    assert w_r == pytest.approx(7.75)
    assert w_l == pytest.approx(4.75)


def test_straight_and_spin_in_place():
    assert inverse_kinematics(0.4, 0.0) == pytest.approx((5.0, 5.0))
    w_l, w_r = inverse_kinematics(0.0, 1.0)
    assert w_l == pytest.approx(-w_r)
    assert w_r == pytest.approx(1.5)


@pytest.mark.parametrize('v,w', [(0.5, 1.0), (-0.2, 0.7), (0.0, -2.0), (0.31, 0.0)])
def test_forward_is_inverse_of_inverse(v, w):
    assert forward_kinematics(*inverse_kinematics(v, w)) == pytest.approx((v, w))


def test_limits_are_consistent():
    # body limits in config/diff_drive_controller.yaml: 0.5 m/s, 2.0 rad/s
    assert max_wheel_speed(0.5, 2.0) == pytest.approx(9.25)
    assert max_wheel_speed(0.5, 2.0) <= WHEEL_MAX_VELOCITY
    # the old config (1.0 m/s) needed 12.5 rad/s just driving straight
    assert max_wheel_speed(1.0, 0.0) > WHEEL_MAX_VELOCITY


def test_invalid_geometry():
    with pytest.raises(ValueError):
        inverse_kinematics(0.1, 0.1, separation=0.0)
    with pytest.raises(ValueError):
        forward_kinematics(1.0, 1.0, radius=-0.1)
    assert math.isfinite(inverse_kinematics(0.1, 0.1)[0])


def test_cli_prints_values(capsys):
    assert main(['0.5', '1.0', '--ros-args', '-r', '__node:=x']) == 0
    out = capsys.readouterr().out
    assert '7.750 rad/s' in out and '4.750 rad/s' in out
