import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

def generate_launch_description():
    pkg_ce_webots = get_package_share_directory('ce_webots')
    
    world_path = PathJoinSubstitution([pkg_ce_webots, 'worlds', '052_slam.wbt'])

    webots_cmd = ExecuteProcess(
        cmd=['webots', world_path],
        output='screen'
    )

    slam_node = Node(
        package='ce_webots',
        executable='052_slam_controller',
        name='slam_odometry',
        output='screen'
    )

    return LaunchDescription([
        webots_cmd,
        slam_node,
    ])
