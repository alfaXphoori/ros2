"""Module 06 unit tests (no ROS graph): mission geometry in the real map, configuration
consistency with modules 03/Week 14, KPI/rubric consistency between config and the docs,
and the pure helpers used by the launch file and the mission executor."""

import json
import math
import os
import re

from amr_adv06 import capstone_config as cc
from amr_adv06.capstone_mission import evaluate, front_min_range
from amr_week12.map_tools import load_map
from ament_index_python.packages import get_package_share_directory
import numpy as np
import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MISSION = cc.load_mission(os.path.join(HERE, 'config', 'capstone_mission.yaml'))
KPIS = cc.load_kpis(os.path.join(HERE, 'config', 'kpi_targets.yaml'))
INFLATION = 0.55   # amr_week14 nav2_params.yaml inflation_radius


def read(name):
    with open(os.path.join(HERE, name), encoding='utf-8') as f:
        return f.read()


@pytest.fixture(scope='module')
def grid_info():
    return load_map(os.path.join(get_package_share_directory('amr_week12'), 'maps',
                                 'warehouse_map.yaml'))


def clearance(grid_info, x, y):
    grid, info = grid_info
    res, (ox, oy) = info['resolution'], info['origin'][:2]
    assert grid[int((y - oy) / res), int((x - ox) / res)] == 0, f'({x}, {y}) not free'
    rows, cols = np.nonzero(grid == 100)
    return float(np.min(np.hypot(ox + (cols + 0.5) * res - x, oy + (rows + 0.5) * res - y)))


NAV_POINTS = [MISSION['home']] + MISSION['stations'] + [
    dict(zip(('x', 'y'), cc.staging_pose(MISSION['dock'])), name='dock staging pose')]


@pytest.mark.parametrize('wp', NAV_POINTS, ids=lambda w: w['name'])
def test_nav_goals_free_in_real_map(grid_info, wp):
    d = clearance(grid_info, wp['x'], wp['y'])
    assert d > INFLATION, f"{wp['name']} only {d:.2f} m from an obstacle"


def test_dock_and_tag_in_free_space(grid_info):
    dx, dy, _ = cc.dock_pose(MISSION['dock'])
    tx, ty, _, _ = cc.tag_world(MISSION['dock'])
    # docked robot footprint (0.40 x 0.28 m, circumscribed 0.244 m) must not touch the map
    assert clearance(grid_info, dx, dy) > 0.30
    assert clearance(grid_info, tx, ty) > 0.10


def test_tag_geometry_matches_module03_docking_params():
    adv03 = cc.load_yaml(os.path.join(get_package_share_directory('amr_adv03'), 'config',
                                      'docking_server_params.yaml'))
    p = adv03['docking_server']['ros__parameters']
    dock = MISSION['dock']
    assert dock['type'] in p['dock_plugins']
    assert -p['simple_charging_dock']['external_detection_translation_x'] == \
        pytest.approx(dock['tag_beyond_dock'])
    sx, sy, _ = cc.staging_pose(dock, p['simple_charging_dock']['staging_x_offset'])
    assert (sx, sy) == pytest.approx(cc.staging_pose(dock)[:2])
    # threshold of the docking server = passing KPI for the docking error
    assert p['simple_charging_dock']['docking_threshold'] * 1000.0 == \
        pytest.approx(KPIS['kpis']['docking_error_mm']['pass'])


def test_tag_world_pose():
    dock = {'x': 1.0, 'y': 2.0, 'yaw_deg': 90.0, 'tag_beyond_dock': 0.4, 'tag_height': 0.1}
    x, y, z, yaw = cc.tag_world(dock)
    assert (x, y, z) == pytest.approx((1.0, 2.4, 0.1))
    assert yaw == pytest.approx(-math.pi / 2)        # tag normal faces the robot
    assert cc.staging_pose(dock)[:2] == pytest.approx((1.0, 1.3))


def test_merged_nav2_params_keep_week14_and_add_stop_zone(tmp_path):
    week14 = os.path.join(get_package_share_directory('amr_week14'), 'config',
                          'nav2_params.yaml')
    out = tmp_path / 'merged.yaml'
    merged = cc.merge_yaml_files(week14, os.path.join(HERE, 'config', 'nav2_overrides.yaml'),
                                 str(out))
    base = cc.load_yaml(week14)
    cm = merged['collision_monitor']['ros__parameters']
    assert cm['polygons'] == ['StopZone', 'FootprintApproach']
    assert cm['StopZone']['action_type'] == 'stop'
    assert cm['FootprintApproach'] == base['collision_monitor']['ros__parameters'][
        'FootprintApproach']
    assert cm['cmd_vel_out_topic'] == 'cmd_vel'               # last node before Gazebo
    assert merged['amcl'] == base['amcl']                     # untouched sections survive
    assert cc.load_yaml(str(out)) == merged


def test_estop_obstacle_inside_stop_zone():
    cm = cc.load_yaml(os.path.join(HERE, 'config', 'nav2_overrides.yaml'))[
        'collision_monitor']['ros__parameters']
    pts = np.array(json.loads(cm['StopZone']['points']))  # "[[x, y], ...]" (Jazzy format)
    d = MISSION['estop_test']['obstacle_face_distance']
    assert pts[:, 0].min() == pytest.approx(0.20)     # starts at the bumper
    assert pts[:, 0].min() < d < pts[:, 0].max()
    assert MISSION['estop_test']['obstacle_size'][1] / 2 < pts[:, 1].max() + 0.1


def test_deep_merge():
    base = {'a': {'b': 1, 'c': [1, 2]}, 'd': 1}
    out = cc.deep_merge(base, {'a': {'c': [3]}, 'e': {'f': 2}})
    assert out == {'a': {'b': 1, 'c': [3]}, 'd': 1, 'e': {'f': 2}}
    assert base == {'a': {'b': 1, 'c': [1, 2]}, 'd': 1}       # input not modified


def test_invert_transform_round_trip():
    yaw = 0.7
    t, q = (1.0, -2.0, 0.1), (0.0, 0.0, math.sin(yaw / 2), math.cos(yaw / 2))
    t_inv, q_inv = cc.invert_transform(t, q)
    # world origin seen from the robot: rotate -t by -yaw
    assert t_inv[0] == pytest.approx(-(math.cos(yaw) * 1.0 + math.sin(yaw) * -2.0))
    assert t_inv[1] == pytest.approx(-(-math.sin(yaw) * 1.0 + math.cos(yaw) * -2.0))
    assert t_inv[2] == pytest.approx(-0.1)
    assert cc.yaw_from_quaternion(*q_inv) == pytest.approx(-yaw)


def test_gap_to_face_and_pose_error():
    face = cc.ahead(0.0, 0.0, 0.0, 0.35)
    assert cc.gap_to_face(face, 0.0, 0.0, 0.0, 0.0) == pytest.approx(0.15)
    assert cc.gap_to_face(face, 0.0, 0.2, 0.05, 0.1) < 0.0     # bumper went past the face
    yaw = -math.pi / 2
    err, lat, lon, eyaw = cc.pose_error((-1.0, -3.51, yaw), (-1.0, -3.5, yaw))
    # 1 cm too far INTO the dock (dock x axis points to -y): longitudinal +10 mm
    assert (err, lat, lon, eyaw) == pytest.approx((0.01, 0.0, 0.01, 0.0), abs=1e-9)


def test_kpi_verdict_and_evaluate():
    assert cc.kpi_verdict(11.6, 15.0) == 'PASS'
    assert cc.kpi_verdict(16.0, 15.0) == 'FAIL'
    assert cc.kpi_verdict(5.9, 2.0, lower_is_better=False) == 'PASS'
    assert cc.kpi_verdict(None, 2.0) == 'N/A'
    ok = [{'ok': True}] * 3
    assert evaluate(ok, [{'verdict': 'PASS'}]) == (3, 1, 'PASS')
    assert evaluate(ok, [{'verdict': 'FAIL'}])[2] == 'FAIL'
    assert evaluate(ok + [{'ok': False}], [])[2] == 'FAIL'
    assert evaluate([], [])[2] == 'FAIL'


def test_front_min_range():
    class Scan:
        angle_min, angle_increment = -math.pi, 2 * math.pi / 360
        range_min, range_max = 0.12, 10.0
        ranges = [5.0] * 360
    s = Scan()
    s.ranges = list(s.ranges)
    s.ranges[180] = 0.27          # straight ahead
    s.ranges[0] = 0.15            # straight behind: ignored
    assert front_min_range(s) == pytest.approx(0.27)


def test_kpi_table_in_readme_matches_config():
    text = read('Readme.md')
    for key, k in KPIS['kpis'].items():
        row = [ln for ln in text.splitlines() if ln.startswith('|') and f'`{key}`' in ln]
        assert len(row) == 1, f'KPI {key} missing in the Readme.md table'
        nums = [float(v) for v in re.findall(r'(\d+(?:\.\d+)?)', row[0].split('`')[-1])]
        assert k['pass'] in nums and k['excellence'] in nums, row[0]


def test_rubric_weights_match_config():
    rubric = KPIS['rubric']
    dims = rubric['dimensions']
    assert sum(d['weight'] for d in dims) == 100
    text = read('rubrics.md')
    found = re.findall(r'^\| \*\*(\d)\. ([^*]+)\*\* \| \*\*(\d+)%\*\*', text, re.M)
    assert [(int(i), n.strip(), int(w)) for i, n, w in found] == \
        [(d['id'], d['name'], d['weight']) for d in dims]
    w = rubric['course_weight_pct']
    assert f"{w['capstone_project']}%" in text and f"{w['oral_defense']}%" in text


def test_docs_have_no_stale_claims():
    readme = read('Readme.md')
    lab = read('Lab_Exercises.md')
    for doc in (readme, lab):
        assert 'Essential_ROS/02_Robot_Modeling_TF2' not in doc
        assert 'Zero-Copy' not in doc and 'ODE Physics' not in doc
        assert 'user@amr-dev' not in doc and 'CHECKPOINT PASSED' not in doc
