# 🛠️ ใบงานปฏิบัติการที่ 1: การกำหนดค่าและควบคุมหุ่นยนต์ด้วย ros2_control
**วิชา:** AMR-201 Advanced ROS 2 & Industrial Fleet Robotics  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** ขั้นสูง (Advanced)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายบทที่ 1](README.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. วิเคราะห์และแก้ไขไฟล์คอนฟิกคอนโทรลเลอร์ [`config/diff_drive_controller.yaml`](config/diff_drive_controller.yaml) เพื่อปรับแต่งคุณลักษณะการเคลื่อนที่ของหุ่นยนต์
2. ตรวจสอบไวยากรณ์ Xacro/URDF ใน [`urdf/diff_drive_ros2_control.xacro`](urdf/diff_drive_ros2_control.xacro) และทำความเข้าใจ `<ros2_control>` tag (mock vs Gazebo)
3. รัน Controller Manager กับ `mock_components/GenericSystem` และสั่งงาน/ตรวจสอบผ่าน ROS 2 Control CLI
4. คำนวณความเร็วรอบของล้อเทียบกับข้อมูล Odometry ที่คำนวณได้จริงจากคอนโทรลเลอร์

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่ไดเรกทอรีรากของ repository (โฟลเดอร์ที่มี `docker/run_lab.sh`)
- ตรวจสอบความพร้อมของแพ็กเกจ `ros2_control` ภายใน Docker:
  ```bash
  ./docker/run_lab.sh bash -c "ros2 pkg list | grep -E '^(controller_manager|diff_drive_controller|gz_ros2_control)$'"
  ```
- Build แพ็กเกจของบทนี้ (ทำครั้งเดียว และทำใหม่ทุกครั้งที่แก้ไฟล์):
  ```bash
  ./docker/run_lab.sh colcon build --base-paths Essential_ROS Advanced_ROS --packages-up-to amr_adv01
  ```
  `run_lab.sh` จะ `source install/setup.bash` ให้อัตโนมัติ คำสั่ง `ros2 launch amr_adv01 ...` จึงใช้ได้ทันที
- เปิด 2 Terminal ด้วย `./docker/run_lab.sh` (ทุก Terminal ใช้ `ROS_DOMAIN_ID` เดียวกัน)

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 1.1: ตรวจสอบและวิเคราะห์ไฟล์คอนฟิก Controller Manager
1. เปิดดูเนื้อหาในไฟล์คอนฟิกคอนโทรลเลอร์:
   ```bash
   cat Advanced_ROS/01_ros2_control_Hardware/config/diff_drive_controller.yaml
   ```
2. สังเกตพารามิเตอร์สำคัญ:
   - `update_rate: 50` (ความถี่ของ Control Loop คือ 50 Hz หรือทุกๆ 20 ms)
   - `wheel_separation: 0.24` (ระยะห่างระหว่างล้อ 24 เซนติเมตร) และ `wheel_radius: 0.08` (รัศมีล้อ 8 เซนติเมตร)
   - `linear.x.max_velocity: 0.5` และ `angular.z.max_velocity: 2.0` — ลิมิตถูกเลือกให้ล้อหมุนไม่เกิน ±10 rad/s ตามลิมิตใน xacro (กรณีแย่สุด 9.25 rad/s)
   - ไม่มี `use_stamped_vel` แล้ว: ใน Jazzy คอนโทรลเลอร์รับเฉพาะ `TwistStamped` ที่ `/diff_drive_controller/cmd_vel`
   - ลิมิตใดไม่ต้องการให้ละไว้ (ค่าเริ่มต้น `NaN` = ปิด) แทน `has_velocity_limits` ที่ deprecated

**คำถาม Checkpoint 1.1:**
- หากเปลี่ยนเส้นผ่านศูนย์กลางล้อของหุ่นยนต์จาก 16 cm เป็น 20 cm จะต้องปรับพารามิเตอร์ใด (ทั้งใน YAML และ xacro) และมีค่าเท่าใด? ลิมิต `linear.x.max_velocity` สูงสุดที่ยังไม่ทำให้ล้อเกิน 10 rad/s (เมื่อ $\omega = 0$) คือเท่าใด?

---

### 🔹 Lab 1.2: ตรวจสอบการนิยาม Hardware Interface ใน URDF/Xacro
1. แปลง xacro เป็น URDF ทั้ง 2 โหมด แล้วตรวจไวยากรณ์ด้วย `check_urdf`:
   ```bash
   ./docker/run_lab.sh bash -c "xacro Advanced_ROS/01_ros2_control_Hardware/urdf/diff_drive_ros2_control.xacro \
       controllers_file:=/tmp/c.yaml > /tmp/mock.urdf && check_urdf /tmp/mock.urdf && grep -A3 '<hardware>' /tmp/mock.urdf"
   ./docker/run_lab.sh bash -c "xacro Advanced_ROS/01_ros2_control_Hardware/urdf/diff_drive_ros2_control.xacro \
       use_mock_hardware:=false | grep -B1 -A3 'plugin'"
   ```
2. ตอบคำถามเชิงโครงสร้าง:
   - Command Interface ที่ส่งไปยังล้อแต่ละข้างคือประเภทใด? (`velocity` หรือ `position`)
   - State Interfaces ที่รับกลับมาจาก Encoders มีกี่ตัว และประเภทใดบ้าง?
   - เมื่อ `use_mock_hardware:=false` มีอะไรเพิ่มเข้ามาใน URDF และทำไม Gazebo จึงต้องรู้ path ของ YAML?

---

### 🔹 Lab 1.3: รัน ros2_control ด้วย Mock Hardware และสั่งงานผ่าน CLI
1. Terminal 1 — เปิด controller_manager + mock hardware + spawners:
   ```bash
   ./docker/run_lab.sh ros2 launch amr_adv01 mock_diff_drive.launch.py
   ```
2. Terminal 2 — ตรวจสอบสถานะ:
   ```bash
   ./docker/run_lab.sh ros2 control list_controllers
   ./docker/run_lab.sh ros2 control list_hardware_interfaces
   ./docker/run_lab.sh ros2 topic info /diff_drive_controller/cmd_vel
   ```
3. ส่งคำสั่ง `TwistStamped` (เดินหน้า 0.5 m/s เลี้ยว 0.2 rad/s) ต่อเนื่อง 10 Hz แล้วดูความเร็วล้อ — กด `Ctrl+C` เพื่อหยุด (ล้อจะหยุดเองหลัง `cmd_vel_timeout` 0.5 s):
   ```bash
   ./docker/run_lab.sh ros2 topic pub -r 10 /diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped \
       "{header: {frame_id: base_footprint}, twist: {linear: {x: 0.5}, angular: {z: 0.2}}}"
   ./docker/run_lab.sh ros2 topic echo --once /joint_states        # (อีก Terminal ระหว่าง pub ทำงาน)
   ./docker/run_lab.sh ros2 topic echo --once /diff_drive_controller/odom
   ```
4. ตรวจสอบสมการจลนศาสตร์อัตโนมัติ (ส่ง v = 0.5 m/s, ω = 1.0 rad/s เป็นเวลา 3 s แล้วเทียบผล):
   ```bash
   ./docker/run_lab.sh ros2 run amr_adv01 diff_drive_ik 0.5 1.0
   ./docker/run_lab.sh ros2 run amr_adv01 twist_ik_check --ros-args -p v:=0.5 -p omega:=1.0
   ```
5. ลองส่ง `Twist` ไปที่ `/cmd_vel` แบบเดิม แล้วอธิบายว่าทำไมหุ่นไม่ขยับ (`ros2 topic info /cmd_vel`)

**คำถาม Checkpoint 1.3:**
- จากข้อ 3 คำนวณ $\omega_L, \omega_R$ ด้วยมือ แล้วเทียบกับค่าใน `/joint_states`
- ทำไม `odom pose` ของ `twist_ik_check` จึงไม่ได้อยู่ที่ yaw = 3.0 rad (171.9°) พอดีหลังส่ง ω = 1.0 rad/s นาน 3 s? (ใบ้: `max_acceleration`)

---

### 🔹 Lab 1.4 (เสริม): หุ่นตัวเดียวกันใน Gazebo Sim ด้วย gz_ros2_control
```bash
./docker/run_lab.sh ros2 launch amr_adv01 gz_diff_drive.launch.py            # headless (server only)
./docker/run_lab.sh ros2 run amr_adv01 twist_ik_check --ros-args -p use_sim_time:=true
```
สังเกตว่า controller YAML และคำสั่ง `TwistStamped` ใช้ร่วมกันได้ทั้ง mock และ Gazebo — สิ่งที่เปลี่ยนมีเพียง `<plugin>` ใน `<ros2_control>`

---

### 🔹 Lab 1.5: รันชุดทดสอบอัตโนมัติ
```bash
./docker/run_lab.sh bash -c "colcon test --base-paths Advanced_ROS --packages-select amr_adv01 \
    --event-handlers console_direct+ ; colcon test-result --verbose"
```

---

## 📟 ผลการรันจริง (Real Run Output)
บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29 — ผลเต็มอยู่ที่ [`results/mock_ros2_control.txt`](results/mock_ros2_control.txt), [`results/gz_ros2_control.txt`](results/gz_ros2_control.txt) และ [`results/colcon_test.txt`](results/colcon_test.txt)

```console
$ ros2 run amr_adv01 twist_ik_check --ros-args -p v:=0.5 -p omega:=1.0
IK  expected : left =   4.750 rad/s   right =   7.750 rad/s
/joint_states: left =   4.750 rad/s   right =   7.750 rad/s
odom twist   : v =  0.500 m/s   omega =  1.000 rad/s
odom pose    : x =  0.147 m  y =  0.966 m  yaw =  159.86 deg
RESULT: PASS - wheel speeds match inverse kinematics
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
