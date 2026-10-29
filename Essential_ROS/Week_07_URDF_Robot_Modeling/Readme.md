# 📖 Week 07: การสร้างแบบจำลอง 3 มิติ (URDF) และ Inertia Matrix
**เวลาเรียน:** บรรยาย 2 ชั่วโมง | ปฏิบัติการ 3 ชั่วโมง | ศึกษาค้นคว้าด้วยตนเอง 4 ชั่วโมง  
**วิชาบังคับก่อน:** [สัปดาห์ที่ 6: มาตรฐานวิศวกรรมพิกัด (REP 103/105) และจลนศาสตร์ AMR](../Week_06_Kinematics_REP_Standards/Readme.md)  
**เอกสารปฏิบัติการ:** [ใบงานแล็บสัปดาห์ที่ 7](Lab_Exercises.md)

---

## 🎯 วัตถุประสงค์การเรียนรู้ (Learning Objectives)
เมื่อจบบทเรียนนี้ ผู้เรียนจะสามารถ:
1. **ออกแบบและสร้างไฟล์ Unified Robot Description Format (URDF)** สำหรับหุ่นยนต์ขับเคลื่อนสองล้อ (AMR) ตามโครงสร้างไวยากรณ์ภาษา XML มาตรฐานของ ROS 2
2. **วิเคราะห์ความแตกต่างและบทบาทเฉพาะของแท็ก 3 มิติ**: `<visual>` (การเรนเดอร์ใน RViz2), `<collision>` (การคำนวณการชนใน Physics Engine), และ `<inertial>` (มวลและเทนเซอร์ความเฉื่อย)
3. **จำแนกประเภทข้อต่อหุ่นยนต์ 6 ชนิด** (`fixed`, `continuous`, `revolute`, `prismatic`, `planar`, `floating`) และเลือกใช้แกนหมุน (`<axis>`) ได้ถูกต้องตามหลักกลศาสตร์
4. **คำนวณเทนเซอร์ความเฉื่อย (Inertia Tensor: $I_{xx}, I_{yy}, I_{zz}$)** ของรูปทรงเรขาคณิตพื้นฐาน (Solid Box, Solid Cylinder, Solid Sphere) พร้อมประยุกต์ทฤษฎีแกนขนาน (Parallel Axis Theorem)
5. **วิเคราะห์กระบวนการทำงานของ `robot_state_publisher`** ในการแปลงข้อความ `sensor_msgs/msg/JointState` ให้เป็นระนาบพิกัดความสัมพันธ์ใน TF Tree (`/tf` และ `/tf_static`)

---

## ⏱️ แผนการสอน 2 ชั่วโมง (Lecture Outline)
| ช่วงเวลา | หัวข้อ | กิจกรรมการเรียนรู้ |
| :---: | :--- | :--- |
| **00:00 - 00:30** | โครงสร้างไวยากรณ์ URDF และทฤษฎีต้นไม้ข้อต่อ (Link-Joint Tree) | วิเคราะห์ข้อกำหนด XML, ความสัมพันธ์ Parent-Child, และประเภทข้อต่อ 6 ชนิด |
| **00:30 - 01:00** | Visual vs Collision Geometry และการ Optimize ประสิทธิภาพ | เปรียบเทียบการใช้ Mesh ไฟล์ CAD กับ Collision Primitives เพื่อลดภาระ CPU |
| **01:00 - 01:40** | คณิตศาสตร์เมทริกซ์ความเฉื่อย (Inertia Tensor Formulation) | พิสูจน์สูตร $I$ ของกล่อง, ล้อทรงกระบอก, ลูกล้อทรงกลม และการจัดแกนหมุน |
| **01:40 - 02:00** | การใช้ `check_urdf`, `robot_state_publisher` และเตรียมเข้า Lab | ตรวจสอบไฟล์ URDF ด้วย CLI และรัน `display_urdf.launch.py` ใน RViz2 |

---

## 🏛️ สถาปัตยกรรมระบบ (Architectural Deep Dive)

### 1. โครงสร้างพื้นฐานของ URDF (Links and Joints Architecture)
URDF (Unified Robot Description Format) เป็นรูปแบบไฟล์ XML ที่ใช้เป็นภาษากลางในการอธิบายสรีระและจลนศาสตร์ของหุ่นยนต์ใน ROS:
- **`<link>`**: ชิ้นส่วนแข็ง (Rigid Body) ที่มีมวล รูปร่าง และพิกัดเฉพาะตัว
- **`<joint>`**: จุดเชื่อมต่อทางกลศาสตร์ระหว่าง 2 ลิงก์ ซึ่งต้องระบุความสัมพันธ์แบบลำดับชั้นต้นไม้ (**Parent Link** และ **Child Link**) ห้ามมีวงจรปิด (No Closed Loops ใน URDF มาตรฐาน)

```mermaid
flowchart TD
    Footprint["base_footprint<br/>(Virtual 2D Ground Projection: Z=0)"]
    BaseLink["base_link<br/>(Main Body / Chassis Center)"]
    LWheel["left_wheel_link<br/>(Active Drive Wheel)"]
    RWheel["right_wheel_link<br/>(Active Drive Wheel)"]
    FCaster["front_caster_link<br/>(Passive Support)"]
    RCaster["rear_caster_link<br/>(Passive Support)"]
    Lidar["lidar_link<br/>(2D Laser Sensor)"]
    Camera["camera_link<br/>(RGB-D Sensor)"]

    Footprint -->|"base_footprint_joint [fixed]"| BaseLink
    BaseLink -->|"left_wheel_joint [continuous]"| LWheel
    BaseLink -->|"right_wheel_joint [continuous]"| RWheel
    BaseLink -->|"front_caster_joint [fixed]"| FCaster
    BaseLink -->|"rear_caster_joint [fixed]"| RCaster
    BaseLink -->|"lidar_joint [fixed]"| Lidar
    BaseLink -->|"camera_joint [fixed]"| Camera

    style Footprint fill:#f5f5f5,stroke:#9e9e9e,stroke-width:1px
    style BaseLink fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style Lidar fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style LWheel fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style RWheel fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
```

#### ประเภทของข้อต่อ (Joint Types in URDF):
1. **`fixed`**: เชื่อมต่อติดแน่น ไม่มีการเคลื่อนไหวสัมพัทธ์ (0 องศาอิสระ) เช่น เซนเซอร์ LiDAR หรือโครงสร้างภายใน
2. **`continuous`**: หมุนรอบแกนได้อย่างอิสระไม่จำกัดรอบ (1 องศาอิสระ, หมุน $360^\circ$ ต่อเนื่อง) นิยมใช้กับล้อขับเคลื่อน
3. **`revolute`**: หมุนรอบแกนโดยมีขีดจำกัดมุมการหมุนต่ำสุดและสูงสุด (`<limit lower="..." upper="..."/>`) นิยมใช้กับข้อต่อแขนกล
4. **`prismatic`**: เคลื่อนที่แบบเชิงเส้นในแนวแกน (1 องศาอิสระแบบเลื่อน) เช่น ลิฟต์ยกพาเลท, รางสไลด์
5. **`planar`**: เคลื่อนที่บนระนาบ 2 มิติ (2 แปลงตำแหน่ง, 1 หมุน)
6. **`floating`**: ลอยตัวอิสระ 6 องศาอิสระ (3 แปลงตำแหน่ง, 3 หมุน)

---

### 2. องค์ประกอบ 3 เสาหลักของ `<link>`
ภายในแท็กลิงก์ 1 ชิ้น จะมีองค์ประกอบที่ทำหน้าที่แตกต่างกันอย่างสิ้นเชิง 3 ส่วน:

```mermaid
classDiagram
    class Link {
        +String name
    }
    class Visual {
        +Origin xyz, rpy
        +Geometry (Box, Cylinder, Sphere, Mesh)
        +Material (Color, Texture)
    }
    class Collision {
        +Origin xyz, rpy
        +Geometry (Simplified Primitives)
    }
    class Inertial {
        +Origin xyz, rpy
        +Mass value
        +Inertia (ixx, iyy, izz, ixy, ixz, iyz)
    }

    Link *-- Visual : "ใช้แสดงผลใน RViz2"
    Link *-- Collision : "ใช้ตรวจจับการชนใน Gazebo"
    Link *-- Inertial : "ใช้คำนวณไดนามิกส์ฟิสิกส์"
```

> [!IMPORTANT]
> **กฎเหล็กของ Collision Geometry:** ในซอฟต์แวร์จำลองฟิสิกส์ (Gazebo Sim) ห้ามนำไฟล์ 3D Mesh ที่มีความละเอียดสูง (High-poly CAD) มาใส่ในแท็ก `<collision>` เป็นอันขาด เพราะอัลกอริทึม Collision Solver (เช่น Bullet หรือ DART) จะต้องคำนวณจุดตัดของสามเหลี่ยมหลายหมื่นชิ้นพร้อมกันในทุกๆ คาบเวลา (1 ms) ส่งผลให้ Real-Time Factor (RTF) ดรอปอย่างรุนแรง ควรใช้เฉพาะ **Geometry Primitives** (Box, Cylinder, Sphere) ห่อหุ้มโครงสร้างเท่านั้น

---

### 3. การคำนวณเทนเซอร์ความเฉื่อย (Inertia Tensor Calculation)
เมทริกซ์ความเฉื่อยใน 3 มิติ (Inertia Tensor) แสดงความต้านทานต่อความเร่งเชิงมุมรอบแกนต่างๆ:
$$\mathbf{I} = \begin{bmatrix} I_{xx} & I_{xy} & I_{xz} \\ I_{yx} & I_{yy} & I_{yz} \\ I_{zx} & I_{zy} & I_{zz} \end{bmatrix}$$

สำหรับวัตถุที่มีรูปทรงสมมาตรและมีจุดกำเนิดอยู่ที่จุดศูนย์ถ่วง (Center of Mass: CoM) ค่า Cross-terms จะเป็นศูนย์ ($I_{xy} = I_{xz} = I_{yz} = 0$) เหลือเพียงเส้นทแยงมุมหลัก:

#### ก. กล่องสี่เหลี่ยมตัน (Solid Box): ความยาวแนวแกน X คือ $d$, แกน Y คือ $w$, แกน Z คือ $h$, มวล $m$
$$I_{xx} = \frac{1}{12} m (w^2 + h^2)$$
$$I_{yy} = \frac{1}{12} m (d^2 + h^2)$$
$$I_{zz} = \frac{1}{12} m (d^2 + w^2)$$

#### ข. ทรงกระบอกตัน (Solid Cylinder): รัศมี $r$, ความยาวตามแนวแกนหมุน $h$, มวล $m$
- หากแกนสมมาตรของทรงกระบอกขนานกับแกน Z:
  $$I_{zz} = \frac{1}{2} m r^2, \quad I_{xx} = I_{yy} = \frac{1}{12} m (3r^2 + h^2)$$
- สำหรับล้อขับเคลื่อนหุ่นยนต์ ล้อหมุนรอบแกน Y (Pitch) ดังนั้นแกนสมมาตรคือแกน Y:
  $$I_{yy} = \frac{1}{2} m r^2, \quad I_{xx} = I_{zz} = \frac{1}{12} m (3r^2 + h^2)$$

> [!WARNING]
> **อย่าหมุนแกนซ้ำสองครั้ง (Double Rotation Bug):** ค่า $I_{xx}, I_{yy}, I_{zz}$ ในแท็ก `<inertia>` ถูกตีความในกรอบพิกัดของ `<inertial><origin rpy="...">` เสมอ
> ในโมเดลเวอร์ชันก่อนหน้า ล้อใช้ `<origin rpy="-1.5708 0 0">` ใน `<inertial>` (เหมือนกับ `<visual>`) **และ** ยังใส่ค่าแกนหมุน $\frac{1}{2}mr^2$ ไว้ที่ `iyy` อีก
> ผลคือการหมุนถูกนำมาใช้ 2 ครั้ง: ค่า $0.0024$ ไปตกที่แกน Z ของล้อ ส่วนแกน Y (แกนที่ล้อหมุนจริง) ได้ค่า $0.0013$ ซึ่งผิด
> วิธีที่ถูกเลือกได้ทางเดียว: (ก) ไม่หมุน `<inertial>` (`rpy="0 0 0"`) แล้วใส่ค่าแกนหมุนที่ `iyy` (แบบที่ไฟล์ปัจจุบันใช้) หรือ (ข) หมุน `<inertial>` เหมือน `<visual>` แล้วใส่ค่าแกนหมุนที่ `izz` (แกนสมมาตรของทรงกระบอก)
> สำหรับล้อ $m = 0.75$ kg, $r = 0.08$ m, $h = 0.04$ m: $I_{yy} = 0.0024$, $I_{xx} = I_{zz} = 0.0013\ \text{kg}\cdot\text{m}^2$ — ตรวจสอบอัตโนมัติได้ด้วย `test/test_urdf_model.py::test_wheel_inertia_about_spin_axis`

#### ค. ทรงกลมตัน (Solid Sphere สำหรับ Caster Wheel): รัศมี $r$, มวล $m$
$$I_{xx} = I_{yy} = I_{zz} = \frac{2}{5} m r^2$$

---

### 4. ทฤษฎีแกนขนาน (Parallel Axis Theorem / Steiner's Theorem)
หากจุดหมุนหรือแกนอ้างอิงไม่ได้อยู่ที่จุดศูนย์ถ่วงของวัตถุ (ห่างออกมาเป็นระยะทาง $d$):
$$I = I_{cm} + m d^2$$
สมการนี้ใช้เมื่อเราคำนวณโมเมนต์ความเฉื่อยของชิ้นส่วนที่ติดตั้งเยื้องศูนย์กลางหุ่นยนต์

---

### 5. การทำงานของ `robot_state_publisher`
โหนด `robot_state_publisher` มีบทบาทสำคัญอย่างยิ่งใน ROS 2:
1. รับพารามิเตอร์ `robot_description` ที่บรรจุเนื้อหาไฟล์ URDF
2. สมัครรับข้อมูลท็อปปิก `/joint_states` (`sensor_msgs/msg/JointState`) ซึ่งส่งค่ามุมและระยะเลื่อนของข้อต่อที่เคลื่อนไหวได้
3. คำนวณจลนศาสตร์เดินหน้า (Forward Kinematics) ของทุกๆ ลิงก์ในหุ่นยนต์
4. กระจายผลลัพธ์พิกัด 3 มิติออกไปยังท็อปปิก `/tf` (สำหรับข้อต่อที่มีการขยับ) และ `/tf_static` (สำหรับข้อต่อแบบ fixed)

```mermaid
flowchart LR
    URDF["robot_description<br/>(URDF XML)"] --> RSP["robot_state_publisher"]
    Joints["/joint_states<br/>(wheel positions)"] --> RSP
    RSP -->|Transforms เคลื่อนที่| TF["/tf (Dynamic Transforms)"]
    RSP -->|Transforms คงที่| TFStatic["/tf_static (Latching)"]
```

---

## 🛠️ การวิเคราะห์โค้ดตัวอย่างในโมดูล (Code Walkthrough)

### 1. [`diff_drive_robot.urdf`](urdf/diff_drive_robot.urdf)
- **การกำหนด `base_footprint` และ Joint Offset ([L25-L32](urdf/diff_drive_robot.urdf#L25-L32)):**
  ```xml
  <link name="base_footprint"/>
  <joint name="base_footprint_joint" type="fixed">
    <parent link="base_footprint"/>
    <child link="base_link"/>
    <origin xyz="0 0 0.08" rpy="0 0 0"/>
  </joint>
  ```
  ยกแชสซีขึ้นจากระนาบพื้น $0.08\text{ m}$ ซึ่งเท่ากับรัศมีล้อพอดี ทำให้ล้อแตะพื้นผิวโลกโดยไม่จมหรือลอย
- **การคำนวณและวางแกนล้อขับเคลื่อน ([L58-L97](urdf/diff_drive_robot.urdf#L58-L97)):**
  ```xml
  <joint name="left_wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="left_wheel_link"/>
    <origin xyz="0 0.12 0" rpy="0 0 0"/>
    <axis xyz="0 1 0"/>
  </joint>
  ```
  กำหนดให้ล้อซ้ายอยู่เยื้องศูนย์กลางไปตามแกน Y $+0.12\text{ m}$ (ระยะฐานล้อรวม $L = 0.24\text{ m}$) และหมุนรอบแกน Y ด้วย `<axis xyz="0 1 0"/>`
  ค่า $L = 0.24$ m และรัศมี $r = 0.08$ m ต้องตรงกับ `<wheel_separation>` และ `<wheel_radius>` ของปลั๊กอิน `gz::sim::systems::DiffDrive` ท้ายไฟล์ มิฉะนั้น Odometry ใน Gazebo (สัปดาห์ที่ 10–11) จะคลาดเคลื่อน (มีเทสต์ตรวจให้อัตโนมัติ)
- **การประกอบ Caster Wheel เพื่อพยุงสมดุล ([L140-L198](urdf/diff_drive_robot.urdf#L140-L198)):**
  ใช้ทรงกลมตัน (Sphere Primitive) ขนาดรัศมี $0.03\text{ m}$ ติดตั้งทั้งด้านหน้า ($x = +0.15$) และด้านหลัง ($x = -0.15$) ที่ $z = -0.05$ m ใต้ `base_link` (ศูนย์กลางสูงจากพื้น $0.08 - 0.05 = 0.03$ m = รัศมีพอดี) เพื่อให้หุ่นยนต์ 4 จุดสัมผัสทรงตัวได้อย่างสมบูรณ์

- **Collision ของล้อและค่าแรงเสียดทานสำหรับ Gazebo ([L269-L296](urdf/diff_drive_robot.urdf#L269-L296)):**
  ```xml
  <collision>                       <!-- ใน left/right_wheel_link -->
    <geometry><sphere radius="0.08"/></geometry>
  </collision>
  <gazebo reference="front_caster_link"><mu1>0.0</mu1><mu2>0.0</mu2></gazebo>
  <gazebo reference="left_wheel_link"><mu1>1.0</mu1><mu2>1.0</mu2><kp>1000000.0</kp><kd>100.0</kd></gazebo>
  ```
  `<visual>` ของล้อยังเป็นทรงกระบอก แต่ `<collision>` ใช้ **ทรงกลมรัศมีเท่าล้อ** เพราะทรงกระบอกบนพื้นราบจะสัมผัสพื้นที่ขอบล้อ (ที่ $y = 0.10$ หรือ $0.14$ m) ทำให้ระยะห่างล้อจริงในฟิสิกส์ไม่เท่ากับ $L = 0.24$ m ที่ปลั๊กอิน DiffDrive ใช้คำนวณ Odometry ส่วน Caster ต้องลื่น ($\mu = 0$) มิฉะนั้นลูกกลมจะ "ไถ" ด้านข้างตอนหมุนตัว
  ผลวัดจริงใน Gazebo (หมุนอยู่กับที่ $\omega = 0.6$ rad/s นาน 5 s): ก่อนแก้ `/odom` บอก $165.8^\circ$ แต่หุ่นหมุนจริงเพียง $142.1^\circ$ (คลาด 14%) หลังแก้ตรงกันที่ $169.7^\circ$ — ดู [`results/gz_odometry.txt`](results/gz_odometry.txt) และเทสต์ [`test/test_gz_odometry.py`](test/test_gz_odometry.py) ซึ่งสำคัญมากต่อ SLAM (สัปดาห์ที่ 12) และ AMCL (สัปดาห์ที่ 14–16)

---

### 2. [`display_urdf.launch.py`](launch/display_urdf.launch.py)
- หาไฟล์ URDF/RViz ผ่าน `get_package_share_directory('amr_week07')` (ไม่อ้างพาธแบบ `__file__`) เพื่อให้สัปดาห์ถัดไป (Gazebo, SLAM, Nav2) นำไปใช้ซ้ำได้
- โหลดไฟล์ URDF เข้าสู่พารามิเตอร์ `robot_description` ของโหนด `robot_state_publisher`
- เปิดใช้งานโหนด `joint_state_publisher_gui` เพื่อให้ผู้เรียนสามารถทดลองลาก Slider ปรับหมุนล้อได้แบบ Interactive
- สั่งเปิดโปรแกรมแสดงผลภาพ 3 มิติ RViz2 พร้อมโหลดคอนฟิก [`rviz/robot_model.rviz`](rviz/robot_model.rviz) (RobotModel + TF, Fixed Frame = `base_footprint`)
- Launch arguments:

| อาร์กิวเมนต์ | ค่าเริ่มต้น | ความหมาย |
| :--- | :---: | :--- |
| `model` | `share/amr_week07/urdf/diff_drive_robot.urdf` | พาธไฟล์ URDF |
| `use_gui` | `true` | `true` = `joint_state_publisher_gui` (Slider), `false` = `joint_state_publisher` ธรรมดา |
| `use_jsp` | `true` | `false` = ไม่เปิด joint state publisher เลย (ใช้ตอน Gazebo ส่ง `/joint_states` เอง) |
| `use_sim_time` | `false` | ส่งต่อให้ `robot_state_publisher`, joint state publisher และ RViz2 (ใช้ `true` เมื่อมี `/clock` จาก Gazebo) |
| `rviz` | `true` | `false` = ไม่เปิด RViz2 (เครื่องที่ไม่มีจอ / CI) |

### 3. [`inertia_calculator.py`](src/inertia_calculator.py)
สคริปต์คำนวณเทนเซอร์ความเฉื่อยของ Box / Cylinder / Sphere และพิมพ์แท็ก `<inertia .../>` พร้อมใช้ เช่น `ros2 run amr_week07 inertia_calculator cylinder 0.75 0.08 0.04 --axis y`

### 4. แพ็กเกจ `amr_week07` และการ Build
โฟลเดอร์สัปดาห์นี้เป็นแพ็กเกจ ROS 2 แบบ `ament_python` ชื่อ `amr_week07` (`package.xml`, `setup.py`, `setup.cfg`) ซึ่งติดตั้ง `urdf/`, `launch/`, `rviz/` ไปที่ `share/amr_week07/`:
```bash
./docker/run_lab.sh bash
colcon build --base-paths Essential_ROS --packages-select amr_week07
source install/setup.bash
ros2 launch amr_week07 display_urdf.launch.py
colcon test --base-paths Essential_ROS --packages-select amr_week07 && colcon test-result --verbose
```
ชุดทดสอบใน [`test/`](test/) ตรวจ: `check_urdf` และ `gz sdf -p` ผ่าน, ระยะล้อ/รัศมีตรงกับปลั๊กอิน DiffDrive, เทนเซอร์ความเฉื่อยทุกลิงก์เป็น Positive-definite และผ่าน Triangle inequality, โมเมนต์รอบแกนหมุนล้อ $=\frac{1}{2}mr^2$, ล้อและ Caster แตะพื้นพอดี, LiDAR ตั้งตรงอยู่บนหลังคา, Quaternion ของ `camera_optical_link` $= [-0.5, 0.5, -0.5, 0.5]$ , launch test ที่ยืนยันว่า TF `base_footprint → base_link → lidar_link` และลิงก์ล้อถูกเผยแพร่จริง และเทสต์ฟิสิกส์ Gazebo แบบไม่มีจอ ([`test/test_gz_odometry.py`](test/test_gz_odometry.py) + โลกพื้นราบ [`worlds/flat_ground.sdf`](worlds/flat_ground.sdf)) ที่เทียบ `/odom` ของ DiffDrive กับตำแหน่งจริง (Ground truth) ทั้งการหมุนอยู่กับที่ การเลี้ยวโค้ง (คลาดได้ไม่เกิน 5%) และเส้นตรง (ไม่เกิน 1%)

---

## ⌨️ ตารางคำสั่ง CLI สำคัญ
| คำสั่ง | คำอธิบาย | ตัวอย่างการใช้งาน |
| :--- | :--- | :--- |
| `check_urdf <file.urdf>` | วิเคราะห์ความถูกต้องของโครงสร้าง XML และ Link-Joint Tree | `check_urdf Essential_ROS/Week_07_URDF_Robot_Modeling/urdf/diff_drive_robot.urdf` |
| `urdf_to_graphviz <file.urdf>` | เรนเดอร์แผนผังต้นไม้ความสัมพันธ์ของหุ่นยนต์ออกมาเป็นไฟล์ PDF / Graphviz (ชื่อเก่า `urdf_to_graphiz` ยังใช้ได้แต่ถูก deprecate) | `urdf_to_graphviz Essential_ROS/Week_07_URDF_Robot_Modeling/urdf/diff_drive_robot.urdf` |
| `ros2 launch <pkg> <launch_file>` | รัน Launch file เพื่อเปิดดูหุ่นยนต์ใน RViz2 | `ros2 launch amr_week07 display_urdf.launch.py` (ไม่มีจอ: `use_gui:=false rviz:=false`) |
| `ros2 run amr_week07 inertia_calculator` | คำนวณ $I_{xx}, I_{yy}, I_{zz}$ ของรูปทรงพื้นฐาน | `ros2 run amr_week07 inertia_calculator box 1.2 0.25 0.18 0.05` |
| `ros2 run tf2_ros tf2_echo <p> <c>` | พิมพ์ระยะห่างและมุมหมุนระหว่าง 2 ข้อต่อแบบเรียลไทม์ | `ros2 run tf2_ros tf2_echo base_footprint lidar_link` |

---

## 📟 ผลการรันจริง (Real Run Output)
บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29

ไฟล์ผลลัพธ์ฉบับเต็ม: [`results/check_urdf.txt`](results/check_urdf.txt), [`results/display_urdf_headless.txt`](results/display_urdf_headless.txt), [`results/inertia_calculator.txt`](results/inertia_calculator.txt), [`results/gz_odometry.txt`](results/gz_odometry.txt), [`results/colcon_test.txt`](results/colcon_test.txt)

```console
$ check_urdf Essential_ROS/Week_07_URDF_Robot_Modeling/urdf/diff_drive_robot.urdf
robot name is: diff_drive_robot
---------- Successfully Parsed XML ---------------
root Link: base_footprint has 1 child(ren)
    child(1):  base_link
        child(1):  camera_link
            child(1):  camera_optical_link
        child(2):  front_caster_link
        child(3):  left_wheel_link
        child(4):  lidar_link
        child(5):  rear_caster_link
        child(6):  right_wheel_link
```

TF จาก `robot_state_publisher` (เปิดแบบไม่มีจอ `use_gui:=false rviz:=false`, ตัดบรรทัดที่ซ้ำ):
```console
$ ros2 run tf2_ros tf2_echo base_footprint lidar_link
At time 0.0
- Translation: [0.080, 0.000, 0.175]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
...
$ ros2 run tf2_ros tf2_echo camera_link camera_optical_link
At time 0.0
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [-0.500, 0.500, -0.500, 0.500]
- Rotation: in RPY (radian) [-1.571, -0.000, -1.571]
...
```
$z = 0.175$ m คือ $0.08$ (`base_footprint → base_link`) $+ 0.095$ (`base_link → lidar_link`) และ Quaternion ของกรอบ Optical ตรงกับ REP 103 พอดี

Odometry ของ DiffDrive เทียบตำแหน่งจริงใน Gazebo Sim แบบไม่มีจอ (`gz sim -s` บน `worlds/flat_ground.sdf`, คำสั่ง: หมุน $\omega=0.6$ rad/s / โค้ง $v=0.2$ m/s, $\omega=0.4$ rad/s / ตรง $v=0.3$ m/s อย่างละ 5 s; ค่า dx, dy อยู่ในกรอบหัวหุ่นยนต์ตอนเริ่มท่า):
```console
# BEFORE (git HEAD URDF: cylinder wheel collision, casters with default friction mu=1)
$ python3 Essential_ROS/Week_07_URDF_Robot_Modeling/test/gz_odom_probe.py before.urdf
rotate_in_place  odom: dx=+0.000 dy=+0.000 dyaw= +165.8 deg | truth: dx=+0.000 dy=-0.000 dyaw= +142.1 deg
arc              odom: dx=+0.467 dy=+0.678 dyaw= +110.8 deg | truth: dx=+0.689 dy=+0.380 dyaw=  +37.7 deg
straight         odom: dx=+1.457 dy=+0.000 dyaw=   +0.0 deg | truth: dx=+1.457 dy=+0.000 dyaw=   +0.0 deg

# AFTER (sphere wheel collision, wheel mu=1 kp=1e6 kd=100, frictionless casters)
$ python3 Essential_ROS/Week_07_URDF_Robot_Modeling/test/gz_odom_probe.py
rotate_in_place  odom: dx=+0.000 dy=+0.000 dyaw= +169.7 deg | truth: dx=+0.000 dy=+0.000 dyaw= +169.7 deg
arc              odom: dx=+0.458 dy=+0.700 dyaw= +113.6 deg | truth: dx=+0.458 dy=+0.700 dyaw= +113.6 deg
straight         odom: dx=+1.497 dy=-0.000 dyaw=   -0.0 deg | truth: dx=+1.497 dy=+0.000 dyaw=   +0.0 deg
```

---

## ⚠️ ปัญหาที่พบบ่อยและการแก้ไข (Troubleshooting)

| ที่ | อาการที่พบ (Symptom) | สาเหตุรากเหง้า (Root Cause) | แนวทางแก้ไข (Resolution) |
|:---:| :--- | :--- | :--- |
| 1 | **คำสั่ง `check_urdf` ฟ้อง `XML parsing error` หรือ `Error: link tags must have name`** | ลืมปิดแท็ก XML (เช่น ขาด `</link>`) หรือลืมระบุแอตทริบิวต์ `name="..."` | ตรวจสอบบรรทัดที่คำสั่งแจ้งเตือน และจัดระเบียบการเปิด-ปิดแท็ก XML ให้ครบถ้วน |
| 2 | **ใน RViz2 หุ่นยนต์กลายเป็นสีขาวล้วน และขึ้นสถานะ `No transform from [link] to [fixed_frame]`** | กำหนดค่า `Fixed Frame` ใน RViz2 ผิด หรือโหนด `robot_state_publisher` ยังไม่ได้รัน | เปลี่ยน `Fixed Frame` เป็น `base_footprint` หรือ `base_link` ในหน้าต่าง Displays แถบซ้าย |
| 3 | **หุ่นยนต์จมลงไปใต้ระนาบกริดพื้นใน RViz2 หรือ Gazebo** | ไม่ได้ตั้งค่าพิกัดความสูง $Z$ ของ Joint ระหว่าง `base_footprint` กับ `base_link` ให้สัมพันธ์กับรัศมีล้อ | ตั้งค่า `<origin xyz="0 0 [wheel_radius]" rpy="0 0 0"/>` ใน `base_footprint_joint` |
| 4 | **ส่งคำสั่งหมุนล้อแล้ว ล้อหมุนรอบแกนที่ผิดเพี้ยน (เช่น ล้อหมุนควงสว่าน)** | กำหนดแท็ก `<axis xyz="..."/>` ผิดแกน หรือวางมุม `<origin rpy="..."/>` ของ Geometry ไม่สอดคล้องกัน | กำหนด `<axis xyz="0 1 0"/>` สำหรับการหมุนรอบแกน Y และหมุนทรงกระบอกด้วย `rpy="-1.5708 0 0"` |
| 5 | **โมเดลสั่นหรือระเบิดกระเด็นเมื่อเปิดใน Gazebo Physics** | ค่าในแท็ก `<inertial>` เล็กหรือใหญ่เกินความเป็นจริง (Inertia Matrix Ill-conditioned) หรือลืมใส่แท็ก `<mass>` | คำนวณค่า $I_{xx}, I_{yy}, I_{zz}$ ให้ตรงตามสูตรฟิสิกส์จริง และหลีกเลี่ยงการใส่ค่า 0 ในเส้นทแยงมุมหลัก |
| 6 | **ไฟล์ URDF มีขนาดใหญ่และซ้ำซ้อนจนแก้ไขยาก** | เขียนโค้ด XML ดิบโดยไม่ได้ใช้ Xacro Macro ในการ Reuse โค้ดชิ้นส่วนที่ซ้ำกัน (เช่น ล้อซ้ายและขวา) | พัฒนาต่อยอดด้วย Xacro ในระดับถัดไปเพื่อสร้างเทมเพลตชิ้นส่วน |

---

## 📝 แบบทดสอบท้ายบท (Self-Assessment Quiz)

1. **คำถาม:** สถาปัตยกรรม URDF กำหนดข้อจำกัดเกี่ยวกับโครงสร้างการเชื่อมต่อระหว่าง Link อย่างไร (โครงสร้างแบบวงจรรอบปิดสามารถทำได้หรือไม่)?
2. **คำถาม:** ข้อต่อชนิดใดใน URDF ที่เหมาะสมที่สุดสำหรับล้อขับเคลื่อนของหุ่นยนต์ Differential Drive และเพราะเหตุใดจึงไม่ใช้ชนิด `revolute`?
3. **คำถาม:** จงอธิบายความแตกต่างของบทบาทหน้าที่ระหว่างแท็ก `<visual>` และ `<collision>` ในการจำลองหุ่นยนต์?
4. **คำถาม:** เหตุใดการใส่ค่าโมเมนต์ความเฉื่อยเป็น $0$ ทั้งหมดในแท็ก `<inertial>` จึงทำให้ Physics Simulator (เช่น Gazebo) เกิดข้อผิดพลาดร้ายแรง?
5. **คำถาม:** กำหนดให้ตัวถังหุ่นยนต์ AMR ทรงสี่เหลี่ยมผืนผ้าตันมีขนาด ยาว $d = 0.60\text{ m}$, กว้าง $w = 0.40\text{ m}$, สูง $h = 0.20\text{ m}$, และมวล $m = 12.0\text{ kg}$ จงคำนวณหาโมเมนต์ความเฉื่อยรอบแกนแนวดิ่ง $I_{zz}$?
6. **คำถาม:** ล้อรถยนต์ตันมีมวล $m = 1.0\text{ kg}$ และรัศมี $r = 0.10\text{ m}$ โมเมนต์ความเฉื่อยรอบแกนหมุนของล้อ ($I_{yy}$) มีค่าเท่ากับเท่าใด?
7. **คำถาม:** ตามมาตรฐาน REP 105 ลิงก์ `base_footprint` มีการวางตำแหน่งสัมพัทธ์กับพื้นโลกและตัวหุ่นยนต์อย่างไร?
8. **คำถาม:** โหนด `robot_state_publisher` ต้องการข้อความจากท็อปปิกใดในการคำนวณและเผยแพร่พิกัดของข้อต่อที่เคลื่อนไหวได้ลงบน `/tf`?
9. **คำถาม:** หากต้องการตรวจสอบความถูกต้องของไฟล์ URDF ทางบรรทัดคำสั่งโดยไม่ต้องเปิดโปรแกรมแสดงผล 3 มิติ จะต้องใช้คำสั่งใด?
10. **คำถาม:** ในแท็ก `<joint>` แอตทริบิวต์ `<axis xyz="0 1 0"/>` มีความหมายทางกายภาพอย่างไรตามกฎพิกัดมือขวา?

<details>
<summary>🔍 ดูเฉลยคำตอบพร้อมคำอธิบายอย่างละเอียด</summary>

1. **ตอบ:** URDF กำหนดให้โครงสร้างต้องเป็น **ต้นไม้แบบมีทิศทางที่ไม่มีวงจรรอบปิด (Strict Tree Structure / Directed Acyclic Graph - DAG)** ห้ามมี Loop การเชื่อมต่อชิ้นส่วนวนกลับมาหากันโดยเด็ดขาด หากต้องการจำลองระบบกลไกที่มีวงรอบปิด (Closed Kinematic Chains เช่น 4-Bar Linkage) จะต้องใช้ SDF (Simulation Description Format) ใน Gazebo แทน
2. **ตอบ:** ใช้ชนิด **`continuous`** เนื่องจากล้อรถต้องสามารถหมุนต่อเนื่องได้ไม่จำกัดรอบ ($360^\circ$ วนไปเรื่อยๆ) ในขณะที่ชนิด `revolute` จะมีการล็อกขีดจำกัดมุมการหมุนต่ำสุดและสูงสุดผ่านแท็ก `<limit>` ซึ่งเหมาะกับข้อต่อแขนกลเท่านั้น
3. **ตอบ:**
   - `<visual>`: ใช้สำหรับการแสดงผลทางสายตาบนหน้าจอ RViz2 สามารถใส่สี ลวดลาย (Texture) และไฟล์ 3D Mesh ที่มีความละเอียดสูงเพื่อความสวยงามสมจริง
   - `<collision>`: ใช้สำหรับการคำนวณแรงกระทบและการชนใน Physics Engine ต้องใช้รูปทรงเรขาคณิตพื้นฐานที่เรียบง่าย (Primitives: Box, Cylinder, Sphere) เพื่อลดภาระการประมวลผลทางคณิตศาสตร์
4. **ตอบ:** เนื่องจากสมการพลศาสตร์ของนิวตัน-ออยเลอร์ ($\tau = \mathbf{I}\alpha + \omega \times \mathbf{I}\omega$) ต้องทำการหา **เมทริกซ์ผกผัน (Inertia Matrix Inversion: $\mathbf{I}^{-1}$)** เพื่อคำนวณหาความเร่งเชิงมุม $\alpha = \mathbf{I}^{-1}(\tau - \dots)$ หากใส่ค่าความเฉื่อยเป็นศูนย์ เมทริกซ์จะกลายเป็น Singular (ดีเทอร์มิแนนต์เป็นศูนย์) ไม่สามารถหาอินเวอร์สได้ ทำให้ระบบเกิดข้อผิดพลาด Division by Zero จนโปรแกรมจำลองแครชทันที
5. **ตอบ:**
   - สูตร: $I_{zz} = \frac{1}{12} m (d^2 + w^2)$
   - แทนค่า: $I_{zz} = \frac{1}{12} \times 12.0 \times (0.60^2 + 0.40^2) = 1.0 \times (0.36 + 0.16) = \mathbf{0.52\text{ kg}\cdot\text{m}^2}$
6. **ตอบ:**
   - สูตรทรงกระบอกตันหมุนรอบแกนสมมาตร: $I_{yy} = \frac{1}{2} m r^2$
   - แทนค่า: $I_{yy} = \frac{1}{2} \times 1.0 \times (0.10^2) = 0.5 \times 0.01 = \mathbf{0.005\text{ kg}\cdot\text{m}^2}$
7. **ตอบ:** `base_footprint` จะถูกตรึงไว้ที่ **ระนาบสัมผัสพื้นดินพอดี ($Z = 0$)** โดยมีจุดพิกัด $(X, Y)$ อยู่ตรงกับเงาฉายของจุดศูนย์กลางการหมุนของตัวหุ่นยนต์ เพื่อใช้เป็นระนาบอ้างอิง 2 มิติในการนำทาง
8. **ตอบ:** ท็อปปิก **`/joint_states`** ซึ่งบรรจุข้อความชนิด `sensor_msgs/msg/JointState` ที่ระบุชื่อข้อต่อและตำแหน่งมุมหมุนปัจจุบัน
9. **ตอบ:** คำสั่ง **`check_urdf <path_to_file.urdf>`**
10. **ตอบ:** หมายถึง ข้อต่อนั้นจะ **หมุนรอบแกน Y (Pitch Axis)** โดยทิศทางการหมุนเป็นไปตามกฎมือกำขวา (ทวนเข็มนาฬิกาเมื่อมองจากด้านปลายลูกศรแกน Y เข้าหาจุดกำเนิด)
</details>

---

## 📚 แหล่งอ้างอิงและศึกษาเพิ่มเติม
- [ROS 2 Official Documentation: Building a Visual Robot Model with URDF](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/Building-a-Visual-Robot-Model-with-URDF-from-Scratch.html)
- [URDF XML Specifications Reference](http://wiki.ros.org/urdf/XML)
- [Solid Body Moments of Inertia Formulae](https://en.wikipedia.org/wiki/List_of_moments_of_inertia)
- [REP 120: Coordinate Frames for Humanoids and Mobile Robots](https://www.ros.org/reps/rep-0120.html)
