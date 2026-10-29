"""launch_testing: QoS behaviour of the Week 02 publisher/subscriber.

* a late-joining TRANSIENT_LOCAL subscriber receives the latched robot state
* BEST_EFFORT temperature messages arrive (qos_profile_sensor_data)
* a RELIABLE subscriber to the BEST_EFFORT topic gets 0 messages + an incompatible-QoS event
* both nodes exit cleanly (code 0) when launch shuts them down
"""
import time
import unittest

import launch
import launch.actions
import launch_ros.actions
import launch_testing.actions
import launch_testing.asserts
import pytest
import rclpy
from rclpy.event_handler import SubscriptionEventCallbacks
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSPolicyKind, QoSProfile,
                       ReliabilityPolicy, qos_profile_sensor_data)
from std_msgs.msg import Float32, String

LATE_JOIN_DELAY = 2.0  # s; first state update is at t=5 s, so the latched value is still SYSTEM_READY


@pytest.mark.launch_test
def generate_test_description():
    pub = launch_ros.actions.Node(package='amr_week02', executable='sensor_qos_publisher',
                                  output='screen')
    sub = launch_ros.actions.Node(package='amr_week02', executable='sensor_qos_subscriber',
                                  output='screen')
    return launch.LaunchDescription([
        pub,
        # subscriber starts after the initial state was already published -> late joiner
        launch.actions.TimerAction(period=LATE_JOIN_DELAY, actions=[sub]),
        launch_testing.actions.ReadyToTest(),
    ]), {'pub': pub, 'sub': sub}


def spin_until(node, predicate, timeout):
    end = time.monotonic() + timeout
    while time.monotonic() < end and not predicate():
        rclpy.spin_once(node, timeout_sec=0.1)
    return predicate()


class TestQoSBehaviour(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('qos_probe')

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def wait_for_publisher(self, topic):
        self.assertTrue(spin_until(self.node, lambda: self.node.count_publishers(topic) > 0, 15.0),
                        f'no publisher on {topic}')

    def test_late_joining_subscriber_node_gets_latched_state(self, proc_output, sub):
        proc_output.assertWaitFor('Latched Robot State Received: "SYSTEM_READY', process=sub,
                                  timeout=20)

    def test_late_joining_probe_gets_latched_state(self):
        self.wait_for_publisher('/robot/state')
        time.sleep(1.0)  # make sure the initial state was published before we join
        latched = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                             durability=DurabilityPolicy.TRANSIENT_LOCAL,
                             history=HistoryPolicy.KEEP_LAST, depth=1)
        got = []
        sub = self.node.create_subscription(String, '/robot/state', got.append, latched)
        try:
            self.assertTrue(spin_until(self.node, lambda: got, 10.0), 'latched state not received')
            self.assertRegex(got[0].data, r'^SYSTEM_(READY|ACTIVE)')
        finally:
            self.node.destroy_subscription(sub)

    def test_temperature_messages_arrive_best_effort(self):
        self.wait_for_publisher('/sensor/temperature')
        got = []
        sub = self.node.create_subscription(Float32, '/sensor/temperature', got.append,
                                            qos_profile_sensor_data)
        try:
            self.assertTrue(spin_until(self.node, lambda: len(got) >= 3, 10.0),
                            f'only {len(got)} temperature messages')
            for msg in got:
                self.assertGreaterEqual(msg.data, 35.9)
                self.assertLessEqual(msg.data, 37.8)
        finally:
            self.node.destroy_subscription(sub)

    def test_reliable_subscriber_is_incompatible(self):
        self.wait_for_publisher('/sensor/temperature')
        got, events = [], []
        callbacks = SubscriptionEventCallbacks(incompatible_qos=events.append)
        reliable = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, depth=10)
        sub = self.node.create_subscription(Float32, '/sensor/temperature', got.append, reliable,
                                            event_callbacks=callbacks)
        try:
            spin_until(self.node, lambda: False, 4.0)  # publisher runs at 2 Hz -> ~8 chances
            self.assertEqual(len(got), 0, 'RELIABLE request must not match a BEST_EFFORT offer')
            self.assertGreaterEqual(len(events), 1, 'no incompatible-QoS event')
            self.assertEqual(events[-1].last_policy_kind, QoSPolicyKind.RELIABILITY)
        finally:
            self.node.destroy_subscription(sub)


@launch_testing.post_shutdown_test()
class TestCleanShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        launch_testing.asserts.assertExitCodes(proc_info)

    def test_no_shutdown_traceback(self, proc_output):
        for line in proc_output:
            self.assertNotIn('rcl_shutdown already called', line.text.decode())
            self.assertNotIn('Traceback', line.text.decode())
