# 🛠️ ใบงานปฏิบัติการที่ 1: การกำหนดค่าและควบคุมหุ่นยนต์ด้วย ros2_control
**วิชา:** AMR-201 Advanced ROS 2 & Industrial Fleet Robotics  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** ขั้นสูง (Advanced)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายบทที่ 1](README.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. วิเคราะห์และแก้ไขไฟล์คอนฟิกคอนโทรลเลอร์ [`config/diff_drive_controller.yaml`](config/diff_drive_controller.yaml) เพื่อปรับแต่งคุณลักษณะการเคลื่อนที่ของหุ่นยนต์
2. ตรวจสอบไวยากรณ์ Xacro/URDF ใน [`urdf/diff_drive_ros2_control.xacro`](urdf/diff_drive_ros2_control.xacro) และทำความเข้าใจ `<ros2_control>` tag
3. สั่งงานและตรวจสอบสถานะของ Controller Manager ผ่าน ROS 2 Control CLI
4. คำนวณความเร็วรอบของล้อเทียบกับข้อมูล Odometry ที่คำนวณได้จริงจากคอนโทรลเลอร์

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่ไดเรกทอรีโครงการ `/mnt/sda/ros`
- ตรวจสอบความพร้อมของแพ็กเกจ `ros2_control` ภายใน Docker:
  ```bash
  ./docker/run_lab.sh ros2 pkg list | grep -E "controller_manager|diff_drive_controller"
  ```

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 1.1: ตรวจสอบและวิเคราะห์ไฟล์คอนฟิก Controller Manager
1. เปิดดูเนื้อหาในไฟล์คอนฟิกคอนโทรลเลอร์:
   ```bash
   cat Advanced_ROS/01_ros2_control_Hardware/config/diff_drive_controller.yaml
   ```
2. สังเกตพารามิเตอร์สำคัญ:
   - `update_rate: 50` (ความถี่ของ Control Loop คือ 50 Hz หรือทุกๆ 20 ms)
   - `wheel_separation: 0.24` (ระยะห่างระหว่างล้อ 24 เซนติเมตร)
   - `wheel_radius: 0.08` (รัศมีล้อ 8 เซนติเมตร)
   - `linear.x.max_velocity: 1.0` (ความเร็วสูงสุด 1.0 เมตร/วินาที)

**คำถาม Checkpoint 1.1:**
- หากเปลี่ยนเส้นผ่านศูนย์กลางล้อของหุ่นยนต์จาก 16 cm เป็น 20 cm จะต้องปรับพารามิเตอร์ใด และมีค่าเท่าใด?

---

### 🔹 Lab 1.2: ตรวจสอบการนิยาม Hardware Interface ใน URDF
1. เปิดดูไฟล์ Xacro ของระบบฮาร์ดแวร์:
   ```bash
   cat Advanced_ROS/01_ros2_control_Hardware/urdf/diff_drive_ros2_control.xacro
   ```
2. ตอบคำถามเชิงโครงสร้าง:
   - Command Interface ที่ส่งไปยังล้อแต่ละข้างคือประเภทใด? (`velocity` หรือ `position`)
   - State Interfaces ที่รับกลับมาจาก Encoders มีกี่ตัว และประเภทใดบ้าง?

---

### 🔹 Lab 1.3: จำลองการทำงานและการควบคุมผ่าน CLI
1. รันโหนด `joint_state_broadcaster` และจำลองคำสั่ง Twist:
   ```bash
   # ส่งคำสั่งทดสอบความเร็วเดินหน้า 0.5 m/s และเลี้ยว 0.2 rad/s
   ./docker/run_lab.sh ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}, angular: {z: 0.2}}"
   ```
2. ตรวจสอบการอัปเดตของ State Interface และ TF2 Transform:
   ```bash
   ./docker/run_lab.sh ros2 topic echo --once /joint_states
   ```

---

## 📊 เกณฑ์การให้คะแนน (Evaluation Rubrics)
| รายการประเมิน | คะแนนเต็ม | เกณฑ์การพิจารณา |
| :--- | :---: | :--- |
| **1. ความถูกต้องในการวิเคราะห์ YAML Config** | 30 | อธิบายหน้าที่ของแต่ละตัวแปรใน `diff_drive_controller.yaml` ได้ครบถ้วน |
| **2. ความเข้าใจ Hardware Interface Xacro** | 30 | ระบุความแตกต่างระหว่าง Command Interface และ State Interface ได้ถูกต้อง |
| **3. การคำนวณความเร็วรอบล้อตามจลนศาสตร์** | 25 | คำนวณค่า $\omega_L$ และ $\omega_R$ จากสมการความเร็วเชิงมุมได้ถูกต้อง |
| **4. ความเรียบร้อยและการบันทึกผล** | 15 | บันทึก Log และคำตอบ Checkpoint ครบถ้วน |
| **รวม** | **100** | |
