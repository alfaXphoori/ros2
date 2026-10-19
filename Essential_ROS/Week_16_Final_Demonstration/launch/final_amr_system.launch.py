#!/usr/bin/env python3
"""
Week 16: Final Demonstration Integrated Launch System
One-click bringup launching Gazebo Sim, Robot Spawner, Bridge,
Robot State Publisher, and full Nav2 Navigation Stack.
"""

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    pkg_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    essential_dir = os.path.dirname(pkg_dir)

    gazebo_launch = os.path.join(essential_dir, 'Week_11_Actuators_Sensors_Bridge', 'launch', 'gazebo_world.launch.py')
    display_urdf_launch = os.path.join(essential_dir, 'Week_07_URDF_Robot_Modeling', 'launch', 'display_urdf.launch.py')
    nav2_launch = os.path.join(essential_dir, 'Week_14_Path_Planning_AMCL', 'launch', 'nav2_bringup.launch.py')

    # 1. Gazebo Simulation World + Spawner + Bridge
    sim_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_launch)
    )

    # 2. Robot State Publisher (TF Tree from URDF)
    robot_state_pub = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(display_urdf_launch),
        launch_arguments={'use_gui': 'false'}.items()
    )

    # 3. Nav2 Navigation Stack (AMCL, Costmaps, Planners, Controllers)
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_launch)
    )

    return LaunchDescription([
        sim_bringup,
        robot_state_pub,
        nav2_bringup
    ])
