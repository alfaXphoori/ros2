# Pinned base image (ROS 2 Jazzy, Ubuntu 24.04 Noble) for reproducible labs.
# Update the digest deliberately: docker pull ros:jazzy-ros-base-noble && docker image inspect ...
FROM ros:jazzy-ros-base-noble@sha256:c3706ef0a0aa45413c07803cf433602f543b22e45b4855f6fca955c2d8ecc4e8

ENV DEBIAN_FRONTEND=noninteractive

# dist-upgrade first: the pinned base image ships older ROS packages, and installing newer
# ones next to them mixes incompatible releases (e.g. launch_testing_ros 0.26.13's pytest
# hook vs launch_testing 3.4.11 -> PluginValidationError before any launch test runs).
RUN apt-get update && apt-get dist-upgrade -y \
 && apt-get install -y --no-install-recommends \
    # GUI Tools & Drivers
    xvfb \
    scrot \
    x11-utils \
    imagemagick \
    mesa-utils \
    # Development & Python Tools
    python3-pil \
    python3-matplotlib \
    python3-pip \
    liburdfdom-tools \
    graphviz \
    # ROS 2 Visualization & Core Nodes
    ros-jazzy-rviz2 \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-tf2-tools \
    ros-jazzy-tf2-ros \
    ros-jazzy-xacro \
    # Gazebo Sim (Harmonic) Stack
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-ros-gz-image \
    # Navigation & SLAM Stack
    ros-jazzy-slam-toolbox \
    ros-jazzy-navigation2 \
    ros-jazzy-nav2-bringup \
    ros-jazzy-nav2-simple-commander \
    # Lab helpers used by the weekly exercises
    ros-jazzy-teleop-twist-keyboard \
    ros-jazzy-demo-nodes-py \
    ros-jazzy-tf-transformations \
    python3-transforms3d \
    ros-jazzy-rqt-graph \
    ros-jazzy-rqt-plot \
    ros-jazzy-cv-bridge \
    python3-pytest \
    # Testing, linting & recording (colcon test / launch_testing / MCAP bags)
    ros-jazzy-launch-testing-ros \
    ros-jazzy-launch-testing-ament-cmake \
    ros-jazzy-rosbag2-storage-mcap \
    yamllint \
    libxml2-utils \
    # Advanced track: ros2_control (mock + Gazebo), docking, safety, perception
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-opennav-docking \
    ros-jazzy-nav2-collision-monitor \
    ros-jazzy-nav2-loopback-sim \
    ros-jazzy-image-publisher \
    ros-jazzy-camera-calibration \
    ros-jazzy-vision-msgs \
    # Multi-robot fleet (Open-RMF Python fleet adapter) & alternative middleware
    ros-jazzy-rmf-fleet-adapter-python \
    ros-jazzy-rmw-zenoh-cpp \
    # Headless visualization (Foxglove Studio connects over WebSocket :8765)
    ros-jazzy-foxglove-bridge \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

CMD ["/bin/bash"]
