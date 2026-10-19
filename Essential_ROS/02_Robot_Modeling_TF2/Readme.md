# 🤖 โมดูล 2: การสร้างโมเดลหุ่นยนต์ 3 มิติ และระบบแปลงพิกัด TF2
## (Module 2: 3D Robot Modeling with URDF/Xacro & TF2 Coordinate Frames)

---

## 🎯 วัตถุประสงค์การเรียนรู้
1. ออกแบบ Kinematic Tree ตามมาตรฐาน REP 103 (Coordinate Standards) และ REP 105 (Mobile Robot Frames)
2. กำหนด Visual, Collision, และคำนวณ Mass & Inertia Matrix สำหรับ Rigid Links
3. กำหนดความสัมพันธ์ Joint แบบ `fixed` และ `continuous` (Differential Drive Wheels & Casters)
4. จัดการระบบการแปลงพิกัด TF2 ด้วย Static/Dynamic Broadcasters และ TF Listeners
5. แสดงผลโมเดลและสถานะข้อต่อหุ่นยนต์แบบเรียลไทม์บน RViz2

---

## 📐 ลำดับชั้นระบบพิกัด (REP 105 Coordinate Frame Tree)

```
        map (World Map - Global Frame จาก SLAM/AMCL)
         │
         ▼
        odom (Odometry Frame - สะสม Drift จากล้อและ IMU)
         │
         ▼
    base_footprint (จุดฉายของหุ่นยนต์บนพื้น Z = 0)
         │
         ▼
     base_link (จุดกึ่งกลางเพลาล้อขับเคลื่อน Z = 0.08m)
   ┌─────┴───────────────┬─────────────────┐
   ▼                     ▼                 ▼
left_wheel_link   right_wheel_link    lidar_link
                                           │
                                           ▼
                                      camera_link
                                           │
                                           ▼
                                  camera_optical_link
```

---

## 📑 สารบัญเอกสารและปฏิบัติการ
- [ใบงานปฏิบัติการโมดูล 2 (Lab_Exercises.md)](Lab_Exercises.md)
  - **Lab 2.1:** การสร้างไฟล์ URDF และทดสอบ Syntax ด้วย `check_urdf`
  - **Lab 2.2:** การแปลงไฟล์ URDF เป็นแผนภาพ Kinematic Tree ด้วย `urdf_to_graphviz`
  - **Lab 2.3:** การเปิด RViz2 และควบคุมล้อด้วย `joint_state_publisher_gui`
  - **Lab 2.4:** การสร้าง Static Sensor TF Broadcaster เผยแพร่ตำแหน่ง LiDAR และกล้อง
  - **Lab 2.5:** การคำนวณ Odometry และแปลงพิกัดสิ่งกีดขวางด้วย TF2 Listener
