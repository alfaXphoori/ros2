# 📖 Week 11: การต่อเชื่อมมอเตอร์ เซนเซอร์ และระบบ ros_gz_bridge
**เวลาเรียน:** บรรยาย 2 ชั่วโมง | ปฏิบัติการ 3 ชั่วโมง | ศึกษาค้นคว้าด้วยตนเอง 4 ชั่วโมง  
**วิชาบังคับก่อน:** [สัปดาห์ที่ 10: สภาพแวดล้อมจำลอง 3 มิติด้วย Gazebo Sim (Harmonic)](../Week_10_Gazebo_Sim_Harmonic/Readme.md)  
**เอกสารปฏิบัติการ:** [ใบงานแล็บสัปดาห์ที่ 11](Lab_Exercises.md)

---

## 🎯 วัตถุประสงค์การเรียนรู้ (Learning Objectives)
เมื่อจบบทเรียนนี้ ผู้เรียนจะสามารถ:
1. **วิเคราะห์สถาปัตยกรรมการแปลงโปรโตคอล** ระหว่าง Google Protobuf (Gazebo Transport) และ Common Data Representation / CDR (ROS 2 DDS) ผ่านสะพาน `ros_gz_bridge`
2. **กำหนดทิศทางการเชื่อมต่อ (Bridge Direction)**: `ROS_TO_GZ`, `GZ_TO_ROS`, และ `BIDIRECTIONAL` ในไฟล์ YAML ได้อย่างถูกต้องและปลอดภัย
3. **กำหนดค่าปลั๊กอินควบคุมการขับเคลื่อนสองล้อ (Gazebo DiffDrive Plugin)** พร้อมเชื่อมโยงการอ่านค่า Odometry และความเร็วรอบล้อกลับเข้าสู่ ROS 2
4. **คำนวณคณิตศาสตร์แปลงพิกัดของลำแสงเลเซอร์ (LaserScan Angle-to-Index & Polar-to-Cartesian Math)** จากข้อความ `sensor_msgs/msg/LaserScan`
5. **พัฒนาระบบม่านความปลอดภัยอัตโนมัติ (Safety Shield & Emergency Braking)** ที่คำนวณระยะหยุดขั้นต่ำตามหลักการหน่วงความเร็ว (Deceleration Physics)

---

## ⏱️ แผนการสอน 2 ชั่วโมง (Lecture Outline)
| ช่วงเวลา | หัวข้อ | กิจกรรมการเรียนรู้ |
| :---: | :--- | :--- |
| **00:00 - 00:30** | สถาปัตยกรรม ros_gz_bridge: การจับคู่ Serialization Protobuf $\leftrightarrow$ CDR | บรรยายพร้อมตารางจับคู่ ROS 2 Type vs Gazebo Msg Type และบทบาทของ `parameter_bridge` |
| **00:30 - 01:00** | ปลั๊กอินควบคุมมอเตอร์ (DiffDrive) และสัญญาณเวลาจำลอง `/clock` | วิเคราะห์ความสำคัญของ `use_sim_time: true` และการปิดลูปคำสั่ง `/cmd_vel` |
| **01:00 - 01:30** | โครงสร้าง LaserScan, คณิตศาสตร์ลำแสง LiDAR และพิกัดคาร์ทีเซียน | แสดงสมการแปลงดัชนีเป็นมุม, การแปลง Polar เป็น $(x, y)$, และการกรองระยะปลอดภัย |
| **01:30 - 02:00** | Code Walkthrough: `ros_gz_bridge.yaml`, `emergency_stop_node.py` และสรุปก่อนเข้า Lab | วิเคราะห์การประยุกต์ใช้วงจรม่านนิรภัย และการทดสอบตัดคำสั่งขับขี่ |

---

## 🏛️ สถาปัตยกรรมระบบ (Architectural Deep Dive)

### 1. สถาปัตยกรรมระบบบริดจ์ (ros_gz_bridge Architecture)
Gazebo Sim (Harmonic) ใช้ระบบเครือข่ายภายใน **Gazebo Transport** ซึ่งใช้ฟอร์แมตข้อมูลเป็น Google Protobuf (น้ำหนักเบาและประมวลผลเร็วมากในระดับ C++) ในขณะที่ ROS 2 ใช้มาตรฐาน **OMG DDS** ซึ่งเข้ารหัสข้อมูลเป็น Common Data Representation (CDR) 

เพื่อให้ทั้งสองระบบสื่อสารกันได้ แพ็กเกจ `ros_gz_bridge` จะสร้างโปรเซสตัวแปลงข้อมูลสองทาง (Bidirectional Translation Process) ชื่อว่า **`parameter_bridge`**:

```mermaid
flowchart LR
    subgraph ROS2_Stack ["ROS 2 Node Graph (DDS / CDR)"]
        Teleop["Teleop / Nav2 Controller<br/>(/cmd_vel [geometry_msgs/Twist])"]
        SLAM["SLAM Toolbox / Costmap<br/>(/scan [sensor_msgs/LaserScan])"]
        OdomNode["Localization / EKF<br/>(/odom [nav_msgs/Odometry])"]
        SimTime["ROS 2 System Clock<br/>(/clock [rosgraph_msgs/Clock])"]
    end

    subgraph Bridge_Layer ["ros_gz_bridge (parameter_bridge)"]
        B_Vel["ROS_TO_GZ<br/>Twist แปลงเป็น gz.msgs.Twist"]
        B_Scan["GZ_TO_ROS<br/>gz.msgs.LaserScan แปลงเป็น LaserScan"]
        B_Odom["GZ_TO_ROS<br/>gz.msgs.Odometry แปลงเป็น Odometry"]
        B_Clock["GZ_TO_ROS<br/>gz.msgs.Clock แปลงเป็น Clock"]
    end

    subgraph Gazebo_Stack ["Gazebo Sim 8 (Gazebo Transport / Protobuf)"]
        GZ_DiffDrive["DiffDrive System Plugin<br/>(ขับเคลื่อนข้อต่อล้อจริง)"]
        GZ_LiDAR["Sensors System Plugin<br/>(เรนเดอร์ GPU Ray Scan)"]
        GZ_OdomPub["Gazebo Odometry Publisher"]
        GZ_WorldClock["Physics Simulation Clock"]
    end

    Teleop --> B_Vel --> GZ_DiffDrive
    GZ_LiDAR --> B_Scan --> SLAM
    GZ_OdomPub --> B_Odom --> OdomNode
    GZ_WorldClock --> B_Clock --> SimTime

    style ROS2_Stack fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style Bridge_Layer fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style Gazebo_Stack fill:#f1f8e9,stroke:#558b2f,stroke-width:2px
```

---

### 2. บทบาทสำคัญของ `/clock` และพารามิเตอร์ `use_sim_time`
ในระบบจำลองฟิสิกส์ ความเร็วของการคำนวณขึ้นอยู่กับภาระของเครื่องคอมพิวเตอร์ ซึ่งมักจะช้ากว่าเวลาจริงบนโลกมนุษย์ (เช่น Real-Time Factor: $\text{RTF} = 0.50$):
- **หากตั้ง `use_sim_time: false`:** โหนดใน ROS 2 จะยึดเวลาจากนาฬิกาของเครื่องคอมพิวเตอร์ (System Wall Time) ในขณะที่ Gazebo ปล่อยข้อมูลเซนเซอร์ออกมาด้วยเวลาจำลอง (Simulation Time) ผลลัพธ์คือ **TF Buffer จะแจ้งเตือน Extrapolation Error ทันที** เพราะเวลาของเซนเซอร์ล้าหลังเวลาในระบบไปเรื่อยๆ
- **หากตั้ง `use_sim_time: true`:** โหนดทุกตัวใน ROS 2 จะหยุดใช้นาฬิกาคอมพิวเตอร์ และเปลี่ยนไปฟังข้อความเวลาจากท็อปปิก `/clock` ที่ Gazebo ปล่อยออกมา ทำให้เวลาของอัลกอริทึม SLAM, Navigation, และ TF ซิงโครไนซ์ตรงกันอย่างสมบูรณ์แบบ $100\%$

---

### 3. โครงสร้างและการประมวลผลข้อความ LaserScan
ข้อความ `sensor_msgs/msg/LaserScan` ประกอบด้วยข้อมูลเรดาร์เลเซอร์ 2 มิติ:

```mermaid
flowchart TD
    Scan["sensor_msgs/msg/LaserScan"]
    H["Header: stamp (เวลาที่ยิงแสง), frame_id = 'lidar_link'"]
    A["มุมกวาด: angle_min (-180°), angle_max (+180°), angle_increment (0.5°)"]
    R["ระยะทาง: range_min (0.12m), range_max (12.0m)"]
    D["ranges[]: อาเรย์ตัวเลขทศนิยมระบุระยะห่างของแต่ละลำแสง"]

    Scan --> H
    Scan --> A
    Scan --> R
    Scan --> D
```

#### ก. การแปลงดัชนีอาเรย์ (Array Index $i$) สู่มุมองศา ($\theta_i$):
$$\theta_i = \text{angle min} + (i \cdot \text{angle increment})$$

#### ข. การแปลงจากมุมเป้าหมาย ($\theta$) กลับเป็นดัชนีอาเรย์ ($i$):
$$i = \left\lfloor \frac{\theta - \text{angle min}}{\text{angle increment}} \right\rfloor$$

#### ค. การแปลงจากระบบพิกัดเชิงขั้ว (Polar) สู่พิกัดคาร์ทีเซียน (Cartesian $x, y$):
จุดตรวจจับสิ่งกีดขวางในระนาบของ LiDAR:
$$x_i = r_i \cos(\theta_i)$$
$$y_i = r_i \sin(\theta_i)$$
โดยที่ $r_i = \text{ranges}[i]$

---

### 4. ฟิสิกส์การเบรกฉุกเฉินและม่านความปลอดภัย (Safety Shield Dynamics)
การตั้งระยะปลอดภัยของม่านนิรภัยหุ่นยนต์ (Safety Shield) ไม่ควรใช้ค่าสุ่ม แต่ต้องคำนวณจากกฎการเคลื่อนที่ของนิวตัน:
$$d_{\text{stop}} = d_{\text{reaction}} + d_{\text{braking}} = (v \cdot t_{\text{reaction}}) + \frac{v^2}{2 a_{\text{max}}}$$

โดยที่:
- $v$: ความเร็วสูงสุดของหุ่นยนต์ ($m/s$)
- $t_{\text{reaction}}$: คาบเวลาหน่วงของระบบประมวลผลรวมกับการส่งคำสั่งผ่านเครือข่าย (Latency เช่น $100\text{ ms} = 0.1\text{ s}$)
- $a_{\text{max}}$: ความหน่วงเบรกสูงสุดของล้อก่อนเกิดการลื่นไถล ($m/s^2$)

**ตัวอย่างการคำนวณ:**  
หากหุ่นยนต์วิ่งด้วยความเร็ว $v = 0.6\text{ m/s}$, เบรกหน่วงได้ $a_{\text{max}} = 1.2\text{ m/s}^2$, และ $t_{\text{reaction}} = 0.1\text{ s}$:
$$d_{\text{stop}} = (0.6 \times 0.1) + \frac{0.6^2}{2 \times 1.2} = 0.06 + \frac{0.36}{2.4} = 0.06 + 0.15 = \mathbf{0.21\text{ m}}$$
ดังนั้น ค่าระยะตรวจจับปลอดภัยในโค้ดจึงควรกำหนดไว้ที่อย่างน้อย $0.35\text{ m}$ เพื่อเป็นระยะเผื่อฉุกเฉิน (Safety Margin)

---

## 🛠️ การวิเคราะห์โค้ดตัวอย่างในโมดูล (Code Walkthrough)

### 1. [`ros_gz_bridge.yaml`](file:///mnt/sda/ros/Essential_ROS/Week_11_Actuators_Sensors_Bridge/config/ros_gz_bridge.yaml)
ไฟล์คอนฟิกกำหนดช่องสัญญาณบริดจ์ระหว่าง ROS 2 และ Gazebo Sim:
- **คำสั่งขับเคลื่อนความเร็ว ([L2-L6](file:///mnt/sda/ros/Essential_ROS/Week_11_Actuators_Sensors_Bridge/config/ros_gz_bridge.yaml#L2-L6)):**
  ```yaml
  - ros_topic_name: "/cmd_vel"
    gz_topic_name: "/cmd_vel"
    ros_type_name: "geometry_msgs/msg/Twist"
    gz_type_name: "gz.msgs.Twist"
    direction: ROS_TO_GZ
  ```
  กำหนดให้คำสั่งความเร็วเดินทางจากโหนด ROS 2 (เช่น แป้นพิมพ์ หรือ Nav2) เข้าสู่ Gazebo Transport เพื่อส่งต่อให้มอเตอร์
- **เซนเซอร์ LiDAR และ Odometry ([L8-L18](file:///mnt/sda/ros/Essential_ROS/Week_11_Actuators_Sensors_Bridge/config/ros_gz_bridge.yaml#L8-L18)):**
  กำหนดทิศทาง `GZ_TO_ROS` เพื่อนำข้อมูลระยะเลเซอร์และตำแหน่งล้อจากโลกจำลองกลับมาประมวลผลในระบบหุ่นยนต์ ROS 2
- **การเชื่อมต่อสัญญาณนาฬิกา ([L26-L30](file:///mnt/sda/ros/Essential_ROS/Week_11_Actuators_Sensors_Bridge/config/ros_gz_bridge.yaml#L26-L30)):**
  บริดจ์ท็อปปิก `/clock` เข้าสู่ ROS 2 เพื่อรักษาความสอดคล้องของเวลา

---

### 2. [`emergency_stop_node.py`](file:///mnt/sda/ros/Essential_ROS/Week_11_Actuators_Sensors_Bridge/src/emergency_stop_node.py)
โหนดตรวจจับระยะประชิดและสั่งตัดความเร็วอัตโนมัติ:
- **การกำหนดระยะปลอดภัย ([L20](file:///mnt/sda/ros/Essential_ROS/Week_11_Actuators_Sensors_Bridge/src/emergency_stop_node.py#L20)):**
  ```python
  self.safety_distance = 0.35  # meters
  ```
- **การกรองกรวยมุมมองด้านหน้า $\pm 30^\circ$ ([L36-L43](file:///mnt/sda/ros/Essential_ROS/Week_11_Actuators_Sensors_Bridge/src/emergency_stop_node.py#L36-L43)):**
  ```python
  for i, dist in enumerate(msg.ranges):
      angle = msg.angle_min + (i * msg.angle_increment)
      if -math.radians(30) <= angle <= math.radians(30):
          if msg.range_min < dist < msg.range_max:
              if dist < min_front_dist:
                  min_front_dist = dist
  ```
  คำนวณมุมจริงของลำแสงเลเซอร์แต่ละเส้น และคัดกรองเฉพาะลำแสงที่อยู่ในขอบเขตที่ตัวถังหุ่นยนต์จะเคลื่อนที่ชน
- **การส่งคำสั่งเบรกฉุกเฉิน ([L44-L52](file:///mnt/sda/ros/Essential_ROS/Week_11_Actuators_Sensors_Bridge/src/emergency_stop_node.py#L44-L52)):**
  หากระยะใกล้สุดน้อยกว่า $0.35\text{ m}$ โหนดจะส่งคำสั่งหยุดนิ่ง `Twist(linear.x=0.0, angular.z=0.0)` ออกไปยัง `/cmd_vel` ทันทีเพื่อเบรกมอเตอร์

---

## ⌨️ ตารางคำสั่ง CLI สำคัญ
| คำสั่ง | คำอธิบาย | ตัวอย่างการใช้งาน |
| :--- | :--- | :--- |
| `ros2 run ros_gz_bridge parameter_bridge --ros-args -p config_file:=<path>` | เปิดโหนดบริดจ์ด้วยไฟล์ YAML | `ros2 run ros_gz_bridge parameter_bridge --ros-args -p config_file:=Essential_ROS/Week_11_Actuators_Sensors_Bridge/config/ros_gz_bridge.yaml` |
| `ros2 topic echo /scan --field ranges` | แสดงข้อมูลระยะทางที่เซนเซอร์ LiDAR ยิงได้แบบสดๆ | `ros2 topic echo /scan --field ranges` |
| `ros2 topic hz /scan` | วัดความถี่ของเซนเซอร์ LiDAR (เป้าหมาย 10–20 Hz) | `ros2 topic hz /scan` |
| `ros2 topic pub /cmd_vel ...` | สั่งเคลื่อนที่หุ่นยนต์ในโลกจำลองผ่านบรรทัดคำสั่ง | `ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.3}}"` |
| `ros2 topic echo /clock` | ตรวจสอบการเดินของสัญญาณเวลาจำลอง | `ros2 topic echo /clock` |

---

## ⚠️ ปัญหาที่พบบ่อยและการแก้ไข (Troubleshooting)

| ที่ | อาการที่พบ (Symptom) | สาเหตุรากเหง้า (Root Cause) | แนวทางแก้ไข (Resolution) |
|:---:| :--- | :--- | :--- |
| 1 | **หุ่นยนต์ใน Gazebo ไม่ยอมขยับตามคำสั่ง `/cmd_vel`** | ทิศทางใน `ros_gz_bridge.yaml` ผิด หรือตั้งชื่อ Topic ไม่ตรงกับปลั๊กอิน | ตรวจสอบว่าระบุทิศทางเป็น `ROS_TO_GZ` และชนิดข้อความเป็น `geometry_msgs/msg/Twist` |
| 2 | **ท็อปปิก `/scan` ใน ROS 2 ไม่มีข้อมูลส่งมาเลย** | ในโลกจำลองลืมโหลด `gz-sim-sensors-system` หรือลืมใส่ Render Engine `ogre2` | ตรวจสอบไฟล์ `.sdf` ของโลกจำลองว่ามีปลั๊กอิน Sensors สมบูรณ์ |
| 3 | **TF Buffer ฟ้อง Error: `Extrapolation into the past/future`** | โหนดใน ROS 2 ไม่ได้เปิดใช้งานเวลาจำลอง ทำให้เทียบเวลากับเวลาจริงบนโลก | เติมพารามิเตอร์ `use_sim_time: true` ให้กับทุกโหนดในระบบ |
| 4 | **เซนเซอร์ LiDAR รายงานค่า `inf` หรือ `0.0` ทั้งหมด** | โมเดลเซนเซอร์ติดตั้งอยู่ข้างในตัวถังหุ่นยนต์ ทำให้ลำแสงเลเซอร์ชนกับ Collision Box ของตัวเอง | ปรับตำแหน่งยกเซนเซอร์ LiDAR ให้สูงพ้นหลังคาตัวถัง หรือเว้นช่องเปิดให้ลำแสง |
| 5 | **Emergency Stop สั่งเบรกแล้วแต่หุ่นยนต์ยังคงวิ่งต่อ** | มีโหนดอื่น (เช่น Teleop) ยังคงส่งข้อความทับลงไปบน `/cmd_vel` ด้วยความถี่สูงกว่า | ใช้แพ็กเกจ `twist_mux` ในการจัดลำดับความสำคัญ (Priority Lockout) ของการสั่งการ |
| 6 | **บริดจ์ล่มพร้อมแจ้งเตือน: `Failed to create bridge for topic`** | ชื่อประเภทข้อความ (Message Type) ใน YAML พิมพ์สะกดผิด | ตรวจสอบชื่อแพ็กเกจและประเภทข้อมูลตามตารางจับคู่มาตรฐาน |

---

## 📝 แบบทดสอบท้ายบท (Self-Assessment Quiz)

1. **คำถาม:** เหตุใดโปรแกรม ROS 2 และ Gazebo Sim (Harmonic) จึงจำเป็นต้องมี `ros_gz_bridge` คอยเป็นตัวกลางในการส่งผ่านข้อมูล?
2. **คำถาม:** การตั้งค่า `direction: ROS_TO_GZ` เหมาะสมสำหรับท็อปปิกใดในระบบควบคุมหุ่นยนต์ AMR?
3. **คำถาม:** หากไม่เปิดใช้งานพารามิเตอร์ `use_sim_time: true` ในโหนด ROS 2 ขณะจำลองใน Gazebo จะเกิดผลกระทบอย่างไรต่อระบบพิกัด TF?
4. **คำถาม:** ในข้อความ `sensor_msgs/msg/LaserScan` หาก $\text{angle min} = -\pi$, $\text{angle max} = +\pi$, และมีลำแสงรวม 360 เส้น ดัชนีช่องใดคือลำแสงที่ชี้ตรงไปข้างหน้าของหุ่นยนต์พอดี?
5. **คำถาม:** จากข้อ 4 ลำแสงที่ทำมุม $+90^\circ$ (ชี้ไปทางซ้ายของหุ่นยนต์) จะอยู่ที่ดัชนีช่องใดในอาเรย์ `ranges`?
6. **คำถาม:** กำหนดให้หุ่นยนต์วิ่งด้วยความเร็ว $v = 0.5\text{ m/s}$ และมีความหน่วงเบรกสูงสุด $a_{\text{max}} = 1.0\text{ m/s}^2$ หากไม่คิดเวลาตอบสนอง ระยะเบรกขั้นต่ำทางทฤษฎีมีค่าเท่าใด?
7. **คำถาม:** ในการแปลงข้อมูลพิกัดเชิงขั้วของ LiDAR ($r, \theta$) เข้าสู่พิกัดคาร์ทีเซียนของจุดสัมผัส $(x, y)$ สมการที่ใช้คืออะไร?
8. **คำถาม:** สัญญาณเวลาจาก Gazebo ที่ส่งผ่านท็อปปิก `/clock` ใช้ข้อความประเภทใดในฝั่ง ROS 2?
9. **คำถาม:** ทำไมโหนด Emergency Stop จึงควรกรองเฉพาะมุมมองด้านหน้า ($\pm 30^\circ$) แทนที่จะตรวจจับรอบตัว 360 องศา?
10. **คำถาม:** คำสั่ง CLI ใดที่ใช้ในการวัดความถี่ของการปล่อยข้อมูลในท็อปปิก `/scan` ว่าทำงานสม่ำเสมอหรือไม่?

<details>
<summary>🔍 ดูเฉลยคำตอบพร้อมคำอธิบายอย่างละเอียด</summary>

1. **ตอบ:** เนื่องจากทั้งสองระบบใช้เทคโนโลยีมิดเดิลแวร์และการเข้ารหัสข้อมูลคนละมาตรฐานกัน (ROS 2 ใช้มาตรฐาน OMG DDS แบบ CDR ในขณะที่ Gazebo Sim ใช้ Gazebo Transport แบบ Google Protobuf) จึงต้องมี `parameter_bridge` คอยถอดรหัสและแปลงโครงสร้างข้อมูลข้ามไปมาระหว่างสองโปรโตคอล
2. **ตอบ:** เหมาะสำหรับ **คำสั่งขับเคลื่อนหรือควบคุม (Control Commands)** เช่น `/cmd_vel` เพื่อส่งค่าความเร็วจาก ROS 2 ไปยังมอเตอร์ในโลกจำลอง
3. **ตอบ:** โหนด ROS 2 จะใช้เวลาจากนาฬิกาของเครื่องคอมพิวเตอร์จริง (Wall Time) ซึ่งเดินเร็วกว่าเวลาจำลองของฟิสิกส์ (Simulation Time) ทำให้เกิดปัญหาเวลาเหลื่อมล้ำ ส่งผลให้ **TF2 เกิดข้อผิดพลาด Extrapolation Error** และระบบ SLAM หรือ Navigation ไม่สามารถคำนวณตำแหน่งได้
4. **ตอบ:**
   - $\text{angle increment} = \frac{2\pi}{360}\text{ rad}$
   - ดัชนีหน้าตรง ($\theta = 0$): $i = \frac{0 - (-\pi)}{2\pi / 360} = \frac{\pi}{2\pi / 360} = \mathbf{180}$
5. **ตอบ:**
   - $+90^\circ = +\frac{\pi}{2}\text{ rad}$
   - ดัชนีทางซ้าย: $i = \frac{\frac{\pi}{2} - (-\pi)}{2\pi / 360} = \frac{\frac{3\pi}{2}}{2\pi / 360} = \frac{3}{4} \times 360 = \mathbf{270}$
6. **ตอบ:**
   - สูตร: $d_{\text{stop}} = \frac{v^2}{2 a_{\text{max}}}$
   - แทนค่า: $d_{\text{stop}} = \frac{0.5^2}{2 \times 1.0} = \frac{0.25}{2.0} = \mathbf{0.125\text{ m}}$ (12.5 เซนติเมตร)
7. **ตอบ:**
   - $x = r \cos(\theta)$
   - $y = r \sin(\theta)$
8. **ตอบ:** ข้อความประเภท **`rosgraph_msgs/msg/Clock`**
9. **ตอบ:** เพื่อป้องกันไม่ให้หุ่นยนต์เบรกโดยไม่จำเป็นเมื่อเคลื่อนที่ผ่านกำแพงด้านข้าง หรือเมื่อมีสิ่งกีดขวางอยู่ด้านหลังในขณะที่หุ่นยนต์กำลังเคลื่อนที่ไปข้างหน้า การจำกัดกรอบเฉพาะทิศทางการเคลื่อนที่จะช่วยให้หุ่นยนต์นำทางได้อย่างราบรื่น
10. **ตอบ:** คำสั่ง **`ros2 topic hz /scan`**
</details>

---

## 📚 แหล่งอ้างอิงและศึกษาเพิ่มเติม
- [ros_gz Official Repository & Tutorials](https://github.com/gazebosim/ros_gz)
- [ROS 2 LaserScan Message Documentation](https://docs.ros2.org/latest/api/sensor_msgs/msg/LaserScan.html)
- [Gazebo Sim DiffDrive Plugin Specification](https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1DiffDrive.html)
- [Autonomous Mobile Robot Safety Standards (ISO 3691-4)](https://www.iso.org/standard/70381.html)
