#!/usr/bin/env python3
"""
Week 06 Lab: Differential Drive Kinematics & Odometry Calculator
Inverse kinematics (cmd_vel twist -> wheel speeds), forward kinematics (wheel speeds -> twist)
and dead reckoning with midpoint (RK2) integration. Publishes nav_msgs/Odometry and the
odom -> base_footprint transform on /tf.
Frames follow REP 103 (m, rad, s) and REP 105 (odom), base_footprint from REP 120.
"""

import signal

import rclpy
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from tf2_ros import TransformBroadcaster

try:  # installed package (ros2 run amr_week06 ...)
    from amr_week06.kinematics import (INTEGRATORS, forward_kinematics, inverse_kinematics,
                                       yaw_to_quaternion)
except ImportError:  # python3 src/diff_drive_kinematics.py
    from kinematics import (INTEGRATORS, forward_kinematics, inverse_kinematics,
                            yaw_to_quaternion)


def ignore_further_sigint():
    """Ctrl+C under `ros2 launch` arrives twice (terminal process group + launch forwarding it).
    Ignore later SIGINTs so they cannot interrupt the cleanup and kill us with a traceback."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


class DiffDriveKinematics(Node):
    def __init__(self):
        super().__init__('diff_drive_kinematics')

        # Robot physical parameters
        self.declare_parameter('wheel_separation', 0.24)  # L (meters)
        self.declare_parameter('wheel_radius', 0.08)      # r (meters)
        # Stop the wheels if no cmd_vel arrives for this long (s); <= 0 disables the watchdog
        self.declare_parameter('cmd_vel_timeout', 0.5)
        self.declare_parameter('integration', 'midpoint')  # euler | midpoint | exact
        self.declare_parameter('publish_tf', True)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_footprint')

        self.L = self.get_parameter('wheel_separation').value
        self.r = self.get_parameter('wheel_radius').value
        self.cmd_timeout = self.get_parameter('cmd_vel_timeout').value
        method = self.get_parameter('integration').value
        if method not in INTEGRATORS:
            raise ValueError(f'integration must be one of {sorted(INTEGRATORS)}, got {method!r}')
        self.integrate = INTEGRATORS[method]
        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value

        # Robot state (x, y, theta) in the odom frame
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_time = self.get_clock().now()

        # Current commanded wheel speeds (rad/s) and when the last command arrived
        self.w_left = 0.0
        self.w_right = 0.0
        self.last_cmd_time = None

        self.sub_cmd_vel = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)
        self.pub_odom = self.create_publisher(Odometry, 'odom_calculated', 10)
        self.tf_broadcaster = (TransformBroadcaster(self)
                               if self.get_parameter('publish_tf').value else None)

        # 20 Hz update loop for dead reckoning
        self.timer = self.create_timer(0.05, self.update_odometry)

        self.get_logger().info(
            f'🤖 [DiffDriveKinematics] Ready: L={self.L}m, r={self.r}m, '
            f'integration={method}, cmd_vel_timeout={self.cmd_timeout}s')

    def cmd_vel_callback(self, msg: Twist):
        # Inverse kinematics: body twist (v, omega) -> wheel angular speeds (rad/s)
        self.w_left, self.w_right = inverse_kinematics(msg.linear.x, msg.angular.z, self.L, self.r)
        self.last_cmd_time = self.get_clock().now()

    def update_odometry(self):
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        self.last_time = current_time
        if dt <= 0.0:
            return

        # Watchdog: a dead teleop/planner must not leave the robot driving forever
        if self.last_cmd_time is not None and self.cmd_timeout > 0.0:
            silent = (current_time - self.last_cmd_time).nanoseconds / 1e9
            if silent > self.cmd_timeout:
                self.get_logger().warn(
                    f'No cmd_vel for {silent:.2f} s (> {self.cmd_timeout} s): stopping wheels')
                self.w_left = self.w_right = 0.0
                self.last_cmd_time = None

        # Forward kinematics: wheel speeds -> body twist (as from wheel encoders)
        v, omega = forward_kinematics(self.w_left, self.w_right, self.L, self.r)

        # Dead reckoning (midpoint / RK2 by default)
        self.x, self.y, self.theta = self.integrate(self.x, self.y, self.theta, v, omega, dt)
        q = yaw_to_quaternion(self.theta)
        stamp = current_time.to_msg()

        odom_msg = Odometry()
        odom_msg.header.stamp = stamp
        odom_msg.header.frame_id = self.odom_frame
        odom_msg.child_frame_id = self.base_frame
        odom_msg.pose.pose.position.x = self.x
        odom_msg.pose.pose.position.y = self.y
        odom_msg.pose.pose.orientation.x = q[0]
        odom_msg.pose.pose.orientation.y = q[1]
        odom_msg.pose.pose.orientation.z = q[2]
        odom_msg.pose.pose.orientation.w = q[3]
        odom_msg.twist.twist.linear.x = v      # twist is expressed in child_frame_id
        odom_msg.twist.twist.angular.z = omega
        self.pub_odom.publish(odom_msg)

        if self.tf_broadcaster is not None:
            tf = TransformStamped()
            tf.header.stamp = stamp
            tf.header.frame_id = self.odom_frame
            tf.child_frame_id = self.base_frame
            tf.transform.translation.x = self.x
            tf.transform.translation.y = self.y
            tf.transform.rotation = odom_msg.pose.pose.orientation
            self.tf_broadcaster.sendTransform(tf)


def main(args=None):
    rclpy.init(args=args)
    node = DiffDriveKinematics()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        ignore_further_sigint()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
