"""Advanced Module 03: Nav2 docking server, headless, with vision in the loop.

  ros2 launch amr_adv03 docking_sim.launch.py
  ros2 run amr_adv03 dock_client          # (second terminal) DockRobot -> measure -> UndockRobot

  fake_base (cmd_vel -> odom + TF odom->base_footprint)
  static TF base_footprint -> camera_link -> camera_optical_link (camera at the robot front)
  amr_adv02 synthetic_tag_camera (mode tf): renders AprilTag 36h11 id 0 mounted on the charger
      wall, as seen from the CURRENT robot pose -> /camera/image_raw + /camera/camera_info
  amr_adv02 apriltag_dock_tracker -> /detected_dock_pose (PoseStamped, camera optical frame)
  opennav_docking docking_server (+ nav2 lifecycle_manager) -> /dock_robot, /undock_robot

Geometry (odom frame): robot starts near the staging pose; the true dock pose (robot pose when
docked) is `dock_x, dock_y, dock_yaw`; the tag is 0.40 m beyond it at camera height (0.10 m).
"""
import math
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

TAG_BEYOND_DOCK = 0.40   # m, must equal -external_detection_translation_x in the YAML
CAMERA_XYZ = (0.20, 0.0, 0.10)  # base_footprint -> camera_link (as in Essential Week 07 URDF)


def launch_setup(context):
    def f(name):
        return float(LaunchConfiguration(name).perform(context))

    dock_x, dock_y, dock_yaw = f('dock_x'), f('dock_y'), f('dock_yaw')
    params = os.path.join(get_package_share_directory('amr_adv03'), 'config',
                          'docking_server_params.yaml')
    tag_world = [dock_x + TAG_BEYOND_DOCK * math.cos(dock_yaw),
                 dock_y + TAG_BEYOND_DOCK * math.sin(dock_yaw),
                 CAMERA_XYZ[2],
                 dock_yaw + math.pi]  # tag normal points back towards the robot

    # dock database prior deliberately `db_error_y` off: the camera must correct it
    overrides = {'home_dock.pose': [dock_x, dock_y + f('db_error_y'), dock_yaw]}
    threshold = LaunchConfiguration('docking_threshold').perform(context)
    if threshold:
        overrides['simple_charging_dock.docking_threshold'] = float(threshold)
    # use_vision:=false -> dock blindly at the (wrong) database pose, for comparison
    overrides['simple_charging_dock.use_external_detection_pose'] = \
        LaunchConfiguration('use_vision').perform(context).lower() in ('true', '1')

    return [
        Node(package='amr_adv03', executable='fake_base', output='screen',
             parameters=[{'initial_x': f('start_x'), 'initial_y': f('start_y'),
                          'initial_yaw': f('start_yaw')}]),
        Node(package='tf2_ros', executable='static_transform_publisher', name='camera_tf',
             arguments=['--x', str(CAMERA_XYZ[0]), '--y', str(CAMERA_XYZ[1]),
                        '--z', str(CAMERA_XYZ[2]),
                        '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link']),
        Node(package='tf2_ros', executable='static_transform_publisher', name='optical_tf',
             arguments=['--roll', str(-math.pi / 2), '--yaw', str(-math.pi / 2),
                        '--frame-id', 'camera_link', '--child-frame-id', 'camera_optical_link']),
        Node(package='amr_adv02', executable='synthetic_tag_camera', output='screen',
             parameters=[{'mode': 'tf', 'world_frame': 'odom', 'tag_world': tag_world,
                          'frame_id': 'camera_optical_link', 'draw_objects': False,
                          'tag_size': 0.10, 'rate': 15.0}]),
        Node(package='amr_adv02', executable='apriltag_dock_tracker', output='screen',
             parameters=[{'tag_size': 0.10, 'tag_id': 0}]),
        Node(package='opennav_docking', executable='opennav_docking', name='docking_server',
             output='screen',
             parameters=[params, overrides]),
        Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
             name='lifecycle_manager_docking', output='screen',
             parameters=[{'autostart': True, 'node_names': ['docking_server']}]),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('dock_x', default_value='1.0'),
        DeclareLaunchArgument('dock_y', default_value='0.0'),
        DeclareLaunchArgument('dock_yaw', default_value='0.0'),
        DeclareLaunchArgument('docking_threshold', default_value='',
                              description='override simple_charging_dock.docking_threshold [m] '
                                          '(empty: value from config/docking_server_params.yaml)'),
        DeclareLaunchArgument('use_vision', default_value='true',
                              description='false: ignore the AprilTag, trust the dock database'),
        DeclareLaunchArgument('db_error_y', default_value='0.05',
                              description='lateral error of the dock database prior [m]'),
        DeclareLaunchArgument('start_x', default_value='0.0'),
        DeclareLaunchArgument('start_y', default_value='-0.08'),
        DeclareLaunchArgument('start_yaw', default_value='0.15'),
        OpaqueFunction(function=launch_setup),
    ])
