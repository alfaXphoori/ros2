"""launch_testing: ros2_control with mock hardware (launch/mock_diff_drive.launch.py).

* controller_manager reports joint_state_broadcaster and diff_drive_controller as active
* diff_drive_controller listens to TwistStamped on /diff_drive_controller/cmd_vel;
  nothing consumes a plain Twist on /cmd_vel (the old lab command did nothing)
* TwistStamped v=0.5 m/s, w=1.0 rad/s -> /joint_states wheel velocities match the inverse
  kinematics (left 4.75, right 7.75 rad/s) and the odometry twist/pose advance
* after cmd_vel_timeout (0.5 s) without commands the wheels stop
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
from controller_manager_msgs.srv import ListControllers
from geometry_msgs.msg import TwistStamped
from launch.launch_description_sources import PythonLaunchDescriptionSource
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState

from amr_adv01.kinematics import inverse_kinematics

V, OMEGA = 0.5, 1.0
TOL = 0.02  # rad/s


@pytest.mark.launch_test
def generate_test_description():
    launch_file = os.path.join(get_package_share_directory('amr_adv01'), 'launch',
                               'mock_diff_drive.launch.py')
    return launch.LaunchDescription([
        launch.actions.IncludeLaunchDescription(PythonLaunchDescriptionSource(launch_file)),
        launch_testing.actions.ReadyToTest(),
    ])


def spin_until(node, predicate, timeout):
    end = time.monotonic() + timeout
    while time.monotonic() < end and not predicate():
        rclpy.spin_once(node, timeout_sec=0.05)
    return predicate()


class TestMockDiffDrive(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('adv01_probe')
        cls.joint_vel = {}
        cls.odom = []
        cls.node.create_subscription(JointState, '/joint_states', cls._on_js, 10)
        cls.node.create_subscription(Odometry, '/diff_drive_controller/odom', cls.odom.append, 10)
        cls.cmd_pub = cls.node.create_publisher(TwistStamped, '/diff_drive_controller/cmd_vel', 10)
        cls.list_client = cls.node.create_client(ListControllers,
                                                 '/controller_manager/list_controllers')

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    @classmethod
    def _on_js(cls, msg):
        cls.joint_vel.update(zip(msg.name, msg.velocity))

    def controller_states(self):
        if not self.list_client.wait_for_service(timeout_sec=5.0):
            return {}
        future = self.list_client.call_async(ListControllers.Request())
        rclpy.spin_until_future_complete(self.node, future, timeout_sec=5.0)
        if not future.done() or future.result() is None:
            return {}
        return {c.name: c.state for c in future.result().controller}

    def wait_controllers_active(self):
        states = {}
        end = time.monotonic() + 60.0
        while time.monotonic() < end:
            states = self.controller_states()
            if states.get('joint_state_broadcaster') == 'active' and \
                    states.get('diff_drive_controller') == 'active':
                break
            spin_until(self.node, lambda: False, 0.5)  # keep spinning while waiting
        return states

    def drive(self, v, omega, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            msg = TwistStamped()
            msg.header.stamp = self.node.get_clock().now().to_msg()
            msg.header.frame_id = 'base_footprint'
            msg.twist.linear.x = v
            msg.twist.angular.z = omega
            self.cmd_pub.publish(msg)
            spin_until(self.node, lambda: False, 0.05)

    def test_1_controllers_active(self):
        states = self.wait_controllers_active()
        self.assertEqual(states.get('joint_state_broadcaster'), 'active', states)
        self.assertEqual(states.get('diff_drive_controller'), 'active', states)

    def test_2_cmd_vel_interface(self):
        self.wait_controllers_active()
        self.assertTrue(spin_until(
            self.node,
            lambda: self.node.count_subscribers('/diff_drive_controller/cmd_vel') > 0, 10.0))
        types = dict(self.node.get_topic_names_and_types())
        self.assertEqual(types.get('/diff_drive_controller/cmd_vel'),
                         ['geometry_msgs/msg/TwistStamped'])
        # a plain Twist on /cmd_vel (old lab sheet) has no consumer at all
        self.assertEqual(self.node.count_subscribers('/cmd_vel'), 0)

    def test_3_wheel_speeds_match_inverse_kinematics(self):
        self.wait_controllers_active()
        self.assertTrue(spin_until(self.node, lambda: len(self.odom) > 0, 10.0), 'no odom')
        start = self.odom[-1].pose.pose.position
        # 1 s acceleration ramp (max_acceleration 1.0 m/s^2) + steady state
        self.drive(V, OMEGA, 2.5)
        exp_l, exp_r = inverse_kinematics(V, OMEGA)
        self.assertAlmostEqual(exp_r, 7.75, places=6)  # quiz answer in README.md
        self.assertAlmostEqual(self.joint_vel['left_wheel_joint'], exp_l, delta=TOL)
        self.assertAlmostEqual(self.joint_vel['right_wheel_joint'], exp_r, delta=TOL)
        twist = self.odom[-1].twist.twist
        self.assertAlmostEqual(twist.linear.x, V, delta=0.01)
        self.assertAlmostEqual(twist.angular.z, OMEGA, delta=0.01)
        end = self.odom[-1].pose.pose.position
        self.assertGreater(math.hypot(end.x - start.x, end.y - start.y), 0.3,
                           'odometry did not advance')

    def test_4_wheels_stop_after_cmd_vel_timeout(self):
        self.wait_controllers_active()
        self.drive(0.3, 0.0, 1.0)
        self.assertGreater(abs(self.joint_vel.get('left_wheel_joint', 0.0)), 1.0)
        # no more commands: cmd_vel_timeout (0.5 s) + deceleration ramp
        self.assertTrue(spin_until(
            self.node,
            lambda: abs(self.joint_vel['left_wheel_joint']) < 1e-3
            and abs(self.joint_vel['right_wheel_joint']) < 1e-3, 5.0),
            f'wheels still turning: {self.joint_vel}')


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):

    def test_no_traceback(self, proc_output):
        for line in proc_output:
            self.assertNotIn('Traceback', line.text.decode())
