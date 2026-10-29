# 🛠️ ใบงานปฏิบัติการที่ 4: การจัดกลุ่มเนมสเปซและการประสานงานฝูงหุ่นยนต์
**วิชา:** AMR-201 Advanced ROS 2 & Industrial Fleet Robotics  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** ขั้นสูง (Advanced)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายบทที่ 4](README.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. รันไฟล์ Launch สำหรับฝูงหุ่นยนต์หลายตัว [`launch/multi_robot_fleet.launch.py`](launch/multi_robot_fleet.launch.py) แบบ headless (ไม่ต้องใช้ Gazebo/GPU)
2. ตรวจสอบการแยกกลุ่ม Node และ Topic ด้วย Namespace และการแยก TF Frame ด้วย `frame_prefix` (`amr_01/`, `amr_02/`) บน `/tf` ที่ใช้ร่วมกัน
3. ทดสอบส่งคำสั่งควบคุมหุ่นยนต์แยกตัวแบบเป็นอิสระต่อกัน
4. ตรวจสอบไฟล์คอนฟิก Open-RMF Fleet Adapter [`config/fleet_adapter_config.yaml`](config/fleet_adapter_config.yaml) และ [`config/nav_graph.yaml`](config/nav_graph.yaml) ด้วย parser จริงของ `rmf_fleet_adapter`

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่ไดเรกทอรีโครงการ `/mnt/sda/ros`
- ถ้าเรียนในห้องที่ใช้เครือข่ายร่วมกัน ให้แยกกลุ่มตัวเองก่อนทุก Terminal (ค่าเลขของกลุ่มตนเอง):
  ```bash
  export ROS_DOMAIN_ID=21 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
  ```
- Build แพ็กเกจ (ครั้งเดียว — `amr_week07` ให้ URDF ของหุ่นยนต์):
  ```bash
  ./docker/run_lab.sh colcon build --base-paths Essential_ROS Advanced_ROS --packages-up-to amr_adv04
  ```

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 4.1: รันระบบ Multi-Robot Fleet Launch
1. Terminal 1 — สั่งรันไฟล์ Launch ของฝูงหุ่นยนต์ (ค่าเริ่มต้น `robots:=amr_01,amr_02`):
   ```bash
   ./docker/run_lab.sh ros2 launch amr_adv04 multi_robot_fleet.launch.py
   ```
2. Terminal 2 — ตรวจสอบรายชื่อ Node และ Topic:
   ```bash
   ./docker/run_lab.sh ros2 node list
   ./docker/run_lab.sh ros2 topic list
   ```
   *ผลลัพธ์จากการรันจริง:* โหนด 6 ตัว `/amr_0X/{robot_state_publisher, fake_diff_drive, map_to_odom}` และ topic `/amr_0X/{cmd_vel, odom, joint_states, robot_description}` ของแต่ละตัว ส่วน `/tf`, `/tf_static` มีชุดเดียว (ดู [ผลการรันจริง](#-ผลการรันจริง-real-run-output))

---

### 🔹 Lab 4.2: ตรวจสอบ TF Frame Tree ของหุ่นยนต์หลายตัว
1. ดู TF ภายในหุ่นยนต์ตัวเดียวกัน (ล้อซ้ายอยู่ห่างแกนกลาง 0.12 m):
   ```bash
   ./docker/run_lab.sh ros2 run tf2_ros tf2_echo amr_01/base_link amr_01/left_wheel_link
   ```
2. ดูตำแหน่งเริ่มต้นของ `amr_02` ใน frame `map` และระยะระหว่างหุ่นยนต์สองตัว:
   ```bash
   ./docker/run_lab.sh ros2 run tf2_ros tf2_echo map amr_02/base_footprint
   ./docker/run_lab.sh ros2 run tf2_ros tf2_echo amr_01/base_link amr_02/base_link
   ```
3. ตรวจว่าใครส่ง/รับ joint state ของ `amr_01` และใครส่ง `/tf`:
   ```bash
   ./docker/run_lab.sh ros2 topic info -v /amr_01/joint_states
   ./docker/run_lab.sh ros2 topic info /tf
   ```
4. (ทางเลือก) สร้างภาพ TF tree: `./docker/run_lab.sh bash -c 'cd /tmp && ros2 run tf2_tools view_frames && cp frames_*.pdf /workspace/'`

**คำถาม Checkpoint 4.1:**
- หากต้องการให้หุ่นยนต์ตัวที่ 3 (`amr_03`) เข้าร่วมฝูง ต้องทำอย่างไร? (ลองรัน `ros2 launch amr_adv04 multi_robot_fleet.launch.py robots:=amr_01,amr_02,amr_03` แล้วดู `map -> amr_03/base_footprint` และดูฟังก์ชัน `robot_group()` ในไฟล์ Launch)
- ทำไม `/amr_01/tf` ไม่มีอยู่ ทั้งที่โหนดทั้งหมดอยู่ใน namespace `/amr_01`? ถ้าต้องการ TF แยกต่อหุ่นยนต์ต้องแก้ไฟล์ Launch อย่างไร?

---

### 🔹 Lab 4.3: สั่งงานหุ่นยนต์แยกตัว
1. ส่งคำสั่งเดินหน้า 0.5 m/s ให้ `amr_01` เท่านั้น (20 ข้อความที่ 10 Hz):
   ```bash
   ./docker/run_lab.sh ros2 topic pub --times 20 --rate 10 /amr_01/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}}"
   ```
2. เปรียบเทียบ odometry ของสองตัว:
   ```bash
   ./docker/run_lab.sh ros2 topic echo --once /amr_01/odom nav_msgs/msg/Odometry --field pose.pose.position
   ./docker/run_lab.sh ros2 topic echo --once /amr_02/odom nav_msgs/msg/Odometry --field pose.pose.position
   ```
   *ผลจากการรันจริง:* `amr_01` อยู่ที่ x ≈ 1.2 m ส่วน `amr_02` ยังอยู่ที่ x = 0.0

**คำถาม Checkpoint 4.2:**
- ทำไมระยะที่ได้คือ ~1.2 m ไม่ใช่ 0.5 × 2.0 = 1.0 m? (ดูพารามิเตอร์ `cmd_vel_timeout` ใน [`src/fake_diff_drive.py`](src/fake_diff_drive.py))

---

### 🔹 Lab 4.4: วิเคราะห์คอนฟิก Open-RMF Fleet Adapter
1. อ่านไฟล์คอนฟิกและ nav graph:
   ```bash
   cat Advanced_ROS/04_Multi_Robot_Fleet_OpenRMF/config/fleet_adapter_config.yaml
   cat Advanced_ROS/04_Multi_Robot_Fleet_OpenRMF/config/nav_graph.yaml
   ```
2. ตรวจด้วย parser ของ `rmf_fleet_adapter` จริง:
   ```bash
   ./docker/run_lab.sh ros2 run amr_adv04 fleet_config_check
   ```
3. ทดลองทำให้คอนฟิกผิด: คัดลอกไฟล์ไปที่ `/tmp` แล้วลบหัวข้อ `mechanical_system` หรือเปลี่ยน charger ของ `amr_02` เป็น `charger_gamma` แล้วตรวจอีกครั้ง:
   ```bash
   ./docker/run_lab.sh bash -c 'cp Advanced_ROS/04_Multi_Robot_Fleet_OpenRMF/config/fleet_adapter_config.yaml /tmp/f.yaml \
     && sed -i "s/charger_beta/charger_gamma/" /tmp/f.yaml && ros2 run amr_adv04 fleet_config_check --config /tmp/f.yaml'
   ```
4. เปิด RMF traffic schedule แล้วดู topic/service ที่มันสร้างจริง:
   ```bash
   ./docker/run_lab.sh ros2 run rmf_traffic_ros2 rmf_traffic_schedule      # Terminal 1
   ./docker/run_lab.sh bash -c 'ros2 topic list -t | grep rmf_traffic; ros2 service list | grep rmf_traffic'   # Terminal 2
   ./docker/run_lab.sh ros2 topic echo --once /rmf_traffic/participants   # Terminal 2
   ```
5. ตอบคำถามเชิงวิศวกรรม:
   - หุ่นยนต์ `amr_01` ถูกกำหนดให้ไปชาร์จที่สถานีใด และสถานีนั้นอยู่ที่พิกัดใดใน nav graph?
   - ระดับแบตเตอรี่ขั้นต่ำ (`recharge_threshold`) และระดับที่ชาร์จถึง (`recharge_soc`) มีค่าเท่าใด และอยู่ในหัวข้อใดของไฟล์?
   - ระยะห่างจุดศูนย์กลางขั้นต่ำระหว่างหุ่นยนต์สองตัวของ fleet นี้คือเท่าใด (ใช้ footprint/vicinity)?
   - ข้อผิดพลาดในข้อ 3 ข้อใดที่ `from_config_files()` จับได้เอง และข้อใดที่ต้องอาศัยการตรวจเพิ่มของ `fleet_config_check`?

---

### 🔹 Lab 4.5: รันชุดทดสอบอัตโนมัติ
```bash
./docker/run_lab.sh colcon test --base-paths Advanced_ROS --packages-select amr_adv04
./docker/run_lab.sh colcon test-result --verbose
```
อ่าน [`test/test_multi_robot_launch.py`](test/test_multi_robot_launch.py) แล้วอธิบายว่ากรณีทดสอบใดจะล้มเหลวถ้าลบ `frame_prefix` ออกจากไฟล์ Launch

---

## 📟 ผลการรันจริง (Real Run Output)

บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29 — ฉบับเต็ม: [`results/multi_robot_fleet.txt`](results/multi_robot_fleet.txt), [`results/fleet_config_check.txt`](results/fleet_config_check.txt), [`results/rmf_traffic_schedule.txt`](results/rmf_traffic_schedule.txt), [`results/colcon_test.txt`](results/colcon_test.txt)

```console
$ ros2 node list
/amr_01/fake_diff_drive
/amr_01/map_to_odom
/amr_01/robot_state_publisher
/amr_02/fake_diff_drive
/amr_02/map_to_odom
/amr_02/robot_state_publisher
$ ros2 run tf2_ros tf2_echo map amr_02/base_footprint
...
- Translation: [0.000, 1.500, 0.000]
...
$ ros2 topic info -v /amr_01/joint_states | grep -E "Node name|Node namespace|Endpoint type"
Node name: fake_diff_drive
Node namespace: /amr_01
Endpoint type: PUBLISHER
Node name: robot_state_publisher
Node namespace: /amr_01
Endpoint type: SUBSCRIPTION
$ ros2 topic info /tf
Type: tf2_msgs/msg/TFMessage
Publisher count: 4
Subscription count: 0
$ ros2 topic list -t | grep rmf_traffic          # ขณะ rmf_traffic_schedule ทำงาน
/rmf_traffic/heartbeat [rmf_traffic_msgs/msg/Heartbeat]
/rmf_traffic/itinerary_clear [rmf_traffic_msgs/msg/ItineraryClear]
...
/rmf_traffic/negotiation_notice [rmf_traffic_msgs/msg/NegotiationNotice]
...
/rmf_traffic/participants [rmf_traffic_msgs/msg/Participants]
/rmf_traffic/registered_queries [rmf_traffic_msgs/msg/ScheduleQueries]
/rmf_traffic/schedule_inconsistency [rmf_traffic_msgs/msg/ScheduleInconsistency]
/rmf_traffic/schedule_startup [rmf_traffic_msgs/msg/ScheduleIdentity]
```

---

## 📊 เกณฑ์การให้คะแนน (Evaluation Rubrics)
| รายการประเมิน | คะแนนเต็ม | เกณฑ์การพิจารณา |
| :--- | :---: | :--- |
| **1. ความเข้าใจการแยก Namespacing และ TF Prefix** | 35 | อธิบายและสาธิตได้ว่าอะไรแยกตาม namespace และอะไรใช้ร่วมกัน (`/tf`) พร้อมเหตุผล |
| **2. ความถูกต้องในการวิเคราะห์โครงสร้าง Open-RMF** | 35 | ตอบคำถาม Checkpoint และคำถาม Lab 4.4 ได้ถูกต้อง อธิบายบทบาทของ Fleet Adapter / Traffic Schedule ได้ |
| **3. ทักษะการใช้ CLI ตรวจสอบ Multi-Robot** | 20 | ใช้ `node list`, `topic list`, `topic info -v`, `tf2_echo`, `topic pub` ตรวจสอบสถานะได้คล่องแคล่ว |
| **4. ความเรียบร้อยและการบันทึกผล** | 10 | บันทึกผลการทดลองและตอบคำถามครบถ้วน |
| **รวม** | **100** | |
