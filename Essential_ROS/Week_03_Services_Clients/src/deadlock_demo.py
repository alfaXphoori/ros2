#!/usr/bin/env python3
"""
Week 03 Lab: the single-threaded executor deadlock, reproduced on purpose.

A timer callback calls the *synchronous* client.call() while the node is spun by a
SingleThreadedExecutor. The only executor thread is busy inside the timer callback, so it can
never process the service response -> call() waits until its timeout and returns None.

  --mode deadlock : SingleThreadedExecutor, default (MutuallyExclusive) callback group -> times out
  --mode fixed    : MultiThreadedExecutor + client in a ReentrantCallbackGroup      -> succeeds

Needs power_service_server running.  Usage:
  ros2 run amr_week03 deadlock_demo --mode deadlock
  ros2 run amr_week03 deadlock_demo --mode fixed
"""

import argparse
import signal
import sys
import time

import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import (ExternalShutdownException, MultiThreadedExecutor,
                             SingleThreadedExecutor)
from rclpy.node import Node
from rclpy.utilities import remove_ros_args
from std_srvs.srv import SetBool


def ignore_further_sigint():
    """Ctrl+C under `ros2 launch` arrives twice (terminal process group + launch forwarding it).
    Ignore later SIGINTs so they cannot interrupt the cleanup and kill us with a traceback."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


class DeadlockDemo(Node):
    def __init__(self, reentrant: bool, call_timeout: float = 3.0):
        super().__init__('deadlock_demo')
        self.call_timeout = call_timeout
        self.outcome = None  # 'success' | 'timeout' once the timer has fired
        # With reentrant=True the response callback may run on a 2nd thread while the timer blocks
        group = ReentrantCallbackGroup() if reentrant else None
        self.cli = self.create_client(SetBool, 'robot/set_power_mode', callback_group=group)
        self.timer = self.create_timer(0.5, self.timer_callback, callback_group=group)

    def timer_callback(self):
        self.timer.cancel()  # run once
        if not self.cli.wait_for_service(timeout_sec=5.0):
            self.get_logger().error('Service not available')
            self.outcome = 'no_service'
            return
        req = SetBool.Request()
        req.data = True
        name = self.resolve_service_name(self.cli.srv_name)
        self.get_logger().info(f'Calling {name} synchronously (client.call) '
                               f'from inside a timer callback...')
        start = time.monotonic()
        response = self.cli.call(req, timeout_sec=self.call_timeout)  # blocks this thread
        elapsed = time.monotonic() - start
        if response is None:
            self.outcome = 'timeout'
            self.get_logger().error(
                f'💥 DEADLOCK: no response after {elapsed:.1f} s - the executor thread was '
                f'blocked inside this callback and could not deliver the reply')
        else:
            self.outcome = 'success'
            self.get_logger().info(
                f'✅ Response after {elapsed:.3f} s: success={response.success} '
                f'(another executor thread delivered it)')


def run(mode: str, call_timeout: float = 3.0) -> str:
    """Spin a DeadlockDemo with the executor for `mode`; return its outcome."""
    reentrant = mode == 'fixed'
    node = DeadlockDemo(reentrant=reentrant, call_timeout=call_timeout)
    executor = MultiThreadedExecutor(num_threads=2) if reentrant else SingleThreadedExecutor()
    executor.add_node(node)
    try:
        deadline = time.monotonic() + call_timeout + 10.0
        while node.outcome is None and time.monotonic() < deadline:
            executor.spin_once(timeout_sec=0.1)
        return node.outcome or 'timeout'
    finally:
        executor.shutdown()
        node.destroy_node()


def main(args=None):
    rclpy.init(args=args)
    parser = argparse.ArgumentParser(description='Synchronous service call deadlock demo')
    parser.add_argument('--mode', choices=['deadlock', 'fixed'], default='deadlock')
    parser.add_argument('--timeout', type=float, default=3.0, help='client.call() timeout [s]')
    opts = parser.parse_args(remove_ros_args(args=sys.argv)[1:])
    outcome = 'timeout'
    try:
        outcome = run(opts.mode, opts.timeout)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        ignore_further_sigint()
        rclpy.try_shutdown()
    print(f'outcome: {outcome}')
    return 0 if outcome in ('timeout', 'success') else 1


if __name__ == '__main__':
    sys.exit(main())
