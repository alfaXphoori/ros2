#!/usr/bin/env python3
"""
Week 02 Lab: ROS 2 QoS Subscriber Node
Subscribes to sensor readings and latched robot state with QoS compatible with the publisher.
"""

import signal

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy,
                       qos_profile_sensor_data)
from std_msgs.msg import Float32, String


def ignore_further_sigint():
    """Ctrl+C under `ros2 launch` arrives twice (terminal process group + launch forwarding it).
    Ignore later SIGINTs so they cannot interrupt the cleanup and kill us with a traceback."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


# Must request TRANSIENT_LOCAL too, otherwise the cached (latched) state is not delivered
STATE_QOS = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)


class SensorQoSSubscriber(Node):
    def __init__(self):
        super().__init__('sensor_qos_subscriber')

        # BEST_EFFORT request matches the BEST_EFFORT offer (RELIABLE here would be incompatible)
        self.sub_sensor = self.create_subscription(
            Float32, 'sensor/temperature', self.sensor_callback, qos_profile_sensor_data
        )
        self.sub_state = self.create_subscription(
            String, 'robot/state', self.state_callback, STATE_QOS
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
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        ignore_further_sigint()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
