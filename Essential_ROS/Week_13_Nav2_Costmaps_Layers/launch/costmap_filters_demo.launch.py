#!/usr/bin/env python3
"""
Costmap Filters Demo (Keep-out Zone + Speed Restricted Zone) on the Week 12 map.

  ros2 launch amr_week13 costmap_filters_demo.launch.py

Starts:
  * map_server -> /map
  * keepout_filter_mask_server -> /keepout_filter_mask
  * keepout_costmap_filter_info_server -> /costmap_filter_info (type 0: keepout)
  * speed_filter_mask_server -> /speed_filter_mask
  * speed_costmap_filter_info_server -> /speed_filter_info (type 1: % speed limit)
  * static TF map -> odom -> base_footprint (default at origin, inside speed zone)
  * global_costmap with KeepoutFilter + SpeedFilter -> /global_costmap/costmap, /speed_limit
  * nav2_lifecycle_manager activating all 6 lifecycle nodes
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    week12 = get_package_share_directory('amr_week12')
    week13 = get_package_share_directory('amr_week13')
    params = LaunchConfiguration('params_file')

    map_server = Node(
        package='nav2_map_server', executable='map_server', name='map_server',
        parameters=[params, {'yaml_filename': LaunchConfiguration('map')}],
        output='screen',
    )
    keepout_mask_server = Node(
        package='nav2_map_server', executable='map_server',
        name='keepout_filter_mask_server',
        parameters=[params, {'yaml_filename': LaunchConfiguration('keepout_mask')}],
        output='screen',
    )
    keepout_info_server = Node(
        package='nav2_map_server', executable='costmap_filter_info_server',
        name='keepout_costmap_filter_info_server',
        parameters=[params],
        output='screen',
    )
    speed_mask_server = Node(
        package='nav2_map_server', executable='map_server',
        name='speed_filter_mask_server',
        parameters=[params, {'yaml_filename': LaunchConfiguration('speed_mask')}],
        output='screen',
    )
    speed_info_server = Node(
        package='nav2_map_server', executable='costmap_filter_info_server',
        name='speed_costmap_filter_info_server',
        parameters=[params],
        output='screen',
    )
    map_to_odom = Node(
        package='tf2_ros', executable='static_transform_publisher', name='map_to_odom',
        arguments=['--frame-id', 'map', '--child-frame-id', 'odom'],
    )
    odom_to_base = Node(
        package='tf2_ros', executable='static_transform_publisher', name='odom_to_base',
        arguments=['--frame-id', 'odom', '--child-frame-id', 'base_footprint'],
    )
    global_costmap = Node(
        package='nav2_costmap_2d', executable='nav2_costmap_2d',
        name='global_costmap', namespace='global_costmap',
        parameters=[params], output='screen',
    )
    lifecycle = Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_costmap_filters', output='screen',
        parameters=[{
            'use_sim_time': False,
            'autostart': True,
            'bond_timeout': 0.0,
            'node_names': [
                'map_server',
                'keepout_filter_mask_server',
                'keepout_costmap_filter_info_server',
                'speed_filter_mask_server',
                'speed_costmap_filter_info_server',
                'global_costmap/global_costmap',
            ],
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value=os.path.join(week12, 'maps', 'warehouse_map.yaml'),
        ),
        DeclareLaunchArgument(
            'keepout_mask',
            default_value=os.path.join(week13, 'maps', 'keepout_mask.yaml'),
        ),
        DeclareLaunchArgument(
            'speed_mask',
            default_value=os.path.join(week13, 'maps', 'speed_mask.yaml'),
        ),
        DeclareLaunchArgument(
            'params_file',
            default_value=os.path.join(week13, 'config', 'costmap_filters_params.yaml'),
        ),
        map_server,
        keepout_mask_server,
        keepout_info_server,
        speed_mask_server,
        speed_info_server,
        map_to_odom,
        odom_to_base,
        global_costmap,
        lifecycle,
    ])
