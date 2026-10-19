#!/usr/bin/env python3
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
        self.declare_parameter('x', 0.0)
        self.declare_parameter('y', 0.0)
        self.declare_parameter('theta', 0.0)
        self.declare_parameter('frame_id', 'map')

        self.x = self.get_parameter('x').get_parameter_value().double_value
        self.y = self.get_parameter('y').get_parameter_value().double_value
        self.theta = self.get_parameter('theta').get_parameter_value().double_value
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        self.publisher = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', qos_profile)
        self.get_logger().info(f'📍 Publishing initial pose: X={self.x:.2f}, Y={self.y:.2f}, Theta={self.theta:.4f}')

    def publish_pose(self):
        msg = PoseWithCovarianceStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        msg.pose.pose.position.x = self.x
        msg.pose.pose.position.y = self.y
        msg.pose.pose.position.z = 0.0

        half = self.theta * 0.5
        msg.pose.pose.orientation.z = math.sin(half)
        msg.pose.pose.orientation.w = math.cos(half)

        # Covariance diagonal
        cov = [0.0] * 36
        cov[0] = 0.25   # x
        cov[7] = 0.25   # y
        cov[35] = 0.068 # yaw
        msg.pose.covariance = cov

        for _ in range(3):
            self.publisher.publish(msg)
            time.sleep(0.3)
        self.get_logger().info('✅ Initial pose published to /initialpose successfully!')

def main(args=None):
    rclpy.init(args=args)
    node = InitialPosePublisher()
    time.sleep(1.0)
    node.publish_pose()
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()

if __name__ == '__main__':
    main()
