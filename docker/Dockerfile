FROM ros:jazzy-ros-base

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
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
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

CMD ["/bin/bash"]
