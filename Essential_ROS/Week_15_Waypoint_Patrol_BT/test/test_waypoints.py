"""Week 15: every patrol station lies in free space of the REAL map, and the
custom behavior tree is well-formed and only uses Nav2 BT nodes that exist."""

import math
import os
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
from builtin_interfaces.msg import Time
from amr_week12.map_tools import load_map
from amr_week15.waypoint_patrol import make_goal, PATROL_WAYPOINTS
import numpy as np
import pytest

INSCRIBED = 0.14     # m, Week 13 footprint
INFLATION = 0.55     # m, Week 13/14 inflation_radius
BT = os.path.join(get_package_share_directory('amr_week15'), 'behavior_trees',
                  'patrol_nav_to_pose.xml')


@pytest.fixture(scope='module')
def occupied_xy():
    grid, info = load_map(os.path.join(get_package_share_directory('amr_week12'), 'maps',
                                       'warehouse_map.yaml'))
    res, (ox, oy) = info['resolution'], info['origin'][:2]
    rows, cols = np.nonzero(grid == 100)
    return np.column_stack([ox + (cols + 0.5) * res, oy + (rows + 0.5) * res]), grid, info


@pytest.mark.parametrize('wp', PATROL_WAYPOINTS, ids=lambda w: w['name'])
def test_station_in_free_space(wp, occupied_xy):
    pts, grid, info = occupied_xy
    res, (ox, oy) = info['resolution'], info['origin'][:2]
    r, c = int((wp['y'] - oy) / res), int((wp['x'] - ox) / res)
    assert 0 <= r < grid.shape[0] and 0 <= c < grid.shape[1], 'outside the map'
    assert grid[r, c] == 0, f"{wp['name']} is not a free map cell"
    d = np.min(np.hypot(pts[:, 0] - wp['x'], pts[:, 1] - wp['y']))
    assert d > INSCRIBED, f"{wp['name']} is in a lethal/inscribed cell ({d:.2f} m)"
    assert d > INFLATION, f"{wp['name']} only {d:.2f} m from an obstacle"


def test_goal_message():
    goal = make_goal({'x': 1.0, 'y': 2.0, 'yaw': math.pi}, Time(sec=5))
    assert goal.pose.header.frame_id == 'map'
    assert (goal.pose.pose.position.x, goal.pose.pose.position.y) == (1.0, 2.0)
    assert abs(goal.pose.pose.orientation.z) == pytest.approx(1.0)


def test_patrol_returns_home():
    assert (PATROL_WAYPOINTS[-1]['x'], PATROL_WAYPOINTS[-1]['y']) == (0.0, 0.0)


KNOWN_BT_NODES = {
    # control / decorator nodes from BehaviorTree.CPP + nav2_behavior_tree
    'RecoveryNode', 'PipelineSequence', 'RateController', 'Sequence', 'ReactiveFallback',
    'RoundRobin', 'Fallback', 'ReactiveSequence',
    # Nav2 action / condition nodes (nav2_behavior_tree plugins)
    'ComputePathToPose', 'SmoothPath', 'FollowPath', 'ClearEntireCostmap', 'GoalUpdated',
    'Spin', 'Wait', 'BackUp',
}


def test_bt_xml_wellformed_and_known_nodes():
    root = ET.parse(BT).getroot()
    assert root.get('BTCPP_format') == '4'
    main = root.get('main_tree_to_execute')
    trees = {t.get('ID'): t for t in root.findall('BehaviorTree')}
    assert main in trees
    used = {e.tag for e in trees[main].iter()} - {'BehaviorTree'}
    assert used <= KNOWN_BT_NODES, used - KNOWN_BT_NODES
    # the smoothed path is what the controller follows
    smooth = next(trees[main].iter('SmoothPath'))
    follow = next(trees[main].iter('FollowPath'))
    assert smooth.get('smoothed_path') == follow.get('path') == '{path}'
    assert smooth.get('smoother_id') == 'simple_smoother'
