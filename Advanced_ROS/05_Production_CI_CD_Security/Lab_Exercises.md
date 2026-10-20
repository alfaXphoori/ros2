# 🛠️ ใบงานปฏิบัติการที่ 5: การจัดการ Lifecycle State Machine และการทดสอบระบบอัตโนมัติ
**วิชา:** AMR-201 Advanced ROS 2 & Industrial Fleet Robotics  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** ขั้นสูง (Advanced)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายบทที่ 5](README.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. รันโหนด `lifecycle_laser_sensor.py` และสังเกตสถานะเริ่มต้น (`Unconfigured`)
2. ใช้คำสั่ง ROS 2 Lifecycle CLI ควบคุมการเปลี่ยนผ่านสถานะ (Transitions) จาก `configure` -> `activate` -> `deactivate` -> `cleanup`
3. พิสูจน์พฤติกรรมการบล็อกข้อมูลของ `LifecyclePublisher` เมื่ออยู่ในสถานะ `Inactive` เทียบกับ `Active`
4. รันชุดทดสอบอัตโนมัติด้วยคำสั่ง `pytest` และ `launch_testing`

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่ไดเรกทอรีโครงการ `/mnt/sda/ros`
- ตรวจสอบความพร้อมของแพ็กเกจ `lifecycle_msgs` และ `launch_testing`:
  ```bash
  ./docker/run_lab.sh ros2 interface list | grep -i lifecycle
  ```

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 5.1: รัน Lifecycle Sensor Node และตรวจสอบสถานะ
1. เปิด Terminal 1 รันโหนด Lifecycle Sensor:
   ```bash
   ./docker/run_lab.sh python3 Advanced_ROS/05_Production_CI_CD_Security/src/lifecycle_laser_sensor.py
   ```
   *สังเกต Log ข้อความ:* `💤 [LifecycleLaserSensor] Created in UNCONFIGURED state.`

2. เปิด Terminal 2 เพื่อตรวจสอบสถานะปัจจุบันผ่าน CLI:
   ```bash
   ./docker/run_lab.sh ros2 lifecycle get /lifecycle_laser_sensor
   ```
   *ผลลัพธ์ที่ได้:* `unconfigured [1]`

---

### 🔹 Lab 5.2: ควบคุมการเปลี่ยนสถานะและการส่งผ่านข้อมูล
1. สั่งตั้งค่าโหนดเข้าสู่สถานะ `Inactive`:
   ```bash
   ./docker/run_lab.sh ros2 lifecycle set /lifecycle_laser_sensor configure
   ```
2. ทดสอบดักฟังสัญญาณ Topic `/scan_managed`:
   ```bash
   ./docker/run_lab.sh ros2 topic echo /scan_managed
   ```
   *ข้อสังเกต:* ยังไม่มีข้อมูลใดๆ ส่งออกมา แม้โหนดจะสร้างตัวแปร Publisher เรียบร้อยแล้ว

3. สั่งเปิดใช้งานโหนดเต็มรูปแบบ (`Active`):
   ```bash
   ./docker/run_lab.sh ros2 lifecycle set /lifecycle_laser_sensor activate
   ```
   *ข้อสังเกต:* ข้อมูล LaserScan เริ่มพ่นออกมาอย่างต่อเนื่องที่ความถี่ 10 Hz!

4. สั่งหยุดการทำงานชั่วคราว (`Deactivate`):
   ```bash
   ./docker/run_lab.sh ros2 lifecycle set /lifecycle_laser_sensor deactivate
   ```
   *ข้อสังเกต:* ข้อมูลเลเซอร์หยุดส่งทันที

---

### 🔹 Lab 5.3: รันชุดทดสอบ Integration Test ด้วย launch_testing
1. รันการทดสอบอัตโนมัติ:
   ```bash
   ./docker/run_lab.sh pytest -v Advanced_ROS/05_Production_CI_CD_Security/tests/test_amr_launch.py
   ```
2. ตรวจสอบรายงานผลการทดสอบ (Pass/Fail)

**คำถาม Checkpoint 5.1:**
- หากเซนเซอร์ตรวจจับว่าอุณหภูมิของบอร์ดร้อนเกิน 85°C โค้ดควรเรียกใช้ Transition ใดเพื่อหยุดการทำงานของเซนเซอร์โดยไม่ต้องปิดโปรเซสทิ้ง?

---

## 📊 เกณฑ์การให้คะแนน (Evaluation Rubrics)
| รายการประเมิน | คะแนนเต็ม | เกณฑ์การพิจารณา |
| :--- | :---: | :--- |
| **1. ความเข้าใจวงจรชีวิต Lifecycle Node** | 35 | อธิบายและสาธิตการเปลี่ยนผ่านสถานะ 4 ขั้นตอนได้ถูกต้องครบถ้วน |
| **2. ความเข้าใจพฤติกรรม LifecyclePublisher** | 30 | อธิบายความแตกต่างของพฤติกรรมข้อมูลในสถานะ Inactive vs Active ได้ถูกต้อง |
| **3. ทักษะการรันชุดทดสอบ launch_testing** | 20 | สั่งรัน pytest และวิเคราะห์ผลการทดสอบระบบได้ถูกต้อง |
| **4. ความเรียบร้อยและการบันทึกผล** | 15 | บันทึก Log และตอบคำถาม Checkpoint ครบถ้วน |
| **รวม** | **100** | |
