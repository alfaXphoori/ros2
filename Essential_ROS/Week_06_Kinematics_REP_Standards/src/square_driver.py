#!/usr/bin/env python3
"""
Week 06 Lab 6.4: drive an open-loop square on /cmd_vel and report the loop-closure error.

Four times: drive `side` metres at `speed` m/s, then turn 90 deg at `turn_rate` rad/s, with
commands streamed at 10 Hz (timing only, no feedback). /odom_calculated is logged and the final
pose is compared with the start pose. Optional CSV log:  square_driver --csv square_odom.csv
"""

import argparse
import csv
import math
import signal
import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.utilities import remove_ros_args


def ignore_further_sigint():
    """Ctrl+C under `ros2 launch` arrives twice (terminal process group + launch forwarding it).
    Ignore later SIGINTs so they cannot interrupt the cleanup and kill us with a traceback."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


class SquareDriver(Node):
    def __init__(self):
        super().__init__('square_driver')
        self.samples = []  # (t, x, y, yaw)
        self.create_subscription(Odometry, 'odom_calculated', self.odom_callback, 10)
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)

    def odom_callback(self, msg):
        q = msg.pose.pose.orientation
        yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        self.samples.append((stamp, msg.pose.pose.position.x, msg.pose.pose.position.y, yaw))

    def spin_for(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            rclpy.spin_once(self, timeout_sec=0.01)

    def drive(self, v, omega, seconds):
        """Stream one command at 10 Hz for `seconds` (open loop)."""
        cmd = Twist()
        cmd.linear.x = v
        cmd.angular.z = omega
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.pub.publish(cmd)
            self.spin_for(0.1)

    def run(self, side, speed, turn_rate):
        self.get_logger().info('Waiting for diff_drive_kinematics...')
        while self.count_subscribers('cmd_vel') == 0 or not self.samples:
            self.spin_for(0.1)
        self.spin_for(0.5)
        start = self.samples[-1]
        for i in range(4):
            self.get_logger().info(f'side {i + 1}: {side} m straight, then turn 90 deg')
            self.drive(speed, 0.0, side / speed)
            self.drive(0.0, turn_rate, (math.pi / 2) / turn_rate)
        self.drive(0.0, 0.0, 1.0)  # explicit stop, let the last odometry arrive
        end = self.samples[-1]
        dx, dy = end[1] - start[1], end[2] - start[2]
        dyaw = math.degrees(math.atan2(math.sin(end[3] - start[3]), math.cos(end[3] - start[3])))
        self.get_logger().info(f'final pose relative to start: x={dx:+.4f} m  y={dy:+.4f} m  '
                               f'yaw={dyaw:+.2f} deg')
        self.get_logger().info(f'loop closure error sqrt(dx^2+dy^2) = {math.hypot(dx, dy):.4f} m')
        return start


def main(args=None):
    rclpy.init(args=args)
    parser = argparse.ArgumentParser(description='Open-loop square path on cmd_vel')
    parser.add_argument('--side', type=float, default=1.0, help='side length [m]')
    parser.add_argument('--speed', type=float, default=0.2, help='linear speed [m/s]')
    parser.add_argument('--turn-rate', type=float, default=0.5, help='turn rate [rad/s]')
    parser.add_argument('--csv', help='write the logged odometry to this CSV file')
    opts = parser.parse_args(remove_ros_args(args=sys.argv)[1:])
    node = SquareDriver()
    try:
        start = node.run(opts.side, opts.speed, opts.turn_rate)
        if opts.csv:
            t0 = start[0]
            with open(opts.csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['t', 'x', 'y', 'yaw'])
                for t, x, y, yaw in node.samples:
                    if t >= t0:
                        writer.writerow([f'{t - t0:.3f}', f'{x:.5f}', f'{y:.5f}', f'{yaw:.5f}'])
            node.get_logger().info(f'odometry log written to {opts.csv}')
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        ignore_further_sigint()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
