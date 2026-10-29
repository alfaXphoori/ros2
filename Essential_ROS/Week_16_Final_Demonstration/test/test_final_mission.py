"""Week 16 integration test: one-command headless bringup + the real mission
executor; requires 'MISSION SUMMARY: 3/3 ... PASS' and exit code 0, and the
Gazebo ground-truth pose back at Home."""

import math
import os
import subprocess
import unittest

from ament_index_python.packages import get_package_share_directory
from amr_week11.ground_truth import robot_pose
import launch
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing
import launch_testing.actions
import pytest


@pytest.mark.launch_test
def generate_test_description():
    os.environ['GZ_PARTITION'] = \
        f"{os.environ.get('GZ_PARTITION', 'amr')}_{os.path.basename(__file__)[:-3]}"
    system = launch.actions.IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('amr_week16'), 'launch', 'final_amr_system.launch.py')),
        launch_arguments={'headless': 'true'}.items())
    return launch.LaunchDescription([system, launch_testing.actions.ReadyToTest()])


class TestFinalMission(unittest.TestCase):

    def test_mission_pass(self):
        run = subprocess.run(
            ['ros2', 'run', 'amr_week16', 'final_mission_executor', '--ros-args',
             '-p', 'use_sim_time:=true', '-p', 'dwell_scale:=0.2'],
            capture_output=True, text=True, timeout=400)
        print(run.stderr[-4000:])
        self.assertEqual(run.returncode, 0, run.stderr[-2000:])
        self.assertIn('MISSION SUMMARY: 3/3 stages SUCCEEDED (100%)', run.stderr)
        self.assertIn('PASS', run.stderr)
        x, y, yaw = robot_pose()
        print(f'[w16] final ground truth x={x:.3f} y={y:.3f} yaw={math.degrees(yaw):.1f} deg')
        self.assertLess(math.hypot(x, y), 0.45)


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
