#!/usr/bin/env python3
"""
Week 11 Lab: Gazebo World Bringup with Bridge
Spawns the warehouse world, launches the robot model, and starts ros_gz_bridge.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    essential_dir = os.path.dirname(pkg_dir)

    world_path = os.path.join(essential_dir, 'Week_10_Gazebo_Sim_Harmonic', 'worlds', 'warehouse.sdf')
    bridge_config_path = os.path.join(pkg_dir, 'config', 'ros_gz_bridge.yaml')
    urdf_path = os.path.join(essential_dir, 'Week_07_URDF_Robot_Modeling', 'urdf', 'diff_drive_robot.urdf')

    # 1. Start Gazebo Sim
    gz_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                get_package_share_directory('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            ])
        ]),
        launch_arguments={'gz_args': f'-r {world_path}'}.items()
    )

    # 2. Spawn Robot from URDF
    spawn_robot_node = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-file', urdf_path,
            '-name', 'diff_drive_robot',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.1'
        ],
        output='screen'
    )

    # 3. ros_gz_bridge
    bridge_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': bridge_config_path}],
        output='screen'
    )

    return LaunchDescription([
        gz_sim_launch,
        spawn_robot_node,
        bridge_node
    ])
