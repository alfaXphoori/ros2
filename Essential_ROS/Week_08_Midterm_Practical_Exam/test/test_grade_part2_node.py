"""Autograder part 2 (40 pts): behaviour of hospital_robot_node.py (launch_testing).

Starts `python3 <EXAM_SUBMISSION_DIR>/hospital_robot_node.py` and checks:
  * max_speed: double, default 0.6; 2.0 / 0.05 / integer rejected with a reason; 0.2 accepted
  * /cmd_vel Twist at ~5 Hz with linear.x = min(0.3, max_speed)
  * /sensor/temperature 70.0 -> warning log + speed throttled to 50 %; 50.0 -> normal again
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
from launch.actions import ExecuteProcess
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue
from rcl_interfaces.srv import GetParameters, SetParameters
from std_msgs.msg import Float32
from domain_coordinator import domain_id

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exam_common import NODE_NAME, NODE_PATH  # noqa: E402

# Reserve an isolated ROS_DOMAIN_ID for this test module (same mechanism as
# add_ros_isolated_launch_test) so packages tested in parallel never see each
# other's /tf or nodes. Keep a reference: the port reservation is released when
# the context manager object is garbage-collected.
_DOMAIN_RESERVATION = domain_id()
os.environ['ROS_DOMAIN_ID'] = str(_DOMAIN_RESERVATION.__enter__())

CRUISE = 0.3


@pytest.mark.launch_test
def generate_test_description():
    controller = ExecuteProcess(cmd=[sys.executable, NODE_PATH], name='student_node',
                                output='screen')
    return launch.LaunchDescription([
        controller,
        launch_testing.actions.ReadyToTest(),
    ]), {'controller': controller}


class TestControllerBehaviour(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('midterm_grader')
        cls.samples = []
        cls.node.create_subscription(
            Twist, '/cmd_vel', lambda m: cls.samples.append((time.monotonic(), m)), 10)
        cls.temp_pub = cls.node.create_publisher(Float32, '/sensor/temperature', 10)
        cls.set_cli = cls.node.create_client(SetParameters, f'/{NODE_NAME}/set_parameters')
        cls.get_cli = cls.node.create_client(GetParameters, f'/{NODE_NAME}/get_parameters')
        assert cls.set_cli.wait_for_service(timeout_sec=30.0), f'/{NODE_NAME} not found'
        assert cls.get_cli.wait_for_service(timeout_sec=10.0)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.try_shutdown()

    # ---------------------------------------------------------------- helpers
    def spin_for(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            rclpy.spin_once(self.node, timeout_sec=0.05)

    def call(self, client, request):
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self.node, future, timeout_sec=10.0)
        self.assertTrue(future.done(), 'parameter service did not answer')
        return future.result()

    def set_param(self, value):
        p = Parameter(name='max_speed')
        if isinstance(value, float):
            p.value = ParameterValue(type=ParameterType.PARAMETER_DOUBLE, double_value=value)
        else:
            p.value = ParameterValue(type=ParameterType.PARAMETER_INTEGER, integer_value=value)
        return self.call(self.set_cli, SetParameters.Request(parameters=[p])).results[0]

    def get_param(self):
        return self.call(self.get_cli, GetParameters.Request(names=['max_speed'])).values[0]

    def recent_speeds(self, seconds):
        self.samples.clear()
        self.spin_for(seconds)
        return [m.linear.x for _, m in self.samples]

    def publish_temperature(self, celsius):
        end = time.monotonic() + 10.0
        while self.temp_pub.get_subscription_count() == 0 and time.monotonic() < end:
            self.spin_for(0.1)
        self.assertGreater(self.temp_pub.get_subscription_count(), 0,
                           'node does not subscribe to /sensor/temperature')
        for _ in range(3):
            self.temp_pub.publish(Float32(data=celsius))
            self.spin_for(0.1)

    def reset(self):
        self.assertTrue(self.set_param(0.6).successful)
        self.publish_temperature(25.0)
        self.spin_for(0.5)

    # ------------------------------------------------------------------ tests
    def test_1_default_parameter_is_double_0_6(self):
        value = self.get_param()
        self.assertEqual(value.type, ParameterType.PARAMETER_DOUBLE)
        self.assertAlmostEqual(value.double_value, 0.6, places=6)

    def test_2_cmd_vel_rate_and_value(self):
        self.reset()
        self.samples.clear()
        self.spin_for(4.0)
        self.assertGreaterEqual(len(self.samples), 10, 'too few /cmd_vel messages')
        stamps = [t for t, _ in self.samples]
        rate = (len(stamps) - 1) / (stamps[-1] - stamps[0])
        self.assertTrue(4.0 <= rate <= 6.0, f'/cmd_vel rate {rate:.2f} Hz, expected 5 Hz')
        for _, msg in self.samples:
            self.assertAlmostEqual(msg.linear.x, min(CRUISE, 0.6), places=3)
            self.assertAlmostEqual(msg.angular.z, 0.0, places=6)

    def test_3_out_of_range_rejected(self):
        self.reset()
        for bad in (2.0, 0.05, 1.6):
            result = self.set_param(bad)
            self.assertFalse(result.successful, f'max_speed={bad} must be rejected')
            self.assertTrue(result.reason.strip(), 'rejection needs a reason')
        self.assertAlmostEqual(self.get_param().double_value, 0.6, places=6)
        speeds = self.recent_speeds(1.0)
        self.assertTrue(speeds)
        self.assertAlmostEqual(speeds[-1], CRUISE, places=3)

    def test_4_integer_type_rejected(self):
        self.reset()
        self.assertFalse(self.set_param(1).successful, 'integer max_speed must be rejected')

    def test_5_valid_value_applied(self):
        self.reset()
        self.assertTrue(self.set_param(0.2).successful)
        self.assertAlmostEqual(self.recent_speeds(1.0)[-1], 0.2, places=3)
        self.assertTrue(self.set_param(1.5).successful)
        self.assertAlmostEqual(self.recent_speeds(1.0)[-1], CRUISE, places=3)
        self.assertTrue(self.set_param(0.1).successful)   # range is inclusive
        self.reset()

    def test_6_high_temperature_throttles(self, proc_output, controller):
        self.reset()
        normal = self.recent_speeds(1.0)[-1]
        self.assertAlmostEqual(normal, CRUISE, places=3)
        self.publish_temperature(70.0)
        self.spin_for(0.5)
        throttled = self.recent_speeds(1.0)
        self.assertTrue(throttled)
        self.assertLess(max(throttled), normal - 1e-3, 'speed not reduced at 70 C')
        self.assertAlmostEqual(throttled[-1], 0.5 * normal, places=3)
        proc_output.assertWaitFor('WARN', process=controller, timeout=5, stream='stderr')
        # Cool down -> normal speed again
        self.publish_temperature(50.0)
        self.spin_for(0.5)
        self.assertAlmostEqual(self.recent_speeds(1.0)[-1], normal, places=3)

    def test_7_threshold_is_strictly_greater_than_65(self):
        self.reset()
        self.publish_temperature(65.0)
        self.spin_for(0.5)
        self.assertAlmostEqual(self.recent_speeds(1.0)[-1], CRUISE, places=3)
        self.publish_temperature(65.5)
        self.spin_for(0.5)
        self.assertAlmostEqual(self.recent_speeds(1.0)[-1], 0.5 * CRUISE, places=3)
        self.reset()
