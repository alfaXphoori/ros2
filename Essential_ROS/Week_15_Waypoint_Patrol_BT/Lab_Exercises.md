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
- เข้าสู่รูทไดเรกทอรี `/mnt/sda/ros`
- ตรวจสอบความถูกต้องของสคริปต์ในสัปดาห์ที่ 15:
  ```bash
  python3 -m py_compile Essential_ROS/Week_15_Waypoint_Patrol_BT/src/waypoint_patrol.py
  ```

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 15.1: การเตรียมระบบจำลองและเปิดระบบ Nav2
**เป้าหมาย:** นำชิ้นส่วนทั้งหมดตั้งแต่สัปดาห์ที่ 11, 7, 14 มาเปิดทำงานร่วมกัน

1. **Terminal 1:** เปิดโลกจำลอง Gazebo พร้อม Bridge
   ```bash
   ./docker/run_lab.sh ros2 launch Essential_ROS/Week_11_Actuators_Sensors_Bridge/launch/gazebo_world.launch.py
   ```
2. **Terminal 2:** เปิดระบบแปลงพิกัด TF ของหุ่นยนต์
   ```bash
   ./docker/run_lab.sh ros2 launch Essential_ROS/Week_07_URDF_Robot_Modeling/launch/display_urdf.launch.py use_gui:=false
   ```
3. **Terminal 3:** เปิดสแตกนำทาง Nav2 Stack
   ```bash
   ./docker/run_lab.sh ros2 launch Essential_ROS/Week_14_Path_Planning_AMCL/launch/nav2_bringup.launch.py
   ```
4. **Terminal 4:** ส่งพิกัดเริ่มต้นให้ AMCL
   ```bash
   ./docker/run_lab.sh python3 Essential_ROS/Week_14_Path_Planning_AMCL/src/amcl_initial_pose.py
   ```
   *ตรวจสอบว่าระบบขึ้นสถานะ Navigation active และมีแผนที่พร้อมนำทาง*

---

### 🔹 Lab 15.2: การรันภารกิจลาดตระเวน 5 สถานี (Waypoint Mission Execution)
**เป้าหมาย:** สังเกตการเคลื่อนที่อัตโนมัติและการหน่วงเวลา ณ แต่ละสถานี

1. ใน **Terminal 4** รันสคริปต์ภารกิจลาดตระเวน:
   ```bash
   ./docker/run_lab.sh python3 Essential_ROS/Week_15_Waypoint_Patrol_BT/src/waypoint_patrol.py
   ```
   **ผลลัพธ์ที่คาดหวัง:**
   ```text
   [INFO] [waypoint_patroller]: 🤖 Nav2 Waypoint Patroller Node Initialized
   [INFO] [waypoint_patroller]: Waiting for /navigate_to_pose action server...
   [INFO] [waypoint_patroller]: 📍 [1/5] Navigating to: Station 1: Receiving Dock
   [INFO] [waypoint_patroller]:    Target: X=2.00, Y=2.00, Yaw=0.00
   [INFO] [waypoint_patroller]: ✅ Arrived at Station 1: Receiving Dock! Dwelling for 3.0s...
   [INFO] [waypoint_patroller]: 📍 [2/5] Navigating to: Station 2: Storage Aisle B
   ...
   [INFO] [waypoint_patroller]: 🎉 All patrol stations visited successfully!
   ```

2. สังเกตว่าในแต่ละสถานี หุ่นยนต์จะหยุดนิ่งตามเวลา `dwell: 3.0s` เพื่อจำลองการโหลดสัมภาระ แล้วจึงเคลื่อนที่ต่อไปยังสถานีถัดไปโดยอัตโนมัติ

---

### 🔹 Lab 15.3: การจำลองการทำงานของ Recovery Behaviors
**เป้าหมาย:** ทดสอบความสามารถในการแก้ไขปัญหาเฉพาะหน้าของ Behavior Tree

1. ในระหว่างที่หุ่นยนต์กำลังเดินทางไปยัง Station 3 ให้นักศึกษาจำลองสิ่งกีดขวางมาขวางช่องทางเดิน
2. สังเกตปฏิกิริยาของระบบใน Terminal 3 (Nav2 Navigator):
   - หุ่นยนต์จะหยุดและขึ้นเตือนว่าเส้นทางเดิมถูกบล็อก
   - Behavior Tree จะเข้าสู่โหนด `RecoveryNode`
   - หุ่นยนต์จะสั่งล้าง Costmap และอาจทำการหมุนตัวสำรวจรอบทิศ (`Spin Action`) เพื่อหาทางเลี่ยงใหม่
3. หากมีทางเลี่ยงอื่น หุ่นยนต์จะคำนวณเส้นทางอ้อมสิ่งกีดขวางและเดินทางไปถึงเป้าหมายได้สำเร็จ

   **คำถาม Checkpoint 15.3:**
   - [ ] หากทางเดินถูกปิดตาย 100% ทุกทิศทาง ผลลัพธ์สุดท้ายของ Action Goal จะเป็นอะไร? (`ABORTED`)
   - [ ] ในโค้ด `waypoint_patrol.py` หากเป้าหมายล้มเหลว โปรแกรมจะหยุดทำงานทันทีหรือข้ามไปสถานีถัดไป?

---

### 🔹 Lab 15.4: การปรับแต่งเพิ่มสถานีจุดตรวจใหม่ (Hands-on Task)
**เป้าหมาย:** เพิ่มสถานีตรวจสอบฉุกเฉิน (Emergency Inspection Bay) เข้าสู่ภารกิจ

ให้นักศึกษาแก้ไขไฟล์ `Essential_ROS/Week_15_Waypoint_Patrol_BT/src/waypoint_patrol.py`:
1. เพิ่มสถานีที่ 6 เข้าไปในรายการ `PATROL_WAYPOINTS`:
   - ชื่อ: `Station 6: Hazmat Inspection`
   - พิกัด: $X = -1.0$, $Y = 1.5$
   - มุมหัน: $\text{Yaw} = 0.785$ rad ($45^\circ$)
   - เวลาหยุดปฏิบัติงาน: `dwell = 4.0` วินาที
2. ทดสอบรันสคริปต์ใหม่ และตรวจสอบว่าหุ่นยนต์เคลื่อนที่เข้าจอดครบทั้ง 6 สถานี

---

## 🏆 โจทย์ท้าทายระดับสูง (Challenge Exercises)
1. **Challenge 15.1:** พัฒนาระบบลาดตระเวนแบบวนลูปต่อเนื่องไม่รู้จบ (**Continuous Infinite Patrol**) จนกว่าจะมีผู้ส่งคำสั่งหยุด หรือจนกว่าแบตเตอรี่จะลดต่ำลง
2. **Challenge 15.2:** ใช้คลาส `BasicNavigator` จาก `nav2_simple_commander.robot_navigator` เขียนสคริปต์เปรียบเทียบระหว่างเมธอด `goToPose()` วนลูป กับการใช้ `followWaypoints()` แบบชุดเดียว

---

## 📦 สิ่งที่ต้องส่ง (Deliverables Checklist)
- [ ] ภาพบันทึกหน้าจอผลการรัน `waypoint_patrol.py` ครบทุกสถานี
- [ ] ภาพบันทึกหน้าจอการแสดงผลเส้นทางเดินหลายสถานีบนโปรแกรม RViz2
- [ ] ภาพบันทึกเหตุการณ์การทำงานของ Recovery Behavior เมื่อพบสิ่งกีดขวางใน Lab 15.3
- [ ] โค้ดส่วนที่เพิ่ม Station 6 ใน Lab 15.4
- [ ] คำตอบ Checkpoint 15.3

---

## 📊 เกณฑ์การประเมินผล (Lab Grading Rubric - 100 คะแนน)
| รายการประเมิน | รายละเอียดการให้คะแนน | คะแนนเต็ม |
| :--- | :--- | :--- :
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
| `waypoint_patrol.py` แจ้ง `Action server not available` | Nav2 Stack ยังไม่เข้าสู่สถานะ Active | ตรวจสอบว่าใน Terminal ของ `nav2_bringup` ขึ้นข้อความ `Navigation active` แล้ว |
| หุ่นยนต์เข้าไม่ถึงสถานีและติด Recovery ซ้ำซาก | พิกัดสถานีอยู่ใกล้กำแพงหรือสิ่งกีดขวางมากเกินไปจนติด Inflation Layer | ขยับพิกัดสถานีให้อยู่ห่างจากขอบกำแพงอย่างน้อย $0.5$ เมตร |
| มุมหันของหุ่นยนต์ตอนจอดไม่ตรงกับที่กำหนด | แปลงมุม Yaw เป็น Quaternion ผิดสูตร | ตรวจสอบว่าใช้ $z = \sin(\theta/2)$ และ $w = \cos(\theta/2)$ |
