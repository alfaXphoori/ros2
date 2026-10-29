#!/usr/bin/env python3
"""
Week 09 Lab: TF2 Buffer & Listener Node
Transforms an obstacle point seen by the camera (camera_link frame) into the
robot base frame (base_link) every 0.5 s.

Lecture example: camera_link is 0.20 m ahead / 0.02 m above base_link, so the
point (1.2, 0.3, 0.0) in camera_link is (1.40, 0.30, 0.02) in base_link.
"""

import rclpy
import tf2_geometry_msgs  # noqa: F401  registers PointStamped with Buffer.transform()
import tf2_ros
from geometry_msgs.msg import PointStamped
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.time import Time

SOURCE_FRAME = 'camera_link'
TARGET_FRAME = 'base_link'
OBSTACLE_IN_CAMERA = (1.2, 0.3, 0.0)


class TfObstacleListener(Node):
    def __init__(self):
        super().__init__('tf_obstacle_listener')

        self.tf_buffer = tf2_ros.Buffer()
        # spin_thread defaults to False: the listener's /tf and /tf_static
        # subscriptions are added to THIS node and served by rclpy.spin(node) in main().
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # Periodic query timer (2 Hz)
        self.timer = self.create_timer(0.5, self.lookup_obstacle_position)
        self.get_logger().info('Listening for transforms and converting obstacle poses...')

    def lookup_obstacle_position(self):
        pt_in_camera = PointStamped()
        pt_in_camera.header.stamp = Time().to_msg()   # time 0 = latest available transform
        pt_in_camera.header.frame_id = SOURCE_FRAME
        (pt_in_camera.point.x, pt_in_camera.point.y,
         pt_in_camera.point.z) = OBSTACLE_IN_CAMERA
        try:
            # Non-blocking: inside a timer callback a timeout would only stall the executor
            pt_in_base = self.tf_buffer.transform(pt_in_camera, TARGET_FRAME)
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException) as e:
            self.get_logger().warn(f'TF lookup waiting: {e}')
            return
        self.get_logger().info(
            f'Obstacle transformed from {SOURCE_FRAME} to {TARGET_FRAME}: '
            f'X={pt_in_base.point.x:.2f}m, Y={pt_in_base.point.y:.2f}m, '
            f'Z={pt_in_base.point.z:.2f}m')


def main(args=None):
    rclpy.init(args=args)
    node = TfObstacleListener()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        try:
            node.destroy_node()
            rclpy.try_shutdown()
        except KeyboardInterrupt:
            pass  # a second SIGINT (Ctrl+C + ros2 launch forwarding) during cleanup


if __name__ == '__main__':
    main()
