#!/usr/bin/env python3
"""
Week 08 Midterm: reference solution for part 3 (hospital_bringup.launch.py)

  ros2 launch amr_week08 hospital_bringup.launch.py              # with RViz2
  ros2 launch amr_week08 hospital_bringup.launch.py rviz:=false  # headless (grader)
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = get_package_share_directory('amr_week08')
    # RViz config (RobotModel + TF, fixed frame base_footprint) reused from Week 07
    rviz_config = os.path.join(get_package_share_directory('amr_week07'),
                               'rviz', 'robot_model.rviz')

    model = LaunchConfiguration('model')
    robot_description = ParameterValue(Command(['cat ', model]), value_type=str)

    return LaunchDescription([
        DeclareLaunchArgument('model',
                              default_value=os.path.join(share, 'urdf', 'hospital_amr.urdf'),
                              description='Path to hospital_amr.urdf'),
        DeclareLaunchArgument('rviz', default_value='true',
                              description='Start RViz2 (false on headless machines)'),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             name='robot_state_publisher', output='screen',
             parameters=[{'robot_description': robot_description}]),
        # Publishes zero wheel angles so the continuous wheel joints appear in TF
        Node(package='joint_state_publisher', executable='joint_state_publisher',
             name='joint_state_publisher'),
        Node(package='amr_week08', executable='hospital_robot_node',
             name='midterm_robot_controller', output='screen'),
        Node(package='rviz2', executable='rviz2', name='rviz2', output='screen',
             arguments=['-d', rviz_config], condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
