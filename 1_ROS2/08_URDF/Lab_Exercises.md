# **🛠️ ROS 2 URDF & Robot Modeling - Lab Exercises**

Master kinematic modeling, sensor grounding, and 3D visualization by building a complete Differential Drive Robot with LiDAR and Camera for ROS 2 Jazzy.

---

## **📌 Lab Information**

**Lab Title:** Differential Drive Robot Kinematic Modeling with URDF & RViz2  
**Duration:** 2 hours  
**Level:** Intermediate  
**Prerequisites:** Completed `08_URDF/Readme.md`, familiar with Launch Files (`07_Launch`)

**What You'll Build in This Lab:**
- 🤖 Complete Differential Drive Mobile Robot Model (`diff_drive_robot.urdf`)
- 🛞 Left & Right drive wheels with continuous joint motion
- ⚪ Dual spherical passive caster wheels for ground stability
- 📡 Mounted 360-degree LiDAR scanner link
- 📷 Forward-facing RGB Camera link + Optical standard frame
- 🚀 Interactive launch file with `robot_state_publisher`, `joint_state_publisher_gui`, and RViz2

---

## **👤 Authors**

- [@phoori-gh](https://www.github.com/phoori-gh)

---

## **🎯 Learning Objectives**

By completing this lab, you will be able to:
1. **Design** a standard robotic kinematic tree following ROS REP 103 and REP 105 conventions.
2. **Implement** Links with accurate Visual, Collision, and Inertial physics properties.
3. **Configure** `continuous` and `fixed` Joints with correct spatial origins and rotation axes.
4. **Calibrate** physical dimensions to match realistic mobile robots and Webots simulation parameters ($R = 0.08\text{ m}$, $L = 0.24\text{ m}$).
5. **Construct** camera optical frames aligned with computer vision coordinate standards.
6. **Deploy** automated visualization launch files connecting `robot_state_publisher` and RViz2.
7. **Debug** URDF syntax using `check_urdf` and ROS 2 topic introspection.

---

## **📊 Lab Progression Roadmap**

```
┌────────────────────────────────────────────────────────┐
│  Exercise 1: Base Footprint & Robot Chassis Link       │
│  Ground projection (z=0) & 0.40m x 0.20m x 0.10m Box   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Exercise 2: Differential Drive Wheels Link & Joint    │
│  Continuous joints, wheel_sep = 0.24m, radius = 0.08m  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Exercise 3: Dual Caster Wheels Link & Joint           │
│  Front & rear spherical contact points (radius = 0.04m)│
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Exercise 4: Perception Sensors (LiDAR & Camera)       │
│  Top-mounted 360° LiDAR & Front Camera + Optical Frame │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Exercise 5: Inertia Dynamics & check_urdf Validation  │
│  Calculate moments of inertia & verify kinematic tree  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Exercise 6: RViz2 Display Launch & GUI Interaction    │
│  Launch robot_state_publisher & joint_state_publisher  │
└────────────────────────────────────────────────────────┘
```

---

## **Exercise 1: Base Footprint & Robot Chassis Link 📦**

### **🎯 Objective:**
Establish the base root frame `base_footprint` resting on the floor plane ($Z=0$), and connect `base_link` at wheel axle elevation ($Z=0.08\text{ m}$) with a rectangular body box.

### **📐 Specifications:**
- `base_footprint`: Dummy root link (no visual, no collision) representing ground projection.
- `base_footprint_joint`: `fixed` joint from `base_footprint` to `base_link` with offset `xyz="0 0 0.08"`.
- `base_link`:
  - Visual: Box dimensions $0.40\text{ m (L)} \times 0.20\text{ m (W)} \times 0.10\text{ m (H)}$, material color Light Blue (`rgba="0.1 0.5 0.9 1.0"`).
  - Center offset: `xyz="0 0 0.02"` so chassis bottom sits at $Z = 0.03\text{ m}$ above ground (well clear of floor).
  - Collision: Identical box bounding shape.

### **💻 Implementation Code Chunk:**
```xml
<?xml version="1.0"?>
<robot name="diff_drive_robot">

  <!-- Materials -->
  <material name="chassis_blue">
    <color rgba="0.1 0.5 0.9 1.0"/>
  </material>

  <!-- 1. Base Footprint (Ground plane reference) -->
  <link name="base_footprint"/>

  <joint name="base_footprint_joint" type="fixed">
    <parent link="base_footprint"/>
    <child link="base_link"/>
    <origin xyz="0 0 0.08" rpy="0 0 0"/>
  </joint>

  <!-- 2. Base Link (Chassis body) -->
  <link name="base_link">
    <visual>
      <origin xyz="0 0 0.02" rpy="0 0 0"/>
      <geometry>
        <box size="0.40 0.20 0.10"/>
      </geometry>
      <material name="chassis_blue"/>
    </visual>
    <collision>
      <origin xyz="0 0 0.02" rpy="0 0 0"/>
      <geometry>
        <box size="0.40 0.20 0.10"/>
      </geometry>
    </collision>
  </link>
</robot>
```

---

## **Exercise 2: Differential Drive Wheels Link & Joint 🛞**

### **🎯 Objective:**
Add two drive wheels (Left and Right) configured with `continuous` joints, allowing infinite rotational motion around the robot's transverse pitch/yaw axis.

### **📐 Specifications:**
- **Wheel Radius:** $0.08\text{ m}$
- **Wheel Thickness (Length):** $0.04\text{ m}$
- **Wheel Separation Distance:** $0.24\text{ m}$
  - Left Wheel: $Y = +0.12\text{ m}$
  - Right Wheel: $Y = -0.12\text{ m}$
- **Orientation:** URDF cylinder primitive points along the Z-axis by default. To align the cylinder roll axis with the robot Y-axis, apply roll rotation `rpy="-1.57079632679 0 0"`.
- **Joint Type:** `continuous`
- **Joint Axis:** `xyz="0 1 0"` (rotates around Y-axis)

### **💻 Implementation Code Chunk:**
```xml
  <material name="wheel_dark">
    <color rgba="0.15 0.15 0.15 1.0"/>
  </material>

  <!-- Left Wheel -->
  <link name="left_wheel_link">
    <visual>
      <origin xyz="0 0 0" rpy="-1.57079632679 0 0"/>
      <geometry>
        <cylinder radius="0.08" length="0.04"/>
      </geometry>
      <material name="wheel_dark"/>
    </visual>
    <collision>
      <origin xyz="0 0 0" rpy="-1.57079632679 0 0"/>
      <geometry>
        <cylinder radius="0.08" length="0.04"/>
      </geometry>
    </collision>
  </link>

  <joint name="left_wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="left_wheel_link"/>
    <origin xyz="0 0.12 0" rpy="0 0 0"/>
    <axis xyz="0 1 0"/>
  </joint>

  <!-- Right Wheel -->
  <link name="right_wheel_link">
    <visual>
      <origin xyz="0 0 0" rpy="-1.57079632679 0 0"/>
      <geometry>
        <cylinder radius="0.08" length="0.04"/>
      </geometry>
      <material name="wheel_dark"/>
    </visual>
    <collision>
      <origin xyz="0 0 0" rpy="-1.57079632679 0 0"/>
      <geometry>
        <cylinder radius="0.08" length="0.04"/>
      </geometry>
    </collision>
  </link>

  <joint name="right_wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="right_wheel_link"/>
    <origin xyz="0 -0.12 0" rpy="0 0 0"/>
    <axis xyz="0 1 0"/>
  </joint>
```

---

## **Exercise 3: Dual Caster Wheels Link & Joint ⚪**

### **🎯 Objective:**
Add front and rear passive caster wheels to prevent tipping while maintaining balanced contact with the ground plane.

### **📐 Specifications:**
- **Geometry:** Sphere with radius $R = 0.04\text{ m}$.
- **Vertical Position:** Axle center is at $Z = -0.04\text{ m}$ relative to `base_link`.
  - Since `base_link` is at $Z = +0.08\text{ m}$, the caster center is at $Z = 0.04\text{ m}$, and its lowest contact point is $0.04 - 0.04 = 0.00\text{ m}$ (exact contact with `base_footprint`!).
- **Longitudinal Positions:**
  - Front Caster: $X = +0.15\text{ m}$
  - Rear Caster: $X = -0.15\text{ m}$
- **Joint Type:** `fixed` (simplifies kinematic representation in URDF).

### **💻 Implementation Code Chunk:**
```xml
  <material name="caster_gray">
    <color rgba="0.5 0.5 0.5 1.0"/>
  </material>

  <!-- Front Caster -->
  <link name="front_caster_link">
    <visual>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <sphere radius="0.04"/>
      </geometry>
      <material name="caster_gray"/>
    </visual>
    <collision>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <sphere radius="0.04"/>
      </geometry>
    </collision>
  </link>

  <joint name="front_caster_joint" type="fixed">
    <parent link="base_link"/>
    <child link="front_caster_link"/>
    <origin xyz="0.15 0 -0.04" rpy="0 0 0"/>
  </joint>

  <!-- Rear Caster -->
  <link name="rear_caster_link">
    <visual>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <sphere radius="0.04"/>
      </geometry>
      <material name="caster_gray"/>
    </visual>
    <collision>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <sphere radius="0.04"/>
      </geometry>
    </collision>
  </link>

  <joint name="rear_caster_joint" type="fixed">
    <parent link="base_link"/>
    <child link="rear_caster_link"/>
    <origin xyz="-0.15 0 -0.04" rpy="0 0 0"/>
  </joint>
```

---

## **Exercise 4: Perception Sensors (LiDAR & Camera) 📡📷**

### **🎯 Objective:**
Mount a 360-degree LiDAR scanner on top of the robot chassis and an RGB Camera on the front bumper, including the standard ROS optical frame.

### **📐 Specifications:**
1. **LiDAR Link (`lidar_link`):**
   - Shape: Cylinder (radius $0.04\text{ m}$, height $0.05\text{ m}$, Orange color)
   - Mounted at center top: `xyz="0.0 0 0.095"` relative to `base_link`
   - Joint type: `fixed`
2. **Camera Link (`camera_link`):**
   - Shape: Box ($0.03\text{ m} \times 0.08\text{ m} \times 0.03\text{ m}$, Red color)
   - Mounted at front: `xyz="0.20 0 0.07"` relative to `base_link`
   - Joint type: `fixed`
3. **Camera Optical Link (`camera_optical_link`):**
   - In computer vision conventions (OpenCV / ROS image processing):
     - $+Z$: Forward (into the scene)
     - $+X$: Right
     - $+Y$: Down
   - Rotated from camera frame using `rpy="-1.57079632679 0 -1.57079632679"`.

### **💻 Implementation Code Chunk:**
```xml
  <material name="lidar_orange">
    <color rgba="1.0 0.5 0.0 1.0"/>
  </material>

  <material name="camera_red">
    <color rgba="0.8 0.1 0.1 1.0"/>
  </material>

  <!-- LiDAR Sensor Link -->
  <link name="lidar_link">
    <visual>
      <geometry>
        <cylinder radius="0.04" length="0.05"/>
      </geometry>
      <material name="lidar_orange"/>
    </visual>
    <collision>
      <geometry>
        <cylinder radius="0.04" length="0.05"/>
      </geometry>
    </collision>
  </link>

  <joint name="lidar_joint" type="fixed">
    <parent link="base_link"/>
    <child link="lidar_link"/>
    <origin xyz="0.0 0 0.095" rpy="0 0 0"/>
  </joint>

  <!-- Camera Sensor Link -->
  <link name="camera_link">
    <visual>
      <geometry>
        <box size="0.03 0.08 0.03"/>
      </geometry>
      <material name="camera_red"/>
    </visual>
    <collision>
      <geometry>
        <box size="0.03 0.08 0.03"/>
      </geometry>
    </collision>
  </link>

  <joint name="camera_joint" type="fixed">
    <parent link="base_link"/>
    <child link="camera_link"/>
    <origin xyz="0.20 0 0.07" rpy="0 0 0"/>
  </joint>

  <!-- Camera Optical Frame -->
  <link name="camera_optical_link"/>

  <joint name="camera_optical_joint" type="fixed">
    <parent link="camera_link"/>
    <child link="camera_optical_link"/>
    <origin xyz="0 0 0" rpy="-1.57079632679 0 -1.57079632679"/>
  </joint>
```

---

## **Exercise 5: Inertia Dynamics & `check_urdf` Validation ⚖️**

### **🎯 Objective:**
Add realistic inertial tensors to all physical links and validate the syntactic structure using command-line tools.

### **Inertia Matrix Reference:**
```xml
<!-- Example: Chassis (Mass: 5.0 kg, Size: 0.40 x 0.20 x 0.10) -->
<inertial>
  <origin xyz="0 0 0.02" rpy="0 0 0"/>
  <mass value="5.0"/>
  <inertia ixx="0.020833" ixy="0.0" ixz="0.0"
           iyy="0.070833" iyz="0.0"
           izz="0.083333"/>
</inertial>
```

### **Validation Command:**
```bash
check_urdf diff_drive_robot.urdf
```
Verify that the output displays:
```
robot name is: diff_drive_robot
---------- Successfully Parsed XML ---------------
```

---

## **Exercise 6: RViz2 Display Launch & GUI Interaction 🚀**

### **🎯 Objective:**
Launch the complete visualization pipeline using `display_urdf.launch.py`.

```bash
cd /Volumes/ExDisk/Google\ Drive\ Ksu/KSU/Git/ROS/1_ROS2/08_URDF/src
ros2 launch display_urdf.launch.py
```

### **Interactive Verification Checklist:**
1. Open RViz2 window.
2. Verify that **Fixed Frame** is set to `base_footprint`.
3. Locate the **Joint State Publisher** floating GUI window.
4. Move the sliders for `left_wheel_joint` and `right_wheel_joint`:
   - Both wheels should rotate smoothly in RViz2 without detaching from the chassis.
5. In RViz2 Displays panel, expand **TF**:
   - Verify all frames (`base_footprint`, `base_link`, `left_wheel_link`, `right_wheel_link`, `lidar_link`, `camera_link`, `camera_optical_link`) are active and connected.

---

## **💯 Evaluation Criteria & Grading Rubric**

| Category | Item Description | Points |
| :--- | :--- | :--- |
| **1. Kinematic Tree Structure (20 pts)** | Correct parent-child hierarchy from `base_footprint` to all child links without circular dependencies | 10 |
| | Proper joint naming (`*_joint`) and link naming (`*_link`) adhering to ROS naming conventions | 10 |
| **2. Dimensional Accuracy (20 pts)** | Wheel radius ($0.08\text{ m}$) and wheel separation ($0.24\text{ m}$) accurately implemented | 10 |
| | Chassis size ($0.40 \times 0.20 \times 0.10\text{ m}$) and caster wheels ground tangent ($Z=0$) | 10 |
| **3. Joint Specifications (20 pts)** | Wheels configured as `continuous` with correct rotation axis `[0, 1, 0]` | 10 |
| | Casters and sensors configured as `fixed` with appropriate spatial origins | 10 |
| **4. Sensor & Optical Frames (15 pts)** | LiDAR link positioned elevated on chassis top | 5 |
| | Camera link positioned forward facing on front bumper | 5 |
| | `camera_optical_link` oriented correctly with standard camera rotation matrix | 5 |
| **5. Inertial & Physics (15 pts)** | Mass and positive-definite inertia matrix defined for every rigid link | 10 |
| | Passes syntax validation with `check_urdf` without warnings | 5 |
| **6. Launch & Visualization (10 pts)** | Launch file runs `robot_state_publisher`, `joint_state_publisher_gui`, and `rviz2` cleanly | 10 |
| **Total** | | **100%** |

---

## **💡 Solution Concepts & Complete Model Reference**

The complete, fully-tested URDF model and launch configuration are available in:
- Model URDF: [`src/diff_drive_robot.urdf`](src/diff_drive_robot.urdf)
- Launch File: [`src/display_urdf.launch.py`](src/display_urdf.launch.py)
- RViz Configuration: [`src/diff_drive.rviz`](src/diff_drive.rviz)

**Key Takeaways:**
1. Always start the kinematic chain from `base_footprint` to give the navigation stack a 2D floor projection.
2. In ROS URDF, a cylinder primitive is oriented along the Z-axis; always apply a $\pm \frac{\pi}{2}$ roll rotation to orient it as a drive wheel along the Y-axis.
3. Optical frames must have their $+Z$ axis pointing out through the lens toward the scene to comply with sensor message conventions.
