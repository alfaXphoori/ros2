#!/usr/bin/env python3
"""
Week 12: SLAM Toolbox online asynchronous mapping.

  ros2 launch amr_week12 online_async_slam.launch.py
  ros2 launch amr_week12 online_async_slam.launch.py slam_params_file:=/path/to/my.yaml

slam_toolbox 2.8 (Jazzy) is a *lifecycle* node: started as a plain Node it stays
`unconfigured` and never publishes /map. We therefore reuse slam_toolbox's own
online_async_launch.py, which starts it as a LifecycleNode and emits the
configure -> activate transitions (autostart:=true).
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    default_params = os.path.join(
        get_package_share_directory('amr_week12'), 'config', 'slam_toolbox_params.yaml')
    slam_launch = os.path.join(
        get_package_share_directory('slam_toolbox'), 'launch', 'online_async_launch.py')

    return LaunchDescription([
        DeclareLaunchArgument('slam_params_file', default_value=default_params,
                              description='SLAM Toolbox parameter file (top key: slam_toolbox)'),
        DeclareLaunchArgument('use_sim_time', default_value='true',
                              description='Use the Gazebo /clock'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(slam_launch),
            launch_arguments={
                'slam_params_file': LaunchConfiguration('slam_params_file'),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'autostart': 'true',
            }.items(),
        ),
    ])
