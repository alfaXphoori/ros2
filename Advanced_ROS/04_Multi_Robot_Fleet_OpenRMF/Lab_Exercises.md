# 🛠️ ใบงานปฏิบัติการที่ 4: การจัดกลุ่มเนมสเปซและการประสานงานฝูงหุ่นยนต์
**วิชา:** AMR-201 Advanced ROS 2 & Industrial Fleet Robotics  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** ขั้นสูง (Advanced)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายบทที่ 4](README.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. รันไฟล์ Launch สำหรับฝูงหุ่นยนต์หลายตัว [`launch/multi_robot_fleet.launch.py`](launch/multi_robot_fleet.launch.py)
2. ตรวจสอบการแยกกลุ่ม Node, Topic และ TF Frame Prefix (`amr_01/` และ `amr_02/`)
3. วิเคราะห์ไฟล์คอนฟิก Open-RMF Fleet Adapter [`config/fleet_adapter_config.yaml`](config/fleet_adapter_config.yaml)
4. ทดสอบส่งคำสั่งควบคุมหุ่นยนต์แยกตัวแบบเป็นอิสระต่อกัน

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่ไดเรกทอรีโครงการ `/mnt/sda/ros`
- ตรวจสอบความพร้อมของระบบ Launch:
  ```bash
  ./docker/run_lab.sh ros2 launch --help
  ```

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 4.1: รันระบบ Multi-Robot Fleet Launch
1. สั่งรันไฟล์ Launch ของฝูงหุ่นยนต์:
   ```bash
   ./docker/run_lab.sh ros2 launch Advanced_ROS/04_Multi_Robot_Fleet_OpenRMF/launch/multi_robot_fleet.launch.py
   ```
2. เปิดอีก Terminal เพื่อตรวจสอบรายชื่อ Node:
   ```bash
   ./docker/run_lab.sh ros2 node list
   ```
   *ผลลัพธ์ที่คาดหวัง:* จะต้องพบโหนด `/amr_01/robot_state_publisher` และ `/amr_02/robot_state_publisher`

---

### 🔹 Lab 4.2: ตรวจสอบการแยกพิกัด TF2 Frame Tree
1. ตรวจสอบ TF Frames ทั้งหมดในระบบ:
   ```bash
   ./docker/run_lab.sh ros2 run tf2_ros tf2_echo amr_01/base_link amr_01/left_wheel_link
   ```
2. ตรวจสอบว่า `amr_02/` มีชุดพิกัดแยกเป็นของตัวเอง

**คำถาม Checkpoint 4.1:**
- หากต้องการให้หุ่นยนต์ตัวที่ 3 (`amr_03`) เข้าร่วมฝูง จะต้องเพิ่มคำสั่งใดลงในไฟล์ Launch?

---

### 🔹 Lab 4.3: วิเคราะห์คอนฟิก Open-RMF Fleet Adapter
1. ตรวจสอบไฟล์คอนฟิก:
   ```bash
   cat Advanced_ROS/04_Multi_Robot_Fleet_OpenRMF/config/fleet_adapter_config.yaml
   ```
2. ตอบคำถามเชิงวิศวกรรม:
   - หุ่นยนต์ `amr_01` ถูกกำหนดให้ไปชาร์จที่สถานีใด?
   - ระดับแบตเตอรี่ขั้นต่ำที่ระบบจะบังคับส่งหุ่นยนต์กลับไปชาร์จไฟ (`recharge_threshold`) มีค่ากี่เปอร์เซ็นต์?

---

## 📊 เกณฑ์การให้คะแนน (Evaluation Rubrics)
| รายการประเมิน | คะแนนเต็ม | เกณฑ์การพิจารณา |
| :--- | :---: | :--- |
| **1. ความเข้าใจการแยก Namespacing และ TF Prefix** | 35 | อธิบายและสาธิตการแยกสัญญาณ Topic และ TF Tree ได้ถูกต้อง |
| **2. ความถูกต้องในการวิเคราะห์โครงสร้าง Open-RMF** | 35 | ตอบคำถาม Checkpoint และอธิบายบทบาทของ Fleet Adapter ได้ชัดเจน |
| **3. ทักษะการใช้ CLI ตรวจสอบ Multi-Robot** | 20 | ใช้คำสั่ง `node list`, `topic list`, และ `tf2_echo` ตรวจสอบสถานะได้คล่องแคล่ว |
| **4. ความเรียบร้อยและการบันทึกผล** | 10 | บันทึกผลการทดลองและตอบคำถามครบถ้วน |
| **รวม** | **100** | |
