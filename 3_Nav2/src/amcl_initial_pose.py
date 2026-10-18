#!/usr/bin/env python3

"""
amcl_initial_pose.py
====================
Programmatically sets the initial pose estimate for AMCL localization in ROS 2 Nav2.
Publishes a geometry_msgs/PoseWithCovarianceStamped message to the '/initialpose' topic.

Usage:
  ros2 run ce_nav2 amcl_initial_pose.py --ros-args -p x:=0.0 -p y:=0.0 -p theta:=1.5708
"""

import sys
import math
import time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from geometry_msgs.msg import PoseWithCovarianceStamped, Quaternion


class InitialPosePublisher(Node):
    def __init__(self):
        super().__init__('amcl_initial_pose_publisher')

        # Declare parameters
        self.declare_parameter('x', 0.0)
        self.declare_parameter('y', 0.0)
        self.declare_parameter('z', 0.0)
        self.declare_parameter('theta', 0.0)  # yaw in radians
        self.declare_parameter('frame_id', 'map')
        self.declare_parameter('repeat_count', 5)
        self.declare_parameter('repeat_interval_sec', 0.5)

        self.x = self.get_parameter('x').get_parameter_value().double_value
        self.y = self.get_parameter('y').get_parameter_value().double_value
        self.z = self.get_parameter('z').get_parameter_value().double_value
        self.theta = self.get_parameter('theta').get_parameter_value().double_value
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value
        self.repeat_count = self.get_parameter('repeat_count').get_parameter_value().integer_value
        self.repeat_interval_sec = self.get_parameter('repeat_interval_sec').get_parameter_value().double_value

        # QoS Profile matching Nav2 /initialpose expectation (Transient Local durability)
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        self.publisher = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', qos_profile)

        self.get_logger().info("=" * 60)
        self.get_logger().info(" 📍 AMCL Initial Pose Publisher")
        self.get_logger().info(f"    Target Frame: {self.frame_id}")
        self.get_logger().info(f"    Position:     X={self.x:.2f} m, Y={self.y:.2f} m, Z={self.z:.2f} m")
        self.get_logger().info(f"    Yaw (theta):  {self.theta:.4f} rad ({math.degrees(self.theta):.1f} deg)")
        self.get_logger().info("=" * 60)

        # Allow subscribers (AMCL) to establish connection
        self.publish_counter = 0
        self.timer = self.create_timer(self.repeat_interval_sec, self.timer_callback)

    def euler_to_quaternion(self, roll: float, pitch: float, yaw: float) -> Quaternion:
        """Convert Euler angles (roll, pitch, yaw) to geometry_msgs Quaternion"""
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)

        q = Quaternion()
        q.w = cr * cp * cy + sr * sp * sy
        q.x = sr * cp * cy - cr * sp * sy
        q.y = cr * sp * cy + sr * cp * sy
        q.z = cr * cp * sy - sr * sp * cy
        return q

    def timer_callback(self):
        msg = PoseWithCovarianceStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id

        # Position
        msg.pose.pose.position.x = self.x
        msg.pose.pose.position.y = self.y
        msg.pose.pose.position.z = self.z

        # Orientation
        msg.pose.pose.orientation = self.euler_to_quaternion(0.0, 0.0, self.theta)

        # Covariance matrix (6x6 row-major: x, y, z, roll, pitch, yaw)
        # Small uncertainty for x, y, yaw
        covariance = [0.0] * 36
        covariance[0] = 0.25      # Var(x)
        covariance[7] = 0.25      # Var(y)
        covariance[35] = 0.0685   # Var(yaw) ~ (15 deg)^2
        msg.pose.covariance = covariance

        self.publisher.publish(msg)
        self.publish_counter += 1
        self.get_logger().info(f"[{self.publish_counter}/{self.repeat_count}] Published initial pose to /initialpose")

        if self.publish_counter >= self.repeat_count:
            self.get_logger().info("✅ Initial pose successfully delivered to AMCL. Exiting.")
            self.timer.cancel()
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = InitialPosePublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()
