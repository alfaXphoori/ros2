# 🛠️ ใบงานปฏิบัติการโมดูล 3: Gazebo Sim Hands-on Laboratory

---

## 📋 สารบัญการทดลอง
- [Lab 3.1: การเปิดโลกจำลอง Gazebo Sim](#lab-31-การเปิดโลกจำลอง-gazebo-sim)
- [Lab 3.2: การ Spawn หุ่นยนต์เข้าสู่โลกจำลอง](#lab-32-การ-spawn-หุ่นยนต์เข้าสู่โลกจำลอง)
- [Lab 3.3: การรัน ros_gz_bridge](#lab-33-การรัน-ros_gz_bridge)
- [Lab 3.4: การควบคุมหุ่นยนต์ด้วย Teleop และตรวจสอบเซนเซอร์](#lab-34-การควบคุมหุ่นยนต์ด้วย-teleop-และตรวจสอบเซนเซอร์)

---

## Lab 3.1: การเปิดโลกจำลอง Gazebo Sim

```bash
# เปิดโลกจำลองคลังสินค้าด้วย Gazebo Sim CLI
gz sim -r worlds/warehouse.sdf
```
สังเกตว่ากำแพง เสาโครงสร้าง และพื้นผิวจำลองปรากฏขึ้นพร้อมระบบฟิสิกส์ 1ms time-step

---

## Lab 3.2: การ Spawn หุ่นยนต์เข้าสู่โลกจำลอง

```bash
# Spawn โมเดล URDF หุ่นยนต์ลงในพิกัด (X=0, Y=0, Z=0.1)
ros2 run ros_gz_sim create \
  -name diff_drive_robot \
  -file ../02_Modeling_TF2/urdf/diff_drive_robot.urdf \
  -z 0.1
```

---

## Lab 3.3: การรัน ros_gz_bridge

```bash
# รัน parameter bridge ตามไฟล์คอนฟิก
ros2 run ros_gz_bridge parameter_bridge --ros-args \
  -p config_file:=config/ros_gz_bridge.yaml
```

---

## Lab 3.4: การควบคุมหุ่นยนต์ด้วย Teleop และตรวจสอบเซนเซอร์

เปิดอีกหนึ่ง Terminal เพื่อบังคับหุ่นยนต์:
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
และตรวจสอบข้อมูลเซนเซอร์ที่สะพานส่งมายัง ROS 2:
```bash
# ดูข้อมูล LaserScan จาก LiDAR
ros2 topic echo /scan --once

# ดูข้อมูล Odometry
ros2 topic echo /odom --once
```
