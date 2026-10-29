#!/usr/bin/env python3
"""
Week 05 Lab: Modular Python Launch System
Starts the core communication subsystem of one robot: QoS publisher (Week 02), power service
(Week 03), navigation action server (Week 04) and the fleet parameter node (Week 05).

  ros2 launch amr_week05 core_system.launch.py robot_ns:=amr_01 fleet_id:=AMR_01
  ros2 launch amr_week05 core_system.launch.py params_file:=/path/to/my_fleet_config.yaml

Every node is pushed into the `robot_ns` namespace (empty = global), so two robots can be
started side by side without name clashes.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    robot_ns = LaunchConfiguration('robot_ns')
    fleet_id = LaunchConfiguration('fleet_id')
    params_file = LaunchConfiguration('params_file')

    declare_args = [
        DeclareLaunchArgument('robot_ns', default_value='',
                              description='Namespace for multi-robot isolation (empty = none)'),
        DeclareLaunchArgument('fleet_id', default_value='AMR_01',
                              description='Robot identifier passed to fleet_parameters'),
        DeclareLaunchArgument('params_file',
                              default_value=PathJoinSubstitution(
                                  [FindPackageShare('amr_week05'), 'config', 'fleet_params.yaml']),
                              description='YAML parameter file for fleet_parameters'),
    ]

    robot = GroupAction([
        PushRosNamespace(robot_ns),
        # 1. Sensor QoS Publisher (Week 02)
        Node(package='amr_week02', executable='sensor_qos_publisher', output='screen'),
        # 2. Power Service Server (Week 03)
        Node(package='amr_week03', executable='power_service_server', output='screen'),
        # 3. Navigation Action Server (Week 04)
        Node(package='amr_week04', executable='navigate_action_server', output='screen'),
        # 4. Fleet Parameters Node (Week 05): YAML file first, launch argument overrides it
        Node(package='amr_week05', executable='fleet_parameters', output='screen',
             parameters=[params_file, {'fleet_id': fleet_id}]),
    ])

    return LaunchDescription(declare_args + [robot])
