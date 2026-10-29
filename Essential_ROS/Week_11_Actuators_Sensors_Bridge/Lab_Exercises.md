# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 11: การต่อเชื่อมมอเตอร์ เซนเซอร์ และระบบ ros_gz_bridge
**วิชา:** AMR-101 Essential ROS 2 for Autonomous Mobile Robots  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** พื้นฐาน (Beginner)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายสัปดาห์ที่ 11](Readme.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. เปิดระบบจำลองแบบบูรณาการ **Gazebo Sim + Robot Spawner + ros_gz_bridge** ด้วยไฟล์ Launch เดียว
2. ตรวจสอบการไหลของข้อมูลข้ามแพลตฟอร์มทั้ง 5 ช่องสัญญาณหลัก (`/cmd_vel`, `/odom`, `/scan`, `/tf`, `/clock`)
3. วิเคราะห์โครงสร้างข้อมูลจากเซนเซอร์ LiDAR ในรูปแบบข้อความ `sensor_msgs/msg/LaserScan`
4. รันและทดสอบระบบม่านความปลอดภัย **Safety Shield & Emergency Stop** ในการตัดกำลังขับเคลื่อนเมื่อเจอสิ่งกีดขวาง

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่รูทไดเรกทอรีของ repository (เช่น `cd ~/ros`)
- Build แพ็กเกจของสัปดาห์นี้และแพ็กเกจที่ใช้ร่วม (`amr_week07` = URDF, `amr_week10` = โลกจำลอง):
  ```bash
  ./docker/run_lab.sh colcon build --base-paths Essential_ROS --packages-up-to amr_week11
  ```
  หลัง build แล้ว `run_lab.sh` จะ source `install/setup.bash` ให้อัตโนมัติ จึงใช้ `ros2 launch amr_week11 ...` / `ros2 run amr_week11 ...` ได้
- ถ้าใช้เครื่องร่วมกับผู้อื่น ให้แยกเครือข่ายก่อน: `export ROS_DOMAIN_ID=<เลขของคุณ> GZ_PARTITION=$USER ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 11.1: การเปิดระบบจำลองพร้อม Bridge (System Bringup)
**เป้าหมาย:** สังเกตการเชื่อมต่อระหว่าง Gazebo และ ROS 2 ผ่านคอนฟิก `ros_gz_bridge.yaml`

1. เปิด **Terminal 1** แล้วรันคำสั่งเปิดระบบ:
   ```bash
   ./docker/run_lab.sh ros2 launch amr_week11 gazebo_world.launch.py                 # มีจอ (GUI)
   ./docker/run_lab.sh ros2 launch amr_week11 gazebo_world.launch.py headless:=true  # ไม่มีจอ / Docker
   ```
   Launch file นี้เปิด Gazebo (โลกจาก `amr_week10`), `robot_state_publisher` (URDF จาก `amr_week07`, `use_sim_time:=true`), spawn หุ่นยนต์ และ `parameter_bridge`
   **ผลลัพธ์จริง (ตัดมาจาก log):**
   ```text
   [create-3] [INFO] [1793245680.218295952] [ros_gz_sim]: Entity creation successful.
   [parameter_bridge-4] [INFO] [1793245680.732352188] [ros_gz_bridge]: Creating ROS->GZ Bridge: [/cmd_vel (geometry_msgs/msg/Twist) -> /cmd_vel (gz.msgs.Twist)] (Lazy 0)
   [parameter_bridge-4] [INFO] [1793245680.734350137] [ros_gz_bridge]: Creating GZ->ROS Bridge: [/odom (gz.msgs.Odometry) -> /odom (nav_msgs/msg/Odometry)] (Lazy 0)
   [parameter_bridge-4] [INFO] [1793245680.736334377] [ros_gz_bridge]: Creating GZ->ROS Bridge: [/scan (gz.msgs.LaserScan) -> /scan (sensor_msgs/msg/LaserScan)] (Lazy 0)
   [parameter_bridge-4] [INFO] [1793245680.738257665] [ros_gz_bridge]: Creating GZ->ROS Bridge: [/tf (gz.msgs.Pose_V) -> /tf (tf2_msgs/msg/TFMessage)] (Lazy 0)
   [parameter_bridge-4] [INFO] [1793245680.740198050] [ros_gz_bridge]: Creating GZ->ROS Bridge: [/joint_states (gz.msgs.Model) -> /joint_states (sensor_msgs/msg/JointState)] (Lazy 0)
   [parameter_bridge-4] [INFO] [1793245680.741500599] [ros_gz_bridge]: Creating GZ->ROS Bridge: [/clock (gz.msgs.Clock) -> /clock (rosgraph_msgs/msg/Clock)] (Lazy 0)
   ```

2. เปิด **Terminal 2** แล้วตรวจสอบว่าท็อปปิกใน ROS 2 เปิดขึ้นครบหรือไม่:
   ```bash
   ./docker/run_lab.sh ros2 topic list
   ```
   *ตรวจสอบว่าปรากฏครบทั้ง:* `/cmd_vel`, `/odom`, `/scan`, `/clock`, `/tf`, `/tf_static`, `/joint_states`, `/robot_description`
3. ตรวจสอบว่า TF ต่อกันครบจาก `odom` ถึงเฟรมของ LiDAR (ถ้าไม่มี `robot_state_publisher` SLAM/Nav2 จะทิ้ง scan ทุกอัน เพราะ `/scan` มี `frame_id: lidar_link`):
   ```bash
   ./docker/run_lab.sh ros2 run tf2_ros tf2_echo odom lidar_link
   ```
   ผลจริง: `Translation: [0.080, -0.000, 0.175]` (LiDAR อยู่หน้าจุดศูนย์กลาง 8 cm สูงจากพื้น 17.5 cm)

---

### 🔹 Lab 11.2: การทดสอบขับเคลื่อนหุ่นยนต์ในโลกจำลอง
**เป้าหมาย:** ส่งคำสั่งจาก ROS ไปหมุนล้อของหุ่นยนต์ใน Gazebo

1. ใน **Terminal 2** ส่งคำสั่งความเร็วเดินหน้า $v = 0.3$ m/s:
   ```bash
   ./docker/run_lab.sh ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.3}}"
   ```
2. เปิด **Terminal 3** เพื่อดูค่า Odometry ที่ส่งกลับมาจากล้อใน Gazebo:
   ```bash
   ./docker/run_lab.sh ros2 topic echo /odom --field pose.pose.position
   ```
   *สังเกต:* พิกัดตำแหน่ง $x$ จะเพิ่มขึ้นอย่างต่อเนื่องตามการหมุนของล้อจริงในฟิสิกส์
3. หยุดการส่งคำสั่ง (กด `Ctrl+C` ที่ Terminal 2) แล้วส่งคำสั่งเบรก: `./docker/run_lab.sh ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"`
   (ปลั๊กอิน DiffDrive ของ Gazebo **จำคำสั่งล่าสุดไว้** ถ้าไม่ส่ง 0 หุ่นยนต์จะวิ่งต่อ)
4. เปรียบเทียบ Odometry กับตำแหน่งจริงในโลกจำลอง (ground truth จาก Gazebo):
   ```bash
   ./docker/run_lab.sh ros2 run amr_week11 ground_truth_pose
   ```

---

### 🔹 Lab 11.3: การวิเคราะห์ข้อมูลลำแสง LiDAR (LaserScan Inspection)
**เป้าหมาย:** ถอดรหัสโครงสร้างข้อความและวัดอัตราความถี่ของเซนเซอร์

1. ตรวจสอบความถี่ของท็อปปิก `/scan`:
   ```bash
   ./docker/run_lab.sh ros2 topic hz /scan
   ```
   *ค่าเฉลี่ยควรใกล้ 10 Hz ตาม `<update_rate>10</update_rate>` ของเซนเซอร์ใน URDF (วัดจริงได้ประมาณ 9.7–9.9 Hz)*

2. อ่านข้อมูลพารามิเตอร์ของ LiDAR สดจากท็อปปิก:
   ```bash
   ./docker/run_lab.sh ros2 topic echo --once /scan sensor_msgs/msg/LaserScan --field header
   ./docker/run_lab.sh ros2 topic echo --once /scan sensor_msgs/msg/LaserScan --field angle_min
   ./docker/run_lab.sh ros2 topic echo --once /scan sensor_msgs/msg/LaserScan --field angle_max
   ./docker/run_lab.sh ros2 topic echo --once /scan sensor_msgs/msg/LaserScan --field angle_increment
   ```
   (ระบุชนิดข้อความไว้ท้ายชื่อท็อปปิก เพื่อไม่ต้องรอ ros2 daemon ค้นหาชนิดของท็อปปิก)
   ผลจริงของ `--field header`: `frame_id: lidar_link` และ `ros2 topic hz /scan` วัดได้ `average rate: 9.888` (ตั้งไว้ `update_rate` 10 Hz ใน URDF)
   **คำถาม Checkpoint 11.3:**
   - [ ] จำนวนลำแสงทั้งหมดในอาเรย์ `ranges` มีกี่ค่า? (`len(msg.ranges)`)
   - [ ] ระยะวัดต่ำสุด (`range_min`) และสูงสุด (`range_max`) ของ LiDAR ตัวนี้มีค่าเท่าใด?

---

### 🔹 Lab 11.4: การทดสอบม่านความปลอดภัย (Safety Gate & Emergency Stop)
**เป้าหมาย:** สังเกตการทำงานของโหนดกั้นความเร็วอัตโนมัติเมื่อหุ่นยนต์เคลื่อนที่เข้าใกล้สิ่งกีดขวาง

`emergency_stop_node` เป็น **ประตูกั้น (gate)** ที่คั่นกลางระหว่างผู้สั่งงานกับหุ่นยนต์:
`teleop / สคริปต์ → /cmd_vel_in → [emergency_stop_node] → /cmd_vel → ros_gz_bridge → Gazebo`
ผู้สั่งงานจึงต้องส่งคำสั่งไปที่ `/cmd_vel_in` (ไม่ใช่ `/cmd_vel`) — ถ้าทั้งสองโหนดส่งเข้า `/cmd_vel` พร้อมกัน ข้อความที่มาทีหลังจะทับกัน (last-writer race) และคำสั่งเบรกจะถูกลบล้างภายในเสี้ยววินาที

1. ปิด launch เดิมแล้วเปิดใหม่พร้อม gate:
   ```bash
   ./docker/run_lab.sh ros2 launch amr_week11 gazebo_world.launch.py headless:=true estop:=true
   ```
   **ผลลัพธ์จริง:**
   ```text
   [emergency_stop_node-5] [INFO] [1793245680.135688811] [emergency_stop_node]: Safety gate ready: cmd_vel_in -> cmd_vel, stop distance 0.35 m, sector +-30 deg, scan timeout 0.5 s
   ```
   (หรือรันแยก: `./docker/run_lab.sh ros2 run amr_week11 emergency_stop_node --ros-args -p use_sim_time:=true`)

2. ใน **Terminal 2** ขับหุ่นยนต์ตรงไปยังกำแพงทิศตะวันออก (ผิวกำแพงอยู่ที่ $x = 4.9$ m) **ผ่าน `/cmd_vel_in`**:
   ```bash
   ./docker/run_lab.sh ros2 topic pub -r 10 /cmd_vel_in geometry_msgs/msg/Twist "{linear: {x: 0.3}}"
   ```
   หรือขับด้วยคีย์บอร์ด: `./docker/run_lab.sh ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel_in`

3. สังเกต log ของ gate เมื่อระยะด้านหน้าน้อยกว่า $0.35$ m (ผลจริง):
   ```text
   [emergency_stop_node-5] [WARN] [1793245723.268663174] [emergency_stop_node]: Obstacle at 0.33 m (< 0.35 m) in front: forward motion BLOCKED
   ```
   แม้ `/cmd_vel_in` ยังขอ 0.3 m/s อยู่ แต่ `/cmd_vel` ที่ออกไปจะเป็น `linear.x = 0.0` หุ่นยนต์หยุดที่ $x \approx 4.52$ m (ดูตารางเต็มใน [ผลการรันจริง](#-ผลการรันจริง-real-run-output))
   ส่วนการหมุนตัว (`angular.z`) และการถอยหลัง (`linear.x < 0`) ยังผ่านได้ เพื่อให้หุ่นยนต์หลบออกจากจุดอันตรายได้
4. **Fail-safe:** ถ้า `/scan` ขาดหายเกิน `scan_timeout` (0.5 s) gate จะส่ง 0 ทั้งหมด เพราะพิสูจน์ไม่ได้ว่าทางข้างหน้าว่าง

---

## 🏆 โจทย์ท้าทายระดับสูง (Challenge Exercises)
1. **Challenge 11.1:** ปรับปรุงโหนด Emergency Stop ให้มี **ระบบเตือนภัย 2 ระดับ (Two-zone Safety Field)**:
   - โซนเตือนภัย (Warning Zone: ระยะ $0.35 - 0.70$ m): ลดความเร็วลงครึ่งหนึ่ง ($50\%$)
   - โซนหยุดฉุกเฉิน (Brake Zone: ระยะ $< 0.35$ m): เบรกหยุดสนิททันที
   (เขียนเป็นฟังก์ชันบริสุทธิ์แบบ `gate_command()` แล้วเพิ่ม unit test ใน `test/test_emergency_stop.py`)
2. **Challenge 11.2:** เชื่อมต่อโหนดควบคุมด้วยคีย์บอร์ด `teleop_twist_keyboard` (remap `cmd_vel:=cmd_vel_in`) และทดลองขับหุ่นยนต์สำรวจรอบโกดัง
3. **Challenge 11.3:** ศึกษา `nav2_collision_monitor` ซึ่งเป็นโหนดทำหน้าที่เดียวกันในระดับ production (ใช้ในสัปดาห์ที่ 14–16: `cmd_vel_smoothed → collision_monitor → cmd_vel`) แล้วเปรียบเทียบกับ gate ของเรา

---

## 📦 สิ่งที่ต้องส่ง (Deliverables Checklist)
- [ ] ภาพบันทึกหน้าจอผลการรัน `ros2 topic list` แสดงท็อปปิกที่ Bridge ครบทั้ง 6 ช่อง (`/cmd_vel`, `/odom`, `/scan`, `/tf`, `/joint_states`, `/clock`)
- [ ] ภาพบันทึกหน้าจอการเคลื่อนที่ของหุ่นยนต์และการอ่านค่าจาก `/odom`
- [ ] ค่าตัวเลข `angle_min`, `angle_max`, `angle_increment` และจำนวนลำแสงใน Lab 11.3
- [ ] ภาพบันทึกหน้าจอ log `forward motion BLOCKED` และค่า `/cmd_vel` = 0 ขณะที่ `/cmd_vel_in` ยังเป็น 0.3
- [ ] คำตอบ Checkpoint 11.3

---

## 📊 เกณฑ์การประเมินผล (Lab Grading Rubric - 100 คะแนน)
| รายการประเมิน | รายละเอียดการให้คะแนน | คะแนนเต็ม |
| :--- | :--- | :---: |
| **การเปิดระบบจำลองและ Bridge** | รัน `gazebo_world.launch.py` สำเร็จและมีท็อปปิกขึ้นครบถ้วน | 25 |
| **การทดสอบขับเคลื่อนและ Odometry** | สั่งการผ่าน `/cmd_vel` และแสดงผลการเปลี่ยนแปลงพิกัดใน `/odom` | 20 |
| **การวิเคราะห์ข้อมูล LaserScan** | วัดความถี่และคำนวณคุณสมบัติมุมลำแสงของ LiDAR ได้ถูกต้อง | 20 |
| **การทดสอบระบบ Safety Gate** | รันและพิสูจน์การกั้นความเร็วของ `emergency_stop_node` ได้สำเร็จ | 25 |
| **ความเรียบร้อยของรายงานและโจทย์ท้าทาย** | รายงานสมบูรณ์ ภาพประกอบครบถ้วน บทวิเคราะห์ชัดเจน | 10 |
| **รวม** | | **100** |

---

## ⚠️ การแก้ปัญหาที่พบบ่อยในแล็บ (Troubleshooting)
| ปัญหา | สาเหตุ | การแก้ไข |
| :--- | :--- | :--- |
| `parameter_bridge` แจ้ง Error: Failed to create bridge | ชนิดข้อความใน `ros_gz_bridge.yaml` สะกดผิด หรือไม่มีแพ็กเกจข้อความนั้นในระบบ | ตรวจสอบตัวสะกดชื่อ Type ให้ตรงกับตารางใน Readme |
| หุ่นยนต์ไม่ยอมเบรกเมื่อเจอกำแพง | ผู้สั่งงานส่งเข้า `/cmd_vel` โดยตรง (ข้าม gate) หรือมุมของกำแพงอยู่นอกกรวย $\pm 30^\circ$ | ส่งคำสั่งเข้า `/cmd_vel_in` และ/หรือ ปรับพารามิเตอร์ `-p sector_half_angle_deg:=45.0` |
| หุ่นยนต์ไม่ขยับเลยหลังเปิด `estop:=true` | gate ยังไม่ได้รับ `/scan` (fail-safe ส่ง 0) | ตรวจ `ros2 topic hz /scan` และ TF ด้วย `tf2_echo odom lidar_link` |
| ค่าใน `msg.ranges` เป็น `inf` ทั้งหมด | หุ่นยนต์อยู่ในที่โล่งกว้างเกินระยะวัดสูงสุดของ LiDAR (`range_max`) | ขับหุ่นยนต์เข้าไปใกล้สิ่งกีดขวางหรือกำแพง |


## 📟 ผลการรันจริง (Real Run Output)
บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29
(ฉบับเต็ม: [`results/gazebo_bridge_estop_run.txt`](results/gazebo_bridge_estop_run.txt))

```console
$ ros2 launch amr_week11 gazebo_world.launch.py headless:=true estop:=true   # terminal 1
$ ros2 topic hz /scan
WARNING: topic [/scan] does not appear to be published yet
average rate: 9.888
$ ros2 run amr_week11 ground_truth_pose
diff_drive_robot ground truth: x=-0.000 y=0.000 yaw=0.000 rad (0.0 deg)
# drive forward at 0.3 m/s through the safety gate (/cmd_vel_in) towards the east wall (x = 4.9 m)
sim t=  24.6s  /cmd_vel_in linear.x=0.30 -> /cmd_vel linear.x=0.30  odom x=0.00 m
sim t=  27.9s  /cmd_vel_in linear.x=0.30 -> /cmd_vel linear.x=0.30  odom x=0.84 m
sim t=  30.8s  /cmd_vel_in linear.x=0.30 -> /cmd_vel linear.x=0.30  odom x=1.73 m
sim t=  33.8s  /cmd_vel_in linear.x=0.30 -> /cmd_vel linear.x=0.30  odom x=2.62 m
sim t=  36.8s  /cmd_vel_in linear.x=0.30 -> /cmd_vel linear.x=0.30  odom x=3.51 m
sim t=  39.8s  /cmd_vel_in linear.x=0.30 -> /cmd_vel linear.x=0.30  odom x=4.41 m
sim t=  42.7s  /cmd_vel_in linear.x=0.30 -> /cmd_vel linear.x=0.00  odom x=4.52 m
sim t=  45.8s  /cmd_vel_in linear.x=0.30 -> /cmd_vel linear.x=0.00  odom x=4.52 m
...
$ ros2 run amr_week11 ground_truth_pose
diff_drive_robot ground truth: x=4.522 y=-0.000 yaw=-0.000 rad (-0.0 deg)
```
LiDAR อยู่ที่ $x + 0.08$ m จึงหยุดห่างผิวกำแพง $4.9 - 4.60 \approx 0.30$ m (gate ตัดที่ 0.33 m แล้วหุ่นยนต์ไถลต่ออีกเล็กน้อยตาม `max_linear_acceleration` ของ DiffDrive) และ Odometry ตรงกับตำแหน่งจริงจาก Gazebo

---
