"""Week 12 integration test (headless): slam_toolbox is configured+activated
(lifecycle), really uses our parameter file, and publishes /map of the room."""

import os
import time
import unittest

from ament_index_python.packages import get_package_share_directory
import launch
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing
import launch_testing.actions
from lifecycle_msgs.srv import GetState
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import Twist
import pytest
from rcl_interfaces.srv import GetParameters
import rclpy
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy


@pytest.mark.launch_test
def generate_test_description():
    # Own Gazebo Transport partition per test file (inherited by the launched gz
    # server and by gz CLI calls made from this process during the test)
    os.environ['GZ_PARTITION'] = \
        f"{os.environ.get('GZ_PARTITION', 'amr')}_{os.path.basename(__file__)[:-3]}"
    demo = launch.actions.IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('amr_week12'), 'launch', 'slam_mapping_sim.launch.py')),
        launch_arguments={'headless': 'true'}.items())
    return launch.LaunchDescription([demo, launch_testing.actions.ReadyToTest()])


class TestSlam(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('w12_slam_test')
        cls.maps = []
        qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                         durability=DurabilityPolicy.TRANSIENT_LOCAL)
        cls.node.create_subscription(OccupancyGrid, '/map', cls.maps.append, qos)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.try_shutdown()

    clients = {}

    def call(self, srv_type, name, request, timeout=60.0):
        if name not in self.clients:
            self.clients[name] = self.node.create_client(srv_type, name)
        cli = self.clients[name]
        self.assertTrue(cli.wait_for_service(timeout_sec=timeout), name)
        fut = cli.call_async(request)
        rclpy.spin_until_future_complete(self.node, fut, timeout_sec=10.0)
        self.assertIsNotNone(fut.result(), name)
        return fut.result()

    def test_1_lifecycle_active(self):
        end = time.monotonic() + 60.0
        label = ''
        while time.monotonic() < end:
            label = self.call(GetState, '/slam_toolbox/get_state', GetState.Request()) \
                .current_state.label
            if label == 'active':
                break
            time.sleep(1.0)
        self.assertEqual(label, 'active')

    def test_3_map_published(self):
        # drive slowly forward (free space ahead) so SLAM Toolbox adds new scans
        # (minimum_travel_distance 0.15 m); a single scan leaves most far cells unknown
        pub = self.node.create_publisher(Twist, '/cmd_vel', 10)
        spin = Twist()
        spin.linear.x = 0.2

        def free_cells():
            return sum(1 for v in self.maps[-1].data if v == 0) if self.maps else 0

        end = time.monotonic() + 120.0
        while time.monotonic() < end and free_cells() < 20000:
            pub.publish(spin)
            rclpy.spin_once(self.node, timeout_sec=0.1)
        pub.publish(Twist())
        self.assertTrue(self.maps, '/map never published')
        m = self.maps[-1]
        self.assertEqual(m.header.frame_id, 'map')
        self.assertAlmostEqual(m.info.resolution, 0.05, places=3)
        # from the origin the 10 m LiDAR sees the whole 10 x 10 m room
        self.assertGreater(m.info.width * m.info.resolution, 9.0)
        self.assertGreater(m.info.height * m.info.resolution, 9.0)
        self.assertGreater(sum(1 for v in m.data if v == 0), 20000)


    def test_4_params_from_our_file(self):
        # max_laser_range is declared by slam_toolbox only once the first scan arrives,
        # so this runs after the map test
        req = GetParameters.Request(names=['max_laser_range', 'map_update_interval',
                                           'use_sim_time'])
        values = self.call(GetParameters, '/slam_toolbox/get_parameters', req).values
        self.assertEqual(len(values), 3, values)
        self.assertEqual(values[0].double_value, 10.0)   # slam_toolbox default is 20.0
        self.assertEqual(values[1].double_value, 2.0)    # default is 5.0
        self.assertTrue(values[2].bool_value)

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
