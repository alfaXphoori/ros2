#!/usr/bin/env python3
"""
Lab 1.5: Modular Python Launch System
Launches the core communication subsystem: Publisher, Subscriber, Service Server, Action Server, and Parameter Node.
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
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
    src_dir = os.path.join(pkg_dir, 'src')

    # 1. Sensor QoS Publisher
    sensor_pub_node = Node(
        executable=os.path.join(src_dir, 'sensor_qos_publisher.py'),
        name='sensor_qos_publisher',
        namespace=robot_ns,
        output='screen'
    )

    # 2. Power Service Server
    power_srv_node = Node(
        executable=os.path.join(src_dir, 'power_service_server.py'),
        name='power_service_server',
        namespace=robot_ns,
        output='screen'
    )

    # 3. Action Server
    action_srv_node = Node(
        executable=os.path.join(src_dir, 'navigate_action_server.py'),
        name='navigate_action_server',
        namespace=robot_ns,
        output='screen'
    )

    # 4. Fleet Parameters Node
    params_node = Node(
        executable=os.path.join(src_dir, 'fleet_parameters.py'),
        name='fleet_parameters',
        namespace=robot_ns,
        parameters=[{
            'fleet_id': fleet_id,
            'max_linear_speed': 1.0,
            'safety_margin': 0.4
        }],
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
