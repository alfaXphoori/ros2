"""Week 13 integration test (headless): standalone global/local costmaps on the
real SLAM map publish OccupancyGrids whose values follow the 0..100 scaling
(lethal 100, inscribed 99, decaying inflation, 0 beyond inflation_radius)."""

import os
import time
import unittest

from ament_index_python.packages import get_package_share_directory
import launch
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing
import launch_testing.actions
from nav_msgs.msg import OccupancyGrid
import numpy as np
import pytest
import rclpy
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy

INSCRIBED = 0.14
INFLATION = 0.55


@pytest.mark.launch_test
def generate_test_description():
    # Own Gazebo Transport partition per test file (inherited by the launched gz
    # server and by gz CLI calls made from this process during the test)
    os.environ['GZ_PARTITION'] = \
        f"{os.environ.get('GZ_PARTITION', 'amr')}_{os.path.basename(__file__)[:-3]}"
    demo = launch.actions.IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('amr_week13'), 'launch', 'costmap_demo.launch.py')),
        launch_arguments={'headless': 'true'}.items())
    return launch.LaunchDescription([demo, launch_testing.actions.ReadyToTest()])


def to_array(msg):
    return np.array(msg.data, dtype=np.int16).reshape(msg.info.height, msg.info.width)


class TestCostmaps(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('w13_costmap_test')
        cls.maps = {}
        qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                         durability=DurabilityPolicy.TRANSIENT_LOCAL)
        for name in ('global_costmap', 'local_costmap'):
            cls.node.create_subscription(
                OccupancyGrid, f'/{name}/costmap',
                lambda m, n=name: cls.maps.__setitem__(n, m), qos)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.try_shutdown()

    def wait_for(self, name, timeout=120.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end and name not in self.maps:
            rclpy.spin_once(self.node, timeout_sec=0.2)
        self.assertIn(name, self.maps, f'/{name}/costmap never published')
        return self.maps[name]

    def test_local_costmap_rolling_window(self):
        msg = self.wait_for('local_costmap')
        self.assertEqual(msg.header.frame_id, 'odom')
        self.assertEqual((msg.info.width, msg.info.height), (60, 60))   # 3 m / 0.05 m

    def test_global_costmap_values(self):
        msg = self.wait_for('global_costmap')
        self.assertEqual(msg.header.frame_id, 'map')
        grid = to_array(msg)
        values = set(np.unique(grid).tolist())
        # OccupancyGrid is scaled: never the raw 253/254/255
        self.assertTrue(values <= set(range(-1, 101)), sorted(values)[-5:])
        self.assertIn(100, values)
        self.assertIn(99, values)
        self.assertIn(0, values)

        res = msg.info.resolution
        ox, oy = msg.info.origin.position.x, msg.info.origin.position.y

        def cell(x, y):
            return int((y - oy) / res), int((x - ox) / res)

        # The pillar at (2, 2) (1.2 x 0.6 m) must be lethal on its surface
        r0, c0 = cell(1.3, 1.6)
        r1, c1 = cell(2.7, 2.4)
        self.assertGreater(int((grid[r0:r1, c0:c1] == 100).sum()), 20)

        # Inflation around the pillar: cost vs distance to the nearest lethal cell
        R0, C0 = cell(0.6, 0.6)
        R1, C1 = cell(3.4, 3.4)
        win = grid[R0:R1, C0:C1]
        lethal = np.argwhere(win == 100)
        free_like = np.argwhere((win >= 0) & (win < 100))
        dist = np.array([np.min(np.hypot(*(lethal - p).T)) * res for p in free_like])
        cost = np.array([win[tuple(p)] for p in free_like])
        inner = cost[dist <= INSCRIBED - 1e-6]
        self.assertTrue(len(inner) > 0 and np.all(inner == 99), np.unique(inner))
        outer = cost[dist > INFLATION + res]
        self.assertTrue(np.all(outer == 0), np.unique(outer))
        # monotonic decay between inscribed and inflation radius (mean per 1-cell bin)
        bins = np.arange(INSCRIBED, INFLATION + res, res)
        means = [cost[(dist > a) & (dist <= b)].mean() for a, b in zip(bins[:-1], bins[1:])
                 if np.any((dist > a) & (dist <= b))]
        self.assertGreater(len(means), 5)
        self.assertTrue(all(a >= b for a, b in zip(means, means[1:])), means)
        self.assertTrue(98 >= means[0] > means[-1] >= 0, means)


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        for info in proc_info:
            if info.process_name.startswith('nav2_costmap_2d'):
                # Observed with Nav2 1.3.13 (Jazzy): the *standalone* nav2_costmap_2d
                # executable sometimes crashes while exiting on SIGINT (SIGSEGV -11 or
                # SIGABRT -6), after it has published correctly; inside
                # planner/controller_server (Week 14) it exits cleanly.
                self.assertIn(info.returncode, (0, -2, -6, -11, -15, 130, 143),
                              info.process_name)
                continue
            self.assertIn(info.returncode, (0, -2, -15, 130, 143), info.process_name)
