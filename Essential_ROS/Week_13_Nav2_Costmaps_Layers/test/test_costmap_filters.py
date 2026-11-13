"""Week 13 / Adv 11 integration test (headless): Nav2 KeepoutFilter and SpeedFilter.

Verifies that:
  1. KeepoutFilter marks the keep-out zone [1.0, 2.5] x [-2.5, -1.0] as lethal (100)
     in /global_costmap/costmap.
  2. SpeedFilter publishes nav2_msgs/SpeedLimit (percentage=True, 50.0%) on /speed_limit
     when the robot at (0, 0) is inside the speed-restricted zone [-1.0, 1.0]^2.
"""

import os
import time
import unittest

from ament_index_python.packages import get_package_share_directory
import launch
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing
import launch_testing.actions
from nav2_msgs.msg import SpeedLimit
from nav_msgs.msg import OccupancyGrid
import numpy as np
import pytest
import rclpy
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy


@pytest.mark.launch_test
def generate_test_description():
    demo = launch.actions.IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('amr_week13'),
            'launch',
            'costmap_filters_demo.launch.py',
        ))
    )
    return launch.LaunchDescription([demo, launch_testing.actions.ReadyToTest()])


class TestCostmapFilters(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('w13_costmap_filters_test')
        cls.costmap = None
        cls.speed_limit = None
        map_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        cls.node.create_subscription(
            OccupancyGrid, '/global_costmap/costmap',
            lambda m: setattr(cls, 'costmap', m), map_qos)
        cls.node.create_subscription(
            SpeedLimit, '/speed_limit',
            lambda m: setattr(cls, 'speed_limit', m), 10)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.try_shutdown()

    def test_keepout_and_speed_filters(self):
        end = time.monotonic() + 30.0
        while time.monotonic() < end:
            rclpy.spin_once(self.node, timeout_sec=0.2)
            if self.costmap is not None and 100 in self.costmap.data and self.speed_limit is not None:
                # Check if keepout zone center (1.75, -1.75) is already marked lethal
                ox = self.costmap.info.origin.position.x
                oy = self.costmap.info.origin.position.y
                res = self.costmap.info.resolution
                c = int((1.75 - ox) / res)
                r = int((-1.75 - oy) / res)
                grid = np.array(self.costmap.data, dtype=np.int16).reshape(
                    self.costmap.info.height, self.costmap.info.width)
                if grid[r, c] == 100:
                    break

        self.assertIsNotNone(self.costmap, '/global_costmap/costmap never published')
        ox = self.costmap.info.origin.position.x
        oy = self.costmap.info.origin.position.y
        res = self.costmap.info.resolution
        grid = np.array(self.costmap.data, dtype=np.int16).reshape(
            self.costmap.info.height, self.costmap.info.width)

        # Keep-out zone [1.0, 2.5] x [-2.5, -1.0]: interior must be lethal (100)
        r0, c0 = int((-2.3 - oy) / res), int((1.2 - ox) / res)
        r1, c1 = int((-1.2 - oy) / res), int((2.3 - ox) / res)
        patch = grid[r0:r1, c0:c1]
        self.assertGreater(patch.size, 0)
        self.assertTrue(np.all(patch == 100), f'Expected all 100 in keepout patch, got {np.unique(patch)}')

        # Speed-restricted zone around origin: should publish 50.0% speed limit
        self.assertIsNotNone(self.speed_limit, '/speed_limit never published')
        self.assertTrue(self.speed_limit.percentage)
        self.assertAlmostEqual(self.speed_limit.speed_limit, 50.0, delta=1.0)


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        for info in proc_info:
            if info.process_name.startswith('nav2_costmap_2d'):
                self.assertIn(info.returncode, (0, -2, -6, -11, -15, 130, 143),
                              info.process_name)
                continue
            self.assertIn(info.returncode, (0, -2, -15, 130, 143), info.process_name)
