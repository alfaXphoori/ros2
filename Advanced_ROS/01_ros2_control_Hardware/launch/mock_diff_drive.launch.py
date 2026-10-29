"""Advanced Module 01: ros2_control with mock hardware (headless, no simulator, no robot).

  ros2 launch amr_adv01 mock_diff_drive.launch.py

Starts robot_state_publisher (robot_description from the xacro with use_mock_hardware:=true),
ros2_control_node (controller_manager + mock_components/GenericSystem) and spawners for
joint_state_broadcaster and diff_drive_controller. Drive it with TwistStamped on
/diff_drive_controller/cmd_vel, e.g.
  ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true \
      -r cmd_vel:=/diff_drive_controller/cmd_vel
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = get_package_share_directory('amr_adv01')
    xacro_file = os.path.join(share, 'urdf', 'diff_drive_ros2_control.xacro')
    controllers = os.path.join(share, 'config', 'diff_drive_controller.yaml')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file, ' use_mock_hardware:=true']), value_type=str)

    rsp = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}], output='screen')

    # Jazzy: the controller_manager reads the URDF from the ~/robot_description topic
    control_node = Node(
        package='controller_manager', executable='ros2_control_node',
        parameters=[controllers],
        remappings=[('~/robot_description', '/robot_description')],
        output='screen')

    jsb_spawner = Node(
        package='controller_manager', executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager',
                   '--controller-manager-timeout', LaunchConfiguration('spawner_timeout')],
        output='screen')

    # start diff_drive_controller only after joint_state_broadcaster is active
    ddc_spawner = Node(
        package='controller_manager', executable='spawner',
        arguments=['diff_drive_controller', '--controller-manager', '/controller_manager',
                   '--controller-manager-timeout', LaunchConfiguration('spawner_timeout')],
        output='screen')

    return LaunchDescription([
        DeclareLaunchArgument('spawner_timeout', default_value='30',
                              description='seconds the spawners wait for controller_manager'),
        rsp,
        control_node,
        jsb_spawner,
        RegisterEventHandler(OnProcessExit(target_action=jsb_spawner, on_exit=[ddc_spawner])),
    ])
