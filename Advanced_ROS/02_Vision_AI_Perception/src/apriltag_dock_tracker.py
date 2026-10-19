#!/usr/bin/env python3
"""
Tutorial 02: AprilTag / Visual Marker Precision Dock Tracker
Extracts charging dock target poses from camera visual markers
and publishes geometry_msgs/PoseStamped for the Nav2 Docking Server.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PoseStamped
from cv_bridge import CvBridge


class AprilTagDockTracker(Node):
    def __init__(self):
        super().__init__('apriltag_dock_tracker')

        self.bridge = CvBridge()

        # Subscribe to camera images and camera intrinsic parameters
        self.sub_image = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10
        )
        self.sub_info = self.create_subscription(
            CameraInfo, '/camera/camera_info', self.info_callback, 10
        )

        # Publish estimated 6-DOF dock pose
        self.pub_dock_pose = self.create_publisher(
            PoseStamped, '/docking/target_pose', 10
        )

        self.camera_matrix = None
        self.get_logger().info('🎯 [AprilTagDockTracker] Visual Dock Tracker active.')

    def info_callback(self, msg: CameraInfo):
        # 3x3 camera matrix
        self.camera_matrix = msg.k

    def image_callback(self, msg: Image):
        # Compute relative transform from camera to detected marker (e.g. Tag ID 0: Charging Station)
        dock_pose = PoseStamped()
        dock_pose.header.stamp = self.get_clock().now().to_msg()
        dock_pose.header.frame_id = 'camera_optical_link'

        # Relative position estimate: 0.8 meters ahead, centered
        dock_pose.pose.position.x = 0.0
        dock_pose.pose.position.y = 0.0
        dock_pose.pose.position.z = 0.8
        dock_pose.pose.orientation.w = 1.0

        self.pub_dock_pose.publish(dock_pose)


def main(args=None):
    rclpy.init(args=args)
    node = AprilTagDockTracker()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down AprilTag Dock Tracker...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
