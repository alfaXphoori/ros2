#!/usr/bin/env python3
"""
Tutorial 04: headless kinematic stand-in for one differential-drive AMR.

No physics, no Gazebo: it integrates the commanded twist (unicycle model) so a
multi-robot launch can run anywhere (CI, laptops without GPU). Per robot it:

  subscribes  cmd_vel       (geometry_msgs/Twist)      -> /<ns>/cmd_vel
  publishes   odom          (nav_msgs/Odometry)        -> /<ns>/odom
  publishes   joint_states  (left/right wheel angles)  -> /<ns>/joint_states
  broadcasts  TF <prefix>odom -> <prefix>base_footprint on the shared /tf

All topic names are *relative*, so PushRosNamespace('amr_01') moves them under
/amr_01. /tf is a global topic in ROS 2 (tf2 uses the absolute name "/tf"), so
frames must be made unique with frame_prefix instead.

  ros2 run amr_adv04 fake_diff_drive --ros-args -r __ns:=/amr_01 -p frame_prefix:=amr_01/
"""

import math

import rclpy
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster


def integrate_pose(x, y, yaw, v, w, dt):
    """Exact unicycle integration over dt for constant (v, w)."""
    if abs(w) < 1e-9:
        return x + v * dt * math.cos(yaw), y + v * dt * math.sin(yaw), yaw
    yaw_new = yaw + w * dt
    r = v / w
    x_new = x + r * (math.sin(yaw_new) - math.sin(yaw))
    y_new = y - r * (math.cos(yaw_new) - math.cos(yaw))
    return x_new, y_new, math.atan2(math.sin(yaw_new), math.cos(yaw_new))


def wheel_rates(v, w, wheel_radius, wheel_separation):
    """Inverse kinematics: body twist -> (left, right) wheel speed in rad/s."""
    left = (v - w * wheel_separation / 2.0) / wheel_radius
    right = (v + w * wheel_separation / 2.0) / wheel_radius
    return left, right


def yaw_to_quaternion(yaw):
    return 0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0)


class FakeDiffDrive(Node):
    def __init__(self):
        super().__init__('fake_diff_drive')
        # Defaults match Essential_ROS Week 07 diff_drive_robot.urdf
        self.declare_parameter('frame_prefix', '')
        self.declare_parameter('wheel_radius', 0.08)
        self.declare_parameter('wheel_separation', 0.24)
        self.declare_parameter('left_wheel_joint', 'left_wheel_joint')
        self.declare_parameter('right_wheel_joint', 'right_wheel_joint')
        self.declare_parameter('publish_rate', 20.0)
        self.declare_parameter('cmd_vel_timeout', 0.5)   # s, stop if no command

        prefix = self.get_parameter('frame_prefix').value
        self.odom_frame = prefix + 'odom'
        self.base_frame = prefix + 'base_footprint'
        self.r = float(self.get_parameter('wheel_radius').value)
        self.sep = float(self.get_parameter('wheel_separation').value)
        self.joints = [self.get_parameter('left_wheel_joint').value,
                       self.get_parameter('right_wheel_joint').value]
        self.timeout = float(self.get_parameter('cmd_vel_timeout').value)
        self.dt = 1.0 / float(self.get_parameter('publish_rate').value)

        self.x = self.y = self.yaw = 0.0
        self.wheel_pos = [0.0, 0.0]
        self.v = self.w = 0.0
        self.last_cmd = None

        self.create_subscription(Twist, 'cmd_vel', self.on_cmd_vel, 10)
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.js_pub = self.create_publisher(JointState, 'joint_states', 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.timer = self.create_timer(self.dt, self.step)
        self.get_logger().info(
            f'fake_diff_drive in namespace "{self.get_namespace()}": '
            f'{self.odom_frame} -> {self.base_frame}')

    def on_cmd_vel(self, msg: Twist):
        self.v, self.w = msg.linear.x, msg.angular.z
        self.last_cmd = self.get_clock().now()

    def step(self):
        now = self.get_clock().now()
        if self.last_cmd is None or (now - self.last_cmd).nanoseconds * 1e-9 > self.timeout:
            self.v = self.w = 0.0
        self.x, self.y, self.yaw = integrate_pose(self.x, self.y, self.yaw,
                                                  self.v, self.w, self.dt)
        wl, wr = wheel_rates(self.v, self.w, self.r, self.sep)
        self.wheel_pos[0] += wl * self.dt
        self.wheel_pos[1] += wr * self.dt
        stamp = now.to_msg()
        qx, qy, qz, qw = yaw_to_quaternion(self.yaw)

        tf = TransformStamped()
        tf.header.stamp = stamp
        tf.header.frame_id = self.odom_frame
        tf.child_frame_id = self.base_frame
        tf.transform.translation.x = self.x
        tf.transform.translation.y = self.y
        tf.transform.rotation.z = qz
        tf.transform.rotation.w = qw
        self.tf_broadcaster.sendTransform(tf)

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.twist.twist.linear.x = self.v
        odom.twist.twist.angular.z = self.w
        self.odom_pub.publish(odom)

        js = JointState()
        js.header.stamp = stamp
        js.name = list(self.joints)
        js.position = list(self.wheel_pos)
        js.velocity = [wl, wr]
        self.js_pub.publish(js)


def main(args=None):
    rclpy.init(args=args)
    node = FakeDiffDrive()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
