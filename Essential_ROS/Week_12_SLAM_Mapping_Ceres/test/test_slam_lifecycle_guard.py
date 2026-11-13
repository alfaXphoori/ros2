"""Week 12: slam_lifecycle_guard drives slam_toolbox to ACTIVE by itself.

slam_toolbox is started with autostart:=false - the same situation as a launch that lost the
lifecycle events: nobody sends configure/activate. The guard (heal_after 2 s) must notice the
stuck `unconfigured` node, send configure + activate itself and exit 0. No simulation needed:
slam_toolbox configures and activates without scans."""

import os
import time
import unittest

from ament_index_python.packages import get_package_share_directory
import launch
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_ros.actions
import launch_testing
import launch_testing.actions
import launch_testing.asserts
from lifecycle_msgs.srv import GetState
import pytest
import rclpy


@pytest.mark.launch_test
def generate_test_description():
    slam = launch.actions.IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('slam_toolbox'), 'launch', 'online_async_launch.py')),
        launch_arguments={
            'autostart': 'false',
            'use_sim_time': 'false',
            'slam_params_file': os.path.join(get_package_share_directory('amr_week12'),
                                             'config', 'slam_toolbox_params.yaml'),
        }.items())
    guard = launch_ros.actions.Node(package='amr_week12', executable='slam_lifecycle_guard',
                                    parameters=[{'heal_after': 2.0}], output='screen')
    return launch.LaunchDescription([slam, guard, launch_testing.actions.ReadyToTest()]), \
        {'guard': guard}


class TestGuard(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('w12_guard_test')

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.try_shutdown()

    def test_guard_activates_slam_toolbox(self, proc_output, proc_info, guard):
        proc_output.assertWaitFor('slam_toolbox is ACTIVE', process=guard, timeout=60)
        proc_info.assertWaitForShutdown(process=guard, timeout=10)
        self.assertEqual(proc_info[guard].returncode, 0)
        # it really had to act: slam_toolbox was left unconfigured
        proc_output.assertWaitFor('configure -> True', process=guard, timeout=1)
        proc_output.assertWaitFor('activate -> True', process=guard, timeout=1)

        cli = self.node.create_client(GetState, '/slam_toolbox/get_state')
        self.assertTrue(cli.wait_for_service(timeout_sec=10.0))
        label = ''
        for _ in range(3):  # right after discovery the server may drop a reply: retry
            fut = cli.call_async(GetState.Request())
            rclpy.spin_until_future_complete(self.node, fut, timeout_sec=5.0)
            if fut.result() is not None:
                label = fut.result().current_state.label
                break
            time.sleep(0.5)
        self.assertEqual(label, 'active')


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        launch_testing.asserts.assertExitCodes(proc_info)
