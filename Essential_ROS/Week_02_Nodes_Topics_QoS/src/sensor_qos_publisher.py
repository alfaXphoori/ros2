#!/usr/bin/env python3
"""
Week 02 Lab: ROS 2 QoS Publisher Node
Publishes high-frequency sensor readings (BEST_EFFORT via qos_profile_sensor_data)
and robot state (RELIABLE + TRANSIENT_LOCAL, i.e. "latched" for late joiners).
"""

import random
import signal
import threading

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy,
                       qos_profile_sensor_data)
from rclpy.signals import SignalHandlerOptions
from std_msgs.msg import Float32, String


# Critical robot state: guaranteed delivery + keep the last value for late-joining subscribers
STATE_QOS = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)


class SensorQoSPublisher(Node):
    def __init__(self):
        super().__init__('sensor_qos_publisher')

        # qos_profile_sensor_data = BEST_EFFORT, VOLATILE, KEEP_LAST(5): drop late frames, keep newest
        self.pub_sensor = self.create_publisher(Float32, 'sensor/temperature',
                                                qos_profile_sensor_data)
        self.pub_state = self.create_publisher(String, 'robot/state', STATE_QOS)

        # Periodic timer (2 Hz)
        self.timer = self.create_timer(0.5, self.timer_callback)
        self.counter = 0

        # Publish initial state immediately (cached by TRANSIENT_LOCAL for late joiners)
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

        # Update the latched state every 10 ticks (5 s)
        if self.counter % 10 == 0:
            state_msg = String()
            state_msg.data = f'SYSTEM_ACTIVE: Uptime={self.counter * 0.5:.1f}s'
            self.pub_state.publish(state_msg)
            self.get_logger().info(f'State Latched: "{state_msg.data}"')


def main(args=None):
    # Clean shutdown (Week 2 Readme, section 3): rclpy's default SIGINT/SIGTERM handler shuts the
    # context down at once, even while spin() is taking a message (RuntimeError -> exit code 1).
    # Here the signals only set a flag; the loop stops between spin_once() calls, and a second
    # Ctrl+C from `ros2 launch` cannot interrupt the cleanup.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    node = SensorQoSPublisher()
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
