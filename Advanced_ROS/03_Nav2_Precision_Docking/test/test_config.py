"""Docking server configuration + pure helpers (fake base kinematics, docking error)."""
import math
import os
import re

import pytest
import yaml
from ament_index_python.packages import get_package_share_directory

from amr_adv03.dock_client import pose_error
from amr_adv03.fake_base import integrate, step_toward

SHARE = get_package_share_directory('amr_adv03')


@pytest.fixture(scope='module')
def params():
    with open(os.path.join(SHARE, 'config', 'docking_server_params.yaml')) as f:
        return yaml.safe_load(f)['docking_server']['ros__parameters']


def test_dock_database(params):
    assert params['docks'] == ['home_dock']          # DockRobot dock_id
    dock = params['home_dock']
    assert dock['type'] in params['dock_plugins']     # type = a dock *plugin* name
    assert dock['frame'] == params['fixed_frame'] == 'odom'
    assert len(dock['pose']) == 3


def test_dock_plugin(params):
    name = params['dock_plugins'][0]
    dock = params[name]
    assert dock['plugin'] == 'opennav_docking::SimpleChargingDock'
    assert dock['use_battery_status'] is False        # no /battery_state in the headless lab
    assert 'charging_timeout' not in dock             # not a SimpleChargingDock parameter
    assert dock['use_external_detection_pose'] is True
    assert 0.0 < dock['docking_threshold'] <= 0.015   # capstone KPI: <= 15 mm
    assert dock['staging_x_offset'] < 0.0


def test_controller_block(params):
    ctrl = params['controller']
    assert ctrl['use_collision_detection'] is False
    assert 0.0 < ctrl['v_linear_min'] <= ctrl['v_linear_max']


def test_tag_offset_matches_launch(params):
    with open(os.path.join(SHARE, 'launch', 'docking_sim.launch.py')) as f:
        beyond = float(re.search(r'TAG_BEYOND_DOCK = ([0-9.]+)', f.read()).group(1))
    dock = params[params['dock_plugins'][0]]
    assert dock['external_detection_translation_x'] == pytest.approx(-beyond)


def test_integrate_straight_and_arc():
    assert integrate(0.0, 0.0, 0.0, 0.5, 0.0, 2.0) == pytest.approx((1.0, 0.0, 0.0))
    # quarter circle of radius 1: v=1, w=1 for pi/2 s
    x, y, yaw = integrate(0.0, 0.0, 0.0, 1.0, 1.0, math.pi / 2)
    assert (x, y, yaw) == pytest.approx((1.0, 1.0, math.pi / 2))


def test_step_toward_limits_acceleration():
    assert step_toward(0.0, 1.0, 0.1) == pytest.approx(0.1)
    assert step_toward(0.5, 0.45, 0.1) == pytest.approx(0.45)


def test_pose_error_in_dock_frame():
    err, lat, lon, eyaw = pose_error((0.99, 0.003, 0.02), (1.0, 0.0, 0.0))
    assert err == pytest.approx(math.hypot(0.01, 0.003))
    assert lat == pytest.approx(0.003) and lon == pytest.approx(-0.01)
    assert eyaw == pytest.approx(0.02)
    # rotated dock: 1 cm short along a dock heading of 90 deg
    _, lat, lon, _ = pose_error((0.0, 0.99, 1.5708), (0.0, 1.0, math.pi / 2))
    assert lon == pytest.approx(-0.01) and lat == pytest.approx(0.0, abs=1e-9)
