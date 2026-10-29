#!/usr/bin/env python3
"""
Week 09: TF2 lab with exactly ONE source for the sensor frames.

  ros2 launch amr_week09 tf_lab.launch.py                       # static_sensor_broadcaster
  ros2 launch amr_week09 tf_lab.launch.py tf_source:=urdf       # robot_state_publisher (Week 07 URDF)

Both modes also start tf_obstacle_listener, which prints the obstacle point in base_link.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    tf_source = LaunchConfiguration('tf_source')
    display_launch = os.path.join(get_package_share_directory('amr_week07'),
                                  'launch', 'display_urdf.launch.py')

    return LaunchDescription([
        DeclareLaunchArgument('tf_source', default_value='broadcaster',
                              choices=['broadcaster', 'urdf'],
                              description='Who publishes base_link->lidar/camera frames'),
        Node(package='amr_week09', executable='static_sensor_broadcaster',
             name='static_sensor_broadcaster', output='screen',
             condition=IfCondition(PythonExpression(["'", tf_source, "' == 'broadcaster'"]))),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(display_launch),
            launch_arguments={'use_gui': 'false', 'rviz': 'false'}.items(),
            condition=IfCondition(PythonExpression(["'", tf_source, "' == 'urdf'"]))),
        Node(package='amr_week09', executable='tf_obstacle_listener',
             name='tf_obstacle_listener', output='screen'),
    ])
