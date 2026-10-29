# 📚 คู่มือการสอนฉบับสมบูรณ์: Lecture & Lab Guide (16 สัปดาห์)

> ℹ️ เอกสารนี้เป็น **ภาพรวมย่อ** ของทั้ง 16 สัปดาห์ เนื้อหาฉบับละเอียด คำสั่งที่ทดสอบแล้ว และ **ผลการรันจริง** อยู่ใน
> `Readme.md` / `Lab_Exercises.md` ของแต่ละโฟลเดอร์ `Week_NN_*` (ดูตารางใน [`../README.md`](../README.md)) หากข้อความตรงไหน
> ขัดกัน ให้ยึดไฟล์ของสัปดาห์นั้นเป็นหลัก คำสั่ง `ros2 run/launch amr_weekNN ...` ต้อง `make build` ก่อน

## วิชา: AMR-101 Essential ROS 2 for Autonomous Mobile Robots

คู่มือนี้ประกอบด้วยเนื้อหาการบรรยายเชิงทฤษฎี (Lecture Notes) และขั้นตอนการปฏิบัติการแล็บ (Hands-on Lab Guides) อย่างละเอียดครบทั้ง 16 สัปดาห์ สำหรับผู้สอนและผู้เรียน

---

## สารบัญสัปดาห์
- [สัปดาห์ที่ 1: สภาพแวดล้อม สถาปัตยกรรม และเครือข่าย DDS](#สัปดาห์ที่-1-สภาพแวดล้อม-สถาปัตยกรรม-และเครือข่าย-dds)
- [สัปดาห์ที่ 2: โครงสร้างโหนด, Topics และการจัดการ QoS](#สัปดาห์ที่-2-โครงสร้างโหนด-topics-และการจัดการ-qos)
- [สัปดาห์ที่ 3: ระบบ Service-Client และการป้องกัน Deadlock](#สัปดาห์ที่-3-ระบบ-service-client-และการป้องกัน-deadlock)
- [สัปดาห์ที่ 4: Action Protocol สำหรับงานระยะยาวและการ Cancel](#สัปดาห์ที่-4-action-protocol-สำหรับงานระยะยาวและการ-cancel)
- [สัปดาห์ที่ 5: Dynamic Parameters และ Python Launch Architecture](#สัปดาห์ที่-5-dynamic-parameters-และ-python-launch-architecture)
- [สัปดาห์ที่ 6: มาตรฐานวิศวกรรมพิกัด (REP 103/105) และจลนศาสตร์ AMR](#สัปดาห์ที่-6-มาตรฐานวิศวกรรมพิกัด-rep-103105-และจลนศาสตร์-amr)
- [สัปดาห์ที่ 7: การสร้างแบบจำลอง 3 มิติ (URDF) และ Inertia Matrix](#สัปดาห์ที่-7-การสร้างแบบจำลอง-3-มิติ-urdf-และ-inertia-matrix)
- [สัปดาห์ที่ 8: สอบปฏิบัติการกลางภาค (Midterm Practical Exam)](#สัปดาห์ที่-8-สอบปฏิบัติการกลางภาค-midterm-practical-exam)
- [สัปดาห์ที่ 9: ระบบพิกัดสัมพัทธ์และการแปลงพิกัด (TF2 System)](#สัปดาห์ที่-9-ระบบพิกัดสัมพัทธ์และการแปลงพิกัด-tf2-system)
- [สัปดาห์ที่ 10: สภาพแวดล้อมจำลอง 3 มิติด้วย Gazebo Sim (Harmonic)](#สัปดาห์ที่-10-สภาพแวดล้อมจำลอง-3-มิติด้วย-gazebo-sim-harmonic)
- [สัปดาห์ที่ 11: การต่อเชื่อมมอเตอร์ เซนเซอร์ และ ros_gz_bridge](#สัปดาห์ที่-11-การต่อเชื่อมมอเตอร์-เซนเซอร์-และ-ros_gz_bridge)
- [สัปดาห์ที่ 12: การสร้างแผนที่ 2 มิติด้วย SLAM Toolbox](#สัปดาห์ที่-12-การสร้างแผนที่-2-มิติด้วย-slam-toolbox)
- [สัปดาห์ที่ 13: สถาปัตยกรรม Nav2 Stack และระบบ Costmap 2D](#สัปดาห์ที่-13-สถาปัตยกรรม-nav2-stack-และระบบ-costmap-2d)
- [สัปดาห์ที่ 14: การวางแผนเส้นทาง, คอนโทรลเลอร์ และ AMCL Localization](#สัปดาห์ที่-14-การวางแผนเส้นทาง-คอนโทรลเลอร์-และ-amcl-localization)
- [สัปดาห์ที่ 15: ระบบลาดตระเวนจุดตรวจอัตโนมัติ (Waypoint Patrol)](#สัปดาห์ที่-15-ระบบลาดตระเวนจุดตรวจอัตโนมัติ-waypoint-patrol)
- [สัปดาห์ที่ 16: สอบปฏิบัติการปลายภาค (Final AMR Demonstration)](#สัปดาห์ที่-16-สอบปฏิบัติการปลายภาค-final-amr-demonstration)

---

### สัปดาห์ที่ 1: สภาพแวดล้อม สถาปัตยกรรม และเครือข่าย DDS

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **วิวัฒนาการทางสถาปัตยกรรม:**
   - **ROS 1:** ใช้สถาปัตยกรรมแบบรวมศูนย์ (Centralized) ผ่านโหนด `roscore` (Master Node) หาก Master ดับ ระบบทั้งหมดจะสื่อสารกันไม่ได้
   - **ROS 2:** สถาปัตยกรรมกระจายศูนย์ (Decentralized Peer-to-Peer) ขับเคลื่อนด้วยมาตรฐานอุตสาหกรรม **Data Distribution Service (DDS)** โดยไม่มีจุดล้มเหลวเดี่ยว (No Single Point of Failure)
2. **DDS และโปรโตคอลการค้นพบ (Discovery Mechanism):**
   - ใช้โปรโตคอล **Simple Participant Discovery Protocol (SPDP)** ผ่านเครือข่าย UDP Multicast
   - การแยกกลุ่มเครือข่ายในห้องเรียนหรือโรงงานทำผ่านตัวแปรสภาพแวดล้อม:
     $$\text{Multicast Port} = 7400 + 250 \times \text{Domain ID}$$
     โดย `ROS_DOMAIN_ID` มีค่าตั้งแต่ $0$ ถึง $101$ (ค่าปริยายคือ $0$)
3. **Colcon Workspaces & Overlay/Underlay:**
   - Underlay คือสภาพแวดล้อมหลักของระบบ (`/opt/ros/jazzy`)
   - Overlay คือโค้ดที่เราเขียนขึ้นเอง (`~/ros2_ws/install/setup.bash`) ซึ่งจะ Overwrite การทำงานของแพ็กเกจเดิมหากมีชื่อซ้ำกัน
4. **วิธีการติดตั้งสภาพแวดล้อม ROS 2:**
   - ติดตั้งแบบ Native บน Ubuntu 24.04 (ผ่าน APT Official Repo)
   - ติดตั้งแบบ Containerization ผ่าน Docker (`ros:lab-runner`)
   - ติดตั้งบน Windows 10/11 ผ่าน WSL2 + WSLg
   *(รายละเอียดขั้นตอนทั้งหมดระบุไว้ใน [docs/ros2_installation_guide.md](../../docs/ros2_installation_guide.md))*

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **วัตถุประสงค์:** ติดตั้งสภาพแวดล้อม รัน Docker Container และทดสอบการค้นพบโหนดข้าม Domain ID
- **ขั้นตอนการทดลอง:**
  1. เข้าสู่ไดเรกทอรีโครงการและเปิดใช้งานคอนเทนเนอร์:
     ```bash
     cd /mnt/sda/ros
     ./docker/run_lab.sh ros2 doctor --report
     ```
  2. ทดสอบตรวจสอบเครือข่าย DDS Multicast:
     ```bash
     # หน้าต่างที่ 1: รอรับแพ็กเก็ต Multicast
     ./docker/run_lab.sh ros2 multicast receive

     # หน้าต่างที่ 2: ส่งแพ็กเก็ต Multicast
     ./docker/run_lab.sh ros2 multicast send
     ```
  3. ทดลองตั้งค่า `ROS_DOMAIN_ID=10` ในหน้าต่างที่ 1 และ `ROS_DOMAIN_ID=20` ในหน้าต่างที่ 2 สังเกตว่าโหนด Talker/Listener ไม่สามารถมองเห็นกันได้
- **ผลลัพธ์ที่คาดหวัง:** `ros2 doctor` รายงานสถานะผ่านทุกข้อ และเข้าใจการแยกแชนเนลด้วย Domain ID

---

### สัปดาห์ที่ 2: โครงสร้างโหนด, Topics และการจัดการ QoS

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **โครงสร้างคลาส `rclpy.node.Node`:**
   - การเขียนโปรแกรมแบบ Object-Oriented (OOP) โดยสืบทอดคลาสจาก `Node`
   - การหลีกเลี่ยงการใช้ Global Variables เพื่อรองรับ Multi-threading ในอนาคต
2. **Quality of Service (QoS) Policies:**
   - **Reliability:**
     - `RELIABLE`: ตรวจสอบและส่งข้อมูลซ้ำหากสูญหาย เหมาะกับคำสั่ง `/cmd_vel` หรือสถานะระบบ
     - `BEST_EFFORT`: เน้นความเร็ว ไม่ส่งซ้ำ เหมาะกับเซนเซอร์ความเร็วสูง เช่น LiDAR หรือกล้อง
   - **Durability:**
     - `TRANSIENT_LOCAL`: โหนด Publisher จะเก็บข้อความล่าสุดไว้ในแคช เพื่อส่งให้ Subscriber ที่เพิ่งเปิดขึ้นมาใหม่ทันที (Latched Topic)
     - `VOLATILE`: ไม่มีการเก็บย้อนหลัง
   - **กฎความเข้ากันได้ (QoS Compatibility Rule):**  
     Publisher และ Subscriber จะสื่อสารกันได้ก็ต่อเมื่อ **Subscriber ไม่เรียกร้องระดับบริการที่สูงกว่าที่ Publisher กำหนด** เช่น หาก Publisher เป็น `BEST_EFFORT` แต่ Subscriber ร้องขอ `RELIABLE` การเชื่อมต่อจะล้มเหลว (QoS Incompatible Warning)

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์โค้ด:** [`Essential_ROS/01_Core_Communication/src/sensor_qos_publisher.py`](../Week_02_Nodes_Topics_QoS/src/sensor_qos_publisher.py) และ [`sensor_qos_subscriber.py`](../Week_02_Nodes_Topics_QoS/src/sensor_qos_subscriber.py)
- **ขั้นตอนการทดลอง:**
  1. สั่งรันโหนด Publisher ในโหมด QoS พิเศษ:
     ```bash
     ./docker/run_lab.sh ros2 run amr_week02 sensor_qos_publisher
     ```
  2. ในอีกหน้าต่างหนึ่ง รันโหนด Subscriber สังเกตว่าโหนดสามารถรับข้อความ `SYSTEM_READY` ที่ Latched ไว้ได้ทันทีแม้จะเปิดทีหลัง:
     ```bash
     ./docker/run_lab.sh ros2 run amr_week02 sensor_qos_subscriber
     ```
  3. ตรวจสอบรายละเอียด QoS ของท็อปปิกด้วย CLI:
     ```bash
     ./docker/run_lab.sh ros2 topic info /sensor/temperature --verbose
     ```

---

### สัปดาห์ที่ 3: ระบบ Service-Client และการป้องกัน Deadlock

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **หลักการทำงานของ Service:**
   - เป็นการสื่อสารแบบ Synchronous Request-Response (1-to-1 RPC pattern)
   - ประกอบด้วยสองส่วนคือ Request Message และ Response Message ซึ่งนิยามอยู่ในไฟล์ `.srv`
2. **ข้อควรระวังเรื่อง Deadlock:**
   - การเรียกใช้ Service แบบบล็อกกิ้ง (`cli.call(req)`) ภายใน Callback เดียวกันของ Single-Threaded Executor จะทำให้เธรดค้างถาวร (Deadlock)
   - แนวทางแก้ไข: ให้ใช้ `call_async()` หรือใช้ `ReentrantCallbackGroup` ควบคู่กับ `MultiThreadedExecutor`

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์โค้ด:** [`Essential_ROS/01_Core_Communication/src/power_service_server.py`](../Week_03_Services_Clients/src/power_service_server.py)
- **ขั้นตอนการทดลอง:**
  1. เปิดการทำงานของ Service Server:
     ```bash
     ./docker/run_lab.sh ros2 run amr_week03 power_service_server
     ```
  2. ตรวจสอบรายการ Service ที่พร้อมให้บริการ:
     ```bash
     ./docker/run_lab.sh ros2 service list
     ```
  3. ทดสอบส่งคำสั่งสลับโหมดประหยัดพลังงาน:
     ```bash
     ./docker/run_lab.sh ros2 service call /robot/set_power_mode std_srvs/srv/SetBool "{data: true}"
     ```
- **ผลลัพธ์ที่คาดหวัง:** ได้รับการตอบกลับ `success=True` พร้อมข้อความแจ้งเตือนจำกัดความเร็วสูงสุดเหลือ 0.3 m/s

---

### สัปดาห์ที่ 4: Action Protocol สำหรับงานระยะยาวและการ Cancel

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **โครงสร้างสถาปัตยกรรมของ Action:**
   - Action ประกอบด้วย 3 บริการย่อย (Goal Service, Cancel Service, Result Service) และ 2 ท็อปปิกย่อย (Feedback Topic, Status Topic)
2. **State Machine ของ Action Goal:**
   $$\text{Goal Received} \rightarrow \text{Accepted} \rightarrow \text{Executing} \xrightarrow{\text{Cancel Requested}} \text{Canceling} \rightarrow \text{Canceled}$$
   หรือเมื่อทำภารกิจสำเร็จ: $\text{Executing} \rightarrow \text{Succeeded}$

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์โค้ด:** [`Essential_ROS/01_Core_Communication/src/navigate_action_server.py`](../Week_04_Actions_Preemption/src/navigate_action_server.py)
- **ขั้นตอนการทดลอง:**
  1. เริ่มต้น Action Server:
     ```bash
     ./docker/run_lab.sh ros2 run amr_week04 navigate_action_server
     ```
  2. ส่ง Goal คำสั่งระยะทาง 8 สเต็ป พร้อมเปิดรับ Feedback แบบเรียลไทม์:
     ```bash
     ./docker/run_lab.sh ros2 action send_goal /navigate_distance example_interfaces/action/Fibonacci "{order: 8}" --feedback
     ```
  3. ทดสอบกด `Ctrl+C` กลางคันเพื่อสังเกตว่า Action Server ดักจับและเข้าสู่ฟังก์ชัน `cancel_callback` อย่างถูกต้อง

---

### สัปดาห์ที่ 5: Dynamic Parameters และ Python Launch Architecture

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **Parameter Callbacks:**
   - `add_on_set_parameters_callback` ทำหน้าที่เป็น Gatekeeper ตรวจสอบความถูกต้อง (Data Validation) ของค่าตัวแปรก่อนยอมรับการเปลี่ยนแปลง
2. **Python Launch System:**
   - ใช้ `LaunchDescription` รวบรวม Node, GroupAction, IncludeLaunchDescription
   - ส่งต่อค่าตัวแปรด้วย `DeclareLaunchArgument` และ `LaunchConfiguration`

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์โค้ด:** [`Essential_ROS/01_Core_Communication/launch/core_system.launch.py`](../Week_05_Parameters_Launch/launch/core_system.launch.py)
- **ขั้นตอนการทดลอง:**
  1. รันระบบย่อยทั้งหมดในคลิกเดียวผ่าน Launch File:
     ```bash
     ./docker/run_lab.sh ros2 launch amr_week05 core_system.launch.py fleet_id:=AMR_PRO_01
     ```
  2. ในอีกหน้าต่าง ทดลองเปลี่ยนค่าความเร็วของหุ่นยนต์แบบเรียลไทม์:
     ```bash
     # ทดสอบใส่ค่าที่ถูกต้อง (1.5 m/s) -> สำเร็จ
     ./docker/run_lab.sh ros2 param set /fleet_parameters max_linear_speed 1.5

     # ทดสอบใส่ค่าที่เกินขีดจำกัดความปลอดภัย (5.0 m/s) -> ถูก Reject อัตโนมัติ
     ./docker/run_lab.sh ros2 param set /fleet_parameters max_linear_speed 5.0
     ```

---

### สัปดาห์ที่ 6: มาตรฐานวิศวกรรมพิกัด (REP 103/105) และจลนศาสตร์ AMR

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **REP 103: มาตรฐานหน่วยและพิกัด:**
   - ระบบพิกัดมือขวา (Right-Hand Rule): แกน $+X$ ชี้ไปข้างหน้า, แกน $+Y$ ชี้ไปทางซ้าย, แกน $+Z$ ชี้ขึ้นบน
   - มุม Yaw หมุนทวนเข็มนาฬิกาเป็นบวก มีหน่วยเป็นเรเดียน
2. **REP 105: มาตรฐานพิกัดหุ่นยนต์เคลื่อนที่:**
   - `earth` $\rightarrow$ `map` (พิกัดแผนที่โลก ไม่มีความคลาดเคลื่อนสะสม)
   - `map` $\rightarrow$ `odom` (ชดเชยการลื่นไถลแบบไม่ต่อเนื่องด้วยระบบ Localization)
   - `odom` $\rightarrow$ `base_footprint` (ระนาบพื้นใต้หุ่นยนต์ อิงจากการนับรอบล้อ ต่อเนื่องแต่มี Drift)
   - `base_footprint` $\rightarrow$ `base_link` (จุดศูนย์กลางทางกายภาพของโครงหุ่นยนต์)
3. **จลนศาสตร์ Differential Drive:**
   $$v = \frac{v_R + v_L}{2}, \quad \omega = \frac{v_R - v_L}{L}$$
   $$v_R = v + \frac{\omega L}{2}, \quad v_L = v - \frac{\omega L}{2}$$
   เมื่อ $L$ คือระยะห่างระหว่างล้อขับ (Wheel Separation)

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **การทดลอง:** คำนวณความเร็วล้อซ้ายและขวาเมื่อหุ่นยนต์ต้องการเลี้ยวโค้ง $v=0.4\text{ m/s}, \omega=0.8\text{ rad/s}$ โดยที่ $L=0.24\text{ m}$
  - $v_R = 0.4 + (0.8 \times 0.24 / 2) = 0.496\text{ m/s}$
  - $v_L = 0.4 - (0.8 \times 0.24 / 2) = 0.304\text{ m/s}$
- ตรวจสอบการแปลงจากความเร็วเชิงเส้นเป็นความเร็วรอบของล้อ $\dot{\theta} = v / r$

---

### สัปดาห์ที่ 7: การสร้างแบบจำลอง 3 มิติ (URDF) และ Inertia Matrix

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **โครงสร้าง URDF XML:**
   - `<link>` นิยามวัตถุทางกายภาพ (Chassis, Wheels, Casters, Sensors)
   - `<joint>` นิยามข้อต่อและการเคลื่อนที่ (`continuous` หมุนต่อเนื่อง, `fixed` ยึดแน่น, `revolute` มีขอบเขต)
2. **การคำนวณ Moment of Inertia สำคัญ:**
   - ทรงกระบอก (Cylinder มวล $m$, รัศมี $r$, ความสูง $h$ แกนหมุนตามยาว):
     $$I_{zz} = \frac{1}{2} m r^2, \quad I_{xx} = I_{yy} = \frac{1}{12} m (3r^2 + h^2)$$
   - กล่องสี่เหลี่ยม (Box มวล $m$, กว้าง $w$, ยาว $d$, สูง $h$):
     $$I_{xx} = \frac{1}{12} m (h^2 + d^2), \quad I_{yy} = \frac{1}{12} m (w^2 + h^2), \quad I_{zz} = \frac{1}{12} m (w^2 + d^2)$$

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์โค้ด:** [`Essential_ROS/02_Robot_Modeling_TF2/urdf/diff_drive_robot.urdf`](../Week_07_URDF_Robot_Modeling/urdf/diff_drive_robot.urdf)
- **ขั้นตอนการทดลอง:**
  1. ตรวจสอบความถูกต้องของโครงสร้าง XML ด้วย `check_urdf`:
     ```bash
     ./docker/run_lab.sh check_urdf Essential_ROS/02_Robot_Modeling_TF2/urdf/diff_drive_robot.urdf
     ```
  2. เปิดแสดงผลโครงสร้างหุ่นยนต์บน RViz2:
     ```bash
     ./docker/run_lab.sh ros2 launch amr_week07 display_urdf.launch.py
     ```

---

### สัปดาห์ที่ 8: สอบปฏิบัติการกลางภาค (Midterm Practical Exam)

#### 📝 รายละเอียดข้อสอบปฏิบัติการกลางภาค (3 ชั่วโมง)
1. **โจทย์:** ให้ออกแบบหุ่นยนต์ส่งของ 3 ล้อ (2 ล้อขับ + 1 ล้ออิสระ Caster) ที่มีขนาดกว้าง 0.3 ม. ยาว 0.5 ม. สูง 0.15 ม. มวล 8 กก.
2. **ข้อกำหนดที่ต้องส่ง:**
   - ไฟล์ URDF ที่มีข้อต่อครบถ้วนและผ่านการตรวจสอบ `check_urdf`
   - มีการติดตั้งเซนเซอร์ LiDAR ยื่นออกมาด้านหน้า 0.15 ม.
   - เขียนโหนด Python สำหรับรับคำสั่งความเร็ว และมี Dynamic Parameter ปรับแก้ขนาดความกว้างล้อได้แบบเรียลไทม์
   - เขียน Launch File รวมระบบทั้งหมดให้เปิดขึ้นมาพร้อมแสดงผลบน RViz2 ได้อย่างสมบูรณ์

---

### สัปดาห์ที่ 9: ระบบพิกัดสัมพัทธ์และการแปลงพิกัด (TF2 System)

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **TF2 Architecture:**
   - โหนดบรอดแคสต์ข้อมูลเข้าสู่ Topic `/tf` (Dynamic Transforms) หรือ `/tf_static` (Static Transforms)
   - `tf2_ros::Buffer` ทำหน้าที่เป็น Ring Buffer เก็บประวัติพิกัดย้อนหลังได้ 10 วินาที
2. **การแปลงพิกัดจุดเป้าหมาย:**
   - การหาตำแหน่งสิ่งกีดขวางจากพิกัดของกล้อง $[X_c, Y_c, Z_c]$ ไปเป็นพิกัดอ้างอิงของหุ่นยนต์ $[X_b, Y_b, Z_b]$:
     $$P_{\text{base}} = T_{\text{base}}^{\text{camera}} \times P_{\text{camera}}$$

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ขั้นตอนการทดลอง:**
  1. ตรวจสอบต้นไม้สายสัมพันธ์พิกัด (TF Tree) ของทั้งระบบ:
     ```bash
     ./docker/run_lab.sh ros2 run tf2_tools view_frames
     ```
  2. ดูค่า Transform แบบสดๆ ระหว่างจุดกำเนิดล้อกับฐานหุ่นยนต์:
     ```bash
     ./docker/run_lab.sh ros2 run tf2_ros tf2_echo base_link left_wheel_link
     ```

---

### สัปดาห์ที่ 10: สภาพแวดล้อมจำลอง 3 มิติด้วย Gazebo Sim (Harmonic)

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **Simulation Description Format (SDF):**
   - ไฟล์ `.sdf` ใช้จำลอง World ซึ่งประกอบด้วย Physics Engine, แหล่งกำเนิดแสง Sun, ระนาบพื้นดิน Ground, สิ่งปลูกสร้าง และโมเดลหุ่นยนต์
2. **คุณสมบัติทางฟิสิกส์และการชน:**
   - สัมประสิทธิ์ความเสียดทาน Coulomb Friction ($\mu_1, \mu_2$)
   - ความแข็งของหน้าสัมผัส (Contact Stiffness $K_p$) และการหน่วง (Damping $K_d$)

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์โค้ด:** [`Essential_ROS/03_Gazebo_Simulation/worlds/warehouse.sdf`](../Week_10_Gazebo_Sim_Harmonic/worlds/warehouse.sdf)
- **ขั้นตอนการทดลอง:**
  1. ตรวจสอบความถูกต้องของไฟล์ World SDF:
     ```bash
     ./docker/run_lab.sh gz sdf -k Essential_ROS/03_Gazebo_Simulation/worlds/warehouse.sdf
     ```
  2. เปิด Gazebo Sim รันโลกคลังสินค้า:
     ```bash
     ./docker/run_lab.sh gz sim Essential_ROS/03_Gazebo_Simulation/worlds/warehouse.sdf
     ```

---

### สัปดาห์ที่ 11: การต่อเชื่อมมอเตอร์ เซนเซอร์ และ ros_gz_bridge

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **กลไกการแปลงข้อความ:**
   - Gazebo Sim ใช้ Protobuf Messages ภายในเครือข่าย Gazebo Transport
   - `ros_gz_bridge` ทำหน้าที่สะพานแปลงข้อความระหว่าง Protobuf $\leftrightarrow$ ROS 2 Interfaces แบบสองทิศทาง
2. **การจับคู่ท็อปปิกมาตรฐาน:**
   - `/cmd_vel` (`geometry_msgs/msg/Twist` $\rightarrow$ `gz.msgs.Twist`)
   - `/odom` (`gz.msgs.Odometry` $\rightarrow$ `nav_msgs/msg/Odometry`)
   - `/scan` (`gz.msgs.LaserScan` $\rightarrow$ `sensor_msgs/msg/LaserScan`)

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ขั้นตอนการทดลอง:**
  1. รัน Launch File เปิด Gazebo, Spawner และ Bridge พร้อมกัน:
     ```bash
     ./docker/run_lab.sh ros2 launch amr_week11 gazebo_world.launch.py headless:=true
     ```
  2. ในอีกหน้าต่าง เปิดคีย์บอร์ดควบคุมหุ่นยนต์:
     ```bash
     ./docker/run_lab.sh ros2 run teleop_twist_keyboard teleop_twist_keyboard
     ```
  3. ตรวจสอบความถี่ของข้อมูลสแกน LiDAR:
     ```bash
     ./docker/run_lab.sh ros2 topic hz /scan
     ```

---

### สัปดาห์ที่ 12: การสร้างแผนที่ 2 มิติด้วย SLAM Toolbox

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **หลักการ Graph-based SLAM:**
   - โหนดแทนตำแหน่งของหุ่นยนต์ในแต่ละช่วงเวลา (Poses)
   - เส้นเชื่อม (Edges) แทนความสัมพันธ์เชิงมิติจากการจับคู่เส้นสแกน LiDAR (Scan Matching)
   - การตรวจจับการวนกลับมาที่เดิม (Loop Closure) เพื่อขจัดความคลาดเคลื่อนสะสมด้วย **Ceres Solver**

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ขั้นตอนการทดลอง:**
  1. เริ่มต้นระบบสร้างแผนที่แบบ Online Asynchronous SLAM:
     ```bash
     ./docker/run_lab.sh ros2 launch amr_week12 slam_mapping_sim.launch.py headless:=true explore:=true
     ```
  2. ขับหุ่นยนต์สำรวจรอบโกดังจนแผนที่เชื่อมต่อกันครบถ้วน
  3. สั่งบันทึกแผนที่ด้วย Map Saver CLI:
     ```bash
     ./docker/run_lab.sh ros2 run nav2_map_server map_saver_cli -f /mnt/sda/ros/Essential_ROS/04_SLAM_Mapping/maps/warehouse_map
     ```

---

### สัปดาห์ที่ 13: สถาปัตยกรรม Nav2 Stack และระบบ Costmap 2D

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **โครงสร้างของ Costmap 2D:**
   - **Static Layer:** อ่านข้อมูลสิ่งกีดขวางถาวรจากไฟล์แผนที่
   - **Obstacle Layer:** เพิ่ม/ลดสิ่งกีดขวางแบบไดนามิกจากเซนเซอร์ LiDAR ตามเวลาจริง
   - **Inflation Layer:** ขยายขอบเขตอันตรายรอบสิ่งกีดขวางตามสูตร Cost Decay:
     $$\text{cost} = e^{-\text{cost\_scaling\_factor} \times (\text{distance} - r_{\text{inscribed}})}$$

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์คอนฟิก:** [`Essential_ROS/05_Nav2_Navigation/config/nav2_params.yaml`](../Week_14_Path_Planning_AMCL/config/nav2_params.yaml)
- **ขั้นตอนการทดลอง:**
  - ปรับค่า `inflation_radius` จาก 0.55 ม. เป็น 0.85 ม. และสังเกตการขยายตัวของพื้นที่สีแดง/เหลืองบน RViz2 เพื่อป้องกันไม่ให้หุ่นยนต์เข้าใกล้เสาโกดังมากเกินไป

---

### สัปดาห์ที่ 14: การวางแผนเส้นทาง, คอนโทรลเลอร์ และ AMCL Localization

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **AMCL (Adaptive Monte Carlo Localization):**
   - ใช้อัลกอริทึม Particle Filter กระจายอนุภาคจำลองตำแหน่งหุ่นยนต์นับพันจุด
   - คัดเลือกอนุภาคที่ข้อมูลสแกน LiDAR ตรงกับแผนที่มากที่สุด จนกระทั่งกลุ่มอนุภาคบีบตัวแน่น (Convergence)
2. **DWB Controller (Dynamic Window Approach):**
   - คำนวณความเร็วจำลอง $(v, \omega)$ หลายสิบเส้นทางล่วงหน้า และให้คะแนนความปลอดภัย ความเร็ว และความใกล้ชิดกับเส้นทางหลัก

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ขั้นตอนการทดลอง:**
  1. เปิดระบบนำทางเต็มรูปแบบ:
     ```bash
     ./docker/run_lab.sh ros2 launch amr_week14 nav2_bringup.launch.py   # เปิด amr_week11 gazebo_world.launch.py ไว้ก่อน
     ```
  2. ระบุพิกัดเริ่มต้นของหุ่นยนต์โดยอัตโนมัติ:
     ```bash
     ./docker/run_lab.sh ros2 run amr_week14 amcl_initial_pose
     ```
  3. สั่งเป้าหมายปลายทางผ่าน RViz2 ด้วยปุ่ม **2D Goal Pose**

---

### สัปดาห์ที่ 15: ระบบลาดตระเวนจุดตรวจอัตโนมัติ (Waypoint Patrol)

#### 📖 1. เนื้อหาบรรยายเชิงลึก (Lecture Notes)
1. **การควบคุมแบบ Headless ด้วย `BasicNavigator`:**
   - ใช้งานคลาส `BasicNavigator` จากโมดูล `nav2_simple_commander.robot_navigator`
   - ฟังก์ชันสำคัญ: `goToPose()`, `followWaypoints()`, `isTaskComplete()`, `getFeedback()`

#### 🛠️ 2. คู่มือปฏิบัติการ (Hands-on Lab)
- **ไฟล์โค้ด:** [`Essential_ROS/05_Nav2_Navigation/src/waypoint_patrol.py`](../Week_15_Waypoint_Patrol_BT/src/waypoint_patrol.py)
- **ขั้นตอนการทดลอง:**
  1. ขณะที่ระบบ Nav2 กำลังทำงาน ให้สั่งรันสคริปต์ลาดตระเวน 4 จุดตรวจรอบโกดัง:
     ```bash
     ./docker/run_lab.sh ros2 run amr_week15 waypoint_patrol
     ```
  2. สังเกตพฤติกรรมการเคลื่อนที่ผ่านแต่ละ Waypoint และการรายงานเปอร์เซ็นต์ความคืบหน้า

---

### สัปดาห์ที่ 16: สอบปฏิบัติการปลายภาค (Final AMR Demonstration)

#### 🏆 เกณฑ์การสอบปฏิบัติการปลายภาค (Final Demonstration)
1. **สถานการณ์ทดสอบ:**
   - กรรมการจะสุ่มพิกัดสินค้า (Pickup Point) และจุดรับสินค้า (Dropoff Point)
   - หุ่นยนต์ต้องเริ่มระบุตำแหน่งเริ่มต้นด้วยตนเองได้อย่างแม่นยำ
   - เดินทางไปถึงจุด Pickup ภายในเวลา 45 วินาที โดยไม่ชนสิ่งกีดขวาง
   - มีการวางสิ่งกีดขวางใหม่ขวางเส้นทางหลัก หุ่นยนต์ต้องวางแผนอ้อมทางใหม่ (Re-planning) สำเร็จ
   - นำส่งสินค้าถึงจุด Dropoff ด้วยความคลาดเคลื่อนเชิงตำแหน่งไม่เกิน 5 เซนติเมตร
2. **การสอบปากเปล่า:** อธิบายสถาปัตยกรรม TF Tree, การจัดการ QoS และการจูนพารามิเตอร์ Costmaps
