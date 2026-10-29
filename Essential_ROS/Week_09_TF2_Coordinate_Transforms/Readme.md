# 📖 Week 09: ระบบพิกัดสัมพัทธ์และการแปลงพิกัด (TF2 Transform System)
**เวลาเรียน:** บรรยาย 2 ชั่วโมง | ปฏิบัติการ 3 ชั่วโมง | ศึกษาค้นคว้าด้วยตนเอง 4 ชั่วโมง  
**วิชาบังคับก่อน:** [สัปดาห์ที่ 6: มาตรฐานวิศวกรรมพิกัด (REP 103/105) และจลนศาสตร์ AMR](../Week_06_Kinematics_REP_Standards/Readme.md)  
**เอกสารปฏิบัติการ:** [ใบงานแล็บสัปดาห์ที่ 9](Lab_Exercises.md)

---

## 🎯 วัตถุประสงค์การเรียนรู้ (Learning Objectives)
เมื่อจบบทเรียนนี้ ผู้เรียนจะสามารถ:
1. **พิสูจน์และคำนวณคณิตศาสตร์การแปลงพิกัด 3 มิติ** ด้วยเมทริกซ์การแปลงแบบเอกพันธุ์ขนาด $4 \times 4$ (Homogeneous Transformation Matrix) และพีชคณิตควอเทอร์เนียน (Quaternion Algebra)
2. **วิเคราะห์ความแตกต่างเชิงสถาปัตยกรรมและ QoS** ระหว่างทรานส์ฟอร์มแบบไดนามิกความถี่สูง (`/tf`) และทรานส์ฟอร์มแบบคงที่ (`/tf_static`)
3. **ประยุกต์ใช้กฎเหล็กของโครงสร้างต้นไม้พิกัด (TF Tree Constraints)**: กฎแม่ตัวเดียว (Single Parent Rule) และข้อห้ามการเกิดวงวนลูป (No-Cycle Constraint)
4. **พัฒนาโหนด StaticTransformBroadcaster** เพื่อเผยแพร่ออฟเซ็ตของเซนเซอร์ LiDAR, กล้อง RGB-D และแปลงเข้าสู่ Optical Frame ตามมาตรฐาน REP 103
5. **พัฒนาโหนด TF2 Buffer & TransformListener** เพื่อแปลงพิกัดจุดตรวจจับสิ่งกีดขวาง (Obstacle Point Transformation) ข้ามเวลา (Time Travel) พร้อมจัดการข้อผิดพลาดกลุ่ม TF Exceptions ได้อย่างสมบูรณ์

---

## ⏱️ แผนการสอน 2 ชั่วโมง (Lecture Outline)
| ช่วงเวลา | หัวข้อ | กิจกรรมการเรียนรู้ |
| :---: | :--- | :--- |
| **00:00 - 00:30** | พีชคณิตเชิงเส้น 3 มิติ: Homogeneous Matrices, Euler Angles vs Quaternions | พิสูจน์ปัญหา Gimbal Lock, เมทริกซ์ $4 \times 4$, การหมุนเวกเตอร์ด้วยควอเทอร์เนียน |
| **00:30 - 01:00** | สถาปัตยกรรม TF2 ใน ROS 2: Ring Buffer, Slerp และ Time Travel | วิเคราะห์หน่วยความจำบัฟเฟอร์ 10 วินาที, การทำ Interpolation พิกัดข้ามเสี้ยววินาที |
| **01:00 - 01:30** | กฎเหล็กของ TF Tree, สเปก REP 103 Optical Frame และ QoS `/tf_static` | ออกแบบ TF Tree สำหรับ Mobile Robot, คำนวณ Quaternion การแปลงกล้อง |
| **01:30 - 02:00** | Code Walkthrough: Broadcaster, Listener และเตรียมเข้าสู่ Lab | เจาะลึกโค้ด `static_sensor_broadcaster.py` และ `tf_obstacle_listener.py` พร้อม CLI |

---

## 🏛️ สถาปัตยกรรมระบบ (Architectural Deep Dive)

### 1. คณิตศาสตร์การแปลงพิกัดใน 3 มิติ (Homogeneous Transformations & Quaternions)

จุดพิกัดใน 3 มิติ $\mathbf{p}_A = [x_A, y_A, z_A]^T$ ที่สังเกตเห็นในระนาบพิกัด $A$ (เช่น ตัวเซนเซอร์กล้อง) สามารถแปลงไปยังระนาบพิกัด $B$ (เช่น โครงสร้างหลักหุ่นยนต์ `base_link`) ได้ผ่านเมทริกซ์การแปลงแบบโฮโมจีเนียสขนาด $4 \times 4$ ($\mathbf{T}_B^A$):

$$\begin{bmatrix} x_B \\ y_B \\ z_B \\ 1 \end{bmatrix} = \mathbf{T}_B^A \begin{bmatrix} x_A \\ y_A \\ z_A \\ 1 \end{bmatrix} = \begin{bmatrix} \mathbf{R}_{3\times3} & \mathbf{t}_{3\times1} \\ \mathbf{0}_{1\times3} & 1 \end{bmatrix} \begin{bmatrix} x_A \\ y_A \\ z_A \\ 1 \end{bmatrix}$$

โดยที่:
- $\mathbf{R}_{3\times3}$ คือ เมทริกซ์การหมุน (Special Orthogonal Group: $\text{SO}(3)$) ซึ่งมีคุณสมบัติ $\mathbf{R}^{-1} = \mathbf{R}^T$ และ $\det(\mathbf{R}) = +1$
- $\mathbf{t}_{3\times1} = [t_x, t_y, t_z]^T$ คือ เวกเตอร์ระยะขจัดหรือตำแหน่งเลื่อน (Translation Vector)
- เมทริกซ์ผกผัน (Inverse Transformation):
  $$\left(\mathbf{T}_B^A\right)^{-1} = \mathbf{T}_A^B = \begin{bmatrix} \mathbf{R}^T & -\mathbf{R}^T \mathbf{t} \\ \mathbf{0}^T & 1 \end{bmatrix}$$

#### พีชคณิตควอเทอร์เนียน (Unit Quaternion Algebra):
เพื่อขจัดปัญหา **Gimbal Lock** (การสูญเสียมิติอิสระเมื่อหมุน Pitch $=\pm 90^\circ$ ในระบบมุมออยเลอร์ Roll-Pitch-Yaw) ROS 2 ใช้ควอเทอร์เนียนหนึ่งหน่วย $\mathbf{q} = (x, y, z, w)$ ซึ่งนิยามบนพื้นผิวทรงกลม 4 มิติ ($S^3$):
$$x^2 + y^2 + z^2 + w^2 = 1.0$$

หากหมุนรอบแกนหนึ่งหน่วย $\mathbf{u} = (u_x, u_y, u_z)$ ด้วยมุม $\theta$:
$$\mathbf{q} = \left[ u_x \sin\left(\frac{\theta}{2}\right), \; u_y \sin\left(\frac{\theta}{2}\right), \; u_z \sin\left(\frac{\theta}{2}\right), \; \cos\left(\frac{\theta}{2}\right) \right]$$

การแปลงเวกเตอร์ตำแหน่ง $\mathbf{v}$ ผ่านการหมุนด้วยควอเทอร์เนียน:
$$\mathbf{v}' = \mathbf{q} \otimes \mathbf{v} \otimes \mathbf{q}^*$$
โดยที่ $\mathbf{q}^* = (-x, -y, -z, w)$ คือคอนจูเกตของควอเทอร์เนียน

---

### 2. สเปกระบบพิกัดของกล้อง (Camera Optical Frame Convention ตาม REP 103)
ในหุ่นยนต์ทั่วไป ระบบพิกัดตัวถังและเซนเซอร์ทั่วไปจะเป็นแบบ **Body Frame** (X หน้า, Y ซ้าย, Z บน) แต่ในระบบคอมพิวเตอร์วิทัศน์ (Computer Vision / OpenCV) มาตรฐานพิกัดภาพคือ **Optical Frame**:
- **แกน +Z:** ชี้พุ่งตรงไปข้างหน้าของเลนส์ (Depth Axis / View Direction)
- **แกน +X:** ชี้ไปทางขวาของภาพ (Image Width / Right)
- **แกน +Y:** ชี้ดิ่งลงด้านล่างของภาพ (Image Height / Down)

```mermaid
flowchart LR
    Body["camera_link<br/>(Body Convention)<br/>X: หน้า, Y: ซ้าย, Z: บน"]
    Optical["camera_optical_link<br/>(Optical Convention)<br/>Z: หน้า, X: ขวา, Y: ล่าง"]

    Body -->|"Roll = -90°, Pitch = 0°, Yaw = -90°"| Optical
```

การแปลงจาก `camera_link` สู่ `camera_optical_link` ต้องหมุนด้วยมุม Euler:
$$\text{Roll} = -90^\circ \left(-\frac{\pi}{2}\right), \quad \text{Pitch} = 0^\circ, \quad \text{Yaw} = -90^\circ \left(-\frac{\pi}{2}\right)$$
ซึ่งเทียบเท่ากับควอเทอร์เนียน:
$$\mathbf{q}_{\text{optical}} = [-0.5, 0.5, -0.5, 0.5]$$

---

### 3. สถาปัตยกรรม TF2 Ring Buffer และ Time Travel
ไลบรารี TF2 ใน ROS 2 ไม่ได้เป็นเพียงผู้กระจายข้อความ แต่เป็น **โครงสร้างข้อมูลแคชประวัติเชิงเวลา (Ring Buffer)** ที่เก็บรักษาข้อมูลพิกัดย้อนหลัง (โดยค่าเริ่มต้น 10 วินาที):

```mermaid
sequenceDiagram
    autonumber
    participant Sensor as กล้องตรวจจับสิ่งกีดขวาง (เวลา t = 100.25 s)
    participant Buffer as TF2 Buffer (เก็บแคชประวัติ t = 95.00 ถึง 105.00 s)
    participant Planner as Local Path Planner

    Sensor->>Planner: ส่งข้อมูล PointStamped ในเฟรม camera_link (ประทับเวลา t = 100.25 s)
    Planner->>Buffer: ขอ Transform: camera_link -> base_link ณ เวลา t = 100.25 s
    Note over Buffer: ทำ Slerp (Spherical Linear Interpolation) หาค่ามุมระหว่างสองจุดเวลาที่ใกล้เคียงที่สุด
    Buffer-->>Planner: ส่งค่า Transform ที่ถูกต้องตรงกับเสี้ยววินาทีที่กล้องถ่ายภาพจริง
    Note over Planner: แปลงจุดกีดขวางเข้าสู่ฐานหุ่นยนต์อย่างแม่นยำแม้หุ่นยนต์กำลังเคลื่อนที่
```

#### ทำไม Time Travel จึงจำเป็น?
หากหุ่นยนต์เคลื่อนที่ด้วยความเร็ว $1.5\text{ m/s}$ และการประมวลผลระบบจำแนกภาพ (Deep Learning) ใช้เวลาหน่วง $200\text{ ms}$:
- หากแปลงพิกัดโดยใช้พิกัดปัจจุบัน (Current Time): ตำแหน่งสิ่งกีดขวางจะคลาดเคลื่อนไป $1.5 \times 0.2 = \mathbf{0.30\text{ m}}$ (30 เซนติเมตร!) ซึ่งมากพอที่จะทำให้หุ่นยนต์ชนสิ่งกีดขวาง
- ด้วยระบบ **Time Travel**: TF2 จะดึงตำแหน่งของหุ่นยนต์ ณ เสี้ยววินาทีที่เซนเซอร์บันทึกภาพจริง ทำให้การแปลงพิกัดมีความแม่นยำระดับมิลลิเมตร

---

### 4. กฎเหล็กของ TF Tree (Coordinate Constraints)
1. **Single Parent Rule (กฎแม่ตัวเดียว):** ใน TF Tree ทุกๆ Coordinate Frame ต้องมี **Parent Frame ได้เพียงตัวเดียวเท่านั้น** (ห้ามมี 2 โหนดมาประกาศแย่งเป็น Parent ของ Frame เดียวกัน)
2. **No-Cycle Constraint (ห้ามเกิดวงรอบปิด):** ลำดับความสัมพันธ์ของพิกัดต้องเป็นแบบ **Directed Acyclic Graph (DAG)** ห้ามเกิดการวนลูป เช่น $A \rightarrow B \rightarrow C \rightarrow A$
3. **การแยกช่องสัญญาณความถี่สูงกับข้อมูลสถิต:**
   - **`/tf` (Dynamic Transforms):** สำหรับทรานส์ฟอร์มที่มีการเคลื่อนที่ต่อเนื่อง เช่น `odom` $\rightarrow$ `base_footprint` ส่งที่อัตรา 20–50 Hz
   - **`/tf_static` (Static Transforms):** สำหรับทรานส์ฟอร์มที่เชื่อมชิ้นส่วนคงที่ เช่น โครงสร้างหุ่นยนต์ไปยังเซนเซอร์ ส่งเพียงครั้งเดียวด้วย QoS `TRANSIENT_LOCAL` (Latching)

---

### 5. ข้อยกเว้นและข้อผิดพลาดในระบบ TF2 (TF Exceptions Handling)
เมื่อเรียกใช้ `tf_buffer.transform()` หรือ `tf_buffer.lookup_transform()` อาจเกิดข้อยกเว้น 3 ประเภทหลัก ซึ่งผู้พัฒนาต้องเขียนบล็อก `try-except` ดักจับเสมอ:

```mermaid
flowchart TD
    Lookup["คำขอดึงพิกัด (lookup_transform)"]
    
    Check1{"พบชื่อ Frame ใน Buffer หรือไม่?"}
    Check2{"มีเส้นทางเชื่อมโยง Parent-Child ถึงกันหรือไม่?"}
    Check3{"ประทับเวลา (Timestamp) อยู่ในช่วงแคช 10 วินาทีหรือไม่?"}
    
    Success["ได้ค่า Transform สำเร็จ"]
    E1["tf2_ros.LookupException<br/>(ไม่พบชื่อ Frame ในระบบ)"]
    E2["tf2_ros.ConnectivityException<br/>(ไม่มีกิ่งไม้เชื่อมต่อระหว่างสองเฟรม)"]
    E3["tf2_ros.ExtrapolationException<br/>(ร้องขอเวลาในอนาคตหรืออดีตที่หลุดแคช)"]

    Lookup --> Check1
    Check1 -- ไม่พบ --> E1
    Check1 -- พบ --> Check2
    Check2 -- ทรีขาดตอน --> E2
    Check2 -- ทรีเชื่อมสมบูรณ์ --> Check3
    Check3 -- นอกช่วงเวลา --> E3
    Check3 -- อยู่ในช่วงแคช --> Success

    style Success fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style E1 fill:#ffebee,stroke:#c62828,stroke-width:2px
    style E2 fill:#ffebee,stroke:#c62828,stroke-width:2px
    style E3 fill:#ffebee,stroke:#c62828,stroke-width:2px
```

---

## 🛠️ การวิเคราะห์โค้ดตัวอย่างในโมดูล (Code Walkthrough)

### 1. [`static_sensor_broadcaster.py`](src/static_sensor_broadcaster.py)
- **ตารางเฟรมเซนเซอร์ ([L22-L27](src/static_sensor_broadcaster.py#L22-L27)):** `SENSOR_FRAMES` เก็บ (parent, child, xyz, rpy) ของ `lidar_link`, `camera_link` และ `camera_optical_link` โดยใช้ **ตัวเลขเดียวกับ URDF ของสัปดาห์ที่ 7** ทุกประการ (มีเทสต์ `test_broadcaster_matches_week07_urdf` ตรวจ)
- **การใช้ `StaticTransformBroadcaster`:** ส่งข้อมูลเข้าสู่ `/tf_static` ด้วย QoS Transient Local (Latching) — ผู้ฟังที่เปิดทีหลังก็ยังได้รับ
- **การหมุน Optical Frame ตาม REP 103 ([L30-L41](src/static_sensor_broadcaster.py#L30-L41)):**
  ```python
  ('camera_link', 'camera_optical_link', (0.0, 0.0, 0.0), (-math.pi / 2, 0.0, -math.pi / 2)),
  q = euler_to_quaternion(-math.pi / 2, 0.0, -math.pi / 2)   # -> (-0.5, 0.5, -0.5, 0.5)
  ```
  หมุนแกนพิกัดเพื่อให้ระบบกล้องชี้แกน Z พุ่งไปข้างหน้าและแกน X ชี้ไปทางขวาตามมาตรฐานสากล (มีเทสต์ `test_rep103_optical_quaternion`)
- **การส่งข้อมูลรวมเป็นชุด ([L64](src/static_sensor_broadcaster.py#L64)):**
  เรียก `self._tf_publisher.sendTransform(transforms)` เพียงคำสั่งเดียวเพื่อบรอดแคสต์ทรานส์ฟอร์มทั้งหมดพร้อมกัน

> [!IMPORTANT]
> **แหล่งเดียวต่อหนึ่ง Transform (Single Source):** เฟรม `lidar_link`, `camera_link`, `camera_optical_link` มีอยู่แล้วใน `diff_drive_robot.urdf` ซึ่ง `robot_state_publisher` เผยแพร่ให้อัตโนมัติ ถ้าเปิดโหนดนี้ **พร้อมกับ** `robot_state_publisher` จะมีสองโหนดประกาศ Parent-Child คู่เดียวกัน ค่าที่อยู่ใน Buffer จะขึ้นกับว่าใครส่งมาทีหลัง และถ้าค่าไม่ตรงกันจะเกิดอาการกระพริบ/`TF_REPEATED_DATA`
> ในแล็บนี้จึงใช้ [`launch/tf_lab.launch.py`](launch/tf_lab.launch.py) ซึ่งเลือกเปิด **แหล่งเดียว**: `tf_source:=broadcaster` (โหนดนี้ — ใช้ตอนยังไม่มี URDF หรือสำหรับเซนเซอร์ที่ติดเพิ่มภายหลัง เช่น Sonar ใน Lab 9.4) หรือ `tf_source:=urdf` (`robot_state_publisher` จากแพ็กเกจ `amr_week07`) — ทั้งสองแบบให้ผล $(1.40, 0.30)$ เหมือนกัน และโหนด Broadcaster จะพิมพ์ ERROR เตือนถ้าตรวจพบ `/robot_description` (มี `robot_state_publisher` รันอยู่)

- **การปิดโหนดอย่างถูกต้อง ([L80-L94](src/static_sensor_broadcaster.py#L80-L94)):** ใน Jazzy, rclpy ติดตั้ง Signal Handler ทั้ง SIGINT และ SIGTERM ซึ่งจะ `shutdown` context ให้เองแล้วโยน `KeyboardInterrupt` หรือ `ExternalShutdownException` ออกจาก `rclpy.spin()` โค้ดเดิมเรียก `rclpy.shutdown()` ซ้ำใน `finally` จึงเกิด `RCLError: rcl_shutdown already called` ทุกครั้งที่ถูก `docker stop`/`kill` โค้ดใหม่จับทั้งสอง Exception และใช้ `rclpy.try_shutdown()` (เทสต์ `test_shutdown_signals.py` ส่ง SIGTERM/SIGINT จริงและตรวจว่า exit code = 0 ไม่มี Traceback)

---

### 2. [`tf_obstacle_listener.py`](src/tf_obstacle_listener.py)
- **การสร้าง TF Buffer และ TransformListener ([L28-L31](src/tf_obstacle_listener.py#L28-L31)):**
  ```python
  self.tf_buffer = tf2_ros.Buffer()
  self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
  ```
  `TransformListener` สร้าง Subscription ของ `/tf` และ `/tf_static` (`/tf_static` ใช้ QoS Transient Local) **บนโหนดที่ส่งเข้าไป** แล้วนำข้อความไปอัปเดตลงใน Buffer
  ใน ROS 2 Jazzy ลายเซ็นคือ `TransformListener(buffer, node, *, spin_thread=False, qos=None, static_qos=None)` — ค่าเริ่มต้น **ไม่สร้างเธรดเบื้องหลัง** Subscription ทั้งสองจึงถูกประมวลผลโดย Executor ที่ spin โหนดนี้อยู่ (`rclpy.spin(node)` ใน `main()`) ถ้าโหนดไม่ถูก spin Buffer จะว่างตลอด หากต้องการเธรดแยก (เช่น เรียก `lookup_transform` แบบรอใน callback) ให้ส่ง `spin_thread=True` หรือใช้ `MultiThreadedExecutor`
- **การแปลงพิกัดจุดสิ่งกีดขวาง ([L39-L52](src/tf_obstacle_listener.py#L39-L52)):**
  ```python
  pt_in_camera.header.stamp = Time().to_msg()   # time 0 = transform ล่าสุด
  pt_in_base = self.tf_buffer.transform(pt_in_camera, TARGET_FRAME)
  ```
  แปลงพิกัดวัตถุ $(1.2, 0.3, 0.0)$ จากระนาบกล้องเข้าสู่ระนาบฐานหุ่นยนต์ได้ $(1.40, 0.30, 0.02)$ เพราะ `camera_link` อยู่หน้า `base_link` $0.20$ m และสูง $0.02$ m (ไม่มีการหมุน) — ไม่ใส่ `timeout` เพราะการรอใน Timer callback ของ Executor เธรดเดียวจะบล็อกไม่ให้ Subscription ของ TF ทำงาน จึงใช้วิธีลองใหม่ทุก 0.5 s และดักจับ `LookupException` / `ConnectivityException` / `ExtrapolationException` แทน

---

### 3. แพ็กเกจ `amr_week09` และการ Build
```bash
./docker/run_lab.sh bash
colcon build --base-paths Essential_ROS --packages-up-to amr_week09     # รวม amr_week07 (URDF)
source install/setup.bash
ros2 run amr_week09 static_sensor_broadcaster
ros2 run amr_week09 tf_obstacle_listener
ros2 launch amr_week09 tf_lab.launch.py tf_source:=broadcaster   # หรือ tf_source:=urdf
colcon test --base-paths Essential_ROS --packages-select amr_week09 && colcon test-result --verbose
```
ยังรันแบบสคริปต์ได้เช่นเดิม: `python3 Essential_ROS/Week_09_TF2_Coordinate_Transforms/src/static_sensor_broadcaster.py`

---

## ⌨️ ตารางคำสั่ง CLI สำคัญ
| คำสั่ง | คำอธิบาย | ตัวอย่างการใช้งาน |
| :--- | :--- | :--- |
| `ros2 run tf2_ros tf2_echo <parent> <child>` | พิมพ์ค่า Translation และ Rotation ระหว่าง 2 เฟรมแบบสดๆ | `ros2 run tf2_ros tf2_echo base_link lidar_link` |
| `ros2 run tf2_tools view_frames` | ฟัง TF 5 วินาทีแล้วสร้างไฟล์ `frames_<วันเวลา>.pdf` และ `.gv` (Graphviz) สรุปโครงสร้าง TF Tree | `ros2 run tf2_tools view_frames` แล้ว `dot -Tpng frames_*.gv -o tf_tree.png` |
| `ros2 run tf2_ros tf2_monitor` | มอนิเตอร์ความถี่และอัตรา Latency ของทุกกิ่งก้านใน TF Tree | `ros2 run tf2_ros tf2_monitor` |
| `ros2 topic echo --qos-durability transient_local /tf_static` | ดักฟังข้อความทรานส์ฟอร์มคงที่ (ตรวจสอบ Latching) | `ros2 topic echo --qos-durability transient_local /tf_static` |
| `ros2 run tf2_ros static_transform_publisher ...` | บรอดแคสต์ Static Transform ชั่วคราวผ่านบรรทัดคำสั่ง CLI | `ros2 run tf2_ros static_transform_publisher --x 0.1 --y 0 --z 0.2 --frame-id base_link --child-frame-id camera_link` |

---

## 📟 ผลการรันจริง (Real Run Output)
บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29

ไฟล์ฉบับเต็ม: [`results/tf_lab_broadcaster.txt`](results/tf_lab_broadcaster.txt), [`results/tf_lab_urdf.txt`](results/tf_lab_urdf.txt), [`results/sigterm_shutdown.txt`](results/sigterm_shutdown.txt), [`results/view_frames.gv`](results/view_frames.gv), [`results/colcon_test.txt`](results/colcon_test.txt)

```console
$ ros2 launch amr_week09 tf_lab.launch.py tf_source:=broadcaster
...
[static_sensor_broadcaster-1] [INFO] [1793243288.280573459] [static_sensor_broadcaster]: Published static transforms: base_link->lidar_link, base_link->camera_link, camera_link->camera_optical_link
[tf_obstacle_listener-2] [INFO] [1793243288.281510631] [tf_obstacle_listener]: Listening for transforms and converting obstacle poses...
[tf_obstacle_listener-2] [INFO] [1793243288.768318273] [tf_obstacle_listener]: Obstacle transformed from camera_link to base_link: X=1.40m, Y=0.30m, Z=0.02m
...
$ ros2 run tf2_ros tf2_echo base_link lidar_link
At time 0.0
- Translation: [0.080, 0.000, 0.095]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
...
$ ros2 run tf2_ros tf2_echo camera_link camera_optical_link
At time 0.0
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [-0.500, 0.500, -0.500, 0.500]
...
[INFO] [tf_obstacle_listener-2]: process has finished cleanly [pid 49]
[INFO] [static_sensor_broadcaster-1]: process has finished cleanly [pid 48]
```

เมื่อใช้ URDF เป็นแหล่ง TF แทน (`tf_source:=urdf`) ได้ผลเดียวกัน `X=1.40m, Y=0.30m, Z=0.02m` และการส่ง SIGTERM/SIGINT ให้ทั้งสองโหนดได้ `exit code: 0` โดยไม่มี Traceback (ดู [`results/sigterm_shutdown.txt`](results/sigterm_shutdown.txt))
*(หมายเหตุ: ตอนปิด launch ในโหมด `urdf` โหนด `joint_state_publisher` ของ ROS 2 Jazzy เองยังพิมพ์ `KeyboardInterrupt` Traceback เมื่อได้ SIGINT ซ้ำสองครั้ง — เป็นพฤติกรรมของแพ็กเกจต้นทาง ไม่ใช่โค้ดในแล็บนี้)*

![TF Tree จาก view_frames](images/view_frames_tf_tree.png)

*ภาพ TF Tree จริง: รัน `ros2 launch amr_week09 tf_lab.launch.py tf_source:=urdf` แล้ว `ros2 run tf2_tools view_frames` (ฟัง 5 วินาที) จากนั้นแปลงไฟล์ `frames_2026-10-29_03.08.35.gv` ที่ view_frames สร้างคู่กับ PDF เป็น PNG ด้วย `dot -Tpng -Gdpi=110` (ImageMagick ใน image `ros:lab-runner` ไม่มี Ghostscript จึงแปลง PDF โดยตรงไม่ได้) — ลิงก์ล้อมาจาก `/tf` (~10 Hz จาก `joint_state_publisher`) ส่วนลิงก์อื่นมาจาก `/tf_static` (แสดง rate 10000 / เวลา 0.0)*

---

## ⚠️ ปัญหาที่พบบ่อยและการแก้ไข (Troubleshooting)

| ที่ | อาการที่พบ (Symptom) | สาเหตุรากเหง้า (Root Cause) | แนวทางแก้ไข (Resolution) |
|:---:| :--- | :--- | :--- |
| 1 | **`ExtrapolationException: Lookup would require extrapolation into the future`** | เวลาบนเซิร์ฟเวอร์หรือสองโหนดเหลื่อมล้ำกัน หรือข้อมูล TF ยังเดินทางมาไม่ถึง | กำหนด `timeout=Duration(seconds=0.2)` ในคำสั่ง lookup เพื่อให้บัฟเฟอร์รอ หรือใช้ `Time()` (เวลาล่าสุด) |
| 2 | **`ConnectivityException: Could not find a connection between 'odom' and 'camera_link'`** | TF Tree ขาดช่วง (Broken Tree) เนื่องจากขาดข้อต่อเชื่อมโยงระหว่างสองกิ่ง (เช่น ขาด `base_link`) | รัน `view_frames` เพื่อตรวจสอบหากิ่งไม้ที่ขาดหายไป แล้วเปิดโหนดเชื่อมทรานส์ฟอร์มนั้น |
| 3 | **`LookupException: "camera_link" passed to lookupTransform does not exist`** | โหนด Broadcaster ยังไม่ได้เปิดทำงาน หรือพิมพ์ชื่อ Frame สลับตัวพิมพ์เล็ก-ใหญ่ | ตรวจสอบชื่อ Frame ในโหนดต้นทาง และรัน Broadcaster ให้เรียบร้อย |
| 4 | **ภาพวัตถุใน RViz2 คว่ำหน้าลงพื้นหรือเอียง 90 องศา** | ไม่ได้หมุนแปลงพิกัดเข้าสู่ Optical Frame ตามมาตรฐาน REP 103 | เพิ่ม Static Transform แปลง `camera_link` สู่ `camera_optical_link` ด้วย Roll $-90^\circ$ และ Yaw $-90^\circ$ |
| 5 | **เครือข่าย Wi-Fi ถูกกินแบนด์วิดท์มหาศาลจาก TF** | ส่งพิกัดตำแหน่งเซนเซอร์ที่ตรึงแน่นผ่านท็อปปิก `/tf` ความถี่สูง แทนที่จะส่งเข้า `/tf_static` | เปลี่ยนมาใช้ `StaticTransformBroadcaster` สำหรับเซนเซอร์ทุกตัวที่ไม่มีการขยับ |
| 6 | **เกิดการกระตุกหรือ Error `TF_REPEATED_DATA` ใน Terminal** | มีโหนดมากกว่าหนึ่งตัวพยายามบรอดแคสต์ Parent-Child คู่เดียวกันด้วยค่าต่างกัน (เช่น เปิด `static_sensor_broadcaster` พร้อม `robot_state_publisher`) | ตรวจสอบให้แน่ใจว่าแต่ละ Transform มีผู้ส่งเพียงโหนดเดียว: `ros2 topic info /tf_static --verbose` แล้วใช้ `tf_lab.launch.py tf_source:=...` |
| 7 | **ปิดโหนดด้วย `docker stop` / `kill` แล้วขึ้น `RCLError: rcl_shutdown already called`** | เรียก `rclpy.shutdown()` ซ้ำหลังจาก Signal Handler ของ rclpy ปิด context ไปแล้ว | จับ `ExternalShutdownException` และใช้ `rclpy.try_shutdown()` แทน |

---

## 📝 แบบทดสอบท้ายบท (Self-Assessment Quiz)

1. **คำถาม:** สภาวะ Gimbal Lock ในการแสดงมุมหมุน 3 มิติคืออะไร และเกิดขึ้นในระบบพิกัดแบบใด?
2. **คำถาม:** ในระบบควอเทอร์เนียนหนึ่งหน่วย $\mathbf{q} = (x, y, z, w)$ เงื่อนไขทางคณิตศาสตร์ใดที่ทำให้มั่นใจว่าเป็นการหมุนที่รักษาระยะทาง (Rigid Body Rotation)?
3. **คำถาม:** จงอธิบายความแตกต่างของทิศทางแกนพิกัดระหว่าง Camera Body Frame กับ Camera Optical Frame ตามมาตรฐาน REP 103?
4. **คำถาม:** เหตุใดทรานส์ฟอร์มระหว่าง `base_link` ไปยัง `lidar_link` จึงควรเผยแพร่ผ่าน `/tf_static` แทนที่จะเป็น `/tf`?
5. **คำถาม:** ในโครงสร้างต้นไม้พิกัด (TF Tree) กฎข้อใดที่ป้องกันไม่ให้เกิดความสับสนในการหาเส้นทางย้อนกลับระหว่างสองเฟรม?
6. **คำถาม:** หากหุ่นยนต์เคลื่อนที่ด้วยความเร็ว $1.0\text{ m/s}$ และระบบตรวจจับภาพใช้เวลาประมวลผล $100\text{ ms}$ การใช้ระบบ Time Travel ของ TF2 มีประโยชน์อย่างไรต่อความแม่นยำของตำแหน่งสิ่งกีดขวาง?
7. **คำถาม:** ข้อยกเว้น `tf2_ros.ExtrapolationException` มีสาเหตุการเกิดมาจากอะไร?
8. **คำถาม:** คำสั่ง CLI ใดที่ใช้สร้างแผนผังไดอะแกรมความสัมพันธ์ของทุก Frame ในระบบออกมาเป็นไฟล์กราฟิก PDF?
9. **คำถาม:** หากต้องการแปลงจุดพิกัดในภาษา Python เหตุใดจึงต้องใช้ข้อความประเภท `PointStamped` แทนการใช้ `Point` ธรรมดา?
10. **คำถาม:** ขนาดเมทริกซ์การแปลงแบบเอกพันธุ์ (Homogeneous Transformation Matrix) ที่ใช้ในระบบพิกัด 3 มิติมีมิติเท่าใด และประกอบด้วยองค์ประกอบย่อยใดบ้าง?

<details>
<summary>🔍 ดูเฉลยคำตอบพร้อมคำอธิบายอย่างละเอียด</summary>

1. **ตอบ:** **Gimbal Lock** คือสภาวะที่แกนหมุน 2 แกนในระบบมุมออยเลอร์ (Roll-Pitch-Yaw) เกิดการหมุนมาซ้อนทับกัน (โดยทั่วไปเกิดขึ้นเมื่อมุม Pitch เอียงเท่ากับ $+90^\circ$ หรือ $-90^\circ$) ส่งผลให้ระบบสูญเสียองศาอิสระในการหมุนไป 1 แกน และไม่สามารถแยกแยะการหมุนระหว่าง Roll และ Yaw ได้
2. **ตอบ:** ผลรวมกำลังสองของส่วนประกอบทั้งสี่จะต้องเท่ากับหนึ่งเสมอ: $\mathbf{x^2 + y^2 + z^2 + w^2 = 1.0}$ (Unit Quaternion)
3. **ตอบ:**
   - **Camera Body Frame:** X ชี้ไปข้างหน้า, Y ชี้ไปทางซ้าย, Z ชี้ขึ้นบน
   - **Camera Optical Frame:** Z ชี้พุ่งไปข้างหน้า (ความลึก), X ชี้ไปทางขวาของภาพ, Y ชี้ดิ่งลงด้านล่างของภาพ
4. **ตอบ:** เนื่องจากเซนเซอร์ LiDAR ถูกยึดติดแน่นทางกายภาพกับโครงสร้างตัวถังหุ่นยนต์ ตำแหน่งและมุมเอียงสัมพัทธ์จึงไม่มีการเปลี่ยนแปลงตามเวลา การส่งเข้า `/tf_static` เพียงครั้งเดียวด้วย QoS `TRANSIENT_LOCAL` ช่วยลดภาระ CPU และแบนด์วิดท์เครือข่ายได้อย่างมหาศาลเมื่อเทียบกับการส่งซ้ำๆ ที่ความถี่ 50 Hz ใน `/tf`
5. **ตอบ:** **Single Parent Rule (กฎแม่ตัวเดียว)** ทุกๆ Frame ต้องมี Parent ได้เพียงตัวเดียวเท่านั้น ทำให้การค้นหาเส้นทางย้อนกลับ (Path Traversal) จาก Child ขึ้นสู่บรรพบุรุษร่วมเป็นเส้นทางตรงที่ชัดเจนเพียงเส้นทางเดียวเสมอ
6. **ตอบ:** Time Travel ช่วยให้ระบบสามารถดึงข้อมูลพิกัดของหุ่นยนต์ **ณ เสี้ยววินาทีที่กล้องถ่ายภาพจริง (ย้อนหลัง 100 ms)** มาใช้ในการแปลงพิกัด ทำให้ขจัดความคลาดเคลื่อนเชิงตำแหน่งขนาด $1.0\text{ m/s} \times 0.1\text{ s} = \mathbf{0.10\text{ m}}$ (10 เซนติเมตร) ออกไปได้อย่างสมบูรณ์
7. **ตอบ:** เกิดจากการที่ผู้เรียก lookup ข้อมูลพิกัด ณ ช่วงเวลาที่อยู่นอกเหนือจากประวัติที่แคชไว้ใน Buffer (เช่น ร้องขอเวลาในอนาคตที่ยังมาไม่ถึง หรือร้องขอเวลาย้อนหลังเกินขีดจำกัดของบัฟเฟอร์ 10 วินาที)
8. **ตอบ:** คำสั่ง **`ros2 run tf2_tools view_frames`** ซึ่งจะสร้างไฟล์ `frames.pdf` ขึ้นมาแสดงความสัมพันธ์และอัตราความถี่ของทุก Frame
9. **ตอบ:** เนื่องจาก `PointStamped` มีส่วนหัวข้อความ (**`std_msgs/Header`**) ซึ่งระบุทั้งชื่อเฟรมพิกัดตั้งต้น (`frame_id`) และเวลาที่เกิดจุดนั้น (`stamp`) ทำให้ TF Buffer ทราบว่าต้องแปลงจากจุดอ้างอิงใดและ ณ เสี้ยววินาทีใด ในขณะที่ `Point` ธรรมดามีเพียงตัวเลข $(x, y, z)$ ลอยๆ โดยไม่มีบริบททางพิกัดและเวลา
10. **ตอบ:** มีขนาด **$4 \times 4$** ประกอบด้วย:
    - เมทริกซ์การหมุนขนาด $3 \times 3$ ($\mathbf{R}$)
    - เวกเตอร์การเลื่อนตำแหน่งขนาด $3 \times 1$ ($\mathbf{t}$)
    - เวกเตอร์แถวล่างขนาด $1 \times 4$ คือ $[0, 0, 0, 1]$
</details>

---

## 📚 แหล่งอ้างอิงและศึกษาเพิ่มเติม
- [About TF2 and Time Travel (ROS 2 Docs)](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Tf2.html)
- [REP 103: Standard Units of Measure & Coordinate Conventions](https://www.ros.org/reps/rep-0103.html)
- [Writing a TF2 Static Broadcaster (Python)](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Tf2/Writing-A-Tf2-Static-Broadcaster-Py.html)
- [Writing a TF2 Listener (Python)](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Tf2/Writing-A-Tf2-Listener-Py.html)
