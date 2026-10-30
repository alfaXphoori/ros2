#!/usr/bin/env python3
"""
Week 02 Lab: ROS 2 QoS Subscriber Node
Subscribes to sensor readings and latched robot state with QoS compatible with the publisher.
"""

import signal
import threading

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy,
                       qos_profile_sensor_data)
from rclpy.signals import SignalHandlerOptions
from std_msgs.msg import Float32, String


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
    # Clean shutdown (Week 2 Readme, section 3): rclpy's default SIGINT/SIGTERM handler shuts the
    # context down at once, even while spin() is taking a message (RuntimeError -> exit code 1).
    # Here the signals only set a flag; the loop stops between spin_once() calls, and a second
    # Ctrl+C from `ros2 launch` cannot interrupt the cleanup.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    node = SensorQoSSubscriber()
    try:
        while not stop.is_set() and rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
    except ExternalShutdownException:
        pass
    finally:
        # We are stopping: ignore further signals. At interpreter exit Python resets our flag
        # handler to the default action, so a 2nd Ctrl+C from `ros2 launch` would kill us (-2).
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal.SIG_IGN)
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
