# 📘 Essential ROS 2 Track: หลักสูตรและแล็บครบ 16 สัปดาห์

ยินดีต้อนรับสู่ **Essential ROS 2 Track** — เส้นทางการเรียนรู้หลักสำหรับวิศวกรที่ต้องการสร้างและควบคุมหุ่นยนต์เคลื่อนที่อัตโนมัติ (Autonomous Mobile Robot - AMR) ตั้งแต่ระดับพื้นฐานจนถึงการขับเคลื่อนอัตโนมัติในแบบจำลอง 3 มิติ ด้วย **ROS 2 Jazzy Jalisco** และ **Gazebo Sim 8 (Harmonic)**

> 🎓 **แผนการสอน 16 สัปดาห์เต็ม:** สำหรับอาจารย์ผู้สอนหรือสถาบันการศึกษา สามารถดูโครงสร้างแผนการสอนฉบับเต็มได้ที่ [`course_syllabus_01_essential_ros2.md`](../course_syllabus_01_essential_ros2.md)  
> 📖 **คู่มือเนื้อหาบรรยายและขั้นตอนแล็บละเอียด 16 สัปดาห์:** อ่านได้ที่ [`docs/weekly_lectures_and_labs.md`](docs/weekly_lectures_and_labs.md)

---

## 🗺️ ตารางบทเรียนและแล็บปฏิบัติการครบ 16 สัปดาห์ (Weeks 01 - 16)

| สัปดาห์ | หัวข้อบทเรียน | คู่มือบรรยาย | ใบงานแล็บ | โค้ด/ไฟล์คอนฟิก |
| :---: | :--- | :--- | :--- | :--- |
| **01** | **Environment & DDS Network** | [`Week_01/Readme.md`](Week_01_Environment_DDS/Readme.md) | [`Lab.md`](Week_01_Environment_DDS/Lab_Exercises.md) | [`domain_check.sh`](Week_01_Environment_DDS/src/domain_check.sh) |
| **02** | **Nodes, Topics & QoS Policies** | [`Week_02/Readme.md`](Week_02_Nodes_Topics_QoS/Readme.md) | [`Lab.md`](Week_02_Nodes_Topics_QoS/Lab_Exercises.md) | [`sensor_qos_publisher.py`](Week_02_Nodes_Topics_QoS/src/sensor_qos_publisher.py) |
| **03** | **Services & Clients (RPC)** | [`Week_03/Readme.md`](Week_03_Services_Clients/Readme.md) | [`Lab.md`](Week_03_Services_Clients/Lab_Exercises.md) | [`power_service_server.py`](Week_03_Services_Clients/src/power_service_server.py)<br>[`power_service_client.py`](Week_03_Services_Clients/src/power_service_client.py) |
| **04** | **Actions & Goal Preemption** | [`Week_04/Readme.md`](Week_04_Actions_Preemption/Readme.md) | [`Lab.md`](Week_04_Actions_Preemption/Lab_Exercises.md) | [`navigate_action_server.py`](Week_04_Actions_Preemption/src/navigate_action_server.py)<br>[`navigate_action_client.py`](Week_04_Actions_Preemption/src/navigate_action_client.py) |
| **05** | **Parameters & Launch Architecture** | [`Week_05/Readme.md`](Week_05_Parameters_Launch/Readme.md) | [`Lab.md`](Week_05_Parameters_Launch/Lab_Exercises.md) | [`fleet_parameters.py`](Week_05_Parameters_Launch/src/fleet_parameters.py)<br>[`core_system.launch.py`](Week_05_Parameters_Launch/launch/core_system.launch.py) |
| **06** | **Kinematics & REP Standards** | [`Week_06/Readme.md`](Week_06_Kinematics_REP_Standards/Readme.md) | [`Lab.md`](Week_06_Kinematics_REP_Standards/Lab_Exercises.md) | [`diff_drive_kinematics.py`](Week_06_Kinematics_REP_Standards/src/diff_drive_kinematics.py) |
| **07** | **URDF 3D Robot Modeling** | [`Week_07/Readme.md`](Week_07_URDF_Robot_Modeling/Readme.md) | [`Lab.md`](Week_07_URDF_Robot_Modeling/Lab_Exercises.md) | [`diff_drive_robot.urdf`](Week_07_URDF_Robot_Modeling/urdf/diff_drive_robot.urdf)<br>[`display_urdf.launch.py`](Week_07_URDF_Robot_Modeling/launch/display_urdf.launch.py) |
| **08** | **🔴 Midterm Practical Exam** | [`Week_08/Readme.md`](Week_08_Midterm_Practical_Exam/Readme.md) | [`Exam_Task.md`](Week_08_Midterm_Practical_Exam/Exam_Task.md) | [`solution/`](Week_08_Midterm_Practical_Exam/solution/) |
| **09** | **TF2 Coordinate Transforms** | [`Week_09/Readme.md`](Week_09_TF2_Coordinate_Transforms/Readme.md) | [`Lab.md`](Week_09_TF2_Coordinate_Transforms/Lab_Exercises.md) | [`static_sensor_broadcaster.py`](Week_09_TF2_Coordinate_Transforms/src/static_sensor_broadcaster.py)<br>[`tf_obstacle_listener.py`](Week_09_TF2_Coordinate_Transforms/src/tf_obstacle_listener.py) |
| **10** | **Gazebo Sim 3D World (SDF)** | [`Week_10/Readme.md`](Week_10_Gazebo_Sim_Harmonic/Readme.md) | [`Lab.md`](Week_10_Gazebo_Sim_Harmonic/Lab_Exercises.md) | [`warehouse.sdf`](Week_10_Gazebo_Sim_Harmonic/worlds/warehouse.sdf) |
| **11** | **Actuators, Sensors & Bridge** | [`Week_11/Readme.md`](Week_11_Actuators_Sensors_Bridge/Readme.md) | [`Lab.md`](Week_11_Actuators_Sensors_Bridge/Lab_Exercises.md) | [`ros_gz_bridge.yaml`](Week_11_Actuators_Sensors_Bridge/config/ros_gz_bridge.yaml)<br>[`gazebo_world.launch.py`](Week_11_Actuators_Sensors_Bridge/launch/gazebo_world.launch.py)<br>[`emergency_stop_node.py`](Week_11_Actuators_Sensors_Bridge/src/emergency_stop_node.py) |
| **12** | **SLAM 2D Mapping (Ceres)** | [`Week_12/Readme.md`](Week_12_SLAM_Mapping_Ceres/Readme.md) | [`Lab.md`](Week_12_SLAM_Mapping_Ceres/Lab_Exercises.md) | [`slam_toolbox_params.yaml`](Week_12_SLAM_Mapping_Ceres/config/slam_toolbox_params.yaml)<br>[`online_async_slam.launch.py`](Week_12_SLAM_Mapping_Ceres/launch/online_async_slam.launch.py)<br>[`maps/`](Week_12_SLAM_Mapping_Ceres/maps/) |
| **13** | **Nav2 Costmaps & Layers** | [`Week_13/Readme.md`](Week_13_Nav2_Costmaps_Layers/Readme.md) | [`Lab.md`](Week_13_Nav2_Costmaps_Layers/Lab_Exercises.md) | [`costmap_params.yaml`](Week_13_Nav2_Costmaps_Layers/config/costmap_params.yaml) |
| **14** | **Path Planning & AMCL** | [`Week_14/Readme.md`](Week_14_Path_Planning_AMCL/Readme.md) | [`Lab.md`](Week_14_Path_Planning_AMCL/Lab_Exercises.md) | [`nav2_params.yaml`](Week_14_Path_Planning_AMCL/config/nav2_params.yaml)<br>[`nav2_bringup.launch.py`](Week_14_Path_Planning_AMCL/launch/nav2_bringup.launch.py)<br>[`amcl_initial_pose.py`](Week_14_Path_Planning_AMCL/src/amcl_initial_pose.py) |
| **15** | **Waypoint Patrol & BT** | [`Week_15/Readme.md`](Week_15_Waypoint_Patrol_BT/Readme.md) | [`Lab.md`](Week_15_Waypoint_Patrol_BT/Lab_Exercises.md) | [`waypoint_patrol.py`](Week_15_Waypoint_Patrol_BT/src/waypoint_patrol.py) |
| **16** | **🏆 Final Practical Demo** | [`Week_16/Readme.md`](Week_16_Final_Demonstration/Readme.md) | [`Lab.md`](Week_16_Final_Demonstration/Lab_Exercises.md)<br>[`Rubric.md`](Week_16_Final_Demonstration/Evaluation_Rubric.md) | [`final_amr_system.launch.py`](Week_16_Final_Demonstration/launch/final_amr_system.launch.py)<br>[`final_mission_executor.py`](Week_16_Final_Demonstration/src/final_mission_executor.py) |

---

## ⚡ Quick Start: คำสั่งรันแล็บแต่ละสัปดาห์

```bash
cd /mnt/sda/ros

# สัปดาห์ที่ 1: ตรวจสอบ DDS
./docker/run_lab.sh bash Essential_ROS/Week_01_Environment_DDS/src/domain_check.sh

# สัปดาห์ที่ 2: รัน QoS Publisher
./docker/run_lab.sh python3 Essential_ROS/Week_02_Nodes_Topics_QoS/src/sensor_qos_publisher.py

# สัปดาห์ที่ 5: รัน Core Launch System
./docker/run_lab.sh ros2 launch Essential_ROS/Week_05_Parameters_Launch/launch/core_system.launch.py

# สัปดาห์ที่ 7: ตรวจสอบ URDF
./docker/run_lab.sh check_urdf Essential_ROS/Week_07_URDF_Robot_Modeling/urdf/diff_drive_robot.urdf

# สัปดาห์ที่ 11: เปิด Gazebo Sim พร้อม Bridge
./docker/run_lab.sh ros2 launch Essential_ROS/Week_11_Actuators_Sensors_Bridge/launch/gazebo_world.launch.py

# สัปดาห์ที่ 12: รัน SLAM ทำแผนที่
./docker/run_lab.sh ros2 launch Essential_ROS/Week_12_SLAM_Mapping_Ceres/launch/online_async_slam.launch.py

# สัปดาห์ที่ 14: รัน Nav2 Bringup
./docker/run_lab.sh ros2 launch Essential_ROS/Week_14_Path_Planning_AMCL/launch/nav2_bringup.launch.py

# สัปดาห์ที่ 16: รัน Final Demonstration
./docker/run_lab.sh ros2 launch Essential_ROS/Week_16_Final_Demonstration/launch/final_amr_system.launch.py
```
