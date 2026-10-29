"""Week 11 integration test (headless Gazebo): the bridge delivers /clock, /odom
and /scan, robot_state_publisher closes the TF chain odom -> base_footprint ->
lidar_link (needed by SLAM/Nav2), and /cmd_vel actually moves the robot."""

import os
import time
import unittest

from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import Twist
import launch
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing
import launch_testing.actions
from nav_msgs.msg import Odometry
import pytest
import rclpy
from rclpy.qos import qos_profile_sensor_data
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import LaserScan
import tf2_ros


@pytest.mark.launch_test
def generate_test_description():
    # Own Gazebo Transport partition per test file (inherited by the launched gz
    # server and by gz CLI calls made from this process during the test)
    os.environ['GZ_PARTITION'] = \
        f"{os.environ.get('GZ_PARTITION', 'amr')}_{os.path.basename(__file__)[:-3]}"
    sim = launch.actions.IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('amr_week11'), 'launch', 'gazebo_world.launch.py')),
        launch_arguments={'headless': 'true'}.items())
    return launch.LaunchDescription([sim, launch_testing.actions.ReadyToTest()])


class TestSimBridge(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('w11_sim_test',
                                     parameter_overrides=[rclpy.parameter.Parameter(
                                         'use_sim_time', value=True)])
        cls.msgs = {'clock': [], 'odom': [], 'scan': []}
        cls.node.create_subscription(Clock, '/clock', cls.msgs['clock'].append, 10)
        cls.node.create_subscription(Odometry, '/odom', cls.msgs['odom'].append, 10)
        cls.node.create_subscription(LaserScan, '/scan', cls.msgs['scan'].append,
                                     qos_profile_sensor_data)
        cls.tf_buffer = tf2_ros.Buffer()
        cls.tf_listener = tf2_ros.TransformListener(cls.tf_buffer, cls.node)
        cls.cmd_pub = cls.node.create_publisher(Twist, '/cmd_vel', 10)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.try_shutdown()

    def spin_until(self, cond, timeout):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if cond():
                return True
        return False

    def test_1_topics_arrive(self):
        ok = self.spin_until(lambda: all(self.msgs[k] for k in self.msgs), 90.0)
        self.assertTrue(ok, {k: len(v) for k, v in self.msgs.items()})
        scan = self.msgs['scan'][-1]
        self.assertEqual(scan.header.frame_id, 'lidar_link')
        self.assertEqual(len(scan.ranges), 360)
        # inside a 10 x 10 m room every beam should hit something within 10 m
        valid = [r for r in scan.ranges if scan.range_min <= r <= scan.range_max]
        self.assertGreater(len(valid), 300)

    def test_2_tf_chain_reaches_lidar(self):
        ok = self.spin_until(lambda: self.tf_buffer.can_transform(
            'odom', 'lidar_link', rclpy.time.Time()), 30.0)
        self.assertTrue(ok, 'no TF odom -> base_footprint -> base_link -> lidar_link')

    def test_3_cmd_vel_moves_robot(self):
        self.assertTrue(self.spin_until(lambda: self.msgs['odom'], 60.0))
        x0 = self.msgs['odom'][-1].pose.pose.position.x
        cmd = Twist()
        cmd.linear.x = 0.3
        clock = self.node.get_clock()
        start = clock.now()
        # 3 s of *simulated* time at 0.3 m/s (independent of real-time factor)
        while (clock.now() - start).nanoseconds < 3e9:
            self.cmd_pub.publish(cmd)
            rclpy.spin_once(self.node, timeout_sec=0.05)
        self.cmd_pub.publish(Twist())
        self.spin_until(lambda: False, 1.0)
        x1 = self.msgs['odom'][-1].pose.pose.position.x
        self.assertGreater(x1 - x0, 0.5, f'odom moved only {x1 - x0:.3f} m')


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
            self.assertIn(info.returncode, allowed, info.process_name)
