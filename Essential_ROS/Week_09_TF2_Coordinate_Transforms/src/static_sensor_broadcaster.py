#!/usr/bin/env python3
"""
Week 09 Lab: Static Transform Broadcaster
Broadcasts static coordinate transforms for LiDAR and Camera relative to base_link.
Follows REP 105 coordinate tree: base_link -> lidar_link, base_link -> camera_link.
"""

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster


def euler_to_quaternion(roll, pitch, yaw):
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


class StaticSensorBroadcaster(Node):
    def __init__(self):
        super().__init__('static_sensor_broadcaster')
        self._tf_publisher = StaticTransformBroadcaster(self)

        transforms = []

        # 1. LiDAR Transform: 0.08m forward, 0.095m up
        t_lidar = TransformStamped()
        t_lidar.header.stamp = self.get_clock().now().to_msg()
        t_lidar.header.frame_id = 'base_link'
        t_lidar.child_frame_id = 'lidar_link'
        t_lidar.transform.translation.x = 0.08
        t_lidar.transform.translation.y = 0.0
        t_lidar.transform.translation.z = 0.095
        t_lidar.transform.rotation.w = 1.0
        transforms.append(t_lidar)

        # 2. Camera Transform: 0.20m forward, 0.02m up
        t_camera = TransformStamped()
        t_camera.header.stamp = self.get_clock().now().to_msg()
        t_camera.header.frame_id = 'base_link'
        t_camera.child_frame_id = 'camera_link'
        t_camera.transform.translation.x = 0.20
        t_camera.transform.translation.y = 0.0
        t_camera.transform.translation.z = 0.02
        t_camera.transform.rotation.w = 1.0
        transforms.append(t_camera)

        # 3. Camera Optical Link (REP 103: X Right, Y Down, Z Forward)
        t_optical = TransformStamped()
        t_optical.header.stamp = self.get_clock().now().to_msg()
        t_optical.header.frame_id = 'camera_link'
        t_optical.child_frame_id = 'camera_optical_link'
        q = euler_to_quaternion(-math.pi/2, 0.0, -math.pi/2)
        t_optical.transform.rotation.x = q[0]
        t_optical.transform.rotation.y = q[1]
        t_optical.transform.rotation.z = q[2]
        t_optical.transform.rotation.w = q[3]
        transforms.append(t_optical)

        self._tf_publisher.sendTransform(transforms)
        self.get_logger().info('📡 [StaticSensorBroadcaster] Published static transforms for LiDAR, Camera, and Optical Frame.')


def main(args=None):
    rclpy.init(args=args)
    node = StaticSensorBroadcaster()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
