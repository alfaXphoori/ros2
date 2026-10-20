# 🛠️ ใบงานปฏิบัติการที่ 2: ระบบการมองเห็นและการตรวจจับวัตถุด้วย AI & AprilTag
**วิชา:** AMR-201 Advanced ROS 2 & Industrial Fleet Robotics  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** ขั้นสูง (Advanced)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายบทที่ 2](README.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. ทดสอบการรันโหนด `yolo_perception_node.py` และแปลงภาพด้วยไลบรารี `cv_bridge`
2. ทดสอบการรันโหนดตรวจจับแท่นชาร์จ `apriltag_dock_tracker.py` และตรวจสอบข้อความ PoseStamped
3. จำลองการส่งข้อมูลภาพกล้องความละเอียด $640 \times 480$ เข้าสู่ระบบ ROS 2
4. สังเกตและวิเคราะห์ผลกระทบของ QoS Policy ต่อน้ำหนักการประมวลผลของภาพ

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่ไดเรกทอรีโครงการ `/mnt/sda/ros`
- ตรวจสอบความพร้อมของแพ็กเกจ `cv_bridge` ภายในคอนเทนเนอร์:
  ```bash
  ./docker/run_lab.sh python3 -c "import cv2; import cv_bridge; print('OpenCV & cv_bridge OK')"
  ```

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 2.1: ทดสอบรัน Perception Node และระบบตรวจจับวัตถุ
1. รันโหนด `yolo_perception_node.py`:
   ```bash
   ./docker/run_lab.sh python3 Advanced_ROS/02_Vision_AI_Perception/src/cv_bridge_yolo_node.py
   ```
   *สังเกต Log ข้อความยืนยัน:* `👁️ [YoloPerceptionNode] Vision & AI Perception Pipeline ready.`

2. ในอีกหน้าต่าง Terminal จำลองการ Publish ภาพเข้าสู่ Topic `/camera/image_raw`
3. ตรวจสอบข้อมูลผลลัพธ์ที่โหนดตรวจจับได้:
   ```bash
   ./docker/run_lab.sh ros2 topic echo /perception/detected_objects
   ```

---

### 🔹 Lab 2.2: ทดสอบโหนดนำทางเข้าแท่นชาร์จ (AprilTag Dock Tracker)
1. รันโหนด `apriltag_dock_tracker.py`:
   ```bash
   ./docker/run_lab.sh python3 Advanced_ROS/02_Vision_AI_Perception/src/apriltag_dock_tracker.py
   ```
   *สังเกต Log ข้อความยืนยัน:* `🎯 [AprilTagDockTracker] Visual Dock Tracker active.`

2. ตรวจสอบการส่งพิกัดเป้าหมาย 6-DoF สู่ Nav2 Docking Server:
   ```bash
   ./docker/run_lab.sh ros2 topic echo /docking/target_pose
   ```

**คำถาม Checkpoint 2.1:**
- หากแท่นชาร์จอยู่ห่างจากกล้อง 1.2 เมตรในแนวแกน $Z$ ของกล้อง และอยู่เยื้องไปทางขวา 0.15 เมตร ค่าพิกัด $(x, y, z)$ ใน `PoseStamped` จะมีค่าเท่าใดตามมาตรฐานพิกัด Optical Frame?

---

## 📊 เกณฑ์การให้คะแนน (Evaluation Rubrics)
| รายการประเมิน | คะแนนเต็ม | เกณฑ์การพิจารณา |
| :--- | :---: | :--- |
| **1. ความเข้าใจการแปลงข้อมูล cv_bridge** | 30 | อธิบายการแปลงระหว่าง ROS Image และ OpenCV Mat ได้ถูกต้อง |
| **2. ความถูกต้องในการคำนวณ 6-DoF Pose** | 35 | ตอบคำถาม Checkpoint และอธิบายแกนพิกัด optical frame ได้ถูกต้อง |
| **3. การปรับแต่ง QoS สำหรับภาพ** | 20 | อธิบายเหตุผลการใช้ Best Effort และ Queue Depth ต่ำได้ถูกต้อง |
| **4. ความเรียบร้อยและการบันทึกผล** | 15 | ผลการทดลองและบันทึกครบถ้วนตามขั้นตอน |
| **รวม** | **100** | |
