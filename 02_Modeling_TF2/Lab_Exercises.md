# 🛠️ ใบงานปฏิบัติการโมดูล 2: Robot Modeling & TF2 Hands-on Laboratory

---

## 📋 สารบัญการทดลอง
- [Lab 2.1: การตรวจสอบความถูกต้องของ URDF ด้วย check_urdf](#lab-21-การตรวจสอบความถูกต้องของ-urdf-ด้วย-check_urdf)
- [Lab 2.2: การสร้างผังข้อต่อด้วย urdf_to_graphviz](#lab-22-การสร้างผังข้อต่อด้วย-urdf_to_graphviz)
- [Lab 2.3: การจำลองการเคลื่อนที่และแสดงผลใน RViz2](#lab-23-การจำลองการเคลื่อนที่และแสดงผลใน-rviz2)
- [Lab 2.4: การสร้าง Static TF Broadcaster](#lab-24-การสร้าง-static-tf-broadcaster)
- [Lab 2.5: การแปลงพิกัดสิ่งกีดขวางแบบเรียลไทม์ด้วย TF2 Listener](#lab-25-การแปลงพิกัดสิ่งกีดขวางแบบเรียลไทม์ด้วย-tf2-listener)

---

## Lab 2.1: การตรวจสอบความถูกต้องของ URDF ด้วย check_urdf

### 🎯 วัตถุประสงค์
ตรวจสอบโครงสร้างไวยากรณ์ XML และลำดับชั้นความสัมพันธ์ Parent-Child ของโมเดล `diff_drive_robot.urdf`

```bash
check_urdf urdf/diff_drive_robot.urdf
```

**ผลลัพธ์ที่ถูกต้อง:**
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

---

## Lab 2.2: การสร้างผังข้อต่อด้วย urdf_to_graphviz

```bash
urdf_to_graphviz urdf/diff_drive_robot.urdf
```
คำสั่งนี้จะสร้างไฟล์ `diff_drive_robot.pdf` เพื่อให้ตรวจดูความถูกต้องของข้อต่อ Origins และ Axes

---

## Lab 2.3: การจำลองการเคลื่อนที่และแสดงผลใน RViz2

```bash
ros2 launch launch/display_urdf.launch.py
```
- ทดลองเลื่อนสไลเดอร์ `left_wheel_joint` และ `right_wheel_joint` ในหน้าต่าง **Joint State Publisher**
- สังเกตว่าล้อทั้งสองหมุนรอบแกน Y ได้อย่างถูกต้องโดยไม่หลุดออกจากตัวถัง

---

## Lab 2.4: การสร้าง Static TF Broadcaster

### 💻 คำสั่งทดสอบการสตรีมพิกัด
```bash
# ตรวจสอบท็อปปิก /tf_static
ros2 topic echo /tf_static --once
```

---

## Lab 2.5: การแปลงพิกัดสิ่งกีดขวางแบบเรียลไทม์ด้วย TF2 Listener

```bash
# ตรวจสอบค่าพิกัดการแปลงระหว่าง odom และ laser_frame
ros2 run tf2_ros tf2_echo odom laser_frame

# สร้างไฟล์แผนผัง Frame Tree แบบ PDF
ros2 run tf2_tools view_frames
```
ตรวจดูไฟล์ `frames.pdf` ว่าเชื่อมต่อสมบูรณ์จาก `odom` ถึง `camera_optical_link` หรือไม่
