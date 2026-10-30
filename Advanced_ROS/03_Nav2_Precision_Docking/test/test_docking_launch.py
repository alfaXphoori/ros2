"""launch_testing: Nav2 docking server, headless, AprilTag detection in the loop.

1. tag hidden  -> DockRobot fails with FAILED_TO_DETECT_DOCK (904), robot does not move
2. tag visible -> DockRobot succeeds; TRUE position error (fake-base ground truth vs the real
   dock pose) < 2 cm, lateral < 1 cm, although the dock database prior is 5 cm off
3. UndockRobot succeeds and the robot backs off to the staging area (>= 0.5 m from the dock)
"""
import math
import os
import time
import unittest

import launch
import launch_testing.actions
import pytest
import rclpy
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue
from rcl_interfaces.srv import SetParameters

from amr_adv03.dock_client import DockClient, pose_error

TRUE_DOCK = (1.0, 0.0, 0.0)


@pytest.mark.launch_test
def generate_test_description():
    launch_file = os.path.join(get_package_share_directory('amr_adv03'), 'launch',
                               'docking_sim.launch.py')
    return launch.LaunchDescription([
        launch.actions.IncludeLaunchDescription(PythonLaunchDescriptionSource(launch_file)),
        launch_testing.actions.ReadyToTest(),
    ])


class TestDocking(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.client = DockClient()

    @classmethod
    def tearDownClass(cls):
        cls.client.destroy_node()
        rclpy.shutdown()

    def set_tag_visible(self, visible):
        srv = self.client.create_client(SetParameters, '/synthetic_tag_camera/set_parameters')
        self.assertTrue(srv.wait_for_service(timeout_sec=20.0))
        req = SetParameters.Request()
        req.parameters = [Parameter(name='tag_visible', value=ParameterValue(
            type=ParameterType.PARAMETER_BOOL, bool_value=visible))]
        # Retry: right after wait_for_service() the server may not see our response reader yet
        # and drops the reply ("failed to send response (timeout)" in its log). Setting the same
        # value twice is harmless.
        for _ in range(3):
            fut = srv.call_async(req)
            rclpy.spin_until_future_complete(self.client, fut, timeout_sec=5.0)
            if fut.result() is not None:
                break
        self.assertIsNotNone(fut.result(), 'no reply from synthetic_tag_camera/set_parameters')
        self.assertTrue(fut.result().results[0].successful)
        end = time.monotonic() + 1.5  # let the old detections expire
        while time.monotonic() < end:
            rclpy.spin_once(self.client, timeout_sec=0.1)

    def test_dock_and_undock(self):
        start = self.client.robot_pose(timeout=20.0)
        self.assertIsNotNone(start, 'no TF odom -> base_footprint')

        # 1. no tag in the image -> the docking server cannot detect the dock
        self.set_tag_visible(False)
        result = self.client.dock(timeout=60.0)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, 904)  # FAILED_TO_DETECT_DOCK
        moved = self.client.robot_pose()
        self.assertLess(math.hypot(moved[0] - start[0], moved[1] - start[1]), 0.01)

        # 2. tag visible -> dock using the vision estimate
        self.set_tag_visible(True)
        result = self.client.dock(timeout=120.0)
        self.assertTrue(result.success, f'error_code={result.error_code}')
        err, lat, lon, eyaw = self.client.report_error('docked')
        self.assertLess(err, 0.02)
        self.assertLess(abs(lat), 0.01)
        self.assertLess(abs(math.degrees(eyaw)), 5.0)

        # 3. undock back to the staging area
        result = self.client.undock(timeout=60.0)
        self.assertTrue(result.success, f'error_code={result.error_code}')
        pose = self.client.robot_pose()
        self.assertGreater(pose_error(pose, TRUE_DOCK)[0], 0.5)


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):

    def test_no_traceback(self, proc_output):
        for line in proc_output:
            self.assertNotIn('Traceback', line.text.decode())
