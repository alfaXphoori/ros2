#!/usr/bin/env python3
"""
Week 16: Final Demonstration one-command bringup.

  ros2 launch amr_week16 final_amr_system.launch.py                       # Gazebo GUI
  ros2 launch amr_week16 final_amr_system.launch.py headless:=true        # Docker / CI
  ros2 launch amr_week16 final_amr_system.launch.py rviz:=true            # + RViz2
  # then, in a second terminal:
  ros2 run amr_week16 final_mission_executor --ros-args -p use_sim_time:=true

Composition (everything with use_sim_time:=true):
  1. amr_week11 gazebo_world.launch.py : Gazebo world (amr_week10), robot_state_publisher
     (amr_week07 URDF, no joint_state_publisher: Gazebo publishes /joint_states),
     spawner and ros_gz_bridge
  2. amr_week14 nav2_bringup.launch.py : map_server (real Week 12 map) + AMCL + Nav2 servers,
     using the Week 15 patrol behavior tree
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    week11 = get_package_share_directory('amr_week11')
    week12 = get_package_share_directory('amr_week12')
    week14 = get_package_share_directory('amr_week14')
    week15 = get_package_share_directory('amr_week15')

    # 1. Simulation + robot model + bridge
    sim_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(week11, 'launch', 'gazebo_world.launch.py')),
        launch_arguments={'headless': LaunchConfiguration('headless'),
                          'rviz': LaunchConfiguration('rviz'),
                          'use_sim_time': 'true'}.items(),
    )

    # 2. Nav2 (localization + navigation)
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(week14, 'launch', 'nav2_bringup.launch.py')),
        launch_arguments={'map': LaunchConfiguration('map'),
                          'use_sim_time': 'true',
                          'nav_to_pose_bt_xml': LaunchConfiguration('bt_xml')}.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument('headless', default_value='false',
                              description='true: Gazebo server only, no GUI'),
        DeclareLaunchArgument('rviz', default_value='false', description='Start RViz2'),
        DeclareLaunchArgument('map', default_value=os.path.join(week12, 'maps', 'warehouse_map.yaml')),
        DeclareLaunchArgument('bt_xml', default_value=os.path.join(
            week15, 'behavior_trees', 'patrol_nav_to_pose.xml')),
        sim_bringup,
        nav2_bringup,
    ])
