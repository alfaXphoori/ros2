#!/usr/bin/env python3
"""
Week 03 Lab: ROS 2 Service Server
Provides a power management service allowing clients to switch between normal and power-saving modes.
"""

import signal
import threading

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from std_srvs.srv import SetBool


class PowerServiceServer(Node):
    def __init__(self):
        super().__init__('power_service_server')
        self.eco_mode = False
        # Relative name -> /robot/set_power_mode, or /<ns>/robot/set_power_mode when namespaced
        self.srv = self.create_service(
            SetBool, 'robot/set_power_mode', self.handle_set_power_mode
        )
        self.get_logger().info(
            f'⚡ [PowerServiceServer] Service '
            f'{self.resolve_service_name("robot/set_power_mode")} ready.')

    def handle_set_power_mode(self, request, response):
        self.eco_mode = request.data
        if self.eco_mode:
            response.success = True
            response.message = 'Power saving mode ENABLED: Max speed capped at 0.3 m/s, sensors throttled.'
            self.get_logger().warn(response.message)
        else:
            response.success = True
            response.message = 'Normal power mode RESTORED: Full speed 0.8 m/s enabled.'
            self.get_logger().info(response.message)
        return response


def main(args=None):
    # Clean shutdown as in Week 2: SIGINT/SIGTERM only set a flag, the loop stops between
    # spin_once() calls (rclpy's own handler could shut the context down mid-callback).
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    node = PowerServiceServer()
    try:
        while not stop.is_set() and rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
    except ExternalShutdownException:
        pass
    finally:
        # stopping: ignore further signals (Python resets our handler at exit -> 2nd Ctrl+C = -2)
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal.SIG_IGN)
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
