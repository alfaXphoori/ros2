#!/usr/bin/env python3
"""
Week 03 Lab: ROS 2 Service Client
Calls the robot/set_power_mode service to switch energy saving mode on or off.

Usage:
  ros2 run amr_week03 power_service_client [true|false] [--wait 10]
  python3 power_service_client.py false --ros-args -r __ns:=/amr_01
"""

import argparse
import signal
import sys

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.utilities import remove_ros_args
from std_srvs.srv import SetBool


def ignore_further_sigint():
    """Ctrl+C under `ros2 launch` arrives twice (terminal process group + launch forwarding it).
    Ignore later SIGINTs so they cannot interrupt the cleanup and kill us with a traceback."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


class PowerServiceClient(Node):
    def __init__(self):
        super().__init__('power_service_client')
        self.cli = self.create_client(SetBool, 'robot/set_power_mode')
        self.service_name = self.resolve_service_name('robot/set_power_mode')  # e.g. /robot/...

    def wait_for_server(self, max_wait: float) -> bool:
        """Wait up to max_wait seconds (checking once per second) for the server."""
        waited = 0.0
        while not self.cli.wait_for_service(timeout_sec=1.0):
            waited += 1.0
            if waited >= max_wait:
                return False
            self.get_logger().info(f'⏳ Service {self.service_name} not available, waiting...')
        self.get_logger().info(f'✅ Service {self.service_name} is online!')
        return True

    def send_request(self, enable_eco: bool):
        req = SetBool.Request()
        req.data = enable_eco
        return self.cli.call_async(req)  # non-blocking: returns a Future immediately


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Switch the robot power mode')
    parser.add_argument('mode', nargs='?', default='true',
                        help='true/on/1 = eco mode, false/off/0 = normal mode (default: true)')
    parser.add_argument('--wait', type=float, default=10.0,
                        help='seconds to wait for the service before giving up (default: 10)')
    args = parser.parse_args(argv)
    if args.mode.lower() in ('true', '1', 'on'):
        args.enable_eco = True
    elif args.mode.lower() in ('false', '0', 'off'):
        args.enable_eco = False
    else:
        parser.error(f'mode must be true/false, got {args.mode!r}')
    return args


def main(args=None):
    rclpy.init(args=args)
    # Strip --ros-args ... so they are not mistaken for the mode argument
    cli_args = parse_args(remove_ros_args(args=sys.argv)[1:])
    client = PowerServiceClient()
    exit_code = 1
    try:
        if not client.wait_for_server(cli_args.wait):
            client.get_logger().error(
                f'❌ Service {client.service_name} not available after {cli_args.wait:.0f} s')
        else:
            future = client.send_request(cli_args.enable_eco)
            rclpy.spin_until_future_complete(client, future, timeout_sec=10.0)
            response = future.result()
            if response is not None:
                client.get_logger().info(
                    f'🎉 Service Response: success={response.success}, message="{response.message}"')
                exit_code = 0 if response.success else 1
            else:
                client.get_logger().error('❌ Service call failed or timed out!')
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        ignore_further_sigint()
        client.destroy_node()
        rclpy.try_shutdown()
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
