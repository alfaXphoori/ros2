"""launch_testing: tf_lab.launch.py tf_source:=urdf.

Exactly one node publishes /tf_static and the listener prints the lecture example
camera_link (1.2, 0.3, 0.0) -> base_link (1.40, 0.30, 0.02).
"""
import os
import time
import unittest

import launch
import launch_testing.actions
import pytest
import rclpy
from ament_index_python.packages import get_package_share_directory
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from rclpy.duration import Duration
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener
from domain_coordinator import domain_id

# Reserve an isolated ROS_DOMAIN_ID for this test module (same mechanism as
# add_ros_isolated_launch_test) so packages tested in parallel never see each
# other's /tf or nodes. Keep a reference: the port reservation is released when
# the context manager object is garbage-collected.
_DOMAIN_RESERVATION = domain_id()
os.environ['ROS_DOMAIN_ID'] = str(_DOMAIN_RESERVATION.__enter__())

TF_SOURCE = 'urdf'


@pytest.mark.launch_test
def generate_test_description():
    lab = os.path.join(get_package_share_directory('amr_week09'), 'launch', 'tf_lab.launch.py')
    return launch.LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(lab),
                                 launch_arguments={'tf_source': TF_SOURCE}.items()),
        launch_testing.actions.ReadyToTest(),
    ])


class TestTfLab(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('week09_tf_checker')
        cls.buffer = Buffer()
        cls.listener = TransformListener(cls.buffer, cls.node)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.try_shutdown()

    def lookup(self, parent, child, timeout=20.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if self.buffer.can_transform(parent, child, Time(), Duration(seconds=0)):
                return self.buffer.lookup_transform(parent, child, Time()).transform
        self.fail(f'no transform {parent} -> {child}')

    def test_listener_prints_lecture_example(self, proc_output):
        proc_output.assertWaitFor('X=1.40m, Y=0.30m, Z=0.02m', timeout=30, stream='stderr')

    def test_optical_frame_quaternion(self):
        q = self.lookup('camera_link', 'camera_optical_link').rotation
        got = [q.x, q.y, q.z, q.w]
        if got[3] < 0:
            got = [-v for v in got]
        for g, e in zip(got, [-0.5, 0.5, -0.5, 0.5]):
            self.assertAlmostEqual(g, e, places=5)

    def test_single_tf_static_source(self):
        t = self.lookup('base_link', 'lidar_link').translation
        self.assertAlmostEqual(t.x, 0.08, places=6)
        self.assertAlmostEqual(t.z, 0.095, places=6)
        # Count only publishers from the lab (our checker node does not publish)
        end = time.monotonic() + 5.0
        while time.monotonic() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)
        names = [i.node_name for i in self.node.get_publishers_info_by_topic('/tf_static')]
        expected = {'broadcaster': ['static_sensor_broadcaster'],
                    'urdf': ['robot_state_publisher']}[TF_SOURCE]
        self.assertEqual(sorted(names), expected)


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        launch_testing.asserts.assertExitCodes(proc_info, allowable_exit_codes=[0, -2, -15])
