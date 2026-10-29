#!/usr/bin/env python3
"""
Week 03 Lab: ROS 2 Service Server
Provides a power management service allowing clients to switch between normal and power-saving modes.
"""

import signal

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_srvs.srv import SetBool


def ignore_further_sigint():
    """Ctrl+C under `ros2 launch` arrives twice (terminal process group + launch forwarding it).
    Ignore later SIGINTs so they cannot interrupt the cleanup and kill us with a traceback."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


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
    rclpy.init(args=args)
    node = PowerServiceServer()
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
