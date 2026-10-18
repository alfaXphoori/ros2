# 🔬 ใบงานปฏิบัติการโมดูล 3: Navigation 2 (Nav2) Hands-on Laboratory

> **คู่มือปฏิบัติการระบบนำทางหุ่นยนต์อัตโนมัติ 4 ตอน: จากการสร้างแผนที่ SLAM สู่ภารกิจลาดตระเวนอัจฉริยะ**

---

## 📋 สารบัญการทดลอง (Laboratory Outline)
- [Lab 3.1: SLAM Mapping ด้วย SLAM Toolbox และการบันทึกแผนที่](#lab-31-slam-mapping-ด้วย-slam-toolbox-และการบันทึกแผนที่)
- [Lab 3.2: Map Server และการระบุตำแหน่งหุ่นยนต์ด้วย AMCL](#lab-32-map-server-และการระบุตำแหน่งหุ่นยนต์ด้วย-amcl)
- [Lab 3.3: การนำทางสู่เป้าหมายอัตโนมัติและการปรับแต่ง Costmap 2D](#lab-33-การนำทางสู่เป้าหมายอัตโนมัติและการปรับแต่ง-costmap-2d)
- [Lab 3.4: การเขียนโปรแกรมลาดตระเวน Multi-Waypoint Patrol ด้วย BasicNavigator API](#lab-34-การเขียนโปรแกรมลาดตระเวน-multi-waypoint-patrol-ด้วย-basicnavigator-api)
- [คำถามท้ายการทดลองและการประเมินผล (Evaluation & Rubrics)](#คำถามท้ายการทดลองและการประเมินผล)

---

## Lab 3.1: SLAM Mapping ด้วย SLAM Toolbox และการบันทึกแผนที่

### 🎯 วัตถุประสงค์
1. เข้าใจสถาปัตยกรรม Graph-based SLAM และการจับคู่ข้อมูลเลเซอร์สแกน (Scan Matching)
2. สามารถเชื่อมโยงข้อมูลเซนเซอร์ LiDAR และ Odometry จาก Webots เข้าสู่ `slam_toolbox` ใน ROS 2 ได้
3. สามารถสำรวจสภาพแวดล้อมและบันทึกแผนที่ Occupancy Grid เป็นไฟล์ `.pgm` และ `.yaml` ได้อย่างถูกต้อง

### 🛠️ เครื่องมือที่ใช้
- โลกจำลอง Webots: `052_slam.wbt` (หุ่นยนต์ติด LiDAR 360°, รัศมีล้อ 0.08m, ระยะห่างล้อ 0.24m)
- คอนโทรลเลอร์: `052_slam_controller`
- โหนด ROS 2: `async_slam_toolbox_node` จากแพ็กเกจ `slam_toolbox`
- โปรแกรมแสดงผล: `rviz2`

### 📝 ขั้นตอนการทดลอง

#### ตอนที่ 1: เปิดการจำลองและเผยแพร่ข้อมูลเซนเซอร์
เปิด Terminal ที่ 1 แล้วรันคำสั่ง:
```bash
# เปิด Webots พร้อมรันโหนด SLAM Controller ในแพ็กเกจ ce_webots
ros2 launch ce_webots slam_mapping.launch.py
```
> **ข้อสังเกต:** โหนดจะเผยแพร่ท็อปปิก `/scan` (LaserScan), `/odom` (Odometry), และ TF Frames: `odom -> base_link -> lidar_link`

#### ตอนที่ 2: รันโหนด SLAM Toolbox
เปิด Terminal ที่ 2 แล้วรันคำสั่ง:
```bash
ros2 run slam_toolbox async_slam_toolbox_node --ros-args \
  --params-file "/Volumes/ExDisk/Google Drive Ksu/KSU/Git/ROS/3_Nav2/config/slam_toolbox_params.yaml"
```

#### ตอนที่ 3: เปิด RViz2 ตรวจสอบการสร้างแผนที่สด
เปิด Terminal ที่ 3 แล้วรันคำสั่ง:
```bash
rviz2 -d "/Volumes/ExDisk/Google Drive Ksu/KSU/Git/ROS/3_Nav2/rviz/nav2_default_view.rviz"
```
- ในหน้าต่าง RViz2 จะมองเห็นแผนที่สีเทา/ดำ/ขาว กำลังขยายตัวตามที่หุ่นยนต์เคลื่อนที่
- สังเกตการกระจายตัวของจุดเลเซอร์สีแดง/รุ้งที่กระทบขอบกำแพง

#### ตอนที่ 4: บังคับหุ่นยนต์สำรวจพื้นที่ให้รอบคอบ
- คลิกที่หน้าต่าง Dashboard ของ `052_slam_controller`
- กดปุ่ม `M` เพื่อสลับเป็นโหมดสำรวจอัตโนมัติ (Auto Mode) หรือใช้ปุ่ม `W/A/S/D` ในการขับหุ่นยนต์ด้วยตนเอง
- ขับวนรอบโกดังให้เกิด **Loop Closure** (เมื่อหุ่นยนต์วนกลับมาที่จุดเริ่มต้น โหนด SLAM จะดึงแนวผนังให้ตรงกันโดยอัตโนมัติ)

#### ตอนที่ 5: บันทึกแผนที่ด้วย `save_map`
เปิด Terminal ที่ 4 เพื่อสั่งบันทึกแผนที่:
```bash
ros2 run ce_webots save_map --ros-args \
  -p map_name:=my_warehouse_map \
  -p output_dir:=/Volumes/ExDisk/Google\ Drive\ Ksu/KSU/Git/ROS/3_Nav2/maps
```
ตรวจสอบว่ามีไฟล์ `my_warehouse_map.pgm` และ `my_warehouse_map.yaml` ถูกสร้างขึ้นเรียบร้อยแล้ว

---

## Lab 3.2: Map Server และการระบุตำแหน่งหุ่นยนต์ด้วย AMCL

### 🎯 วัตถุประสงค์
1. เข้าใจหลักการทำงานของ Map Server ในการอ่านไฟล์ภาพ PGM และส่งข้อมูลเป็น Occupancy Grid
2. เข้าใจการทำงานของ Adaptive Monte Carlo Localization (AMCL) และแบบจำลอง Particle Filter
3. สามารถตั้งค่าพิกัดเริ่มต้น (Initial Pose) ทั้งผ่าน GUI RViz และโค้ด Python ได้

### 📝 ขั้นตอนการทดลอง

#### ตอนที่ 1: รัน Map Server ให้บริการแผนที่
เปิด Terminal ที่ 1:
```bash
ros2 run nav2_map_server map_server --ros-args \
  -p yaml_filename:="/Volumes/ExDisk/Google Drive Ksu/KSU/Git/ROS/3_Nav2/maps/warehouse_map.yaml" \
  -p use_sim_time:=true
```

เปลี่ยนสถานะ Lifecycle Node ให้ Active:
```bash
ros2 run nav2_util lifecycle_bringup map_server
```

#### ตอนที่ 2: รัน AMCL Localization Node
เปิด Terminal ที่ 2:
```bash
ros2 run nav2_amcl amcl --ros-args \
  --params-file "/Volumes/ExDisk/Google Drive Ksu/KSU/Git/ROS/3_Nav2/config/nav2_params.yaml" \
  -p use_sim_time:=true
```

เปิดสถานะ Lifecycle Node ของ AMCL:
```bash
ros2 run nav2_util lifecycle_bringup amcl
```

#### ตอนที่ 3: กำหนดพิกัดเริ่มต้นให้หุ่นยนต์ (Initial Pose Estimation)
ทดสอบ 2 วิธี:
1. **ผ่าน RViz2 GUI:** คลิกเครื่องมือ `2D Pose Estimate` ด้านบน แล้วคลิกลากลูกศรบนแผนที่ตรงจุดกำเนิด `(0, 0)` หันหัวไปทางทิศเหนือ ($90^\circ$)
2. **ผ่านสคริปต์อัตโนมัติ (Automated Python):**
   ```bash
   python3 "/Volumes/ExDisk/Google Drive Ksu/KSU/Git/ROS/3_Nav2/src/amcl_initial_pose.py" --ros-args \
     -p x:=0.0 -p y:=0.0 -p theta:=1.5708
   ```

#### ตอนที่ 4: ทดสอบ Kidnapped Robot Problem
- ย้ายตำแหน่งหุ่นยนต์ในโลกจำลอง Webots ไปไว้ที่จุดอื่นทันที
- สังเกตการกระจายตัวของอนุภาค Particle Cloud (ลูกศรสีเขียวใน RViz)
- ขับหุ่นยนต์เดินหน้า-เลี้ยว แล้วบันทึกจำนวนรอบการหมุนที่อนุภาคใช้ในการยุบตัวรวมเป็นกลุ่มก้อนเดียว (Convergence)

---

## Lab 3.3: การนำทางสู่เป้าหมายอัตโนมัติและการปรับแต่ง Costmap 2D

### 🎯 วัตถุประสงค์
1. เข้าใจกลไกการทำงานของ Global Planner (Navfn) และ Local Controller (DWB)
2. วิเคราะห์ผลกระทบของ Inflation Radius และ Cost Scaling Factor ต่อเส้นทางการเคลื่อนที่
3. สั่งนำทางไปยังเป้าหมายพิกัดที่กำหนด พร้อมสังเกตพฤติกรรมการหลบหลีกสิ่งกีดขวางแบบเรียลไทม์

### 📝 ขั้นตอนการทดลอง

#### ตอนที่ 1: รัน Nav2 Stack แบบเต็มรูปแบบ
เปิด Terminal ที่ 1:
```bash
ros2 launch "/Volumes/ExDisk/Google Drive Ksu/KSU/Git/ROS/3_Nav2/launch/nav2_bringup.launch.py"
```

เปิด Terminal ที่ 2 เพื่อตั้งพิกัดเริ่มต้น:
```bash
python3 "/Volumes/ExDisk/Google Drive Ksu/KSU/Git/ROS/3_Nav2/src/amcl_initial_pose.py" --ros-args -p x:=0.0 -p y:=0.0 -p theta:=0.0
```

#### ตอนที่ 2: สั่งเป้าหมายด้วย 2D Goal Pose
1. เปิด RViz2 ตรวจสอบว่ามองเห็นเลเยอร์:
   - **Global Costmap** (สีรุ้งรอบกำแพง)
   - **Local Costmap** (สี่เหลี่ยม 3x3m รอบตัวหุ่นยนต์)
2. คลิกปุ่ม `Nav2 Goal` (หรือ `2D Goal Pose`) บนแถบเครื่องมือของ RViz2
3. คลิกจุดเป้าหมายในบริเวณช่องทางเดินคลังสินค้า เช่น พิกัด $(x=3.5, y=-2.5)$
4. สังเกต:
   - เส้นทางสีเขียว/น้ำเงินจาก Global Planner
   - เวกเตอร์ Trajectory ย่อยที่ DWB Controller คำนวณออกมาเพื่อหมุนและเร่งความเร็ว

#### ตอนที่ 3: การปรับแต่ง Costmap Inflation (Tuning Experiment)
เปิดไฟล์ [`config/nav2_params.yaml`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/3_Nav2/config/nav2_params.yaml) และทดลองปรับค่า:
```yaml
inflation_layer:
  cost_scaling_factor: 1.5   # จากเดิม 2.5 (ยิ่งน้อย ขอบเขตสีแดงจะแผ่กว้างขึ้น)
  inflation_radius: 0.85      # จากเดิม 0.65 (เพิ่มรัศมีความปลอดภัย)
```
- บันทึกความแตกต่างของระยะห่างระหว่างตัวหุ่นยนต์กับกำแพงขณะเข้าโค้ง
- สังเกตกรณีที่ทางเดินแคบเกินไป จน Global Planner แจ้งเตือน `Failed to find a valid plan`

---

## Lab 3.4: การเขียนโปรแกรมลาดตระเวน Multi-Waypoint Patrol ด้วย BasicNavigator API

### 🎯 วัตถุประสงค์
1. สามารถเขียนโปรแกรมภาษา Python สั่งการ Nav2 Stack ผ่าน `nav2_simple_commander` หรือ ROS 2 Action Client
2. ควบคุมหุ่นยนต์เคลื่อนที่ผ่านจุดตรวจ (Waypoints) ลาดตระเวนในคลังสินค้าตามลำดับ
3. จัดการสถานะการรอคอย (Dwell Time), การอ่านค่า Feedback (ระยะทางคงเหลือ), และการรับมือข้อผิดพลาด (Failure Recovery)

### 📝 ขั้นตอนการทดลอง

#### ตอนที่ 1: ศึกษาโค้ดโครงสร้างลาดตระเวน
ตรวจสอบไฟล์ [`src/waypoint_patrol.py`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/3_Nav2/src/waypoint_patrol.py) โดยดูรายการจุด Waypoints ทั้ง 5 จุด:
1. **Station 1**: รับสินค้าเข้า (Receiving Dock) $\rightarrow (x=2.5, y=3.5)$
2. **Station 2**: ช่องเก็บสินค้าแถว B $\rightarrow (x=3.5, y=-2.5)$
3. **Station 3**: จุดตรวจคุณภาพสินค้า (QC Station) $\rightarrow (x=-3.0, y=-3.5)$
4. **Station 4**: แท่นจัดส่งสินค้า (Packaging Bay) $\rightarrow (x=-3.0, y=3.5)$
5. **Station 5**: แท่นชาร์จไฟ / จุดเริ่มต้น (Home) $\rightarrow (x=0.0, y=0.0)$

#### ตอนที่ 2: รันภารกิจลาดตระเวนอัตโนมัติ
เปิด Terminal แล้วรัน:
```bash
python3 "/Volumes/ExDisk/Google Drive Ksu/KSU/Git/ROS/3_Nav2/src/waypoint_patrol.py"
```

#### ตอนที่ 3: สังเกตและบันทึกข้อมูลการปฏิบัติงาน
- สังเกตหน้าจอคอนโซลที่รายงานค่าความคืบหน้าระหว่างเดินทาง:
  ```text
  📍 [1/5] Navigating to: Station 1: Inbound Receiving Dock
     Target: X=2.50, Y=3.50, Yaw=0.0°
     ⏳ Distance remaining: 1.42 m | ETA: 3s
     ✅ Arrived at Station 1: Inbound Receiving Dock! Performing task for 3.0s...
  ```
- ทดลองวางสิ่งกีดขวางกีดขวางเส้นทางใน Webots ระหว่างที่หุ่นยนต์กำลังเคลื่อนที่
- สังเกตการทำงานของ Behavior Recovery (หุ่นยนต์จะพยายามหมุนตัว หรือรอจนกระทั่ง Costmap อัปเดตและคำนวณเส้นทางเลี่ยงใหม่)

---

## คำถามท้ายการทดลองและการประเมินผล

### ❓ คำถามท้ายบท (Post-Lab Questions)
1. **เปรียบเทียบ SLAM และ Localization**: เหตุใดเมื่อมีแผนที่ที่สมบูรณ์แล้ว เราจึงควรใช้ `AMCL` แทนการเปิด `slam_toolbox` ตลอดเวลา?
2. **Costmap Tuning**: หากหุ่นยนต์มีอาการสะบัดหรือสั่นเมื่อวิ่งเข้าใกล้ขอบประตูแคบ ควรปรับค่าพารามิเตอร์ใดใน DWB Controller และ Costmap Inflation Layer เพราะเหตุใด?
3. **TF Coordinate Frame**: อธิบายความแตกต่างระหว่างเฟรม `map` และ `odom` ทำไมหุ่นยนต์จึงไม่สามารถนำทางระยะไกลโดยใช้เฟรม `odom` เพียงอย่างเดียวได้?
4. **Recovery Behaviors**: หากหุ่นยนต์เข้าสู่สถานะติดขัด (Stuck) ใน Behavior Tree จะมีลำดับขั้นตอนในการกู้คืนสถานะอย่างไรบ้าง?

### 📊 เกณฑ์การให้คะแนน (Evaluation Rubrics - 100%)
| หัวข้อประเมิน | สัดส่วน | รายละเอียดเกณฑ์ |
|---|---|---|
| **1. แผนที่ SLAM (Lab 3.1)** | 25% | แผนที่มีความคมชัด ไม่มีภาพซ้อน (No Ghosting), มี Loop Closure สมบูรณ์, สเกลถูกต้อง |
| **2. ความแม่นยำ AMCL (Lab 3.2)** | 25% | ตั้งพิกัด Initial Pose ถูกต้อง, อนุภาค Particle ลู่เข้าตำแหน่งจริงได้รวดเร็ว, ค่าความคลาดเคลื่อน $< 0.15\text{m}$ |
| **3. การนำทางและ Costmap (Lab 3.3)** | 25% | วิ่งเข้าเป้าหมายได้โดยไม่ชนสิ่งกีดขวาง, ปรับจูน Costmap ให้เคลื่อนที่ผ่านช่องแคบได้ราบรื่น |
| **4. สคริปต์ Waypoint Patrol (Lab 3.4)** | 25% | หุ่นยนต์วิ่งครบทั้ง 5 จุดตามลำดับ, มี Dwell time ถูกต้อง, จัดการข้อผิดพลาดและแสดงผลสถานะครบถ้วน |
