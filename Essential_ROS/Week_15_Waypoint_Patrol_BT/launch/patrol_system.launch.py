#!/usr/bin/env python3
"""
Week 15: simulation + Nav2 with the custom patrol behavior tree.

  ros2 launch amr_week15 patrol_system.launch.py headless:=true
  ros2 run amr_week14 amcl_initial_pose --ros-args -p use_sim_time:=true
  ros2 run amr_week15 waypoint_patrol --ros-args -p use_sim_time:=true

The behavior tree behavior_trees/patrol_nav_to_pose.xml replaces Nav2's default
NavigateToPose tree via bt_navigator's default_nav_to_pose_bt_xml parameter.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    week11 = get_package_share_directory('amr_week11')
    week14 = get_package_share_directory('amr_week14')
    week15 = get_package_share_directory('amr_week15')

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(week11, 'launch', 'gazebo_world.launch.py')),
        launch_arguments={'headless': LaunchConfiguration('headless'),
                          'rviz': LaunchConfiguration('rviz')}.items(),
    )
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(week14, 'launch', 'nav2_bringup.launch.py')),
        launch_arguments={'nav_to_pose_bt_xml': LaunchConfiguration('bt_xml')}.items(),
    )
    return LaunchDescription([
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('rviz', default_value='false'),
        DeclareLaunchArgument(
            'bt_xml',
            default_value=os.path.join(week15, 'behavior_trees', 'patrol_nav_to_pose.xml'),
            description='NavigateToPose behavior tree'),
        sim,
        nav2,
    ])
