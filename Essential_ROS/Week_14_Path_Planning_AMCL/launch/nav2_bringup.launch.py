#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    root_dir = os.path.dirname(pkg_dir)

    default_map = os.path.join(root_dir, 'Week_12_SLAM_Mapping_Ceres', 'maps', 'warehouse_map.yaml')
    default_params = os.path.join(pkg_dir, 'config', 'nav2_params.yaml')

    map_arg = DeclareLaunchArgument('map', default_value=default_map, description='Full path to map yaml file')
    params_arg = DeclareLaunchArgument('params_file', default_value=default_params, description='Nav2 params file')
    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='true', description='Use simulation time')

    lifecycle_nodes = [
        'map_server',
        'amcl',
        'controller_server',
        'planner_server',
        'bt_navigator'
    ]

    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[LaunchConfiguration('params_file'), {'yaml_filename': LaunchConfiguration('map'), 'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    amcl_node = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[LaunchConfiguration('params_file'), {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    controller_node = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[LaunchConfiguration('params_file'), {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    planner_node = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[LaunchConfiguration('params_file'), {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    bt_navigator_node = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[LaunchConfiguration('params_file'), {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    lifecycle_manager_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
            {'autostart': True},
            {'node_names': lifecycle_nodes}
        ]
    )

    return LaunchDescription([
        map_arg,
        params_arg,
        use_sim_time_arg,
        map_server_node,
        amcl_node,
        controller_node,
        planner_node,
        bt_navigator_node,
        lifecycle_manager_node
    ])
