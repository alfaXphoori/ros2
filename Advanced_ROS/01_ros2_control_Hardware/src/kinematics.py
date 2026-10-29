#!/usr/bin/env python3
"""
Advanced Module 01: differential-drive kinematics (the maths diff_drive_controller runs).

Inverse kinematics (body twist -> wheel angular velocities):
    w_L = (v - w*L/2) / r        w_R = (v + w*L/2) / r
Forward kinematics (wheel angular velocities -> body twist):
    v = r * (w_R + w_L) / 2      w = r * (w_R - w_L) / L

Run:  ros2 run amr_adv01 diff_drive_ik 0.5 1.0
      python3 Advanced_ROS/01_ros2_control_Hardware/src/kinematics.py 0.5 1.0
"""

import argparse
import sys

# Robot constants (urdf/diff_drive_ros2_control.xacro and config/diff_drive_controller.yaml)
WHEEL_SEPARATION = 0.24  # m
WHEEL_RADIUS = 0.08      # m
WHEEL_MAX_VELOCITY = 10.0  # rad/s, command-interface limit in the xacro


def inverse_kinematics(v, omega, separation=WHEEL_SEPARATION, radius=WHEEL_RADIUS):
    """Return (omega_left, omega_right) in rad/s for a body twist (v [m/s], omega [rad/s])."""
    if separation <= 0.0 or radius <= 0.0:
        raise ValueError('wheel separation and radius must be positive')
    v_left = v - omega * separation / 2.0
    v_right = v + omega * separation / 2.0
    return v_left / radius, v_right / radius


def forward_kinematics(omega_left, omega_right, separation=WHEEL_SEPARATION, radius=WHEEL_RADIUS):
    """Return (v [m/s], omega [rad/s]) from wheel angular velocities in rad/s."""
    if separation <= 0.0 or radius <= 0.0:
        raise ValueError('wheel separation and radius must be positive')
    v = radius * (omega_right + omega_left) / 2.0
    omega = radius * (omega_right - omega_left) / separation
    return v, omega


def max_wheel_speed(v_max, omega_max, separation=WHEEL_SEPARATION, radius=WHEEL_RADIUS):
    """Worst-case wheel speed (rad/s) when both body limits are reached at the same time."""
    return (abs(v_max) + abs(omega_max) * separation / 2.0) / radius


def main(argv=None):
    parser = argparse.ArgumentParser(description='Diff-drive inverse kinematics')
    parser.add_argument('v', type=float, nargs='?', default=0.5, help='linear velocity m/s')
    parser.add_argument('omega', type=float, nargs='?', default=1.0, help='angular velocity rad/s')
    parser.add_argument('--separation', type=float, default=WHEEL_SEPARATION)
    parser.add_argument('--radius', type=float, default=WHEEL_RADIUS)
    # ros2 run may append --ros-args ...; ignore anything after it
    args_in = sys.argv[1:] if argv is None else argv
    if '--ros-args' in args_in:
        args_in = args_in[:args_in.index('--ros-args')]
    args = parser.parse_args(args_in)

    w_l, w_r = inverse_kinematics(args.v, args.omega, args.separation, args.radius)
    print(f'L = {args.separation:.3f} m, r = {args.radius:.3f} m')
    print(f'v = {args.v:.3f} m/s, omega = {args.omega:.3f} rad/s')
    print(f'omega_L = ({args.v} - {args.omega}*{args.separation}/2) / {args.radius} = {w_l:.3f} rad/s')
    print(f'omega_R = ({args.v} + {args.omega}*{args.separation}/2) / {args.radius} = {w_r:.3f} rad/s')
    for name, w in (('left', w_l), ('right', w_r)):
        if abs(w) > WHEEL_MAX_VELOCITY:
            print(f'WARNING: {name} wheel {w:.2f} rad/s exceeds the +/-{WHEEL_MAX_VELOCITY} rad/s limit')
    return 0


if __name__ == '__main__':
    sys.exit(main())
