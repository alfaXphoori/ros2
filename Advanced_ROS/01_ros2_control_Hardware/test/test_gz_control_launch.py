"""launch_testing: the module-01 robot in headless Gazebo Sim via gz_ros2_control.

gz sim -s -r --headless-rendering empty.sdf + ros_gz_sim create + spawners
(launch/gz_diff_drive.launch.py). Checks that both controllers become active inside the
gz_ros2_control controller_manager and that a TwistStamped command spins the simulated
wheels at the inverse-kinematics speeds and moves the robot.
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


@pytest.mark.launch_test
def generate_test_description():
    launch_file = os.path.join(get_package_share_directory('amr_adv01'), 'launch',
                               'gz_diff_drive.launch.py')
    return launch.LaunchDescription([
        launch.actions.IncludeLaunchDescription(PythonLaunchDescriptionSource(launch_file)),
        launch_testing.actions.ReadyToTest(),
    ])


def spin_until(node, predicate, timeout):
    end = time.monotonic() + timeout
    while time.monotonic() < end and not predicate():
        rclpy.spin_once(node, timeout_sec=0.05)
    return predicate()


class TestGazeboDiffDrive(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('adv01_gz_probe')
        cls.joint_vel = {}
        cls.odom = []
        cls.node.create_subscription(
            JointState, '/joint_states',
            lambda m: cls.joint_vel.update(zip(m.name, m.velocity)), 10)
        cls.node.create_subscription(Odometry, '/diff_drive_controller/odom', cls.odom.append, 10)
        cls.pub = cls.node.create_publisher(TwistStamped, '/diff_drive_controller/cmd_vel', 10)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def controllers_active(self):
        client = self.node.create_client(ListControllers, '/controller_manager/list_controllers')
        try:
            end = time.monotonic() + 90.0
            while time.monotonic() < end:
                if client.wait_for_service(timeout_sec=2.0):
                    fut = client.call_async(ListControllers.Request())
                    rclpy.spin_until_future_complete(self.node, fut, timeout_sec=5.0)
                    states = {c.name: c.state for c in (fut.result().controller
                                                        if fut.result() else [])}
                    if states.get('joint_state_broadcaster') == 'active' and \
                            states.get('diff_drive_controller') == 'active':
                        return True
                time.sleep(1.0)
            return False
        finally:
            self.node.destroy_client(client)

    def test_gazebo_wheels_follow_twist(self):
        self.assertTrue(self.controllers_active(), 'controllers not active in gz_ros2_control')
        self.assertTrue(spin_until(self.node, lambda: len(self.odom) > 0, 20.0), 'no odom')
        start = self.odom[-1].pose.pose.position
        end_t = time.monotonic() + 4.0
        while time.monotonic() < end_t:
            msg = TwistStamped()
            msg.header.stamp = self.node.get_clock().now().to_msg()
            msg.twist.linear.x = 0.5
            msg.twist.angular.z = 1.0
            self.pub.publish(msg)
            spin_until(self.node, lambda: False, 0.05)
        exp_l, exp_r = inverse_kinematics(0.5, 1.0)
        self.assertAlmostEqual(self.joint_vel['left_wheel_joint'], exp_l, delta=0.1)
        self.assertAlmostEqual(self.joint_vel['right_wheel_joint'], exp_r, delta=0.1)
        end = self.odom[-1].pose.pose.position
        self.assertGreater(math.hypot(end.x - start.x, end.y - start.y), 0.3)
