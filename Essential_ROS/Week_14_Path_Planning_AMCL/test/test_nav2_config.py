"""Week 14: static checks of the Nav2 configuration and launch (no ROS graph).
Each check corresponds to a bug that kept Nav2 from activating or behaving."""

import os

from ament_index_python.packages import get_package_share_directory
from amr_week14.amcl_initial_pose import make_initial_pose
import pytest
import yaml

W14 = get_package_share_directory('amr_week14')


@pytest.fixture(scope='module')
def cfg():
    with open(os.path.join(W14, 'config', 'nav2_params.yaml')) as f:
        return yaml.safe_load(f)


def p(cfg, node):
    return cfg[node]['ros__parameters']


def test_dwb_has_critics(cfg):
    fp = p(cfg, 'controller_server')['FollowPath']
    assert fp['plugin'] == 'dwb_core::DWBLocalPlanner'
    assert len(fp['critics']) >= 5
    for critic in ('BaseObstacle', 'PathAlign', 'PathDist', 'GoalAlign', 'GoalDist', 'RotateToGoal'):
        assert critic in fp['critics']
        assert f'{critic}.scale' in fp, f'no scale for critic {critic}'


def test_jazzy_progress_checker_schema(cfg):
    cs = p(cfg, 'controller_server')
    assert 'progress_checker_plugin' not in cs
    assert cs['progress_checker_plugins'] == ['progress_checker']
    assert 'plugin' in cs['progress_checker']


def test_ranges_match_lidar(cfg):
    assert p(cfg, 'amcl')['laser_max_range'] <= 10.0
    assert p(cfg, 'amcl')['base_frame_id'] == 'base_footprint'


def test_behaviors_for_default_bt(cfg):
    plugins = p(cfg, 'behavior_server')['behavior_plugins']
    for b in ('spin', 'backup', 'wait'):
        assert b in plugins


def test_costmaps_identical_to_week13(cfg):
    with open(os.path.join(get_package_share_directory('amr_week13'), 'config',
                           'costmap_params.yaml')) as f:
        w13 = yaml.safe_load(f)
    for name in ('local_costmap', 'global_costmap'):
        assert cfg[name][name]['ros__parameters'] == w13[name][name]['ros__parameters'], name


def test_all_nodes_use_sim_time(cfg):
    for node, body in cfg.items():
        params = body.get('ros__parameters') or body[node]['ros__parameters']
        assert params.get('use_sim_time') is True, node


def test_launch_manages_every_server():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'nav2_bringup_launch', os.path.join(W14, 'launch', 'nav2_bringup.launch.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ld = mod.generate_launch_description()
    nodes = [e for e in ld.entities if type(e).__name__ == 'Node']
    executables = {n.node_executable for n in nodes}
    for exe in ('map_server', 'amcl', 'controller_server', 'planner_server', 'smoother_server',
                'behavior_server', 'velocity_smoother', 'collision_monitor', 'bt_navigator',
                'waypoint_follower', 'lifecycle_manager'):
        assert exe in executables, exe


def test_initial_pose_message():
    msg = make_initial_pose(1.0, -2.0, 1.5707963, 'map')
    assert msg.header.frame_id == 'map'
    assert (msg.pose.pose.position.x, msg.pose.pose.position.y) == (1.0, -2.0)
    assert msg.pose.pose.orientation.z == pytest.approx(0.7071, abs=1e-4)
    assert msg.pose.pose.orientation.w == pytest.approx(0.7071, abs=1e-4)
    assert msg.pose.covariance[0] == pytest.approx(0.25)
    assert msg.pose.covariance[7] == pytest.approx(0.25)
    assert msg.pose.covariance[35] == pytest.approx(0.0685, abs=1e-3)
