#!/usr/bin/env python3
"""
Lab 1.1: ROS 2 Custom QoS Subscriber Node
Subscribes to sensor readings with compatible QoS matching the publisher.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from std_msgs.msg import String, Float32


class SensorQoSSubscriber(Node):
    def __init__(self):
        super().__init__('sensor_qos_subscriber')

        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )

        state_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        self.sub_sensor = self.create_subscription(
            Float32, '/sensor/temperature', self.sensor_callback, sensor_qos
        )
        self.sub_state = self.create_subscription(
            String, '/robot/state', self.state_callback, state_qos
        )

        self.get_logger().info('📡 [SensorQoSSubscriber] Listening for sensor & state updates...')

    def sensor_callback(self, msg: Float32):
        self.get_logger().info(f'Received Temperature: {msg.data:.2f} °C')

    def state_callback(self, msg: String):
        self.get_logger().info(f'📢 Latched Robot State Received: "{msg.data}"')


def main(args=None):
    rclpy.init(args=args)
    node = SensorQoSSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down Sensor QoS Subscriber...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
