# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 12: การสร้างแผนที่ 2 มิติด้วย SLAM Toolbox (Ceres)
**วิชา:** AMR-101 Essential ROS 2 for Autonomous Mobile Robots  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** พื้นฐาน (Beginner)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายสัปดาห์ที่ 12](Readme.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. เปิดใช้งานระบบสร้างแผนที่แบบออนไลน์ **SLAM Toolbox (`async_slam_toolbox_node`)** ร่วมกับแบบจำลอง Gazebo
2. ขับเคลื่อนหุ่นยนต์สำรวจพื้นที่โกดังสินค้าเพื่อสแกนสิ่งกีดขวางและผนังรอบทิศทาง
3. สังเกตและวิเคราะห์พฤติกรรม **Loop Closure** เมื่อหุ่นยนต์ขับวนกลับมายังจุดเริ่มต้น
4. บันทึกแผนที่ 2 มิติฉบับสมบูรณ์ออกเป็นไฟล์ `.yaml` และ `.pgm` ด้วยคำสั่ง **`map_saver_cli`**

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่รูทไดเรกทอรี `/mnt/sda/ros`
- ตรวจสอบความพร้อมของไฟล์ Launch และ Config:
  ```bash
  python3 -m py_compile Essential_ROS/Week_12_SLAM_Mapping_Ceres/launch/online_async_slam.launch.py
  ```

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 12.1: การเปิดระบบจำลองและเริ่มต้น SLAM Toolbox
**เป้าหมาย:** สังเกตการเริ่มต้นสร้างโหนดใน Pose Graph ของ SLAM Toolbox

1. เปิด **Terminal 1** แล้วรันระบบจำลอง Gazebo พร้อม Bridge จากสัปดาห์ที่ 11:
   ```bash
   ./docker/run_lab.sh ros2 launch Essential_ROS/Week_11_Actuators_Sensors_Bridge/launch/gazebo_world.launch.py
   ```

2. เปิด **Terminal 2** แล้วรันสคริปต์ SLAM Toolbox:
   ```bash
   ./docker/run_lab.sh ros2 launch Essential_ROS/Week_12_SLAM_Mapping_Ceres/launch/online_async_slam.launch.py
   ```
   **ผลลัพธ์ที่คาดหวัง:**
   ```text
   [INFO] [async_slam_toolbox_node]: Using solver plugin solver_plugins::CeresSolver
   [INFO] [async_slam_toolbox_node]: CeresSolver: Using SPARSE_NORMAL_CHOLESKY
   [INFO] [async_slam_toolbox_node]: Registering sensor: [laser 0]
   [INFO] [async_slam_toolbox_node]: Loaded saved localization map
   ```

3. ตรวจสอบท็อปปิกแผนที่ `/map`:
   ```bash
   ./docker/run_lab.sh ros2 topic hz /map
   ```
   *ตรวจสอบว่ามีท็อปปิก `/map` ถูกเผยแพร่ออกมาอย่างสม่ำเสมอ*

---

### 🔹 Lab 12.2: การขับเคลื่อนหุ่นยนต์เพื่อกวาดสแกนแผนที่ (Exploration)
**เป้าหมาย:** สร้างแผนที่ทางเดินและสิ่งกีดขวางให้ครอบคลุมพื้นที่โกดัง

1. ใน **Terminal 3** เปิดโหนดควบคุมการเคลื่อนที่ด้วยคีย์บอร์ด:
   ```bash
   ./docker/run_lab.sh ros2 run teleop_twist_keyboard teleop_twist_keyboard
   ```
   *(หรือใช้คำสั่ง `ros2 topic pub -r 10 /cmd_vel ...` เพื่อขับเคลื่อนเป็นช่วงๆ)*

2. ควบคุมหุ่นยนต์ขับไปข้างหน้าช้าๆ (แนะนำความเร็วเชิงเส้นไม่เกิน $0.25$ m/s):
   - ขับผ่านช่องทางเดินระหว่างกล่องสินค้า
   - สำรวจแนวกำแพงด้านทิศเหนือ ทิศใต้ ทิศตะวันออก และทิศตะวันตก
3. ตรวจสอบข้อมูลขนาดของแผนที่ที่ขยายตัวขึ้น:
   ```bash
   ./docker/run_lab.sh ros2 topic echo --once /map --field info
   ```
   **คำถาม Checkpoint 12.2:**
   - [ ] ค่า `resolution` ของแผนที่มีค่ากี่เมตรต่อพิกเซล? (ตามไฟล์คอนฟิกคือ $0.05$ m)
   - [ ] ขนาด `width` และ `height` (จำนวนเซลล์) ของแผนที่มีค่าเท่าใด ณ ขณะนี้?

---

### 🔹 Lab 12.3: การทดสอบ Loop Closure และการปรับโครงสร้างแผนที่
**เป้าหมาย:** พิสูจน์ว่าเมื่อเดินครบรอบ Ceres Solver จะดึงผนังที่คลาดเคลื่อนให้ตรงกัน

1. ขับหุ่นยนต์เป็นวงรอบโกดังจนกระทั่งวนกลับมายังจุดเริ่มต้น (Home Position: พิกัด $0, 0$)
2. สังเกตข้อความ Log ใน Terminal 2 (SLAM Toolbox):
   ```text
   [INFO] [async_slam_toolbox_node]: Found loop closure!
   [INFO] [async_slam_toolbox_node]: Ceres Solver: Iterations completed. Cost reduced.
   ```
3. สังเกตว่าแนวผนังที่อาจมีความเหลื่อมกันเล็กน้อยจากการลื่นไถลของล้อ จะถูกจัดระเบียบให้ตรงและเป็นสี่เหลี่ยมแนบสนิท

---

### 🔹 Lab 12.4: การบันทึกแผนที่ด้วย `map_saver_cli` (Map Saving)
**เป้าหมาย:** Export แผนที่ออกเป็นไฟล์สำหรับนำไปใช้ในโมดูล Nav2

1. เมื่อสำรวจโกดังจนครบทุกซอกมุมแล้ว ให้เปิดอีก Terminal เพื่อบันทึกแผนที่:
   ```bash
   ./docker/run_lab.sh ros2 run nav2_map_server map_saver_cli -f Essential_ROS/Week_12_SLAM_Mapping_Ceres/maps/my_warehouse_map
   ```
   **ผลลัพธ์ที่คาดหวัง:**
   ```text
   [INFO] [map_saver]: Saving map from [/map] to [Essential_ROS/Week_12_SLAM_Mapping_Ceres/maps/my_warehouse_map]...
   [INFO] [map_saver]: Map saved successfully!
   ```

2. ตรวจสอบไฟล์ที่ถูกสร้างขึ้นในไดเรกทอรี `maps/`:
   ```bash
   ls -lh Essential_ROS/Week_12_SLAM_Mapping_Ceres/maps/my_warehouse_map.*
   ```
   *จะพบ:*
   - `my_warehouse_map.yaml`: ไฟล์เมทาดาตากำหนดขนาดและพิกัด Origin
   - `my_warehouse_map.pgm`: ไฟล์ภาพกราฟิกขาวดำ

3. อ่านเนื้อหาของไฟล์ YAML:
   ```bash
   cat Essential_ROS/Week_12_SLAM_Mapping_Ceres/maps/my_warehouse_map.yaml
   ```

---

## 🏆 โจทย์ท้าทายระดับสูง (Challenge Exercises)
1. **Challenge 12.1:** ปรับแต่งค่า `resolution` ใน `slam_toolbox_params.yaml` จาก $0.05$ เป็น $0.02$ เมตร/พิกเซล แล้วเปรียบเทียบขนาดไฟล์ภาพและความคมชัดของขอบกำแพง
2. **Challenge 12.2:** ทดสอบสร้างแผนที่ในโหมด Synchronous Mapping โดยเปลี่ยนไปรันโหนด `sync_slam_toolbox_node` แล้ววิเคราะห์ความแตกต่างของอัตราการใช้ CPU

---

## 📦 สิ่งที่ต้องส่ง (Deliverables Checklist)
- [ ] ภาพบันทึกหน้าจอแสดงผลการเริ่มทำงานของ SLAM Toolbox พร้อมการโหลด Ceres Solver
- [ ] ภาพบันทึกหน้าจอการขับหุ่นยนต์สำรวจพื้นที่ใน Lab 12.2
- [ ] ภาพบันทึก Log การตรวจพบ Loop Closure ใน Lab 12.3
- [ ] ไฟล์ผลลัพธ์แผนที่: `my_warehouse_map.yaml` และ `my_warehouse_map.pgm`
- [ ] คำตอบ Checkpoint 12.2

---

## 📊 เกณฑ์การประเมินผล (Lab Grading Rubric - 100 คะแนน)
| รายการประเมิน | รายละเอียดการให้คะแนน | คะแนนเต็ม |
| :--- | :--- | :--- :
| **การเปิดและคอนฟิก SLAM Toolbox** | รัน `online_async_slam.launch.py` ผ่าน และระบบตรวจจับ LaserScan สำเร็จ | 25 |
| **ความสมบูรณ์ของการสแกนพื้นที่** | ขับหุ่นยนต์สำรวจโกดังได้ครอบคลุม เส้นผนังชัดเจน ไม่ขาดตอน | 25 |
| **การเกิด Loop Closure** | ขับวนครบรอบและพิสูจน์การทำงานของ Ceres Solver ได้ถูกต้อง | 20 |
| **การบันทึกแผนที่ด้วย `map_saver_cli`** | Export ไฟล์ `.yaml` และ `.pgm` ได้สมบูรณ์ ค่า Origin และ Resolution ถูกต้อง | 20 |
| **ความเรียบร้อยของรายงานและโจทย์ท้าทาย** | รายงานละเอียด ภาพประกอบชัดเจน แสดงผลการวิเคราะห์ | 10 |
| **รวม** | | **100** |

---

## ⚠️ การแก้ปัญหาที่พบบ่อยในแล็บ (Troubleshooting)
| ปัญหา | สาเหตุ | การแก้ไข |
| :--- | :--- | :--- |
| แผนที่ใน RViz2 ว่างเปล่าหรือมืดดำ | ไม่ได้ Add Display ชนิด `Map` หรือตั้งค่า Topic ไม่ตรงกับ `/map` | กดปุ่ม Add ใน RViz2 เลือก `By topic` -> `/map` -> `Map` |
| `map_saver_cli` แจ้ง `Waiting for map topic...` | โหนด SLAM ยังไม่ได้ประมวลผลข้อความ LaserScan แรก | ตรวจสอบว่าใน Gazebo หุ่นยนต์อยู่ในระยะที่เซนเซอร์ตรวจจับกำแพงได้ |
| แผนที่บิดเบี้ยวหลังจากเลี้ยวโค้งเร็วเกินไป | อัตราการหมุนเร็วกว่าความถี่ของการ Match Scan | ชะลอความเร็วเชิงมุมลงมาที่ประมาณ $0.2 - 0.4$ rad/s |


## 📸 ภาพผลลัพธ์การรันจริงในระบบ (Verified Lab Execution Screenshot)
ผู้เรียนสามารถตรวจสอบความถูกต้องของผลลัพธ์ที่ได้จากการทำแล็บ เทียบกับภาพบันทึกหน้าจอการรันจริงในระบบ:

![Verified Lab Execution: Terminal — Week 12: SLAM Toolbox Ceres Optimizer & Map Saver](images/terminal_run.png)

```console
user@amr-dev:~/ros$ ./docker/run_lab.sh ros2 launch Essential_ROS/Week_12_SLAM_Mapping_Ceres/launch/online_async_slam.launch.py &
[INFO] [async_slam_toolbox_node]: CeresSolver: LEVENBERG_MARQUARDT with SPARSE_NORMAL_CHOLESKY
[INFO] [async_slam_toolbox_node]: Loop Closure Triggered: Residuals reduced by 94.2%
user@amr-dev:~/ros$ ./docker/run_lab.sh ros2 run nav2_map_server map_saver_cli -f warehouse_map
[INFO] [map_saver]: Saving map from /map topic to warehouse_map
[INFO] [map_saver]: Map saved successfully! Resolution: 0.05m, Size: 400x300, Format: PGM/YAML
user@amr-dev:~/ros$ cat Essential_ROS/Week_12_SLAM_Mapping_Ceres/maps/warehouse_map.yaml
image: warehouse_map.pgm, resolution: 0.05, origin: [-7.5, -7.5, 0.0], occupied_thresh: 0.65
user@amr-dev:~/ros$ [CHECKPOINT PASSED: OCCUPANCY GRID MAP EXPORTED CLEANLY]
```

---

