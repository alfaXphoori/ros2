"""Advanced Module 01: the same ros2_control robot in Gazebo Sim (gz_ros2_control).

  ros2 launch amr_adv01 gz_diff_drive.launch.py              # server only (headless)
  ros2 launch amr_adv01 gz_diff_drive.launch.py gui:=true    # with the Gazebo GUI

The robot_description is generated with use_mock_hardware:=false, so the hardware plugin is
gz_ros2_control/GazeboSimSystem and the gz_ros2_control system plugin inside Gazebo runs the
controller_manager (with config/diff_drive_controller.yaml). Command interface is the same as
the mock launch: TwistStamped on /diff_drive_controller/cmd_vel.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, EmitEvent, ExecuteProcess,
                            IncludeLaunchDescription, RegisterEventHandler)
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = get_package_share_directory('amr_adv01')
    xacro_file = os.path.join(share, 'urdf', 'diff_drive_ros2_control.xacro')
    gz_launch = os.path.join(get_package_share_directory('ros_gz_sim'), 'launch',
                             'gz_sim.launch.py')
    world = LaunchConfiguration('world')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file, ' use_mock_hardware:=false']), value_type=str)

    rsp = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
        output='screen')

    # server only; give it time to stop on SIGINT, otherwise the `gz` ruby wrapper is killed
    # and the forked gz-sim server (with its controller_manager) is left running
    gz_headless = ExecuteProcess(
        cmd=['gz', 'sim', '-s', '-r', '--headless-rendering', world],
        sigterm_timeout='20', sigkill_timeout='5', output='screen',
        on_exit=[EmitEvent(event=Shutdown(reason='gz sim exited'))],
        condition=UnlessCondition(LaunchConfiguration('gui')))
    gz_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_launch),
        launch_arguments={'gz_args': ['-r ', world], 'on_exit_shutdown': 'true'}.items(),
        condition=IfCondition(LaunchConfiguration('gui')))

    spawn = Node(
        package='ros_gz_sim', executable='create',
        arguments=['-topic', 'robot_description', '-name', 'amr', '-z', '0.02'],
        output='screen')

    clock_bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen')

    jsb_spawner = Node(
        package='controller_manager', executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager',
                   '--controller-manager-timeout', '60'],
        parameters=[{'use_sim_time': True}], output='screen')
    ddc_spawner = Node(
        package='controller_manager', executable='spawner',
        arguments=['diff_drive_controller', '--controller-manager', '/controller_manager',
                   '--controller-manager-timeout', '60'],
        parameters=[{'use_sim_time': True}], output='screen')

    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='false'),
        DeclareLaunchArgument('world', default_value='empty.sdf'),
        gz_headless,
        gz_gui,
        clock_bridge,
        rsp,
        spawn,
        RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=[jsb_spawner])),
        RegisterEventHandler(OnProcessExit(target_action=jsb_spawner, on_exit=[ddc_spawner])),
    ])
