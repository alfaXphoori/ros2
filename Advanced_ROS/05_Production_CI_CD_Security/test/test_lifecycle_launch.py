"""launch_testing: drive lifecycle_laser_sensor through its state machine.

Checks what a LifecyclePublisher must (and must not) put on the wire:
  Unconfigured/Inactive -> 0 messages, Active -> ~10 Hz of valid LaserScans,
  deactivate -> 0, cleanup -> configure -> activate works again,
  shutdown from Active -> Finalized and 0 messages afterwards.

Run:  colcon test --packages-select amr_adv05     (after colcon build)
      launch_test Advanced_ROS/05_Production_CI_CD_Security/test/test_lifecycle_launch.py
"""
import math
import time
import unittest

import launch
import launch_testing.actions
import launch_testing.asserts
import pytest
import rclpy
from launch_ros.actions import Node
from lifecycle_msgs.msg import State, Transition
from lifecycle_msgs.srv import ChangeState, GetState
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

NODE = 'lifecycle_laser_sensor'
TOPIC = '/scan_managed'


@pytest.mark.launch_test
def generate_test_description():
    sensor = Node(package='amr_adv05', executable='lifecycle_laser_sensor',
                  name=NODE, output='screen')
    return launch.LaunchDescription([
        sensor,
        launch_testing.actions.ReadyToTest(),
    ]), {'sensor': sensor}


class TestLifecycleLaser(unittest.TestCase):
    """Test methods run in alphabetical order and share one node instance."""

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('adv05_lifecycle_checker')
        cls.msgs = []
        cls.node.create_subscription(LaserScan, TOPIC, cls.msgs.append,
                                     qos_profile_sensor_data)
        cls.change = cls.node.create_client(ChangeState, f'/{NODE}/change_state')
        cls.get = cls.node.create_client(GetState, f'/{NODE}/get_state')
        assert cls.change.wait_for_service(timeout_sec=20.0), 'change_state not available'
        assert cls.get.wait_for_service(timeout_sec=20.0), 'get_state not available'

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.try_shutdown()

    # ---- helpers --------------------------------------------------------
    def call(self, client, request, timeout=10.0):
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self.node, future, timeout_sec=timeout)
        self.assertTrue(future.done(), 'service call timed out')
        return future.result()

    def state(self):
        return self.call(self.get, GetState.Request()).current_state.id

    def transition(self, transition_id, expected_state):
        req = ChangeState.Request()
        req.transition.id = transition_id
        self.assertTrue(self.call(self.change, req).success,
                        f'transition {transition_id} failed')
        self.assertEqual(self.state(), expected_state)

    def count(self, seconds, settle=0.5):
        """Messages received during `seconds`, after dropping in-flight ones."""
        end = time.monotonic() + settle
        while time.monotonic() < end:
            rclpy.spin_once(self.node, timeout_sec=0.05)
        self.msgs.clear()
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            rclpy.spin_once(self.node, timeout_sec=0.05)
        return len(self.msgs)

    # ---- the state machine, in order ------------------------------------
    def test_1_unconfigured_publishes_nothing(self):
        self.assertEqual(self.state(), State.PRIMARY_STATE_UNCONFIGURED)
        self.assertEqual(self.count(1.0), 0)

    def test_2_inactive_publishes_nothing(self):
        self.transition(Transition.TRANSITION_CONFIGURE, State.PRIMARY_STATE_INACTIVE)
        self.assertEqual(self.count(1.5), 0)

    def test_3_active_publishes_valid_scans_at_10hz(self):
        self.transition(Transition.TRANSITION_ACTIVATE, State.PRIMARY_STATE_ACTIVE)
        n = self.count(3.0)
        self.assertGreaterEqual(n, 24, f'expected ~30 scans in 3 s, got {n}')
        self.assertLessEqual(n, 36, f'expected ~30 scans in 3 s, got {n}')
        scan = self.msgs[-1]
        # RViz2 / Nav2 / slam_toolbox reject scans with a zero angle_increment
        self.assertGreater(scan.angle_increment, 0.0)
        self.assertLess(scan.angle_min, scan.angle_max)
        beams = round((scan.angle_max - scan.angle_min) / scan.angle_increment) + 1
        self.assertEqual(beams, len(scan.ranges))
        self.assertAlmostEqual(scan.angle_increment * len(scan.ranges), 2 * math.pi,
                               places=4)
        self.assertGreater(scan.scan_time, 0.0)
        self.assertTrue(all(scan.range_min <= r <= scan.range_max for r in scan.ranges))
        self.assertEqual(scan.header.frame_id, 'lidar_link')

    def test_4_deactivate_stops_publishing(self):
        self.transition(Transition.TRANSITION_DEACTIVATE, State.PRIMARY_STATE_INACTIVE)
        self.assertEqual(self.count(1.5), 0)

    def test_5_cleanup_then_reconfigure_and_activate_again(self):
        self.transition(Transition.TRANSITION_CLEANUP, State.PRIMARY_STATE_UNCONFIGURED)
        self.assertEqual(self.count(1.0), 0)
        self.transition(Transition.TRANSITION_CONFIGURE, State.PRIMARY_STATE_INACTIVE)
        self.assertEqual(self.count(1.0), 0)
        self.transition(Transition.TRANSITION_ACTIVATE, State.PRIMARY_STATE_ACTIVE)
        n = self.count(2.0)
        self.assertGreaterEqual(n, 15, f'expected ~20 scans in 2 s after re-activate, got {n}')
        self.assertLessEqual(n, 25, f'expected ~20 scans in 2 s after re-activate, got {n}')

    def test_6_shutdown_from_active_finalizes_and_stops(self):
        self.transition(Transition.TRANSITION_ACTIVE_SHUTDOWN,
                        State.PRIMARY_STATE_FINALIZED)
        self.assertEqual(self.count(1.5), 0,
                         'node still publishes after reaching Finalized')


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):

    def test_exit_code(self, proc_info, sensor):
        launch_testing.asserts.assertExitCodes(
            proc_info, process=sensor, allowable_exit_codes=[0, -2, -15])
