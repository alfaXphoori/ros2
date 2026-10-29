"""Advanced Module 02: synthetic camera -> AprilTag dock tracker + object detector (headless).

  ros2 launch amr_adv02 vision_pipeline.launch.py
  ros2 launch amr_adv02 vision_pipeline.launch.py tag_z:=1.2 tag_yaw_deg:=-25.0
  ros2 launch amr_adv02 vision_pipeline.launch.py tag_visible:=false   # no pose is published

Topics: /camera/image_raw, /camera/camera_info, /camera/tag_pose_ground_truth,
        /detected_dock_pose (PoseStamped), /perception/detections (Detection2DArray),
        /perception/debug_image
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    def arg(name, default, desc):
        return DeclareLaunchArgument(name, default_value=default, description=desc)

    def num(name):
        return ParameterValue(LaunchConfiguration(name), value_type=float)

    return LaunchDescription([
        arg('tag_x', '0.10', 'tag position in the camera optical frame [m] (right)'),
        arg('tag_y', '0.05', 'tag position in the camera optical frame [m] (down)'),
        arg('tag_z', '0.80', 'tag distance along the optical axis [m]'),
        arg('tag_yaw_deg', '15.0', 'tag rotation about the vertical axis [deg]'),
        arg('tag_size', '0.10', 'tag edge length (black border) [m]'),
        arg('tag_visible', 'true', 'render the tag at all'),
        Node(package='amr_adv02', executable='synthetic_tag_camera', output='screen',
             parameters=[{'tag_x': num('tag_x'), 'tag_y': num('tag_y'), 'tag_z': num('tag_z'),
                          'tag_yaw_deg': num('tag_yaw_deg'), 'tag_size': num('tag_size'),
                          'tag_visible': ParameterValue(LaunchConfiguration('tag_visible'),
                                                        value_type=bool)}]),
        Node(package='amr_adv02', executable='apriltag_dock_tracker', output='screen',
             parameters=[{'tag_size': num('tag_size')}]),
        Node(package='amr_adv02', executable='object_detector', output='screen'),
    ])
