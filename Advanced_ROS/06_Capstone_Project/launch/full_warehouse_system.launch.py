#!/usr/bin/env python3
"""
Advanced Module 06 (Capstone): the integrated warehouse AMR system, one command.

  ros2 launch amr_adv06 full_warehouse_system.launch.py headless:=true   # Docker / CI
  ros2 launch amr_adv06 full_warehouse_system.launch.py                  # Gazebo GUI
  ros2 launch amr_adv06 full_warehouse_system.launch.py rviz:=true       # + RViz2
  # second terminal: the mission (pick -> drop -> dock -> undock -> e-stop test -> home)
  ros2 run amr_adv06 capstone_mission --ros-args -p use_sim_time:=true

Composition (all nodes use_sim_time:=true, Gazebo /clock):
  1. amr_week11 gazebo_world.launch.py : Gazebo Sim (Week 10 warehouse), robot_state_publisher
     (Week 07 URDF), spawn, ros_gz_bridge (/cmd_vel /odom /scan /tf /joint_states /clock)
  2. amr_week14 nav2_bringup.launch.py : map_server (real Week 12 SLAM map) + AMCL + Nav2
     (controller, planner, smoother, behavior server, velocity_smoother, collision_monitor,
     bt_navigator with the Week 15 behavior tree, waypoint_follower), params = Week 14 file
     deep-merged with config/nav2_overrides.yaml (collision_monitor StopZone)
  3. ground_truth_tf (this package)   : Gazebo true pose -> /ground_truth/pose + TF
     base_footprint -> sim_world
  4. amr_adv02 synthetic_tag_camera (mode tf) renders the charger AprilTag from the TRUE robot
     pose -> /camera/image_raw, amr_adv02 apriltag_dock_tracker -> /detected_dock_pose
  5. opennav_docking docking_server with the amr_adv03 parameters + config/docking_overrides.yaml
     (use_sim_time, slower final approach) + the capstone dock pose, and its own lifecycle
     manager; cmd_vel -> cmd_vel_nav so docking motions also pass the velocity smoother and
     the collision monitor

Velocity chain: controller/behavior/docking -> cmd_vel_nav -> velocity_smoother
  -> cmd_vel_smoothed -> collision_monitor (StopZone + FootprintApproach) -> cmd_vel -> Gazebo
"""

import os
import tempfile

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from amr_adv06.capstone_config import dock_pose, load_mission, merge_yaml_files, tag_world


def launch_setup(context):
    week11 = get_package_share_directory('amr_week11')
    week14 = get_package_share_directory('amr_week14')
    adv03 = get_package_share_directory('amr_adv03')
    adv06 = get_package_share_directory('amr_adv06')
    mission = load_mission(LaunchConfiguration('mission').perform(context))
    dock = mission['dock']
    sim = {'use_sim_time': True}

    # Week 14 Nav2 params + capstone overrides -> one temporary params file
    merged = os.path.join(tempfile.mkdtemp(prefix='amr_adv06_'), 'nav2_params_capstone.yaml')
    merge_yaml_files(os.path.join(week14, 'config', 'nav2_params.yaml'),
                     os.path.join(adv06, 'config', 'nav2_overrides.yaml'), merged)

    sim_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(week11, 'launch', 'gazebo_world.launch.py')),
        launch_arguments={'headless': LaunchConfiguration('headless'),
                          'rviz': LaunchConfiguration('rviz'),
                          'use_sim_time': 'true'}.items(),
    )
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(week14, 'launch', 'nav2_bringup.launch.py')),
        launch_arguments={'map': LaunchConfiguration('map'),
                          'params_file': merged,
                          'use_sim_time': 'true',
                          'nav_to_pose_bt_xml': LaunchConfiguration('bt_xml')}.items(),
    )

    ground_truth = Node(package='amr_adv06', executable='ground_truth_tf', output='screen',
                        parameters=[sim])

    tag_camera = Node(
        package='amr_adv02', executable='synthetic_tag_camera', output='screen',
        parameters=[sim, {'mode': 'tf', 'world_frame': 'sim_world', 'tag_world': tag_world(dock),
                          'tag_id': int(dock['tag_id']), 'tag_size': float(dock['tag_size']),
                          'frame_id': 'camera_optical_link', 'draw_objects': False,
                          'rate': 15.0}])
    tag_tracker = Node(
        package='amr_adv02', executable='apriltag_dock_tracker', output='screen',
        parameters=[sim, {'tag_id': int(dock['tag_id']), 'tag_size': float(dock['tag_size'])}])

    dx, dy, dyaw = dock_pose(dock)
    docking_server = Node(
        package='opennav_docking', executable='opennav_docking', name='docking_server',
        output='screen',
        parameters=[os.path.join(adv03, 'config', 'docking_server_params.yaml'),
                    os.path.join(adv06, 'config', 'docking_overrides.yaml'),
                    {'docks': [dock['id']],
                     f"{dock['id']}.type": dock['type'],
                     f"{dock['id']}.frame": 'map',
                     f"{dock['id']}.pose": [dx, dy, dyaw]}],
        remappings=[('cmd_vel', 'cmd_vel_nav')])
    docking_lifecycle = Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_docking', output='screen',
        parameters=[{'use_sim_time': True, 'autostart': True,
                     'node_names': ['docking_server']}])

    return [sim_bringup, nav2_bringup, ground_truth, tag_camera, tag_tracker,
            docking_server, docking_lifecycle]


def generate_launch_description():
    week12 = get_package_share_directory('amr_week12')
    week15 = get_package_share_directory('amr_week15')
    adv06 = get_package_share_directory('amr_adv06')
    return LaunchDescription([
        DeclareLaunchArgument('headless', default_value='false',
                              description='true: Gazebo server only (no GUI) - Docker/CI'),
        DeclareLaunchArgument('rviz', default_value='false', description='Start RViz2'),
        DeclareLaunchArgument('map', default_value=os.path.join(week12, 'maps',
                                                                'warehouse_map.yaml')),
        DeclareLaunchArgument('bt_xml', default_value=os.path.join(
            week15, 'behavior_trees', 'patrol_nav_to_pose.xml')),
        DeclareLaunchArgument('mission', default_value=os.path.join(
            adv06, 'config', 'capstone_mission.yaml'),
            description='Mission/dock definition (dock pose -> docking DB + AprilTag pose)'),
        OpaqueFunction(function=launch_setup),
    ])
