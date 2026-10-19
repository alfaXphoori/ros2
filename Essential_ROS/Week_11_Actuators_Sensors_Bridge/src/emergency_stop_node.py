#!/usr/bin/env python3
"""
Week 11 Lab: Safety Shield & Emergency Stop Node
Subscribes to /scan from Gazebo LiDAR.
Monitors frontal safety sector (-30° to +30°).
Automatically publishes zero velocity to /cmd_vel if an obstacle is within 0.35m.
"""

import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


class EmergencyStopNode(Node):
    def __init__(self):
        super().__init__('emergency_stop_node')

        self.safety_distance = 0.35  # meters
        self.sub_scan = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10
        )
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)

        self.get_logger().info(f'🛡️ [EmergencyStopNode] Active! Safety Shield Threshold = {self.safety_distance}m')

    def scan_callback(self, msg: LaserScan):
        # Front sector check: -30 to +30 degrees
        num_samples = len(msg.ranges)
        if num_samples == 0:
            return

        min_front_dist = float('inf')

        for i, dist in enumerate(msg.ranges):
            # Calculate beam angle
            angle = msg.angle_min + (i * msg.angle_increment)
            if -math.radians(30) <= angle <= math.radians(30):
                if msg.range_min < dist < msg.range_max:
                    if dist < min_front_dist:
                        min_front_dist = dist

        if min_front_dist < self.safety_distance:
            self.get_logger().error(
                f'🚨 OBSTACLE DETECTED at {min_front_dist:.2f}m! Triggering EMERGENCY BRAKE!'
            )
            stop_cmd = Twist()
            stop_cmd.linear.x = 0.0
            stop_cmd.angular.z = 0.0
            self.pub_cmd_vel.publish(stop_cmd)


def main(args=None):
    rclpy.init(args=args)
    node = EmergencyStopNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
