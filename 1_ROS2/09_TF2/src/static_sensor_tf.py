#!/usr/bin/env python3
"""
Tutorial 09 - TF2 Static Transform Broadcaster Node

Publishes fixed spatial transformations from the robot body ('base_link')
to attached perception sensors ('laser_frame' and 'camera_link').

Static transforms are latched on the '/tf_static' topic, minimizing network
bandwidth because their spatial relationship never changes during robot operation.
"""

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster


def euler_to_quaternion(roll: float, pitch: float, yaw: float):
    """
    Convert Euler angles (roll, pitch, yaw in radians) to Quaternion (x, y, z, w).
    Formula derived from standard ZYX rotation sequence.
    """
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    qx = sr * cp * cy - cr * sp * sy
    qy = cr * sp * cy + sr * cp * sy
    qz = cr * cp * sy - sr * sp * cy
    qw = cr * cp * cy + sr * cp * sy
    return qx, qy, qz, qw


class StaticSensorTFBroadcaster(Node):
    """Broadcaster node for static sensor transforms."""

    def __init__(self):
        super().__init__('static_sensor_tf_broadcaster')
        self.tf_static_broadcaster = StaticTransformBroadcaster(self)

        self.get_logger().info('📡 Initializing Static Sensor TF Broadcaster...')
        self.broadcast_sensor_transforms()

    def broadcast_sensor_transforms(self):
        """Build and publish static transforms for LiDAR and Camera sensors."""
        now = self.get_clock().now().to_msg()
        transforms = []

        # -------------------------------------------------------------
        # 1. Transform: base_link -> laser_frame (360° LiDAR Scanner)
        # Position: Center top of chassis (x=0.0m, y=0.0m, z=0.095m)
        # Orientation: Aligned with robot forward heading (yaw=0 rad)
        # -------------------------------------------------------------
        t_laser = TransformStamped()
        t_laser.header.stamp = now
        t_laser.header.frame_id = 'base_link'
        t_laser.child_frame_id = 'laser_frame'

        t_laser.transform.translation.x = 0.0
        t_laser.transform.translation.y = 0.0
        t_laser.transform.translation.z = 0.095

        qx, qy, qz, qw = euler_to_quaternion(0.0, 0.0, 0.0)
        t_laser.transform.rotation.x = qx
        t_laser.transform.rotation.y = qy
        t_laser.transform.rotation.z = qz
        t_laser.transform.rotation.w = qw
        transforms.append(t_laser)

        # -------------------------------------------------------------
        # 2. Transform: base_link -> camera_link (Front RGB Camera)
        # Position: Front top bumper (x=0.20m, y=0.0m, z=0.07m)
        # Orientation: Facing forward along X-axis
        # -------------------------------------------------------------
        t_camera = TransformStamped()
        t_camera.header.stamp = now
        t_camera.header.frame_id = 'base_link'
        t_camera.child_frame_id = 'camera_link'

        t_camera.transform.translation.x = 0.20
        t_camera.transform.translation.y = 0.0
        t_camera.transform.translation.z = 0.07

        qx, qy, qz, qw = euler_to_quaternion(0.0, 0.0, 0.0)
        t_camera.transform.rotation.x = qx
        t_camera.transform.rotation.y = qy
        t_camera.transform.rotation.z = qz
        t_camera.transform.rotation.w = qw
        transforms.append(t_camera)

        # -------------------------------------------------------------
        # 3. Transform: camera_link -> camera_optical_frame
        # Standard ROS REP 103 optical frame:
        #   Z: Forward into scene, X: Right, Y: Down
        # Rotation: Roll = -pi/2, Pitch = 0, Yaw = -pi/2
        # -------------------------------------------------------------
        t_optical = TransformStamped()
        t_optical.header.stamp = now
        t_optical.header.frame_id = 'camera_link'
        t_optical.child_frame_id = 'camera_optical_frame'

        t_optical.transform.translation.x = 0.0
        t_optical.transform.translation.y = 0.0
        t_optical.transform.translation.z = 0.0

        qx, qy, qz, qw = euler_to_quaternion(-math.pi / 2, 0.0, -math.pi / 2)
        t_optical.transform.rotation.x = qx
        t_optical.transform.rotation.y = qy
        t_optical.transform.rotation.z = qz
        t_optical.transform.rotation.w = qw
        transforms.append(t_optical)

        # Send all static transforms simultaneously
        self.tf_static_broadcaster.sendTransform(transforms)

        self.get_logger().info('✅ Published Static Transforms:')
        self.get_logger().info('   • base_link -> laser_frame [x=0.00, y=0.00, z=0.095]')
        self.get_logger().info('   • base_link -> camera_link [x=0.20, y=0.00, z=0.070]')
        self.get_logger().info('   • camera_link -> camera_optical_frame [REP 103 optical]')


def main(args=None):
    rclpy.init(args=args)
    node = StaticSensorTFBroadcaster()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
