# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 14: การวางแผนเส้นทางและ AMCL Localization
**วิชา:** AMR-101 Essential ROS 2 for Autonomous Mobile Robots  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** พื้นฐาน (Beginner)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายสัปดาห์ที่ 14](Readme.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. เปิดใช้งานระบบ **Nav2 Stack** แบบครบวงจรผ่านไฟล์ `nav2_bringup.launch.py`
2. กำหนดพิกัดเริ่มต้นให้ระบบประมาณตำแหน่ง **AMCL** ผ่านสคริปต์ `amcl_initial_pose.py`
3. สังเกตพฤติกรรมการลู่เข้าของกลุ่มอนุภาค (**Particle Cloud Convergence**) ใน RViz2
4. ส่งเป้าหมายพิกัดนำทางอัตโนมัติผ่านแอ็กชัน `/navigate_to_pose` และวิเคราะห์การหลบหลีกสิ่งกีดขวาง

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่รูทไดเรกทอรีของ repository (เช่น `cd ~/ros`)
- Build แพ็กเกจ (รวมสัปดาห์ที่ 7, 10–13 ที่ใช้ร่วม):
  ```bash
  ./docker/run_lab.sh colcon build --base-paths Essential_ROS --packages-up-to amr_week14
  ```
- เครื่องทดสอบของผู้สอน: Nav2 ใช้ CPU ค่อนข้างมาก ให้รัน Gazebo + Nav2 ทีละชุด และปิดทุกโปรเซสเมื่อเลิกใช้

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 14.1: การเปิดระบบจำลองและ Nav2 Stack
**เป้าหมาย:** สังเกตการเข้าสู่สถานะ Active ของโหนด Nav2 ทั้งหมด

1. เปิด **Terminal 1** แล้วรันแบบจำลองโกดังสินค้า (รวม `robot_state_publisher` แล้ว ไม่ต้องเปิด `display_urdf` แยก):
   ```bash
   ./docker/run_lab.sh ros2 launch amr_week11 gazebo_world.launch.py headless:=true
   ```

2. เปิด **Terminal 2** แล้วเปิดระบบนำทาง Nav2 Stack (ใช้แผนที่จริงจากสัปดาห์ที่ 12 เป็นค่าเริ่มต้น):
   ```bash
   ./docker/run_lab.sh ros2 launch amr_week14 nav2_bringup.launch.py
   ```
   **ผลลัพธ์จริง (ตัดมา):**
   ```text
   [lifecycle_manager-3] [INFO] [1793245896.630389847] [lifecycle_manager_localization]: Managed nodes are active
   [lifecycle_manager-12] [INFO] [1793245900.995845057] [lifecycle_manager_navigation]: Managed nodes are active
   ```
   Lifecycle manager มี 2 ตัว: `lifecycle_manager_localization` (map_server, amcl) และ `lifecycle_manager_navigation`
   (controller_server, smoother_server, planner_server, behavior_server, velocity_smoother, collision_monitor, bt_navigator, waypoint_follower)

3. ตรวจสถานะโหนด (ผลจริง):
   ```bash
   for n in controller_server planner_server behavior_server bt_navigator waypoint_follower velocity_smoother collision_monitor smoother_server; do echo -n "$n: "; ./docker/run_lab.sh ros2 lifecycle get /$n; done
   ```
   ```text
   controller_server: active [3]
   planner_server: active [3]
   behavior_server: active [3]
   bt_navigator: active [3]
   waypoint_follower: active [3]
   velocity_smoother: active [3]
   collision_monitor: active [3]
   smoother_server: active [3]
   ```

---

### 🔹 Lab 14.2: การตั้งค่าพิกัดเริ่มต้น (AMCL Initialization)
**เป้าหมาย:** กำหนดพิกัดตั้งต้นของหุ่นยนต์บนแผนที่เพื่อเปิดใช้งานทรานส์ฟอร์ม `map -> odom`

> ในคอนฟิกนี้ AMCL ตั้ง `set_initial_pose: true` ที่ $(0, 0, 0)$ ไว้แล้ว (หุ่นยนต์เกิดที่ origin ของแผนที่เสมอ) เพื่อให้มี TF `map → odom` ทันที
> ถ้าไม่มี initial pose เลย global costmap ใน `planner_server` จะรอ TF `map → base_footprint` จนหมดเวลาแล้ว **ล้มการ activate ทั้ง Nav2** (เกิดขึ้นจริงระหว่างเตรียมแล็บ: `Failed to activate global_costmap because transform from base_footprint to map did not become available before timeout`)
> ขั้นตอนต่อไปนี้จึงเป็นการ *ตั้งตำแหน่งใหม่ (re-localize)* เหมือนกดปุ่ม 2D Pose Estimate ใน RViz2

1. เปิด **Terminal 3** แล้วรันสคริปต์ส่ง Initial Pose (สคริปต์รอจนกว่า AMCL จะตอบกลับทาง `/amcl_pose`):
   ```bash
   ./docker/run_lab.sh ros2 run amr_week14 amcl_initial_pose --ros-args -p use_sim_time:=true -p x:=0.0 -p y:=0.0 -p theta:=0.0
   ```
   **ผลลัพธ์จริง:**
   ```text
   [INFO] [1793245948.890258962] [amcl_initial_pose_publisher]: Publishing initial pose x=0.00 y=0.00 theta=0.000 rad in frame map
   [INFO] [1793245948.976965104] [amcl_initial_pose_publisher]: AMCL pose: x=-0.017 y=0.033 yaw=0.007 rad
   ```

2. ตรวจสอบใน Terminal 2 (log ของ AMCL, ผลจริง):
   ```text
   [amcl-2] [INFO] [1793245948.890744947] [amcl]: initialPoseReceived
   [amcl-2] [INFO] [1793245948.890831107] [amcl]: Setting pose (57.146000): 0.000 0.000 0.000
   ```
   (ตัวเลขในวงเล็บคือเวลาจำลองเป็นวินาที)

3. ตรวจสอบว่ามีทรานส์ฟอร์ม `map -> odom` ปรากฏขึ้นในระบบแล้ว:
   ```bash
   ./docker/run_lab.sh ros2 run tf2_ros tf2_echo map odom
   ```

   **คำถาม Checkpoint 14.2:**
   - [ ] ถ้าตั้ง `set_initial_pose: false` และยังไม่ส่ง Initial Pose ค่าทรานส์ฟอร์มระหว่าง `map` และ `odom` สามารถ lookup ได้หรือไม่? เกิดอะไรขึ้นกับการ activate ของ Nav2?
   - [ ] เหตุใด AMCL จึงต้องใช้ข้อมูลทั้งจาก `/scan` และ `/initialpose` ในการเริ่มทำงาน?

---

### 🔹 Lab 14.3: การสั่งนำทางอัตโนมัติไปยังจุดเป้าหมาย (Autonomous Navigation)
**เป้าหมาย:** สั่งการผ่าน ROS 2 Action ให้หุ่นยนต์วางแผนและขับเคลื่อนไปยังพิกัดเป้าหมาย

1. ใน **Terminal 3** ส่งคำสั่งให้นำทางไปยังพิกัดเป้าหมาย $(X = 2.0, Y = -2.0, \theta = -90^\circ)$:
   ```bash
   ./docker/run_lab.sh ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 2.0, y: -2.0}, orientation: {z: -0.7071, w: 0.7071}}}}"
   ```
   (เพิ่ม `--feedback` เพื่อดู `distance_remaining` ระหว่างทาง)
2. **ผลลัพธ์จริง (ตัดมา):**
   ```text
   Goal accepted with ID: f58aa5137a8e4aec9e74178de70ef217

   Result:
       error_code: 0
   error_msg: ''

   Goal finished with status: SUCCEEDED
   ```
   ใช้เวลาจริง 14.2 วินาที; log ของ Nav2 แสดง `Begin navigating from current location (-0.02, 0.03) to (2.00, -2.00)` → `Reached the goal!` → `Goal succeeded`
3. ตรวจตำแหน่งจริงใน Gazebo: `./docker/run_lab.sh ros2 run amr_week11 ground_truth_pose`
   ```text
   diff_drive_robot ground truth: x=1.900 y=-1.927 yaw=-1.321 rad (-75.7 deg)
   ```
   คลาดจากเป้า 0.125 m และ 14.3° ซึ่งอยู่ภายใน `xy_goal_tolerance: 0.25` และ `yaw_goal_tolerance: 0.25` rad (14.3°) — goal checker หยุดหุ่นยนต์ทันทีที่เข้าเกณฑ์ จึงไม่ได้จอดตรงเป้าเป๊ะ

---

### 🔹 Lab 14.4: การทดสอบหลบหลีกสิ่งกีดขวางแบบพลวัต (Dynamic Obstacle Avoidance)
**เป้าหมาย:** สังเกตปฏิกิริยาของตัวควบคุม DWB Controller เมื่อมีวัตถุโผล่ขึ้นมาขวางเส้นทาง

1. ส่งเป้าหมายให้หุ่นยนต์เดินหน้าตรงระยะไกล ($X = 4.0, Y = 0.0$)
2. ในขณะที่หุ่นยนต์กำลังเคลื่อนที่ ให้เปิดอีก Terminal เพื่อจำลองวัตถุตัดหน้าโดยการ Spawn กล่อง (เช่น `ros2 run ros_gz_sim create -name box -x 2.0 -y 0.0 -z 0.3 -string "<SDF ของกล่อง static>"`) แล้วสังเกตใน RViz2 (`/plan`, `/local_costmap/costmap`)
3. สังเกตพฤติกรรมใน Controller Server:
   - เส้นทาง Global Path เดิมจะถูกตัดทิ้งเนื่องจากติด Inscribed Cost
   - Planner Server จะ Re-plan คำนวณเส้นทางเบี่ยงหลบอันใหม่
   - DWB Controller จะส่งคำสั่งเลี้ยวโค้งอ้อมสิ่งกีดขวางอย่างปลอดภัย

---

## 🏆 โจทย์ท้าทายระดับสูง (Challenge Exercises)
1. **Challenge 14.1:** ปรับลดค่า `xy_goal_tolerance` ใน `nav2_params.yaml` จาก $0.25$ เป็น $0.05$ เมตร และสังเกตเวลาที่หุ่นยนต์ใช้ในการเข้าจอดเทียบแท่นให้แม่นยำระดับเซนติเมตร
2. **Challenge 14.2:** เปลี่ยนตัวควบคุมจาก DWB Controller เป็น **Regulated Pure Pursuit (RPP)** (`plugin: "nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController"`) แล้ววัดความราบเรียบของความเร็วในการเลี้ยวเข้าโค้ง
3. **Challenge 14.3:** เปลี่ยน `use_astar: true` ใน `planner_server` แล้วเปรียบเทียบเวลาวางแผน (ดู log ของ `planner_server`) กับ Dijkstra บนแผนที่โกดังนี้ — บันทึกผลจริงของตนเอง

---

## 📦 สิ่งที่ต้องส่ง (Deliverables Checklist)
- [ ] ภาพบันทึกหน้าจอผลการเปิด Nav2 Stack และสถานะ Lifecycle Management
- [ ] ภาพบันทึกหน้าจอผลการรัน `amcl_initial_pose` (บรรทัด `AMCL pose: ...`) และทรานส์ฟอร์ม `map -> odom` จาก `tf2_echo`
- [ ] ภาพบันทึกหน้าจอคำสั่ง `ros2 action send_goal /navigate_to_pose` ที่รายงานผล `SUCCEEDED`
- [ ] ภาพบันทึกเส้นทางเดินของหุ่นยนต์ในการหลบสิ่งกีดขวาง
- [ ] คำตอบ Checkpoint 14.2

---

## 📊 เกณฑ์การประเมินผล (Lab Grading Rubric - 100 คะแนน)
| รายการประเมิน | รายละเอียดการให้คะแนน | คะแนนเต็ม |
| :--- | :--- | :---: |
| **การเปิดและจัดการ Lifecycle Nav2** | รัน `nav2_bringup.launch.py` สำเร็จ โหนดทั้ง 10 ตัว (2 lifecycle manager) อยู่ในสถานะ Active | 25 |
| **การตั้งค่าพิกัดเริ่มต้นด้วย AMCL** | รัน `amcl_initial_pose` และทรานส์ฟอร์ม `map -> odom` สมบูรณ์ | 25 |
| **ความสำเร็จของการนำทางอัตโนมัติ** | ส่งคำสั่งผ่าน Action `/navigate_to_pose` และหุ่นยนต์เข้าถึงเป้าหมายสำเร็จ | 30 |
| **การทดสอบการหลบหลีกสิ่งกีดขวาง** | อธิบายและบันทึกภาพการวางเส้นทางใหม่เมื่อมีสิ่งกีดขวางได้ถูกต้อง | 10 |
| **ความเรียบร้อยของรายงานและโจทย์ท้าทาย** | รายงานละเอียด ภาพประกอบครบถ้วน บทวิเคราะห์ชัดเจน | 10 |
| **รวม** | | **100** |

---

## ⚠️ การแก้ปัญหาที่พบบ่อยในแล็บ (Troubleshooting)
| ปัญหา | สาเหตุ | การแก้ไข |
| :--- | :--- | :--- |
| `bt_navigator` แจ้ง `Action server is inactive. Rejecting the goal.` | Nav2 ยัง activate ไม่เสร็จ (หรือล้มระหว่าง bringup) | รอจน log `lifecycle_manager_navigation: Managed nodes are active` แล้วตรวจ `ros2 lifecycle get /bt_navigator` |
| controller_server configure ไม่ผ่าน / Nav2 ไม่ active | `FollowPath` (DWB) ไม่มีรายการ `critics` หรือใช้คีย์เก่า `progress_checker_plugin` | ใช้ `nav2_params.yaml` ของแพ็กเกจนี้ (มี `critics` และ `progress_checker_plugins: [...]`) |
| `Failed to activate global_costmap because transform from base_footprint to map did not become available` | ไม่มี initial pose → ไม่มี TF `map → odom` | ตั้ง `set_initial_pose: true` (ค่าปัจจุบัน) หรือส่ง initial pose ภายในไม่กี่วินาทีหลังเปิด Nav2 |
| หุ่นยนต์พยายามเบรกและขึ้น `Recovery Behavior` | มีสิ่งกีดขวางปิดกั้นทางเดินทุกทิศทาง หรือ Inflation กว้างเกินไป | ตรวจสอบว่าทางเดินมีความกว้างมากกว่าความกว้าง Footprint ของหุ่นยนต์ |
| ข้อความ `TF timeout between map and odom` | AMCL ยังไม่เริ่มทำงาน หรือลืมส่ง Initial Pose | รัน `ros2 run amr_week14 amcl_initial_pose --ros-args -p use_sim_time:=true` |


## 📟 ผลการรันจริง (Real Run Output)
บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29
(ฉบับเต็มพร้อม log ของ Nav2: [`results/nav2_navigate_to_pose_run.txt`](results/nav2_navigate_to_pose_run.txt))

```console
$ ros2 launch amr_week11 gazebo_world.launch.py headless:=true   # terminal 1
$ ros2 launch amr_week14 nav2_bringup.launch.py                   # terminal 2
$ for n in controller_server planner_server ...; do ros2 lifecycle get /$n; done
controller_server: active [3]
planner_server: active [3]
behavior_server: active [3]
bt_navigator: active [3]
waypoint_follower: active [3]
velocity_smoother: active [3]
collision_monitor: active [3]
smoother_server: active [3]
$ ros2 run amr_week14 amcl_initial_pose --ros-args -p use_sim_time:=true
[INFO] [1793245948.890258962] [amcl_initial_pose_publisher]: Publishing initial pose x=0.00 y=0.00 theta=0.000 rad in frame map
[INFO] [1793245948.976965104] [amcl_initial_pose_publisher]: AMCL pose: x=-0.017 y=0.033 yaw=0.007 rad
$ ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose {pose: {header: {frame_id: 'map'}, pose: {position: {x: 2.0, y: -2.0}, orientation: {z: -0.7071, w: 0.7071}}}}
Waiting for an action server to become available...
Sending goal:
...

Goal accepted with ID: f58aa5137a8e4aec9e74178de70ef217

Result:
    error_code: 0
error_msg: ''

Goal finished with status: SUCCEEDED
(wall time 14.2 s)
$ ros2 run amr_week11 ground_truth_pose
diff_drive_robot ground truth: x=1.900 y=-1.927 yaw=-1.321 rad (-75.7 deg)
```

---
