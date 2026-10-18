# **🤖 ROS 2 URDF & Robot Modeling Fundamentals**

Learn how to create comprehensive robot kinematic models using **URDF** (Unified Robot Description Format) and **Xacro**, visualize them in **RViz2**, and bridge real/simulated robot hardware with ROS 2.

---

## **📌 Project Title**

Create, Verify, and Visualize Robot Kinematic Models using URDF & RViz2 in ROS 2 Jazzy

## **👤 Authors**

- [@phoori-gh](https://www.github.com/phoori-gh)

---

## **🛠 Overview**

In ROS 2, a robot cannot navigate, manipulate objects, or process sensor data accurately without a formal mathematical and geometric description of its physical structure. This description is provided by **URDF (Unified Robot Description Format)**.

**What URDF Provides:**
- 📐 **Kinematic Tree:** Defines the hierarchy and spatial relationships of robot parts (Links and Joints)
- 👁️ **Visual Models:** Specifies 3D shapes, colors, and CAD meshes for RViz2 and simulation rendering
- 💥 **Collision Models:** Defines simplified boundary geometries for real-time collision detection and obstacle avoidance
- ⚖️ **Inertial Dynamics:** Specifies mass, center of mass (COM), and moments of inertia for physics simulation (Gazebo, Webots)
- 📡 **Sensor Placements:** Accurately grounds sensors (LiDAR, Camera, IMU) onto the robot coordinate frame

**Key Components Covered in this Module:**
1. **XML & URDF Structure:** `<robot>`, `<link>`, and `<joint>`
2. **Joint Mechanics:** `continuous`, `fixed`, `revolute`, and `prismatic`
3. **Physical Properties:** Visual, Collision, and Inertia calculations
4. **Xacro (XML Macros):** Code reuse, constants, and parametric modeling
5. **ROS 2 Ecosystem Nodes:** `robot_state_publisher`, `joint_state_publisher_gui`, and `rviz2`
6. **Webots Kinematics Synchronization:** Aligning URDF dimensions directly with Webots simulation parameters

**Duration:** ~2.0 hours  
**Level:** Intermediate  
**Prerequisites:** Parameters lab completed, Launch files completed (`07_Launch`)

---

## **🎯 Why URDF Matters in Robotics**

Without URDF:
- A LiDAR sensor publishes distances, but ROS doesn't know where the sensor is mounted relative to the wheels.
- A path planner generates velocity commands without knowing the robot width or wheel spacing.
- RViz displays arbitrary points floating in empty space without a robot body.

With URDF:
```
           LiDAR Scan [laser_frame]
                      │
           (Transform via URDF Joint)
                      ▼
         Robot Center [base_link]
                      │
           (Transform via URDF Joint)
                      ▼
        Contact Plane [base_footprint]
```
`robot_state_publisher` reads your URDF file once and automatically derives all spatial coordinate transforms between your sensors, chassis, and wheels!

---

## **📊 ROS 2 Robot Modeling Architecture**

```
┌────────────────────────────────────────────────────────────────────────┐
│                        diff_drive_robot.urdf                           │
│     (Robot Links, Joint Offsets, Visuals, Collisions, Inertials)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                         Parameter: robot_description
                                    │
                                    ▼
┌─────────────────────────┐                 ┌────────────────────────────┐
│ joint_state_publisher   │                 │   robot_state_publisher    │
│ (or _gui)               ├────────────────►│                            │
│ Topic: /joint_states    │                 │ • Reads robot_description  │
└─────────────────────────┘                 │ • Computes kinematics      │
                                            └─────────────┬──────────────┘
                                                          │
                                                    Topics: /tf & /tf_static
                                                          │
                                                          ▼
                                            ┌────────────────────────────┐
                                            │           RViz2            │
                                            │ (RobotModel + TF Displays) │
                                            └────────────────────────────┘
```

---

## **📐 1. URDF Core Anatomy**

### **1.1 Robot Root Tag**
Every URDF begins and ends with the `<robot>` element:
```xml
<?xml version="1.0"?>
<robot name="diff_drive_robot">
  <!-- Links and joints go here -->
</robot>
```

---

### **1.2 Links: The Rigid Bodies**
A `<link>` represents a rigid body of the robot (such as the chassis, a wheel, or a sensor).

Each link contains three essential sub-elements:

```xml
<link name="chassis_link">
  <!-- 1. Visual: How it looks in RViz -->
  <visual>
    <origin xyz="0 0 0" rpy="0 0 0"/>
    <geometry>
      <box size="0.4 0.2 0.1"/>
    </geometry>
    <material name="blue">
      <color rgba="0.0 0.4 0.8 1.0"/>
    </material>
  </visual>

  <!-- 2. Collision: Geometry for physics collision checking -->
  <collision>
    <origin xyz="0 0 0" rpy="0 0 0"/>
    <geometry>
      <box size="0.4 0.2 0.1"/>
    </geometry>
  </collision>

  <!-- 3. Inertial: Mass and moment of inertia for dynamics -->
  <inertial>
    <origin xyz="0 0 0" rpy="0 0 0"/>
    <mass value="5.0"/>
    <inertia ixx="0.0208" ixy="0.0" ixz="0.0"
             iyy="0.0708" iyz="0.0"
             izz="0.0833"/>
  </inertial>
</link>
```

#### **Supported Geometries in URDF:**
| Geometry | XML Tag | Parameters | Example Use |
| :--- | :--- | :--- | :--- |
| **Box** | `<box size="x y z"/>` | Dimensions in meters along X, Y, Z | Robot chassis, electronics enclosures |
| **Cylinder** | `<cylinder radius="r" length="l"/>` | Radius and height (aligned along Z axis) | Wheels, LiDAR towers, drive shafts |
| **Sphere** | `<sphere radius="r"/>` | Radius in meters | Caster ball wheels |
| **Mesh** | `<mesh filename="package://.../file.stl" scale="1 1 1"/>` | 3D CAD file (`.stl`, `.dae`) | Complex industrial robotic arms |

---

### **1.3 Calculating Moments of Inertia**

Accurate moments of inertia are essential when simulating robots in Webots or Gazebo. Below are the formulas for standard geometric primitives:

1. **Solid Box** (Mass $m$, dimensions $x, y, z$):
   $$I_{xx} = \frac{1}{12} m (y^2 + z^2)$$
   $$I_{yy} = \frac{1}{12} m (x^2 + z^2)$$
   $$I_{zz} = \frac{1}{12} m (x^2 + y^2)$$

2. **Solid Cylinder** (Mass $m$, radius $r$, length $h$ aligned along Z-axis):
   $$I_{xx} = I_{yy} = \frac{1}{12} m (3r^2 + h^2)$$
   $$I_{zz} = \frac{1}{2} m r^2$$

3. **Solid Sphere** (Mass $m$, radius $r$):
   $$I_{xx} = I_{yy} = I_{zz} = \frac{2}{5} m r^2$$

---

### **1.4 Joints: The Kinematic Connectors**
A `<joint>` connects a **parent link** to a **child link**, dictating how the child can move relative to the parent.

```xml
<joint name="left_wheel_joint" type="continuous">
  <parent link="base_link"/>
  <child link="left_wheel_link"/>
  <!-- Spatial location of joint origin relative to parent link frame -->
  <origin xyz="0 0.12 0" rpy="0 0 0"/>
  <!-- Axis of rotation in child link frame -->
  <axis xyz="0 1 0"/>
</joint>
```

#### **Standard Joint Types:**
- **`fixed`**: No relative motion permitted (e.g. sensor mounted on body, chassis assembly)
- **`continuous`**: Continuous rotation around an axis without limit (e.g. robot drive wheels)
- **`revolute`**: Rotation around an axis with strict lower and upper angular limits (e.g. steering knuckles, robot arm joints)
- **`prismatic`**: Linear sliding motion along an axis with distance limits (e.g. elevators, linear actuators)
- **`floating`**: 6-DOF unconstrained motion
- **`planar`**: 2D planar motion in a plane

---

## **⚡ 2. URDF vs. Xacro (XML Macros)**

Plain URDF is purely XML and suffers from code duplication:
- Left wheel and right wheel require identical geometry and inertial definitions.
- Changing the wheel radius requires editing values in dozens of places.

**Xacro** extends URDF with macro programming:
```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="diff_robot">

  <!-- 1. Define Constants / Properties -->
  <xacro:property name="wheel_radius" value="0.08" />
  <xacro:property name="wheel_width" value="0.04" />
  <xacro:property name="wheel_sep" value="0.24" />

  <!-- 2. Define Parametric Macro -->
  <xacro:macro name="wheel" params="prefix y_reflect">
    <link name="${prefix}_wheel_link">
      <visual>
        <origin xyz="0 0 0" rpy="${-pi/2} 0 0"/>
        <geometry>
          <cylinder radius="${wheel_radius}" length="${wheel_width}"/>
        </geometry>
      </visual>
    </link>

    <joint name="${prefix}_wheel_joint" type="continuous">
      <parent link="base_link"/>
      <child link="${prefix}_wheel_link"/>
      <origin xyz="0 ${y_reflect * (wheel_sep / 2)} 0" rpy="0 0 0"/>
      <axis xyz="0 1 0"/>
    </joint>
  </xacro:macro>

  <!-- 3. Instantiate Left and Right Wheels -->
  <xacro:wheel prefix="left" y_reflect="1" />
  <xacro:wheel prefix="right" y_reflect="-1" />

</robot>
```

To convert a `.xacro` file into a pure `.urdf` file for inspection:
```bash
xacro robot.urdf.xacro > robot.urdf
```

---

## **🔗 3. Webots Kinematics Synchronization**

In our course curriculum (`2_Webots`), our differential drive robot possesses the following physical parameters:
- **Wheel Radius:** `0.08 m`
- **Wheel Distance (Separation):** `0.24 m` (Left wheel: `+0.12 m`, Right wheel: `-0.12 m`)
- **Body Dimensions:** `0.40 m` (length X) $\times$ `0.20 m` (width Y) $\times$ `0.10 m` (height Z)
- **Caster Wheels:** Radius `0.04 m` placed at $X = \pm 0.15\text{ m}$
- **LiDAR Sensor:** 360-degree cylinder placed on top of chassis ($Z = 0.095\text{ m}$)
- **RGB Camera:** Front-facing box placed at $X = 0.20\text{ m}$

Our file `src/diff_drive_robot.urdf` matches these exact dimensions!

---

## **🚀 4. Visualizing URDF in RViz2**

To inspect our robot model in RViz2, we use a launch file that starts:
1. `robot_state_publisher`: publishes `/robot_description` and transforms
2. `joint_state_publisher_gui`: opens a GUI slider window to test joint rotations
3. `rviz2`: displays the 3D model

### **Running the Visualization:**
```bash
cd /Volumes/ExDisk/Google\ Drive\ Ksu/KSU/Git/ROS/1_ROS2/08_URDF/src
ros2 launch display_urdf.launch.py
```

### **Manual Command Breakdown (Under the Hood):**
```bash
# Terminal 1: Publish robot model state
ros2 run robot_state_publisher robot_state_publisher --ros-args -p robot_description:="$(cat diff_drive_robot.urdf)"

# Terminal 2: GUI joint state publisher
ros2 run joint_state_publisher_gui joint_state_publisher_gui

# Terminal 3: RViz2
rviz2 -d diff_drive.rviz
```

---

## **🔍 5. Verification & Debugging Tools**

### **5.1 Check URDF Syntax**
Use `check_urdf` to validate the XML syntax and link hierarchy:
```bash
check_urdf diff_drive_robot.urdf
```
**Expected Output:**
```
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

### **5.2 Generate Kinematic Tree Diagram (Graphviz)**
```bash
urdf_to_graphiz diff_drive_robot.urdf
```
This generates `diff_drive_robot.gv` and `diff_drive_robot.pdf`, allowing you to inspect the joint hierarchy visually.

### **5.3 Inspect Live Topics**
```bash
# Verify robot description topic
ros2 topic echo /robot_description --once

# Monitor joint angles published by GUI
ros2 topic echo /joint_states

# Monitor broadcasted transforms
ros2 topic echo /tf
```

---

## **⚠️ Common Pitfalls & Troubleshooting**

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **Model appears white/untextured in RViz2** | Missing `<material>` definition or fixed frame mismatch | Set RViz Fixed Frame to `base_footprint` or `base_link` |
| **"No transform from [link] to [base_link]"** | `robot_state_publisher` is not running or joint has broken link name | Check spelling of `parent` and `child` link names |
| **Wheel spins around wrong axis** | Cylinder geometry not rotated or joint `<axis>` incorrect | Orient cylinder with `rpy="-1.5708 0 0"` and set joint `<axis xyz="0 1 0"/>` |
| **Robot falls through floor in simulation** | Center of mass / collision origin incorrect | Ensure caster wheel contact points align with wheel bottom radius |

---

## **🎓 Summary**

✅ Defined rigid links with Visual, Collision, and Inertial physics properties  
✅ Connected robot links using `fixed` and `continuous` joints  
✅ Aligned coordinate frame origins with standard ROS conventions (REP 103 & REP 105)  
✅ Visualized and manipulated joints interactively in RViz2 with `joint_state_publisher_gui`  
✅ Prepared robot kinematics for autonomous navigation with TF2 and Webots  

---

## **🚀 Next Steps**

Proceed to [`Lab_Exercises.md`](Lab_Exercises.md) to build the Differential Drive URDF model step-by-step from scratch and complete hands-on challenges!
