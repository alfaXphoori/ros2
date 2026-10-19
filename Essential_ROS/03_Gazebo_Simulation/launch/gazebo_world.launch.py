#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    root_dir = os.path.dirname(pkg_dir)
    
    world_path = os.path.join(pkg_dir, 'worlds', 'warehouse.sdf')
    bridge_config_path = os.path.join(pkg_dir, 'config', 'ros_gz_bridge.yaml')
    urdf_path = os.path.join(root_dir, '02_Robot_Modeling_TF2', 'urdf', 'diff_drive_robot.urdf')

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
        output='screen',
        arguments=[
            '-name', 'diff_drive_robot',
            '-file', urdf_path,
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.1'
        ]
    )

    # 3. ros_gz_bridge node
    bridge_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        arguments=[
            '--ros-args',
            '-p', f'config_file:={bridge_config_path}'
        ]
    )

    return LaunchDescription([
        gz_sim_launch,
        spawn_robot_node,
        bridge_node
    ])
