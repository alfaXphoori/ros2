#!/usr/bin/env python3
"""
Week 04 Lab: ROS 2 Action Client
Sends navigation distance goal to /navigate_distance, receives feedback,
and demonstrates cancellation handling.
"""

import sys
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from example_interfaces.action import Fibonacci


class NavigateActionClient(Node):
    def __init__(self):
        super().__init__('navigate_action_client')
        self._action_client = ActionClient(self, Fibonacci, '/navigate_distance')
        self._cancel_timer = None

    def send_goal(self, order=6, test_cancel=False):
        self.get_logger().info('⏳ Waiting for /navigate_distance action server...')
        self._action_client.wait_for_server()

        goal_msg = Fibonacci.Goal()
        goal_msg.order = order

        self.get_logger().info(f'🚀 Sending goal with order={order}...')
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg, feedback_callback=self.feedback_callback
        )
        self._send_goal_future.add_done_callback(
            lambda future: self.goal_response_callback(future, test_cancel)
        )

    def goal_response_callback(self, future, test_cancel):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('❌ Goal was rejected by Action Server!')
            return

        self.get_logger().info('✅ Goal accepted! Executing...')

        if test_cancel:
            self.get_logger().warn('⚠️ Triggering Goal Cancellation in 1.5 seconds...')
            # Use non-blocking timer instead of time.sleep
            self._cancel_timer = self.create_timer(
                1.5, lambda: self._do_cancel(goal_handle)
            )
        else:
            get_result_future = goal_handle.get_result_async()
            get_result_future.add_done_callback(self.get_result_callback)

    def _do_cancel(self, goal_handle):
        if self._cancel_timer:
            self._cancel_timer.cancel()
            self._cancel_timer = None
        self.get_logger().warn('🛑 Sending cancel request now...')
        cancel_future = goal_handle.cancel_goal_async()
        cancel_future.add_done_callback(self.cancel_done_callback)

    def feedback_callback(self, feedback_msg):
        self.get_logger().info(f'📊 Feedback received: sequence={feedback_msg.feedback.sequence}')

    def cancel_done_callback(self, future):
        cancel_response = future.result()
        if len(cancel_response.goals_canceling) > 0:
            self.get_logger().warn('🛑 Action Goal was successfully canceled!')
        else:
            self.get_logger().info('Goal cancel was not accepted or already finished.')

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'🎉 Final Result sequence: {result.sequence}')
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    action_client = NavigateActionClient()

    test_cancel = False
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['cancel', '--cancel']:
        test_cancel = True

    action_client.send_goal(order=6, test_cancel=test_cancel)
    try:
        rclpy.spin(action_client)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass


if __name__ == '__main__':
    main()
