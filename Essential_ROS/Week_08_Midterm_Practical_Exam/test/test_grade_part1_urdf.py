"""Autograder part 1 (35 pts): hospital_amr.urdf numeric specification (Exam_Task.md).

  EXAM_SUBMISSION_DIR=/path/to/student python3 -m pytest \
      Essential_ROS/Week_08_Midterm_Practical_Exam/test/test_grade_part1_urdf.py -v
"""
import os
import shutil
import subprocess
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exam_common import URDF_PATH, UrdfModel, origin_of, vec  # noqa: E402

TOL = 1e-3          # metres / kg
REL = 0.01          # 1 % on inertia values

REQUIRED_LINKS = ['base_footprint', 'base_link', 'left_wheel_link', 'right_wheel_link',
                  'front_caster_link', 'rear_caster_link', 'lidar_link']
WHEELS = {'left_wheel_link': +0.17, 'right_wheel_link': -0.17}
CASTERS = {'front_caster_link': +0.18, 'rear_caster_link': -0.18}


@pytest.fixture(scope='module')
def model():
    assert os.path.isfile(URDF_PATH), f'missing {URDF_PATH}'
    return UrdfModel(URDF_PATH)


def test_check_urdf_passes():
    if shutil.which('check_urdf') is None:
        pytest.skip('check_urdf not installed')
    out = subprocess.run(['check_urdf', URDF_PATH], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stdout + out.stderr
    assert 'Successfully Parsed XML' in out.stdout
    assert 'root Link: base_footprint' in out.stdout


def test_link_joint_tree(model):
    for name in REQUIRED_LINKS:
        assert name in model.links, f'missing link {name}'
    for link in REQUIRED_LINKS[1:]:
        assert link in model.joint_of_child, f'{link} has no parent joint'
    assert model.joint_of_child['base_link'].find('parent').get('link') == 'base_footprint'
    for link in REQUIRED_LINKS[2:]:
        assert model.joint_of_child[link].find('parent').get('link') == 'base_link', link
    for link in ('front_caster_link', 'rear_caster_link', 'lidar_link'):
        assert model.joint_of_child[link].get('type') == 'fixed', link


def test_chassis_box_mass_inertia(model):
    size = vec(model.geometry('base_link', 'box').get('size'))
    assert size == pytest.approx([0.50, 0.30, 0.15], abs=TOL)
    assert model.mass('base_link') == pytest.approx(8.0, abs=TOL)
    tensor = model.inertia_in_link_frame('base_link')
    assert np.diag(tensor) == pytest.approx([0.075000, 0.181667, 0.226667], rel=REL)


@pytest.mark.parametrize('wheel', WHEELS)
def test_drive_wheel(model, wheel):
    joint = model.joint_of_child[wheel]
    assert joint.get('type') == 'continuous'
    axis = vec(joint.find('axis').get('xyz'))
    assert np.allclose(axis, [0, 1, 0]), 'wheel must spin about +Y'
    cyl = model.geometry(wheel, 'cylinder')
    assert float(cyl.get('radius')) == pytest.approx(0.08, abs=TOL)
    assert float(cyl.get('length')) == pytest.approx(0.04, abs=TOL)
    assert model.mass(wheel) == pytest.approx(0.80, abs=TOL)
    pos, _ = model.pose(wheel, root='base_link')
    assert pos[1] == pytest.approx(WHEELS[wheel], abs=TOL)
    # Inertia about the real spin axis (catches a rotated inertial frame + swapped values)
    tensor = model.inertia_in_link_frame(wheel)
    assert tensor[1, 1] == pytest.approx(0.002560, rel=REL), 'spin-axis inertia (Iyy)'
    assert tensor[0, 0] == pytest.approx(0.001387, rel=REL)
    assert tensor[2, 2] == pytest.approx(0.001387, rel=REL)


@pytest.mark.parametrize('wheel', WHEELS)
def test_wheel_cylinder_aligned_with_axis(model, wheel):
    _, rot = origin_of(model.links[wheel].find('visual'))
    assert abs((rot @ [0, 0, 1]) @ np.array([0, 1, 0])) == pytest.approx(1.0, abs=1e-3)


@pytest.mark.parametrize('caster', CASTERS)
def test_caster(model, caster):
    sphere = model.geometry(caster, 'sphere')
    assert sphere is not None, 'caster must be a sphere'
    r = float(sphere.get('radius'))
    assert r == pytest.approx(0.03, abs=TOL)
    assert model.mass(caster) == pytest.approx(0.25, abs=TOL)
    pos, _ = model.pose(caster, root='base_link')
    assert pos[0] == pytest.approx(CASTERS[caster], abs=TOL)
    assert model.pose(caster)[0][2] == pytest.approx(r, abs=TOL), 'caster must touch the floor'
    assert np.diag(model.inertia_in_link_frame(caster)) == pytest.approx(
        [0.4 * 0.25 * r ** 2] * 3, rel=REL)


def test_wheels_touch_ground_and_clear_chassis(model):
    half_width = vec(model.geometry('base_link', 'box').get('size'))[1] / 2
    for wheel in WHEELS:
        cyl = model.geometry(wheel, 'cylinder')
        r, length = float(cyl.get('radius')), float(cyl.get('length'))
        pos = model.pose(wheel)[0]
        assert pos[2] == pytest.approx(r, abs=TOL), f'{wheel} sinks into / floats above floor'
        assert abs(pos[1]) - length / 2 >= half_width - TOL, f'{wheel} is inside the chassis'


def test_chassis_above_ground(model):
    bottom, _ = model.box_extent_z('base_link')
    assert bottom > 0.0, 'chassis box goes below the floor'


def test_lidar_position_on_roof(model):
    pos, rot = model.pose('lidar_link', root='base_link')
    assert pos[0] == pytest.approx(0.12, abs=TOL)
    assert pos[1] == pytest.approx(0.0, abs=TOL)
    assert pos[2] == pytest.approx(0.18, abs=TOL)
    assert np.allclose(rot, np.eye(3), atol=1e-3), 'LiDAR must be upright (REP 103)'
    _, roof = model.box_extent_z('base_link')
    shape = model.geometry('lidar_link', 'cylinder')
    half = float(shape.get('length')) / 2 if shape is not None else 0.0
    lidar_bottom = model.pose('lidar_link')[0][2] - half
    assert lidar_bottom >= roof - TOL, 'LiDAR is buried inside the chassis'


@pytest.mark.parametrize('link', REQUIRED_LINKS[1:])
def test_inertia_positive_definite(model, link):
    tensor = model.inertia_in_link_frame(link)
    assert np.all(np.linalg.eigvalsh(tensor) > 0), f'{link} inertia not positive-definite'
    a, b, c = np.linalg.eigvalsh(tensor)
    assert a + b >= c - 1e-6, f'{link} violates the triangle inequality'


def test_diff_drive_plugin_consistent_if_present(model):
    plugins = [p for p in model.root.iter('plugin')
               if p.get('name') == 'gz::sim::systems::DiffDrive']
    if not plugins:
        pytest.skip('no DiffDrive plugin (optional)')
    p = plugins[0]
    assert float(p.findtext('wheel_separation')) == pytest.approx(0.34, abs=TOL)
    assert float(p.findtext('wheel_radius')) == pytest.approx(0.08, abs=TOL)
