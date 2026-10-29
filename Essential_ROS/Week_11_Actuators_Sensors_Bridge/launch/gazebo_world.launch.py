#!/usr/bin/env python3
"""
Week 11 Lab: Gazebo world + robot + ROS <-> Gazebo bridge.

  ros2 launch amr_week11 gazebo_world.launch.py                 # Gazebo GUI
  ros2 launch amr_week11 gazebo_world.launch.py headless:=true  # server only (Docker/CI)
  ros2 launch amr_week11 gazebo_world.launch.py estop:=true     # + safety gate (cmd_vel_in -> cmd_vel)

Started here:
  1. Gazebo Sim with the Week 10 warehouse world      (amr_week10)
  2. robot_state_publisher with the Week 07 URDF       (amr_week07, use_sim_time:=true)
     -> TF base_footprint -> base_link -> lidar_link / wheels / camera
  3. ros_gz_sim create: spawns the same URDF into Gazebo
  4. ros_gz_bridge: /cmd_vel, /odom, /scan, /tf (odom -> base_footprint), /joint_states, /clock
  5. (optional) emergency_stop_node safety gate
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    week07 = get_package_share_directory('amr_week07')
    week10 = get_package_share_directory('amr_week10')
    week11 = get_package_share_directory('amr_week11')

    default_urdf = os.path.join(week07, 'urdf', 'diff_drive_robot.urdf')
    urdf_path = LaunchConfiguration('model')
    bridge_config_path = os.path.join(week11, 'config', 'ros_gz_bridge.yaml')

    headless = LaunchConfiguration('headless')
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_sim_time_param = ParameterValue(use_sim_time, value_type=bool)

    args = [
        DeclareLaunchArgument('model', default_value=default_urdf,
                              description='Robot URDF (default: Week 07 diff_drive_robot.urdf)'),
        DeclareLaunchArgument('world', default_value=os.path.join(week10, 'worlds', 'warehouse.sdf'),
                              description='SDF world file'),
        DeclareLaunchArgument('headless', default_value='false',
                              description='true: gz sim -s -r --headless-rendering (no GUI)'),
        DeclareLaunchArgument('use_sim_time', default_value='true',
                              description='Use the Gazebo /clock in ROS nodes'),
        DeclareLaunchArgument('rviz', default_value='false', description='Start RViz2'),
        DeclareLaunchArgument('estop', default_value='false',
                              description='Start the emergency_stop_node gate (cmd_vel_in -> cmd_vel)'),
        DeclareLaunchArgument('x', default_value='0.0', description='Spawn x [m]'),
        DeclareLaunchArgument('y', default_value='0.0', description='Spawn y [m]'),
        DeclareLaunchArgument('yaw', default_value='0.0', description='Spawn yaw [rad]'),
    ]

    # 1. Gazebo Sim (GUI or headless server) with the Week 10 world
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(week10, 'launch', 'warehouse_world.launch.py')),
        launch_arguments={'world': LaunchConfiguration('world'), 'headless': headless}.items(),
    )

    # 2. robot_state_publisher (+ optional RViz) from Week 07; Gazebo provides /joint_states
    robot_state = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(week07, 'launch', 'display_urdf.launch.py')),
        launch_arguments={'model': urdf_path, 'use_jsp': 'false', 'use_gui': 'false',
                          'use_sim_time': use_sim_time,
                          'rviz': LaunchConfiguration('rviz')}.items(),
    )

    # 3. Spawn the robot into the running world
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-file', urdf_path, '-name', 'diff_drive_robot',
                   '-x', LaunchConfiguration('x'), '-y', LaunchConfiguration('y'),
                   '-z', '0.02', '-Y', LaunchConfiguration('yaw')],
        output='screen',
    )

    # 4. ros_gz_bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': bridge_config_path, 'use_sim_time': use_sim_time_param}],
        output='screen',
    )

    # 5. Optional safety gate: command sources must publish on /cmd_vel_in
    estop = Node(
        package='amr_week11',
        executable='emergency_stop_node',
        parameters=[{'use_sim_time': use_sim_time_param}],
        output='screen',
        condition=IfCondition(LaunchConfiguration('estop')),
    )

    return LaunchDescription(args + [gazebo, robot_state, spawn_robot, bridge, estop])
