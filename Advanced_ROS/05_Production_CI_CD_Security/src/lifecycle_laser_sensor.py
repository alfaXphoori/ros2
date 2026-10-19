#!/usr/bin/env python3
"""
Tutorial 05: ROS 2 Production Lifecycle Node
Demonstrates managed states (Unconfigured -> Inactive -> Active -> Finalized)
ensuring safe hardware initialization and fail-safe shutdowns.
"""

import rclpy
from rclpy.lifecycle import Node, State, TransitionCallbackReturn
from sensor_msgs.msg import LaserScan


class LifecycleLaserSensor(Node):
    def __init__(self):
        super().__init__('lifecycle_laser_sensor')
        self.pub_scan = None
        self.timer = None
        self.get_logger().info('💤 [LifecycleLaserSensor] Created in UNCONFIGURED state.')

    def on_configure(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('⚙️ Configuring hardware connection and buffers...')
        self.pub_scan = self.create_lifecycle_publisher(LaserScan, '/scan_managed', 10)
        self.timer = self.create_timer(0.1, self.publish_scan)
        # Cancel timer initially until activated
        self.timer.cancel()
        self.get_logger().info('✅ Configured successfully. Transitioned to INACTIVE.')
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('⚡ Activating node: Starting laser emission & timer...')
        self.timer.reset()
        return super().on_activate(state)

    def on_deactivate(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().warn('⏸️ Deactivating node: Pausing laser emission...')
        self.timer.cancel()
        return super().on_deactivate(state)

    def on_cleanup(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('🧹 Cleaning up hardware resources...')
        self.destroy_publisher(self.pub_scan)
        self.destroy_timer(self.timer)
        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('🛑 Shutting down sensor node permanently.')
        return TransitionCallbackReturn.SUCCESS

    def publish_scan(self):
        msg = LaserScan()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'lidar_link'
        msg.range_min = 0.12
        msg.range_max = 10.0
        msg.ranges = [2.5] * 360
        self.pub_scan.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = LifecycleLaserSensor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down Lifecycle Sensor...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
