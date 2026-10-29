"""Robot description (xacro) + controller YAML consistency checks for module 01."""
import math
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET

import pytest
import xacro
import yaml
from ament_index_python.packages import get_package_share_directory

SHARE = get_package_share_directory('amr_adv01')
XACRO = os.path.join(SHARE, 'urdf', 'diff_drive_ros2_control.xacro')
YAML = os.path.join(SHARE, 'config', 'diff_drive_controller.yaml')


def urdf(use_mock):
    return xacro.process_file(
        XACRO, mappings={'use_mock_hardware': 'true' if use_mock else 'false'}).toxml()


@pytest.fixture(scope='module')
def ddc():
    with open(YAML) as f:
        return yaml.safe_load(f)['diff_drive_controller']['ros__parameters']


def test_mock_hardware_selected_by_default():
    root = ET.fromstring(xacro.process_file(XACRO).toxml())
    hw = root.find('ros2_control/hardware')
    assert hw.findtext('plugin') == 'mock_components/GenericSystem'
    params = {p.get('name'): p.text for p in hw.findall('param')}
    assert params.get('calculate_dynamics') == 'true'
    assert root.find('gazebo/plugin') is None  # no gz_ros2_control plugin in mock mode


def test_gazebo_hardware_and_plugin():
    root = ET.fromstring(urdf(False))
    assert root.find('ros2_control/hardware').findtext('plugin') == 'gz_ros2_control/GazeboSimSystem'
    plugin = root.find('gazebo/plugin')
    assert plugin.get('filename') == 'gz_ros2_control-system'
    params_file = plugin.findtext('parameters')
    assert os.path.isfile(params_file), params_file  # no $(find my_robot_bringup) anymore


@pytest.mark.parametrize('use_mock', [True, False])
def test_complete_robot_with_wheel_joints(use_mock):
    root = ET.fromstring(urdf(use_mock))
    links = {link.get('name') for link in root.findall('link')}
    joints = {j.get('name'): j for j in root.findall('joint')}
    assert {'base_footprint', 'base_link', 'left_wheel_link', 'right_wheel_link'} <= links
    for name in ('left_wheel_joint', 'right_wheel_joint'):
        assert joints[name].get('type') == 'continuous'
    ctrl = {j.get('name') for j in root.findall('ros2_control/joint')}
    assert ctrl == {'left_wheel_joint', 'right_wheel_joint'}
    for j in root.findall('ros2_control/joint'):
        assert [c.get('name') for c in j.findall('command_interface')] == ['velocity']
        assert [s.get('name') for s in j.findall('state_interface')] == ['position', 'velocity']


@pytest.mark.skipif(shutil.which('check_urdf') is None, reason='check_urdf not installed')
def test_check_urdf(tmp_path):
    path = tmp_path / 'robot.urdf'
    path.write_text(urdf(True))
    out = subprocess.run(['check_urdf', str(path)], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert 'Successfully Parsed XML' in out.stdout


def test_geometry_matches_controller_yaml(ddc):
    root = ET.fromstring(urdf(True))
    joints = {j.get('name'): j for j in root.findall('joint')}
    y_left = float(joints['left_wheel_joint'].find('origin').get('xyz').split()[1])
    y_right = float(joints['right_wheel_joint'].find('origin').get('xyz').split()[1])
    assert y_left - y_right == pytest.approx(ddc['wheel_separation'])
    radius = float(root.find("link[@name='left_wheel_link']/collision/geometry/cylinder")
                   .get('radius'))
    assert radius == pytest.approx(ddc['wheel_radius'])
    assert ddc['left_wheel_names'] == ['left_wheel_joint']
    assert ddc['right_wheel_names'] == ['right_wheel_joint']


def test_body_limits_fit_wheel_command_limits(ddc):
    root = ET.fromstring(urdf(True))
    w_max = min(float(p.text) for p in root.findall("ros2_control/joint/command_interface/"
                                                    "param[@name='max']"))
    v_max = ddc['linear.x.max_velocity']
    om_max = ddc['angular.z.max_velocity']
    worst = (v_max + om_max * ddc['wheel_separation'] / 2.0) / ddc['wheel_radius']
    assert worst <= w_max + 1e-9, f'{worst:.2f} rad/s > {w_max} rad/s'
    assert math.isclose(worst, 9.25)


def test_no_removed_or_deprecated_parameters(ddc):
    assert 'use_stamped_vel' not in ddc  # removed in Jazzy: only TwistStamped is accepted
    assert not [k for k in ddc if k.endswith('_limits')]  # has_*_limits deprecated


def test_controller_manager_section():
    with open(YAML) as f:
        cm = yaml.safe_load(f)['controller_manager']['ros__parameters']
    assert cm['update_rate'] == 50
    assert cm['diff_drive_controller']['type'] == 'diff_drive_controller/DiffDriveController'
    assert cm['joint_state_broadcaster']['type'] == \
        'joint_state_broadcaster/JointStateBroadcaster'
