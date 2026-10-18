#!/usr/bin/env python3
"""
Tutorial 09 - TF2 Transform Listener & Coordinate Transformation Node

Demonstrates how to:
  1. Initialize tf2_ros Buffer and TransformListener to cache coordinate frames
  2. Query spatial transforms between arbitrary frames (e.g., 'odom' -> 'laser_frame')
  3. Transform detected 3D target coordinates from sensor frame to robot and world frames
  4. Handle timing exceptions and buffer lookups robustly
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.time import Time
from rclpy.duration import Duration
import tf2_ros
from tf2_ros import TransformException, LookupException, ConnectivityException, ExtrapolationException


def quaternion_to_yaw(qx: float, qy: float, qz: float, qw: float) -> float:
    """Extract Euler Yaw angle (rotation around Z axis in radians) from Quaternion."""
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    return math.atan2(siny_cosp, cosy_cosp)


def apply_transform_to_point(point: tuple, transform) -> tuple:
    """
    Applies a TransformStamped (Translation + Quaternion Rotation) to a 3D Point (px, py, pz).
    Uses the exact 3x3 rotation matrix derived from quaternion (x, y, z, w).
    """
    px, py, pz = point

    # Translation
    tx = transform.transform.translation.x
    ty = transform.transform.translation.y
    tz = transform.transform.translation.z

    # Quaternion
    x = transform.transform.rotation.x
    y = transform.transform.rotation.y
    z = transform.transform.rotation.z
    w = transform.transform.rotation.w

    # Rotation Matrix elements
    r00 = 1.0 - 2.0 * (y * y + z * z)
    r01 = 2.0 * (x * y - z * w)
    r02 = 2.0 * (x * z + y * w)

    r10 = 2.0 * (x * y + z * w)
    r11 = 1.0 - 2.0 * (x * x + z * z)
    r12 = 2.0 * (y * z - x * w)

    r20 = 2.0 * (x * z - y * w)
    r21 = 2.0 * (y * z + x * w)
    r22 = 1.0 - 2.0 * (x * x + y * y)

    # Compute rotated and translated point
    p_out_x = r00 * px + r01 * py + r02 * pz + tx
    p_out_y = r10 * px + r11 * py + r12 * pz + ty
    p_out_z = r20 * px + r21 * py + r22 * pz + tz

    return p_out_x, p_out_y, p_out_z


class TFListenerNode(Node):
    """Node that listens to TF tree and transforms obstacle coordinates."""

    def __init__(self):
        super().__init__('tf_listener_node')

        # 1. Initialize TF Buffer and Listener
        # Buffer caches transform tree history in memory (default 10 seconds)
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # 2. Timer to query transforms and compute target tracking (1.0 Hz)
        self.timer = self.create_timer(1.0, self.on_timer_lookup)

        # Simulated obstacle detected by LiDAR in 'laser_frame'
        # 1.5 meters directly ahead, 0.3 meters to the left
        self.obstacle_laser_frame = (1.50, 0.30, 0.0)

        self.get_logger().info('👂 TF2 Listener Node initialized.')
        self.get_logger().info('   Waiting for transform chain: odom -> base_link -> laser_frame...')

    def on_timer_lookup(self):
        """Query TF buffer to compute robot pose and transformed obstacle positions."""
        # Query the latest available transform at Time() (time 0 = latest)
        target_time = Time()

        try:
            # ---------------------------------------------------------
            # 1. Lookup Robot Body Pose in World/Odom Frame
            # ---------------------------------------------------------
            transform_odom_to_base = self.tf_buffer.lookup_transform(
                target_frame='odom',
                source_frame='base_link',
                time=target_time,
                timeout=Duration(seconds=0.2)
            )

            # Extract Translation
            trans = transform_odom_to_base.transform.translation
            rot = transform_odom_to_base.transform.rotation
            yaw_deg = math.degrees(quaternion_to_yaw(rot.x, rot.y, rot.z, rot.w))

            # ---------------------------------------------------------
            # 2. Lookup Transform from 'laser_frame' to 'odom'
            # ---------------------------------------------------------
            transform_odom_to_laser = self.tf_buffer.lookup_transform(
                target_frame='odom',
                source_frame='laser_frame',
                time=target_time,
                timeout=Duration(seconds=0.2)
            )

            # Transform obstacle point from sensor frame to world frame
            obstacle_world = apply_transform_to_point(
                self.obstacle_laser_frame,
                transform_odom_to_laser
            )

            # ---------------------------------------------------------
            # 3. Lookup Transform from 'laser_frame' to 'base_link'
            # ---------------------------------------------------------
            transform_base_to_laser = self.tf_buffer.lookup_transform(
                target_frame='base_link',
                source_frame='laser_frame',
                time=target_time,
                timeout=Duration(seconds=0.2)
            )

            obstacle_base = apply_transform_to_point(
                self.obstacle_laser_frame,
                transform_base_to_laser
            )

            # Log results cleanly
            self.get_logger().info('---------------------------------------------------------')
            self.get_logger().info(f'📍 Robot Base (in odom): X={trans.x:6.2f}m, Y={trans.y:6.2f}m, Heading={yaw_deg:5.1f}°')
            self.get_logger().info(f'🎯 Obstacle (in laser_frame): X={self.obstacle_laser_frame[0]:.2f}m, Y={self.obstacle_laser_frame[1]:.2f}m')
            self.get_logger().info(f'🤖 Obstacle (in base_link):   X={obstacle_base[0]:.2f}m, Y={obstacle_base[1]:.2f}m')
            self.get_logger().info(f'🗺️ Obstacle (in odom world):  X={obstacle_world[0]:.2f}m, Y={obstacle_world[1]:.2f}m')

        except (LookupException, ConnectivityException, ExtrapolationException) as ex:
            self.get_logger().warn(f'⏳ Waiting for transforms to become available: {ex}')
        except TransformException as ex:
            self.get_logger().error(f'⚠️ TF error: {ex}')


def main(args=None):
    rclpy.init(args=args)
    node = TFListenerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
