#!/usr/bin/env python3
"""
Week 11 Lab: Safety Shield / Emergency Stop *gate*.

Data flow (the node sits BETWEEN the command source and the robot):

    teleop / Nav2 --> /cmd_vel_in --> [emergency_stop_node] --> /cmd_vel --> ros_gz_bridge --> DiffDrive
                                             ^
                                   /scan (LiDAR, sensor-data QoS)

* The node forwards every Twist from cmd_vel_in to cmd_vel unchanged while the
  frontal sector (+-30 deg) is clear.
* If the closest valid return in that sector is nearer than `safety_distance`,
  forward motion (linear.x > 0) is replaced by 0. Turning in place and reversing
  are still allowed so the robot can escape.
* Fail-safe: if no scan has arrived for `scan_timeout` seconds, the output is a
  full stop (we cannot prove the path is clear).

Why a gate and not "publish zero on /cmd_vel too"?  Two publishers on one topic
race (last writer wins): teleop at 10 Hz would immediately overwrite the brake.
"""

import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


def front_min_range(ranges, angle_min, angle_increment, range_min, range_max,
                    half_angle_rad):
    """Closest valid range (m) with |beam angle| <= half_angle_rad; inf if none."""
    closest = math.inf
    for i, r in enumerate(ranges):
        angle = angle_min + i * angle_increment
        # normalise to (-pi, pi] so scans that start at 0 also work
        angle = math.atan2(math.sin(angle), math.cos(angle))
        if abs(angle) <= half_angle_rad and range_min <= r <= range_max and r < closest:
            closest = r
    return closest


def gate_command(linear_x, angular_z, min_front, safety_distance):
    """Return (linear_x, angular_z, blocked) after applying the safety shield."""
    if min_front < safety_distance and linear_x > 0.0:
        return 0.0, angular_z, True
    return linear_x, angular_z, min_front < safety_distance


class EmergencyStopNode(Node):
    def __init__(self):
        super().__init__('emergency_stop_node')
        self.safety_distance = self.declare_parameter('safety_distance', 0.35).value
        half_deg = self.declare_parameter('sector_half_angle_deg', 30.0).value
        self.half_angle = math.radians(half_deg)
        self.scan_timeout = self.declare_parameter('scan_timeout', 0.5).value

        self.min_front = math.inf
        self.last_scan_time = None
        self.blocked = False
        self.last_out = Twist()

        self.sub_scan = self.create_subscription(
            LaserScan, 'scan', self.scan_callback, qos_profile_sensor_data)
        self.sub_cmd = self.create_subscription(Twist, 'cmd_vel_in', self.cmd_callback, 10)
        self.pub_cmd = self.create_publisher(Twist, 'cmd_vel', 10)

        self.get_logger().info(
            f'Safety gate ready: cmd_vel_in -> cmd_vel, stop distance '
            f'{self.safety_distance:.2f} m, sector +-{half_deg:.0f} deg, '
            f'scan timeout {self.scan_timeout:.1f} s')

    def scan_fresh(self):
        if self.last_scan_time is None:
            return False
        age = (self.get_clock().now() - self.last_scan_time).nanoseconds * 1e-9
        return age <= self.scan_timeout

    def scan_callback(self, msg: LaserScan):
        self.last_scan_time = self.get_clock().now()
        self.min_front = front_min_range(msg.ranges, msg.angle_min, msg.angle_increment,
                                         msg.range_min, msg.range_max, self.half_angle)
        blocked = self.min_front < self.safety_distance
        if blocked and not self.blocked:
            self.get_logger().warn(
                f'Obstacle at {self.min_front:.2f} m (< {self.safety_distance:.2f} m) '
                f'in front: forward motion BLOCKED')
        elif not blocked and self.blocked:
            self.get_logger().info(f'Path clear ({self.min_front:.2f} m): forwarding cmd_vel')
        self.blocked = blocked
        # Command sources such as teleop_twist_keyboard publish only on key press and
        # Gazebo DiffDrive keeps the last command, so brake actively right now.
        if blocked and self.last_out.linear.x > 0.0:
            self.publish(0.0, self.last_out.angular.z)

    def cmd_callback(self, msg: Twist):
        if not self.scan_fresh():
            self.get_logger().warn('No recent /scan: holding the robot (fail-safe)',
                                   throttle_duration_sec=2.0)
            self.publish(0.0, 0.0)
            return
        lin, ang, _ = gate_command(msg.linear.x, msg.angular.z,
                                   self.min_front, self.safety_distance)
        self.publish(lin, ang)

    def publish(self, linear_x, angular_z):
        out = Twist()
        out.linear.x = float(linear_x)
        out.angular.z = float(angular_z)
        self.pub_cmd.publish(out)
        self.last_out = out


def main(args=None):
    rclpy.init(args=args)
    node = EmergencyStopNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
