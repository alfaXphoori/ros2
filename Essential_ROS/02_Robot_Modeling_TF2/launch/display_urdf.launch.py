#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    pkg_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    default_urdf_path = os.path.join(pkg_dir, 'urdf', 'diff_drive_robot.urdf')
    default_rviz_path = os.path.join(pkg_dir, 'rviz', 'robot_model.rviz')

    model_arg = DeclareLaunchArgument(
        name='model',
        default_value=default_urdf_path,
        description='Path to robot URDF file'
    )

    use_gui_arg = DeclareLaunchArgument(
        name='use_gui',
        default_value='true',
        description='Flag to enable joint_state_publisher_gui'
    )

    robot_description = ParameterValue(
        Command(['cat ', LaunchConfiguration('model')]),
        value_type=str
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description}]
    )

    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        condition=IfCondition(LaunchConfiguration('use_gui'))
    )

    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        condition=UnlessCondition(LaunchConfiguration('use_gui'))
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', default_rviz_path] if os.path.exists(default_rviz_path) else []
    )

    return LaunchDescription([
        model_arg,
        use_gui_arg,
        robot_state_publisher_node,
        joint_state_publisher_gui_node,
        joint_state_publisher_node,
        rviz_node
    ])
