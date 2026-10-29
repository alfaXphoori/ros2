#!/usr/bin/env python3
"""
Week 14 Lab: send the robot's starting pose to AMCL (/initialpose) and wait until
AMCL answers on /amcl_pose.

  ros2 run amr_week14 amcl_initial_pose --ros-args -p use_sim_time:=true -p x:=0.0 -p y:=0.0 -p theta:=0.0

Equivalent to RViz2 "2D Pose Estimate". Exit code 0 when AMCL accepted the pose.
"""

import math
import sys

from geometry_msgs.msg import PoseWithCovarianceStamped
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


def make_initial_pose(x, y, theta, frame_id='map', sigma_xy=0.5, sigma_yaw=math.radians(15)):
    """PoseWithCovarianceStamped with a diagonal covariance (x, y, yaw)."""
    msg = PoseWithCovarianceStamped()
    msg.header.frame_id = frame_id
    msg.pose.pose.position.x = float(x)
    msg.pose.pose.position.y = float(y)
    msg.pose.pose.orientation.z = math.sin(theta / 2.0)
    msg.pose.pose.orientation.w = math.cos(theta / 2.0)
    cov = [0.0] * 36
    cov[0] = sigma_xy ** 2      # var(x)   0.25 m^2 -> sigma 0.5 m
    cov[7] = sigma_xy ** 2      # var(y)
    cov[35] = sigma_yaw ** 2    # var(yaw) 0.068 rad^2 -> sigma ~15 deg
    msg.pose.covariance = cov
    return msg


class InitialPosePublisher(Node):
    def __init__(self):
        super().__init__('amcl_initial_pose_publisher')
        self.x = self.declare_parameter('x', 0.0).value
        self.y = self.declare_parameter('y', 0.0).value
        self.theta = self.declare_parameter('theta', 0.0).value
        self.frame_id = self.declare_parameter('frame_id', 'map').value
        self.timeout = self.declare_parameter('timeout', 30.0).value
        self.amcl_pose = None
        self.pub = self.create_publisher(PoseWithCovarianceStamped, 'initialpose', 10)
        self.create_subscription(PoseWithCovarianceStamped, 'amcl_pose', self.on_amcl, 10)

    def on_amcl(self, msg):
        self.amcl_pose = msg

    def run(self):
        clock = self.get_clock()
        # with use_sim_time, wait for the first /clock message so the stamp is valid
        while rclpy.ok() and clock.now().nanoseconds == 0:
            rclpy.spin_once(self, timeout_sec=0.1)
        start = clock.now()
        while rclpy.ok() and self.pub.get_subscription_count() == 0:
            rclpy.spin_once(self, timeout_sec=0.1)
            if (clock.now() - start).nanoseconds * 1e-9 > self.timeout:
                self.get_logger().error('No subscriber on /initialpose (is AMCL running?)')
                return False
        msg = make_initial_pose(self.x, self.y, self.theta, self.frame_id)
        self.get_logger().info(
            f'Publishing initial pose x={self.x:.2f} y={self.y:.2f} '
            f'theta={self.theta:.3f} rad in frame {self.frame_id}')
        start = clock.now()
        last_pub = None
        while rclpy.ok() and self.amcl_pose is None:
            now = clock.now()
            if last_pub is None or (now - last_pub).nanoseconds > 1e9:
                msg.header.stamp = now.to_msg()
                self.pub.publish(msg)
                last_pub = now
            rclpy.spin_once(self, timeout_sec=0.1)
            if (now - start).nanoseconds * 1e-9 > self.timeout:
                self.get_logger().error('AMCL did not publish /amcl_pose (no /scan or TF?)')
                return False
        p = self.amcl_pose.pose.pose
        yaw = 2.0 * math.atan2(p.orientation.z, p.orientation.w)
        self.get_logger().info(
            f'AMCL pose: x={p.position.x:.3f} y={p.position.y:.3f} yaw={yaw:.3f} rad')
        return True


def main(args=None):
    rclpy.init(args=args)
    node = InitialPosePublisher()
    ok = False
    try:
        ok = node.run()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
