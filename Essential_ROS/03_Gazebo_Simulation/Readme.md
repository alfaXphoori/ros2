# 🌍 โมดูล 3: การจำลองสภาพแวดล้อมด้วย Gazebo Sim (Harmonic)
## (Module 3: Physics Simulation & Sensors with Gazebo Sim 8)

---

## 🎯 วัตถุประสงค์การเรียนรู้
1. เข้าใจสถาปัตยกรรมของ Gazebo Sim (Harmonic) และระบบ Entity Component System (ECS)
2. สร้างและปรับแต่งฉากโลกจำลอง 3 มิติ (SDF Worlds) เช่น สภาพแวดล้อมคลังสินค้า ชั้นวางสินค้า และสิ่งกีดขวาง
3. กำหนด Gazebo System Plugins ใน URDF/SDF เพื่อจำลองระบบขับเคลื่อนสองล้อ (`gz-sim-diff-drive-system`) และเซนเซอร์ (`gz-sim-sensors-system`)
4. เชื่อมโยงและแลกเปลี่ยนข้อมูลระหว่าง Gazebo Transport และ ROS 2 DDS ผ่าน `ros_gz_bridge`
5. บังคับหุ่นยนต์จำลองด้วยคีย์บอร์ด (`teleop_twist_keyboard`) และดึงข้อมูลเซนเซอร์ LiDAR / Odometry เข้าสู่ ROS 2

---

## 🏛️ สถาปัตยกรรมของ ros_gz_bridge

```
Gazebo Sim (World + Physics)
  │
  ├──► gz-sim-diff-drive-system ──► Topic: /cmd_vel, /odom, /tf
  └──► gz-sim-sensors-system    ──► Topic: /scan (LiDAR)
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
                 [Gazebo Transport]              [Gazebo Transport]
                         │                               │
                         └───────────────┬───────────────┘
                                         ▼
                                  ros_gz_bridge
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
                  [ROS 2 Topic]                   [ROS 2 Topic]
                    /cmd_vel                        /scan, /odom
                         │                               │
                         ▼                               ▼
                 teleop_keyboard                   SLAM & Nav2
```

---

## 📑 สารบัญเอกสารและปฏิบัติการ
- [ใบงานปฏิบัติการโมดูล 3 (Lab_Exercises.md)](Lab_Exercises.md)
  - **Lab 3.1:** การเปิดโลกจำลอง Gazebo Sim ด้วยคำสั่ง CLI
  - **Lab 3.2:** การเขียนและแก้ไขโลกจำลองคลังสินค้า (`warehouse.sdf`)
  - **Lab 3.3:** การผูก Gazebo Plugins ใน URDF สำหรับมอเตอร์ล้อและ LiDAR
  - **Lab 3.4:** การตั้งค่า `ros_gz_bridge` เพื่อเชื่อมโยงท็อปปิก
  - **Lab 3.5:** การควบคุมหุ่นยนต์ใน Gazebo ด้วยคีย์บอร์ดและดูค่า LiDAR สด
