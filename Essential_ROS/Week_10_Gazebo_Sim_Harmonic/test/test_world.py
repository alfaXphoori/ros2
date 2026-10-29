"""Week 10 tests: the warehouse world is valid SDF, has the expected layout
and actually runs in a headless Gazebo Sim server."""

import os
import subprocess
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
import pytest

WORLD = os.path.join(get_package_share_directory('amr_week10'), 'worlds', 'warehouse.sdf')


def _gz_env():
    env = dict(os.environ)
    # Private Gazebo Transport partition so parallel runs never see each other
    env['GZ_PARTITION'] = f"{env.get('GZ_PARTITION', 'amr')}_w10test_{os.getpid()}"
    return env


def _pose(elem):
    return [float(v) for v in elem.find('pose').text.split()]


@pytest.fixture(scope='module')
def world():
    return ET.parse(WORLD).getroot().find('world')


def test_sdf_is_valid():
    out = subprocess.run(['gz', 'sdf', '-k', WORLD], capture_output=True, text=True,
                         timeout=60, env=_gz_env())
    assert out.returncode == 0, out.stderr
    assert 'Valid.' in out.stdout


def test_required_system_plugins(world):
    names = {p.get('name') for p in world.findall('plugin')}
    for required in ('gz::sim::systems::Physics', 'gz::sim::systems::UserCommands',
                     'gz::sim::systems::SceneBroadcaster', 'gz::sim::systems::Sensors'):
        assert required in names
    sensors = [p for p in world.findall('plugin') if p.get('name') == 'gz::sim::systems::Sensors']
    assert sensors[0].find('render_engine').text == 'ogre2'


def test_physics_step_is_1ms(world):
    physics = world.find('physics')
    assert float(physics.find('max_step_size').text) == pytest.approx(0.001)
    assert float(physics.find('real_time_factor').text) == pytest.approx(1.0)


def test_models_and_layout(world):
    models = {m.get('name'): m for m in world.findall('model')}
    assert set(models) == {'ground_plane', 'warehouse_walls'}
    for m in models.values():
        assert m.find('static').text.strip() == 'true'

    link = models['warehouse_walls'].find('link')
    cols = {c.get('name'): c for c in link.findall('collision')}
    vis = {v.get('name') for v in link.findall('visual')}
    # every collision has a visual twin (what the LiDAR hits is what you see)
    assert {n.replace('_col', '_vis') for n in cols} == vis

    # 10 x 10 m arena: walls centred at +-5 m
    assert _pose(cols['wall_north_col'])[:2] == [0.0, 5.0]
    assert _pose(cols['wall_south_col'])[:2] == [0.0, -5.0]
    assert _pose(cols['wall_east_col'])[:2] == [5.0, 0.0]
    assert _pose(cols['wall_west_col'])[:2] == [-5.0, 0.0]
    # two storage pillars (1.2 x 0.6 m) at (+-2, 2) -- later weeks rely on this
    assert _pose(cols['pillar1_col'])[:2] == [2.0, 2.0]
    assert _pose(cols['pillar2_col'])[:2] == [-2.0, 2.0]
    size = cols['pillar1_col'].find('geometry/box/size').text.split()
    assert [float(s) for s in size] == [1.2, 0.6, 2.0]


def test_headless_server_runs_and_exits_cleanly():
    # -s server only, -r run, --iterations stop after N physics steps (1 ms each)
    out = subprocess.run(
        ['gz', 'sim', '-s', '-r', '--headless-rendering', '--iterations', '2000', WORLD],
        capture_output=True, text=True, timeout=120, env=_gz_env())
    assert out.returncode == 0, out.stdout[-2000:] + out.stderr[-2000:]
