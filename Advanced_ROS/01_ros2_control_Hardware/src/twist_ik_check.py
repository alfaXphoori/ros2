#!/usr/bin/env python3
"""
Advanced Module 01: drive diff_drive_controller with TwistStamped and check the wheel speeds.

Publishes geometry_msgs/TwistStamped on /diff_drive_controller/cmd_vel (the only command input
of diff_drive_controller in Jazzy) for `duration` seconds, then compares
  * /joint_states wheel velocities  with the inverse kinematics  (w_L, w_R)
  * /diff_drive_controller/odom twist with the command, and prints the odometry pose.
Exit code 0 when everything matches within `tolerance`.

Run (with launch/mock_diff_drive.launch.py running):
  ros2 run amr_adv01 twist_ik_check --ros-args -p v:=0.5 -p omega:=1.0
"""

import math
import sys

import rclpy
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import JointState

try:
    from amr_adv01.kinematics import inverse_kinematics
except ImportError:  # python3 src/twist_ik_check.py
    from kinematics import inverse_kinematics


def yaw_from_quaternion(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class TwistIkCheck(Node):
    def __init__(self):
        super().__init__('twist_ik_check')
        self.v = self.declare_parameter('v', 0.5).value
        self.omega = self.declare_parameter('omega', 1.0).value
        self.duration = self.declare_parameter('duration', 3.0).value
        self.tolerance = self.declare_parameter('tolerance', 0.05).value  # rad/s and m/s
        self.separation = self.declare_parameter('wheel_separation', 0.24).value
        self.radius = self.declare_parameter('wheel_radius', 0.08).value
        self.cmd_topic = self.declare_parameter('cmd_vel_topic', '/diff_drive_controller/cmd_vel').value

        self.pub = self.create_publisher(TwistStamped, self.cmd_topic, 10)
        self.create_subscription(JointState, '/joint_states', self.on_joint_states, 10)
        self.create_subscription(Odometry, '/diff_drive_controller/odom', self.on_odom, 10)
        self.wheel_vel = {}
        self.odom = None
        self.start = None
        self.done = False
        self.ok = False
        self.timer = self.create_timer(0.05, self.on_timer)  # 20 Hz command stream

    def on_joint_states(self, msg):
        for name, vel in zip(msg.name, msg.velocity):
            self.wheel_vel[name] = vel

    def on_odom(self, msg):
        self.odom = msg

    def publish_cmd(self, v, omega):
        cmd = TwistStamped()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.header.frame_id = 'base_footprint'
        cmd.twist.linear.x = float(v)
        cmd.twist.angular.z = float(omega)
        self.pub.publish(cmd)

    def on_timer(self):
        if self.done:
            return
        if self.start is None:
            if self.pub.get_subscription_count() == 0:
                self.get_logger().info(f'waiting for a subscriber on {self.cmd_topic} ...',
                                       throttle_duration_sec=2.0)
                return
            self.start = self.get_clock().now()
            self.get_logger().info(f'sending TwistStamped v={self.v} m/s, omega={self.omega} rad/s '
                                   f'for {self.duration} s on {self.cmd_topic}')
        elapsed = (self.get_clock().now() - self.start).nanoseconds * 1e-9
        if elapsed < self.duration:
            self.publish_cmd(self.v, self.omega)
            return
        self.report()
        self.publish_cmd(0.0, 0.0)
        self.done = True

    def report(self):
        exp_l, exp_r = inverse_kinematics(self.v, self.omega, self.separation, self.radius)
        got_l = self.wheel_vel.get('left_wheel_joint', float('nan'))
        got_r = self.wheel_vel.get('right_wheel_joint', float('nan'))
        print(f'IK  expected : left = {exp_l:7.3f} rad/s   right = {exp_r:7.3f} rad/s', flush=True)
        print(f'/joint_states: left = {got_l:7.3f} rad/s   right = {got_r:7.3f} rad/s', flush=True)
        ok = abs(got_l - exp_l) < self.tolerance and abs(got_r - exp_r) < self.tolerance
        if self.odom is not None:
            p = self.odom.pose.pose
            t = self.odom.twist.twist
            print(f'odom twist   : v = {t.linear.x:6.3f} m/s   omega = {t.angular.z:6.3f} rad/s',
                  flush=True)
            print(f'odom pose    : x = {p.position.x:6.3f} m  y = {p.position.y:6.3f} m  '
                  f'yaw = {math.degrees(yaw_from_quaternion(p.orientation)):7.2f} deg', flush=True)
            ok = ok and abs(t.linear.x - self.v) < self.tolerance \
                and abs(t.angular.z - self.omega) < self.tolerance
        else:
            print('odom         : no message on /diff_drive_controller/odom', flush=True)
            ok = False
        print('RESULT: ' + ('PASS - wheel speeds match inverse kinematics' if ok else 'FAIL'),
              flush=True)
        self.ok = ok


def main(args=None):
    rclpy.init(args=args)
    node = TwistIkCheck()
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
        # give the zero command a moment to go out
        for _ in range(3):
            rclpy.spin_once(node, timeout_sec=0.05)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        ok = node.ok
        node.destroy_node()
        rclpy.try_shutdown()
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
