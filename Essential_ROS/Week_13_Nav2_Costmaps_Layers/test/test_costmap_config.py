"""Week 13: static checks of config/costmap_params.yaml (no ROS graph)."""

import math
import os

from ament_index_python.packages import get_package_share_directory
import pytest
import yaml

CFG = os.path.join(get_package_share_directory('amr_week13'), 'config', 'costmap_params.yaml')


@pytest.fixture(scope='module')
def cfg():
    with open(CFG) as f:
        return yaml.safe_load(f)


def params(cfg, name):
    return cfg[name][name]['ros__parameters']


def footprint(p):
    return yaml.safe_load(p['footprint'])


def test_both_costmaps_use_the_same_footprint(cfg):
    assert footprint(params(cfg, 'local_costmap')) == footprint(params(cfg, 'global_costmap'))
    for name in ('local_costmap', 'global_costmap'):
        assert 'robot_radius' not in params(cfg, name), 'footprint and robot_radius conflict'


def test_footprint_matches_urdf(cfg):
    pts = footprint(params(cfg, 'local_costmap'))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    assert max(xs) - min(xs) == pytest.approx(0.40)   # chassis length
    assert max(ys) - min(ys) == pytest.approx(0.28)   # outer wheel width


def test_inflation_covers_circumscribed_radius(cfg):
    pts = footprint(params(cfg, 'global_costmap'))
    circumscribed = max(math.hypot(x, y) for x, y in pts)
    assert circumscribed == pytest.approx(0.244, abs=1e-3)
    for name in ('local_costmap', 'global_costmap'):
        infl = params(cfg, name)['inflation_layer']
        assert infl['inflation_radius'] > circumscribed
    assert params(cfg, 'local_costmap')['inflation_layer'] == \
        params(cfg, 'global_costmap')['inflation_layer']


def test_frames_and_layers(cfg):
    local, glob = params(cfg, 'local_costmap'), params(cfg, 'global_costmap')
    assert local['global_frame'] == 'odom' and local['rolling_window'] is True
    assert glob['global_frame'] == 'map'
    assert glob['plugins'][0] == 'static_layer'
    assert glob['plugins'][-1] == 'inflation_layer' and local['plugins'][-1] == 'inflation_layer'
    for p in (local, glob):
        assert p['use_sim_time'] is True
        assert p['robot_base_frame'] == 'base_footprint'
        # LiDAR max range is 10 m
        assert p['obstacle_layer']['scan']['raytrace_max_range'] <= 10.0


def test_snapshot_summaries():
    from amr_week13.costmap_snapshot import occupancy_summary, raw_summary
    occ = occupancy_summary([-1, 0, 0, 5, 98, 99, 100, 100])
    assert occ == {'unknown(-1)': 1, 'free(0)': 2, 'inflated(1..98)': 2,
                   'inscribed(99)': 1, 'lethal(100)': 2}
    raw = raw_summary([0, 1, 252, 253, 254, 255, 255])
    assert raw == {'free(0)': 1, 'inflated(1..252)': 2, 'inscribed(253)': 1,
                   'lethal(254)': 1, 'no_information(255)': 2}
