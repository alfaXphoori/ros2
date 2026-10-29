"""Static checks of urdf/diff_drive_robot.urdf (no ROS graph needed).

Run:  python3 -m pytest Essential_ROS/Week_07_URDF_Robot_Modeling/test/test_urdf_model.py -v
"""
import math
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

import numpy as np
import pytest

PKG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URDF = os.path.join(PKG_DIR, 'urdf', 'diff_drive_robot.urdf')
sys.path.insert(0, os.path.join(PKG_DIR, 'src'))
import inertia_calculator  # noqa: E402  (module under src/, installed as amr_week07)


def rpy_to_matrix(r, p, y):
    cr, sr, cp, sp, cy, sy = (math.cos(r), math.sin(r), math.cos(p), math.sin(p),
                              math.cos(y), math.sin(y))
    rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return rz @ ry @ rx          # URDF convention: fixed-axis roll, pitch, yaw


def rpy_to_quaternion(r, p, y):
    """Return (x, y, z, w) like tf_transformations.quaternion_from_euler."""
    cr, sr = math.cos(r / 2), math.sin(r / 2)
    cp, sp = math.cos(p / 2), math.sin(p / 2)
    cy, sy = math.cos(y / 2), math.sin(y / 2)
    return np.array([sr * cp * cy - cr * sp * sy,
                     cr * sp * cy + sr * cp * sy,
                     cr * cp * sy - sr * sp * cy,
                     cr * cp * cy + sr * sp * sy])


def vec(text, default='0 0 0'):
    return np.array([float(v) for v in (text or default).split()])


def origin_of(elem):
    o = elem.find('origin') if elem is not None else None
    if o is None:
        return np.zeros(3), np.eye(3)
    return vec(o.get('xyz')), rpy_to_matrix(*vec(o.get('rpy')))


@pytest.fixture(scope='module')
def robot():
    return ET.parse(URDF).getroot()


@pytest.fixture(scope='module')
def links(robot):
    return {link.get('name'): link for link in robot.findall('link')}


@pytest.fixture(scope='module')
def joints(robot):
    return {j.get('name'): j for j in robot.findall('joint')}


@pytest.fixture(scope='module')
def poses(joints):
    """Pose (position, rotation) of every link in base_footprint at zero joint angles."""
    by_child = {j.find('child').get('link'): j for j in joints.values()}
    cache = {'base_footprint': (np.zeros(3), np.eye(3))}

    def pose(name):
        if name not in cache:
            j = by_child[name]
            pp, pr = pose(j.find('parent').get('link'))
            xyz, rot = origin_of(j)
            cache[name] = (pp + pr @ xyz, pr @ rot)
        return cache[name]
    for child in by_child:
        pose(child)
    return cache


@pytest.fixture(scope='module')
def diff_drive(robot):
    for plugin in robot.iter('plugin'):
        if plugin.get('name') == 'gz::sim::systems::DiffDrive':
            return plugin
    pytest.fail('gz::sim::systems::DiffDrive plugin not found')


def wheel_geometry(link):
    """(radius, width) of the wheel from its visual cylinder."""
    cyl = link.find('visual/geometry/cylinder')
    return float(cyl.get('radius')), float(cyl.get('length'))


def test_check_urdf_parses():
    if shutil.which('check_urdf') is None:
        pytest.skip('check_urdf (liburdfdom-tools) not installed')
    out = subprocess.run(['check_urdf', URDF], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stdout + out.stderr
    assert 'Successfully Parsed XML' in out.stdout
    assert 'root Link: base_footprint' in out.stdout


def test_gz_sdf_converts():
    if shutil.which('gz') is None:
        pytest.skip('gz (Gazebo Sim) not installed')
    out = subprocess.run(['gz', 'sdf', '-p', URDF], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert "<model name='diff_drive_robot'>" in out.stdout
    assert 'gz-sim-diff-drive-system' in out.stdout
    assert 'Error' not in out.stderr, out.stderr


def test_frame_names_are_stable(links, joints):
    # Later weeks (Gazebo, SLAM, Nav2) depend on these exact names.
    for name in ('base_footprint', 'base_link', 'left_wheel_link', 'right_wheel_link',
                 'lidar_link', 'camera_link', 'camera_optical_link'):
        assert name in links
    assert joints['left_wheel_joint'].get('type') == 'continuous'
    assert joints['right_wheel_joint'].get('type') == 'continuous'


def test_diff_drive_plugin_matches_geometry(links, poses, diff_drive):
    separation = float(diff_drive.findtext('wheel_separation'))
    radius = float(diff_drive.findtext('wheel_radius'))
    left = poses['left_wheel_link'][0]
    right = poses['right_wheel_link'][0]
    assert separation == pytest.approx(abs(left[1] - right[1]), abs=1e-9)
    for wheel in ('left_wheel_link', 'right_wheel_link'):
        assert radius == pytest.approx(wheel_geometry(links[wheel])[0], abs=1e-9)
    assert diff_drive.findtext('left_joint') == 'left_wheel_joint'
    assert diff_drive.findtext('right_joint') == 'right_wheel_joint'
    assert diff_drive.findtext('child_frame_id') == 'base_footprint'
    assert diff_drive.findtext('frame_id') == 'odom'
    assert diff_drive.findtext('topic') == '/cmd_vel'
    assert diff_drive.findtext('odom_topic') == '/odom'


@pytest.mark.parametrize('name', ['base_link', 'left_wheel_link', 'right_wheel_link',
                                  'front_caster_link', 'rear_caster_link', 'lidar_link',
                                  'camera_link'])
def test_inertia_physically_valid(links, name):
    inertial = links[name].find('inertial')
    assert inertial is not None, f'{name} has no <inertial>'
    assert float(inertial.find('mass').get('value')) > 0
    i = inertial.find('inertia')
    g = {k: float(i.get(k)) for k in ('ixx', 'iyy', 'izz', 'ixy', 'ixz', 'iyz')}
    tensor = np.array([[g['ixx'], g['ixy'], g['ixz']],
                       [g['ixy'], g['iyy'], g['iyz']],
                       [g['ixz'], g['iyz'], g['izz']]])
    assert np.all(np.linalg.eigvalsh(tensor) > 0), f'{name} inertia not positive-definite'
    a, b, c = g['ixx'], g['iyy'], g['izz']
    # Triangle inequality (small tolerance for 6-digit rounding in the file)
    tol = 1e-6
    assert a + b >= c - tol and b + c >= a - tol and a + c >= b - tol, name


@pytest.mark.parametrize('wheel', ['left_wheel_link', 'right_wheel_link'])
def test_wheel_inertia_about_spin_axis(links, joints, wheel):
    """Spin-axis moment must be 1/2 m r^2, the other two 1/12 m (3r^2 + h^2).

    The tensor is rotated into the link frame using the <inertial><origin rpy>,
    so a rotated inertial frame plus a pre-rotated tensor (rotation applied
    twice) is detected.
    """
    link = links[wheel]
    joint = joints[wheel.replace('_link', '_joint')]
    axis = vec(joint.find('axis').get('xyz'))
    axis = axis / np.linalg.norm(axis)
    inertial = link.find('inertial')
    m = float(inertial.find('mass').get('value'))
    r, h = wheel_geometry(link)
    i = inertial.find('inertia')
    tensor_in = np.diag([float(i.get('ixx')), float(i.get('iyy')), float(i.get('izz'))])
    _, rot = origin_of(inertial)
    tensor_link = rot @ tensor_in @ rot.T
    spin = axis @ tensor_link @ axis
    assert spin == pytest.approx(0.5 * m * r ** 2, rel=1e-3)
    side = m * (3 * r ** 2 + h ** 2) / 12.0
    for perp in np.eye(3):
        if abs(perp @ axis) < 1e-9:
            assert perp @ tensor_link @ perp == pytest.approx(side, rel=1e-3)


@pytest.mark.parametrize('wheel', ['left_wheel_link', 'right_wheel_link'])
def test_wheel_cylinder_aligned_with_axis(links, joints, wheel):
    joint = joints[wheel.replace('_link', '_joint')]
    axis = vec(joint.find('axis').get('xyz'))
    _, rot = origin_of(links[wheel].find('visual'))
    cyl_axis = rot @ np.array([0.0, 0.0, 1.0])
    assert abs(cyl_axis @ axis) == pytest.approx(1.0, abs=1e-6)


@pytest.mark.parametrize('wheel', ['left_wheel_link', 'right_wheel_link'])
def test_wheel_collision_touches_ground_in_mid_plane(links, wheel):
    """Collision sphere (radius = wheel radius, centred on the axle) gives a single
    contact point at the wheel mid-plane, so Gazebo's effective wheel separation equals
    the DiffDrive wheel_separation. A cylinder touches the plane at its rim edges."""
    sphere = links[wheel].find('collision/geometry/sphere')
    assert sphere is not None, 'wheel collision must be a sphere (see URDF comment)'
    xyz, _ = origin_of(links[wheel].find('collision'))
    assert np.allclose(xyz, 0.0)
    assert float(sphere.get('radius')) == pytest.approx(wheel_geometry(links[wheel])[0])


def gazebo_surface(robot, link):
    for g in robot.findall('gazebo'):
        if g.get('reference') == link:
            return {c.tag: float(c.text) for c in g}
    return {}


def test_contact_friction(robot):
    for caster in ('front_caster_link', 'rear_caster_link'):
        surf = gazebo_surface(robot, caster)
        assert surf.get('mu1') == 0.0 and surf.get('mu2') == 0.0, \
            f'{caster} must be frictionless, otherwise it scrubs and the robot under-rotates'
    for wheel in ('left_wheel_link', 'right_wheel_link'):
        surf = gazebo_surface(robot, wheel)
        assert surf.get('mu1', 0) >= 1.0 and surf.get('mu2', 0) >= 1.0, wheel


def test_wheels_and_casters_touch_ground(links, poses):
    for wheel in ('left_wheel_link', 'right_wheel_link'):
        radius, _ = wheel_geometry(links[wheel])
        assert poses[wheel][0][2] == pytest.approx(radius, abs=1e-6), wheel
    for caster in ('front_caster_link', 'rear_caster_link'):
        radius = float(links[caster].find('collision/geometry/sphere').get('radius'))
        assert poses[caster][0][2] == pytest.approx(radius, abs=1e-6), caster


def test_wheels_outside_chassis(links, poses):
    xyz, _ = origin_of(links['base_link'].find('collision'))
    half_width = vec(links['base_link'].find('collision/geometry/box').get('size'))[1] / 2
    for wheel in ('left_wheel_link', 'right_wheel_link'):
        _, length = wheel_geometry(links[wheel])
        inner_face = abs(poses[wheel][0][1]) - length / 2
        assert inner_face >= abs(xyz[1]) + half_width - 1e-9, wheel


def test_lidar_mounted_upright_on_roof(links, joints, poses):
    pos, rot = poses['lidar_link']
    # REP 103: x forward, z up -> no rotation relative to the robot body
    assert np.allclose(rot, np.eye(3), atol=1e-9)
    box_xyz, _ = origin_of(links['base_link'].find('collision'))
    size = vec(links['base_link'].find('collision/geometry/box').get('size'))
    base_z = poses['base_link'][0][2]
    roof_z = base_z + box_xyz[2] + size[2] / 2
    lidar_len = float(links['lidar_link'].find('collision/geometry/cylinder').get('length'))
    assert pos[2] - lidar_len / 2 >= roof_z - 1e-9, 'LiDAR is buried in the chassis'
    assert abs(pos[0]) <= size[0] / 2 and abs(pos[1]) <= size[1] / 2


def test_camera_optical_frame_rep103(joints):
    o = joints['camera_optical_joint'].find('origin')
    q = rpy_to_quaternion(*vec(o.get('rpy')))
    expected = np.array([-0.5, 0.5, -0.5, 0.5])
    assert np.allclose(q, expected, atol=1e-6) or np.allclose(q, -expected, atol=1e-6)
    rot = rpy_to_matrix(*vec(o.get('rpy')))
    # optical z (forward) == body x, optical x (right) == body -y, optical y (down) == body -z
    assert np.allclose(rot[:, 2], [1, 0, 0], atol=1e-9)
    assert np.allclose(rot[:, 0], [0, -1, 0], atol=1e-9)
    assert np.allclose(rot[:, 1], [0, 0, -1], atol=1e-9)


def test_inertia_calculator_matches_textbook():
    # Lab 7.3 payload tray and the wheel used in the model
    ixx, iyy, izz = inertia_calculator.box_inertia(1.2, 0.25, 0.18, 0.05)
    assert (round(ixx, 6), round(iyy, 6), round(izz, 6)) == (0.003490, 0.006500, 0.009490)
    assert inertia_calculator.cylinder_inertia(0.75, 0.08, 0.04, 'y') == pytest.approx(
        (0.0013, 0.0024, 0.0013))
    assert inertia_calculator.sphere_inertia(0.2, 0.03) == pytest.approx((7.2e-5,) * 3)
