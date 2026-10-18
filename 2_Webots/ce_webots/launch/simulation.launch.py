import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

def generate_launch_description():
    pkg_ce_webots = get_package_share_directory('ce_webots')
    
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='052_slam.wbt',
        description='Name of the Webots world file to load from worlds/ directory'
    )
    
    gui_arg = DeclareLaunchArgument(
        'gui',
        default_value='true',
        description='Whether to start Webots GUI'
    )

    world_path = PathJoinSubstitution([pkg_ce_webots, 'worlds', LaunchConfiguration('world')])

    webots_cmd = ExecuteProcess(
        cmd=['webots', world_path],
        output='screen'
    )

    return LaunchDescription([
        world_arg,
        gui_arg,
        webots_cmd,
    ])
