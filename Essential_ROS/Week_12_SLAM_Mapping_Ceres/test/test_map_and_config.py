"""Week 12: the committed map is a REAL SLAM map of warehouse.sdf, the SLAM
parameter file is actually applied (key == node name), and the explorer's
controller behaves."""

import math
import os

from ament_index_python.packages import get_package_share_directory
from amr_week12.explore_warehouse import go_to_point, ROUTE
from amr_week12.map_tools import load_map, map_stats, sdf_boxes
import numpy as np
import pytest
import yaml

W12 = get_package_share_directory('amr_week12')
MAP = os.path.join(W12, 'maps', 'warehouse_map.yaml')
SDF = os.path.join(get_package_share_directory('amr_week10'), 'worlds', 'warehouse.sdf')


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _no_duplicates(loader, node, deep=False):
    keys = [loader.construct_object(k, deep=deep) for k, _ in node.value]
    dup = {k for k in keys if keys.count(k) > 1}
    assert not dup, f'duplicate YAML keys: {dup}'
    return loader.construct_mapping(node, deep)


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates)


@pytest.fixture(scope='module')
def stats():
    return map_stats(MAP, SDF)


def test_slam_params_key_matches_node_name():
    with open(os.path.join(W12, 'config', 'slam_toolbox_params.yaml')) as f:
        cfg = yaml.load(f, Loader=UniqueKeyLoader)
    assert list(cfg) == ['slam_toolbox']          # node name in online_async_launch.py
    p = cfg['slam_toolbox']['ros__parameters']
    assert p['max_laser_range'] <= 10.0          # LiDAR max range
    assert p['base_frame'] == 'base_footprint'
    assert p['mode'] == 'mapping'


def test_map_covers_10x10_arena(stats):
    assert stats['resolution'] == pytest.approx(0.05)
    ex, ey = stats['known_extent_m']
    assert 9.5 <= ex <= 10.6 and 9.5 <= ey <= 10.6, stats['known_extent_m']
    # a 10 x 10 m room at 5 cm: ~40 000 cells; most must be explored
    assert stats['free'] > 30000
    assert stats['unknown'] < 0.1 * stats['width'] * stats['height']


def test_map_matches_sdf_geometry(stats):
    # occupied cells lie on the SDF walls/pillars (+-2 cells), and most walls were seen
    assert stats['precision_tol'] > 0.9, stats
    assert stats['recall_tol'] > 0.8, stats


def test_pillars_present_and_centre_free():
    grid, info = load_map(MAP)
    res, (ox, oy) = info['resolution'], info['origin'][:2]

    def window(x0, y0, x1, y1):
        r0, r1 = int((y0 - oy) / res), int((y1 - oy) / res)
        c0, c1 = int((x0 - ox) / res), int((x1 - ox) / res)
        return grid[r0:r1, c0:c1]

    pillars = [b for b in sdf_boxes(SDF) if b[4].startswith('pillar')]
    assert len(pillars) == 2
    for cx, cy, sx, sy, name in pillars:
        w = window(cx - sx / 2 - 0.1, cy - sy / 2 - 0.1, cx + sx / 2 + 0.1, cy + sy / 2 + 0.1)
        assert (w == 100).sum() > 40, f'{name} not in map'
    assert np.all(window(-1.0, -1.0, 1.0, 1.0) == 0), 'phantom obstacle near origin'


def test_go_to_point_controller():
    v, w, done = go_to_point(0.0, 0.0, 0.0, 2.0, 0.0)
    assert v > 0 and abs(w) < 1e-9 and not done
    v, w, done = go_to_point(0.0, 0.0, 0.0, 0.0, 2.0)      # goal to the left
    assert v == 0.0 and w > 0 and not done                 # turn in place first
    assert go_to_point(1.0, 1.0, 0.3, 1.05, 1.0)[2] is True


def test_route_avoids_pillars():
    for step in ROUTE:
        if step[0] == 'spin':
            continue
        x, y = step
        for cx, cy, sx, sy, name in sdf_boxes(SDF):
            # keep 0.35 m clearance (robot half-length 0.2 m + margin)
            assert not (abs(x - cx) < sx / 2 + 0.35 and abs(y - cy) < sy / 2 + 0.35), (step, name)
    assert math.hypot(*ROUTE[-1]) < 1e-9   # ends at home
