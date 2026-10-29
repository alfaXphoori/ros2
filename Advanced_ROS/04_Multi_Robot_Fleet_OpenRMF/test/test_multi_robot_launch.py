"""launch_testing: two namespaced AMRs from multi_robot_fleet.launch.py (headless).

Checks
  * nodes /amr_01/robot_state_publisher, /amr_02/robot_state_publisher (+ fake_diff_drive)
  * per-robot topics are namespaced and nothing collides on a global name
  * TF amr_0X/base_link -> amr_0X/left_wheel_link resolves (needs joint_states)
  * one shared TF tree: map -> amr_02/base_footprint is the amr_02 start pose
  * driving /amr_01/cmd_vel moves only amr_01

Run:  colcon test --packages-select amr_adv04
      launch_test Advanced_ROS/04_Multi_Robot_Fleet_OpenRMF/test/test_multi_robot_launch.py
"""
import os
import time
import unittest

import launch
import launch_testing.actions
import launch_testing.asserts
import pytest
import rclpy
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import Twist
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from nav_msgs.msg import Odometry
from rclpy.duration import Duration
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener

ROBOTS = ('amr_01', 'amr_02')


@pytest.mark.launch_test
def generate_test_description():
    launch_file = os.path.join(get_package_share_directory('amr_adv04'),
                               'launch', 'multi_robot_fleet.launch.py')
    return launch.LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(launch_file)),
        launch_testing.actions.ReadyToTest(),
    ])


class TestMultiRobotFleet(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('adv04_fleet_checker')
        cls.buffer = Buffer()
        cls.listener = TransformListener(cls.buffer, cls.node)
        cls.odom = {r: None for r in ROBOTS}
        for r in ROBOTS:
            cls.node.create_subscription(
                Odometry, f'/{r}/odom',
                lambda msg, r=r: cls.odom.__setitem__(r, msg), 10)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.try_shutdown()

    def spin_for(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            rclpy.spin_once(self.node, timeout_sec=0.05)

    def wait_until(self, predicate, timeout, what):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if predicate():
                return
        self.fail(f'timed out after {timeout}s waiting for {what}')

    def lookup(self, parent, child, timeout=15.0):
        self.wait_until(lambda: self.buffer.can_transform(parent, child, Time(),
                                                          Duration(seconds=0)),
                        timeout, f'TF {parent} -> {child}')
        return self.buffer.lookup_transform(parent, child, Time()).transform

    def test_1_namespaced_nodes(self):
        expected = {(n, f'/{r}') for r in ROBOTS
                    for n in ('robot_state_publisher', 'fake_diff_drive', 'map_to_odom')}
        self.wait_until(
            lambda: expected <= set(self.node.get_node_names_and_namespaces()),
            20.0, f'nodes {sorted(expected)}')

    def test_2_topics_namespaced_without_collisions(self):
        per_robot = ('cmd_vel', 'odom', 'joint_states', 'robot_description')
        expected = {f'/{r}/{t}' for r in ROBOTS for t in per_robot}
        self.wait_until(
            lambda: expected <= {n for n, _ in self.node.get_topic_names_and_types()},
            20.0, f'topics {sorted(expected)}')
        topics = {n for n, _ in self.node.get_topic_names_and_types()}
        for t in per_robot:
            self.assertNotIn(f'/{t}', topics, f'/{t} must not exist un-namespaced')
        # tf is the one deliberately shared topic
        self.assertIn('/tf', topics)
        self.assertIn('/tf_static', topics)
        for r in ROBOTS:
            self.assertNotIn(f'/{r}/tf', topics)
        # exactly one robot_state_publisher publishes each robot's joint-state input
        for r in ROBOTS:
            pubs = self.node.get_publishers_info_by_topic(f'/{r}/joint_states')
            self.assertEqual([(p.node_namespace, p.node_name) for p in pubs],
                             [(f'/{r}', 'fake_diff_drive')])

    def test_3_wheel_tf_per_robot(self):
        for r in ROBOTS:
            for wheel, y in (('left_wheel_link', 0.12), ('right_wheel_link', -0.12)):
                t = self.lookup(f'{r}/base_link', f'{r}/{wheel}')
                self.assertAlmostEqual(t.translation.y, y, places=6)

    def test_4_one_shared_tree_with_start_poses(self):
        t = self.lookup('map', 'amr_02/base_footprint')
        self.assertAlmostEqual(t.translation.x, 0.0, places=3)
        self.assertAlmostEqual(t.translation.y, 1.5, places=3)
        t = self.lookup('amr_01/base_link', 'amr_02/base_link')
        self.assertAlmostEqual(t.translation.y, 1.5, places=3)
        # un-prefixed frames must not exist at all
        self.assertFalse(self.buffer.can_transform('base_link', 'left_wheel_link', Time(),
                                                   Duration(seconds=0)))

    def test_5_cmd_vel_moves_only_its_own_robot(self):
        self.wait_until(lambda: all(self.odom.values()), 15.0, 'odom of both robots')
        pub = self.node.create_publisher(Twist, '/amr_01/cmd_vel', 10)
        cmd = Twist()
        cmd.linear.x = 0.5
        end = time.monotonic() + 2.0
        while time.monotonic() < end:
            pub.publish(cmd)
            self.spin_for(0.1)
        self.spin_for(1.0)   # let the cmd_vel timeout stop the robot
        x1 = self.odom['amr_01'].pose.pose.position.x
        x2 = self.odom['amr_02'].pose.pose.position.x
        self.assertGreater(x1, 0.6, f'amr_01 should have driven ~1 m, odom x={x1:.3f}')
        self.assertLess(x1, 1.4)
        self.assertAlmostEqual(x2, 0.0, places=6, msg='amr_02 must not move')
        self.assertAlmostEqual(self.odom['amr_01'].twist.twist.linear.x, 0.0,
                               msg='robot must stop when cmd_vel stops')
        t = self.lookup('map', 'amr_01/base_footprint')
        self.assertAlmostEqual(t.translation.x, x1, delta=0.05)
        self.node.destroy_publisher(pub)


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        launch_testing.asserts.assertExitCodes(
            proc_info, allowable_exit_codes=[0, -2, -15])
