"""launch_testing: SetBool power-mode service, the client executable and the deadlock demo."""
import unittest

import launch
import launch.actions
import launch_ros.actions
import launch_testing.actions
import launch_testing.asserts
import pytest
import rclpy
from amr_week03.deadlock_demo import run as run_deadlock_demo
from std_srvs.srv import SetBool

PKG = 'amr_week03'


@pytest.mark.launch_test
def generate_test_description():
    server = launch_ros.actions.Node(package=PKG, executable='power_service_server',
                                     output='screen')
    # Client gets a ROS argument *and* a mode: the mode must still be parsed as 'false'
    client = launch_ros.actions.Node(package=PKG, executable='power_service_client',
                                     arguments=['false'], name='cli_under_test', output='screen')
    return launch.LaunchDescription([
        server,
        launch.actions.TimerAction(period=1.0, actions=[client]),
        launch_testing.actions.ReadyToTest(),
    ]), {'server': server, 'client': client}


class TestPowerService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('power_probe')
        cls.cli = cls.node.create_client(SetBool, '/robot/set_power_mode')
        assert cls.cli.wait_for_service(timeout_sec=15.0), 'server did not come up'

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def call(self, value):
        future = self.cli.call_async(SetBool.Request(data=value))
        rclpy.spin_until_future_complete(self.node, future, timeout_sec=10.0)
        self.assertTrue(future.done(), 'no response')
        return future.result()

    def test_set_true_enables_eco_mode(self):
        res = self.call(True)
        self.assertTrue(res.success)
        self.assertIn('Power saving mode ENABLED', res.message)

    def test_set_false_restores_normal_mode(self):
        res = self.call(False)
        self.assertTrue(res.success)
        self.assertIn('Normal power mode RESTORED', res.message)

    def test_client_executable_with_ros_args(self, proc_output, client):
        # launch_ros appends --ros-args -r __node:=cli_under_test after 'false'
        proc_output.assertWaitFor('Normal power mode RESTORED', process=client, timeout=20)

    def test_sync_call_in_callback_deadlocks_single_threaded(self):
        self.assertEqual(run_deadlock_demo('deadlock', call_timeout=2.0), 'timeout')

    def test_reentrant_multithreaded_fix_succeeds(self):
        self.assertEqual(run_deadlock_demo('fixed', call_timeout=2.0), 'success')


@launch_testing.post_shutdown_test()
class TestAfterShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        launch_testing.asserts.assertExitCodes(proc_info)
