# 📚 คู่มือการสอนฉบับสมบูรณ์: Lecture & Lab Guide (16 สัปดาห์)
## วิชา: AMR-201 Advanced ROS 2 & Industrial Fleet Robotics

คู่มือนี้ประกอบด้วยเนื้อหาการบรรยายเชิงวิศวกรรมขั้นสูง (Advanced Lecture Notes) และขั้นตอนการปฏิบัติการแล็บระดับอุตสาหกรรม (Industrial Lab Guides) ครบทั้ง 16 สัปดาห์ สำหรับผู้สอนและผู้เรียน

---

## สารบัญสัปดาห์
- [สัปดาห์ที่ 1: สถาปัตยกรรมเฟรมเวิร์ก ros2_control และ Resource Management](#สัปดาห์ที่-1-สถาปัตยกรรมเฟรมเวิร์ก-ros2_control-และ-resource-management)
- [สัปดาห์ที่ 2: การพัฒนา Custom C++ Hardware Interface](#สัปดาห์ที่-2-การพัฒนา-custom-c-hardware-interface)
- [สัปดาห์ที่ 3: การเชื่อมต่อไมโครคอนโทรลเลอร์ด้วย micro-ROS และลูปปิด PID](#สัปดาห์ที่-3-การเชื่อมต่อไมโครคอนโทรลเลอร์ด้วย-micro-ros-และลูปปิด-pid)
- [สัปดาห์ที่ 4: ระบบประมวลผลภาพใน ROS 2 และการคาลิเบรตกล้อง](#สัปดาห์ที่-4-ระบบประมวลผลภาพใน-ros-2-และการคาลิเบรตกล้อง)
- [สัปดาห์ที่ 5: การประมวลผลภาพด้วยปัญญาประดิษฐ์ (Deep Learning YOLO)](#สัปดาห์ที่-5-การประมวลผลภาพด้วยปัญญาประดิษฐ์-deep-learning-yolo)
- [สัปดาห์ที่ 6: การตรวจจับ Visual Marker และการประมาณพิกัด 3 มิติ](#สัปดาห์ที่-6-การตรวจจับ-visual-marker-และการประมาณพิกัด-3-มิติ)
- [สัปดาห์ที่ 7: การประมวลผลข้อมูล 3D Point Cloud ด้วย PCL](#สัปดาห์ที่-7-การประมวลผลข้อมูล-3d-point-cloud-ด้วย-pcl)
- [สัปดาห์ที่ 8: สอบประเมินสถาปัตยกรรมกลางภาค (Midterm Industrial Review)](#สัปดาห์ที่-8-สอบประเมินสถาปัตยกรรมกลางภาค-midterm-industrial-review)
- [สัปดาห์ที่ 9: Nav2 Precision Docking Server สำหรับการเข้าชาร์จอัตโนมัติ](#สัปดาห์ที่-9-nav2-precision-docking-server-สำหรับการเข้าชาร์จอัตโนมัติ)
- [สัปดาห์ที่ 10: การออกแบบ Nav2 Behavior Trees ขั้นสูง](#สัปดาห์ที่-10-การออกแบบ-nav2-behavior-trees-ขั้นสูง)
- [สัปดาห์ที่ 11: การควบคุมพื้นที่ด้วย Nav2 Costmap Filters & Speed Zones](#สัปดาห์ที่-11-การควบคุมพื้นที่ด้วย-nav2-costmap-filters--speed-zones)
- [สัปดาห์ที่ 12: สถาปัตยกรรมระบบฝูงหุ่นยนต์ (Multi-Robot Fleet Architecture)](#สัปดาห์ที่-12-สถาปัตยกรรมระบบฝูงหุ่นยนต์-multi-robot-fleet-architecture)
- [สัปดาห์ที่ 13: ระบบจัดการจราจรและงานส่วนกลางด้วย Open-RMF](#สัปดาห์ที่-13-ระบบจัดการจราจรและงานส่วนกลางด้วย-open-rmf)
- [สัปดาห์ที่ 14: วิศวกรรมระบบระดับ Production ด้วย Managed Lifecycle Nodes](#สัปดาห์ที่-14-วิศวกรรมระบบระดับ-production-ด้วย-managed-lifecycle-nodes)
- [สัปดาห์ที่ 15: ความมั่นคงปลอดภัยไซเบอร์ (SROS 2) และ CI/CD ด้วย launch_testing](#สัปดาห์ที่-15-ความมั่นคงปลอดภัยไซเบอร์-sros-2-และ-cicd-ด้วย-launch_testing)
- [สัปดาห์ที่ 16: Capstone Final Showcase & Industrial Defense](#สัปดาห์ที่-16-capstone-final-showcase--industrial-defense)

---

### สัปดาห์ที่ 1: สถาปัตยกรรมเฟรมเวิร์ก ros2_control และ Resource Management

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **ทำไมต้องใช้ `ros2_control`:**
   - การเขียน Node รับ `/cmd_vel` ไปหมุนมอเตอร์ตรงๆ มีความเสี่ยงสูงหากเกิด Latency หรือโหนดค้าง มอเตอร์อาจวิ่งชนโดยไม่หยุด
   - `ros2_control` แยกส่วนลอจิกคอนโทรลเลอร์ออกจากฮาร์ดแวร์จริง มีระบบ Command/State Interface และ Watchdog ตัดคำสั่งอัตโนมัติเมื่อ Timeout
2. **องค์ประกอบหลัก:**
   - **Controller Manager:** จัดการวงรอบเวลา (Control Loop) และการสลับโหมดคอนโทรลเลอร์
   - **Resource Manager:** โหลด Hardware Plugin และจัดการสิทธิ์การเข้าถึง Actuators/Sensors
   - **DiffDriveController:** คำนวณ Odometry และแปลง Twist เป็นความเร็วล้อซ้าย-ขวาอย่างแม่นยำ

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์คอนฟิก:** [`Advanced_ROS/01_ros2_control_Hardware/config/diff_drive_controller.yaml`](../01_ros2_control_Hardware/config/diff_drive_controller.yaml)
- **การทดลอง:**
  - วิเคราะห์การตั้งค่า `wheel_separation_multiplier` และ `twist_covariance_diagonal`
  - ตรวจสอบโครงสร้างแท็ก `<ros2_control>` ใน [`diff_drive_ros2_control.xacro`](../01_ros2_control_Hardware/urdf/diff_drive_ros2_control.xacro)

---

### สัปดาห์ที่ 2: การพัฒนา Custom C++ Hardware Interface

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **โครงสร้างคลาส `SystemInterface`:**
   - ต้องสืบทอดมาจาก `hardware_interface::SystemInterface`
   - เมธอดสำคัญ:
     - `on_init()`: โหลดพารามิเตอร์ Serial Port / Baud Rate
     - `on_activate()`: เปิดพอร์ตเชื่อมต่อมอเตอร์ และรีเซ็ต Encoder
     - `read()`: อ่านค่า Position และ Velocity ของล้อแต่ละข้าง
     - `write()`: ส่งคำสั่ง Target Velocity ไปยัง Motor Driver
2. **กฎ Real-time Safety:** ห้ามใช้ `std::cout`, `malloc`, `new`, หรือระบบ I/O ชนิดบล็อกกิ้งภายในฟังก์ชัน `read()` และ `write()`

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **การทดลอง:** ออกแบบ C++ Hardware Interface ส่งคำสั่งผ่าน Serial Communication และทดสอบคำสั่ง CLI:
  ```bash
  ros2 control list_hardware_interfaces
  ros2 control list_controllers
  ```

---

### สัปดาห์ที่ 3: การเชื่อมต่อไมโครคอนโทรลเลอร์ด้วย micro-ROS และลูปปิด PID

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **สถาปัตยกรรม micro-ROS:**
   - ใช้ eProsima Micro XRCE-DDS รันบนฮาร์ดแวร์ทรัพยากรจำกัด (เช่น ESP32 หรือ STM32 Cortex-M4)
   - Micro-ROS Client ทำหน้าที่นับพัลส์ Encoder, รัน Discrete PID Loop และ Publish ข้อมูล JointState
2. **Discrete PID Velocity Control:**
   $$u[k] = u[k-1] + K_p (e[k] - e[k-1]) + K_i T_s e[k] + \frac{K_d}{T_s} (e[k] - 2e[k-1] + e[k-2])$$

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **การทดลอง:**
  1. เปิด micro-ROS Agent บนคอมพิวเตอร์หลักเพื่อเชื่อมต่อกับบอร์ดไมโครคอนโทรลเลอร์:
     ```bash
     ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0 -b 115200
     ```
  2. ตรวจสอบสถานะการเชื่อมต่อและข้อมูล Joint States:
     ```bash
     ros2 topic echo /joint_states
     ```

---

### สัปดาห์ที่ 4: ระบบประมวลผลภาพใน ROS 2 และการคาลิเบรตกล้อง

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **Pinhole Camera Model & Distortion:**
   - พารามิเตอร์ Intrinsic Matrix $K$: ความยาวโฟกัส $(f_x, f_y)$ และจุดกึ่งกลางภาพ $(c_x, c_y)$
   - Radial and Tangential Distortion Coefficients $(k_1, k_2, p_1, p_2, k_3)$
2. **การแปลงข้อความภาพด้วย `cv_bridge`:**
   - `cv_bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')`
   - `cv_bridge.cv2_to_imgmsg(cv_image, encoding='bgr8')`

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **การทดลอง:** รันการคาลิเบรตกล้องผ่านกระดานหมากรุก (Checkerboard) 8x6 ช่อง และสร้างไฟล์ `camera_info.yaml`

---

### สัปดาห์ที่ 5: การประมวลผลภาพด้วยปัญญาประดิษฐ์ (Deep Learning YOLO)

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **Edge AI Inference Pipeline:**
   - การรับภาพ BGR8 จาก ROS 2 $\rightarrow$ ทำ Pre-processing (Resize 640x640, Normalize) $\rightarrow$ ส่งเข้า Model Inference Engine (ONNX / TensorRT) $\rightarrow$ Non-Maximum Suppression (NMS) $\rightarrow$ Publish Bounding Boxes
2. **การส่งต่อข้อมูลเข้าสู่ระบบนำทาง:**
   - การแปลง Bounding Box เป็นพิกัด 3D เชิงเรขาคณิตโดยใช้ระยะทางจาก Depth Image

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์โค้ด:** [`Advanced_ROS/02_Vision_AI_Perception/src/cv_bridge_yolo_node.py`](../02_Vision_AI_Perception/src/cv_bridge_yolo_node.py)
- **ขั้นตอนการทดลอง:**
  ```bash
  ./docker/run_lab.sh python3 Advanced_ROS/02_Vision_AI_Perception/src/cv_bridge_yolo_node.py
  ```
- ตรวจสอบผลการตรวจจับวัตถุใน Topic:
  ```bash
  ./docker/run_lab.sh ros2 topic echo /perception/detected_objects
  ```

---

### สัปดาห์ที่ 6: การตรวจจับ Visual Marker และการประมาณพิกัด 3 มิติ

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **หลักการของ AprilTag / ArUco:**
   - การสกัดขอบภาพ (Adaptive Thresholding) $\rightarrow$ ค้นหากลอบสี่เหลี่ยม (Quad Detection) $\rightarrow$ ถอดรหัสบิตข้อมูล (Bit Decoding)
2. **Perspective-n-Point (PnP) Solver:**
   - คำนวณ Rotation Matrix ($R$) และ Translation Vector ($t$) ที่สอดคล้องกับพิกัดมุมทั้ง 4 ของมาร์กเกอร์
   - แปลงเป็น Quaternion $(x, y, z, w)$ เพื่อส่งต่อให้ Nav2 Docking Server

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์โค้ด:** [`Advanced_ROS/02_Vision_AI_Perception/src/apriltag_dock_tracker.py`](../02_Vision_AI_Perception/src/apriltag_dock_tracker.py)
- **ขั้นตอนการทดลอง:**
  ```bash
  ./docker/run_lab.sh python3 Advanced_ROS/02_Vision_AI_Perception/src/apriltag_dock_tracker.py
  ```
- สังเกตพิกัดเป้าหมาย 3 มิติที่ส่งออกมาทาง `/docking/target_pose`

---

### สัปดาห์ที่ 7: การประมวลผลข้อมูล 3D Point Cloud ด้วย PCL

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **Point Cloud Library (PCL) Pipeline:**
   - **PassThrough Filter:** กรองตัดข้อมูลนอกระยะทำการ ($Z > 4.0\text{ m}$)
   - **VoxelGrid Filter:** บีบอัดข้อมูลด้วยการแทนจุดในลูกบาศก์ขนาดเท่ากัน (เช่น 5 cm Voxel)
   - **RANSAC Plane Segmentation:** หาโมเดลระนาบพื้น $Ax + By + Cz + D = 0$ และแยกเฉพาะสิ่งกีดขวางที่ลอยเหนือพื้นดินเข้าสู่ Costmap

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **การทดลอง:** เขียนโหนดแปลงภาพ Depth จากกล้องเสมือนใน Gazebo เป็น PointCloud2 และทดสอบตัดระนาบพื้นออกใน RViz2

---

### สัปดาห์ที่ 8: สอบประเมินสถาปัตยกรรมกลางภาค (Midterm Industrial Review)

#### 📝 เกณฑ์การประเมินสถาปัตยกรรมกลางภาค (Industrial Architecture Defense)
1. **การนำเสนอและสาธิตสด (Live Demo & Presentation):**
   - สาธิตระบบการขับเคลื่อนผ่าน `ros2_control` ร่วมกับการเปิดสตรีมภาพและรัน AI Perception
   - รายงานสถิติ Resource Profiling: CPU Utilization, Memory Footprint, และ Frame-to-Inference Latency (ต้องต่ำกว่า 50 ms)
   - อธิบายกลไกความปลอดภัย Fail-safe เมื่อกล้องหรือสัญญาณคำสั่งขาดหาย

---

### สัปดาห์ที่ 9: Nav2 Precision Docking Server สำหรับการเข้าชาร์จอัตโนมัติ

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **วงจรการทำงานของ Nav2 Docking Server (`opennav_docking`):**
   - **Stage 1 (Staging):** เคลื่อนที่ด้วย Nav2 ปกติไปยังจุดตั้งลำ (Staging Pose) หน้าแท่นชาร์จ 0.6–1.0 ม.
   - **Stage 2 (Detection & Approach):** ตรวจจับมาร์กเกอร์แท่นชาร์จ และควบคุมความเร็วต่ำแบบ Closed-loop Visual Servoing (0.05 m/s)
   - **Stage 3 (Contact Verification):** ตรวจสอบแรงสัมผัสหรือระดับกระแสไฟชาร์จก่อนตัดกำลังขับ

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์คอนฟิก:** [`Advanced_ROS/03_Nav2_Precision_Docking/config/docking_server_params.yaml`](../03_Nav2_Precision_Docking/config/docking_server_params.yaml)
- **การทดลอง:** วิเคราะห์พารามิเตอร์ `docking_threshold` (0.03 ม.) และการตั้งค่า `staging_x_offset`

---

### สัปดาห์ที่ 10: การออกแบบ Nav2 Behavior Trees ขั้นสูง

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **ทฤษฎี Behavior Tree (BT):**
   - **Fallback (Selector):** ประมวลผลลูกทีละตัวจนกว่าจะพบตัวที่ `SUCCESS`
   - **Sequence:** ประมวลผลลูกทีละตัวจนจบ หากตัวใด `FAILURE` จะหยุดทันที
   - **Reactive Sequence:** ตรวจสอบ Condition ซ้ำทุก Tick ระหว่างรัน Action
2. **Recovery Pipeline ใน Nav2:**
   $$\text{ComputePath} \rightarrow \text{FollowPath} \xrightarrow{\text{Failed}} \text{ClearCostmap} \rightarrow \text{Spin} \rightarrow \text{BackUp}$$

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์ BT XML:** [`Advanced_ROS/03_Nav2_Precision_Docking/behavior_trees/dock_and_charge_bt.xml`](../03_Nav2_Precision_Docking/behavior_trees/dock_and_charge_bt.xml)
- **การทดลอง:** ศึกษาขั้นตอนการผูกเงื่อนไขแบตเตอรี่ต่ำเพื่อกระตุ้นให้หุ่นยนต์เข้าสู่โหมดชาร์จไฟอัตโนมัติ

---

### สัปดาห์ที่ 11: การควบคุมพื้นที่ด้วย Nav2 Costmap Filters & Speed Zones

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **Costmap Filter Architecture:**
   - การใช้ภาพขาว-ดำ (Costmap Filter Mask) ซ้อนทับบนแผนที่หลัก
   - **Keep-out Zones:** พื้นที่ห้ามวิ่งผ่าน (เช่น เขตสารเคมีอันตราย หรือรางรถไฟ)
   - **Speed Restriction Zones:** ควบคุมความเร็วสูงสุดของหุ่นยนต์ เช่น ลดความเร็วเหลือ 0.2 m/s เมื่อผ่านทางแยกที่มีคนเดิน

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **การทดลอง:** สร้างภาพมาสก์ PGM กำหนดพื้นที่ห้ามเข้า และทดสอบสั่งหุ่นยนต์วางเส้นทางหลบเลี่ยงพื้นที่ดังกล่าวโดยอัตโนมัติ

---

### สัปดาห์ที่ 12: สถาปัตยกรรมระบบฝูงหุ่นยนต์ (Multi-Robot Fleet Architecture)

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **การแยกแชนเนลสื่อสาร:**
   - การใช้ ROS 2 Namespaces (`/amr_01`, `/amr_02`)
   - การใช้ `frame_prefix` ใน TF Tree (`amr_01/base_link`, `amr_02/base_link`) เพื่อป้องกันการเขียนพิกัดทับกัน
2. **โปรโตคอล Zenoh สำหรับเครือข่ายหุ่นยนต์:**
   - แก้ปัญหา Multicast Storm ใน Wi-Fi อุตสาหกรรม โดยใช้ Zenoh Router ในการส่งข้อมูลข้ามซับเน็ต

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์โค้ด:** [`Advanced_ROS/04_Multi_Robot_Fleet_OpenRMF/launch/multi_robot_fleet.launch.py`](../04_Multi_Robot_Fleet_OpenRMF/launch/multi_robot_fleet.launch.py)
- **ขั้นตอนการทดลอง:**
  ```bash
  ./docker/run_lab.sh ros2 launch Advanced_ROS/04_Multi_Robot_Fleet_OpenRMF/launch/multi_robot_fleet.launch.py
  ```
- ตรวจสอบว่ามี Topic ของหุ่นยนต์ทั้ง 2 ตัวแยกกันอย่างสมบูรณ์:
  ```bash
  ./docker/run_lab.sh ros2 topic list | grep amr_
  ```

---

### สัปดาห์ที่ 13: ระบบจัดการจราจรและงานส่วนกลางด้วย Open-RMF

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **สถาปัตยกรรม Open-RMF (Robotics Middleware Framework):**
   - **RMF Traffic Schedule:** ฐานข้อมูลแบบกระจายศูนย์เก็บเส้นทางและช่วงเวลา ($X, Y, t$) ของหุ่นยนต์ทุกตัว
   - **Traffic Deconfliction:** ตรวจจับเส้นทางขัดแย้งล่วงหน้า และสั่งให้หุ่นยนต์ตัวหนึ่งหยุดรอที่ Waypoint ก่อนทางแยก
   - **Infrastructure Interfaces:** สื่อสารกับระบบลิฟต์และประตูปิด-เปิดอัตโนมัติ

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์คอนฟิก:** [`Advanced_ROS/04_Multi_Robot_Fleet_OpenRMF/config/fleet_adapter_config.yaml`](../04_Multi_Robot_Fleet_OpenRMF/config/fleet_adapter_config.yaml)
- **การทดลอง:** วิเคราะห์การกำหนด Vicinity Bubble รัศมี 0.5 ม. ป้องกันไม่ให้หุ่นยนต์เข้าใกล้กันเกินไป

---

### สัปดาห์ที่ 14: วิศวกรรมระบบระดับ Production ด้วย Managed Lifecycle Nodes

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **Managed Lifecycle States:**
   - `Unconfigured` $\rightarrow$ `on_configure()` $\rightarrow$ `Inactive`
   - `Inactive` $\rightarrow$ `on_activate()` $\rightarrow$ `Active` (เริ่มทำงานและส่งข้อมูล)
   - `Active` $\rightarrow$ `on_deactivate()` $\rightarrow$ `Inactive` (หยุดชั่วคราวเพื่อความปลอดภัย)
   - `Inactive` $\rightarrow$ `on_cleanup()` $\rightarrow$ `Unconfigured` (ปล่อยทรัพยากร)
   - ป้องกันอันตรายจากการที่โหนดสั่งหมุนมอเตอร์ก่อนที่เซนเซอร์ LiDAR จะพร้อมทำงาน

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์โค้ด:** [`Advanced_ROS/05_Production_CI_CD_Security/src/lifecycle_laser_sensor.py`](../05_Production_CI_CD_Security/src/lifecycle_laser_sensor.py)
- **ขั้นตอนการทดลอง:**
  1. เปิดโหนด Lifecycle:
     ```bash
     ./docker/run_lab.sh python3 Advanced_ROS/05_Production_CI_CD_Security/src/lifecycle_laser_sensor.py
     ```
  2. สั่งเปลี่ยนสถานะของโหนดผ่าน CLI:
     ```bash
     ./docker/run_lab.sh ros2 lifecycle get /lifecycle_laser_sensor
     ./docker/run_lab.sh ros2 lifecycle set /lifecycle_laser_sensor configure
     ./docker/run_lab.sh ros2 lifecycle set /lifecycle_laser_sensor activate
     ```

---

### สัปดาห์ที่ 15: ความมั่นคงปลอดภัยไซเบอร์ (SROS 2) และ CI/CD ด้วย launch_testing

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **มาตรฐาน SROS 2 (Secure ROS 2):**
   - **Authentication:** พิสูจน์ตัวตนโหนดด้วยใบรับรองดิจิทัล X.509
   - **Access Control:** จำกัดสิทธิ์โหนดว่าสามารถ Publish หรือ Subscribe ท็อปปิกใดได้บ้าง
   - **Encryption:** เข้ารหัสแพ็กเก็ต DDS บนเครือข่ายด้วย AES-GCM-256
2. **Automated Testing ใน CI/CD:**
   - การใช้ `launch_testing` รันหุ่นยนต์ในคอนเทนเนอร์แบบไร้หน้าจอ (Headless) เพื่อทดสอบการประกอบโหนดก่อน Deploy ขึ้นหุ่นยนต์จริง

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์ชุดทดสอบ:** [`Advanced_ROS/05_Production_CI_CD_Security/tests/test_amr_launch.py`](../05_Production_CI_CD_Security/tests/test_amr_launch.py)
- **การทดลอง:** รันชุดทดสอบความสมบูรณ์ของระบบผ่าน `pytest`:
  ```bash
  pytest-3 Advanced_ROS/05_Production_CI_CD_Security/tests/test_amr_launch.py
  ```

---

### สัปดาห์ที่ 16: Capstone Final Showcase & Industrial Defense

#### 🏆 เกณฑ์การสอบโครงงานบูรณาการระดับอุตสาหกรรม (Final Capstone Evaluation)
- **ไฟล์ระบบครบวงจร:** [`Advanced_ROS/06_Capstone_Project/launch/full_warehouse_system.launch.py`](../06_Capstone_Project/launch/full_warehouse_system.launch.py)
- **เกณฑ์การประเมิน 5 มิติ:** ดูรายละเอียดใน [`rubrics.md`](../06_Capstone_Project/rubrics.md)
  1. สถาปัตยกรรมระบบและความถูกต้องตามมาตรฐานวิศวกรรม (20%)
  2. การควบคุมฮาร์ดแวร์จริงและการจัดการความปลอดภัยแบบ Lifecycle (20%)
  3. ประสิทธิภาพของการนำทางอัตโนมัติและการหลบหลีกสิ่งกีดขวาง (25%)
  4. ความแม่นยำของระบบเข้าแท่นชาร์จอัตโนมัติและการตรวจจับ Visual Marker (20%)
  5. คุณภาพซอฟต์แวร์, การรักษาความปลอดภัย SROS 2 และชุดทดสอบอัตโนมัติ (15%)
