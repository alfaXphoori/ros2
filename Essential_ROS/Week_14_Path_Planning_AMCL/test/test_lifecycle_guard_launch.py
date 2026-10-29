"""Fault injection for the Nav2 lifecycle guard: map_server and amcl are started WITHOUT a
lifecycle manager, which is exactly what a manager that lost a transition reply looks like
(nodes stay unconfigured/inactive forever). amcl is configured by hand first, so both
stable states are covered. The guard must bring both nodes to ACTIVE by itself, and
map_server must then really serve the Week 12 map on /map."""

import os
import time
import unittest

from ament_index_python.packages import get_package_share_directory
from amr_week14.nav2_lifecycle_guard import describe, ensure_nav2_active, LOCALIZATION_NODES
import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
from lifecycle_msgs.msg import Transition
from lifecycle_msgs.srv import ChangeState, GetState
from nav_msgs.msg import OccupancyGrid
import pytest
import rclpy
from rclpy.qos import DurabilityPolicy, QoSProfile

PARAMS = os.path.join(get_package_share_directory('amr_week14'), 'config', 'nav2_params.yaml')
MAP = os.path.join(get_package_share_directory('amr_week12'), 'maps', 'warehouse_map.yaml')


@pytest.mark.launch_test
def generate_test_description():
    common = [PARAMS, {'use_sim_time': False}]
    return launch.LaunchDescription([
        launch_ros.actions.Node(package='nav2_map_server', executable='map_server',
                                name='map_server', output='screen',
                                parameters=common + [{'yaml_filename': MAP}]),
        launch_ros.actions.Node(package='nav2_amcl', executable='amcl', name='amcl',
                                output='screen', parameters=common),
        # no lifecycle_manager on purpose
        launch_testing.actions.ReadyToTest(),
    ])


class TestLifecycleGuard(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('w14_lifecycle_guard_test')

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.try_shutdown()

    def call(self, srv, name, req):
        cli = self.node.create_client(srv, name)
        self.assertTrue(cli.wait_for_service(timeout_sec=30.0), name)
        fut = cli.call_async(req)
        rclpy.spin_until_future_complete(self.node, fut, timeout_sec=10.0)
        self.assertIsNotNone(fut.result(), name)
        return fut.result()

    def state(self, name):
        return self.call(GetState, f'/{name}/get_state', GetState.Request()).current_state.label

    def test_guard_activates_nodes_left_behind_by_the_manager(self):
        # amcl: configure by hand -> stuck in 'inactive' (manager never sent activate)
        req = ChangeState.Request()
        req.transition.id = Transition.TRANSITION_CONFIGURE
        self.assertTrue(self.call(ChangeState, '/amcl/change_state', req).success)
        self.assertEqual(self.state('map_server'), 'unconfigured')
        self.assertEqual(self.state('amcl'), 'inactive')

        t0 = time.monotonic()
        ok, states, healed = ensure_nav2_active(self.node, LOCALIZATION_NODES,
                                                timeout=60.0, heal_after=2.0)
        print(f'[w14 guard] {describe(states, healed)} in {time.monotonic() - t0:.1f} s')
        self.assertTrue(ok, describe(states, healed))
        self.assertEqual(healed, ['map_server', 'amcl'])
        self.assertGreater(time.monotonic() - t0, 2.0)   # waited heal_after first
        self.assertEqual(self.state('map_server'), 'active')
        self.assertEqual(self.state('amcl'), 'active')

        # map_server is really serving: the latched /map arrives with the Week 12 size
        maps = []
        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.node.create_subscription(OccupancyGrid, '/map', maps.append, qos)
        end = time.monotonic() + 15.0
        while not maps and time.monotonic() < end:
            rclpy.spin_once(self.node, timeout_sec=0.2)
        self.assertTrue(maps, 'no /map after the guard activated map_server')
        print(f'[w14 guard] /map {maps[0].info.width}x{maps[0].info.height} '
              f'@ {maps[0].info.resolution:.2f} m')
        self.assertEqual((maps[0].info.width, maps[0].info.height), (200, 199))

    def test_guard_returns_quickly_when_everything_is_active(self):
        ok, states, healed = ensure_nav2_active(self.node, LOCALIZATION_NODES,
                                                timeout=60.0, heal_after=2.0)
        self.assertTrue(ok)
        self.assertEqual(healed, [])


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        for info in proc_info:
            self.assertIn(info.returncode, (0, -2, -15, 130, 143), info.process_name)
