#!/usr/bin/env python3
"""
Week 12: one-command mapping session = Week 11 simulation + SLAM Toolbox
(+ optionally the scripted explorer that drives the robot around the warehouse).

  ros2 launch amr_week12 slam_mapping_sim.launch.py headless:=true explore:=true
  # when the explorer prints "Exploration finished", in another terminal:
  ros2 run nav2_map_server map_saver_cli -f warehouse_map --ros-args -p use_sim_time:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    week11 = get_package_share_directory('amr_week11')
    week12 = get_package_share_directory('amr_week12')

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(week11, 'launch', 'gazebo_world.launch.py')),
        launch_arguments={'headless': LaunchConfiguration('headless'),
                          'rviz': LaunchConfiguration('rviz')}.items(),
    )
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(week12, 'launch', 'online_async_slam.launch.py')),
        launch_arguments={'use_sim_time': 'true'}.items(),
    )
    explorer = TimerAction(period=10.0, actions=[Node(
        package='amr_week12',
        executable='explore_warehouse',
        parameters=[{'use_sim_time': True}],
        output='screen',
        condition=IfCondition(LaunchConfiguration('explore')),
    )])

    return LaunchDescription([
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('rviz', default_value='false'),
        DeclareLaunchArgument('explore', default_value='false',
                              description='Run the scripted exploration drive'),
        sim,
        slam,
        explorer,
    ])
