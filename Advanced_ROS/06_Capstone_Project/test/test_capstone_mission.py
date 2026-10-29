"""Module 06 integration test: the full headless capstone system + the real mission executor.

Requires exit code 0 and 'MISSION SUMMARY: 7/7 stages PASS, 7/7 KPIs met', i.e. pick, drop,
dock (true docking error within the KPI), undock, the e-stop fault injection (robot stopped
before the box) and return home - and checks a few measured values in the log."""

import os
import re
import subprocess
import unittest

from ament_index_python.packages import get_package_share_directory
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
            get_package_share_directory('amr_adv06'), 'launch',
            'full_warehouse_system.launch.py')),
        launch_arguments={'headless': 'true'}.items())
    return launch.LaunchDescription([system, launch_testing.actions.ReadyToTest()])


class TestCapstoneMission(unittest.TestCase):

    def test_mission_pass(self):
        run = subprocess.run(
            ['ros2', 'run', 'amr_adv06', 'capstone_mission', '--ros-args',
             '-p', 'use_sim_time:=true', '-p', 'dwell_scale:=0.5'],
            capture_output=True, text=True, timeout=300)
        log = run.stderr
        print('\n'.join(ln for ln in log.splitlines()
                        if re.search(r'Stage \d \S.*(PASS|FAIL)|KPI|SUMMARY', ln)))
        self.assertEqual(run.returncode, 0, log[-3000:])
        self.assertIn('MISSION SUMMARY: 7/7 stages PASS, 7/7 KPIs met', log)
        self.assertIn('11/11 lifecycle nodes ACTIVE', log)
        self.assertIn('error_code=0 (NONE)', log)
        docking = float(re.search(r'TRUE docking error ([\d.]+) mm', log).group(1))
        self.assertLess(docking, 15.0)
        gap = float(re.search(r'robot stopped with ([-\d.]+) cm', log).group(1))
        self.assertGreater(gap, 0.0)


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
