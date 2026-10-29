"""launch_testing: navigate_distance action server (result, rejection, cancel, preemption)
and the client executable (must exit after a cancel)."""
import time
import unittest

import launch
import launch.actions
import launch_ros.actions
import launch_testing.actions
import launch_testing.asserts
import pytest
import rclpy
from action_msgs.msg import GoalStatus
from amr_week04.navigate_action_server import fibonacci_sequence
from example_interfaces.action import Fibonacci
from rclpy.action import ActionClient

PKG = 'amr_week04'


@pytest.mark.launch_test
def generate_test_description():
    # server for the in-process tests below
    server = launch_ros.actions.Node(package=PKG, executable='navigate_action_server',
                                     output='screen')
    # separate server+client pair in its own namespace for the client-executable test
    server_ns = launch_ros.actions.Node(package=PKG, executable='navigate_action_server',
                                        namespace='client_test', output='screen')
    client = launch_ros.actions.Node(package=PKG, executable='navigate_action_client',
                                     namespace='client_test',
                                     arguments=['cancel', '--cancel-after', '1.0'],
                                     output='screen')
    return launch.LaunchDescription([
        server, server_ns,
        launch.actions.TimerAction(period=1.0, actions=[client]),
        launch_testing.actions.ReadyToTest(),
    ]), {'client': client}


class TestNavigateAction(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('action_probe')
        cls.ac = ActionClient(cls.node, Fibonacci, '/navigate_distance')
        assert cls.ac.wait_for_server(timeout_sec=15.0), 'action server did not come up'

    @classmethod
    def tearDownClass(cls):
        cls.ac.destroy()
        cls.node.destroy_node()
        rclpy.shutdown()

    def wait(self, future, timeout):
        rclpy.spin_until_future_complete(self.node, future, timeout_sec=timeout)
        self.assertTrue(future.done(), 'timed out')
        return future.result()

    def send(self, order):
        return self.wait(self.ac.send_goal_async(Fibonacci.Goal(order=order)), 10.0)

    def test_goal_6_succeeds_with_sequence(self):
        handle = self.send(6)
        self.assertTrue(handle.accepted)
        res = self.wait(handle.get_result_async(), 15.0)
        self.assertEqual(res.status, GoalStatus.STATUS_SUCCEEDED)
        self.assertEqual(list(res.result.sequence), [0, 1, 1, 2, 3, 5, 8])
        self.assertEqual(fibonacci_sequence(6), [0, 1, 1, 2, 3, 5, 8])

    def test_negative_order_rejected(self):
        self.assertFalse(self.send(-5).accepted)

    def test_cancel_after_1s_is_canceled(self):
        handle = self.send(10)  # 9 steps x 0.5 s = 4.5 s of work
        self.assertTrue(handle.accepted)
        result_future = handle.get_result_async()
        rclpy.spin_until_future_complete(self.node, result_future, timeout_sec=1.0)
        self.assertFalse(result_future.done())
        t0 = time.monotonic()
        cancel = self.wait(handle.cancel_goal_async(), 5.0)
        self.assertEqual(len(cancel.goals_canceling), 1, 'cancel request not accepted')
        res = self.wait(result_future, 5.0)
        self.assertEqual(res.status, GoalStatus.STATUS_CANCELED)
        self.assertLess(len(res.result.sequence), len(fibonacci_sequence(10)))
        self.assertLess(time.monotonic() - t0, 2.0, 'cancel took too long to take effect')

    def test_new_goal_preempts_running_goal(self):
        first = self.send(10)
        self.assertTrue(first.accepted)
        first_result = first.get_result_async()
        rclpy.spin_until_future_complete(self.node, first_result, timeout_sec=1.0)
        second = self.send(3)
        self.assertTrue(second.accepted)
        res1 = self.wait(first_result, 5.0)
        res2 = self.wait(second.get_result_async(), 10.0)
        self.assertEqual(res1.status, GoalStatus.STATUS_ABORTED)
        self.assertEqual(res2.status, GoalStatus.STATUS_SUCCEEDED)
        self.assertEqual(list(res2.result.sequence), [0, 1, 1, 2])

    def test_client_executable_exits_after_cancel(self, proc_info, proc_output, client):
        proc_info.assertWaitForShutdown(process=client, timeout=30)
        launch_testing.asserts.assertExitCodes(proc_info, process=client)
        proc_output.assertWaitFor('status=CANCELED', process=client, timeout=1)


@launch_testing.post_shutdown_test()
class TestAfterShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        launch_testing.asserts.assertExitCodes(proc_info)
