#!/usr/bin/env python3
"""
Week 06 Lab: Differential Drive Kinematics & Odometry Calculator
Demonstrates Forward Kinematics (Twist -> Wheel Speeds)
and Inverse Kinematics / Dead Reckoning (Wheel Speeds -> Odometry).
Follows REP 103 (m, rad, s) and REP 105 (odom -> base_footprint).
"""

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
import tf_transformations


class DiffDriveKinematics(Node):
    def __init__(self):
        super().__init__('diff_drive_kinematics')

        # Robot Physical Parameters
        self.declare_parameter('wheel_separation', 0.24)  # L (meters)
        self.declare_parameter('wheel_radius', 0.08)       # r (meters)

        self.L = self.get_parameter('wheel_separation').value
        self.r = self.get_parameter('wheel_radius').value

        # Robot State (x, y, theta)
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_time = self.get_clock().now()

        # Current commanded wheel speeds (rad/s)
        self.w_left = 0.0
        self.w_right = 0.0

        # Subscriptions & Publishers
        self.sub_cmd_vel = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_vel_callback, 10
        )
        self.pub_odom = self.create_publisher(Odometry, '/odom_calculated', 10)

        # 20 Hz update loop for Dead Reckoning
        self.timer = self.create_timer(0.05, self.update_odometry)

        self.get_logger().info(f'🤖 [DiffDriveKinematics] Ready: L={self.L}m, r={self.r}m')

    def cmd_vel_callback(self, msg: Twist):
        # 1. Forward Kinematics: (v, omega) -> (v_left, v_right)
        v = msg.linear.x
        omega = msg.angular.z

        v_right = v + (omega * self.L / 2.0)
        v_left = v - (omega * self.L / 2.0)

        # Convert linear wheel velocities to angular velocities (rad/s)
        self.w_right = v_right / self.r
        self.w_left = v_left / self.r

    def update_odometry(self):
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        self.last_time = current_time

        if dt <= 0.0:
            return

        # 2. Inverse Kinematics: (w_left, w_right) -> (v, omega)
        v_right = self.w_right * self.r
        v_left = self.w_left * self.r

        v = (v_right + v_left) / 2.0
        omega = (v_right - v_left) / self.L

        # Numerical Integration (Euler method)
        delta_x = v * math.cos(self.theta) * dt
        delta_y = v * math.sin(self.theta) * dt
        delta_theta = omega * dt

        self.x += delta_x
        self.y += delta_y
        self.theta += delta_theta

        # Normalize theta to [-pi, pi]
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

        # Publish Odometry Message
        odom_msg = Odometry()
        odom_msg.header.stamp = current_time.to_msg()
        odom_msg.header.frame_id = 'odom'
        odom_msg.child_frame_id = 'base_footprint'

        odom_msg.pose.pose.position.x = self.x
        odom_msg.pose.pose.position.y = self.y
        odom_msg.pose.pose.position.z = 0.0

        # Euler to Quaternion
        q = tf_transformations.quaternion_from_euler(0, 0, self.theta)
        odom_msg.pose.pose.orientation.x = q[0]
        odom_msg.pose.pose.orientation.y = q[1]
        odom_msg.pose.pose.orientation.z = q[2]
        odom_msg.pose.pose.orientation.w = q[3]

        odom_msg.twist.twist.linear.x = v
        odom_msg.twist.twist.angular.z = omega

        self.pub_odom.publish(odom_msg)


def main(args=None):
    rclpy.init(args=args)
    node = DiffDriveKinematics()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
