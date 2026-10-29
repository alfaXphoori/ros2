"""Week 14 integration test (headless Gazebo + full Nav2 on the real map):
set the initial pose, send NavigateToPose to a free cell and require
SUCCEEDED within 90 s with the *real* (Gazebo ground-truth) pose near the goal."""

import math
import os
import time
import unittest

from ament_index_python.packages import get_package_share_directory
from amr_week11.ground_truth import robot_pose
from amr_week14.amcl_initial_pose import make_initial_pose
from amr_week14.nav2_lifecycle_guard import describe, ensure_nav2_active
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
import launch
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing
import launch_testing.actions
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import pytest
import rclpy

GOAL = (2.0, -2.0, -math.pi / 2)


@pytest.mark.launch_test
def generate_test_description():
    # Own Gazebo Transport partition per test file (inherited by the launched gz
    # server and by gz CLI calls made from this process during the test)
    os.environ['GZ_PARTITION'] = \
        f"{os.environ.get('GZ_PARTITION', 'amr')}_{os.path.basename(__file__)[:-3]}"
    def include(pkg, name, args):
        return launch.actions.IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory(pkg), 'launch', name)),
            launch_arguments=args.items())
    return launch.LaunchDescription([
        include('amr_week11', 'gazebo_world.launch.py', {'headless': 'true'}),
        include('amr_week14', 'nav2_bringup.launch.py', {}),
        launch_testing.actions.ReadyToTest(),
    ])


class TestNavigateToPose(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.nav = BasicNavigator()
        cls.nav.set_parameters([rclpy.parameter.Parameter('use_sim_time', value=True)])

    @classmethod
    def tearDownClass(cls):
        cls.nav.destroy_node()
        rclpy.try_shutdown()

    def test_navigate_to_free_cell(self):
        nav = self.nav
        # wait for /clock so stamps are valid
        while nav.get_clock().now().nanoseconds == 0:
            rclpy.spin_once(nav, timeout_sec=0.1)
        init = make_initial_pose(0.0, 0.0, 0.0)
        init.header.stamp = nav.get_clock().now().to_msg()
        pub = nav.create_publisher(PoseWithCovarianceStamped, 'initialpose', 10)
        for _ in range(30):
            if pub.get_subscription_count() > 0:
                break
            rclpy.spin_once(nav, timeout_sec=0.5)
        pub.publish(init)
        # never hang on a lost lifecycle_manager reply (waitUntilNav2Active has no timeout)
        ok, states, healed = ensure_nav2_active(nav, timeout=150.0)
        print(f'[w14] {describe(states, healed)}')
        self.assertTrue(ok, describe(states, healed))
        nav.waitUntilNav2Active(localizer='amcl')

        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.header.stamp = nav.get_clock().now().to_msg()
        goal.pose.position.x, goal.pose.position.y = GOAL[0], GOAL[1]
        goal.pose.orientation.z = math.sin(GOAL[2] / 2)
        goal.pose.orientation.w = math.cos(GOAL[2] / 2)
        t0 = time.monotonic()
        self.assertTrue(nav.goToPose(goal), 'goal rejected')
        while not nav.isTaskComplete():
            if time.monotonic() - t0 > 90.0:
                nav.cancelTask()
                self.fail('NavigateToPose did not finish within 90 s')
        result = nav.getResult()
        elapsed = time.monotonic() - t0
        x, y, yaw = robot_pose()
        err = math.hypot(x - GOAL[0], y - GOAL[1])
        yaw_err = abs(math.atan2(math.sin(yaw - GOAL[2]), math.cos(yaw - GOAL[2])))
        print(f'[w14] result={result} wall_time={elapsed:.1f}s ground_truth=({x:.3f},{y:.3f},'
              f'{yaw:.3f}) position_error={err:.3f}m yaw_error={math.degrees(yaw_err):.1f}deg')
        self.assertEqual(result, TaskResult.SUCCEEDED)
        # goal checker tolerance 0.25 m + AMCL error
        self.assertLess(err, 0.45)
        self.assertLess(yaw_err, math.radians(30))


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
            # nav2 collision_monitor (Jazzy 1.3.13) sometimes segfaults (-11) in on_cleanup:
            # a scan callback still looks up TF while the Scan source is destroyed (seen
            # in the log right before the crash); only after the test has passed
            if info.process_name.startswith('collision_monitor'):
                allowed += (-11,)
            # a lifecycle_manager that lost a change_state reply (healed by the guard /
            # supervisor) is still blocked in that call and only stops on SIGKILL (-9)
            if info.process_name.startswith('lifecycle_manager'):
                allowed += (-9,)
            self.assertIn(info.returncode, allowed, info.process_name)
