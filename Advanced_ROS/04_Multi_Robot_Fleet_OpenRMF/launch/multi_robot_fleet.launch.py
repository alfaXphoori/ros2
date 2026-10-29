#!/usr/bin/env python3
"""
Tutorial 04: Multi-Robot Fleet Launch System (headless, no simulator)

Starts N copies of the Week 07 AMR (default: amr_01, amr_02). Per robot, inside
a GroupAction with PushRosNamespace('<robot>'):

  robot_state_publisher  frame_prefix '<robot>/'  -> <robot>/base_link, <robot>/left_wheel_link ...
  fake_diff_drive        /<robot>/cmd_vel -> /<robot>/odom, /<robot>/joint_states,
                         TF <robot>/odom -> <robot>/base_footprint
  static_transform_publisher  map -> <robot>/odom  (start pose of the robot)

What is isolated and what is shared:
  * relative topics (cmd_vel, odom, joint_states, robot_description) and node
    names are namespaced: /amr_01/..., /amr_02/...
  * /tf and /tf_static are absolute topic names and stay SHARED by all robots;
    frame_prefix keeps the frame names unique, so one TF tree holds every robot:
        map -> amr_01/odom -> amr_01/base_footprint -> amr_01/base_link -> ...
        map -> amr_02/odom -> amr_02/base_footprint -> amr_02/base_link -> ...
    (The alternative used by Nav2 multi-robot bringup - remapping /tf -> tf so
     each robot has its own /amr_0X/tf - is explained in the README.)

  ros2 launch amr_adv04 multi_robot_fleet.launch.py
  ros2 launch amr_adv04 multi_robot_fleet.launch.py robots:=amr_01,amr_02,amr_03
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace

# Start poses in the map frame. amr_01/amr_02 start on their chargers of
# config/nav_graph.yaml; further robots are lined up along +y.
START_POSES = {
    'amr_01': (0.0, 0.0),
    'amr_02': (0.0, 1.5),
}
ROBOT_SPACING = 1.5


def robot_group(name, index, robot_desc):
    x, y = START_POSES.get(name, (0.0, ROBOT_SPACING * index))
    prefix = name + '/'
    return GroupAction([
        PushRosNamespace(name),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{
                'robot_description': robot_desc,
                'frame_prefix': prefix,   # base_link -> amr_01/base_link
            }],
            output='screen',
        ),
        Node(
            package='amr_adv04',
            executable='fake_diff_drive',
            name='fake_diff_drive',
            parameters=[{'frame_prefix': prefix}],
            output='screen',
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='map_to_odom',
            arguments=['--x', str(x), '--y', str(y),
                       '--frame-id', 'map', '--child-frame-id', prefix + 'odom'],
            output='screen',
        ),
    ])


def launch_setup(context, *args, **kwargs):
    urdf_path = LaunchConfiguration('model').perform(context)
    with open(urdf_path, 'r') as f:
        robot_desc = f.read()
    robots = [r.strip() for r in LaunchConfiguration('robots').perform(context).split(',')
              if r.strip()]
    if len(set(robots)) != len(robots):
        raise RuntimeError(f'duplicate robot names in robots:={robots}')
    return [robot_group(name, i, robot_desc) for i, name in enumerate(robots)]


def generate_launch_description():
    default_urdf = os.path.join(get_package_share_directory('amr_week07'),
                                'urdf', 'diff_drive_robot.urdf')
    return LaunchDescription([
        DeclareLaunchArgument('robots', default_value='amr_01,amr_02',
                              description='Comma-separated robot names (= namespaces)'),
        DeclareLaunchArgument('model', default_value=default_urdf,
                              description='URDF used for every robot'),
        OpaqueFunction(function=launch_setup),
    ])
