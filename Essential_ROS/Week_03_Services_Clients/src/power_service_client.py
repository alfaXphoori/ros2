#!/usr/bin/env python3
"""
Week 03 Lab: ROS 2 Service Client
Calls /robot/set_power_mode service to request energy saving mode.
Demonstrates asynchronous service calling and response waiting.
"""

import sys
import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool


class PowerServiceClient(Node):
    def __init__(self):
        super().__init__('power_service_client')
        self.cli = self.create_client(SetBool, '/robot/set_power_mode')

        # Wait for service availability
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('⏳ Service /robot/set_power_mode not available, waiting...')

        self.get_logger().info('✅ Service /robot/set_power_mode is online!')

    def send_request(self, enable_eco: bool):
        req = SetBool.Request()
        req.data = enable_eco
        future = self.cli.call_async(req)
        return future


def main(args=None):
    rclpy.init(args=args)
    client = PowerServiceClient()

    enable_eco = True
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['false', '0', 'off']:
        enable_eco = False

    future = client.send_request(enable_eco)
    rclpy.spin_until_future_complete(client, future)

    response = future.result()
    if response is not None:
        client.get_logger().info(f'🎉 Service Response: success={response.success}, message="{response.message}"')
    else:
        client.get_logger().error('❌ Service call failed or timed out!')

    client.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
