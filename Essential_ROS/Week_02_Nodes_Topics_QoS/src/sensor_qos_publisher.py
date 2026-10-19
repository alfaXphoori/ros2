#!/usr/bin/env python3
"""
Lab 1.1: ROS 2 Custom QoS Publisher Node
Publishes high-frequency sensor readings (BEST_EFFORT) and robot state (RELIABLE + TRANSIENT_LOCAL).
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from std_msgs.msg import String, Float32
import random


class SensorQoSPublisher(Node):
    def __init__(self):
        super().__init__('sensor_qos_publisher')

        # QoS profile for high-rate sensor streams (allow dropped frames, keep newest)
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )

        # QoS profile for critical robot state (guaranteed delivery, latch last value for late-joiners)
        state_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        self.pub_sensor = self.create_publisher(Float32, '/sensor/temperature', sensor_qos)
        self.pub_state = self.create_publisher(String, '/robot/state', state_qos)

        # Periodic timer (2 Hz)
        self.timer = self.create_timer(0.5, self.timer_callback)
        self.counter = 0

        # Publish initial state immediately
        initial_state = String()
        initial_state.data = 'SYSTEM_READY: Battery=100%, Mode=NORMAL'
        self.pub_state.publish(initial_state)

        self.get_logger().info('🚀 [SensorQoSPublisher] Node initialized and publishing...')

    def timer_callback(self):
        self.counter += 1
        
        # Publish sensor data
        temp_msg = Float32()
        temp_msg.data = 36.5 + random.uniform(-0.5, 1.2)
        self.pub_sensor.publish(temp_msg)

        # Periodically update state every 10 ticks
        if self.counter % 10 == 0:
            state_msg = String()
            state_msg.data = f'SYSTEM_ACTIVE: Uptime={self.counter * 0.5:.1f}s'
            self.pub_state.publish(state_msg)
            self.get_logger().info(f'State Latched: "{state_msg.data}"')


def main(args=None):
    rclpy.init(args=args)
    node = SensorQoSPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down Sensor QoS Publisher...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
