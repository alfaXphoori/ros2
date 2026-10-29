# 📊 เกณฑ์การประเมินผลโครงงานบูรณาการ (Capstone Project Rubrics)

**เอกสารที่เกี่ยวข้อง:** [คู่มือโครงงาน](Readme.md) | [ใบงานโครงงาน](Lab_Exercises.md) | ค่าเป้าหมาย KPI และน้ำหนักคะแนนทั้งหมดอยู่ในไฟล์เดียว [`config/kpi_targets.yaml`](config/kpi_targets.yaml) (ชุดทดสอบ `test/test_capstone_config.py` ตรวจว่าเอกสารนี้ตรงกับไฟล์ config เสมอ)

---

## 🧮 สัดส่วนในเกรดรายวิชา (AMR-201)

| ส่วนการประเมิน | สัดส่วนในเกรดรายวิชา | ประเมินจาก |
|---|:---:|---|
| **Industrial Capstone AMR Project** | 35% | คะแนน 100 คะแนนตาม 5 มิติด้านล่าง (ซอฟต์แวร์ + รายงาน + ผลรัน `capstone_mission`) |
| **Final Oral Defense & Demonstration** | 10% | สาธิตสด + Fault Injection + ตอบคำถามเชิงวิศวกรรม (ดูหัวข้อสุดท้าย) |

---

## 📐 สัดส่วนการให้คะแนน 5 มิติของโครงงาน (Total: 100 คะแนน)

| มิติการประเมิน (Dimension) | น้ำหนัก | หลักฐานที่ใช้ตัดสิน (Evidence) |
|---|:---:|---|
| **1. System Architecture & Engineering Standards** | **20%** | Launch แบบ one-command (`full_warehouse_system.launch.py headless:=true`), TF tree ถูกต้องตาม REP 103/105, `use_sim_time` ครบทุกโหนด, การ reuse แพ็กเกจด้วย `get_package_share_directory` แทนการอ้าง path ตรง |
| **2. Hardware Abstraction & Lifecycle Safety** | **20%** | Stage 0 ต้องรายงาน lifecycle nodes ACTIVE ครบ, ห่วงโซ่ความเร็วผ่าน `collision_monitor`, KPI E-stop (latency + ระยะเหลือหน้ากันชน), อธิบายทางเลือก Gazebo DiffDrive vs `ros2_control` (โมดูล 01) ได้ |
| **3. Autonomous Navigation Performance** | **25%** | KPI Mission stage success, ความคลาดเคลื่อนตำแหน่งปลายทางจริง และ AMCL error เทียบ Ground Truth, ภาพเส้นทางจริงจาก `plot_capstone` |
| **4. Precision Docking & Visual Marker Detection** | **20%** | `DockRobot` สำเร็จ (error_code 0) โดยใช้ AprilTag ในลูป, KPI ความคลาดเคลื่อนการเข้าแท่นจริง (มม.) และมุม, `UndockRobot` สำเร็จ |
| **5. Software Quality, SROS 2 Security & Automated Tests** | **15%** | `colcon test` ผ่านทั้ง unit test และ `launch_testing`, โค้ดผ่าน flake8, สาธิต SROS 2 enforce (โมดูล 05), เอกสารมีผลรันจริงพร้อมแหล่งที่มา |

---

## 🎯 ค่าเป้าหมาย KPI ที่ใช้ให้คะแนน

ใช้ตาราง KPI ใน [Readme.md](Readme.md) (หัวข้อ "ดัชนีชี้วัดประสิทธิภาพของระบบ") — **เป้าหมายขั้นต่ำ** คือเกณฑ์ที่ `capstone_mission` ใช้ตัดสิน PASS/FAIL (exit code 1 ถ้าไม่ผ่านแม้ข้อเดียว) ส่วน **ระดับดีเยี่ยม** ใช้แยกระดับ Distinction ทุกค่าวัดเทียบ Ground Truth ของ Gazebo ไม่ใช่ค่าที่หุ่นยนต์ประมาณเอง

---

## 🏆 ระดับคะแนนและการประเมิน (Performance Levels)

- **ดีเยี่ยม (Distinction: 85 - 100%):**
  `capstone_mission` จบด้วย `7/7 stages PASS, 7/7 KPIs met` และ KPI อย่างน้อย 4 ข้อถึงระดับดีเยี่ยม, รันซ้ำ 5 ครั้งผ่านทุกครั้ง, `colcon test` ผ่านทั้งหมด, อธิบายที่มาของตัวเลขทุกตัวได้ (เช่น ทำไม docking error ขึ้นกับ `docking_threshold`, ทำไม E-stop latency ถูกจำกัดด้วยความถี่ของ cmd_vel 20 Hz)
- **ดี (Proficient: 70 - 84%):**
  ผ่านทุก Stage และทุก KPI ระดับขั้นต่ำในการรันที่ส่ง แต่ยังไม่เสถียรเมื่อรันซ้ำ (เช่น ผ่าน 3-4 ใน 5 ครั้ง) หรือเอกสาร/ภาพผลรันไม่ครบ
- **พอใช้ (Developing: 50 - 69%):**
  ระบบขึ้นครบและนำทางถึงสถานีได้ แต่ Dock/Undock หรือ E-stop test ไม่ผ่าน หรือ KPI บางข้อไม่ถึงเกณฑ์ขั้นต่ำ
- **ต้องปรับปรุง (Unsatisfactory: < 50%):**
  Stage 0 ไม่ผ่าน (Nav2/docking server ไม่ ACTIVE, ไม่มี Ground Truth) หรือรันได้เฉพาะเมื่อแก้ไขด้วยมือระหว่างทาง

---

## 🎤 การสอบปากเปล่า (Final Oral Defense, 10% ของรายวิชา)

กรรมการเลือกสถานการณ์ Fault Injection อย่างน้อย 2 ข้อ แล้วให้ผู้เรียนสาธิตและอธิบาย:

| สถานการณ์ | สิ่งที่ต้องแสดง | เกณฑ์ผ่าน |
|---|---|---|
| **Kidnapped Robot** | ย้ายหุ่นยนต์ใน Gazebo แล้วแสดงว่า AMCL (ค่า `recovery_alpha_*` = 0) **ไม่** ฟื้นตัวเอง จากนั้นใช้วิธีที่ถูกต้อง: `/reinitialize_global_localization` + หมุนรอบตัว หรือส่ง `/initialpose` ใหม่ | อธิบายได้ว่าทำไม Global Localization ในโลกที่สมมาตรอาจลู่เข้าผิดตำแหน่ง (perceptual aliasing) และทำให้ AMCL error กลับมา ≤ 0.10 m |
| **Dynamic Obstacle** | วางกล่องขวางทางระหว่างนำทาง | หุ่นยนต์ไม่ชน วางแผนอ้อมหรือหยุดรอ และอธิบาย costmap obstacle layer ได้ |
| **Emergency Stop** | กล่องโผล่ใน StopZone ขณะเคลื่อนที่ (Stage 5 ของ `capstone_mission`) | หยุดก่อนชน (ระยะเหลือ ≥ 2 cm) และอธิบายห่วงโซ่ `cmd_vel_nav → velocity_smoother → collision_monitor → cmd_vel` ได้ |
