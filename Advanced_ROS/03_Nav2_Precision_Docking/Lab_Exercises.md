# 🛠️ ใบงานปฏิบัติการที่ 3: การกำหนดค่าและการทดสอบระบบนำทางเข้าแท่นชาร์จความแม่นยำสูง
**วิชา:** AMR-201 Advanced ROS 2 & Industrial Fleet Robotics  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** ขั้นสูง (Advanced)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายบทที่ 3](README.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. วิเคราะห์และปรับพารามิเตอร์ใน [`config/docking_server_params.yaml`](config/docking_server_params.yaml) รวมถึง dock database
2. รัน Nav2 Docking Server จริงแบบ headless (fake base + กล้องสังเคราะห์ + AprilTag tracker ของบทที่ 2) แล้วส่ง Action `DockRobot` / `UndockRobot`
3. วัดความคลาดเคลื่อนการจอดเทียบกับตำแหน่งจริง และเปรียบเทียบการจอดแบบใช้/ไม่ใช้กล้อง
4. วิเคราะห์และตรวจสอบ Behavior Tree XML ใน [`behavior_trees/dock_and_charge_bt.xml`](behavior_trees/dock_and_charge_bt.xml) และออกแบบกลยุทธ์การกู้คืนเมื่อไม่พบมาร์กเกอร์

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่ไดเรกทอรีรากของ repository
- ตรวจสอบความพร้อมของแพ็กเกจ Nav2 Docking Server ใน Docker:
  ```bash
  ./docker/run_lab.sh bash -c "ros2 pkg list | grep docking"
  ```
- Build แพ็กเกจของบทนี้ (จะ build `amr_adv02` ที่เป็น dependency ให้ด้วย):
  ```bash
  ./docker/run_lab.sh colcon build --base-paths Essential_ROS Advanced_ROS --packages-up-to amr_adv03
  ```

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 3.1: ตรวจสอบพารามิเตอร์ของ Docking Server และ Action Interface
1. ตรวจสอบไฟล์คอนฟิก: หา `dock_plugins`, `docks`, `home_dock.pose`, `docking_threshold`, `external_detection_*`
   ```bash
   cat Advanced_ROS/03_Nav2_Precision_Docking/config/docking_server_params.yaml
   ```
2. ตรวจสอบ Action Types (Jazzy ใช้ `nav2_msgs` — ไม่มีแพ็กเกจ `opennav_docking_msgs`) สังเกตฟิลด์ใน Request, Result (error codes 901–999) และ Feedback (state):
   ```bash
   ./docker/run_lab.sh ros2 interface show nav2_msgs/action/DockRobot
   ./docker/run_lab.sh ros2 interface show nav2_msgs/action/UndockRobot
   ```

**คำถาม Checkpoint 3.1:**
- `dock_plugins` กับ `docks` ต่างกันอย่างไร? หากส่ง `dock_id: simple_charging_dock` จะได้ error code ใด?
- หากแท่นชาร์จมีมุมเอียงทำมุม 180 องศากับหัวหุ่นยนต์ (หุ่นยนต์ต้องหันก้นเข้าชาร์จ) ต้องตั้ง `dock_backwards` และ `staging_x_offset` อย่างไร?

---

### 🔹 Lab 3.2: เข้าจอดจริงด้วย Vision-in-the-loop
1. Terminal 1:
   ```bash
   ./docker/run_lab.sh ros2 launch amr_adv03 docking_sim.launch.py
   ```
2. Terminal 2 — ตรวจ action server แล้วสั่ง Dock → วัดผล → Undock:
   ```bash
   ./docker/run_lab.sh ros2 action list
   ./docker/run_lab.sh ros2 topic hz /detected_dock_pose
   ./docker/run_lab.sh ros2 run amr_adv03 dock_client
   ```
   หรือสั่งด้วย CLI โดยตรง:
   ```bash
   ./docker/run_lab.sh ros2 action send_goal -f /dock_robot nav2_msgs/action/DockRobot \
       "{dock_id: 'home_dock', navigate_to_staging_pose: false}"
   ```
3. ทำซ้ำโดยเปลี่ยนสถานการณ์ แล้วบันทึกตาราง error (รวม lateral / longitudinal):
   ```bash
   ./docker/run_lab.sh ros2 launch amr_adv03 docking_sim.launch.py start_y:=0.12 start_yaw:=-0.2
   ./docker/run_lab.sh ros2 launch amr_adv03 docking_sim.launch.py dock_y:=0.2 dock_yaw:=0.3 start_yaw:=0.0
   ./docker/run_lab.sh ros2 run amr_adv03 dock_client --ros-args -p "true_dock:=[1.0, 0.2, 0.3]"
   ./docker/run_lab.sh ros2 launch amr_adv03 docking_sim.launch.py use_vision:=false   # เชื่อ dock DB อย่างเดียว
   ./docker/run_lab.sh ros2 launch amr_adv03 docking_sim.launch.py docking_threshold:=0.03
   ```
4. ระหว่างหุ่นยืนที่จุดเริ่มต้น ซ่อนแท็กแล้วสั่ง Dock: `ros2 param set /synthetic_tag_camera tag_visible false` → ควรได้ `FAILED_TO_DETECT_DOCK` (904) หลัง `initial_perception_timeout`

**คำถาม Checkpoint 3.2:**
- ทำไม error ตามแนวเข้าจอด (longitudinal) จึงใกล้เคียง `docking_threshold` เสมอ ขณะที่ lateral มีค่าเพียงไม่กี่มิลลิเมตร?
- เมื่อ `use_vision:=false` error เป็นเท่าใด และมาจากสาเหตุใด (ดู `db_error_y` ใน launch file)?
- `external_detection_translation_x: -0.40` เป็น "แขนโมเมนต์" ระหว่างแท็กกับจุดจอด หากมุม yaw ของแท็กที่ตรวจได้ผิด 2° จะทำให้ตำแหน่งจุดจอดผิดด้านข้างประมาณกี่มิลลิเมตร?

---

### 🔹 Lab 3.3: ตรวจสอบ Behavior Tree XML
1. ตรวจสอบโครงสร้างไฟล์และตรวจกับ BT node ที่ติดตั้งจริง:
   ```bash
   cat Advanced_ROS/03_Nav2_Precision_Docking/behavior_trees/dock_and_charge_bt.xml
   ./docker/run_lab.sh ros2 run amr_adv03 check_bt
   ```
2. ลองแก้ BT ให้ผิด (เช่น `min_battery="20.0"` หรือลบ `BTCPP_format="4"`) แล้วรัน `check_bt` อีกครั้ง
3. ตอบคำถามเชิงการออกแบบ:
   - หากเงื่อนไข `IsBatteryLow` คืนค่าเป็น `FAILURE` (แบตเตอรี่ยังเหลือ 80%) โหนดลูกในลำดับถัดไปของ `<Sequence>` จะถูกทำงานหรือไม่? เพราะเหตุใด?
   - ทำไม `DockRobot` ใน BT นี้ต้องตั้ง `navigate_to_staging_pose="false"`?
   - ออกแบบ Recovery: หาก `DockRobot` ล้มเหลวด้วย `FAILED_TO_DETECT_DOCK` ควรเพิ่มโหนดใด (เช่น `RecoveryNode` + `Spin`/`BackUp`) ไว้ตรงไหน?

### 🔹 Lab 3.4: รันชุดทดสอบอัตโนมัติ
```bash
./docker/run_lab.sh bash -c "colcon test --base-paths Advanced_ROS --packages-select amr_adv03 \
    --event-handlers console_direct+ ; colcon test-result --verbose"
```

---

## 📟 ผลการรันจริง (Real Run Output)
บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29 — ผลเต็มที่ [`results/docking_run.txt`](results/docking_run.txt) และ [`results/docking_scenarios.txt`](results/docking_scenarios.txt)

```console
$ ros2 launch amr_adv03 docking_sim.launch.py 
docked: error = 14.5 mm (lateral -0.6 mm, longitudinal -14.5 mm), yaw error = +0.79 deg
$ ros2 launch amr_adv03 docking_sim.launch.py start_y:=0.12 start_yaw:=-0.2
docked: error = 11.4 mm (lateral +3.0 mm, longitudinal -11.0 mm), yaw error = -1.60 deg
$ ros2 launch amr_adv03 docking_sim.launch.py dock_y:=0.2 dock_yaw:=0.3 start_yaw:=0.0
docked: error = 14.3 mm (lateral -0.9 mm, longitudinal -14.3 mm), yaw error = +0.83 deg
$ ros2 launch amr_adv03 docking_sim.launch.py start_x:=-0.3 start_y:=0.05 start_yaw:=0.0
docked: error = 14.3 mm (lateral +1.2 mm, longitudinal -14.3 mm), yaw error = -0.58 deg
$ ros2 launch amr_adv03 docking_sim.launch.py use_vision:=false
docked: error = 48.9 mm (lateral +47.5 mm, longitudinal -11.6 mm), yaw error = +1.55 deg
```

---

## 📊 เกณฑ์การให้คะแนน (Evaluation Rubrics)
| รายการประเมิน | คะแนนเต็ม | เกณฑ์การพิจารณา |
| :--- | :---: | :--- |
| **1. ความเข้าใจสถาปัตยกรรม Docking Server** | 35 | อธิบาย 4 ลำดับขั้นของกระบวนการ Docking ได้ถูกต้องชัดเจน |
| **2. ความถูกต้องในการวิเคราะห์ Behavior Tree** | 35 | วิเคราะห์กลไก Control Flow ของ Sequence และ Condition Nodes ได้ถูกต้อง |
| **3. การปรับแต่งค่าพารามิเตอร์ YAML** | 20 | ปรับแต่งพารามิเตอร์ได้สอดคล้องกับขนาดและข้อจำกัดของหุ่นยนต์ |
| **4. ความเรียบร้อยและการบันทึกผล** | 10 | บันทึกผลการทดลองและตอบคำถาม Checkpoint ครบถ้วน |
| **รวม** | **100** | |
