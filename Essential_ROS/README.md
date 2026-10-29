# 📘 Essential ROS 2 Track: หลักสูตรและแล็บครบ 16 สัปดาห์

ยินดีต้อนรับสู่ **Essential ROS 2 Track** — เส้นทางการเรียนรู้หลักสำหรับวิศวกรที่ต้องการสร้างและควบคุมหุ่นยนต์เคลื่อนที่อัตโนมัติ (Autonomous Mobile Robot - AMR) ตั้งแต่ระดับพื้นฐานจนถึงการขับเคลื่อนอัตโนมัติในแบบจำลอง 3 มิติ ด้วย **ROS 2 Jazzy Jalisco** และ **Gazebo Sim 8 (Harmonic)**

> 🎓 **แผนการสอน 16 สัปดาห์เต็ม:** สำหรับอาจารย์ผู้สอนหรือสถาบันการศึกษา สามารถดูโครงสร้างแผนการสอนฉบับเต็มได้ที่ [`course_syllabus_01_essential_ros2.md`](../course_syllabus_01_essential_ros2.md)  
> 📖 **คู่มือเนื้อหาบรรยายและขั้นตอนแล็บละเอียด 16 สัปดาห์:** อ่านได้ที่ [`docs/weekly_lectures_and_labs.md`](docs/weekly_lectures_and_labs.md)  
> 🛠️ **คู่มือการติดตั้ง ROS 2 ทุกระบบปฏิบัติการ (Native, Docker, WSL2):** อ่านได้ที่ [**`docs/ros2_installation_guide.md`**](../docs/ros2_installation_guide.md)  
> 🧰 **คู่มือเครื่องมือโปรแกรมเมอร์ & CLI Cheat Sheet:** อ่านได้ที่ [**`docs/ros2_developer_toolkit.md`**](../docs/ros2_developer_toolkit.md)

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

แต่ละโฟลเดอร์ `Week_NN_*` เป็น ROS 2 package ชนิด `ament_python` ชื่อ `amr_weekNN` (โค้ดอยู่ใน `src/`, launch/config/urdf
ติดตั้งลง `share/amr_weekNN`) ให้ build ทั้งหมดครั้งเดียวด้วย `make build` จากนั้น `run_lab.sh` จะ source
`install/setup.bash` ให้อัตโนมัติ คำสั่งทั้งหมดรันในคอนเทนเนอร์ `ros:lab-runner` (ROS 2 Jazzy + Gazebo Harmonic)

```bash
# จาก root ของ repo
make build                       # colcon build ทุกแพ็กเกจ (Essential + Advanced)
make test PKG=amr_week04         # รันชุดทดสอบอัตโนมัติของสัปดาห์ที่ 4

# สัปดาห์ที่ 1: คำนวณพอร์ต DDS / ตรวจ Domain
./docker/run_lab.sh ros2 run amr_week01 domain_check.sh
# สัปดาห์ที่ 2: QoS Publisher / Subscriber
./docker/run_lab.sh ros2 run amr_week02 sensor_qos_publisher
# สัปดาห์ที่ 4: Action Server (ยกเลิก/preempt goal ได้)
./docker/run_lab.sh ros2 run amr_week04 navigate_action_server
# สัปดาห์ที่ 5: Launch + namespace + parameters
./docker/run_lab.sh ros2 launch amr_week05 core_system.launch.py robot_ns:=amr_01
# สัปดาห์ที่ 7: ตรวจ URDF และแสดง TF แบบไม่เปิด RViz
./docker/run_lab.sh check_urdf Essential_ROS/Week_07_URDF_Robot_Modeling/urdf/diff_drive_robot.urdf
./docker/run_lab.sh ros2 launch amr_week07 display_urdf.launch.py rviz:=false
# สัปดาห์ที่ 9: TF2 lab (broadcaster หรือ URDF เป็นแหล่ง TF เพียงแหล่งเดียว)
./docker/run_lab.sh ros2 launch amr_week09 tf_lab.launch.py tf_source:=broadcaster
# สัปดาห์ที่ 11: Gazebo Sim + Bridge + robot_state_publisher (headless:=true เมื่อไม่มีจอ)
./docker/run_lab.sh ros2 launch amr_week11 gazebo_world.launch.py headless:=true
# สัปดาห์ที่ 12: SLAM พร้อม sim และสคริปต์สำรวจอัตโนมัติ
./docker/run_lab.sh ros2 launch amr_week12 slam_mapping_sim.launch.py headless:=true explore:=true
# สัปดาห์ที่ 13: Global/Local costmap บนแผนที่จริง
./docker/run_lab.sh ros2 launch amr_week13 costmap_demo.launch.py headless:=true
# สัปดาห์ที่ 14: Nav2 Bringup (AMCL + planner + controller + behavior server) — เปิด sim ของสัปดาห์ที่ 11 ไว้ก่อน (คนละเทอร์มินัล)
./docker/run_lab.sh ros2 launch amr_week11 gazebo_world.launch.py headless:=true
./docker/run_lab.sh ros2 launch amr_week14 nav2_bringup.launch.py
# สัปดาห์ที่ 15: Waypoint patrol + custom Behavior Tree
./docker/run_lab.sh ros2 launch amr_week15 patrol_system.launch.py headless:=true
# สัปดาห์ที่ 16: Final Demonstration (คนละเทอร์มินัล)
./docker/run_lab.sh ros2 launch amr_week16 final_amr_system.launch.py headless:=true
./docker/run_lab.sh ros2 run amr_week16 final_mission_executor --ros-args -p use_sim_time:=true
```

อาร์กิวเมนต์และขั้นตอนละเอียดของแต่ละคำสั่งอยู่ใน `Readme.md` / `Lab_Exercises.md` ของสัปดาห์นั้น และทุกสัปดาห์มีหัวข้อ
**📟 ผลการรันจริง (Real Run Output)** พร้อมไฟล์ log ดิบในโฟลเดอร์ `results/`

> ℹ️ โฟลเดอร์ `01_Core_Communication` … `05_Nav2_Navigation` เป็นโครงสร้างโมดูลรุ่นเก่า ปัจจุบันเหลือเพียง `Readme.md`
> ที่ชี้ไปยังโฟลเดอร์สัปดาห์ที่เกี่ยวข้อง (โค้ดชุดเก่ายังดูได้จากประวัติ git)
