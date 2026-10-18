# 🤖 ROS 2 Robotics Learning Platform

A comprehensive educational platform for learning **ROS 2 Jazzy** robotics programming with hands-on exercises, simulations, and real-world applications.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy%20Jalisco-blue)](https://docs.ros.org/en/jazzy/)
[![Webots](https://img.shields.io/badge/Webots-2023b+-red)](https://cyberbotics.com/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-phoori--gh%2Fros-brightgreen)](https://github.com/phoori-gh/ros)

---

## 📋 แผนการเรียนรู้และโครงสร้างโปรเจกต์ (Project Structure)

This repository is organized into three progressive learning sections and a 15-week university syllabus:

### 🎓 **[weekly-lesson-plan.md](weekly-lesson-plan.md)** - 15-Week Academic Course Syllabus
A complete university curriculum covering Course Learning Outcomes (CLOs), Lesson Learning Outcomes (LLOs), theory lectures (2 hrs/wk), laboratory exercises (3 hrs/wk), and grading rubrics:
- **Weeks 1-5:** ROS 2 Core Middleware Architecture
- **Weeks 6-12:** Webots Simulation, Kinematics, Sensor Integration (Encoders, IMU, Vision, LiDAR, 3D Point Cloud)
- **Weeks 13-15:** SLAM Mapping, Costmaps, AMCL, and Nav2 Multi-Waypoint Logistics Patrol

[👉 View 15-Week Lesson Plan & Syllabus →](weekly-lesson-plan.md)

---

### 1️⃣ **[1_ROS2/](1_ROS2/README.md)** - Core ROS 2 Concepts
Foundational ROS 2 programming tutorials covering:
- **00_Install** - ROS 2 Jazzy installation guide and setup
- **01_Publisher_Subscriber** - Message passing between nodes
- **02_Server_Client** - Request-response communication patterns
- **03_Message** - Custom message definition and usage
- **04_Service** - Service definition and implementation
- **05_Parameters** - Dynamic parameter management
- **06_Action** - Long-running task execution with feedback
- **07_Launch** - Multi-node launch file configuration and execution

[📖 Explore ROS 2 Core Tutorials →](1_ROS2/README.md)

---

### 2️⃣ **[2_Webots/](2_Webots/Readme.md)** - Robot Simulation & Sensor Integration
Advanced robotics tutorials using Webots simulator with ROS 2 integration:
- **Level 0 (000):** Installation and basic setup
- **Level 1 (001, 002):** Motor control fundamentals & keyboard teleoperation
- **Level 2 (011, 012):** Proprioceptive sensing (rotary wheel encoders & distance tracking)
- **Level 3 (021, 022):** Obstacle avoidance (touch bumpers & distance sensors)
- **Level 4 (031, 032):** Inertial measurement (IMU heading control & accelerometer motion)
- **Level 5 (041, 042):** Computer vision (HSV color tracking & adaptive line following)
- **Level 6 (051, 052):** Range sensing & SLAM mapping (LiDAR scanning & Odometry mapping)
- **Level 7 (061, 062):** 3D perception (RGB-D depth camera & 3D point cloud reconstruction)
- **Level 8 (071):** Autonomous navigation and stuck recovery
- **Package `ce_webots`:** Ready-to-build ROS 2 package containing all 15 controllers, worlds, launch files, and map saver node (`save_map`)

[🚀 Explore Webots Simulation Tutorials →](2_Webots/Readme.md)

---

### 3️⃣ **[3_Nav2/](3_Nav2/Readme.md)** - Navigation 2 (Nav2) Autonomous Stack
Complete production-grade autonomous mobile robot (AMR) navigation stack:
- **SLAM Toolbox:** Online asynchronous graph-based mapping and loop closure
- **Map Server & AMCL:** Occupancy grid serving and Adaptive Monte Carlo Localization
- **Costmap 2D:** Global and local costmaps with static, obstacle, and inflation layers
- **Planners & Controllers:** Navfn global path planner and DWB local trajectory follower
- **Behavior Trees & Recovery:** Spin, BackUp, and Wait recovery behaviors
- **Simple Commander API:** Python-based autonomous waypoint navigation and logistics patrol

[🧭 Explore Navigation 2 Tutorials & Labs →](3_Nav2/Readme.md)

---

## ⚡ Quick Start

### Prerequisites
- **OS**: Ubuntu 22.04 LTS (or compatible Linux / WSL2)
- **Python**: 3.10+
- **ROS 2**: Jazzy Jalisco
- **Webots**: 2023b or later (for simulation exercises)

### 1. Clone Repository
```bash
git clone https://github.com/phoori-gh/ros.git
cd ros
```

### 2. Build the `ce_webots` Simulation Package
```bash
# Create ROS 2 workspace
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
ln -s "/path/to/ros/2_Webots/ce_webots" .

# Build with colcon
cd ~/ros2_ws
colcon build --packages-select ce_webots
source install/setup.bash
```

### 3. Launching Tutorials

**A. ROS 2 Core Message Passing:**
```bash
cd 1_ROS2/01_Publisher_Subscriber/src
python3 simple_publisher.py    # Terminal 1
python3 simple_subscriber.py   # Terminal 2
```

**B. Webots SLAM Mapping Simulation:**
```bash
# Terminal 1: Launch simulation
ros2 launch ce_webots slam_mapping.launch.py

# Terminal 2: Save map when done
ros2 run ce_webots save_map --ros-args -p map_name:=warehouse_map
```

**C. Nav2 Autonomous Navigation & Multi-Waypoint Patrol:**
```bash
# Terminal 1: Launch Nav2 stack
ros2 launch 3_Nav2/launch/nav2_bringup.launch.py

# Terminal 2: Set AMCL initial pose
python3 3_Nav2/src/amcl_initial_pose.py

# Terminal 3: Run autonomous patrol
python3 3_Nav2/src/waypoint_patrol.py
```

---

## 🛠 Technology Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| **ROS 2** | Jazzy Jalisco | Distributed robotics middleware |
| **Python** | 3.10+ | Primary programming language |
| **Webots** | 2023b+ | High-fidelity robot simulator |
| **Nav2** | Jazzy | Autonomous navigation & path planning |
| **SLAM Toolbox** | Jazzy | 2D Pose-Graph SLAM & loop closure |
| **Ubuntu** | 22.04 LTS | Standard operating system |

---

## 🎓 Learning Outcomes

After completing this course, you will be able to:

✅ Understand ROS 2 architecture, DDS, QoS, and lifecycle management  
✅ Develop asynchronous publishers, subscribers, services, and actions  
✅ Model differential drive kinematics and sensor physics in Webots  
✅ Integrate Encoders, IMU, Touch, Distance, Camera, and LiDAR sensors  
✅ Perform computer vision image processing with OpenCV and `cv_bridge`  
✅ Build 2D occupancy grid maps using SLAM Toolbox and Odometry  
✅ Configure AMCL particle filter localization and 2D Costmaps  
✅ Tune DWB local controllers for safe obstacle avoidance  
✅ Implement Behavior Tree navigation and multi-waypoint patrol via Python API  

---

## 🤝 Contributing

This is an open educational repository. Contributions, corrections, and improvements are welcome:
- Report issues and suggest enhancements
- Submit pull requests for new simulation worlds or algorithms
- Star and share with the robotics community!

---

## 📜 License

This project is open-source and available under the [MIT License](LICENSE).

---

## 👤 Authors & Maintainers

- **phoori-gh** - Repository creator and maintainer ([https://github.com/phoori-gh/ros](https://github.com/phoori-gh/ros))
- **KSU Robotics Team & CE Faculty**

---

## 📞 Support & Community

- 📖 [Explore 15-Week Lesson Plan](weekly-lesson-plan.md)
- 🚀 [Webots Simulation Guide](2_Webots/Readme.md)
- 🧭 [Nav2 Architecture Guide](3_Nav2/Readme.md)
- 🐛 [Report Issues](https://github.com/phoori-gh/ros/issues)
- 💬 [Discussions](https://github.com/phoori-gh/ros/discussions)
