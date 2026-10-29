"""launch_testing: core_system.launch.py namespacing + fleet_parameters validation.

Launches with robot_ns:=amr_01 and checks that every node lives in /amr_01, that the
fleet_id launch argument reaches the node, and that SetParameters rejects 3.0 m/s but
accepts 1.0 m/s, which is then published on /amr_01/speed_limit.
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
from launch.launch_description_sources import PythonLaunchDescriptionSource
from rcl_interfaces.srv import GetParameters, SetParameters, SetParametersAtomically
from rclpy.parameter import Parameter, parameter_value_to_python
from rclpy.qos import DurabilityPolicy, QoSProfile
from std_msgs.msg import Float64

NS = '/amr_01'
NODE = NS + '/fleet_parameters'
EXPECTED_NODES = {'sensor_qos_publisher', 'power_service_server', 'navigate_action_server',
                  'fleet_parameters'}


@pytest.mark.launch_test
def generate_test_description():
    launch_file = os.path.join(get_package_share_directory('amr_week05'), 'launch',
                               'core_system.launch.py')
    core = launch.actions.IncludeLaunchDescription(
        PythonLaunchDescriptionSource(launch_file),
        launch_arguments={'robot_ns': 'amr_01', 'fleet_id': 'AMR_TEST_07'}.items())
    return launch.LaunchDescription([core, launch_testing.actions.ReadyToTest()])


class TestCoreSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('core_system_probe')
        cls.set_cli = cls.node.create_client(SetParameters, NODE + '/set_parameters')
        cls.set_atomic_cli = cls.node.create_client(SetParametersAtomically,
                                                    NODE + '/set_parameters_atomically')
        cls.get_cli = cls.node.create_client(GetParameters, NODE + '/get_parameters')
        for cli in (cls.set_cli, cls.set_atomic_cli, cls.get_cli):
            assert cli.wait_for_service(timeout_sec=20.0), f'{cli.srv_name} not available'

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def call(self, cli, request):
        future = cli.call_async(request)
        rclpy.spin_until_future_complete(self.node, future, timeout_sec=10.0)
        self.assertTrue(future.done())
        return future.result()

    def set_params(self, *params):
        req = SetParameters.Request(parameters=[p.to_parameter_msg() for p in params])
        return self.call(self.set_cli, req).results

    def get_value(self, name):
        value = self.call(self.get_cli, GetParameters.Request(names=[name])).values[0]
        return parameter_value_to_python(value)

    def latest_speed_limit(self):
        got = []
        sub = self.node.create_subscription(
            Float64, NS + '/speed_limit', got.append,
            QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))
        end = time.monotonic() + 10.0
        while not got and time.monotonic() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)
        self.node.destroy_subscription(sub)
        self.assertTrue(got, 'no speed_limit message')
        return got[-1].data

    def test_all_nodes_are_namespaced(self):
        end = time.monotonic() + 20.0
        found = set()
        while time.monotonic() < end:
            names = self.node.get_node_names_and_namespaces()
            found = {n for n, ns in names if ns == NS}
            if EXPECTED_NODES <= found:
                break
            rclpy.spin_once(self.node, timeout_sec=0.2)
        self.assertTrue(EXPECTED_NODES <= found, f'found in {NS}: {found}')
        global_nodes = {n for n, ns in self.node.get_node_names_and_namespaces() if ns == '/'}
        self.assertFalse(EXPECTED_NODES & global_nodes, 'a node escaped the namespace')

    def test_interfaces_are_namespaced(self):
        end = time.monotonic() + 20.0
        while time.monotonic() < end:
            services = dict(self.node.get_service_names_and_types())
            topics = dict(self.node.get_topic_names_and_types())
            if (NS + '/robot/set_power_mode' in services
                    and NS + '/navigate_distance/_action/send_goal' in services
                    and NS + '/sensor/temperature' in topics):
                return
            rclpy.spin_once(self.node, timeout_sec=0.2)
        self.fail(f'namespaced interfaces missing: {sorted(services)} {sorted(topics)}')

    def test_fleet_id_launch_argument_is_used(self):
        self.assertEqual(self.get_value('fleet_id'), 'AMR_TEST_07')

    def test_speed_3_0_rejected_1_0_accepted_and_used(self):
        res = self.set_params(Parameter('max_linear_speed', value=3.0))[0]
        self.assertFalse(res.successful)
        self.assertIn('outside valid safety range', res.reason)
        self.assertNotEqual(self.get_value('max_linear_speed'), 3.0)

        res = self.set_params(Parameter('max_linear_speed', value=1.0))[0]
        self.assertTrue(res.successful, res.reason)
        self.assertEqual(self.get_value('max_linear_speed'), 1.0)
        self.assertEqual(self.latest_speed_limit(), 1.0)

    def test_integer_rejected_by_rclpy_type_check(self):
        res = self.set_params(Parameter('max_linear_speed', value=1))[0]
        self.assertFalse(res.successful)
        self.assertIn('Wrong parameter type', res.reason)

    def test_small_safety_margin_rejected(self):
        res = self.set_params(Parameter('safety_margin', value=0.05))[0]
        self.assertFalse(res.successful)
        self.assertIn('safety_margin cannot be smaller', res.reason)

    def test_atomic_set_is_all_or_nothing(self):
        before = self.get_value('max_linear_speed')
        req = SetParametersAtomically.Request(parameters=[
            Parameter('max_linear_speed', value=2.0).to_parameter_msg(),
            Parameter('safety_margin', value=0.01).to_parameter_msg()])
        res = self.call(self.set_atomic_cli, req).result
        self.assertFalse(res.successful)
        self.assertEqual(self.get_value('max_linear_speed'), before)


@launch_testing.post_shutdown_test()
class TestAfterShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        launch_testing.asserts.assertExitCodes(proc_info)
