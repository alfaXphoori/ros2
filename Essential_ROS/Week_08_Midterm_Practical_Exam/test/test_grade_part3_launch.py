"""Autograder part 3 (25 pts): hospital_bringup.launch.py (launch_testing, headless).

Includes <EXAM_SUBMISSION_DIR>/hospital_bringup.launch.py with rviz:=false and checks that
robot_state_publisher + midterm_robot_controller come up together, the TF tree matches the
URDF specification (LiDAR, wheels) and /cmd_vel is published.
"""
import os
import sys
import time
import unittest

import launch
import launch_testing.actions
import pytest
import rclpy
from geometry_msgs.msg import Twist
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from rclpy.duration import Duration
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener
from domain_coordinator import domain_id

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exam_common import LAUNCH_PATH, NODE_NAME  # noqa: E402

# Reserve an isolated ROS_DOMAIN_ID for this test module (same mechanism as
# add_ros_isolated_launch_test) so packages tested in parallel never see each
# other's /tf or nodes. Keep a reference: the port reservation is released when
# the context manager object is garbage-collected.
_DOMAIN_RESERVATION = domain_id()
os.environ['ROS_DOMAIN_ID'] = str(_DOMAIN_RESERVATION.__enter__())


@pytest.mark.launch_test
def generate_test_description():
    return launch.LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(LAUNCH_PATH),
                                 launch_arguments={'rviz': 'false'}.items()),
        launch_testing.actions.ReadyToTest(),
    ])


class TestBringup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('midterm_launch_grader')
        cls.buffer = Buffer()
        cls.listener = TransformListener(cls.buffer, cls.node)
        cls.cmd = []
        cls.node.create_subscription(Twist, '/cmd_vel', cls.cmd.append, 10)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.try_shutdown()

    def spin_until(self, predicate, timeout):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if predicate():
                return True
        return False

    def lookup(self, parent, child):
        ok = self.spin_until(
            lambda: self.buffer.can_transform(parent, child, Time(), Duration(seconds=0)), 30.0)
        self.assertTrue(ok, f'no TF {parent} -> {child}')
        return self.buffer.lookup_transform(parent, child, Time()).transform.translation

    def test_launch_file_mentions_rviz(self):
        with open(LAUNCH_PATH, encoding='utf-8') as f:
            self.assertIn('rviz2', f.read(), 'launch file must start rviz2')

    def test_nodes_running(self):
        def names():
            return {n for n, _ in self.node.get_node_names_and_namespaces()}
        self.assertTrue(self.spin_until(lambda: NODE_NAME in names(), 30.0),
                        f'{NODE_NAME} not running')
        self.assertTrue(self.spin_until(lambda: 'robot_state_publisher' in names(), 10.0),
                        'robot_state_publisher not running')

    def test_tf_lidar_and_wheels(self):
        t = self.lookup('base_footprint', 'lidar_link')
        self.assertAlmostEqual(t.x, 0.12, places=3)
        self.assertAlmostEqual(t.y, 0.0, places=3)
        self.assertAlmostEqual(t.z, 0.08 + 0.18, places=3)
        for wheel, y in (('left_wheel_link', 0.17), ('right_wheel_link', -0.17)):
            t = self.lookup('base_footprint', wheel)
            self.assertAlmostEqual(t.y, y, places=3)
            self.assertAlmostEqual(t.z, 0.08, places=3)

    def test_cmd_vel_published(self):
        self.assertTrue(self.spin_until(lambda: len(self.cmd) >= 3, 15.0), 'no /cmd_vel')
        self.assertAlmostEqual(self.cmd[-1].linear.x, 0.3, places=3)
