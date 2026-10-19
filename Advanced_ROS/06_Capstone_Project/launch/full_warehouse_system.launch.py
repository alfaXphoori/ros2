#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    pkg_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    repo_root = os.path.dirname(pkg_dir)

    gazebo_launch_path = os.path.join(repo_root, 'Essential_ROS', '03_Gazebo_Simulation', 'launch', 'gazebo_world.launch.py')
    nav2_launch_path = os.path.join(repo_root, 'Essential_ROS', '05_Nav2_Navigation', 'launch', 'nav2_bringup.launch.py')
    display_urdf_path = os.path.join(repo_root, 'Essential_ROS', '02_Robot_Modeling_TF2', 'launch', 'display_urdf.launch.py')

    # 1. Gazebo Simulation + Spawner + Bridge
    gazebo_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_launch_path)
    )

    # 2. Robot State Publisher (TF from URDF)
    robot_state_pub = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(display_urdf_path),
        launch_arguments={'use_gui': 'false'}.items()
    )

    # 3. Nav2 Autonomous Navigation Stack
    nav2_stack = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_launch_path),
        launch_arguments={'autostart': 'true', 'use_sim_time': 'true'}.items()
    )

    return LaunchDescription([
        gazebo_sim,
        robot_state_pub,
        nav2_stack
    ])
