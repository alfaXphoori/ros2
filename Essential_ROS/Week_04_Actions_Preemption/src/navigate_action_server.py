#!/usr/bin/env python3
"""
Week 04 Lab: ROS 2 Action Server with cancellation and goal preemption
Simulates a long-running navigation task (one Fibonacci step every 0.5 s) using the
standard example_interfaces/action/Fibonacci interface.

* Cancellation: the client asks to stop -> the goal ends as CANCELED.
* Preemption:   a NEW goal arrives while one is running -> the running goal is ABORTED and the
                new one takes over (single-goal policy, like Nav2's navigate_to_pose).
                Disable with --ros-args -p preempt:=false (new goals are then rejected while busy).

execute_callback sleeps between steps, so the node runs on a MultiThreadedExecutor and all
action callbacks share a ReentrantCallbackGroup: other threads stay free to accept cancel
requests and new goals while a goal is executing.
"""

import signal
import threading
import time

import rclpy
from example_interfaces.action import Fibonacci
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node


def ignore_further_sigint():
    """Ctrl+C under `ros2 launch` arrives twice (terminal process group + launch forwarding it).
    Ignore later SIGINTs so they cannot interrupt the cleanup and kill us with a traceback."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


STEP_PERIOD = 0.5  # seconds per "distance step"


def fibonacci_sequence(order: int):
    """Sequence the server returns for a goal of `order`: [0, 1] plus order-1 more terms."""
    seq = [0, 1]
    for i in range(1, order):
        seq.append(seq[i] + seq[i - 1])
    return seq


class NavigateActionServer(Node):
    def __init__(self):
        super().__init__('navigate_action_server')
        self.declare_parameter('preempt', True)
        self._goal_lock = threading.Lock()
        self._active_goal = None
        self._action_server = ActionServer(
            self,
            Fibonacci,
            'navigate_distance',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            handle_accepted_callback=self.handle_accepted_callback,
            cancel_callback=self.cancel_callback,
            callback_group=ReentrantCallbackGroup(),
        )
        self.get_logger().info('🏁 [NavigateActionServer] Ready to receive navigation distance goals.')

    def goal_callback(self, goal_request):
        self.get_logger().info(f'Received goal request with order/distance steps: {goal_request.order}')
        if goal_request.order < 0:
            self.get_logger().error('Rejecting negative distance step goal.')
            return GoalResponse.REJECT
        if not self.get_parameter('preempt').value:
            with self._goal_lock:
                if self._active_goal is not None and self._active_goal.is_active:
                    self.get_logger().error('Busy and preempt:=false -> rejecting new goal.')
                    return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def handle_accepted_callback(self, goal_handle):
        with self._goal_lock:
            # Single-goal policy: a newer goal preempts (aborts) the one still running
            if self._active_goal is not None and self._active_goal.is_active:
                self.get_logger().warn('⚠️ New goal accepted -> preempting (aborting) the current goal.')
                self._active_goal.abort()
            self._active_goal = goal_handle
        goal_handle.execute()

    def cancel_callback(self, goal_handle):
        self.get_logger().warn('Received request to cancel goal execution!')
        return CancelResponse.ACCEPT

    def _stop_requested(self, goal_handle):
        """True if the goal was preempted (already aborted) or canceled (then marks it CANCELED).

        Call with _goal_lock held, so a preempting abort() from another thread can never race
        with canceled()/succeed() in this thread.
        """
        if not goal_handle.is_active:  # aborted by handle_accepted_callback
            self.get_logger().warn('Goal preempted by a newer goal.')
            return True
        if goal_handle.is_cancel_requested:
            goal_handle.canceled()
            self.get_logger().warn('Goal canceled by client request.')
            return True
        return False

    def execute_callback(self, goal_handle):
        self.get_logger().info('Executing navigation distance steps...')
        feedback_msg = Fibonacci.Feedback()
        feedback_msg.sequence = [0, 1]
        order = goal_handle.request.order
        result = Fibonacci.Result()

        for i in range(1, order):
            with self._goal_lock:
                if self._stop_requested(goal_handle):
                    result.sequence = feedback_msg.sequence
                    return result

            feedback_msg.sequence.append(
                feedback_msg.sequence[i] + feedback_msg.sequence[i - 1]
            )
            self.get_logger().info(f'Step {i}/{order} progress: {list(feedback_msg.sequence)}')
            goal_handle.publish_feedback(feedback_msg)
            time.sleep(STEP_PERIOD)  # OK here: other executor threads keep serving cancel/goals

        with self._goal_lock:
            if self._stop_requested(goal_handle):
                result.sequence = feedback_msg.sequence
                return result
            goal_handle.succeed()
        result.sequence = feedback_msg.sequence
        self.get_logger().info(f'Navigation sequence succeeded with result: {list(result.sequence)}')
        return result


def main(args=None):
    rclpy.init(args=args)
    node = NavigateActionServer()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        ignore_further_sigint()
        executor.shutdown()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
