# 🏆 โครงงานบูรณาการ: ระบบหุ่นยนต์ลำเลียงสินค้าอัตโนมัติ (AMR Warehouse System)
## (Module 6: Capstone Project - Autonomous Mobile Robot for Smart Warehouse)

---

## 📌 บทนำและโจทย์ของโครงงาน (Project Brief)

ผู้เรียนต้องบูรณาการองค์ความรู้ทั้งหมดตั้งแต่โมดูล 1 ถึง 5 เพื่อสร้างระบบ **Autonomous Mobile Robot (AMR)** ที่สามารถปฏิบัติงานในคลังสินค้าจำลอง (Gazebo Sim) ได้อย่างอัตโนมัติ สมบูรณ์ และมีเสถียรภาพสูง

---

## 🎯 ข้อกำหนดเชิงเทคนิค (Technical Requirements)

1. **Kinematic Modeling & Sensors:**
   - หุ่นยนต์ Differential Drive ต้องมีขนาดและค่า Inertia ที่สอดคล้องกับหลักฟิสิกส์จริง
   - ติดตั้ง 360° LiDAR และ Sensor Frame ที่ตรงตามมาตรฐาน REP 103 / REP 105
2. **Simulation & Digital Twin:**
   - รันในโลกจำลอง Gazebo Sim 8 (Harmonic) พร้อมกำแพง ชั้นวางสินค้า และสิ่งกีดขวางแบบเคลื่อนที่ได้ (Dynamic Obstacles)
   - เชื่อมต่อสัญญาณผ่าน `ros_gz_bridge` ครบทุกท็อปปิก (`/cmd_vel`, `/odom`, `/scan`, `/tf`)
3. **SLAM & Localization:**
   - สร้างแผนที่คลังสินค้าความละเอียด $0.05\text{ m/pixel}$ ด้วย SLAM Toolbox
   - ระบุตำแหน่งหุ่นยนต์ด้วย AMCL ได้อย่างแม่นยำแม้เกิด Kidnapped Robot Problem
4. **Autonomous Navigation:**
   - เดินทางตามคำสั่ง Order Dispatcher ผ่านสถานีรับสินค้า (Dock), ชั้นวาง (Rack), จุดตรวจสอบ (QC) และแท่นชาร์จไฟ (Charging Station)
   - มีกลไก Recovery Behaviors เมื่อทางเดินถูกขวางกะทันหัน
5. **Software Engineering & Quality:**
   - เขียนโค้ดตามมาตรฐาน PEP 8 และ ROS 2 Conventions
   - ควบคุมการทำงานของระบบทั้งหมดผ่าน Master Launch File เพียงคำสั่งเดียว

---

## 🚀 การรันระบบทั้งระบบแบบบูรณาการ (One-Click Launch)

```bash
ros2 launch launch/full_warehouse_system.launch.py
```

---

## 📊 เกณฑ์การประเมินผลและการให้คะแนน (Grading Rubrics)

ดูรายละเอียดเกณฑ์การให้คะแนนแบบ 5 มิติได้ที่:  
👉 [**`rubrics.md`**](rubrics.md)
