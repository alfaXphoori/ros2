#!/usr/bin/env python3
"""
Advanced Module 06 helpers: load the capstone configuration and derive the geometry that the
launch file, the mission executor and the tests must agree on.

Pure Python (no ROS graph), so every function is unit-tested in test/test_capstone_config.py.
"""

import copy
import math
import os

import yaml

PACKAGE = 'amr_adv06'


def share_file(*parts):
    """Path of an installed file of this package (config/..., launch/...)."""
    from ament_index_python.packages import get_package_share_directory
    return os.path.join(get_package_share_directory(PACKAGE), *parts)


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def load_mission(path=None):
    """Mission definition: home, stations, dock, estop_test (config/capstone_mission.yaml)."""
    return load_yaml(path or share_file('config', 'capstone_mission.yaml'))


def load_kpis(path=None):
    """KPI targets + rubric (config/kpi_targets.yaml)."""
    return load_yaml(path or share_file('config', 'kpi_targets.yaml'))


def deep_merge(base, override):
    """Return a copy of `base` with `override` merged in recursively.

    dicts are merged key by key; any other value (lists included) in `override` replaces the
    one in `base`. Used to layer config/nav2_overrides.yaml on top of the Week 14 params.
    """
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def merge_yaml_files(base_path, override_path, out_path):
    merged = deep_merge(load_yaml(base_path), load_yaml(override_path))
    with open(out_path, 'w') as f:
        yaml.safe_dump(merged, f, sort_keys=False)
    return merged


def dock_pose(dock):
    """(x, y, yaw_rad) of the dock (= base_footprint pose when docked)."""
    return float(dock['x']), float(dock['y']), math.radians(float(dock['yaw_deg']))


def tag_world(dock):
    """[x, y, z, yaw] of the AprilTag in the world frame for amr_adv02 synthetic_tag_camera.

    The tag sits `tag_beyond_dock` beyond the dock pose along the dock x axis; its outward
    normal points back towards the approaching robot (yaw + pi)."""
    x, y, yaw = dock_pose(dock)
    d = float(dock['tag_beyond_dock'])
    return [x + d * math.cos(yaw), y + d * math.sin(yaw), float(dock['tag_height']),
            math.atan2(math.sin(yaw + math.pi), math.cos(yaw + math.pi))]


def staging_pose(dock, staging_x_offset=-0.7):
    """Staging pose used by opennav_docking SimpleChargingDock (offset along the dock x)."""
    x, y, yaw = dock_pose(dock)
    return x + staging_x_offset * math.cos(yaw), y + staging_x_offset * math.sin(yaw), yaw


def ahead(x, y, yaw, distance):
    """Point `distance` metres ahead of the pose (x, y, yaw)."""
    return x + distance * math.cos(yaw), y + distance * math.sin(yaw)


def gap_to_face(face_xy, heading, robot_x, robot_y, robot_yaw, bumper=0.20):
    """Free distance (m) between the robot's front bumper and an obstacle face.

    face_xy: a point on the obstacle face, heading: the face normal pointing away from the
    robot (the robot heading when the obstacle was placed). Negative = contact/penetration."""
    bx, by = ahead(robot_x, robot_y, robot_yaw, bumper)
    return (face_xy[0] - bx) * math.cos(heading) + (face_xy[1] - by) * math.sin(heading)


def invert_transform(t, q):
    """Inverse of the rigid transform (translation t, quaternion q=(x,y,z,w)).

    Returns (t_inv, q_inv) such that applying (t, q) then (t_inv, q_inv) is the identity."""
    qx, qy, qz, qw = q
    n = math.sqrt(qx * qx + qy * qy + qz * qz + qw * qw)
    qx, qy, qz, qw = qx / n, qy / n, qz / n, qw / n
    q_inv = (-qx, -qy, -qz, qw)
    # rotate -t by q_inv:  v' = v + 2w(u x v) + 2 u x (u x v), u = vector part of q_inv
    vx, vy, vz = -t[0], -t[1], -t[2]
    ux, uy, uz, w = q_inv
    cx, cy, cz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    ccx, ccy, ccz = uy * cz - uz * cy, uz * cx - ux * cz, ux * cy - uy * cx
    t_inv = (vx + 2 * (w * cx + ccx), vy + 2 * (w * cy + ccy), vz + 2 * (w * cz + ccz))
    return t_inv, q_inv


def yaw_from_quaternion(qx, qy, qz, qw):
    return math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))


def pose_error(robot_xyyaw, dock_xyyaw):
    """(position, lateral, longitudinal [m], yaw [rad]) error in the dock frame.

    Re-uses the module 03 implementation (amr_adv03.dock_client.pose_error)."""
    from amr_adv03.dock_client import pose_error as module03_pose_error
    return module03_pose_error(robot_xyyaw, dock_xyyaw)


def kpi_verdict(value, target, lower_is_better=True):
    """'PASS' if value meets the passing target, else 'FAIL' (None value -> 'N/A')."""
    if value is None:
        return 'N/A'
    ok = value <= target if lower_is_better else value >= target
    return 'PASS' if ok else 'FAIL'
