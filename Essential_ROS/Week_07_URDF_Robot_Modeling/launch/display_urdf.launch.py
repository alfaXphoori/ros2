#!/usr/bin/env python3
"""
Week 07: Display the course AMR URDF in RViz2.

  ros2 launch amr_week07 display_urdf.launch.py                 # RViz2 + slider GUI
  ros2 launch amr_week07 display_urdf.launch.py use_gui:=false rviz:=false   # headless
  ros2 launch amr_week07 display_urdf.launch.py use_jsp:=false use_sim_time:=true
      # in Gazebo: /joint_states comes from the simulator, not joint_state_publisher

Later weeks include this file via get_package_share_directory('amr_week07').
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = get_package_share_directory('amr_week07')
    default_urdf_path = os.path.join(pkg_share, 'urdf', 'diff_drive_robot.urdf')
    default_rviz_path = os.path.join(pkg_share, 'rviz', 'robot_model.rviz')

    model = LaunchConfiguration('model')
    use_gui = LaunchConfiguration('use_gui')
    use_jsp = LaunchConfiguration('use_jsp')
    use_sim_time = LaunchConfiguration('use_sim_time')
    rviz = LaunchConfiguration('rviz')
    use_sim_time_param = ParameterValue(use_sim_time, value_type=bool)

    declared_args = [
        DeclareLaunchArgument('model', default_value=default_urdf_path,
                              description='Absolute path to the robot URDF file'),
        DeclareLaunchArgument('use_gui', default_value='true',
                              description='true: joint_state_publisher_gui (sliders), '
                                          'false: plain joint_state_publisher'),
        DeclareLaunchArgument('use_jsp', default_value='true',
                              description='Start a joint state publisher at all '
                                          '(set false when Gazebo publishes /joint_states)'),
        DeclareLaunchArgument('use_sim_time', default_value='false',
                              description='Use /clock from the simulator'),
        DeclareLaunchArgument('rviz', default_value='true',
                              description='Start RViz2 (set false on headless machines)'),
        DeclareLaunchArgument('rviz_config', default_value=default_rviz_path,
                              description='RViz2 config file'),
    ]

    robot_description = ParameterValue(Command(['cat ', model]), value_type=str)

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description,
                     'use_sim_time': use_sim_time_param}],
    )

    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        parameters=[{'use_sim_time': use_sim_time_param}],
        condition=IfCondition(PythonExpression(
            ["'", use_jsp, "' == 'true' and '", use_gui, "' == 'true'"])),
    )

    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters=[{'use_sim_time': use_sim_time_param}],
        condition=IfCondition(PythonExpression(
            ["'", use_jsp, "' == 'true' and '", use_gui, "' != 'true'"])),
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', LaunchConfiguration('rviz_config')],
        parameters=[{'use_sim_time': use_sim_time_param}],
        condition=IfCondition(rviz),
    )

    return LaunchDescription(declared_args + [
        robot_state_publisher_node,
        joint_state_publisher_gui_node,
        joint_state_publisher_node,
        rviz_node,
    ])
