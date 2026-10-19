#!/usr/bin/env python3
"""
Lab 1.3: ROS 2 Action Server
Demonstrates non-blocking long-running task execution with progress feedback and cancellation handling.
Uses standard example_interfaces/action/Fibonacci.
"""

import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from example_interfaces.action import Fibonacci


class NavigateActionServer(Node):
    def __init__(self):
        super().__init__('navigate_action_server')
        self._action_server = ActionServer(
            self,
            Fibonacci,
            '/navigate_distance',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback
        )
        self.get_logger().info('🏁 [NavigateActionServer] Ready to receive navigation distance goals.')

    def goal_callback(self, goal_request):
        self.get_logger().info(f'Received goal request with order/distance steps: {goal_request.order}')
        if goal_request.order < 0:
            self.get_logger().error('Rejecting negative distance step goal.')
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().warn('Received request to cancel goal execution!')
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        self.get_logger().info('Executing navigation distance steps...')
        feedback_msg = Fibonacci.Feedback()
        feedback_msg.sequence = [0, 1]

        order = goal_handle.request.order

        for i in range(1, order):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.get_logger().warn('Goal canceled by client request.')
                result = Fibonacci.Result()
                result.sequence = feedback_msg.sequence
                return result

            feedback_msg.sequence.append(
                feedback_msg.sequence[i] + feedback_msg.sequence[i - 1]
            )
            self.get_logger().info(f'Step {i}/{order} progress: {feedback_msg.sequence}')
            goal_handle.publish_feedback(feedback_msg)
            time.sleep(0.5)

        goal_handle.succeed()
        result = Fibonacci.Result()
        result.sequence = feedback_msg.sequence
        self.get_logger().info(f'Navigation sequence succeeded with result: {result.sequence}')
        return result


def main(args=None):
    rclpy.init(args=args)
    node = NavigateActionServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down Navigate Action Server...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
