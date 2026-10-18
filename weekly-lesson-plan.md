# 🎓 แผนการจัดการเรียนรู้รายสัปดาห์ (15 สัปดาห์)
## วิชา: การเขียนโปรแกรมหุ่นยนต์และระบบอัตโนมัติด้วย ROS 2 (Robotics & Autonomous Systems with ROS 2)

> **หลักสูตรระดับปริญญาตรี สาขาวิชาวิศวกรรมคอมพิวเตอร์และหุ่นยนต์**  
> **คลังความรู้และโค้ดปฏิบัติการ:** [https://github.com/phoori-gh/ros](https://github.com/phoori-gh/ros)

---

## 📌 ข้อมูลทั่วไปของรายวิชา (Course Overview)
- **รหัสและชื่อวิชา:** CE-432 การเขียนโปรแกรมระบบปฏิบัติการหุ่นยนต์ (Robot Operating System Programming)
- **จำนวนหน่วยกิต:** 3 (2-3-5) — บรรยาย 2 ชั่วโมง, ปฏิบัติการ 3 ชั่วโมง, ศึกษาด้วยตนเอง 5 ชั่วโมงต่อสัปดาห์
- **สถาปัตยกรรมเป้าหมาย:** ROS 2 Jazzy Jalisco บน Ubuntu 22.04 LTS / Webots Simulator 2023b+
- **คลังโค้ดประกอบการเรียน:**
  - โมดูลพื้นฐาน: [`1_ROS2/`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/1_ROS2/README.md) (00 ถึง 07)
  - โมดูลการจำลองและเซนเซอร์: [`2_Webots/`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/Readme.md) (001 ถึง 071 และแพ็กเกจ `ce_webots`)
  - โมดูลการนำทางอัตโนมัติ: [`3_Nav2/`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/3_Nav2/Readme.md) (SLAM, AMCL, Costmaps, Waypoint Patrol)

---

## 🎯 ผลลัพธ์การเรียนรู้ระดับรายวิชา (Course Learning Outcomes: CLOs)
เมื่อสิ้นสุดการเรียนการสอน ผู้เรียนสามารถ:
- **CLO 1:** อธิบายสถาปัตยกรรม ROS 2, Data Distribution Service (DDS), TF2 Coordinate Frames, และหลักการทำงานของเซนเซอร์หุ่นยนต์ชนิดต่างๆ ได้ถูกต้องตามหลักทฤษฎี (Cognitive - Understand)
- **CLO 2:** ออกแบบและพัฒนาโหนด ROS 2 ด้วยภาษา Python โดยประยุกต์ใช้รูปแบบการสื่อสาร Topics, Services, Actions, Parameters, และ Launch Files ได้อย่างมีประสิทธิภาพ (Psychomotor - Applying)
- **CLO 3:** บูรณาการระบบจำลองหุ่นยนต์ Webots Differential Drive ร่วมกับเซนเซอร์ Encoders, IMU, LIDAR, และ Depth Camera เพื่อประมวลผลข้อมูลสิ่งแวดล้อมและควบคุมการเคลื่อนที่ (Psychomotor - Analyzing & Creating)
- **CLO 4:** ติดตั้ง ปรับแต่ง และประเมินผลระบบสร้างแผนที่ 2D SLAM, AMCL Localization, และ Nav2 Stack เพื่อสั่งการหุ่นยนต์ลาดตระเวนอัตโนมัติในสภาพแวดล้อมจำลอง (Psychomotor - Evaluating)
- **CLO 5:** ทำงานร่วมกันเป็นทีมในการแก้ปัญหาโครงงานหุ่นยนต์อัตโนมัติ นำเสนอผลงานเชิงเทคนิค และปฏิบัติตามจรรยาบรรณวิศวกรรม (Affective - Teamwork & Responsibility)

---

## 📊 สัดส่วนการวัดและประเมินผล (Grading Policy)
| รายการประเมิน | สัดส่วน | CLOs ที่วัดผล | รายละเอียด |
|---|---|---|---|
| **1. การเข้าชั้นเรียนและการมีส่วนร่วม** | 10% | CLO 5 | การเข้าเรียนตรงเวลา ความสนใจ และการซักถาม |
| **2. ใบงานปฏิบัติการประจำสัปดาห์ (Weekly Labs)** | 30% | CLO 2, CLO 3 | ตรวจสอบผลการทดลองและการส่งรายงานแล็บ 12 ครั้ง |
| **3. การสอบประเมินผลกลางภาค (Midterm Practical)** | 20% | CLO 1, CLO 2 | การสอบเขียนโค้ดแก้โจทย์ ROS 2 Core และ Kinematics Control |
| **4. โครงงานพัฒนาระบบนำทางหุ่นยนต์ (Term Project)** | 30% | CLO 3, CLO 4, CLO 5 | โครงงานระบบ AMR นำทางในคลังสินค้าด้วย Nav2 และนำเสนอ |
| **5. การสอบประเมินผลปลายภาค (Final Examination)** | 10% | CLO 1, CLO 4 | การสอบทฤษฎีเชิงลึกด้าน SLAM, Sensor Fusion, และ Navigation Stack |
| **รวมทั้งหมด** | **100%** | | |

---

## 📅 ตารางแผนการจัดการเรียนรู้รายสัปดาห์ (15-Week Schedule)

---

### สัปดาห์ที่ 1: แนะนำวิชา สถาปัตยกรรม ROS 2 และการเตรียมสภาพแวดล้อม
- **ผลลัพธ์การเรียนรู้ประจำบท (LLOs):**
  - อธิบายความแตกต่างระหว่าง ROS 1 และ ROS 2 รวมถึงบทบาทของ DDS Middleware ได้
  - สามารถติดตั้งและตั้งค่า ROS 2 Jazzy บนระบบปฏิบัติการ Ubuntu/WSL2 ได้อย่างถูกต้อง
- **หัวข้อบรรยาย (Theory - 2 ชม.):**
  - ประวัติความเป็นมาของ ROS และปัญหาของ ROS 1 (Master node single point of failure)
  - สถาปัตยกรรม ROS 2: DDS (Data Distribution Service), QoS Profiles, RMW Layer
  - โครงสร้าง Workspace, Packages, และคำสั่ง CLI พื้นฐาน (`ros2 node`, `ros2 topic`)
- **ปฏิบัติการ (Lab - 3 ชม.):**
  - ปฏิบัติการติดตั้ง ROS 2 Jazzy และการสร้าง Workspace: [`1_ROS2/00_Install/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/1_ROS2/00_Install/Readme.md)
  - การติดตั้ง Webots Robotics Simulator: [`2_Webots/000_Install_webots/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/000_Install_webots/Readme.md)
  - ทดสอบการรันโหนดมาตรฐาน `turtlesim` และคำสั่ง `teleop_twist_keyboard`
- **การบ้าน/มอบหมายงาน:** ออกแบบผัง Node Graph สรุปสถาปัตยกรรม DDS ใน ROS 2

---

### สัปดาห์ที่ 2: การสื่อสารแบบท็อปปิก (Publishers & Subscribers Pattern)
- **ผลลัพธ์การเรียนรู้ประจำบท (LLOs):**
  - เขียนโหนด Publisher และ Subscriber ด้วยไลบรารี `rclpy` ได้
  - จัดการ Callback Functions และการ Spin โหนดแบบ Single-threaded ได้
- **หัวข้อบรรยาย (Theory - 2 ชม.):**
  - รูปแบบการส่งข้อความแบบ Asynchronous Many-to-Many
  - โครงสร้างข้อความมาตรฐาน `std_msgs`, `geometry_msgs`
  - Lifecycle ของโหนด และการทำงานของ Executor ใน `rclpy`
- **ปฏิบัติการ (Lab - 3 ชม.):**
  - ใบงานปฏิบัติการ [`1_ROS2/01_Publisher_Subscriber/Lab_Exercises.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/1_ROS2/01_Publisher_Subscriber/Lab_Exercises.md)
  - พัฒนาโหนดอ่านค่าเซนเซอร์จำลอง `sensor_monitor.py` และ `counter_logger.py`
  - ตรวจสอบการส่งข้อมูลด้วยคำสั่ง `ros2 topic echo`, `ros2 topic hz`, และ `ros2 topic bw`
- **การบ้าน/มอบหมายงาน:** พัฒนาโหนดประมวลผลค่าเฉลี่ยเซนเซอร์อุณหภูมิแบบเคลื่อนที่ (Moving Average Filter)

---

### สัปดาห์ที่ 3: การสื่อสารแบบคำขอ-ตอบรับ (Services & Clients Pattern)
- **ผลลัพธ์การเรียนรู้ประจำบท (LLOs):**
  - เข้าใจความแตกต่างระหว่าง Topic (Continuous) และ Service (Synchronous Request-Response)
  - พัฒนา Service Server และ Service Client ทั้งแบบ Synchronous และ Asynchronous ได้
- **หัวข้อบรรยาย (Theory - 2 ชม.):**
  - Client-Server Architecture ใน ROS 2
  - การจัดการปัญหา Blocking Call และ Deadlock ในการเรียก Service ข้ามโหนด
  - รูปแบบบริการมาตรฐาน `std_srvs` (`Trigger`, `SetBool`, `Empty`)
- **ปฏิบัติการ (Lab - 3 ชม.):**
  - ปฏิบัติการสร้าง Service Server และ Client: [`1_ROS2/02_Server_Client/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/1_ROS2/02_Server_Client/Readme.md)
  - พัฒนาบริการคำนวณระยะทางและบริการรีเซ็ตตำแหน่งหุ่นยนต์: [`1_ROS2/04_Service/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/1_ROS2/04_Service/Readme.md)
  - การเรียกใช้ Service ผ่าน CLI: `ros2 service call` และการตรวจสอบประเภทด้วย `ros2 service type`
- **การบ้าน/มอบหมายงาน:** พัฒนาบริการ Emergency Stop Service ที่ส่งสัญญาณตัดการทำงานของระบบขับเคลื่อนทันที

---

### สัปดาห์ที่ 4: การนิยามข้อความและบริการแบบกำหนดเอง (Custom Messages & Dynamic Parameters)
- **ผลลัพธ์การเรียนรู้ประจำบท (LLOs):**
  - สร้างและคอมไพล์ไฟล์อินเทอร์เฟซ `.msg` และ `.srv` ด้วย `rosidl` ได้
  - ประกาศ อ่าน และอัปเดต Dynamic Parameters ขณะโหนดกำลังทำงานได้
- **หัวข้อบรรยาย (Theory - 2 ชม.):**
  - โครงสร้าง Interface Packages และการประกาศ Header Fields
  - กลไก Dynamic Reconfigure ผ่าน ROS 2 Parameters และ Parameter Events Callback
- **ปฏิบัติการ (Lab - 3 ชม.):**
  - ปฏิบัติการสร้าง Custom Messages: [`1_ROS2/03_Message/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/1_ROS2/03_Message/Readme.md)
  - ปฏิบัติการจัดการ Dynamic Parameters: [`1_ROS2/05_Parameters/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/1_ROS2/05_Parameters/Readme.md)
  - พัฒนาโหนดตรวจสอบสถานะหุ่นยนต์ `RobotStatus_safety_monitor.py`
- **การบ้าน/มอบหมายงาน:** สร้าง Parameter Server สำหรับปรับค่าขีดจำกัดความเร็วสูงสุดของหุ่นยนต์แบบเรียลไทม์

---

### สัปดาห์ที่ 5: ภารกิจระยะยาวและการรันระบบแบบบูรณาการ (Actions & Launch System)
- **ผลลัพธ์การเรียนรู้ประจำบท (LLOs):**
  - พัฒนา Action Server และ Action Client รองรับ Feedback และ Goal Preemption ได้
  - เขียน Launch File ด้วยภาษา Python สำหรับเปิดหลายโหนดพร้อมกันได้
- **หัวข้อบรรยาย (Theory - 2 ชม.):**
  - โครงสร้าง Action: Goal, Result, และ Periodic Feedback
  - การทำงานของ Action State Machine (`ACCEPTED`, `EXECUTING`, `SUCCEEDED`, `CANCELED`)
  - สถาปัตยกรรม `launch` และ `launch_ros`: Parameter substitution, Namespace, และ Event handlers
- **ปฏิบัติการ (Lab - 3 ชม.):**
  - ปฏิบัติการสร้าง Action Server สำหรับงานเคลื่อนที่เป็นระยะทาง: [`1_ROS2/06_Action/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/1_ROS2/06_Action/Readme.md)
  - ปฏิบัติการออกแบบ Launch Files: [`1_ROS2/07_Launch/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/1_ROS2/07_Launch/Readme.md)
  - รันระบบหุ่นยนต์จำลองผ่าน Launch File เพียงคำสั่งเดียว
- **การบ้าน/มอบหมายงาน:** พัฒนา Launch File ที่รองรับการรับ Argument เพื่อสลับโหมดการทำงานระหว่าง Manual และ Autonomous

---

### สัปดาห์ที่ 6: การจำลองหุ่นยนต์ใน Webots และจลนศาสตร์การเคลื่อนที่ (Differential Drive Kinematics)
- **ผลลัพธ์การเรียนรู้ประจำบท (LLOs):**
  - เข้าใจสมการจลนศาสตร์ Forward & Inverse Kinematics ของ Differential Drive Robot
  - แปลงคำสั่ง Twist ($v, \omega$) เป็นความเร็วรอบของล้อซ้าย-ขวา ($\omega_L, \omega_R$) ได้
- **หัวข้อบรรยาย (Theory - 2 ชม.):**
  - สมการ Unicycle Model และ Differential Drive:
    $$\omega_L = \frac{v - \frac{\omega \cdot L}{2}}{r}, \quad \omega_R = \frac{v + \frac{\omega \cdot L}{2}}{r}$$
  - โครงสร้างโลกจำลอง Webots `.wbt` (Solids, Joints, Motors, Physics)
- **ปฏิบัติการ (Lab - 3 ชม.):**
  - ควบคุมมอเตอร์พื้นฐานใน Webots: [`2_Webots/001_simple_robot_controller/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/001_simple_robot_controller/Readme.md)
  - การเขียนโปรแกรมควบคุมผ่านคีย์บอร์ดแบบ Non-blocking: [`2_Webots/002_keyboard_teleop/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/002_keyboard_teleop/Readme.md)
  - ตรวจสอบพารามิเตอร์จริง: รัศมีล้อ $r = 0.08\text{m}$, ระยะห่างล้อ $L = 0.24\text{m}$
- **การบ้าน/มอบหมายงาน:** เขียนสคริปต์สั่งให้หุ่นยนต์วิ่งเป็นรูปสี่เหลี่ยมจัตุรัสขนาด $2\text{m} \times 2\text{m}$ โดยอาศัยคำสั่งเวลา

---

### สัปดาห์ที่ 7: เซนเซอร์วัดการหมุนของล้อและการคำนวณตำแหน่งสะสม (Encoders & Odometry)
- **ผลลัพธ์การเรียนรู้ประจำบท (LLOs):**
  - คำนวณพิกัดสะสม ($x, y, \theta$) จากค่าพัลส์หรือมุมของ Rotary Wheel Encoders ได้
  - บันทึกและวิเคราะห์ความผิดพลาดสะสม (Odometry Drift & Wheel Slip) ได้
- **หัวข้อบรรยาย (Theory - 2 ชม.):**
  - หลักการทำงานของ Optical Incremental Encoder และ Hall Effect Sensors
  - การประมาณค่าตำแหน่งด้วย Dead Reckoning ผ่าน Runge-Kutta และ Exact Integration
  - โครงสร้างข้อความ `nav_msgs/msg/Odometry` และเมทริกซ์ความแปรปรวนร่วม (Covariance Matrix)
- **ปฏิบัติการ (Lab - 3 ชม.):**
  - ภารกิจเคลื่อนที่ตามระยะทางด้วย Encoders: [`2_Webots/011_wheel_encoder_mission/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/011_wheel_encoder_mission/Readme.md)
  - การควบคุมทิศทางพร้อมมอนิเตอร์ระยะทางจริง: [`2_Webots/012_keyboard_with_distance/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/012_keyboard_with_distance/Readme.md)
  - ทดสอบวิ่งไป-กลับ $5.4$ เมตร และวัดค่าความคลาดเคลื่อนเทียบกับค่า Ground Truth
- **การบ้าน/มอบหมายงาน:** ออกแบบอัลกอริทึม Closed-loop P-Controller สำหรับการหยุดตรงเป้าหมายด้วยระยะทางจาก Encoder

---

### สัปดาห์ที่ 8: การประเมินผลกลางภาค (Midterm Practical Examination)
- **รูปแบบการสอบ:** การสอบปฏิบัติการเขียนโปรแกรมบนเครื่องคอมพิวเตอร์ (3 ชั่วโมง)
- **เนื้อหาที่ประเมิน:**
  - สร้าง ROS 2 Package พร้อมกำหนด Dependencies ใน `package.xml` และ `setup.py`
  - สร้างโหนดรับส่งข้อมูล Topic / Service ตามสถานการณ์จำลองที่กำหนด
  - เขียนโหนดควบคุมหุ่นยนต์ใน Webots เคลื่อนที่ตามภารกิจโดยใช้ข้อมูล Odometry จาก Encoders
  - เผยแพร่ข้อมูลสถานะและ TF Frame ที่ถูกต้องตามมาตรฐาน REP-105

---

### สัปดาห์ที่ 9: เซนเซอร์ตรวจจับระยะประชิดและการหลบหลีกสิ่งกีดขวาง (Touch & Distance Sensors)
- **ผลลัพธ์การเรียนรู้ประจำบท (LLOs):**
  - ประยุกต์ใช้ Touch Sensor (Bumper) และ Distance Sensors (IR / Ultrasonic) ในการหลบหลีกสิ่งกีดขวาง
  - ออกแบบ Finite State Machine (FSM) สำหรับพฤติกรรมการหลบหลีกแบบตอบสนอง (Reactive Avoidance)
- **หัวข้อบรรยาย (Theory - 2 ชม.):**
  - ฟิสิกส์ของเซนเซอร์อินฟราเรด (Time-of-Flight vs. Triangulation) และอัลตราโซนิก
  - ปัญหา Beam Divergence, จุดบอด (Blind Spots), และพื้นผิวสะท้อนแสง
  - สถาปัตยกรรมการควบคุมแบบ Subsumption และ Braitenberg Vehicles
- **ปฏิบัติการ (Lab - 3 ชม.):**
  - การควบคุมการชนด้วย Touch Sensor: [`2_Webots/021_touch_sensor_controller/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/021_touch_sensor_controller/Readme.md)
  - การหลบหลีกสิ่งกีดขวางด้วยเซนเซอร์วัดระยะ 5 จุด: [`2_Webots/022_distance_sensor_controller/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/022_distance_sensor_controller/Readme.md)
  - ทดสอบหุ่นยนต์ในเขาวงกตจำลองพร้อมแบ่งโซนเตือนภัย: Emergency, Critical, Mild
- **การบ้าน/มอบหมายงาน:** พัฒนาอัลกอริทึม Wall Follower (เดินเลาะขอบผนังด้านขวา) โดยใช้ Distance Sensors

---

### สัปดาห์ที่ 10: เซนเซอร์ตรวจวัดความเฉื่อยและการรวมข้อมูลทิศทาง (IMU & Sensor Fusion)
- **ผลลัพธ์การเรียนรู้ประจำบท (LLOs):**
  - แปลงมุมการหมุนระหว่าง Euler Angles (Roll, Pitch, Yaw) และ Quaternions ได้
  - รวมข้อมูลมุมหัน (Heading) จาก Gyroscope/Compass เข้ากับ Encoders เพื่อลดการดริฟต์
- **หัวข้อบรรยาย (Theory - 2 ชม.):**
  - โครงสร้างและหลักการทำงานของ MEMS IMU (Accelerometer, Gyroscope, Magnetometer)
  - ปัญหา Gimbal Lock ในมุมออยเลอร์ และข้อดีของควอเทอร์เนียนในการคำนวณทาง 3 มิติ
  - การชดเชยค่าความเร่งโน้มถ่วงของโลก (Gravity Compensation)
- **ปฏิบัติการ (Lab - 3 ชม.):**
  - การควบคุมทิศทางด้วย IMU / Compass: [`2_Webots/031_imu_controller/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/031_imu_controller/Readme.md)
  - การตรวจจับการสั่นสะเทือนและการชนด้วย Accelerometer: [`2_Webots/032_accelerometer_controller/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/032_accelerometer_controller/Readme.md)
  - เปรียบเทียบความแม่นยำในการหมุน $360^\circ$ ระหว่าง Encoders เพียงอย่างเดียว กับการใช้ IMU ร่วมด้วย
- **การบ้าน/มอบหมายงาน:** เขียนโหนดแปลงข้อมูล `sensor_msgs/Imu` เป็นมุมองศาและพล็อตด้วย `rqt_plot`

---

### สัปดาห์ที่ 11: การมองเห็นของหุ่นยนต์และการประมวลผลภาพ (Computer Vision & Line Following)
- **ผลลัพธ์การเรียนรู้ประจำบท (LLOs):**
  - เชื่อมโยงข้อมูลภาพจาก ROS 2 เข้ากับ OpenCV ผ่านแพ็กเกจ `cv_bridge` ได้
  - พัฒนาอัลกอริทึมตรวจจับวัตถุสีในปริภูมิสี HSV และการวิ่งตามเส้นทางอัตโนมัติได้
- **หัวข้อบรรยาย (Theory - 2 ชม.):**
  - แบบจำลองกล้องพินโฮล (Pinhole Camera Model) และความบิดเบี้ยวของเลนส์ (Distortion)
  - ปริภูมิสี: RGB vs. HSV (ทำไม HSV จึงทนทานต่อการเปลี่ยนแปลงของแสงมากกว่า)
  - การสกัดจุดศูนย์กลางมวล (Centroid) และการควบคุมแบบ Proportional-Derivative (PD)
- **ปฏิบัติการ (Lab - 3 ชม.):**
  - หุ่นยนต์ตรวจจับและติดตามลูกบอลสีเหลือง: [`2_Webots/041_camera_controller/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/041_camera_controller/Readme.md)
  - หุ่นยนต์วิ่งตามเส้นอัตโนมัติ (Line Follower): [`2_Webots/042_line_follower_controller/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/042_line_follower_controller/Readme.md)
  - ปรับค่า Threshold และ Gain $K_p, K_d$ เพื่อให้หุ่นยนต์วิ่งผ่านทางโค้งความเร็วสูงได้โดยไม่หลุดเส้น
- **การบ้าน/มอบหมายงาน:** ปรับปรุงอัลกอริทึมให้ตรวจจับเส้นขวางสีแดงเพื่อสั่งให้หุ่นยนต์หยุดจอดเทียบท่าอัตโนมัติ

---

### สัปดาห์ที่ 12: การตรวจจับระยะทาง 360 องศา และการมองเห็นเชิงลึก 3 มิติ (LIDAR & RGB-D Vision)
- **ผลลัพธ์การเรียนรู้ประจำบท (LLOs):**
  - ประมวลผลข้อมูลระยะทาง 360 องศาจากโครงสร้าง `sensor_msgs/LaserScan` ได้
  - สร้างกลุ่มจุดพิกัด 3 มิติ (3D Point Cloud) จากกล้องวัดระยะลึก (RGB-D Depth Camera) ได้
- **หัวข้อบรรยาย (Theory - 2 ชม.):**
  - ฟิสิกส์ของเซนเซอร์ LiDAR แบบ 2D หมุนวน (Time-of-Flight vs. AMCW)
  - การทำงานของกล้องวัดระยะลึก Structured Light / Active Stereo
  - การแปลงภาพ Depth Map เป็น Point Cloud 3D ด้วยสมการ Backprojection:
    $$X = \frac{(u - c_x) \cdot Z}{f_x}, \quad Y = \frac{(v - c_y) \cdot Z}{f_y}$$
- **ปฏิบัติการ (Lab - 3 ชม.):**
  - ตรวจจับสิ่งกีดขวางรอบทิศทางด้วย LiDAR: [`2_Webots/051_lidar_controller/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/051_lidar_controller/Readme.md)
  - การใช้งานกล้อง RGB-D และการสร้าง Point Cloud 3D: [`2_Webots/061_depth_camera_controller/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/061_depth_camera_controller/Readme.md)
  - การสร้างแผนที่ 3 มิติ (3D Voxel Mapping): [`2_Webots/062_3d_mapping/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/062_3d_mapping/Readme.md)
- **การบ้าน/มอบหมายงาน:** เขียนโหนดกรองจุดรบกวน (Statistical Outlier Filter) จากข้อมูล Point Cloud ใน RViz2

---

### สัปดาห์ที่ 13: การสร้างแผนที่พร้อมระบุตำแหน่ง (2D SLAM Mapping & Map Server)
- **ผลลัพธ์การเรียนรู้ประจำบท (LLOs):**
  - เข้าใจทฤษฎี Graph-Based SLAM, Scan Matching, และ Loop Closure Optimization
  - ใช้ `slam_toolbox` ในการขับสำรวจและบันทึกแผนที่ Occupancy Grid ได้อย่างถูกต้อง
- **หัวข้อบรรยาย (Theory - 2 ชม.):**
  - ปัญหาไก่กับไข่ของ SLAM (สร้างแผนที่ต้องรู้ตำแหน่ง / ระบุตำแหน่งต้องมีแผนที่)
  - การคำนวณ Pose Graph และการปรับลดความคลาดเคลื่อนด้วย Ceres Solver
  - มาตรฐานไฟล์แผนที่ ROS 2 (`.pgm`, `.yaml`) และโหนด Map Server
- **ปฏิบัติการ (Lab - 3 ชม.):**
  - การทำ SLAM ด้วย Odometry ใน Webots: [`2_Webots/052_slam_controller/Readme.md`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/052_slam_controller/Readme.md)
  - ปฏิบัติการสร้างแผนที่ด้วย SLAM Toolbox: [`3_Nav2/Lab_Exercises.md` (Lab 3.1 & 3.2)](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/3_Nav2/Lab_Exercises.md)
  - บันทึกแผนที่ด้วยโหนด [`ce_webots/save_map.py`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/2_Webots/ce_webots/ce_webots/save_map.py)
- **การบ้าน/มอบหมายงาน:** เปรียบเทียบความคมชัดของแผนที่ที่ได้จากการขับสำรวจด้วยความเร็วต่ำกับความเร็วสูง

---

### สัปดาห์ที่ 14: ระบบนำทางอัตโนมัติและการระบุตำแหน่ง (Nav2 Stack, AMCL & Costmaps)
- **ผลลัพธ์การเรียนรู้ประจำบท (LLOs):**
  - ปรับแต่งและใช้งาน AMCL Localization สำหรับการระบุตำแหน่งหุ่นยนต์ในแผนที่ได้
  - วิเคราะห์และจูนค่าพารามิเตอร์ของ Costmap 2D, Global Planner, และ DWB Local Controller ได้
- **หัวข้อบรรยาย (Theory - 2 ชม.):**
  - ทฤษฎี Particle Filter และ Likelihood Field Model ใน AMCL
  - เลเยอร์ของ Costmap: Static, Obstacle (Voxel), และ Inflation Layer
  - การวางแผนเส้นทางระดับโลก (Global Dijkstra/A*) เทียบกับการคำนวณ Trajectory ระดับท้องถิ่น (DWB)
- **ปฏิบัติการ (Lab - 3 ชม.):**
  - รันระบบนำทางเต็มรูปแบบ: [`3_Nav2/launch/nav2_bringup.launch.py`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/3_Nav2/launch/nav2_bringup.launch.py)
  - ปฏิบัติการนำทางและปรับจูน Costmap: [`3_Nav2/Lab_Exercises.md` (Lab 3.3)](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/3_Nav2/Lab_Exercises.md)
  - การกำหนดพิกัด Initial Pose อัตโนมัติด้วย [`3_Nav2/src/amcl_initial_pose.py`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/3_Nav2/src/amcl_initial_pose.py)
- **การบ้าน/มอบหมายงาน:** บันทึกวิดีโอการสั่งหุ่นยนต์หลบสิ่งกีดขวางแบบพลวัตที่เดินตัดหน้าใน Webots

---

### สัปดาห์ที่ 15: ภารกิจหุ่นยนต์เคลื่อนที่อัตโนมัติระดับสูง (Autonomous Waypoint Patrol & Project Showcase)
- **ผลลัพธ์การเรียนรู้ประจำบท (LLOs):**
  - เขียนโปรแกรมควบคุมหุ่นยนต์ลาดตระเวนหลายจุดด้วย `nav2_simple_commander` หรือ Action Client ได้
  - นำเสนอโครงงานประยุกต์ใช้ ROS 2 ในงานอุตสาหกรรมหรือโลจิสติกส์ได้
- **หัวข้อบรรยาย (Theory - 2 ชม.):**
  - สถาปัตยกรรม Behavior Trees (BT) ในการควบคุมพฤติกรรมอัตโนมัติและการกู้คืนข้อผิดพลาด (Recovery Behaviors)
  - การประยุกต์ใช้ Autonomous Mobile Robots (AMRs) ในโรงงานอุตสาหกรรม 4.0 และคลังสินค้าอัจฉริยะ
- **ปฏิบัติการ (Lab - 3 ชม.):**
  - ปฏิบัติการลาดตระเวน Multi-Waypoint Patrol: [`3_Nav2/Lab_Exercises.md` (Lab 3.4)](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/3_Nav2/Lab_Exercises.md)
  - รันสคริปต์ภารกิจคลังสินค้า: [`3_Nav2/src/waypoint_patrol.py`](file:///Volumes/ExDisk/Google%20Drive%20Ksu/KSU/Git/ROS/3_Nav2/src/waypoint_patrol.py)
  - การนำเสนอโครงงานประจำภาคการศึกษา (Term Project Demonstration & Presentation)
- **การประเมินผล:** ประเมินคะแนนโครงงานตามเกณฑ์ Rubrics และส่งมอบรายงานฉบับสมบูรณ์

---

## 📚 เอกสารอ้างอิงและแหล่งข้อมูลเพิ่มเติม (References)
1. Macenski, S., et al. (2020). *From the desks of ROS 2: A view on Robot Operating System*. Science Robotics, 5(49).
2. Cyberbotics Ltd. (2023). *Webots User Guide & Reference Manual*. Cyberbotics.
3. ROS 2 Jazzy Documentation: [https://docs.ros.org/en/jazzy/](https://docs.ros.org/en/jazzy/)
4. Navigation 2 (Nav2) Documentation: [https://navigation.ros.org/](https://navigation.ros.org/)
5. GitHub Repository: [https://github.com/phoori-gh/ros](https://github.com/phoori-gh/ros)
