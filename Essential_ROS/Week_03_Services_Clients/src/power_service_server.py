#!/usr/bin/env python3
"""
Lab 1.2: ROS 2 Service Server
Provides a power management service allowing clients to switch between normal and power-saving modes.
"""

import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool


class PowerServiceServer(Node):
    def __init__(self):
        super().__init__('power_service_server')
        self.eco_mode = False
        self.srv = self.create_service(
            SetBool, '/robot/set_power_mode', self.handle_set_power_mode
        )
        self.get_logger().info('⚡ [PowerServiceServer] Service /robot/set_power_mode ready.')

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
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down Power Service Server...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
