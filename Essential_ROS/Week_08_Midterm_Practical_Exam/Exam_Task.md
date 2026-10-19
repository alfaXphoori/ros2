# 📝 ใบสั่งงานข้อสอบปฏิบัติการกลางภาค (Midterm Exam Task Specification)
**วิชา:** AMR-101 Essential ROS 2 for Autonomous Mobile Robots  
**เวลาสอบ:** 3 ชั่วโมง (180 นาที)  
**โจทย์สถานการณ์:** การพัฒนาระบบหุ่นยนต์ขนส่งเวชภัณฑ์ในโรงพยาบาล (Hospital Logistics AMR)

---

## 🏥 สถานการณ์จำลอง (Scenario Context)
โรงพยาบาลศูนย์การแพทย์ต้องการนำหุ่นยนต์อัตโนมัติ (AMR) มาใช้งานส่งถุงยาและเวชภัณฑ์ระหว่างห้องยาและหอผู้ป่วย โดยหุ่นยนต์จะต้องมีโครงสร้างตัวถังขนาดใหญ่พอที่จะบรรทุกกล่องยา มีความปลอดภัยสูงโดยต้องจำกัดความเร็วไม่ให้เกินมาตรฐานความปลอดภัยในอาคารที่มีผู้ป่วยเดินสัญจร และมีระบบตรวจสอบความร้อนของมอเตอร์และแบตเตอรี่เพื่อป้องกันอัคคีภัย

---

## 📋 ข้อกำหนดโจทย์เชิงวิศวกรรม (Engineering Specifications)

### 🔹 ตอนที่ 1: การสร้างแบบจำลอง 3 มิติ URDF (`hospital_amr.urdf`) - 35 คะแนน
สร้างไฟล์ URDF โดยมีรายละเอียดทางกลศาสตร์ดังนี้:
1. **ตัวถังหลัก (Chassis Base Link):**
   - รูปทรง: กล่องสี่เหลี่ยม (Box) กว้าง $w = 0.30$ m, ยาว $d = 0.50$ m, สูง $h = 0.15$ m
   - มวลรวม: $m = 8.0$ kg
   - สี: น้ำเงินเข้ม (`chassis_blue`)
   - เมทริกซ์ความเฉื่อย: คำนวณจากสูตร Solid Box:
     $$I_{xx} = \frac{1}{12} m (w^2 + h^2) = 0.075000 \text{ kg}\cdot\text{m}^2$$
     $$I_{yy} = \frac{1}{12} m (d^2 + h^2) = 0.181667 \text{ kg}\cdot\text{m}^2$$
     $$I_{zz} = \frac{1}{12} m (d^2 + w^2) = 0.226667 \text{ kg}\cdot\text{m}^2$$
2. **ล้อขับเคลื่อนซ้าย-ขวา (Drive Wheels):**
   - ชนิดข้อต่อ: `type="continuous"` หมุนรอบแกน Y (`<axis xyz="0 1 0"/>`)
   - ขนาด: เส้นผ่านศูนย์กลาง $0.16$ m (รัศมี $r = 0.08$ m), ความหนา $0.04$ m
   - มวล: ข้างละ $0.80$ kg
   - ระยะห่างระหว่างกึ่งกลางล้อซ้ายและขวา: $L = 0.24$ m ($y = +0.12$ และ $y = -0.12$)
   - ความเฉื่อย: $I_{yy} = 0.002560 \text{ kg}\cdot\text{m}^2$, $I_{xx} = I_{zz} = 0.001387 \text{ kg}\cdot\text{m}^2$
3. **ล้อพยุงอิสระ Caster Wheels (หน้าและหลัง):**
   - ทรงกลมรัศมี $0.03$ m มวล $0.25$ kg อยู่ที่ $x = +0.18$ m และ $x = -0.18$ m สัมผัสระนาบพื้นพอดี
4. **เซนเซอร์ LiDAR:**
   - ติดตั้งบนหลังคาตัวถังที่พิกัด $x = 0.12$ m และความสูงจากจุดศูนย์กลาง $z = 0.18$ m
5. **การทดสอบความถูกต้อง:**
   - รันคำสั่งตรวจสอบ:
     ```bash
     ./docker/run_lab.sh check_urdf hospital_amr.urdf
     ```
     *ต้องแสดงผล Successfully Parsed XML โดยไม่มี Warning ใดๆ*

---

### 🔹 ตอนที่ 2: การพัฒนาโหนดควบคุมและความปลอดภัยใน Python (`hospital_robot_node.py`) - 40 คะแนน
พัฒนาโหนดชื่อ `midterm_robot_controller` ตามโครงสร้าง Class-based OOP:
1. **Dynamic Parameter & Safety Callback (15 คะแนน):**
   - ประกาศพารามิเตอร์ `max_speed` ชนิด `ParameterType.PARAMETER_DOUBLE` กำหนดค่าเริ่มต้น $0.6$ m/s
   - เชื่อมต่อฟังก์ชัน Callback ผ่าน `self.add_on_set_parameters_callback`
   - ตรวจสอบช่วงความปลอดภัย: หากผู้ใช้ตั้งค่าอยู่นอกช่วง $[0.1, 1.5]$ m/s จะต้องตอบ `result.successful = False` พร้อมระบุเหตุผลเตือน
2. **Velocity Command Publisher (10 คะแนน):**
   - สร้าง Publisher ส่งข้อความ `geometry_msgs/msg/Twist` ไปยังท็อปปิก `/cmd_vel`
   - ในลูปควบคุม (Timer 5 Hz) ให้ส่งความเร็ว $v = \min(0.3, \text{max\_speed})$
3. **Sensor Temperature Monitor & Throttling (15 คะแนน):**
   - สร้าง Subscriber ดักฟังท็อปปิก `/sensor/temperature` (`std_msgs/msg/Float32`)
   - หากตรวจพบอุณหภูมิเกิน $65.0^\circ\text{C}$ ให้พิมพ์ Warning Log สีเหลือง และจำกัดความเร็วทันที

---

### 🔹 ตอนที่ 3: ระบบ Launch และการจำลองใน RViz2 (`hospital_bringup.launch.py`) - 25 คะแนน
1. เขียนไฟล์ Launch System เปิดโหนด `robot_state_publisher` โหลดไฟล์ `hospital_amr.urdf`
2. เปิดโหนด `midterm_robot_controller` ควบคู่กัน
3. เปิดหน้าต่าง `rviz2` เพื่อแสดงผลโมเดลและแกนพิกัด TF

---

## 🧪 คำสั่งทดสอบและตรวจให้คะแนนสำหรับกรรมการ (Grading Commands)
```bash
# 1. ตรวจสอบไฟล์ URDF
./docker/run_lab.sh check_urdf solution/solution_urdf.urdf

# 2. รันโหนดควบคุม
./docker/run_lab.sh python3 solution/robot_node.py &

# 3. ตรวจสอบการส่งความเร็ว /cmd_vel
./docker/run_lab.sh ros2 topic echo --once /cmd_vel

# 4. ทดสอบเปลี่ยนพารามิเตอร์เป็นค่าที่ถูกต้อง
./docker/run_lab.sh ros2 param set /midterm_robot_controller max_speed 1.0

# 5. ทดสอบส่งค่าความเร็วเกินขีดจำกัด (ต้องถูกปฏิเสธ)
./docker/run_lab.sh ros2 param set /midterm_robot_controller max_speed 2.5

# 6. ทดสอบจำลองความร้อนสูงเกินพิกัด (ต้องขึ้นเตือน Throttling)
./docker/run_lab.sh ros2 topic pub --once /sensor/temperature std_msgs/msg/Float32 "{data: 72.5}"
```

---

## 🏆 ตัวอย่างเฉลยและไฟล์อ้างอิง
นักศึกษาสามารถศึกษาโครงสร้างไฟล์เฉลยเพื่อเป็นแนวทางได้ที่:
- ไฟล์โมเดล URDF: [`solution/solution_urdf.urdf`](solution/solution_urdf.urdf)
- ไฟล์สคริปต์โหนดควบคุม: [`solution/robot_node.py`](solution/robot_node.py)
