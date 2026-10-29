"""Week 16 unit tests: mission stations are in free space of the real map and
the PASS/FAIL evaluation only passes when every stage SUCCEEDED."""

import os

from ament_index_python.packages import get_package_share_directory
from amr_week12.map_tools import load_map
from amr_week16.final_mission_executor import evaluate, MISSION
from nav2_simple_commander.robot_navigator import TaskResult
import numpy as np
import pytest


@pytest.mark.parametrize('wp', MISSION, ids=lambda w: w['name'])
def test_station_clear_of_obstacles(wp):
    grid, info = load_map(os.path.join(get_package_share_directory('amr_week12'), 'maps',
                                       'warehouse_map.yaml'))
    res, (ox, oy) = info['resolution'], info['origin'][:2]
    rows, cols = np.nonzero(grid == 100)
    d = np.min(np.hypot(ox + (cols + 0.5) * res - wp['x'], oy + (rows + 0.5) * res - wp['y']))
    assert grid[int((wp['y'] - oy) / res), int((wp['x'] - ox) / res)] == 0
    assert d > 0.55, f"{wp['name']} only {d:.2f} m from an obstacle (inflation radius 0.55 m)"


def test_evaluate():
    ok = TaskResult.SUCCEEDED
    assert evaluate([ok, ok, ok]) == (3, 100.0, 'PASS')
    assert evaluate([ok, TaskResult.FAILED])[2] == 'FAIL'
    assert evaluate([ok, ok, TaskResult.CANCELED])[:2] == (2, pytest.approx(66.67, abs=0.01))
    assert evaluate([])[2] == 'FAIL'


def test_plot_path(tmp_path):
    from amr_week16.mission_path import plot
    csv_file = tmp_path / 'p.csv'
    csv_file.write_text('t,x,y,yaw\n0,0,0,0\n1,0.5,0.3,0.1\n2,1.5,1.0,1.57\n')
    png = tmp_path / 'p.png'
    n = plot(str(csv_file), str(png), os.path.join(
        get_package_share_directory('amr_week12'), 'maps', 'warehouse_map.yaml'))
    assert n == 3 and png.stat().st_size > 10000
