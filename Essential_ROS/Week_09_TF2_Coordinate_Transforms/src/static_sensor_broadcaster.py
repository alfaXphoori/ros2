#!/usr/bin/env python3
"""
Week 09 Lab: Static Transform Broadcaster
Broadcasts the static sensor transforms of the course robot on /tf_static:
  base_link -> lidar_link, base_link -> camera_link -> camera_optical_link

The values are identical to Week 07's diff_drive_robot.urdf. Use EITHER this node
OR robot_state_publisher with that URDF, never both: two publishers for the same
child frame break TF's "one source per transform" rule. tf_lab.launch.py
(tf_source:=broadcaster|urdf) starts exactly one of them.
"""

import math
import signal
import threading

import rclpy
from geometry_msgs.msg import TransformStamped
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster

# (parent, child, xyz, rpy) -- same numbers as amr_week07/urdf/diff_drive_robot.urdf
SENSOR_FRAMES = [
    ('base_link', 'lidar_link', (0.08, 0.0, 0.095), (0.0, 0.0, 0.0)),
    ('base_link', 'camera_link', (0.20, 0.0, 0.02), (0.0, 0.0, 0.0)),
    # REP 103 optical frame: z forward, x right, y down
    ('camera_link', 'camera_optical_link', (0.0, 0.0, 0.0), (-math.pi / 2, 0.0, -math.pi / 2)),
]


def euler_to_quaternion(roll, pitch, yaw):
    """Fixed-axis roll/pitch/yaw (URDF/tf convention) -> (x, y, z, w)."""
    r, p, y = roll * 0.5, pitch * 0.5, yaw * 0.5
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    return (
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * cy + sr * sp * sy
    )


def make_transform(stamp, parent, child, xyz, rpy):
    t = TransformStamped()
    t.header.stamp = stamp
    t.header.frame_id = parent
    t.child_frame_id = child
    t.transform.translation.x, t.transform.translation.y, t.transform.translation.z = xyz
    q = euler_to_quaternion(*rpy)
    (t.transform.rotation.x, t.transform.rotation.y,
     t.transform.rotation.z, t.transform.rotation.w) = q
    return t


class StaticSensorBroadcaster(Node):
    def __init__(self):
        super().__init__('static_sensor_broadcaster')
        self._tf_publisher = StaticTransformBroadcaster(self)

        stamp = self.get_clock().now().to_msg()
        transforms = [make_transform(stamp, *frame) for frame in SENSOR_FRAMES]
        # One call -> one latched (TRANSIENT_LOCAL) /tf_static message with all frames
        self._tf_publisher.sendTransform(transforms)
        self.get_logger().info(
            'Published static transforms: '
            + ', '.join(f'{p}->{c}' for p, c, _, _ in SENSOR_FRAMES))

        # Discovery takes a moment, so check once after 3 s for a conflicting source
        self._check_timer = self.create_timer(3.0, self._check_single_source)

    def _check_single_source(self):
        self._check_timer.cancel()
        if self.count_publishers('/robot_description') > 0:
            self.get_logger().error(
                'robot_state_publisher is running and already publishes these frames from '
                'the URDF. Stop one of the two sources (see tf_lab.launch.py tf_source:=...).')


def main(args=None):
    # Clean shutdown as in Week 2: SIGINT/SIGTERM only set a flag, the loop stops between
    # spin_once() calls (rclpy's own handler could shut the context down mid-callback).
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    node = StaticSensorBroadcaster()
    try:
        while not stop.is_set() and rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
    except ExternalShutdownException:
        pass
    finally:
        # stopping: ignore further signals (Python resets our handler at exit -> 2nd Ctrl+C = -2)
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal.SIG_IGN)
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
