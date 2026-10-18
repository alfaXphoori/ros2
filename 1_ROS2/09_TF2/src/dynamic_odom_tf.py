#!/usr/bin/env python3
"""
Tutorial 09 - TF2 Dynamic Odometry Broadcaster Node

Simulates differential drive robot kinematics and continuously broadcasts:
  1. Dynamic Transform: 'odom' -> 'base_footprint' (Position & Yaw change over time)
  2. Static Transform:  'base_footprint' -> 'base_link' (Chassis ground offset = 0.08m)
  3. ROS Odometry Message: published to '/odom' (Pose + Twist telemetry)

Dynamic transforms are streamed to the '/tf' topic at high frequency (20 Hz - 50 Hz).
"""

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped, Quaternion
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster


def euler_to_quaternion(roll: float, pitch: float, yaw: float):
    """Convert Euler angles (in radians) to Quaternion (x, y, z, w)."""
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    qx = sr * cp * cy - cr * sp * sy
    qy = cr * cp * cy + sr * cp * sy
    qz = cr * cp * sy - sr * sp * cy
    qw = cr * cp * cy + sr * cp * sy
    return qx, qy, qz, qw


class DynamicOdomTFBroadcaster(Node):
    """Broadcaster node for dynamic robot odometry and TF frames."""

    def __init__(self):
        super().__init__('dynamic_odom_tf_broadcaster')

        # TF Broadcasters
        self.tf_broadcaster = TransformBroadcaster(self)
        self.tf_static_broadcaster = StaticTransformBroadcaster(self)

        # Odometry Publisher
        self.odom_publisher = self.create_publisher(Odometry, '/odom', 10)

        # Robot kinematic state
        self.x = 0.0          # meters
        self.y = 0.0          # meters
        self.theta = 0.0      # radians (yaw)

        # Simulated velocities
        self.linear_velocity = 0.25   # m/s forward
        self.angular_velocity = 0.20  # rad/s turning counter-clockwise

        # Simulation loop timer (20 Hz = 50ms period)
        self.dt = 0.05
        self.timer = self.create_timer(self.dt, self.update_kinematics_and_broadcast)

        # Broadcast static base_footprint -> base_link offset
        self.broadcast_base_link_offset()

        self.step_count = 0
        self.get_logger().info('🚀 Dynamic Odom TF Broadcaster started (20 Hz)')
        self.get_logger().info(f'   Simulating circular trajectory: v={self.linear_velocity} m/s, w={self.angular_velocity} rad/s')

    def broadcast_base_link_offset(self):
        """Broadcast static transform between ground footprint and robot axle origin."""
        t_base = TransformStamped()
        t_base.header.stamp = self.get_clock().now().to_msg()
        t_base.header.frame_id = 'base_footprint'
        t_child = 'base_link'
        t_base.child_frame_id = t_child

        t_base.transform.translation.x = 0.0
        t_base.transform.translation.y = 0.0
        t_base.transform.translation.z = 0.08  # Wheel radius elevation

        qx, qy, qz, qw = euler_to_quaternion(0.0, 0.0, 0.0)
        t_base.transform.rotation.x = qx
        t_base.transform.rotation.y = qy
        t_base.transform.rotation.z = qz
        t_base.transform.rotation.w = qw

        self.tf_static_broadcaster.sendTransform(t_base)

    def update_kinematics_and_broadcast(self):
        """Integrate velocities and broadcast dynamic odom -> base_footprint transform."""
        now = self.get_clock().now()
        stamp = now.to_msg()

        # Differential drive kinematic integration
        self.x += self.linear_velocity * math.cos(self.theta) * self.dt
        self.y += self.linear_velocity * math.sin(self.theta) * self.dt
        self.theta += self.angular_velocity * self.dt

        # Normalize theta to [-pi, pi]
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

        qx, qy, qz, qw = euler_to_quaternion(0.0, 0.0, self.theta)

        # -------------------------------------------------------------
        # 1. Broadcast Dynamic Transform: 'odom' -> 'base_footprint'
        # -------------------------------------------------------------
        t_odom = TransformStamped()
        t_odom.header.stamp = stamp
        t_odom.header.frame_id = 'odom'
        t_odom.child_frame_id = 'base_footprint'

        t_odom.transform.translation.x = self.x
        t_odom.transform.translation.y = self.y
        t_odom.transform.translation.z = 0.0

        t_odom.transform.rotation.x = qx
        t_odom.transform.rotation.y = qy
        t_odom.transform.rotation.z = qz
        t_odom.transform.rotation.w = qw

        self.tf_broadcaster.sendTransform(t_odom)

        # -------------------------------------------------------------
        # 2. Publish Standard nav_msgs/Odometry Message
        # -------------------------------------------------------------
        odom_msg = Odometry()
        odom_msg.header.stamp = stamp
        odom_msg.header.frame_id = 'odom'
        odom_msg.child_frame_id = 'base_footprint'

        # Pose in odom frame
        odom_msg.pose.pose.position.x = self.x
        odom_msg.pose.pose.position.y = self.y
        odom_msg.pose.pose.position.z = 0.0
        odom_msg.pose.pose.orientation = Quaternion(x=qx, y=qy, z=qz, w=qw)

        # Twist in robot body frame
        odom_msg.twist.twist.linear.x = self.linear_velocity
        odom_msg.twist.twist.angular.z = self.angular_velocity

        self.odom_publisher.publish(odom_msg)

        # Periodic logging every 1 second (20 steps * 0.05s)
        self.step_count += 1
        if self.step_count % 20 == 0:
            deg = math.degrees(self.theta)
            self.get_logger().info(
                f'🤖 Robot Pose: X={self.x:6.2f}m | Y={self.y:6.2f}m | Yaw={deg:6.1f}°'
            )


def main(args=None):
    rclpy.init(args=args)
    node = DynamicOdomTFBroadcaster()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
