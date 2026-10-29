"""launch_testing: display_urdf.launch.py (headless) publishes the full TF tree.

Run:  launch_test Essential_ROS/Week_07_URDF_Robot_Modeling/test/test_display_launch.py
      (or via colcon test --packages-select amr_week07)
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


@pytest.mark.launch_test
def generate_test_description():
    launch_file = os.path.join(get_package_share_directory('amr_week07'),
                               'launch', 'display_urdf.launch.py')
    return launch.LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(launch_file),
            launch_arguments={'use_gui': 'false', 'rviz': 'false'}.items()),
        launch_testing.actions.ReadyToTest(),
    ])


class TestDisplayUrdfTf(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('week07_tf_checker')
        cls.buffer = Buffer()
        cls.listener = TransformListener(cls.buffer, cls.node)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.try_shutdown()

    def lookup(self, parent, child, timeout=15.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if self.buffer.can_transform(parent, child, Time(), Duration(seconds=0)):
                return self.buffer.lookup_transform(parent, child, Time())
        self.fail(f'no transform {parent} -> {child} within {timeout}s')

    def test_static_chain_footprint_base_lidar(self):
        t = self.lookup('base_footprint', 'base_link').transform.translation
        self.assertAlmostEqual(t.z, 0.08, places=6)
        t = self.lookup('base_link', 'lidar_link').transform.translation
        self.assertAlmostEqual(t.x, 0.08, places=6)
        self.assertAlmostEqual(t.z, 0.095, places=6)
        t = self.lookup('base_footprint', 'lidar_link').transform.translation
        self.assertAlmostEqual(t.z, 0.175, places=6)

    def test_wheel_links_from_joint_states(self):
        # Wheel transforms are on /tf (continuous joints) and need /joint_states
        # from joint_state_publisher; without it they would never appear.
        for wheel, y in (('left_wheel_link', 0.12), ('right_wheel_link', -0.12)):
            tf = self.lookup('base_footprint', wheel)
            self.assertAlmostEqual(tf.transform.translation.y, y, places=6)
            self.assertAlmostEqual(tf.transform.translation.z, 0.08, places=6)

    def test_camera_optical_quaternion(self):
        q = self.lookup('camera_link', 'camera_optical_link').transform.rotation
        got = [q.x, q.y, q.z, q.w]
        expected = [-0.5, 0.5, -0.5, 0.5]
        if got[3] < 0:
            got = [-v for v in got]
        for g, e in zip(got, expected):
            self.assertAlmostEqual(g, e, places=5)


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        launch_testing.asserts.assertExitCodes(
            proc_info, allowable_exit_codes=[0, -2, -15])
