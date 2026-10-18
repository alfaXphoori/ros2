#!/usr/bin/env python3
"""
Launch file to visualize Differential Drive Robot URDF in RViz2.
Runs:
  1. robot_state_publisher (publishes 3D transforms based on URDF and joint states)
  2. joint_state_publisher_gui (interactive GUI slider to move robot joints)
  3. rviz2 (3D robot visualization)
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # Locate files relative to this launch script
    pkg_share_dir = os.path.dirname(os.path.realpath(__file__))
    default_urdf_path = os.path.join(pkg_share_dir, 'diff_drive_robot.urdf')
    default_rviz_path = os.path.join(pkg_share_dir, 'diff_drive.rviz')

    # Launch configuration variables
    model_arg = DeclareLaunchArgument(
        name='model',
        default_value=default_urdf_path,
        description='Absolute path to robot URDF file'
    )

    use_gui_arg = DeclareLaunchArgument(
        name='use_gui',
        default_value='true',
        description='Flag to enable joint_state_publisher_gui slider tool'
    )

    rviz_config_arg = DeclareLaunchArgument(
        name='rviz_config',
        default_value=default_rviz_path,
        description='Absolute path to RViz configuration file'
    )

    # Read robot URDF content dynamically
    robot_description = ParameterValue(
        Command(['cat ', LaunchConfiguration('model')]),
        value_type=str
    )

    # 1. robot_state_publisher node
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description}]
    )

    # 2a. joint_state_publisher with GUI (for interactive joint manipulation)
    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        condition=IfCondition(LaunchConfiguration('use_gui'))
    )

    # 2b. standard joint_state_publisher (headless, non-GUI)
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        condition=UnlessCondition(LaunchConfiguration('use_gui'))
    )

    # 3. RViz2 visualization node
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', LaunchConfiguration('rviz_config')]
    )

    return LaunchDescription([
        model_arg,
        use_gui_arg,
        rviz_config_arg,
        robot_state_publisher_node,
        joint_state_publisher_gui_node,
        joint_state_publisher_node,
        rviz_node
    ])
