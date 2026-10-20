# 🛠️ ใบงานปฏิบัติการที่ 3: การกำหนดค่าและการทดสอบระบบนำทางเข้าแท่นชาร์จความแม่นยำสูง
**วิชา:** AMR-201 Advanced ROS 2 & Industrial Fleet Robotics  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** ขั้นสูง (Advanced)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายบทที่ 3](README.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. วิเคราะห์และทำความเข้าใจพารามิเตอร์ใน [`config/docking_server_params.yaml`](config/docking_server_params.yaml)
2. วิเคราะห์โครงสร้าง Behavior Tree XML ใน [`behavior_trees/dock_and_charge_bt.xml`](behavior_trees/dock_and_charge_bt.xml)
3. ทดสอบการส่ง Action Goal ผ่าน CLI สำหรับการสั่ง Dock และ Undock
4. ออกแบบกลยุทธ์การกู้คืน (Recovery Strategy) เมื่อหุ่นยนต์ไม่พบมาร์กเกอร์ของแท่นชาร์จ

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่ไดเรกทอรีโครงการ `/mnt/sda/ros`
- ตรวจสอบความพร้อมของแพ็กเกจ Nav2 Docking Server ใน Docker:
  ```bash
  ./docker/run_lab.sh ros2 pkg list | grep docking
  ```

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 3.1: ตรวจสอบและแก้ไขพารามิเตอร์ของ Docking Server
1. ตรวจสอบไฟล์คอนฟิก:
   ```bash
   cat Advanced_ROS/03_Nav2_Precision_Docking/config/docking_server_params.yaml
   ```
2. แก้ไขค่าพารามิเตอร์ในไฟล์ YAML:
   - ปรับ `dock_approach_timeout: 45.0` (วินาที)
   - ปรับ `docking_threshold: 0.02` (2 เซนติเมตร) เพื่อเพิ่มความแม่นยำ

**คำถาม Checkpoint 3.1:**
- หากแท่นชาร์จมีมุมเอียงทำมุม 180 องศากับหัวหุ่นยนต์ (หุ่นยนต์ต้องหันก้นเข้าชาร์จ) ค่า `staging_x_offset` ควรมีเครื่องหมายบวกหรือลบอย่างไร?

---

### 🔹 Lab 3.2: ตรวจสอบและจำลอง Behavior Tree XML
1. ตรวจสอบโครงสร้างไฟล์ Behavior Tree:
   ```bash
   cat Advanced_ROS/03_Nav2_Precision_Docking/behavior_trees/dock_and_charge_bt.xml
   ```
2. ตอบคำถามเชิงการออกแบบ:
   - หากเงื่อนไข `IsBatteryLow` คืนค่าเป็น `FAILURE` (แบตเตอรี่ยังเหลือ 80%) โหนดลูกในลำดับถัดไปของ `<Sequence>` จะถูกทำงานหรือไม่? เพราะเหตุใด?

---

### 🔹 Lab 3.3: ทดลองส่งคำสั่ง Action Goal จำลอง
1. ตรวจสอบ Action Types ของ Nav2 Docking:
   ```bash
   ./docker/run_lab.sh ros2 interface show opennav_docking_msgs/action/DockRobot
   ```
2. สังเกตฟิลด์ใน Request, Feedback และ Result

---

## 📊 เกณฑ์การให้คะแนน (Evaluation Rubrics)
| รายการประเมิน | คะแนนเต็ม | เกณฑ์การพิจารณา |
| :--- | :---: | :--- |
| **1. ความเข้าใจสถาปัตยกรรม Docking Server** | 35 | อธิบาย 4 ลำดับขั้นของกระบวนการ Docking ได้ถูกต้องชัดเจน |
| **2. ความถูกต้องในการวิเคราะห์ Behavior Tree** | 35 | วิเคราะห์กลไก Control Flow ของ Sequence และ Condition Nodes ได้ถูกต้อง |
| **3. การปรับแต่งค่าพารามิเตอร์ YAML** | 20 | ปรับแต่งพารามิเตอร์ได้สอดคล้องกับขนาดและข้อจำกัดของหุ่นยนต์ |
| **4. ความเรียบร้อยและการบันทึกผล** | 10 | บันทึกผลการทดลองและตอบคำถาม Checkpoint ครบถ้วน |
| **รวม** | **100** | |
