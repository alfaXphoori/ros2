# 🛠️ ใบงานโครงงานบูรณาการ: การทดสอบระบบหุ่นยนต์คลังสินค้าแบบครบวงจร
**วิชา:** AMR-201 Advanced ROS 2 & Industrial Fleet Robotics  
**เวลาปฏิบัติการ:** 8 ชั่วโมง  
**ระดับ:** โครงงานจบรายวิชา (Capstone Project)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายโครงงาน](Readme.md) | [เกณฑ์การประเมิน 5 มิติ](rubrics.md)

---

## 🎯 วัตถุประสงค์ของใบงานโครงงาน (Capstone Tasks)
1. รันระบบหุ่นยนต์คลังสินค้าแบบบูรณาการผ่าน [`launch/full_warehouse_system.launch.py`](launch/full_warehouse_system.launch.py)
2. ตรวจสอบสถานะการเชื่อมต่อระหว่าง Gazebo Sim, ros_gz_bridge, TF2, และ Nav2 Stack
3. ปฏิบัติการทดสอบสถานการณ์จำลอง (Simulated Test Cases) ตาม KPI อุตสาหกรรม
4. บันทึกผลการทดสอบและจัดทำรายงานเพื่อเตรียมสอบป้องกันโครงงาน (Oral Defense)

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่ไดเรกทอรีโครงการ `/mnt/sda/ros`
- ตรวจสอบความพร้อมของไฟล์โลกจำลองและไฟล์โมเดลหุ่นยนต์:
  ```bash
  ./docker/run_lab.sh check_urdf Essential_ROS/02_Robot_Modeling_TF2/urdf/diff_drive_robot.urdf
  ```

---

## 🧪 ขั้นตอนการทดสอบระบบ (System Test Cases)

### 🔹 Test Case 1: One-Click System Bringup
1. รัน Master Launch File:
   ```bash
   ./docker/run_lab.sh ros2 launch Advanced_ROS/06_Capstone_Project/launch/full_warehouse_system.launch.py
   ```
2. ตรวจสอบการส่งสัญญาณ Topic ที่จำเป็น:
   ```bash
   ./docker/run_lab.sh ros2 topic list | grep -E "cmd_vel|scan|odom|tf"
   ```
   *เกณฑ์ผ่าน:* ต้องมี Topics ครบทั้ง 4 ตัว และไม่มี Error สีแดงใน Console Log

---

### 🔹 Test Case 2: การทดสอบ Kidnapped Robot และ Global Localization
1. สั่งให้หุ่นยนต์วิ่งเข้าสู่โหมดสุ่มสำรวจหรือระบุตำแหน่ง
2. จำลองการย้ายตำแหน่งหุ่นยนต์ในโลกจำลอง
3. สังเกตการกระจายตัวของอนุภาค Particle Filter ของ AMCL:
   ```bash
   ./docker/run_lab.sh ros2 topic echo --once /particle_cloud
   ```
   *เกณฑ์ผ่าน:* หุ่นยนต์สามารถลู่เข้าสู่ตำแหน่งจริงได้ภายในระยะเวลาไม่เกิน 15 วินาที

---

### 🔹 Test Case 3: การทดสอบการเบรกฉุกเฉิน (E-Stop Latency)
1. จำลองข้อมูลเซนเซอร์ LiDAR พบสิ่งกีดขวางในระยะ 0.20 เมตร
2. ตรวจสอบความเร็วที่สั่งการไปยังมอเตอร์:
   ```bash
   ./docker/run_lab.sh ros2 topic echo --once /cmd_vel
   ```
   *เกณฑ์ผ่าน:* ค่า `linear.x` และ `angular.z` ต้องเป็น 0.0 ทันที

---

## 📊 สรุปการประเมินผลและการส่งงาน
- บันทึกคลิปวิดีโอสาธิตการทำงานตั้งแต่เริ่มเปิดระบบจนจบภารกิจ 1 ลูป (Pickup -> Dropoff -> Docking)
- บันทึกไฟล์ ROS Bag ของภารกิจ:
  ```bash
  ros2 bag record -o capstone_run /tf /scan /cmd_vel /amcl_pose
  ```
- ส่งมอบซอร์สโค้ดและรายงานทางเทคนิคตามเกณฑ์ [Rubrics](rubrics.md)
