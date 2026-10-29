#!/usr/bin/env python3
"""
Week 04 Lab: ROS 2 Action Client
Sends a navigation-distance goal to navigate_distance, prints feedback and the final status,
then exits. Three modes:

  run      (default) wait for the result                      -> SUCCEEDED
  cancel   send cancel_goal after --cancel-after seconds       -> CANCELED
  preempt  send a 2nd goal after --cancel-after seconds; the server aborts the 1st one
                                                               -> 1st ABORTED, 2nd SUCCEEDED
Usage:
  ros2 run amr_week04 navigate_action_client [run|cancel|preempt] [--order 6] [--cancel-after 1.5]
  (the old flag form `--cancel` still works)
"""

import argparse
import signal
import sys

import rclpy
from action_msgs.msg import GoalStatus
from example_interfaces.action import Fibonacci
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.utilities import remove_ros_args


def ignore_further_sigint():
    """Ctrl+C under `ros2 launch` arrives twice (terminal process group + launch forwarding it).
    Ignore later SIGINTs so they cannot interrupt the cleanup and kill us with a traceback."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


STATUS_NAMES = {
    GoalStatus.STATUS_UNKNOWN: 'UNKNOWN', GoalStatus.STATUS_ACCEPTED: 'ACCEPTED',
    GoalStatus.STATUS_EXECUTING: 'EXECUTING', GoalStatus.STATUS_CANCELING: 'CANCELING',
    GoalStatus.STATUS_SUCCEEDED: 'SUCCEEDED', GoalStatus.STATUS_CANCELED: 'CANCELED',
    GoalStatus.STATUS_ABORTED: 'ABORTED',
}


class NavigateActionClient(Node):
    def __init__(self):
        super().__init__('navigate_action_client')
        self._action_client = ActionClient(self, Fibonacci, 'navigate_distance')

    def feedback_callback(self, feedback_msg):
        self.get_logger().info(f'📊 Feedback received: sequence={list(feedback_msg.feedback.sequence)}')

    def send_goal(self, order):
        """Send a goal and spin until the server accepts/rejects it. Returns the goal handle."""
        self.get_logger().info(f'🚀 Sending goal with order={order}...')
        future = self._action_client.send_goal_async(
            Fibonacci.Goal(order=order), feedback_callback=self.feedback_callback)
        rclpy.spin_until_future_complete(self, future)  # executor keeps running callbacks
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('❌ Goal was rejected by Action Server!')
            return None
        # the goal UUID was generated here, on the client side, by send_goal_async()
        self.get_logger().info(
            f'✅ Goal accepted (id={bytes(goal_handle.goal_id.uuid).hex()[:8]}...) Executing...')
        return goal_handle

    def wait_result(self, goal_handle, timeout_sec=None):
        """Spin until the goal finishes. Returns (status, sequence) or None on timeout."""
        future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, future, timeout_sec=timeout_sec)
        if not future.done():
            return None
        res = future.result()
        return res.status, list(res.result.sequence)

    def run(self, mode='run', order=6, cancel_after=1.5):
        """Execute one scenario; returns the final status of the (first) goal or None."""
        self.get_logger().info('⏳ Waiting for navigate_distance action server...')
        if not self._action_client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error('❌ Action server not available after 10 s')
            return None
        goal = self.send_goal(order)
        if goal is None:
            return None

        if mode == 'run':
            status, seq = self.wait_result(goal)
        else:
            # let the goal run for a while, the result arrives only if it is faster than that
            early = self.wait_result(goal, timeout_sec=cancel_after)
            if early is not None:
                status, seq = early
            elif mode == 'cancel':
                self.get_logger().warn('🛑 Sending cancel request now...')
                cancel_future = goal.cancel_goal_async()
                rclpy.spin_until_future_complete(self, cancel_future, timeout_sec=5.0)
                accepted = cancel_future.done() and len(cancel_future.result().goals_canceling) > 0
                self.get_logger().warn('🛑 Cancel request accepted by server.' if accepted
                                       else 'Cancel request was not accepted (goal finished?).')
                status, seq = self.wait_result(goal)
            else:  # preempt
                self.get_logger().warn('🔀 Sending a NEW goal (order=4) to preempt the running one...')
                second = self.send_goal(4)
                status, seq = self.wait_result(goal)
                if second is not None:
                    s2, seq2 = self.wait_result(second)
                    self.get_logger().info(
                        f'🎯 Second goal finished: status={STATUS_NAMES[s2]}, sequence={seq2}')

        self.get_logger().info(f'🏁 Goal finished: status={STATUS_NAMES[status]}, sequence={seq}')
        return status


def parse_args(argv):
    parser = argparse.ArgumentParser(description='navigate_distance action client')
    parser.add_argument('mode', nargs='?', default='run', choices=['run', 'cancel', 'preempt'])
    parser.add_argument('--cancel', action='store_true', help='same as mode "cancel"')
    parser.add_argument('--order', type=int, default=6)
    parser.add_argument('--cancel-after', type=float, default=1.5,
                        help='seconds before cancel/preempt (default 1.5)')
    args = parser.parse_args(argv)
    if args.cancel:
        args.mode = 'cancel'
    return args


def main(args=None):
    rclpy.init(args=args)
    opts = parse_args(remove_ros_args(args=sys.argv)[1:])
    node = NavigateActionClient()
    status = None
    try:
        status = node.run(opts.mode, opts.order, opts.cancel_after)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        ignore_further_sigint()
        node.destroy_node()
        rclpy.try_shutdown()
    expected = {'run': GoalStatus.STATUS_SUCCEEDED, 'cancel': GoalStatus.STATUS_CANCELED,
                'preempt': GoalStatus.STATUS_ABORTED}[opts.mode]
    return 0 if status == expected else 1


if __name__ == '__main__':
    sys.exit(main())
