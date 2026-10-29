# 🛠️ ใบงานปฏิบัติการที่ 2: ระบบการมองเห็นและการตรวจจับวัตถุด้วย AI & AprilTag
**วิชา:** AMR-201 Advanced ROS 2 & Industrial Fleet Robotics  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** ขั้นสูง (Advanced)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายบทที่ 2](README.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. รันโหนดตรวจจับวัตถุ [`object_detector_node.py`](src/object_detector_node.py) (`ros2 run amr_adv02 object_detector`) ที่แปลงภาพด้วย `cv_bridge` และ publish `vision_msgs/Detection2DArray`
2. รันโหนดตรวจจับแท่นชาร์จ [`apriltag_dock_tracker.py`](src/apriltag_dock_tracker.py) และตรวจสอบ `PoseStamped` บน `/detected_dock_pose` เทียบกับค่าจริง
3. ส่งภาพกล้องความละเอียด $640 \times 480$ เข้าสู่ระบบ ROS 2 ด้วยกล้องสังเคราะห์ [`synthetic_tag_camera.py`](src/synthetic_tag_camera.py) (รู้ค่า $\mathbf{K}$ และท่าทางของแท็กแน่นอน)
4. สังเกตและวิเคราะห์ผลของ QoS Policy (`sensor_data` = BEST_EFFORT) และความแม่นยำของ PnP ตามระยะ/มุม

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่ไดเรกทอรีรากของ repository
- ตรวจสอบความพร้อมของ OpenCV (มี `cv2.aruco`), `cv_bridge` และ `vision_msgs` ภายในคอนเทนเนอร์:
  ```bash
  ./docker/run_lab.sh python3 -c "import cv2, cv_bridge, vision_msgs; print('OpenCV', cv2.__version__, 'aruco:', hasattr(cv2, 'aruco'))"
  ```
- Build แพ็กเกจของบทนี้:
  ```bash
  ./docker/run_lab.sh colcon build --base-paths Essential_ROS Advanced_ROS --packages-up-to amr_adv02
  ```

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 2.1: รัน Vision Pipeline และระบบตรวจจับวัตถุ
1. Terminal 1 — รันกล้องสังเคราะห์ + tracker + detector (แท็กอยู่ที่ x = 0.10, y = 0.05, z = 0.80 m หมุน 15°):
   ```bash
   ./docker/run_lab.sh ros2 launch amr_adv02 vision_pipeline.launch.py
   ```
   *สังเกต Log:* `Object detector ready: classical HSV colour + contour detector (no neural network)` และ `tag 0: x=+0.100 y=+0.050 z=0.801 m  yaw=+15.1 deg`
2. Terminal 2 — ตรวจสอบหัวข้อ, QoS และอัตราเฟรม:
   ```bash
   ./docker/run_lab.sh ros2 topic list
   ./docker/run_lab.sh ros2 topic info -v /camera/image_raw
   ./docker/run_lab.sh ros2 topic hz /camera/image_raw
   ```
3. ตรวจสอบผลการตรวจจับวัตถุ (สังเกต `header.stamp` ต้องตรงกับภาพ, `bbox` เป็นพิกเซล):
   ```bash
   ./docker/run_lab.sh ros2 topic echo --once /perception/detections
   ```

**คำถาม Checkpoint 2.1:**
- ทำไม `score` ของ `safety_cone` จึงได้ประมาณ 0.50 และ `pallet_cargo` ประมาณ 0.98? ค่านี้เป็นความน่าจะเป็นหรือไม่?
- หาก subscriber ของภาพใช้ QoS RELIABLE จะเชื่อมต่อกับ publisher แบบ BEST_EFFORT ได้หรือไม่?

---

### 🔹 Lab 2.2: AprilTag Dock Tracker และความแม่นยำของ PnP
1. เทียบ pose ที่ตรวจได้กับค่าจริง (ground truth) แบบเฟรมต่อเฟรม:
   ```bash
   ./docker/run_lab.sh ros2 topic echo --once /detected_dock_pose
   ./docker/run_lab.sh ros2 run amr_adv02 pose_error_monitor --ros-args -p count:=10
   ```
2. ปิด launch แล้วลองท่าทางอื่น บันทึก error ในตาราง: (z = 0.4, 0.8, 1.2, 1.6 m) × (yaw = 0°, 30°)
   ```bash
   ./docker/run_lab.sh ros2 launch amr_adv02 vision_pipeline.launch.py tag_z:=1.6 tag_yaw_deg:=0.0
   ```
3. นำแท็กออกจากภาพ แล้วยืนยันว่า **ไม่มี** pose ถูก publish (tracker เดิมส่ง z = 0.8 m ทุกเฟรมแม้ไม่มีแท็ก):
   ```bash
   ./docker/run_lab.sh ros2 launch amr_adv02 vision_pipeline.launch.py tag_visible:=false
   ./docker/run_lab.sh timeout 5 ros2 topic echo /detected_dock_pose
   ```

**คำถาม Checkpoint 2.2:**
- หากแท่นชาร์จอยู่ห่างจากกล้อง 1.2 เมตรในแนวแกน $Z$ ของกล้อง และอยู่เยื้องไปทางขวา 0.15 เมตร ค่าพิกัด $(x, y, z)$ ใน `PoseStamped` จะมีค่าเท่าใดตามมาตรฐานพิกัด Optical Frame? ทดลองด้วย `tag_x:=0.15 tag_y:=0.0 tag_z:=1.2` แล้วเทียบคำตอบ
- จากตาราง error ในข้อ 2: ระยะและมุมแบบใดทำให้ "มุม" ของแท็กคลาดเคลื่อนมากที่สุด เพราะเหตุใด?

---

### 🔹 Lab 2.3: รันชุดทดสอบอัตโนมัติ
```bash
./docker/run_lab.sh bash -c "colcon test --base-paths Advanced_ROS --packages-select amr_adv02 \
    --event-handlers console_direct+ ; colcon test-result --verbose"
```

### 🔹 Lab 2.4 (เสริม): สลับไปใช้ YOLO จริง
ทำตามหัวข้อ "แบบฝึกหัดเสริม: เปลี่ยนเป็น YOLO จริง" ใน [README](README.md) บนเครื่องที่ติดตั้ง Ultralytics ได้ แล้วส่งภาพจริงด้วย `image_publisher`

---

## 📟 ผลการรันจริง (Real Run Output)
บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29 — ผลเต็มที่ [`results/vision_pipeline.txt`](results/vision_pipeline.txt)

```console
$ ros2 topic info -v /camera/image_raw | grep -E 'Node name|Reliability|Topic type|count'
Publisher count: 1
Node name: synthetic_tag_camera
Node namespace: /
Topic type: sensor_msgs/msg/Image
  Reliability: BEST_EFFORT
Subscription count: 2
Node name: apriltag_dock_tracker
Node namespace: /
Topic type: sensor_msgs/msg/Image
  Reliability: BEST_EFFORT
Node name: object_detector
Node namespace: /
Topic type: sensor_msgs/msg/Image
  Reliability: BEST_EFFORT

$ ros2 run amr_adv02 pose_error_monitor --ros-args -p count:=10
stamp 1793246196.970792411 detected z=0.8010 m truth z=0.8000 m | position error   0.99 mm  rotation error  0.23 deg
...
10 frames: position error mean 0.99 mm max 0.99 mm | rotation error mean 0.23 deg max 0.23 deg
```

---

## 📊 เกณฑ์การให้คะแนน (Evaluation Rubrics)
| รายการประเมิน | คะแนนเต็ม | เกณฑ์การพิจารณา |
| :--- | :---: | :--- |
| **1. ความเข้าใจการแปลงข้อมูล cv_bridge** | 30 | อธิบายการแปลงระหว่าง ROS Image และ OpenCV Mat ได้ถูกต้อง |
| **2. ความถูกต้องในการคำนวณ 6-DoF Pose** | 35 | ตอบคำถาม Checkpoint และอธิบายแกนพิกัด optical frame ได้ถูกต้อง |
| **3. การปรับแต่ง QoS สำหรับภาพ** | 20 | อธิบายเหตุผลการใช้ Best Effort และ Queue Depth ต่ำได้ถูกต้อง |
| **4. ความเรียบร้อยและการบันทึกผล** | 15 | ผลการทดลองและบันทึกครบถ้วนตามขั้นตอน |
| **รวม** | **100** | |
