#!/usr/bin/env python3
"""
Lab 1.5: Modular Python Launch System
Launches the core communication subsystem: Publisher, Subscriber, Service Server, Action Server, and Parameter Node.
"""

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    robot_namespace_arg = DeclareLaunchArgument(
        'robot_ns',
        default_value='',
        description='Optional namespace for multi-robot isolation'
    )

    fleet_id_arg = DeclareLaunchArgument(
        'fleet_id',
        default_value='AMR_01',
        description='Robot identifier'
    )

    robot_ns = LaunchConfiguration('robot_ns')
    fleet_id = LaunchConfiguration('fleet_id')

    pkg_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    essential_dir = os.path.dirname(pkg_dir)

    # Resolve paths to nodes across the core communication weeks
    sensor_pub_path = os.path.join(essential_dir, 'Week_02_Nodes_Topics_QoS', 'src', 'sensor_qos_publisher.py')
    power_srv_path = os.path.join(essential_dir, 'Week_03_Services_Clients', 'src', 'power_service_server.py')
    action_srv_path = os.path.join(essential_dir, 'Week_04_Actions_Preemption', 'src', 'navigate_action_server.py')
    params_path = os.path.join(pkg_dir, 'src', 'fleet_parameters.py')

    # 1. Sensor QoS Publisher
    sensor_pub_node = ExecuteProcess(
        cmd=['python3', sensor_pub_path],
        name='sensor_qos_publisher',
        output='screen'
    )

    # 2. Power Service Server
    power_srv_node = ExecuteProcess(
        cmd=['python3', power_srv_path],
        name='power_service_server',
        output='screen'
    )

    # 3. Action Server
    action_srv_node = ExecuteProcess(
        cmd=['python3', action_srv_path],
        name='navigate_action_server',
        output='screen'
    )

    # 4. Fleet Parameters Node
    params_node = ExecuteProcess(
        cmd=['python3', params_path],
        name='fleet_parameters',
        output='screen'
    )

    return LaunchDescription([
        robot_namespace_arg,
        fleet_id_arg,
        sensor_pub_node,
        power_srv_node,
        action_srv_node,
        params_node
    ])
