# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 15: ระบบลาดตระเวนจุดตรวจอัตโนมัติ (Waypoint Patrol)
**วิชา:** AMR-101 Essential ROS 2 for Autonomous Mobile Robots  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** พื้นฐาน (Beginner)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายสัปดาห์ที่ 15](Readme.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. พัฒนาและเปิดใช้งานระบบนำทางอัตโนมัติหลายสถานี (**Multi-Station Waypoint Patrol**) ผ่านภาษา Python
2. ควบคุมการจัดลำดับเวลาและหน่วงเวลาการขนถ่ายสินค้า (**Station Dwell Time**) ในแต่ละจุดตรวจ
3. จำลองเหตุการณ์สิ่งกีดขวางปิดกั้นเส้นทางและสังเกตพฤติกรรมการกู้คืน (**Recovery Behaviors**) ของ Behavior Trees
4. ปรับแต่งและเพิ่มสถานีจุดตรวจใหม่เข้าสู่ตารางภารกิจลาดตระเวนตามข้อกำหนดของคลังสินค้า

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่รูทไดเรกทอรีของ repository (เช่น `cd ~/ros`)
- Build แพ็กเกจ (รวมสัปดาห์ที่ 7, 10–14 ที่ใช้ร่วม):
  ```bash
  ./docker/run_lab.sh colcon build --base-paths Essential_ROS --packages-up-to amr_week15
  ```

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 15.1: การเตรียมระบบจำลองและเปิดระบบ Nav2
**เป้าหมาย:** นำชิ้นส่วนทั้งหมดตั้งแต่สัปดาห์ที่ 7, 10–14 มาเปิดทำงานร่วมกัน พร้อม Behavior Tree ของสัปดาห์นี้

1. **Terminal 1:** เปิดโลกจำลอง + หุ่นยนต์ + Bridge + Nav2 (ใช้ BT `behavior_trees/patrol_nav_to_pose.xml`) ด้วยคำสั่งเดียว
   ```bash
   ./docker/run_lab.sh ros2 launch amr_week15 patrol_system.launch.py headless:=true
   ```
2. **Terminal 2:** ตรวจว่า `bt_navigator` ใช้ BT ของเรา (ผลจริง):
   ```bash
   ./docker/run_lab.sh ros2 param get /bt_navigator default_nav_to_pose_bt_xml
   ```
   ```text
   String value is: /workspace/.colcon/c/install/amr_week15/share/amr_week15/behavior_trees/patrol_nav_to_pose.xml
   ```
   (path ขึ้นกับว่า build ไว้ที่ใด; ของนักศึกษาจะเป็น `/workspace/install/amr_week15/share/...`)
3. **(ทางเลือก) ส่งพิกัดเริ่มต้นใหม่ให้ AMCL** — AMCL เริ่มที่ $(0,0,0)$ ให้อยู่แล้ว (`set_initial_pose: true`):
   ```bash
   ./docker/run_lab.sh ros2 run amr_week14 amcl_initial_pose --ros-args -p use_sim_time:=true
   ```

---

### 🔹 Lab 15.2: การรันภารกิจลาดตระเวน 5 สถานี (Waypoint Mission Execution)
**เป้าหมาย:** สังเกตการเคลื่อนที่อัตโนมัติและการหน่วงเวลา ณ แต่ละสถานี

1. ใน **Terminal 2** รันสคริปต์ภารกิจลาดตระเวน:
   ```bash
   ./docker/run_lab.sh ros2 run amr_week15 waypoint_patrol --ros-args -p use_sim_time:=true
   ```
   **ผลลัพธ์จริง:**
   ```text
   [INFO] [1793246902.779426712] [waypoint_patroller]: Waiting for Nav2 (bt_navigator active, /navigate_to_pose)...
   [INFO] [1793246904.054665454] [waypoint_patroller]: [1/5] Navigating to Station 1: Receiving Dock (x=2.00, y=3.50, yaw=0.00)
   [INFO] [1793246920.529044781] [waypoint_patroller]: [1/5] Station 1: Receiving Dock: SUCCEEDED after 16.4 s, dwelling 3.0 s
   [INFO] [1793246923.548490325] [waypoint_patroller]: [2/5] Navigating to Station 2: Storage Aisle B (x=2.00, y=-2.00, yaw=-1.57)
   [INFO] [1793246947.872586855] [waypoint_patroller]: [2/5] Station 2: Storage Aisle B: SUCCEEDED after 24.2 s, dwelling 3.0 s
   ...
   [INFO] [1793247014.562584142] [waypoint_patroller]: [5/5] Station 5: Charging Base: SUCCEEDED after 18.4 s, dwelling 2.0 s
   [INFO] [1793247016.588136858] [waypoint_patroller]: Patrol finished: 5/5 stations SUCCEEDED in 111.6 s (sim time)
   ```
   ตรวจ exit code: `echo $?` ต้องได้ `0` (ถ้ามีสถานีใดไม่ `SUCCEEDED` จะได้ `1`)

2. สังเกตว่าในแต่ละสถานี หุ่นยนต์จะหยุดนิ่งตามเวลา `dwell` (หน่วยเป็นเวลาจำลอง) เพื่อจำลองการโหลดสัมภาระ แล้วจึงเคลื่อนที่ต่อไปยังสถานีถัดไปโดยอัตโนมัติ
3. ลองใช้ `/follow_waypoints` ของ Nav2 (`waypoint_follower`) ส่งหลายจุดใน goal เดียว (ผลจริง: `Goal finished with status: SUCCEEDED`):
   ```bash
   ./docker/run_lab.sh ros2 action send_goal /follow_waypoints nav2_msgs/action/FollowWaypoints "{poses: [{header: {frame_id: map}, pose: {position: {x: 1.0, y: -1.0}, orientation: {w: 1.0}}}, {header: {frame_id: map}, pose: {position: {x: -1.0, y: -1.0}, orientation: {w: 1.0}}}]}"
   ```

---

### 🔹 Lab 15.3: การจำลองการทำงานของ Recovery Behaviors
**เป้าหมาย:** ทดสอบความสามารถในการแก้ไขปัญหาเฉพาะหน้าของ Behavior Tree

1. ในระหว่างที่หุ่นยนต์กำลังเดินทางไปยัง Station 3 ให้นักศึกษาจำลองสิ่งกีดขวางมาขวางช่องทางเดิน
2. สังเกตปฏิกิริยาของระบบใน Terminal 3 (Nav2 Navigator):
   - หุ่นยนต์จะหยุดและขึ้นเตือนว่าเส้นทางเดิมถูกบล็อก
   - Behavior Tree จะเข้าสู่โหนด `RecoveryNode`
   - ใน BT ของเรา (`patrol_nav_to_pose.xml`) ลำดับ recovery แบบ RoundRobin คือ ล้าง Costmap → `Spin` 90° → `Wait` 3 s → `BackUp` 0.3 m
3. หากมีทางเลี่ยงอื่น หุ่นยนต์จะคำนวณเส้นทางอ้อมสิ่งกีดขวางและเดินทางไปถึงเป้าหมายได้สำเร็จ

   **คำถาม Checkpoint 15.3:**
   - [ ] หากทางเดินถูกปิดตาย 100% ทุกทิศทาง ผลลัพธ์สุดท้ายของ Action Goal จะเป็นอะไร? (`ABORTED`)
   - [ ] ในโค้ด `waypoint_patrol.py` หากเป้าหมายล้มเหลว โปรแกรมจะหยุดทำงานทันทีหรือข้ามไปสถานีถัดไป? และ exit code สุดท้ายเป็นเท่าใด?

---

### 🔹 Lab 15.4: การปรับแต่งเพิ่มสถานีจุดตรวจใหม่ (Hands-on Task)
**เป้าหมาย:** เพิ่มสถานีตรวจสอบฉุกเฉิน (Emergency Inspection Bay) เข้าสู่ภารกิจ

ให้นักศึกษาแก้ไขไฟล์ `Essential_ROS/Week_15_Waypoint_Patrol_BT/src/waypoint_patrol.py`:
1. เพิ่มสถานีที่ 6 เข้าไปในรายการ `PATROL_WAYPOINTS`:
   - ชื่อ: `Station 6: Hazmat Inspection`
   - พิกัด: $X = -1.0$, $Y = 0.8$ (ห่างเสาต้นซ้ายเกิน 0.55 m)
   - มุมหัน: $\text{Yaw} = 0.785$ rad ($45^\circ$)
   - เวลาหยุดปฏิบัติงาน: `dwell = 4.0` วินาที
2. ตรวจพิกัดใหม่เทียบแผนที่จริงด้วยชุดทดสอบ (ต้องผ่านก่อนรันจริง):
   ```bash
   ./docker/run_lab.sh colcon build --base-paths Essential_ROS --packages-select amr_week15
   ./docker/run_lab.sh colcon test --base-paths Essential_ROS --packages-select amr_week15 --pytest-args -k test_station
   ```
   (ลองใส่ $Y = 1.5$ ดู: จุดนั้นห่างมุมเสาเพียง 0.45 m จึงตกในเขต inflation และการทดสอบจะไม่ผ่าน)
3. ทดสอบรันสคริปต์ใหม่ และตรวจสอบว่าหุ่นยนต์เคลื่อนที่เข้าจอดครบทั้ง 6 สถานี (`6/6 stations SUCCEEDED`)

---

## 🏆 โจทย์ท้าทายระดับสูง (Challenge Exercises)
1. **Challenge 15.1:** พัฒนาระบบลาดตระเวนแบบวนลูปต่อเนื่องไม่รู้จบ (**Continuous Infinite Patrol**) จนกว่าจะมีผู้ส่งคำสั่งหยุด หรือจนกว่าแบตเตอรี่จะลดต่ำลง
2. **Challenge 15.2:** ใช้คลาส `BasicNavigator` จาก `nav2_simple_commander.robot_navigator` เขียนสคริปต์เปรียบเทียบระหว่างเมธอด `goToPose()` วนลูป กับการใช้ `followWaypoints()` แบบชุดเดียว

---

## 📦 สิ่งที่ต้องส่ง (Deliverables Checklist)
- [ ] ภาพบันทึกหน้าจอผลการรัน `waypoint_patrol` ครบทุกสถานี (`5/5 stations SUCCEEDED`)
- [ ] ภาพบันทึกหน้าจอการแสดงผลเส้นทางเดินหลายสถานีบนโปรแกรม RViz2
- [ ] ภาพบันทึกเหตุการณ์การทำงานของ Recovery Behavior เมื่อพบสิ่งกีดขวางใน Lab 15.3
- [ ] โค้ดส่วนที่เพิ่ม Station 6 ใน Lab 15.4
- [ ] คำตอบ Checkpoint 15.3

---

## 📊 เกณฑ์การประเมินผล (Lab Grading Rubric - 100 คะแนน)
| รายการประเมิน | รายละเอียดการให้คะแนน | คะแนนเต็ม |
| :--- | :--- | :---: |
| **การเปิดและบูรณาการระบบ Nav2** | นำระบบจำลอง, TF, และ Nav2 Stack มาเปิดทำงานร่วมกันได้สมบูรณ์ | 25 |
| **ความสำเร็จของภารกิจลาดตระเวน** | หุ่นยนต์เคลื่อนที่ผ่านจุดตรวจครบ 5 สถานี พร้อมระบบหน่วงเวลาถูกต้อง | 25 |
| **การวิเคราะห์ Recovery Behaviors** | อธิบายและบันทึกภาพการกู้สถานการณ์ของ Behavior Tree ได้ถูกต้อง | 20 |
| **การพัฒนาเพิ่มสถานีที่ 6 ใน Lab 15.4** | แก้ไขตารางภารกิจและหุ่นยนต์เข้าจอดสถานีใหม่ได้อย่างแม่นยำ | 20 |
| **ความเรียบร้อยของรายงานและโจทย์ท้าทาย** | รายงานละเอียด ภาพประกอบครบถ้วน บทวิเคราะห์ชัดเจน | 10 |
| **รวม** | | **100** |

---

## ⚠️ การแก้ปัญหาที่พบบ่อยในแล็บ (Troubleshooting)
| ปัญหา | สาเหตุ | การแก้ไข |
| :--- | :--- | :--- |
| `waypoint_patrol` แจ้ง `Nav2 /navigate_to_pose is not available/active!` | Nav2 Stack ยังไม่เข้าสู่สถานะ Active ภายใน 120 s | ตรวจ log `lifecycle_manager_navigation: Managed nodes are active` และ `ros2 lifecycle get /bt_navigator` |
| `bt_navigator` activate ไม่ผ่านหลังแก้ไฟล์ BT | XML ผิดรูปแบบหรือใช้โหนดที่ไม่มี (เช่น `Error at line 4: -> Node not recognized`) | ตรวจด้วย `test_waypoints.py::test_bt_xml_wellformed_and_known_nodes` และดู [`results/bt_load_check.txt`](results/bt_load_check.txt) |
| หุ่นยนต์เข้าไม่ถึงสถานีและติด Recovery ซ้ำซาก | พิกัดสถานีอยู่ใกล้กำแพงหรือสิ่งกีดขวางมากเกินไปจนติด Inflation Layer | ขยับพิกัดสถานีให้อยู่ห่างจากขอบกำแพงอย่างน้อย $0.5$ เมตร |
| มุมหันของหุ่นยนต์ตอนจอดไม่ตรงกับที่กำหนด | แปลงมุม Yaw เป็น Quaternion ผิดสูตร | ตรวจสอบว่าใช้ $z = \sin(\theta/2)$ และ $w = \cos(\theta/2)$ |


## 📟 ผลการรันจริง (Real Run Output)
บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29
(ฉบับเต็ม: [`results/waypoint_patrol_run.txt`](results/waypoint_patrol_run.txt) และ [`results/bt_load_check.txt`](results/bt_load_check.txt))

```console
$ ros2 launch amr_week15 patrol_system.launch.py headless:=true   # terminal 1
$ ros2 run amr_week15 waypoint_patrol --ros-args -p use_sim_time:=true
[INFO] [1793246902.779426712] [waypoint_patroller]: Waiting for Nav2 (bt_navigator active, /navigate_to_pose)...
[INFO] [1793246904.054665454] [waypoint_patroller]: [1/5] Navigating to Station 1: Receiving Dock (x=2.00, y=3.50, yaw=0.00)
[INFO] [1793246920.529044781] [waypoint_patroller]: [1/5] Station 1: Receiving Dock: SUCCEEDED after 16.4 s, dwelling 3.0 s
[INFO] [1793246923.548490325] [waypoint_patroller]: [2/5] Navigating to Station 2: Storage Aisle B (x=2.00, y=-2.00, yaw=-1.57)
[INFO] [1793246947.872586855] [waypoint_patroller]: [2/5] Station 2: Storage Aisle B: SUCCEEDED after 24.2 s, dwelling 3.0 s
[INFO] [1793246950.899491906] [waypoint_patroller]: [3/5] Navigating to Station 3: Quality Check (x=-2.00, y=-2.00, yaw=3.14)
[INFO] [1793246965.173777686] [waypoint_patroller]: [3/5] Station 3: Quality Check: SUCCEEDED after 14.2 s, dwelling 3.0 s
[INFO] [1793246968.192004624] [waypoint_patroller]: [4/5] Navigating to Station 4: Shipping Dock (x=-2.00, y=3.50, yaw=1.57)
[INFO] [1793246992.966556927] [waypoint_patroller]: [4/5] Station 4: Shipping Dock: SUCCEEDED after 24.5 s, dwelling 3.0 s
[INFO] [1793246995.990225090] [waypoint_patroller]: [5/5] Navigating to Station 5: Charging Base (x=0.00, y=0.00, yaw=0.00)
[INFO] [1793247014.562584142] [waypoint_patroller]: [5/5] Station 5: Charging Base: SUCCEEDED after 18.4 s, dwelling 2.0 s
[INFO] [1793247016.588136858] [waypoint_patroller]: Patrol finished: 5/5 stations SUCCEEDED in 111.6 s (sim time)
(exit code 0)
```

---
