#!/usr/bin/env python3
"""
Week 14: Nav2 bringup (localization + navigation) for the course AMR.

  # terminal 1: simulation (Week 11)
  ros2 launch amr_week11 gazebo_world.launch.py headless:=true
  # terminal 2: Nav2 on the real Week 12 map
  ros2 launch amr_week14 nav2_bringup.launch.py
  # terminal 3: tell AMCL where the robot is
  ros2 run amr_week14 amcl_initial_pose --ros-args -p use_sim_time:=true

Nodes (all lifecycle nodes, configured + activated by two lifecycle managers):
  localization : map_server, amcl
  navigation   : controller_server, smoother_server, planner_server, behavior_server,
                 velocity_smoother, collision_monitor, bt_navigator, waypoint_follower
behavior_server (Spin/BackUp/Wait) is required by the default behavior tree,
waypoint_follower provides /follow_waypoints (Week 15).
If a lifecycle manager hangs (node left unconfigured/inactive, see nav2_lifecycle_guard.py):
  ros2 run amr_week14 nav2_lifecycle_guard --ros-args -p use_sim_time:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from amr_week14.nav2_lifecycle_guard import LOCALIZATION_NODES, NAVIGATION_NODES
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    week12 = get_package_share_directory('amr_week12')
    week14 = get_package_share_directory('amr_week14')
    default_bt = os.path.join(get_package_share_directory('nav2_bt_navigator'), 'behavior_trees',
                              'navigate_to_pose_w_replanning_and_recovery.xml')

    params = LaunchConfiguration('params_file')
    use_sim_time = ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool)
    autostart = ParameterValue(LaunchConfiguration('autostart'), value_type=bool)
    log_level = LaunchConfiguration('log_level')
    common = [params, {'use_sim_time': use_sim_time}]
    # controller/behavior servers publish on cmd_vel_nav -> velocity_smoother ->
    # cmd_vel_smoothed -> collision_monitor -> cmd_vel
    nav_cmd = [('cmd_vel', 'cmd_vel_nav')]

    def nav2_node(package, executable, name=None, extra_params=(), remappings=()):
        return Node(package=package, executable=executable, name=name or executable,
                    output='screen', parameters=common + list(extra_params),
                    remappings=list(remappings), arguments=['--ros-args', '--log-level', log_level])

    localization = [
        nav2_node('nav2_map_server', 'map_server',
                  extra_params=[{'yaml_filename': LaunchConfiguration('map')}]),
        nav2_node('nav2_amcl', 'amcl'),
        Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
             name='lifecycle_manager_localization', output='screen',
             parameters=[{'use_sim_time': use_sim_time, 'autostart': autostart,
                          'node_names': LOCALIZATION_NODES}]),
    ]

    navigation_names = NAVIGATION_NODES
    navigation = [
        nav2_node('nav2_controller', 'controller_server', remappings=nav_cmd),
        nav2_node('nav2_smoother', 'smoother_server'),
        nav2_node('nav2_planner', 'planner_server'),
        nav2_node('nav2_behaviors', 'behavior_server', remappings=nav_cmd),
        nav2_node('nav2_velocity_smoother', 'velocity_smoother',
                  remappings=[('cmd_vel', 'cmd_vel_nav')]),
        nav2_node('nav2_collision_monitor', 'collision_monitor'),
        nav2_node('nav2_bt_navigator', 'bt_navigator',
                  extra_params=[{'default_nav_to_pose_bt_xml':
                                 LaunchConfiguration('nav_to_pose_bt_xml')}]),
        nav2_node('nav2_waypoint_follower', 'waypoint_follower'),
        Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
             name='lifecycle_manager_navigation', output='screen',
             parameters=[{'use_sim_time': use_sim_time, 'autostart': autostart,
                          'node_names': navigation_names}]),
    ]

    return LaunchDescription([
        SetEnvironmentVariable('RCUTILS_LOGGING_BUFFERED_STREAM', '1'),
        DeclareLaunchArgument('map', default_value=os.path.join(week12, 'maps', 'warehouse_map.yaml'),
                              description='Map yaml (default: real Week 12 SLAM map)'),
        DeclareLaunchArgument('params_file',
                              default_value=os.path.join(week14, 'config', 'nav2_params.yaml')),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('autostart', default_value='true'),
        DeclareLaunchArgument('log_level', default_value='info'),
        DeclareLaunchArgument('nav_to_pose_bt_xml', default_value=default_bt,
                              description='Behavior tree for NavigateToPose'),
    ] + localization + navigation)
