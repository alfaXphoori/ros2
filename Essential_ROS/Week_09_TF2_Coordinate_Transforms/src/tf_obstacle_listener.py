#!/usr/bin/env python3
"""
Week 09 Lab: TF2 Buffer & Listener Node
Queries transforms from camera/sensor frame to base_link / odom.
Transforms detected points into robot base coordinates for collision avoidance.
"""

import rclpy
from rclpy.node import Node
import tf2_ros
from geometry_msgs.msg import PointStamped
import tf2_geometry_msgs


class TfObstacleListener(Node):
    def __init__(self):
        super().__init__('tf_obstacle_listener')

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # Periodic query timer (2 Hz)
        self.timer = self.create_timer(0.5, self.lookup_obstacle_position)
        self.get_logger().info('🔍 [TfObstacleListener] Listening for transforms and converting obstacle poses...')

    def lookup_obstacle_position(self):
        try:
            # Simulated point detected by camera 1.2m ahead, 0.3m to the left in camera frame
            pt_in_camera = PointStamped()
            pt_in_camera.header.stamp = rclpy.time.Time().to_msg()
            pt_in_camera.header.frame_id = 'camera_link'
            pt_in_camera.point.x = 1.2
            pt_in_camera.point.y = 0.3
            pt_in_camera.point.z = 0.0

            # Transform into base_link coordinate frame
            pt_in_base = self.tf_buffer.transform(
                pt_in_camera, 'base_link', timeout=rclpy.duration.Duration(seconds=0.2)
            )

            self.get_logger().info(
                f'🎯 Obstacle transformed from camera to base_link: '
                f'X={pt_in_base.point.x:.2f}m, Y={pt_in_base.point.y:.2f}m'
            )
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException) as e:
            self.get_logger().warn(f'TF lookup waiting: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = TfObstacleListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
