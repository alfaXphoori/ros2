# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 7: การสร้างแบบจำลอง 3 มิติ (URDF) และ Inertia Matrix
**วิชา:** AMR-101 Essential ROS 2 for Autonomous Mobile Robots  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** พื้นฐาน (Beginner)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายสัปดาห์ที่ 7](Readme.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. ตรวจสอบความถูกต้องของโมเดล URDF ด้วยเครื่องมือ `check_urdf` และวิเคราะห์โครงสร้างต้นไม้ข้อต่อ
2. แสดงผลโมเดลหุ่นยนต์ 3 มิติบนโปรแกรม **RViz2** พร้อมทดสอบการหมุนข้อต่อผ่าน GUI Slider
3. คำนวณเมทริกซ์ความเฉื่อย (**Inertia Tensor**) และจุดศูนย์ถ่วง (Center of Mass) สำหรับชิ้นส่วนใหม่
4. แก้ไขไฟล์ URDF เพื่อติดตั้งอุปกรณ์เพิ่มเติม (Payload Tray หรือ เสาอากาศ Antenna) ตามข้อกำหนดทางกล

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่รูทไดเรกทอรี `/mnt/sda/ros`
- สำหรับการเปิดหน้าต่าง GUI (RViz2) ให้เปิดสิทธิ์การแสดงผล X11 บนโฮสต์ก่อน:
  ```bash
  xhost +local:docker
  ```
- ทดสอบการคอมไพล์ Launch File:
  ```bash
  python3 -m py_compile Essential_ROS/Week_07_URDF_Robot_Modeling/launch/display_urdf.launch.py
  ```

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 7.1: การตรวจสอบไวยากรณ์ด้วย `check_urdf`
**เป้าหมาย:** ใช้คำสั่งมาตรฐานเพื่อยืนยันว่าโครงสร้าง XML ของโมเดลไม่มีข้อผิดพลาด

1. รันคำสั่งตรวจสอบไฟล์ URDF ของหุ่นยนต์:
   ```bash
   ./docker/run_lab.sh check_urdf Essential_ROS/Week_07_URDF_Robot_Modeling/urdf/diff_drive_robot.urdf
   ```
   **ผลลัพธ์ที่คาดหวัง:**
   ```text
   robot name is: diff_drive_robot
   ---------- Successfully Parsed XML ---------------
   root Link: base_footprint has 1 child(ren)
       child(1):  base_link
           child(1):  camera_link
               child(1):  camera_optical_link
           child(2):  front_caster_link
           child(3):  left_wheel_link
           child(4):  lidar_link
           child(5):  rear_caster_link
           child(6):  right_wheel_link
   ```

   **คำถาม Checkpoint 7.1:**
   - [ ] ลิงก์ใดทำหน้าที่เป็น Root Link ของหุ่นยนต์ตัวนี้?
   - [ ] `camera_optical_link` เป็นลูก (Child) ของลิงก์ใด?

---

### 🔹 Lab 7.2: การแสดงผลโมเดลใน RViz2 และควบคุม Joint State
**เป้าหมาย:** ตรวจสอบมิติ รูปร่าง และการหมุนของล้อหุ่นยนต์ในสภาพแวดล้อม 3 มิติ

1. เปิด Launch File สำหรับการแสดงผล URDF:
   ```bash
   ./docker/run_lab.sh ros2 launch Essential_ROS/Week_07_URDF_Robot_Modeling/launch/display_urdf.launch.py
   ```
2. สังเกตหน้าต่าง RViz2 ที่เปิดขึ้นมา:
   - ตรวจสอบว่าโมเดลตัวถังมีสีน้ำเงิน ล้อสีดำ เซนเซอร์ LiDAR สีส้ม และกล้องสีแดง
   - ตรวจสอบว่าไม่มีเครื่องหมายตกใจสีแดง (Error) ในแถบ RobotModel
3. ทดลองเลื่อนสไลเดอร์ในหน้าต่าง `Joint State Publisher GUI`:
   - ปรับค่าสไลเดอร์ `left_wheel_joint` และ `right_wheel_joint`
   - สังเกตการหมุนของล้อในหน้าจอ RViz2

---

### 🔹 Lab 7.3: การคำนวณ Inertia Matrix ของถาดบรรทุกสัมภาระ (Payload Tray)
**เป้าหมาย:** ประยุกต์ใช้สูตรฟิสิกส์คำนวณความเฉื่อยเพื่อเตรียมติดตั้งชิ้นส่วนใหม่

กำหนดให้ต้องการติดตั้ง **ถาดบรรทุกสัมภาระ (Payload Tray)** บนหลังคาหุ่นยนต์:
- รูปทรง: กล่องสี่เหลี่ยม (Solid Box)
- ขนาด: ยาว $d = 0.25$ m, กว้าง $w = 0.18$ m, สูง $h = 0.05$ m
- มวลรวม: $m = 1.2$ kg

**โจทย์คำนวณ:**
1. คำนวณ $I_{xx} = \frac{1}{12} m (w^2 + h^2)$
2. คำนวณ $I_{yy} = \frac{1}{12} m (d^2 + h^2)$
3. คำนวณ $I_{zz} = \frac{1}{12} m (d^2 + w^2)$
*(บันทึกตัวเลขทศนิยม 6 ตำแหน่งลงในรายงาน)*

---

### 🔹 Lab 7.4: การแก้ไขไฟล์ URDF เพื่อเพิ่มชิ้นส่วน Payload Tray (Hands-on Task)
**เป้าหมาย:** เพิ่มลิงก์และข้อต่อใหม่ลงใน `diff_drive_robot.urdf`

1. เปิดไฟล์ `Essential_ROS/Week_07_URDF_Robot_Modeling/urdf/diff_drive_robot.urdf`
2. เพิ่มแท็ก `<link name="payload_tray_link">` โดยใส่ค่า `<visual>`, `<collision>` และ `<inertial>` ตามตัวเลขที่คำนวณได้ใน Lab 7.3
3. เพิ่มแท็ก `<joint name="payload_tray_joint" type="fixed">`:
   - Parent: `base_link`
   - Child: `payload_tray_link`
   - Origin: ติดตั้งบนหลังคาตัวถังที่พิกัด $(x = 0.0, y = 0.0, z = 0.08)$
4. ตรวจสอบความถูกต้องด้วย `check_urdf` และเปิดดูใน RViz2:
   ```bash
   ./docker/run_lab.sh check_urdf Essential_ROS/Week_07_URDF_Robot_Modeling/urdf/diff_drive_robot.urdf
   ```

---

## 🏆 โจทย์ท้าทายระดับสูง (Challenge Exercises)
1. **Challenge 7.1:** เพิ่มเสาไฟสัญญาณแจ้งเตือน (Status Beacon / Tower Light) สีเขียวทรงกระบอกขึ้นมาบนหลังคาหุ่นยนต์ พร้อมคำนวณ Inertia แบบทรงกระบอก
2. **Challenge 7.2:** แปลงโครงสร้าง URDF ออกมาเป็นแผนผังไฟล์ PDF โดยใช้คำสั่ง `urdf_to_graphiz` แล้วตรวจสอบโครงสร้างความสัมพันธ์

---

## 📦 สิ่งที่ต้องส่ง (Deliverables Checklist)
- [ ] ผลลัพธ์ข้อความจากคำสั่ง `check_urdf` ของโมเดลเริ่มต้น
- [ ] ภาพบันทึกหน้าจอโมเดล 3D ใน RViz2 พร้อมหน้าต่าง Joint State Publisher GUI
- [ ] แสดงวิธีทำและผลการคำนวณ $I_{xx}, I_{yy}, I_{zz}$ ของ Payload Tray ใน Lab 7.3
- [ ] โค้ด XML ของ `<link name="payload_tray_link">` และ `<joint name="payload_tray_joint">` ที่เขียนเพิ่ม
- [ ] ภาพบันทึกหน้าจอ RViz2 ที่แสดงถาดสัมภาระติดตั้งสำเร็จบนตัวหุ่นยนต์

---

## 📊 เกณฑ์การประเมินผล (Lab Grading Rubric - 100 คะแนน)
| รายการประเมิน | รายละเอียดการให้คะแนน | คะแนนเต็ม |
| :--- | :--- | :---: |
| **การตรวจสอบโมเดลด้วย `check_urdf`** | รันคำสั่งผ่านและอธิบายลำดับ Parent-Child ได้ถูกต้อง | 20 |
| **การแสดงผล 3D ใน RViz2** | ตั้งค่า Fixed Frame และควบคุม Joint GUI ได้อย่างสมบูรณ์ | 20 |
| **ความถูกต้องของการคำนวณ Inertia** | แสดงวิธีทำและคำนวณค่า $I_{xx}, I_{yy}, I_{zz}$ ถูกต้องตามหลักฟิสิกส์ | 25 |
| **การแก้ไข URDF เพิ่ม Payload Tray** | เขียนแท็ก XML ถูกต้อง ขนาด ตำแหน่ง และการแสดงผลตรงตามสเปก | 25 |
| **ความเรียบร้อยของรายงานและโจทย์ท้าทาย** | รายงานสมบูรณ์ ภาพประกอบและบทสรุปชัดเจน | 10 |
| **รวม** | | **100** |

---

## ⚠️ การแก้ปัญหาที่พบบ่อยในแล็บ (Troubleshooting)
| ปัญหา | สาเหตุ | การแก้ไข |
| :--- | :--- | :--- |
| `rviz2: cannot connect to X server` | ไม่ได้เปิดสิทธิ์ X11 บนโฮสต์ | รัน `xhost +local:docker` บนเครื่อง Host |
| `check_urdf` แจ้ง Error `Joint [xxx] has parent [yyy] which is not a link` | พิมพ์ชื่อ Parent Link ไม่ตรงกับ Link ที่ประกาศไว้ก่อนหน้า | ตรวจสอบตัวสะกดตัวพิมพ์เล็ก-ใหญ่ (Case-sensitive) |
| Inertia Tensor เป็นค่าลบหรือศูนย์ทั้งหมด | ใส่ค่า 0 ในระนาบความเฉื่อยหลัก | $I_{xx}, I_{yy}, I_{zz}$ ของวัตถุที่มีมวลต้องมีค่าเป็นบวกเสมอ |
