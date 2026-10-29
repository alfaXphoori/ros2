#!/usr/bin/env python3
"""
Week 11 helper: read the robot's TRUE pose from Gazebo (not from odometry).

  ros2 run amr_week11 ground_truth_pose            # prints x y yaw of diff_drive_robot

Gazebo publishes every model pose on /world/<world>/pose/info (gz.msgs.Pose_V).
Comparing it with /odom shows how much the wheel odometry drifts; tests use it
to check that Nav2 really drove the robot where it reported.
"""

import math
import re
import subprocess
import sys


def parse_pose_v(text, model):
    """Extract (x, y, yaw) of `model` from `gz topic -e` text output of a Pose_V."""
    start = text.find(f'name: "{model}"')
    if start < 0:
        raise ValueError(f'model {model!r} not found in pose message')
    end = text.find('\npose {', start)
    block = text[start:end if end > 0 else len(text)]

    def field(section, key):
        m = re.search(section + r' \{([^}]*)\}', block, re.S)
        if not m:
            return 0.0
        v = re.search(r'\b' + key + r': ([-+\d.eE]+)', m.group(1))
        return float(v.group(1)) if v else 0.0

    x, y = field('position', 'x'), field('position', 'y')
    qx, qy, qz = field('orientation', 'x'), field('orientation', 'y'), field('orientation', 'z')
    # protobuf text omits zero fields: missing w inside an orientation block means w = 0,
    # a missing orientation block means the identity rotation
    qw = field('orientation', 'w') if 'orientation {' in block else 1.0
    yaw = math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))
    return x, y, yaw


def robot_pose(model='diff_drive_robot', world='warehouse', timeout=10.0):
    out = subprocess.run(['gz', 'topic', '-e', '-n', '1', '-t', f'/world/{world}/pose/info'],
                         capture_output=True, text=True, timeout=timeout)
    return parse_pose_v(out.stdout, model)


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else 'diff_drive_robot'
    x, y, yaw = robot_pose(model)
    print(f'{model} ground truth: x={x:.3f} y={y:.3f} yaw={yaw:.3f} rad ({math.degrees(yaw):.1f} deg)')


if __name__ == '__main__':
    main()
