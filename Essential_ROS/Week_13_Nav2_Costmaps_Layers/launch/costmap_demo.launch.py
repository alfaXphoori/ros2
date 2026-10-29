#!/usr/bin/env python3
"""
Week 13 Lab: Global + Local Costmap 2D on the real SLAM map, without the rest of Nav2.

  ros2 launch amr_week13 costmap_demo.launch.py headless:=true
  ros2 launch amr_week13 costmap_demo.launch.py rviz:=true        # with Gazebo GUI + RViz2

Started here:
  * Week 11 simulation (Gazebo + robot_state_publisher + bridge)
  * nav2_map_server with the Week 12 map               -> /map
  * static TF map -> odom (identity: the robot spawns at the map origin; Week 14
    replaces this with AMCL, which estimates map -> odom from the LiDAR)
  * two standalone nav2_costmap_2d nodes using config/costmap_params.yaml
      /global_costmap/global_costmap -> /global_costmap/costmap (+ costmap_raw)
      /local_costmap/local_costmap   -> /local_costmap/costmap  (+ costmap_raw)
  * nav2_lifecycle_manager that configures + activates the three lifecycle nodes
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    week11 = get_package_share_directory('amr_week11')
    week12 = get_package_share_directory('amr_week12')
    week13 = get_package_share_directory('amr_week13')
    params = LaunchConfiguration('params_file')

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(week11, 'launch', 'gazebo_world.launch.py')),
        launch_arguments={'headless': LaunchConfiguration('headless'),
                          'rviz': LaunchConfiguration('rviz')}.items(),
    )
    map_server = Node(
        package='nav2_map_server', executable='map_server', name='map_server',
        parameters=[params, {'yaml_filename': LaunchConfiguration('map'), 'use_sim_time': True}],
        output='screen',
    )
    map_to_odom = Node(
        package='tf2_ros', executable='static_transform_publisher', name='map_to_odom',
        arguments=['--frame-id', 'map', '--child-frame-id', 'odom'],
        parameters=[{'use_sim_time': True}],
    )
    global_costmap = Node(
        package='nav2_costmap_2d', executable='nav2_costmap_2d',
        name='global_costmap', namespace='global_costmap',
        parameters=[params], output='screen',
    )
    local_costmap = Node(
        package='nav2_costmap_2d', executable='nav2_costmap_2d',
        name='local_costmap', namespace='local_costmap',
        parameters=[params], output='screen',
    )
    lifecycle = Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_costmap', output='screen',
        # bond_timeout 0: a standalone costmap node does not open a bond connection
        # (inside Nav2 it lives in planner_server / controller_server, which do)
        parameters=[{'use_sim_time': True, 'autostart': True, 'bond_timeout': 0.0,
                     'node_names': ['map_server', 'global_costmap/global_costmap',
                                    'local_costmap/local_costmap']}],
    )

    return LaunchDescription([
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('rviz', default_value='false'),
        DeclareLaunchArgument('map', default_value=os.path.join(week12, 'maps', 'warehouse_map.yaml'),
                              description='Map yaml (default: real Week 12 SLAM map)'),
        DeclareLaunchArgument('params_file',
                              default_value=os.path.join(week13, 'config', 'costmap_params.yaml')),
        sim, map_server, map_to_odom, global_costmap, local_costmap, lifecycle,
    ])
