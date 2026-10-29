# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 6: มาตรฐานวิศวกรรมพิกัด และจลนศาสตร์ AMR
**วิชา:** AMR-101 Essential ROS 2 for Autonomous Mobile Robots  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** พื้นฐาน (Beginner)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายสัปดาห์ที่ 6](Readme.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. รันและทดสอบโหนดคำนวณจลนศาสตร์ `diff_drive_kinematics` ตามมาตรฐาน REP 103/105 (Odometry + TF `odom → base_footprint`)
2. พิสูจน์ความสัมพันธ์ระหว่างคำสั่งความเร็วหุ่นยนต์ `/cmd_vel` กับความเร็วรอบของล้อซ้าย-ขวา
3. วิเคราะห์ผลการประมาณตำแหน่งสะสม (Odometry Dead Reckoning) ในการวิ่งเป็นเส้นตรงและการหมุนตัวอยู่กับที่
4. คำนวณความคลาดเคลื่อนสะสม (Odometry Drift) เมื่อหุ่นยนต์เคลื่อนที่เป็นรูปสี่เหลี่ยมจัตุรัส

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่รูทไดเรกทอรีของ repository วิชา
- Build แพ็กเกจ `amr_week06` (ament_python) — หลัง build แล้ว `run_lab.sh` จะ source `install/setup.bash` ให้อัตโนมัติ:
  ```bash
  ./docker/run_lab.sh colcon build --base-paths Essential_ROS --packages-select amr_week06
  # หรือ: make build PKG=amr_week06      ชุดทดสอบอัตโนมัติ: make test PKG=amr_week06
  ```
- ตั้ง `ROS_DOMAIN_ID` ของตนเองและ `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` ก่อนเรียก `run_lab.sh` ทุก Terminal

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 6.1: การเปิดโหนดจลนศาสตร์และตรวจสอบสถานะเริ่มต้น
**เป้าหมาย:** สังเกตพิกัดเริ่มต้น $(0, 0, 0)$ ของ Odometry

1. เปิด **Terminal 1** แล้วรันโหนดจลนศาสตร์:
   ```bash
   ./docker/run_lab.sh ros2 run amr_week06 diff_drive_kinematics
   # แบบไม่ build: ./docker/run_lab.sh python3 Essential_ROS/Week_06_Kinematics_REP_Standards/src/diff_drive_kinematics.py
   ```
   **ผลลัพธ์จริง:**
   ```text
   [INFO] [1793242902.560118803] [diff_drive_kinematics]: 🤖 [DiffDriveKinematics] Ready: L=0.24m, r=0.08m, integration=midpoint, cmd_vel_timeout=0.5s
   ```

2. เปิด **Terminal 2** แล้วดักฟังข้อความ Odometry:
   ```bash
   ./docker/run_lab.sh ros2 topic echo /odom_calculated --field pose.pose
   ```
   *สังเกต:* พิกัดตำแหน่ง $x, y, z$ เริ่มต้นที่ $0.0$ และควอเทอร์เนียน $x=0, y=0, z=0, w=1$ (ตรงกับมุม $\theta = 0^\circ$) — ผลจริง (`--once`):
   ```text
   position:
     x: 0.0
     y: 0.0
     z: 0.0
   orientation:
     x: 0.0
     y: 0.0
     z: 0.0
     w: 1.0
   ---
   ```

3. ตรวจสอบความถี่ของวงรอบการคำนวณ:
   ```bash
   ./docker/run_lab.sh ros2 topic hz /odom_calculated
   ```
   *ตรวจสอบว่าความถี่เฉลี่ยอยู่ที่ประมาณ 20 Hz* (ผลจริง: `average rate: 19.995`)

---

### 🔹 Lab 6.2: การทดสอบวิ่งตรง (Forward Motion Verification)
**เป้าหมาย:** ทดสอบการเคลื่อนที่ไปข้างหน้าตามแนวแกน +X

1. ให้ Terminal 1 และ 2 เปิดค้างไว้
2. เปิด **Terminal 3** แล้วสั่งความเร็ว $v = 0.2$ m/s เป็นเวลา 5 วินาที (`-t 50` = ส่ง 50 ครั้งที่ 10 Hz แล้วหยุดเอง):
   ```bash
   ./docker/run_lab.sh ros2 topic pub -r 10 -t 50 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: 0.0}}"
   ```
3. สังเกตการเปลี่ยนแปลงพิกัดใน Terminal 2:
   - ค่า $x$ จะค่อยๆ เพิ่มขึ้นวินาทีละประมาณ $0.2$ เมตร
   - ค่า $y$ และค่าควอเทอร์เนียน $z$ จะคงที่อยู่ที่ประมาณ $0.0$
4. เมื่อคำสั่งหยุดมา **Watchdog** ของโหนด (`cmd_vel_timeout` = 0.5 s) จะสั่งหยุดล้อเองและ Terminal 1 พิมพ์ `No cmd_vel for 0.50 s (> 0.5 s): stopping wheels` ผลจริงหลังหยุด 1 วินาที:
   ```text
   position:
     x: 1.0800343727999997
     y: 0.0
     z: 0.0
   orientation:
     x: 0.0
     y: 0.0
     z: 0.0
     w: 1.0
   ---
   ```
   **คำถาม:** ทำไมได้ $x = 1.08$ m ไม่ใช่ 1.00 m? (ใบ้: ล้อยังทำตามคำสั่งสุดท้ายจนกว่า Watchdog จะทำงาน) — ถ้าต้องการเบรกทันทีให้ส่งความเร็ว 0: `ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"`

---

### 🔹 Lab 6.3: การทดสอบหมุนตัวอยู่กับที่ (In-Place Rotation Verification)
**เป้าหมาย:** ตรวจสอบการหมุนรอบแกน Z (+Yaw ทวนเข็มนาฬิกา)

1. ใน **Terminal 3** ส่งคำสั่งหมุนตัว $\omega = 0.5$ rad/s โดยที่ $v = 0.0$:
   ```bash
   ./docker/run_lab.sh ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.5}}"
   ```
2. สังเกตค่าใน Terminal 2:
   - ค่าพิกัด $x, y$ ยังคงอยู่ที่ตำแหน่งเดิม (ไม่ขยับ)
   - ค่าควอเทอร์เนียน $z$ และ $w$ จะเปลี่ยนแปลงอย่างต่อเนื่องตามสูตร $z = \sin(\theta/2), w = \cos(\theta/2)$
3. หยุดการส่งคำสั่ง (`Ctrl+C`) หลังจากผ่านไปประมาณ 6.28 วินาที (หมุนครบ 1 รอบ $2\pi$ เรเดียน) — อย่าลืมว่า Watchdog ทำให้หมุนต่ออีกไม่เกิน 0.5 วินาที ($\approx 0.25$ rad)
4. ดู Transform ที่โหนด Broadcast ลง `/tf`:
   ```bash
   ./docker/run_lab.sh ros2 run tf2_ros tf2_echo odom base_footprint
   ```
   ผลจริง (หลังวิ่งตรงแล้วหมุนด้วย `-t 31`):
   ```text
   At time 1793242933.846810339
   - Translation: [1.080, 0.000, 0.000]
   - Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.768, 0.641]
   - Rotation: in RPY (radian) [0.000, -0.000, 1.750]
   - Rotation: in RPY (degree) [0.000, -0.000, 100.268]
   - Matrix:
    -0.178 -0.984  0.000  1.080
     0.984 -0.178  0.000  0.000
     0.000  0.000  1.000  0.000
   ```

   **คำถาม Checkpoint 6.3:**
   - [ ] ขณะหุ่นยนต์หมุนตัวอยู่กับที่ ล้อซ้ายและล้อขวามีทิศทางการหมุนและความเร็วอย่างไร?
   - [ ] ค่าควอเทอร์เนียน $(z, w)$ เมื่อหมุนครบ $180^\circ$ ($\pi$ rad) จะมีค่าประมาณเท่าใด? ($z \approx 1.0, w \approx 0.0$)

---

### 🔹 Lab 6.4: การจำลองการเคลื่อนที่สี่เหลี่ยมจัตุรัสและวิเคราะห์ Drift
**เป้าหมาย:** สังเกตพฤติกรรม Closed-Loop Path (เดินวน 1 รอบแล้วกลับมาที่จุดเดิม)

1. ให้นักศึกษาส่งคำสั่งเป็นลำดับ 4 ขั้นตอน (ด้วยมือ หรือใช้โปรแกรม [`src/square_driver.py`](src/square_driver.py) ที่สตรีม `/cmd_vel` ตามเวลาที่ 10 Hz):
   - เดินหน้าตรง $1.0$ เมตร
   - หมุนตัวซ้าย $90^\circ$ ($\pi/2$ rad)
   - ทำซ้ำจนครบ 4 ด้าน
   ```bash
   ./docker/run_lab.sh ros2 run amr_week06 diff_drive_kinematics          # Terminal 1 (เริ่มใหม่ที่จุด 0,0)
   ./docker/run_lab.sh ros2 run amr_week06 square_driver --csv square_odom.csv   # Terminal 2
   ```
2. บันทึกพิกัดสุดท้าย $(x_{\text{final}}, y_{\text{final}}, \theta_{\text{final}})$ — ผลจริง:
   ```text
   [INFO] [1793243102.916294032] [square_driver]: final pose relative to start: x=+0.0353 m  y=-0.0571 m  yaw=+5.26 deg
   [INFO] [1793243102.916868263] [square_driver]: loop closure error sqrt(dx^2+dy^2) = 0.0672 m
   ```
3. คำนวณความคลาดเคลื่อนสะสม (Loop Closure Error):
   $$\text{Error} = \sqrt{x_{\text{final}}^2 + y_{\text{final}}^2}$$

---

## 🏆 โจทย์ท้าทายระดับสูง (Challenge Exercises)
1. **Challenge 6.1:** เติมค่า `pose.covariance` และ `twist.covariance` (เมทริกซ์ 6×6) ในข้อความ Odometry ให้สมเหตุสมผล (เช่น ความแปรปรวนของ $x, y$ โตตามระยะทางสะสม) แล้วอธิบายว่า EKF ของ `robot_localization` จะใช้ค่านี้อย่างไร
2. **Challenge 6.2:** รัน Lab 6.4 ซ้ำด้วย `--ros-args -p integration:=euler` และ `-p integration:=exact` เทียบกับ `midpoint` แล้วเขียนเทสต์ใน `test/test_kinematics.py` ที่แสดงว่า Error ของ Euler ลดลงแบบ $O(\Delta t)$ ขณะที่ Midpoint ลดแบบ $O(\Delta t^2)$

---

## 📦 สิ่งที่ต้องส่ง (Deliverables Checklist)
- [ ] ภาพบันทึกหน้าจอผลการทดสอบใน Lab 6.1 แสดงค่า Odometry เริ่มต้น
- [ ] ตารางบันทึกค่าพิกัด $(x, y, \theta)$ ในการวิ่งตรง (Lab 6.2) และการหมุนตัว (Lab 6.3)
- [ ] ผลการคำนวณ Loop Closure Error จากการเดินสี่เหลี่ยมจัตุรัสใน Lab 6.4
- [ ] คำตอบ Checkpoint 6.3

---

## 📊 เกณฑ์การประเมินผล (Lab Grading Rubric - 100 คะแนน)
| รายการประเมิน | รายละเอียดการให้คะแนน | คะแนนเต็ม |
| :--- | :--- | :---: |
| **การทดสอบความถี่และสถานะเริ่มต้น** | รันโหนดและวัดความถี่ 20 Hz บนท็อปปิก `/odom_calculated` ได้ถูกต้อง | 20 |
| **การทดสอบ Forward Kinematics** | ส่งคำสั่งวิ่งตรงและวิเคราะห์ความสัมพันธ์ของแกน X ได้ถูกต้อง | 25 |
| **การทดสอบ In-Place Rotation** | ส่งคำสั่งหมุนตัวและแปลงค่า Quaternion สู่มุมเรเดียนได้ถูกต้อง | 25 |
| **การวิเคราะห์ Closed-Loop Error** | ดำเนินการทดสอบสี่เหลี่ยมและคำนวณค่า Drift ได้สมบูรณ์ | 20 |
| **ความเรียบร้อยของรายงานและโจทย์ท้าทาย** | รายงานละเอียด กราฟหรือภาพประกอบชัดเจน | 10 |
| **รวม** | | **100** |

---

## ⚠️ การแก้ปัญหาที่พบบ่อยในแล็บ (Troubleshooting)
| ปัญหา | สาเหตุ | การแก้ไข |
| :--- | :--- | :--- |
| ค่า Odometry พุ่งไปไกลผิดปกติ | ค่า $\Delta t$ เกิด Spike ขนาดใหญ่จากเครื่องหน่วง | ใส่ Safety Clamp จำกัดค่า $\Delta t \le 0.1$ วินาที |
| หุ่นยนต์ขยับแค่แวบเดียวแล้วหยุด | ใช้ `--once` ส่งครั้งเดียว Watchdog จึงหยุดล้อหลัง 0.5 วินาที | ใช้ `-r 10` (และ `-t N`) เพื่อส่งคำสั่งต่อเนื่อง 10 Hz |
| หุ่นยนต์หมุนทวนเข็มแต่มุมเป็นลบ | สลับแกน Z หรือคำนวณสมการ Inverse Kinematics ผิด | ตรวจสอบว่า $\omega = (v_R - v_L) / L$ |


## 📟 ผลการรันจริง (Real Run Output)
บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29 — ไฟล์เต็ม: [`results/kinematics_lab_run.txt`](results/kinematics_lab_run.txt), [`results/square_run.txt`](results/square_run.txt)

```console
$ ros2 run amr_week06 square_driver --csv square_odom.csv     # terminal 2
[INFO] [1793243067.818953481] [square_driver]: Waiting for diff_drive_kinematics...
[INFO] [1793243068.836069842] [square_driver]: side 1: 1.0 m straight, then turn 90 deg
[INFO] [1793243077.155339408] [square_driver]: side 2: 1.0 m straight, then turn 90 deg
[INFO] [1793243085.375468828] [square_driver]: side 3: 1.0 m straight, then turn 90 deg
[INFO] [1793243093.655505876] [square_driver]: side 4: 1.0 m straight, then turn 90 deg
[INFO] [1793243102.916294032] [square_driver]: final pose relative to start: x=+0.0353 m  y=-0.0571 m  yaw=+5.26 deg
[INFO] [1793243102.916868263] [square_driver]: loop closure error sqrt(dx^2+dy^2) = 0.0672 m
[INFO] [1793243102.918410822] [square_driver]: odometry log written to square_odom.csv

$ ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.4}, angular: {z: 0.2}}"
Waiting for at least 1 matching subscription(s)...
Waiting for at least 1 matching subscription(s)...
Waiting for at least 1 matching subscription(s)...
publisher: beginning loop
publishing #1: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=0.4, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.2))

$ ros2 topic echo /odom_calculated --field twist.twist --once   # 2 s later: watchdog stopped the wheels
linear:
  x: 0.0
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 0.0
---
```

![Real /odom_calculated trajectory of the Lab 6.4 square run](images/square_odom.png)

*ภาพ: เส้นทางจริงจาก `/odom_calculated` ของ Lab 6.4 ([`results/square_odom.csv`](results/square_odom.csv) พล็อตด้วย matplotlib) — ความคลาดเคลื่อน 0.067 m มาจากจังหวะเวลาของคำสั่งแบบ Open-loop ไม่ใช่จากสมการจลนศาสตร์*

---

