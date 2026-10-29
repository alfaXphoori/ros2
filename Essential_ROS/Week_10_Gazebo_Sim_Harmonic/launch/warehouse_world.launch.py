#!/usr/bin/env python3
"""
Week 10: start the warehouse world in Gazebo Sim 8 (Harmonic).

  ros2 launch amr_week10 warehouse_world.launch.py               # GUI + server
  ros2 launch amr_week10 warehouse_world.launch.py headless:=true  # server only

headless:=true runs `gz sim -s -r --headless-rendering <world>`: no GUI window,
but the Sensors system can still render (gpu_lidar / cameras) through EGL.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, EmitEvent, ExecuteProcess,
                            IncludeLaunchDescription)
from launch.conditions import IfCondition, UnlessCondition
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    default_world = os.path.join(
        get_package_share_directory('amr_week10'), 'worlds', 'warehouse.sdf')
    gz_sim_launch = os.path.join(
        get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')

    world = LaunchConfiguration('world')
    headless = LaunchConfiguration('headless')

    # Server + GUI (needs a display / X11 forwarding)
    gz_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_sim_launch),
        launch_arguments={'gz_args': ['-r ', world], 'on_exit_shutdown': 'true'}.items(),
        condition=UnlessCondition(headless),
    )
    # Server only (-s), run immediately (-r), offscreen rendering for sensors.
    # Started directly, not through ros_gz_sim's gz_sim.launch.py: that one runs gz under
    # `/bin/sh -c`, launch's SIGINT/SIGTERM reach only the shell, and the gz-sim server is
    # left running after shutdown (still publishing /clock and sensors into the same
    # GZ_PARTITION, which broke the next launch test). Run directly it stops in ~1 s.
    gz_headless = ExecuteProcess(
        cmd=['gz', 'sim', '-s', '-r', '--headless-rendering', world],
        name='gazebo', output='screen', sigterm_timeout='20', sigkill_timeout='5',
        on_exit=[EmitEvent(event=Shutdown(reason='gz sim exited'))],
        condition=IfCondition(headless),
    )

    return LaunchDescription([
        DeclareLaunchArgument('world', default_value=default_world,
                              description='Full path to the SDF world file'),
        DeclareLaunchArgument('headless', default_value='false',
                              description='true = gz sim server only (no GUI window)'),
        gz_gui,
        gz_headless,
    ])
