#!/usr/bin/env python3
"""
Tutorial 04: Multi-Robot Fleet Launch System
Demonstrates namespacing two independent AMRs (amr_01 and amr_02)
with isolated TF trees, cmd_vel, and odom channels.
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import GroupAction
from launch_ros.actions import PushRosNamespace
import os


def generate_launch_description():
    pkg_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    root_dir = os.path.dirname(pkg_dir)
    urdf_path = os.path.join(root_dir, 'Essential_ROS', '02_Robot_Modeling_TF2', 'urdf', 'diff_drive_robot.urdf')

    with open(urdf_path, 'r') as f:
        robot_desc = f.read()

    # Robot 1: AMR Alpha
    robot1_group = GroupAction([
        PushRosNamespace('amr_01'),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{
                'robot_description': robot_desc,
                'frame_prefix': 'amr_01/'
            }],
            output='screen'
        )
    ])

    # Robot 2: AMR Beta
    robot2_group = GroupAction([
        PushRosNamespace('amr_02'),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{
                'robot_description': robot_desc,
                'frame_prefix': 'amr_02/'
            }],
            output='screen'
        )
    ])

    return LaunchDescription([
        robot1_group,
        robot2_group
    ])
