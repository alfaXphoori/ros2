# 🤖 การเขียนโปรแกรมระบบปฏิบัติการหุ่นยนต์ด้วย ROS 2 Jazzy & Gazebo Sim
## (Robotics & Autonomous Systems with ROS 2 Jazzy Jalisco & Gazebo Harmonic)

> **หลักสูตรปฏิบัติการระดับวิศวกรรม: จากรากฐานสถาปัตยกรรมสู่หุ่นยนต์เคลื่อนที่อัตโนมัติ (AMR) เต็มรูปแบบ**  
> **มาตรฐานระบบ:** ROS 2 Jazzy Jalisco (LTS 2024–2029) + Gazebo Sim 8 (Harmonic) + Navigation 2 (Nav2)

---

## 📌 ภาพรวมหลักสูตร (Course Overview)

คลังความรู้นี้ออกแบบมาสำหรับการเรียนรู้และการฝึกทักษะวิศวกรรมหุ่นยนต์สมัยใหม่ โดยเน้นการลงมือปฏิบัติจริง (Hands-on Engineering) ตั้งแต่การเขียน Node สื่อสารผ่าน DDS Middleware, การสร้างโมเดล kinematic 3D ด้วย URDF/Xacro, การจำลองฟิสิกส์และเซนเซอร์ใน **Gazebo Sim (Harmonic)**, การแปลงพิกัดด้วย **TF2**, การสร้างแผนที่ **2D SLAM** ไปจนถึงการควบคุมนำทางหลบสิ่งกีดขวางอัตโนมัติด้วย **Nav2 Stack**

```
┌────────────────────────────────────────────────────────────────────────┐
│                        โครงสร้างหลักสูตร 6 โมดูล                        │
├───────────────────┬───────────────────┬────────────────────────────────┤
│ 01_ROS2_Core      │ 02_Modeling_TF2   │ 03_Gazebo_Simulation           │
│ • Nodes, DDS, QoS │ • URDF & Xacro    │ • Gazebo Sim (Harmonic)        │
│ • Topics/Services │ • REP 103 / 105   │ • ros_gz_bridge                │
│ • Actions/Params  │ • TF2 Tree Frames │ • Physics & Sensor Simulation  │
├───────────────────┼───────────────────┼────────────────────────────────┤
│ 04_SLAM_Mapping   │ 05_Nav2_Navigation│ 06_Capstone_Project            │
│ • SLAM Toolbox    │ • AMCL Localization│ • Full Warehouse AMR System   │
│ • Graph SLAM      │ • Costmap 2D      │ • Waypoint Order Dispatcher    │
│ • Loop Closure    │ • DWB & NavFn     │ • Production Deployment & Test │
└───────────────────┴───────────────────┴────────────────────────────────┘
```

---

## 📂 โครงสร้างไดเรกทอรี (Repository Structure)

| ไดเรกทอรี | รายละเอียดเนื้อหาและปฏิบัติการ | ใบงานแล็บ |
|---|---|---|
| [`01_ROS2_Core/`](01_ROS2_Core/) | สถาปัตยกรรม ROS 2, DDS Middleware, Node lifecycle, Topics, Services, Actions, Parameters, Launch System | [`01_ROS2_Core/Lab_Exercises.md`](01_ROS2_Core/Lab_Exercises.md) |
| [`02_Modeling_TF2/`](02_Modeling_TF2/) | การสร้างโมเดลหุ่นยนต์ 3 มิติ (URDF/Xacro), การคำนวณ Inertia, การจัดการ Coordinate Frames ด้วย TF2 | [`02_Modeling_TF2/Lab_Exercises.md`](02_Modeling_TF2/Lab_Exercises.md) |
| [`03_Gazebo_Simulation/`](03_Gazebo_Simulation/) | การจำลองใน Gazebo Harmonic, การต่อ Plugin มอเตอร์/เซนเซอร์, การสร้าง SDF World และการ Bridge ท็อปปิก | [`03_Gazebo_Simulation/Lab_Exercises.md`](03_Gazebo_Simulation/Lab_Exercises.md) |
| [`04_SLAM_Mapping/`](04_SLAM_Mapping/) | การสร้างแผนที่ 2D Occupancy Grid ด้วย SLAM Toolbox, Scan Matching และการบันทึกไฟล์ PGM/YAML | [`04_SLAM_Mapping/Lab_Exercises.md`](04_SLAM_Mapping/Lab_Exercises.md) |
| [`05_Nav2_Navigation/`](05_Nav2_Navigation/) | ระบบนำทางอัตโนมัติ Nav2 Stack, AMCL Localization, Costmaps 2D, Path Planning และ Waypoint Patrol | [`05_Nav2_Navigation/Lab_Exercises.md`](05_Nav2_Navigation/Lab_Exercises.md) |
| [`06_Capstone_Project/`](06_Capstone_Project/) | โครงงานบูรณาการ AMR คลังสินค้า: รับออเดอร์ ขับหลบสิ่งกีดขวาง ลาดตระเวนจุดตรวจ และเข้าแท่นชาร์จไฟ | [`06_Capstone_Project/Readme.md`](06_Capstone_Project/Readme.md) |
| [`docker/`](docker/) | สภาพแวดล้อม Docker Container ติดตั้ง ROS 2 Jazzy + Gazebo Sim + Nav2 + RViz2 พร้อมใช้งาน | [`docker/README.md`](docker/README.md) |

---

## ⚡ เริ่มต้นใช้งานด่วน (Quick Start with Docker)

ระบบทั้งหมดสามารถรันผ่าน Docker ที่เตรียมไว้ให้ โดยไม่ต้องติดตั้ง ROS 2 หรือ Gazebo บน Host OS:

### 1. เข้าสู่ Container สภาพแวดล้อมแล็บ
```bash
cd docker
./run_lab.sh
```

### 2. ทดสอบคอมไพล์และ Source Workspace
```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### 3. รันการทดสอบโมเดลและระบบจำลอง
```bash
# ทดสอบดูโมเดลหุ่นยนต์ใน RViz2
ros2 launch 02_Modeling_TF2/launch/display_urdf.launch.py

# เปิดโลกจำลอง Gazebo Sim พร้อมหุ่นยนต์และต่อ Bridge
ros2 launch 03_Gazebo_Simulation/launch/gazebo_world.launch.py
```

---

## 📖 แผนการเรียนรู้รายสัปดาห์ (16-Week Syllabus)

ศึกษาตารางแผนการจัดการเรียนรู้รายสัปดาห์ วัตถุประสงค์เชิงพฤติกรรม และเกณฑ์การประเมินผลฉบับสมบูรณ์ได้ที่:  
👉 [**`weekly_curriculum.md`**](weekly_curriculum.md)
