# 📝 ใบสั่งงานข้อสอบปฏิบัติการกลางภาค (Midterm Exam Task Specification)
**วิชา:** AMR-101 Essential ROS 2 for Autonomous Mobile Robots  
**เวลาสอบ:** 3 ชั่วโมง (180 นาที)  
**โจทย์สถานการณ์:** การพัฒนาระบบหุ่นยนต์ขนส่งเวชภัณฑ์ในโรงพยาบาล (Hospital Logistics AMR)

---

## 🏥 สถานการณ์จำลอง (Scenario Context)
โรงพยาบาลศูนย์การแพทย์ต้องการนำหุ่นยนต์อัตโนมัติ (AMR) มาใช้งานส่งถุงยาและเวชภัณฑ์ระหว่างห้องยาและหอผู้ป่วย โดยหุ่นยนต์จะต้องมีโครงสร้างตัวถังขนาดใหญ่พอที่จะบรรทุกกล่องยา มีความปลอดภัยสูงโดยต้องจำกัดความเร็วไม่ให้เกินมาตรฐานความปลอดภัยในอาคารที่มีผู้ป่วยเดินสัญจร และมีระบบตรวจสอบความร้อนของมอเตอร์และแบตเตอรี่เพื่อป้องกันอัคคีภัย

---

## 📦 สิ่งที่ต้องส่ง (Submission Layout)
ส่งโฟลเดอร์เดียว (เช่น `submissions/<รหัสนักศึกษา>/`) ที่มีไฟล์ 3 ไฟล์ **ชื่อตรงตามนี้** (ระบบตรวจอัตโนมัติจะค้นหาจากชื่อไฟล์):

| ไฟล์ | ตอน | หมายเหตุ |
| :--- | :---: | :--- |
| `hospital_amr.urdf` | 1 | ใช้ชื่อลิงก์ตามตารางด้านล่าง |
| `hospital_robot_node.py` | 2 | ต้องรันได้ด้วย `python3 hospital_robot_node.py` (มี `if __name__ == '__main__': main()`) |
| `hospital_bringup.launch.py` | 3 | ต้องรองรับ launch argument `rviz` (`rviz:=false` สำหรับเครื่องตรวจที่ไม่มีจอ) |

> [!NOTE]
> **การแก้ไขโจทย์ (2026-10-29):** สเปกฉบับก่อนกำหนดล้อที่ $y = \pm 0.12$ m ซึ่งอยู่ **ภายใน** ตัวถังกว้าง $0.30$ m (ขอบตัวถังที่ $y = \pm 0.15$ m) — ล้อจะทะลุตัวถังและเป็นไปไม่ได้ทางกายภาพ
> สเปกนี้จึงแก้ให้สอดคล้องกันโดยเปลี่ยนแปลงให้น้อยที่สุด: (1) ระยะห่างล้อ $L = 0.34$ m ($y = \pm 0.17$ m) ให้ล้อหนา $0.04$ m อยู่นอกตัวถังพอดี (2) ระบุตำแหน่งความสูงของกล่องตัวถังและขนาด LiDAR เพื่อให้ LiDAR ที่ $z = 0.18$ m วางบนหลังคาพอดีไม่จมในตัวถัง (3) ระบุพฤติกรรม "จำกัดความเร็ว" เป็นตัวเลข (50%) เพื่อให้ตรวจได้

---

## 📋 ข้อกำหนดโจทย์เชิงวิศวกรรม (Engineering Specifications)

### 🔹 ตอนที่ 1: การสร้างแบบจำลอง 3 มิติ URDF (`hospital_amr.urdf`) - 35 คะแนน
สร้างไฟล์ URDF โดยมีรายละเอียดทางกลศาสตร์ดังนี้ (พิกัดทั้งหมดอ้างอิงกรอบ `base_link` ซึ่งอยู่ที่แกนล้อ, ตาม REP 103: X หน้า, Y ซ้าย, Z ขึ้น):

| ลิงก์ (ชื่อบังคับ) | Joint จาก parent | ตำแหน่ง Origin |
| :--- | :--- | :--- |
| `base_footprint` | (root) | ระนาบพื้น $z = 0$ |
| `base_link` | `fixed` จาก `base_footprint` | $z = 0.08$ m (= รัศมีล้อ) |
| `left_wheel_link` / `right_wheel_link` | `continuous` จาก `base_link` | $(0, \pm 0.17, 0)$ |
| `front_caster_link` / `rear_caster_link` | `fixed` จาก `base_link` | $(\pm 0.18, 0, -0.05)$ |
| `lidar_link` | `fixed` จาก `base_link` | $(0.12, 0, 0.18)$, ไม่หมุน (`rpy="0 0 0"`) |

1. **ตัวถังหลัก (Chassis `base_link`):**
   - รูปทรง: กล่องสี่เหลี่ยม (Box) ยาว $d = 0.50$ m (แกน X), กว้าง $w = 0.30$ m (แกน Y), สูง $h = 0.15$ m (แกน Z) — `<box size="0.50 0.30 0.15"/>`
   - ตำแหน่งกล่อง (`<origin>` ของ visual/collision/inertial): $z = +0.055$ m ⇒ ท้องรถอยู่ที่ $z = -0.02$ m และหลังคาที่ $z = 0.13$ m ใน `base_link`
   - มวลรวม: $m = 8.0$ kg, สี: น้ำเงินเข้ม (`chassis_blue`)
   - เมทริกซ์ความเฉื่อย: คำนวณจากสูตร Solid Box:
     $$I_{xx} = \frac{1}{12} m (w^2 + h^2) = 0.075000 \text{ kg}\cdot\text{m}^2$$
     $$I_{yy} = \frac{1}{12} m (d^2 + h^2) = 0.181667 \text{ kg}\cdot\text{m}^2$$
     $$I_{zz} = \frac{1}{12} m (d^2 + w^2) = 0.226667 \text{ kg}\cdot\text{m}^2$$
2. **ล้อขับเคลื่อนซ้าย-ขวา (Drive Wheels):**
   - ชนิดข้อต่อ: `type="continuous"` หมุนรอบแกน Y (`<axis xyz="0 1 0"/>`)
   - ขนาด: เส้นผ่านศูนย์กลาง $0.16$ m (รัศมี $r = 0.08$ m), ความหนา $0.04$ m
   - มวล: ข้างละ $0.80$ kg
   - ระยะห่างระหว่างกึ่งกลางล้อซ้ายและขวา: $L = 0.34$ m ($y = +0.17$ และ $y = -0.17$) — ผิวล้อด้านในอยู่ที่ $|y| = 0.15$ m พอดีกับขอบตัวถัง
   - ความเฉื่อย (ในกรอบของลิงก์ล้อ): $I_{yy} = 0.002560 \text{ kg}\cdot\text{m}^2$ (แกนหมุน), $I_{xx} = I_{zz} = 0.001387 \text{ kg}\cdot\text{m}^2$
     *(ระวัง: ถ้าหมุน `<inertial><origin rpy>` ตาม visual ค่าแกนหมุนต้องย้ายไปไว้ที่ `izz` — ระบบตรวจคำนวณโมเมนต์รอบแกนหมุนจริงเสมอ)*
3. **ล้อพยุงอิสระ Caster Wheels (หน้าและหลัง):**
   - ทรงกลมรัศมี $0.03$ m มวล $0.25$ kg ($I = \frac{2}{5}mr^2 = 0.000090$) อยู่ที่ $x = +0.18$ m และ $x = -0.18$ m, $z = -0.05$ m สัมผัสระนาบพื้นพอดี
4. **เซนเซอร์ LiDAR:**
   - ทรงกระบอกรัศมี $0.04$ m สูง $0.10$ m (รวมฐานยึด) มวล $0.30$ kg ติดตั้งบนหลังคาตัวถังที่พิกัด $x = 0.12$ m, $z = 0.18$ m จาก `base_link` (ฐาน LiDAR อยู่ที่ $0.18 - 0.05 = 0.13$ m = หลังคาพอดี)
5. **การทดสอบความถูกต้อง:**
   - รันคำสั่งตรวจสอบ:
     ```bash
     ./docker/run_lab.sh check_urdf submissions/<รหัสนักศึกษา>/hospital_amr.urdf
     ```
     *ต้องแสดงผล Successfully Parsed XML โดยไม่มี Warning ใดๆ*
   - (ไม่บังคับ) หากใส่ปลั๊กอิน `gz::sim::systems::DiffDrive` ค่า `wheel_separation` / `wheel_radius` ต้องเป็น $0.34$ / $0.08$

---

### 🔹 ตอนที่ 2: การพัฒนาโหนดควบคุมและความปลอดภัยใน Python (`hospital_robot_node.py`) - 40 คะแนน
พัฒนาโหนดชื่อ `midterm_robot_controller` ตามโครงสร้าง Class-based OOP:
1. **Dynamic Parameter & Safety Callback (15 คะแนน):**
   - ประกาศพารามิเตอร์ `max_speed` ชนิด `ParameterType.PARAMETER_DOUBLE` กำหนดค่าเริ่มต้น $0.6$ m/s
   - เชื่อมต่อฟังก์ชัน Callback ผ่าน `self.add_on_set_parameters_callback`
   - ตรวจสอบช่วงความปลอดภัย: หากผู้ใช้ตั้งค่าอยู่นอกช่วง $[0.1, 1.5]$ m/s (รวมขอบ) จะต้องตอบ `result.successful = False` พร้อมระบุเหตุผลใน `result.reason` และคงค่าเดิมไว้
2. **Velocity Command Publisher (10 คะแนน):**
   - สร้าง Publisher ส่งข้อความ `geometry_msgs/msg/Twist` ไปยังท็อปปิก `/cmd_vel`
   - ในลูปควบคุม (Timer 5 Hz) ให้ส่งความเร็ว $v = \min(0.3, \text{max\_speed})$ ใน `linear.x` และ `angular.z = 0.0`
3. **Sensor Temperature Monitor & Throttling (15 คะแนน):**
   - สร้าง Subscriber ดักฟังท็อปปิก `/sensor/temperature` (`std_msgs/msg/Float32`)
   - หากค่าล่าสุด **มากกว่า** $65.0^\circ\text{C}$ ให้พิมพ์ Warning Log สีเหลือง (`get_logger().warn`) และ **ลดความเร็วที่ส่งออก `/cmd_vel` ลงเหลือ 50%** ทันที (เช่น $0.3 \rightarrow 0.15$ m/s)
   - เมื่ออุณหภูมิกลับมา $\le 65.0^\circ\text{C}$ ให้กลับมาใช้ความเร็วปกติ

---

### 🔹 ตอนที่ 3: ระบบ Launch และการจำลองใน RViz2 (`hospital_bringup.launch.py`) - 25 คะแนน
1. เขียนไฟล์ Launch System เปิดโหนด `robot_state_publisher` โหลดไฟล์ `hospital_amr.urdf` และ `joint_state_publisher` (เพื่อให้ลิงก์ล้อปรากฏใน TF)
2. เปิดโหนด `midterm_robot_controller` ควบคู่กัน
3. เปิดหน้าต่าง `rviz2` เพื่อแสดงผลโมเดลและแกนพิกัด TF โดยประกาศ launch argument `rviz` (ค่าเริ่มต้น `true`) เพื่อให้ปิด RViz2 ได้ด้วย `rviz:=false`
4. ห้าม Hardcode พาธแบบ Absolute (เช่น `/home/student/...`)

---

## 🧪 คำสั่งทดสอบและตรวจให้คะแนนสำหรับกรรมการ (Grading Commands)
ชุดตรวจอัตโนมัติอยู่ใน [`test/`](test/) (แพ็กเกจ `amr_week08`) ตรวจโฟลเดอร์ที่ระบุใน `EXAM_SUBMISSION_DIR` (ค่าเริ่มต้น = [`solution/`](solution/) ซึ่งต้องผ่านทุกข้อ):

| ไฟล์ทดสอบ | ตอน | สิ่งที่ตรวจ |
| :--- | :---: | :--- |
| [`test_grade_part1_urdf.py`](test/test_grade_part1_urdf.py) | 1 | `check_urdf`, ชื่อลิงก์/ชนิด joint, ขนาด มวล ตำแหน่ง, Inertia (รวมแกนหมุนล้อจริง), ล้อ/caster แตะพื้น, ล้ออยู่นอกตัวถัง, LiDAR ไม่จม, Positive-definite |
| [`test_grade_part2_node.py`](test/test_grade_part2_node.py) | 2 | ค่าเริ่มต้น 0.6 (double), ปฏิเสธ 2.0 / 0.05 / 1.6 / จำนวนเต็ม พร้อม reason, `/cmd_vel` 5 Hz และ $v = \min(0.3, \text{max\_speed})$, 70 °C → WARN + ความเร็ว 50%, 65.0 °C ไม่ลด / 65.5 °C ลด, เย็นลงแล้วกลับปกติ |
| [`test_grade_part3_launch.py`](test/test_grade_part3_launch.py) | 3 | เปิด launch ด้วย `rviz:=false` แล้วตรวจว่ามีโหนดทั้งสอง, TF `base_footprint → lidar_link = (0.12, 0, 0.26)` และลิงก์ล้อ, `/cmd_vel` ถูกส่ง, ไฟล์มี `rviz2` |

```bash
# 0. Build ครั้งเดียว (ใน container) — ชุดตรวจใช้ amr_week07 (RViz config) และ amr_week08
./docker/run_lab.sh colcon build --base-paths Essential_ROS --packages-up-to amr_week08

# 1. ตรวจเฉลย (ต้องผ่านทั้งหมด)
./docker/run_lab.sh python3 -m pytest -v Essential_ROS/Week_08_Midterm_Practical_Exam/test/

# 2. ตรวจงานนักศึกษา: ชี้ EXAM_SUBMISSION_DIR ไปที่โฟลเดอร์ส่งงาน (พาธภายใน container: /workspace/...)
./docker/run_lab.sh bash -c 'EXAM_SUBMISSION_DIR=/workspace/submissions/6501234 \
    python3 -m pytest -v Essential_ROS/Week_08_Midterm_Practical_Exam/test/'

# 3. ดูรายละเอียดรายข้อของ launch test (ตอนที่ 2 / 3)
./docker/run_lab.sh bash -c 'EXAM_SUBMISSION_DIR=/workspace/submissions/6501234 \
    launch_test Essential_ROS/Week_08_Midterm_Practical_Exam/test/test_grade_part2_node.py'
```
> ตรวจหลายเครื่องพร้อมกันบนเครือข่ายเดียวกัน ให้ตั้ง `ROS_DOMAIN_ID` ต่างกันและ `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` ก่อนรัน (`run_lab.sh` ส่งต่อตัวแปรนี้ให้ container)

การตรวจแบบ Manual (ทีละคำสั่ง เหมือนในห้องสอบ):
```bash
./docker/run_lab.sh check_urdf Essential_ROS/Week_08_Midterm_Practical_Exam/solution/hospital_amr.urdf
./docker/run_lab.sh ros2 run amr_week08 hospital_robot_node          # เทอร์มินัลที่ 1
# หรือไฟล์ของนักศึกษา: ./docker/run_lab.sh python3 submissions/6501234/hospital_robot_node.py
./docker/run_lab.sh ros2 topic hz /cmd_vel                            # ~5 Hz
./docker/run_lab.sh ros2 topic echo --once /cmd_vel geometry_msgs/msg/Twist --field linear.x
./docker/run_lab.sh ros2 param set /midterm_robot_controller max_speed 1.0   # สำเร็จ
./docker/run_lab.sh ros2 param set /midterm_robot_controller max_speed 2.5   # ต้องถูกปฏิเสธ
./docker/run_lab.sh ros2 topic pub -w 1 --once /sensor/temperature std_msgs/msg/Float32 "{data: 72.5}"
./docker/run_lab.sh ros2 topic echo --once /cmd_vel geometry_msgs/msg/Twist --field linear.x   # 0.15
```

---

## 📟 ผลการรันจริง (Real Run Output)
บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29

ไฟล์ฉบับเต็ม: [`results/check_urdf_hospital_amr.txt`](results/check_urdf_hospital_amr.txt), [`results/grading_session.txt`](results/grading_session.txt), [`results/autograder_solution.txt`](results/autograder_solution.txt), [`results/colcon_test.txt`](results/colcon_test.txt)

```console
$ ros2 topic hz /cmd_vel   (5 s)
...
	min: 0.199s max: 0.202s std dev: 0.00076s window: 12
average rate: 5.001
	min: 0.198s max: 0.202s std dev: 0.00107s window: 18
$ ros2 topic echo --once /cmd_vel geometry_msgs/msg/Twist --field linear.x
0.3
---
$ ros2 param set /midterm_robot_controller max_speed 1.0
Set parameter successful
$ ros2 param set /midterm_robot_controller max_speed 2.5
Setting parameter failed: max_speed 2.5 out of safe limit [0.1, 1.5] m/s
$ ros2 param set /midterm_robot_controller max_speed 2.0
Setting parameter failed: max_speed 2.0 out of safe limit [0.1, 1.5] m/s
$ ros2 param set /midterm_robot_controller max_speed 0.2
Set parameter successful
$ ros2 topic echo --once /cmd_vel geometry_msgs/msg/Twist --field linear.x
0.2
---
$ ros2 param set /midterm_robot_controller max_speed 0.6
Set parameter successful
$ ros2 topic pub -w 1 --once /sensor/temperature std_msgs/msg/Float32 "{data: 72.5}"
Waiting for at least 1 matching subscription(s)...
Waiting for at least 1 matching subscription(s)...
publisher: beginning loop
publishing #1: std_msgs.msg.Float32(data=72.5)

$ ros2 topic echo --once /cmd_vel geometry_msgs/msg/Twist --field linear.x
0.15
---
$ ros2 topic pub -w 1 --once /sensor/temperature std_msgs/msg/Float32 "{data: 50.0}"
Waiting for at least 1 matching subscription(s)...
Waiting for at least 1 matching subscription(s)...
publisher: beginning loop
publishing #1: std_msgs.msg.Float32(data=50.0)

$ ros2 topic echo --once /cmd_vel geometry_msgs/msg/Twist --field linear.x
0.3
---
--- node output: ros2 run amr_week08 hospital_robot_node ---
[INFO] [1793242436.244599146] [midterm_robot_controller]: Midterm controller running (max_speed=0.6 m/s)
[INFO] [1793242452.029338489] [midterm_robot_controller]: max_speed updated to 1.0 m/s
[INFO] [1793242461.030573290] [midterm_robot_controller]: max_speed updated to 0.2 m/s
[INFO] [1793242466.969326355] [midterm_robot_controller]: max_speed updated to 0.6 m/s
[WARN] [1793242469.933094960] [midterm_robot_controller]: High temperature 72.5 C > 65.0 C: throttling speed to 0.15 m/s
[INFO] [1793242475.914081376] [midterm_robot_controller]: Temperature back to 50.0 C: normal speed
```

---

## 🏆 ตัวอย่างเฉลยและไฟล์อ้างอิง
นักศึกษาสามารถศึกษาโครงสร้างไฟล์เฉลยเพื่อเป็นแนวทางได้ที่:
- ไฟล์โมเดล URDF: [`solution/hospital_amr.urdf`](solution/hospital_amr.urdf)
- ไฟล์สคริปต์โหนดควบคุม: [`solution/hospital_robot_node.py`](solution/hospital_robot_node.py) (`ros2 run amr_week08 hospital_robot_node`)
- ไฟล์ Launch: [`solution/hospital_bringup.launch.py`](solution/hospital_bringup.launch.py) (`ros2 launch amr_week08 hospital_bringup.launch.py`)
