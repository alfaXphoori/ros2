"""
Week 06: pure differential-drive kinematics (no ROS imports, unit-testable).

Conventions (REP 103): x forward, y left, z up, yaw counter-clockwise positive; SI units.
  r = wheel radius [m], L = wheel separation [m]
  Forward kinematics (FK): wheel speeds (w_left, w_right) [rad/s] -> body twist (v, omega)
  Inverse kinematics (IK): body twist (v, omega)               -> wheel speeds (w_left, w_right)
"""

import math


def inverse_kinematics(v, omega, wheel_separation, wheel_radius):
    """(v [m/s], omega [rad/s]) -> (w_left, w_right) [rad/s]."""
    v_right = v + omega * wheel_separation / 2.0
    v_left = v - omega * wheel_separation / 2.0
    return v_left / wheel_radius, v_right / wheel_radius


def forward_kinematics(w_left, w_right, wheel_separation, wheel_radius):
    """(w_left, w_right) [rad/s] -> (v [m/s], omega [rad/s])."""
    v_right = w_right * wheel_radius
    v_left = w_left * wheel_radius
    v = (v_right + v_left) / 2.0
    omega = (v_right - v_left) / wheel_separation
    return v, omega


def normalize_angle(theta):
    """Wrap an angle to [-pi, pi]."""
    return math.atan2(math.sin(theta), math.cos(theta))


def integrate_euler(x, y, theta, v, omega, dt):
    """Forward Euler: project the velocity along the heading at the START of the interval."""
    return (x + v * math.cos(theta) * dt,
            y + v * math.sin(theta) * dt,
            normalize_angle(theta + omega * dt))


def integrate_midpoint(x, y, theta, v, omega, dt):
    """Midpoint (2nd-order Runge-Kutta): use the heading halfway through the interval."""
    theta_mid = theta + omega * dt / 2.0
    return (x + v * math.cos(theta_mid) * dt,
            y + v * math.sin(theta_mid) * dt,
            normalize_angle(theta + omega * dt))


def integrate_exact(x, y, theta, v, omega, dt, eps=1e-9):
    """Exact arc for constant (v, omega) over dt (ICC circle, radius R = v / omega)."""
    if abs(omega) < eps:  # straight line: R -> infinity
        return integrate_euler(x, y, theta, v, 0.0, dt)
    radius = v / omega
    theta_new = theta + omega * dt
    return (x + radius * (math.sin(theta_new) - math.sin(theta)),
            y - radius * (math.cos(theta_new) - math.cos(theta)),
            normalize_angle(theta_new))


INTEGRATORS = {
    'euler': integrate_euler,
    'midpoint': integrate_midpoint,
    'exact': integrate_exact,
}


def yaw_to_quaternion(yaw):
    """Planar yaw -> quaternion (x, y, z, w) with roll = pitch = 0."""
    half = yaw * 0.5
    return (0.0, 0.0, math.sin(half), math.cos(half))
