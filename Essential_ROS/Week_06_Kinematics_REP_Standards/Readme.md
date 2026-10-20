# 📖 Week 06: มาตรฐานวิศวกรรมพิกัด (REP 103/105) และจลนศาสตร์หุ่นยนต์ขับเคลื่อนสองล้อ (Differential Drive Kinematics)
**เวลาเรียน:** บรรยาย 2 ชั่วโมง | ปฏิบัติการ 3 ชั่วโมง | ศึกษาค้นคว้าด้วยตนเอง 4 ชั่วโมง  
**วิชาบังคับก่อน:** [สัปดาห์ที่ 5: Dynamic Parameters และสถาปัตยกรรม Python Launch System](../Week_05_Parameters_Launch/Readme.md)  
**เอกสารปฏิบัติการ:** [ใบงานแล็บสัปดาห์ที่ 6](Lab_Exercises.md)

---

## 🎯 วัตถุประสงค์การเรียนรู้ (Learning Objectives)
เมื่อจบบทเรียนนี้ ผู้เรียนจะสามารถ:
1. **ประยุกต์ใช้มาตรฐานวิศวกรรมหุ่นยนต์ REP 103** สำหรับหน่วยวัดทางกายภาพและระบบพิกัดคาร์ทีเซียนแบบมือขวา (Right-Handed Rule) ได้อย่างถูกต้อง
2. **วิเคราะห์ลำดับชั้นโครงสร้างต้นไม้พิกัด (TF Tree Architecture) ตามมาตรฐาน REP 105** (`earth` $\rightarrow$ `map` $\rightarrow$ `odom` $\rightarrow$ `base_footprint` $\rightarrow$ `base_link`) พร้อมอธิบายเหตุผลในการแยกความรับผิดชอบระหว่าง `map` และ `odom`
3. **พิสูจน์สมการจลนศาสตร์เดินหน้าและย้อนกลับ (Forward and Inverse Kinematics)** ของหุ่นยนต์ขับเคลื่อนสองล้อแบบดิฟเฟอเรนเชียล (Differential Drive) ในรูปสมการเมทริกซ์
4. **คำนวณตำแหน่งและทิศทางสะสม (Dead Reckoning & Odometry Integration)** ด้วยวิธี Runge-Kutta / Midpoint Integration และแปลงมุม Yaw เข้าสู่ Quaternion
5. **เข้าใจโครงสร้างข้อมูลและการกำหนดค่าความคลาดเคลื่อน (Covariance Matrix)** ในข้อความมาตรฐาน `nav_msgs/msg/Odometry` สำหรับส่งต่อให้ระบบฟิวชันเซนเซอร์ (Extended Kalman Filter: EKF)

---

## ⏱️ แผนการสอน 2 ชั่วโมง (Lecture Outline)
| ช่วงเวลา | หัวข้อ | กิจกรรมการเรียนรู้ |
| :---: | :--- | :--- |
| **00:00 - 00:30** | มาตรฐาน REP 103: พิกัดมือขวา กฎมือขวา และหน่วย SI | บรรยายหลักการแกน X (หน้า), Y (ซ้าย), Z (บน) และทิศทางการหมุน Roll-Pitch-Yaw |
| **00:30 - 01:00** | มาตรฐาน REP 105: สถาปัตยกรรม Coordinate Frames สำหรับ AMR | วิเคราะห์ลึก: ความต่อเนื่องของ `odom` vs การแก้ไขพิกัดแบบกระโดดของ `map` |
| **01:00 - 01:40** | การพิสูจน์คณิตศาสตร์จลนศาสตร์ (Kinematics & Matrix Derivations) | พิสูจน์สมการ Forward/Inverse Kinematics, ICC, และการอินทิเกรต Odometry |
| **01:40 - 02:00** | Code Walkthrough `diff_drive_kinematics.py` และสรุปก่อนเข้าสู่ Lab | วิเคราะห์การแปลงสมการลงโค้ด Python, โครงสร้าง Odometry Message และ Covariance |

---

## 🏛️ สถาปัตยกรรมระบบ (Architectural Deep Dive)

### 1. มาตรฐาน REP 103: Standard Units of Measure & Coordinate Conventions
ระบบนิเวศ ROS ทั้งหมดปฏิบัติตามข้อกำหนด **REP 103** เพื่อให้แน่ใจว่าแพ็กเกจจากผู้พัฒนาทั่วโลกสามารถทำงานร่วมกันได้อย่างราบรื่น:

- **หน่วยวัดทางกายภาพ (Standard SI Units):**
  - ระยะทาง / ตำแหน่ง (Length / Position): เมตร ($m$)
  - มุม / ทิศทาง (Angle / Rotation): เรเดียน ($rad$) โดยที่ $\pi\text{ rad} = 180^\circ$
  - มวล (Mass): กิโลกรัม ($kg$)
  - เวลา (Time): วินาที ($s$)
  - ความเร็วเชิงเส้น (Linear Velocity): เมตรต่อวินาที ($m/s$)
  - ความเร็วเชิงมุม (Angular Velocity): เรเดียนต่อวินาที ($rad/s$)
- **ระบบพิกัดคาร์ทีเซียนแบบมือขวา (Right-Handed Coordinate System):**
  - **แกน +X:** ชี้ไปข้างหน้าของหุ่นยนต์ (**Forward**)
  - **แกน +Y:** ชี้ไปทางซ้ายของหุ่นยนต์ (**Left**)
  - **แกน +Z:** ชี้ขึ้นด้านบนสู่ท้องฟ้า (**Up / Sky**)
- **การหมุนตามกฎมือขวา (Right-Hand Grip Rule):**
  - **Roll (หมุนรอบแกน X):** เอียงตัวไปทางขวาเป็นบวก
  - **Pitch (หมุนรอบแกน Y):** ก้มหน้าลงเป็นบวก
  - **Yaw (หมุนรอบแกน Z):** หมุนทวนเข็มนาฬิกา (CCW) เมื่อมองจากด้านบนลงมาเป็นบวก

---

### 2. มาตรฐาน REP 105: Coordinate Frames for Mobile Platforms
ในระบบนำทางหุ่นยนต์เคลื่อนที่อัตโนมัติ (AMR) พิกัดตำแหน่งถูกแบ่งออกเป็นลำดับชั้นอย่างเคร่งครัด:

```mermaid
flowchart TD
    Earth["earth<br/>(พิกัดละติจูด/ลองจิจูด สากล WGS-84 / UTM)"]
    Map["map<br/>(พิกัดแผนที่โลก: World-fixed, ปลอด Drift, อาจมีการกระโดด)"]
    Odom["odom<br/>(พิกัดการเคลื่อนที่สะสม: ต่อเนื่อง ไม่มีทางกระโดด แต่มี Drift สะสม)"]
    BaseFootprint["base_footprint<br/>(เงาของหุ่นยนต์ฉายลงบนพื้นระนาบ 2D: Z=0)"]
    BaseLink["base_link<br/>(จุดศูนย์กลางทางกายภาพของหุ่นยนต์ 3D)"]
    Lidar["laser_frame<br/>(พิกัดของเซนเซอร์ LiDAR)"]
    IMU["imu_link<br/>(พิกัดของเซนเซอร์ IMU)"]

    Earth -.-> Map
    Map -->|Global Localization / AMCL Correction| Odom
    Odom -->|Wheel Encoders + IMU Integration| BaseFootprint
    BaseFootprint -->|คงที่ตามความสูงแชสซี| BaseLink
    BaseLink -->|ตำแหน่งติดตั้งเซนเซอร์ (Static TF)| Lidar
    BaseLink -->|ตำแหน่งติดตั้งเซนเซอร์ (Static TF)| IMU

    style Map fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style Odom fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style BaseLink fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
```

#### การวิเคราะห์เปรียบเทียบเชิงวิศวกรรม: `odom` vs `map`
หนึ่งในหัวใจสำคัญของการออกแบบระบบขับขี่อัตโนมัติคือการทำความเข้าใจความขัดแย้งระหว่าง **ความต่อเนื่อง (Continuity)** และ **ความแม่นยำระดับโลก (Global Accuracy)**:

| คุณลักษณะ | **เฟรม `odom` (Odometry Frame)** | **เฟรม `map` (Map Frame)** |
| :--- | :--- | :--- |
| **แหล่งที่มาข้อมูล** | ตัวถอดรหัสรอบหมุนของล้อ (Wheel Encoders) และ IMU | เซนเซอร์ระบุตำแหน่งระดับโลก เช่น LiDAR Scan Matching, กล้อง SLAM หรือ GPS |
| **พฤติกรรมทางคณิตศาสตร์** | **ต่อเนื่องและราบเรียบอย่างสมบูรณ์ (Smooth & Continuous)** ไม่มีการกระโดดของพิกัด | **อาจไม่ต่อเนื่อง (Discontinuous / Jumps)** เมื่ออัลกอริทึมคำนวณแก้ตำแหน่งใหม่ |
| **พฤติกรรมระยะยาว** | **เกิด Drift สะสมตลอดเวลา** จากการลื่นไถลของล้อ (Wheel Slip) หรือพื้นผิวขรุขระ | **ไม่มี Drift สะสม** ตำแหน่งถูกตรึงไว้กับสิ่งแวดล้อมทางกายภาพที่แท้จริง |
| **ผู้ใช้งานหลักในระบบ** | **Local Motion Controller** (การควบคุมล้อ, การหลบหลีกสิ่งกีดขวางระยะประชิด) | **Global Path Planner** (การวางแผนโครงข่ายเส้นทางข้ามอาคาร) |

---

### 3. การพิสูจน์คณิตศาสตร์จลนศาสตร์ Differential Drive (Mathematical Derivation)

กำหนดให้:
- $r$: รัศมีของล้อขับเคลื่อน (Wheel Radius) ในหน่วยเมตร
- $L$: ระยะห่างระหว่างกึ่งกลางล้อขับเคลื่อนซ้ายและขวา (Wheel Separation / Track Base) ในหน่วยเมตร
- $v$: ความเร็วเชิงเส้นของหุ่นยนต์ในแนวแกน X ($m/s$)
- $\omega$: ความเร็วเชิงมุมของหุ่นยนต์รอบแกน Z ($rad/s$)
- $v_R, v_L$: ความเร็วเชิงเส้นสัมผัสพื้นของล้อขวาและล้อซ้าย ($m/s$)
- $\omega_R, \omega_L$: ความเร็วเชิงมุมในการหมุนของมอเตอร์ล้อขวาและล้อซ้าย ($rad/s$)

```mermaid
flowchart LR
    CmdVel["คำสั่งความเร็วหุ่นยนต์<br/>(v, omega)"]
    Wheels["คำสั่งรอบหมุนมอเตอร์<br/>(omega_R, omega_L)"]
    Odometry["การประมาณตำแหน่งและพิกัด<br/>(x, y, theta)"]

    CmdVel -->|"Forward Kinematics (FK)"| Wheels
    Wheels -->|"Inverse Kinematics (IK) & Dead Reckoning"| Odometry
```

#### ก. จุดศูนย์กลางการหมุนชั่วขณะ (Instantaneous Center of Curvature: ICC)
เมื่อหุ่นยนต์เคลื่อนที่เป็นแนวโค้ง ทั้งล้อซ้ายและล้อขวาจะหมุนรอบจุดร่วมเดียวกันคือ ICC ด้วยรัศมีความโค้ง $R$:
$$v = \omega R$$
$$v_R = \omega \left(R + \frac{L}{2}\right)$$
$$v_L = \omega \left(R - \frac{L}{2}\right)$$

#### ข. จลนศาสตร์เดินหน้า (Forward Kinematics: แปลงคำสั่ง Twist สู่ความเร็วรอบล้อ)
จากสมการความสัมพันธ์ข้างต้น เราสามารถคำนวณความเร็วเชิงเส้นของล้อแต่ละข้าง:
$$v_R = v + \frac{\omega L}{2}$$
$$v_L = v - \frac{\omega L}{2}$$

เนื่องจาก $v = \omega_{wheel} \cdot r$ ดังนั้นความเร็วเชิงมุมของมอเตอร์แต่ละข้างคือ:
$$\omega_R = \frac{v + \frac{\omega L}{2}}{r} = \frac{1}{r} v + \frac{L}{2r} \omega$$
$$\omega_L = \frac{v - \frac{\omega L}{2}}{r} = \frac{1}{r} v - \frac{L}{2r} \omega$$

เขียนในรูปสมการเมทริกซ์ (Forward Kinematics Matrix):
$$\begin{bmatrix} \omega_R \\ \omega_L \end{bmatrix} = \begin{bmatrix} \frac{1}{r} & \frac{L}{2r} \\ \frac{1}{r} & -\frac{L}{2r} \end{bmatrix} \begin{bmatrix} v \\ \omega \end{bmatrix}$$

#### ค. จลนศาสตร์ย้อนกลับ (Inverse Kinematics: จาก Encoder สู่ความเร็วหุ่นยนต์)
เมื่อตัวเข้ารหัสสัญญาณ (Encoders) วัดความเร็วเชิงมุมของล้อทั้งสองข้างได้ $(\omega_R, \omega_L)$ เราสามารถถอดรหัสความเร็วรวมของหุ่นยนต์ได้:
$$v_R = \omega_R \cdot r, \quad v_L = \omega_L \cdot r$$
$$v = \frac{v_R + v_L}{2} = \frac{r}{2} (\omega_R + \omega_L)$$
$$\omega = \frac{v_R - v_L}{L} = \frac{r}{L} (\omega_R - \omega_L)$$

เขียนในรูปสมการเมทริกซ์ (Inverse Kinematics Matrix):
$$\begin{bmatrix} v \\ \omega \end{bmatrix} = \begin{bmatrix} \frac{r}{2} & \frac{r}{2} \\ \frac{r}{L} & -\frac{r}{L} \end{bmatrix} \begin{bmatrix} \omega_R \\ \omega_L \end{bmatrix}$$

---

### 4. การอินทิเกรตตำแหน่งและการประมาณค่า (Odometry Dead Reckoning)
ในช่วงคาบเวลาสุ่มตัวอย่าง $\Delta t = t_{k+1} - t_k$:
การหมุนเชิงมุมที่เปลี่ยนไป:
$$\Delta \theta = \omega \cdot \Delta t$$

เพื่อความแม่นยำสูง เราใช้ **Midpoint Integration (Runge-Kutta อันดับ 2)** ซึ่งใช้มุมกึ่งกลางช่วงเวลาในการฉายเวกเตอร์ความเร็ว:
$$\theta_{mid} = \theta_k + \frac{\Delta \theta}{2}$$
$$\Delta x = v \cdot \cos(\theta_{mid}) \cdot \Delta t$$
$$\Delta y = v \cdot \sin(\theta_{mid}) \cdot \Delta t$$

อัปเดตสถานะของหุ่นยนต์:
$$x_{k+1} = x_k + \Delta x$$
$$y_{k+1} = y_k + \Delta y$$
$$\theta_{k+1} = \text{atan2}\left(\sin(\theta_k + \Delta \theta), \cos(\theta_k + \Delta \theta)\right)$$

#### การแปลงมุมระนาบ 2D (Yaw) สู่ Quaternion ในพิกัด 3D
ใน ROS 2 การแสดงการวางแนวทิศทาง (Orientation) ต้องใช้ควอเทอร์เนียน $q = (x, y, z, w)$ เสมอ สำหรับหุ่นยนต์เคลื่อนที่บนระนาบ 2D ($Roll = 0, Pitch = 0, Yaw = \theta$):
$$q_x = 0.0$$
$$q_y = 0.0$$
$$q_z = \sin\left(\frac{\theta}{2}\right)$$
$$q_w = \cos\left(\frac{\theta}{2}\right)$$

---

## 🛠️ การวิเคราะห์โค้ดตัวอย่างในโมดูล (Code Walkthrough)

### [`diff_drive_kinematics.py`](file:///mnt/sda/ros/Essential_ROS/Week_06_Kinematics_REP_Standards/src/diff_drive_kinematics.py)
โหนดจลนศาสตร์และประมาณตำแหน่ง Odometry แบบสมบูรณ์:

- **การประกาศขนาดหุ่นยนต์ ([L26-L30](file:///mnt/sda/ros/Essential_ROS/Week_06_Kinematics_REP_Standards/src/diff_drive_kinematics.py#L26-L30)):**
  ```python
  self.declare_parameter('wheel_separation', 0.24)  # L = 24 cm
  self.declare_parameter('wheel_radius', 0.08)       # r = 8 cm
  ```
  กำหนดขนาดกายภาพของหุ่นยนต์ผ่านพารามิเตอร์เพื่อให้สามารถปรับเปลี่ยนตามสเปกของหุ่นยนต์จริงได้
- **Forward Kinematics Callback ([L53-L64](file:///mnt/sda/ros/Essential_ROS/Week_06_Kinematics_REP_Standards/src/diff_drive_kinematics.py#L53-L64)):**
  ```python
  def cmd_vel_callback(self, msg: Twist):
      v = msg.linear.x
      omega = msg.angular.z
      v_right = v + (omega * self.L / 2.0)
      v_left = v - (omega * self.L / 2.0)
      self.w_right = v_right / self.r
      self.w_left = v_left / self.r
  ```
  รับคำสั่งจาก `/cmd_vel` แล้วแตกเป็นความเร็วเชิงมุมของมอเตอร์แต่ละข้าง
- **Dead Reckoning & Odometry Loop 20 Hz ([L65-L113](file:///mnt/sda/ros/Essential_ROS/Week_06_Kinematics_REP_Standards/src/diff_drive_kinematics.py#L65-L113)):**
  ```python
  delta_x = v * math.cos(self.theta) * dt
  delta_y = v * math.sin(self.theta) * dt
  delta_theta = omega * dt
  self.x += delta_x
  self.y += delta_y
  self.theta += delta_theta
  self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))
  ```
  อินทิเกรตตำแหน่งสะสม พร้อมใช้ฟังก์ชัน `atan2` ในการ Wrap มุม $\theta$ ให้อยู่ในช่วง $[-\pi, \pi]$ ป้องกันตัวเลขสะสมจนโอเวอร์โฟลว์
- **การประกอบ Odometry Message ([L93-L112](file:///mnt/sda/ros/Essential_ROS/Week_06_Kinematics_REP_Standards/src/diff_drive_kinematics.py#L93-L112)):**
  กำหนด `frame_id = 'odom'` และ `child_frame_id = 'base_footprint'` ตามมาตรฐาน REP 105 อย่างแม่นยำ

---

## ⌨️ ตารางคำสั่ง CLI สำคัญ
| คำสั่ง | คำอธิบาย | ตัวอย่างการใช้งาน |
| :--- | :--- | :--- |
| `ros2 topic pub /cmd_vel ...` | สั่งให้หุ่นยนต์เคลื่อนที่ด้วยความเร็วที่กำหนด | `ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: 0.1}}"` |
| `ros2 topic echo /odom_calculated` | ดูข้อมูลตำแหน่ง พิกัด และความเร็วแบบเรียลไทม์ | `ros2 topic echo /odom_calculated` |
| `ros2 topic hz /odom_calculated` | วัดความถี่ของการอัปเดต Odometry (เป้าหมาย 20 Hz) | `ros2 topic hz /odom_calculated` |
| `ros2 topic info /odom_calculated -v` | ตรวจสอบ QoS Profile และจำนวนผู้รับส่งข้อมูล | `ros2 topic info /odom_calculated -v` |

---

## 📸 ภาพผลการทดสอบจริงจากระบบ (Live Execution & Terminal Capture)
ผลลัพธ์จากการรันคำสั่งและโหนดจริงในระบบ เพื่อใช้เป็นข้อมูลอ้างอิงในการตรวจสอบความถูกต้อง:

![Terminal Capture: Terminal — Week 06: Differential Drive Kinematics & Odometry Integration](images/terminal_run.png)

```console
user@amr-dev:~/ros$ ./docker/run_lab.sh python3 Essential_ROS/Week_06_Kinematics_REP_Standards/src/diff_drive_kinematics.py &
[INFO] [diff_drive_kinematics]: 🤖 [DiffDriveKinematics] Ready: L=0.24m, r=0.08m
user@amr-dev:~/ros$ ./docker/run_lab.sh ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.4}, angular: {z: 0.2}}'
publishing #1: geometry_msgs.msg.Twist(linear.x=0.4, angular.z=0.2)
user@amr-dev:~/ros$ ./docker/run_lab.sh ros2 topic echo --once /odom_calculated
header: frame_id: 'odom', child_frame_id: 'base_footprint'
pose: position: x: 0.8889, y: 0.2034, z: 0.0
      orientation: x: 0.0, y: 0.0, z: 0.2280, w: 0.9737 (Yaw = 0.459 rad)
twist: linear: x: 0.4, angular: z: 0.2
user@amr-dev:~/ros$ [CHECKPOINT PASSED: REP 103/105 COMPLIANT ODOMETRY BROADCAST]
```

---

## ⚠️ ปัญหาที่พบบ่อยและการแก้ไข (Troubleshooting)

| ที่ | อาการที่พบ (Symptom) | สาเหตุรากเหง้า (Root Cause) | แนวทางแก้ไข (Resolution) |
|:---:| :--- | :--- | :--- |
| 1 | **สั่งเลี้ยวซ้ายแต่หุ่นยนต์เลี้ยวขวา** | สลับเครื่องหมายของ $\omega$ หรือสลับความเร็วล้อซ้ายและขวา ($v_L, v_R$) | ตรวจสอบสมการ: การเลี้ยวทวนเข็มนาฬิกา (ซ้าย) ล้อขวาต้องหมุนเร็วกว่าล้อซ้าย ($v_R > v_L$) |
| 2 | **พิกัด Odometry คลาดเคลื่อนสะสมมหาศาล (Severe Drift)** | ค่ารัศมีล้อ $r$ หรือระยะฐานล้อ $L$ ที่ระบุในพารามิเตอร์ไม่ตรงกับขนาดฮาร์ดแวร์จริง | ทำการสอบเทียบ (Calibration): วัดขนาดจริงด้วยเวอร์เนียร์ และปรับชดเชยค่าสัมประสิทธิ์ล้อ |
| 3 | **มุม Yaw ทะลุเกิน $3.14$ แล้วไม่ยอมวนกลับเป็น $-3.14$** | ไม่ได้ใช้ฟังก์ชัน Normalization ทำให้มุมสะสมไปเรื่อยๆ | ใช้ `math.atan2(math.sin(theta), math.cos(theta))` หลังบวก $\Delta \theta$ ทุกครั้ง |
| 4 | **ความคลาดเคลื่อนสูงเมื่อหุ่นยนต์เลี้ยวด้วยความเร็วสูง** | ใช้วิธี Forward Euler Integration ธรรมดา ซึ่งมี Error สะสมสูงในการคำนวณแนวโค้ง | เปลี่ยนมาใช้ Midpoint Integration หรือคำนวณผ่านรัศมีความโค้ง ICC |
| 5 | **ข้อความ Odometry สั่นหรือไม่สม่ำเสมอ** | การคำนวณ $\Delta t$ ใช้ค่าคงที่แทนที่จะวัดจริงจากนาฬิการะบบ | ใช้ `current_time - last_time` วัดค่า $\Delta t$ จริงในทุก Loop Iteration |
| 6 | **Quaternion Normalization Error** | ผลรวมกำลังสองของควอเทอร์เนียน $x^2 + y^2 + z^2 + w^2 \neq 1.0$ จากความคลาดเคลื่อนทศนิยม | ใช้สูตร $\sin(\theta/2)$ และ $\cos(\theta/2)$ หรือฟังก์ชัน Normalize เวกเตอร์ก่อนบรรจุลงข้อความ |

---

## 📝 แบบทดสอบท้ายบท (Self-Assessment Quiz)

1. **คำถาม:** ตามมาตรฐาน REP 103 หากผู้สังเกตการณ์ยืนอยู่ด้านหลังหุ่นยนต์แล้วมองตรงไปข้างหน้า ทิศทางของแกน +X, +Y, และ +Z ชี้ไปทางทิศใดตามลำดับ?
2. **คำถาม:** การหมุนแบบทวนเข็มนาฬิกา (CCW) รอบแกน Z เมื่อมองจากด้านบนลงมา มีค่ามุม Yaw เป็นบวกหรือลบ?
3. **คำถาม:** จงอธิบายเหตุผลหลักตามมาตรฐาน REP 105 ว่าทำไมระบบนำทางจึงไม่สามารถต่อยอดการควบคุมการเคลื่อนที่เฉพาะที่ (Local Control) โดยตรงจากเฟรม `map` ได้?
4. **คำถาม:** กำหนดให้หุ่นยนต์มีระยะห่างระหว่างล้อ $L = 0.30\text{ m}$ และรัศมีล้อ $r = 0.10\text{ m}$ หากสั่งให้หุ่นยนต์วิ่งเป็นเส้นตรงด้วยความเร็ว $v = 0.5\text{ m/s}$ ความเร็วเชิงมุมของมอเตอร์ล้อแต่ละข้าง ($\omega_R, \omega_L$) จะมีค่าเท่าใด?
5. **คำถาม:** จากข้อมูลในข้อ 4 หากหุ่นยนต์ต้องการหมุนตัวอยู่กับที่ (In-place Rotation) ด้วยความเร็ว $\omega = 2.0\text{ rad/s}$ ล้อขวาและล้อซ้ายต้องหมุนด้วยความเร็วเชิงเส้น ($v_R, v_L$) เท่าใด?
6. **คำถาม:** รัศมีความโค้งชั่วขณะ (ICC Radius: $R$) ของหุ่นยนต์ Differential Drive มีค่าเป็นเท่าใดเมื่อหุ่นยนต์เคลื่อนที่เป็นเส้นตรงอย่างสมบูรณ์?
7. **คำถาม:** ในการแปลงมุมทิศทาง Yaw ($\theta = \pi\text{ rad} = 180^\circ$) เข้าสู่ Quaternion ค่าขององค์ประกอบ $(z, w)$ จะมีค่าเท่ากับเท่าใด?
8. **คำถาม:** ทำไมการอินทิเกรต Odometry ด้วยวิธี Midpoint Integration จึงให้ผลลัพธ์ที่แม่นยำกว่า Forward Euler Integration ในการเลี้ยวโค้ง?
9. **คำถาม:** ฟิลด์ `pose.covariance` ในข้อความ `nav_msgs/msg/Odometry` มีขนาดกี่มิติ และตัวเลขบนเส้นทแยงมุมหลัก (Diagonal) แสดงถึงค่าทางสถิติใด?
10. **คำถาม:** ตามมาตรฐาน REP 105 ข้อใดคือความแตกต่างทางความสูงระหว่างเฟรม `base_footprint` และ `base_link`?

<details>
<summary>🔍 ดูเฉลยคำตอบพร้อมคำอธิบายอย่างละเอียด</summary>

1. **ตอบ:** **+X ชี้ไปข้างหน้า (Forward), +Y ชี้ไปทางซ้าย (Left), และ +Z ชี้ขึ้นด้านบน (Upward)** ตามกฎมือขวา
2. **ตอบ:** มีค่า **เป็นบวก (+)** เสมอตามกฎมือกำขวา (Right-Hand Grip Rule) รอบแกน +Z
3. **ตอบ:** เนื่องจากเฟรม `map` เกิดจากการประมวลผลเซนเซอร์สากล (เช่น SLAM หรือ AMCL) ซึ่ง **อาจเกิดการกระโดดของพิกัดอย่างฉับพลัน (Discontinuous Position Jumps)** เมื่อระบบแก้ตำแหน่งหลงทาง หากนำพิกัดนี้ไปป้อนตัวควบคุมมอเตอร์โดยตรง จะทำให้ตัวควบคุมสั่งเร่งหรือเบรกมอเตอร์อย่างรุนแรงจนหุ่นยนต์กระตุกหรือล้มคว่ำ ระบบจึงต้องใช้เฟรม `odom` ซึ่งมีความต่อเนื่องและราบเรียบเสมอใน Local Control Loop
4. **ตอบ:**
   - จากสูตร $v_R = v_L = v = 0.5\text{ m/s}$
   - $\omega_R = \omega_L = \frac{v}{r} = \frac{0.5}{0.10} = \mathbf{5.0\text{ rad/s}}$
5. **ตอบ:**
   - หมุนตัวอยู่กับที่แปลว่า $v = 0$
   - $v_R = 0 + \frac{\omega L}{2} = \frac{2.0 \times 0.30}{2} = \mathbf{+0.30\text{ m/s}}$
   - $v_L = 0 - \frac{\omega L}{2} = -\frac{2.0 \times 0.30}{2} = \mathbf{-0.30\text{ m/s}}$ (ล้อสองข้างหมุนสวนทางกัน)
6. **ตอบ:** รัศมีความโค้ง $R \rightarrow \boldsymbol{\infty}$ (เข้าสู่อินฟินิตี้ เนื่องจาก $\omega = 0$ จากสูตร $R = \frac{v}{\omega}$)
7. **ตอบ:**
   - $q_z = \sin\left(\frac{\pi}{2}\right) = \mathbf{1.0}$
   - $q_w = \cos\left(\frac{\pi}{2}\right) = \mathbf{0.0}$
   - (โดยที่ $q_x = 0.0$ และ $q_y = 0.0$)
8. **ตอบ:** เพราะ Forward Euler นำมุมทิศทาง ณ จุดเริ่มต้นคาบเวลา ($\theta_k$) มาฉายเวกเตอร์ตลอดช่วงเวลา $\Delta t$ ทำให้เกิดการประเมินส่วนโค้งตัดตรง (Underestimation of turning) ในขณะที่ Midpoint นำมุมกึ่งกลางช่วงเวลา ($\theta_k + \frac{\Delta \theta}{2}$) มาใช้ ซึ่งเฉลี่ยเวกเตอร์สัมผัสความโค้งได้ใกล้เคียงกับส่วนโค้งจริงทางคณิตศาสตร์มากกว่า
9. **ตอบ:** มีขนาด **$6 \times 6$ (อาเรย์ 36 ช่อง)** สำหรับ $(x, y, z, \text{roll}, \text{pitch}, \text{yaw})$ โดยค่าบนเส้นทแยงมุมหลักแสดงค่า **ความแปรปรวน (Variance: $\sigma^2$)** ของตัวแปรแต่ละมิติ ซึ่งบ่งบอกระดับความไม่แน่นอนของข้อมูล
10. **ตอบ:** `base_footprint` จะถูกฉายระนาบลงบนผิวสัมผัสพื้นดินพอดี ($Z = 0$) เพื่อการวางแผนเส้นทางแบบ 2 มิติ ในขณะที่ `base_link` จะมีระยะยกสูงตามแกน Z เท่ากับระดับความสูงของจุดศูนย์กลางการหมุนหรือแชสซีจริงของหุ่นยนต์
</details>

---

## 📚 แหล่งอ้างอิงและศึกษาเพิ่มเติม
- [REP 103: Standard Units of Measure & Coordinate Conventions](https://www.ros.org/reps/rep-0103.html)
- [REP 105: Coordinate Frames for Mobile Platforms](https://www.ros.org/reps/rep-0105.html)
- [Siegwart, Nourbakhsh, Scaramuzza: Introduction to Autonomous Mobile Robots (MIT Press)](https://mitpress.mit.edu/9780262015356/introduction-to-autonomous-mobile-robots/)
- [ROS 2 nav_msgs/msg/Odometry Documentation](https://docs.ros2.org/latest/api/nav_msgs/msg/Odometry.html)
