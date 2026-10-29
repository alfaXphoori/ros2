"""Week 15 integration test (headless Gazebo + Nav2 + custom BT): bt_navigator
loads and activates with OUR behavior tree, and the full 5-station patrol
finishes with every goal SUCCEEDED (waypoint_patrol exits 0)."""

import os
import subprocess
import time
import unittest

from ament_index_python.packages import get_package_share_directory
from amr_week11.ground_truth import robot_pose
import launch
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing
import launch_testing.actions
from lifecycle_msgs.srv import GetState
import pytest
from rcl_interfaces.srv import GetParameters
import rclpy

BT = os.path.join(get_package_share_directory('amr_week15'), 'behavior_trees',
                  'patrol_nav_to_pose.xml')


@pytest.mark.launch_test
def generate_test_description():
    os.environ['GZ_PARTITION'] = \
        f"{os.environ.get('GZ_PARTITION', 'amr')}_{os.path.basename(__file__)[:-3]}"
    system = launch.actions.IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('amr_week15'), 'launch', 'patrol_system.launch.py')),
        launch_arguments={'headless': 'true'}.items())
    return launch.LaunchDescription([system, launch_testing.actions.ReadyToTest()])


class TestPatrol(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('w15_patrol_test')

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.try_shutdown()

    def call(self, srv, name, req):
        cli = self.node.create_client(srv, name)
        self.assertTrue(cli.wait_for_service(timeout_sec=60.0), name)
        fut = cli.call_async(req)
        rclpy.spin_until_future_complete(self.node, fut, timeout_sec=10.0)
        self.assertIsNotNone(fut.result(), name)
        return fut.result()

    def test_1_custom_bt_active(self):
        values = self.call(GetParameters, '/bt_navigator/get_parameters',
                           GetParameters.Request(names=['default_nav_to_pose_bt_xml'])).values
        self.assertEqual(values[0].string_value, BT)
        # bt_navigator parses the default tree when it activates; a broken XML or an
        # unknown node type would leave it inactive
        state = ''
        deadline = time.monotonic() + 120.0
        while time.monotonic() < deadline:
            state = self.call(GetState, '/bt_navigator/get_state',
                              GetState.Request()).current_state.label
            if state == 'active':
                break
            time.sleep(1.0)
        self.assertEqual(state, 'active')

    def test_2_patrol_all_succeeded(self):
        init = subprocess.run(
            ['ros2', 'run', 'amr_week14', 'amcl_initial_pose', '--ros-args',
             '-p', 'use_sim_time:=true'], capture_output=True, text=True, timeout=90)
        print(init.stderr[-1500:])
        self.assertEqual(init.returncode, 0)
        patrol = subprocess.run(
            ['ros2', 'run', 'amr_week15', 'waypoint_patrol', '--ros-args',
             '-p', 'use_sim_time:=true', '-p', 'dwell_scale:=0.0'],
            capture_output=True, text=True, timeout=420)
        print(patrol.stderr[-4000:])
        self.assertEqual(patrol.returncode, 0, patrol.stderr[-2000:])
        self.assertIn('5/5 stations SUCCEEDED', patrol.stderr)
        x, y, yaw = robot_pose()
        print(f'[w15] final ground truth x={x:.3f} y={y:.3f} yaw={yaw:.3f}')
        self.assertLess((x * x + y * y) ** 0.5, 0.45)


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        # Nodes must exit cleanly. gz sim (process 'gazebo') sometimes ignores SIGINT and
        # SIGTERM while shutting down after a long run and is SIGKILLed (-9) by launch;
        # it is a single process, so nothing is left running.
        for info in proc_info:
            allowed = (0, -2, -15, 130, 143)
            if info.process_name.startswith('gazebo'):
                allowed += (-9,)
            # nav2 collision_monitor (Jazzy 1.3.13) sometimes segfaults (-11) in on_cleanup:
            # a scan callback still looks up TF while the Scan source is destroyed (seen
            # in the log right before the crash); only after the test has passed
            if info.process_name.startswith('collision_monitor'):
                allowed += (-11,)
            # a lifecycle_manager that lost a change_state reply (healed by the guard /
            # supervisor) is still blocked in that call and only stops on SIGKILL (-9)
            if info.process_name.startswith('lifecycle_manager'):
                allowed += (-9,)
            self.assertIn(info.returncode, allowed, info.process_name)
