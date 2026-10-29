#!/usr/bin/env python3
"""
Advanced Module 02: compare the tracker's /detected_dock_pose with the synthetic camera's
ground truth (/camera/tag_pose_ground_truth), matched by header stamp (same image).

  ros2 run amr_adv02 pose_error_monitor --ros-args -p count:=10
"""

import math

import numpy as np
import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

try:
    from amr_adv02 import vision_utils as vu
except ImportError:  # python3 src/pose_error_monitor.py
    import vision_utils as vu


def to_rt(msg):
    p, q = msg.pose.position, msg.pose.orientation
    return vu.quaternion_to_rotation(q.x, q.y, q.z, q.w), np.array([p.x, p.y, p.z])


class PoseErrorMonitor(Node):
    def __init__(self):
        super().__init__('pose_error_monitor')
        self.count = self.declare_parameter('count', 10).value
        self.truth = {}
        self.errors = []
        self.create_subscription(PoseStamped, 'camera/tag_pose_ground_truth', self.on_truth, 50)
        self.create_subscription(PoseStamped, 'detected_dock_pose', self.on_detected, 50)

    @staticmethod
    def key(msg):
        return (msg.header.stamp.sec, msg.header.stamp.nanosec)

    def on_truth(self, msg):
        self.truth[self.key(msg)] = msg
        if len(self.truth) > 100:
            self.truth.pop(next(iter(self.truth)))

    def on_detected(self, msg):
        gt = self.truth.get(self.key(msg))
        if gt is None:
            return
        R_d, t_d = to_rt(msg)
        R_g, t_g = to_rt(gt)
        e_pos = float(np.linalg.norm(t_d - t_g))
        e_rot = vu.rotation_angle_deg(R_g, R_d)
        self.errors.append((e_pos, e_rot))
        print(f'stamp {msg.header.stamp.sec}.{msg.header.stamp.nanosec:09d} '
              f'detected z={t_d[2]:.4f} m truth z={t_g[2]:.4f} m | '
              f'position error {e_pos * 1000:6.2f} mm  rotation error {e_rot:5.2f} deg',
              flush=True)

    def summary(self):
        if not self.errors:
            print('no matched detections', flush=True)
            return
        e = np.array(self.errors)
        print(f'{len(e)} frames: position error mean {e[:, 0].mean() * 1000:.2f} mm '
              f'max {e[:, 0].max() * 1000:.2f} mm | rotation error mean {e[:, 1].mean():.2f} deg '
              f'max {e[:, 1].max():.2f} deg', flush=True)


def main(args=None):
    rclpy.init(args=args)
    node = PoseErrorMonitor()
    try:
        while rclpy.ok() and len(node.errors) < node.count:
            rclpy.spin_once(node, timeout_sec=0.1)
        node.summary()
    except (KeyboardInterrupt, ExternalShutdownException):
        node.summary()
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    return 0 if node.errors and math.isfinite(node.errors[-1][0]) else 1


if __name__ == '__main__':
    main()
