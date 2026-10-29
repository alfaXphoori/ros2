#!/usr/bin/env python3
"""
Week 07: Inertia tensor calculator for URDF <inertial> blocks.

Prints a ready-to-paste <inertia .../> tag for the three primitive shapes
used in the course model. All tensors are about the centre of mass and
expressed in the link frame (no rotated inertial origin needed).

Usage:
  ros2 run amr_week07 inertia_calculator box <m> <d_x> <w_y> <h_z>
  ros2 run amr_week07 inertia_calculator cylinder <m> <r> <h> [--axis x|y|z]
  ros2 run amr_week07 inertia_calculator sphere <m> <r>
"""

import argparse
import sys


def box_inertia(m, d, w, h):
    """Solid box: d along X, w along Y, h along Z. Returns (ixx, iyy, izz)."""
    return (m * (w ** 2 + h ** 2) / 12.0,
            m * (d ** 2 + h ** 2) / 12.0,
            m * (d ** 2 + w ** 2) / 12.0)


def cylinder_inertia(m, r, h, axis='z'):
    """Solid cylinder whose symmetry (spin) axis is `axis`. Returns (ixx, iyy, izz)."""
    spin = 0.5 * m * r ** 2
    side = m * (3.0 * r ** 2 + h ** 2) / 12.0
    return {'x': (spin, side, side), 'y': (side, spin, side), 'z': (side, side, spin)}[axis]


def sphere_inertia(m, r):
    """Solid sphere. Returns (ixx, iyy, izz)."""
    i = 0.4 * m * r ** 2
    return (i, i, i)


def format_inertia(ixx, iyy, izz):
    return (f'<inertia ixx="{ixx:.6f}" ixy="0.0" ixz="0.0" '
            f'iyy="{iyy:.6f}" iyz="0.0" izz="{izz:.6f}"/>')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Inertia tensor for URDF primitives')
    sub = parser.add_subparsers(dest='shape', required=True)
    b = sub.add_parser('box')
    for name in ('m', 'd', 'w', 'h'):
        b.add_argument(name, type=float)
    c = sub.add_parser('cylinder')
    for name in ('m', 'r', 'h'):
        c.add_argument(name, type=float)
    c.add_argument('--axis', choices=['x', 'y', 'z'], default='z')
    s = sub.add_parser('sphere')
    for name in ('m', 'r'):
        s.add_argument(name, type=float)
    # Ignore ROS arguments appended by `ros2 run` (e.g. --ros-args)
    if argv is None:
        argv = sys.argv[1:]
    if '--ros-args' in argv:
        argv = argv[:argv.index('--ros-args')]
    args = parser.parse_args(argv)

    if args.shape == 'box':
        tensor = box_inertia(args.m, args.d, args.w, args.h)
    elif args.shape == 'cylinder':
        tensor = cylinder_inertia(args.m, args.r, args.h, args.axis)
    else:
        tensor = sphere_inertia(args.m, args.r)
    print(f'{args.shape}: Ixx={tensor[0]:.6f} Iyy={tensor[1]:.6f} Izz={tensor[2]:.6f} kg*m^2')
    print(format_inertia(*tensor))
    return 0


if __name__ == '__main__':
    sys.exit(main())
