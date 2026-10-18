# **🛠️ ROS 2 TF2 & Coordinate Transforms - Lab Exercises**

Master coordinate frame transformations, sensor grounding, dynamic odometry streaming, and spatial target tracking in ROS 2 Jazzy.

---

## **📌 Lab Information**

**Lab Title:** Mobile Robot TF2 Broadcaster, Odometry Integration, and Target Tracking  
**Duration:** 2 hours  
**Level:** Intermediate  
**Prerequisites:** Completed `09_TF2/Readme.md`, completed `08_URDF`, familiar with Python geometry & trigonometry

**What You'll Build in This Lab:**
- 📡 **Static Sensor Broadcaster:** Publishes fixed mounting offsets for LiDAR and Camera frames
- 🚀 **Dynamic Odometry Broadcaster:** Simulates differential drive kinematics and streams `odom` ➔ `base_footprint`
- 🎯 **TF Listener & Target Transformer:** Queries relative frames and transforms sensor obstacle detections into global world coordinates
- 🔍 **Diagnostic Pipeline:** Analyzes transform health with `tf2_echo`, `view_frames`, and RViz2

---

## **👤 Authors**

- [@phoori-gh](https://www.github.com/phoori-gh)

---

## **🎯 Learning Objectives**

By completing this lab, you will be able to:
1. **Broadcast** static spatial transformations on `/tf_static` with `StaticTransformBroadcaster`.
2. **Convert** Euler angles into Quaternions using trigonometry and understand REP 103 conventions.
3. **Simulate** 2D robot kinematics and stream dynamic moving transforms on `/tf` at 20 Hz.
4. **Publish** `nav_msgs/msg/Odometry` messages synchronized with TF frames.
5. **Implement** `tf2_ros.Buffer` and `TransformListener` to look up transforms with timeout protection.
6. **Apply** 3D rotation matrices and translations to project obstacle points across coordinate systems.
7. **Inspect** live transform trees using `tf2_echo`, `view_frames`, and RViz2.

---

## **📊 Lab Architecture & Exercise Flow**

```
┌────────────────────────────────────────────────────────┐
│  Exercise 1: Static Sensor TF Broadcaster              │
│  Publish base_link -> laser_frame & camera_link        │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Exercise 2: Dynamic Odometry Kinematics Broadcaster   │
│  Publish odom -> base_footprint (20 Hz) + /odom topic  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Exercise 3: TF Listener & Target Coordinate Tracking  │
│  Transform LiDAR detection into robot & world frames   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Exercise 4: System Integration & CLI Diagnostics      │
│  Run view_frames, tf2_echo, and verify in RViz2        │
└────────────────────────────────────────────────────────┘
```

---

## **Exercise 1: Static Sensor TF Broadcaster 📡**

### **🎯 Objective:**
Create a Python node `static_sensor_tf.py` that broadcasts fixed transforms from `base_link` to `laser_frame` and `camera_link` onto the latched `/tf_static` topic.

### **📐 Specifications:**
1. **LiDAR Frame (`laser_frame`):**
   - Translation: $X = 0.00\text{ m}$, $Y = 0.00\text{ m}$, $Z = 0.095\text{ m}$
   - Orientation: Aligned with body ($\text{Roll} = 0, \text{Pitch} = 0, \text{Yaw} = 0$)
2. **Camera Frame (`camera_link`):**
   - Translation: $X = 0.20\text{ m}$, $Y = 0.00\text{ m}$, $Z = 0.070\text{ m}$
   - Orientation: Facing forward ($\text{Roll} = 0, \text{Pitch} = 0, \text{Yaw} = 0$)
3. **Camera Optical Frame (`camera_optical_frame`):**
   - Translation: $X = 0.00\text{ m}$, $Y = 0.00\text{ m}$, $Z = 0.00\text{ m}$
   - Orientation: $\text{Roll} = -\frac{\pi}{2}$, $\text{Pitch} = 0$, $\text{Yaw} = -\frac{\pi}{2}$

### **💻 Step-by-Step Instructions:**
1. Navigate to your workspace directory:
   ```bash
   cd /Volumes/ExDisk/Google\ Drive\ Ksu/KSU/Git/ROS/1_ROS2/09_TF2/src
   ```
2. Implement the Euler-to-quaternion mathematical helper:
   ```python
   def euler_to_quaternion(roll, pitch, yaw):
       cy = math.cos(yaw * 0.5)
       sy = math.sin(yaw * 0.5)
       cp = math.cos(pitch * 0.5)
       sp = math.sin(pitch * 0.5)
       cr = math.cos(roll * 0.5)
       sr = math.sin(roll * 0.5)
       return (
           sr * cp * cy - cr * sp * sy,
           cr * sp * cy + sr * cp * sy,
           cr * cp * sy - sr * sp * cy,
           cr * cp * cy + sr * cp * sy
       )
   ```
3. Use `StaticTransformBroadcaster(self)` to publish `TransformStamped` messages in a single list.
4. Run the node:
   ```bash
   python3 static_sensor_tf.py
   ```
5. Verify in another terminal:
   ```bash
   ros2 topic echo /tf_static
   ```

---

## **Exercise 2: Dynamic Odometry Kinematics Broadcaster 🚀**

### **🎯 Objective:**
Create a Python node `dynamic_odom_tf.py` that simulates a differential drive robot traversing a circular trajectory and streams continuous transforms from `odom` to `base_footprint` at 20 Hz.

### **📐 Specifications:**
- **Linear Velocity:** $v = 0.25\text{ m/s}$
- **Angular Velocity:** $\omega = 0.20\text{ rad/s}$
- **Update Frequency:** $20\text{ Hz}$ ($\Delta t = 0.05\text{ s}$)
- **Kinematic Integration:**
  $$x_{t+\Delta t} = x_t + v \cos(\theta_t) \Delta t$$
  $$y_{t+\Delta t} = y_t + v \sin(\theta_t) \Delta t$$
  $$\theta_{t+\Delta t} = \theta_t + \omega \Delta t$$
- **Transforms to Broadcast:**
  - Dynamic transform `odom` ➔ `base_footprint` on `/tf`
  - Static transform `base_footprint` ➔ `base_link` ($Z = 0.08\text{ m}$)
- **Odometry Topic:** Publish `nav_msgs/msg/Odometry` on `/odom` with position, quaternion, linear and angular velocities.

### **💻 Testing Command:**
```bash
python3 dynamic_odom_tf.py
```
**Expected Console Output:**
```
[INFO] [dynamic_odom_tf_broadcaster]: 🚀 Dynamic Odom TF Broadcaster started (20 Hz)
[INFO] [dynamic_odom_tf_broadcaster]: 🤖 Robot Pose: X=  0.25m | Y=  0.03m | Yaw=  11.5°
[INFO] [dynamic_odom_tf_broadcaster]: 🤖 Robot Pose: X=  0.48m | Y=  0.11m | Yaw=  23.0°
```

---

## **Exercise 3: TF Listener & Target Coordinate Tracking 🎯**

### **🎯 Objective:**
Create `tf_listener_node.py` that listens to the TF tree, queries the robot's current pose, and converts a sensor obstacle coordinate into world map coordinates.

### **📐 Scenario:**
Your 2D LiDAR scanner detects an obstacle in its local sensor frame at:
$$P_{\text{laser}} = \begin{bmatrix} 1.50\text{ m} \\ 0.30\text{ m} \\ 0.00\text{ m} \end{bmatrix}$$
Calculate:
1. Where is this obstacle located relative to the robot chassis (`base_link`)?
2. Where is this obstacle located in the fixed world room (`odom`)?

### **📐 Transformation Math:**
Given a transform with translation $T = [t_x, t_y, t_z]^T$ and rotation quaternion $q = [x, y, z, w]^T$, the rotated and translated 3D point is:
$$P_{\text{target}} = R(q) \cdot P_{\text{source}} + T$$

Where $R(q)$ is the standard 3x3 rotation matrix:
$$R(q) = \begin{bmatrix}
1 - 2(y^2 + z^2) & 2(xy - zw) & 2(xz + yw) \\
2(xy + zw) & 1 - 2(x^2 + z^2) & 2(yz - xw) \\
2(xz - yw) & 2(yz + xw) & 1 - 2(x^2 + y^2)
\end{bmatrix}$$

### **💻 Testing Command:**
```bash
python3 tf_listener_node.py
```
**Expected Console Output:**
```
[INFO] [tf_listener_node]: ---------------------------------------------------------
[INFO] [tf_listener_node]: 📍 Robot Base (in odom): X=  1.12m, Y=  0.84m, Heading= 36.8°
[INFO] [tf_listener_node]: 🎯 Obstacle (in laser_frame): X=1.50m, Y=0.30m
[INFO] [tf_listener_node]: 🤖 Obstacle (in base_link):   X=1.50m, Y=0.30m
[INFO] [tf_listener_node]: 🗺️ Obstacle (in odom world):  X=2.14m, Y=1.98m
```

---

## **Exercise 4: System Integration & CLI Diagnostics 🔍**

### **🎯 Objective:**
Run the complete TF pipeline across multiple terminals, inspect the active tree, and generate diagnostic documentation.

### **Terminal 1: Static Broadcaster**
```bash
cd /Volumes/ExDisk/Google\ Drive\ Ksu/KSU/Git/ROS/1_ROS2/09_TF2/src
python3 static_sensor_tf.py
```

### **Terminal 2: Dynamic Broadcaster**
```bash
cd /Volumes/ExDisk/Google\ Drive\ Ksu/KSU/Git/ROS/1_ROS2/09_TF2/src
python3 dynamic_odom_tf.py
```

### **Terminal 3: Listener Node**
```bash
cd /Volumes/ExDisk/Google\ Drive\ Ksu/KSU/Git/ROS/1_ROS2/09_TF2/src
python3 tf_listener_node.py
```

### **Terminal 4: Verification Commands**
1. Check live transform between world and sensor:
   ```bash
   ros2 run tf2_ros tf2_echo odom laser_frame
   ```
2. Generate the PDF frame tree:
   ```bash
   ros2 run tf2_tools view_frames
   ```
   Open `frames.pdf` and verify that the complete tree connects from `odom` down to `camera_optical_frame`.
3. Check publication frequencies:
   ```bash
   ros2 run tf2_ros tf2_monitor
   ```

---

## **💯 Evaluation Criteria & Grading Rubric**

| Category | Item Description | Points |
| :--- | :--- | :--- |
| **1. Static Broadcaster Implementation (25 pts)** | Uses `StaticTransformBroadcaster` with `/tf_static` latched topic | 10 |
| | Accurately models LiDAR ($Z = 0.095\text{ m}$) and Camera ($X = 0.20\text{ m}$) offsets | 10 |
| | Implements REP 103 Camera Optical rotation ($\text{Roll}=-\frac{\pi}{2}, \text{Yaw}=-\frac{\pi}{2}$) | 5 |
| **2. Dynamic Odometry Implementation (25 pts)** | Implements 2D differential drive kinematic equations correctly | 10 |
| | Broadcasts moving `odom` ➔ `base_footprint` transform at 20 Hz on `/tf` | 10 |
| | Publishes standard `nav_msgs/msg/Odometry` on `/odom` | 5 |
| **3. TF Listener & Transformation (25 pts)** | Uses `Buffer` and `TransformListener` with timeout and exception catching | 10 |
| | Correctly computes Euler yaw from quaternion | 5 |
| | Correctly applies rotation and translation to transform points between frames | 10 |
| **4. Integration & Diagnostics (15 pts)** | All nodes run concurrently without race conditions or missing frame errors | 10 |
| | Successfully produces complete `frames.pdf` with `view_frames` | 5 |
| **5. Code Quality & Standards (10 pts)** | Clean code formatting, descriptive comments, professional logger output | 10 |
| **Total** | | **100%** |

---

## **💡 Solution Concepts & Node Reference**

Full implementations are provided in the `src/` directory:
- Static Sensor Broadcaster: [`src/static_sensor_tf.py`](src/static_sensor_tf.py)
- Dynamic Odometry Broadcaster: [`src/dynamic_odom_tf.py`](src/dynamic_odom_tf.py)
- TF Listener & Target Tracking: [`src/tf_listener_node.py`](src/tf_listener_node.py)

**Key Takeaways:**
1. Never query TF lookups without exception handling; frames take a few milliseconds to arrive in the buffer at startup.
2. Static transforms should always be broadcasted via `StaticTransformBroadcaster` to save processing power.
3. Keep standard frame conventions in mind: `odom` is the parent of `base_footprint`, which is the parent of `base_link`, which is the parent of sensor links.
