"""Headless Gazebo physics test: DiffDrive /odom must track ground truth.

Runs gz_odom_probe.run() (gz sim -s on worlds/flat_ground.sdf, ~35 s) and compares the
odometry with /world/flat_ground/dynamic_pose/info for an in-place rotation, an arc and
a straight line. Before the contact fix (cylinder wheel collision, caster mu = 1) the
in-place rotation was 147 deg true vs 171 deg odom (-14 %).
"""
import math
import os
import shutil
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

pytestmark = pytest.mark.skipif(shutil.which('gz') is None, reason='Gazebo Sim not installed')


@pytest.fixture(scope='module')
def results():
    import gz_odom_probe
    return gz_odom_probe.run()


def rel_err(measured, reference):
    return abs(measured - reference) / abs(reference)


def test_rotation_in_place_yaw_within_5_percent(results):
    odom, truth = results['rotate_in_place']['odom'], results['rotate_in_place']['truth']
    assert abs(math.degrees(odom[2])) > 90, 'robot did not turn'
    assert rel_err(truth[2], odom[2]) < 0.05, (math.degrees(odom[2]), math.degrees(truth[2]))
    assert math.hypot(truth[0], truth[1]) < 0.02, 'in-place rotation drifted'


def test_arc_within_5_percent(results):
    odom, truth = results['arc']['odom'], results['arc']['truth']
    assert rel_err(truth[2], odom[2]) < 0.05, (math.degrees(odom[2]), math.degrees(truth[2]))
    gap = math.hypot(truth[0] - odom[0], truth[1] - odom[1])
    assert gap < 0.05 * math.hypot(odom[0], odom[1]), (odom, truth)


def test_straight_line_within_1_percent(results):
    odom, truth = results['straight']['odom'], results['straight']['truth']
    assert odom[0] > 1.0, 'robot did not drive'
    assert rel_err(truth[0], odom[0]) < 0.01, (odom, truth)
    assert abs(truth[1]) < 0.015 and abs(math.degrees(truth[2])) < 1.0, truth
