# **🧭 ROS 2 TF2 & Coordinate Frames Fundamentals**

Master spatial coordinate transformations, standard robotic frame conventions (REP 105 & REP 103), quaternion mathematics, and the **TF2** transform library in **ROS 2 Jazzy**.

---

## **📌 Project Title**

Coordinate Transformations, Broadcasters, and Frame Listeners using ROS 2 TF2

## **👤 Authors**

- [@phoori-gh](https://www.github.com/phoori-gh)

---

## **🛠 Overview**

In any autonomous mobile robot, different sensors and actuators operate in different physical locations and orientations:
- A **LiDAR** detects an obstacle 2 meters ahead of *its own lens*.
- A **camera** detects an object in pixels with optical coordinates (Z forward, X right, Y down).
- The **wheels** move relative to the robot's drive axle.
- The **robot chassis** moves relative to the room floor.
- The **global planner** plans paths in a map coordinate system.

To combine sensor readings and navigate without collisions, the robot must constantly answer:
> *"Where is this sensor point located relative to the robot chassis and relative to the global map right now?"*

The ROS 2 **TF2 (Transform 2)** library solves this problem by maintaining a dynamic, time-buffered tree of coordinate frames and providing mathematical transformations between any two frames at any point in time.

**Key Topics Covered in this Module:**
1. **REP 105 Standard Frame Hierarchy:** `map` ➔ `odom` ➔ `base_footprint` ➔ `base_link` ➔ `sensors`
2. **REP 103 Conventions:** Right-hand coordinate system (X forward, Y left, Z up)
3. **Euler Angles vs. Quaternions:** Why robotics uses quaternions, avoiding Gimbal Lock, and conversion formulas
4. **TF2 Broadcasters:** `StaticTransformBroadcaster` (latched `/tf_static`) vs `TransformBroadcaster` (streaming `/tf`)
5. **TF2 Listeners & Buffers:** `Buffer` caching and `lookup_transform` query APIs
6. **CLI Inspection Tools:** `view_frames`, `tf2_echo`, `tf2_monitor`, and RViz2 visualization

**Duration:** ~2.0 hours  
**Level:** Intermediate  
**Prerequisites:** Robot Modeling completed (`08_URDF`), Parameters completed (`05_Parameters`), Launch files completed (`07_Launch`)

---

## **🌲 1. ROS Standard Coordinate Frame Tree (REP 105)**

ROS standards dictate a standardized kinematic tree for mobile robots:

```
                  ┌──────────────────────┐
                  │         map          │  <-- Global World Frame (Drift-free, SLAM/GPS)
                  └──────────┬───────────┘
                             │
                             ▼  (Published by Localization / SLAM node)
                  ┌──────────────────────┐
                  │         odom         │  <-- Local Odometry Frame (Smooth, Continuous, Drifts)
                  └──────────┬───────────┘
                             │
                             ▼  (Published by Wheel Odometry / IMU Broadcaster)
                  ┌──────────────────────┐
                  │    base_footprint    │  <-- 2D Floor Projection (Z = 0, Roll = 0, Pitch = 0)
                  └──────────┬───────────┘
                             │
                             ▼  (Fixed vertical elevation = wheel radius)
                  ┌──────────────────────┐
                  │      base_link       │  <-- Robot Chassis Origin (Axle center)
                  └─────┬──────────┬─────┘
                        │          │
        ┌───────────────┘          └───────────────┐
        ▼ (Static TF)                              ▼ (Static TF)
┌──────────────┐                          ┌─────────────────┐
│ laser_frame  │                          │   camera_link   │
└──────────────┘                          └────────┬────────┘
                                                   │
                                                   ▼ (Static TF - REP 103)
                                          ┌──────────────────────┐
                                          │ camera_optical_frame │
                                          └──────────────────────┘
```

### **Coordinate Frame Definitions:**
| Frame Name | Type | Characteristics & Role | Publisher |
| :--- | :--- | :--- | :--- |
| **`map`** | World Fixed | Global reference frame. Coordinates do not drift over time. May experience discrete "jumps" when SLAM makes loop closures or GPS fixes. | SLAM / Cartographer / AMCL |
| **`odom`** | World Fixed | Local continuous frame. Position is smooth and continuous without jumps, but accumulates wheel slip drift over time. Essential for local collision avoidance. | Wheel Odometry / EKF Filter |
| **`base_footprint`**| Robot Relative | 2D projection of the robot body directly onto the ground plane ($Z = 0$). Used by Nav2 for 2D footprint costmaps. | Robot Odometry Broadcaster |
| **`base_link`** | Robot Relative | Center of rotation of the robot body (usually the center of the drive axle). Rigidly attached to the chassis. | Robot State Publisher / Broadcaster |
| **`laser_frame`** | Sensor Relative | Origin of the LiDAR scan optical center. Fixed relative to `base_link`. | Static TF Broadcaster / URDF |
| **`camera_link`** | Sensor Relative | Physical center of the camera housing. | Static TF Broadcaster / URDF |
| **`camera_optical_frame`** | Sensor Relative | Optical axis convention: $+Z$ through lens, $+X$ right, $+Y$ down (used by OpenCV / point clouds). | Static TF Broadcaster / URDF |

---

## **🔄 2. Orientations: Euler Angles vs. Quaternions**

### **The Problem with Euler Angles (Roll, Pitch, Yaw):**
Euler angles represent 3D orientation as three sequential rotations around axes (e.g. Yaw around Z, Pitch around Y, Roll around X).
- **Gimbal Lock:** When pitch reaches $\pm 90^\circ$ ($\pm \frac{\pi}{2}$ rad), the roll and yaw axes align, causing a catastrophic loss of one rotational degree of freedom.
- **Ambiguity:** Multiple combinations of Euler angles represent the exact same 3D orientation.
- **Interpolation issues:** You cannot smoothly interpolate between two Euler angles without artifacts.

### **The Robotics Solution: Quaternions ($x, y, z, w$):**
A quaternion is a 4-dimensional hypercomplex number on a unit sphere:
$$q = x\mathbf{i} + y\mathbf{j} + z\mathbf{k} + w$$
where:
$$x^2 + y^2 + z^2 + w^2 = 1.0$$

Quaternions completely eliminate Gimbal Lock, allow smooth spherical linear interpolation (SLERP), and can be multiplied directly to chain rotations.

### **Conversion: Euler (Roll $\phi$, Pitch $\theta$, Yaw $\psi$) to Quaternion:**
$$\begin{aligned}
x &= \sin(\phi/2)\cos(\theta/2)\cos(\psi/2) - \cos(\phi/2)\sin(\theta/2)\sin(\psi/2) \\
y &= \cos(\phi/2)\sin(\theta/2)\cos(\psi/2) + \sin(\phi/2)\cos(\theta/2)\sin(\psi/2) \\
z &= \cos(\phi/2)\cos(\theta/2)\sin(\psi/2) - \sin(\phi/2)\sin(\theta/2)\cos(\psi/2) \\
w &= \cos(\phi/2)\cos(\theta/2)\cos(\psi/2) + \sin(\phi/2)\sin(\theta/2)\sin(\psi/2)
\end{aligned}$$

For a planar 2D mobile robot moving on a flat floor ($\text{roll} = 0$, $\text{pitch} = 0$, $\text{yaw} = \psi$):
$$x = 0,\quad y = 0,\quad z = \sin(\psi/2),\quad w = \cos(\psi/2)$$

### **Conversion: Quaternion to Yaw ($\psi$):**
$$\psi = \text{atan2}(2(w z + x y),\; 1 - 2(y^2 + z^2))$$

---

## **📡 3. TF2 Architecture in ROS 2**

TF2 separates transforms into two distinct publication streams:

### **3.1 Static Transforms (`/tf_static` topic)**
- Used for transforms that **do not change over time** (e.g. LiDAR bracket bolted to the robot chassis, camera mount).
- Broadcasted using `tf2_ros.StaticTransformBroadcaster`.
- **Latched topic (QoS Transient Local):** The broadcaster publishes once or when changes occur. New subscriber nodes immediately receive the cached transform upon connecting, saving enormous CPU and network bandwidth.

### **3.2 Dynamic Transforms (`/tf` topic)**
- Used for frames that **move dynamically** (e.g. `odom` ➔ `base_footprint`, wheel rotations).
- Broadcasted using `tf2_ros.TransformBroadcaster`.
- Streamed continuously at high rates (typically 20 Hz to 100 Hz).

### **3.3 Transform Buffer & Listener**
- `tf2_ros.Buffer`: Maintains an in-memory sliding time window (default 10.0 seconds) of all transforms received across `/tf` and `/tf_static`.
- `tf2_ros.TransformListener`: Subscribes to `/tf` and `/tf_static` and automatically inserts messages into the `Buffer`.
- `lookup_transform(target_frame, source_frame, time, timeout)`: Traverses the transform tree to compute the relative transform between any two frames.

---

## **💻 4. Code Examples & Workflow**

Our `src/` directory contains three complete, standalone nodes demonstrating the entire TF2 pipeline:

### **Node 1: Static Sensor Broadcaster (`static_sensor_tf.py`)**
Broadcasts fixed geometric relationships from `base_link` to `laser_frame` and `camera_link`:
```python
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster
from geometry_msgs.msg import TransformStamped

class StaticSensorTFBroadcaster(Node):
    def __init__(self):
        super().__init__('static_sensor_tf_broadcaster')
        self.tf_static_broadcaster = StaticTransformBroadcaster(self)

        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'base_link'
        t.child_frame_id = 'laser_frame'
        t.transform.translation.z = 0.095
        t.transform.rotation.w = 1.0  # Zero rotation

        self.tf_static_broadcaster.sendTransform(t)
```

### **Node 2: Dynamic Odometry Broadcaster (`dynamic_odom_tf.py`)**
Simulates mobile robot kinematics and streams moving coordinates to `/tf`:
```python
from tf2_ros import TransformBroadcaster

class DynamicOdomTFBroadcaster(Node):
    def __init__(self):
        super().__init__('dynamic_odom_tf_broadcaster')
        self.tf_broadcaster = TransformBroadcaster(self)
        self.timer = self.create_timer(0.05, self.broadcast_odometry)

    def broadcast_odometry(self):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_footprint'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.rotation.z = math.sin(self.theta / 2.0)
        t.transform.rotation.w = math.cos(self.theta / 2.0)
        self.tf_broadcaster.sendTransform(t)
```

### **Node 3: TF Listener & Target Transformation (`tf_listener_node.py`)**
Queries the transform tree to translate a sensor-detected obstacle into world coordinates:
```python
import tf2_ros

class TFListenerNode(Node):
    def __init__(self):
        super().__init__('tf_listener_node')
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.timer = self.create_timer(1.0, self.query_transform)

    def query_transform(self):
        try:
            # Query latest transform from 'laser_frame' to 'odom'
            transform = self.tf_buffer.lookup_transform(
                target_frame='odom',
                source_frame='laser_frame',
                time=rclpy.time.Time()
            )
            # Transform point coordinates into odom frame...
        except tf2_ros.TransformException as ex:
            self.get_logger().warn(f'Could not transform: {ex}')
```

---

## **🔍 5. Command-Line Inspection & Diagnostic Tools**

ROS 2 provides powerful CLI tools to inspect, verify, and debug your transform tree:

### **5.1 Echo Transforms in Real Time (`tf2_echo`)**
Prints the translation and rotation between any two coordinate frames:
```bash
ros2 run tf2_ros tf2_echo odom laser_frame
```
**Example Output:**
```
At time 1739080000.123456789
- Translation: [1.250, 0.850, 0.175]
- Rotation: in Quaternion [0.000, 0.000, 0.382, 0.924]
- Rotation: in RPY (radian) [0.000, -0.000, 0.785]
- Rotation: in RPY (degree) [0.000, -0.000, 45.000]
```

### **5.2 Generate Frame Tree PDF Diagram (`view_frames`)**
Captures a snapshot of all active frames and generates a visual PDF tree diagram:
```bash
ros2 run tf2_tools view_frames
```
This generates `frames.pdf` showing:
- Parent-child linkages
- Broadcaster node names
- Average transform update rates (Hz)
- Buffer ages and delay times

### **5.3 Monitor TF Health & Delays (`tf2_monitor`)**
```bash
ros2 run tf2_ros tf2_monitor
```
Reports whether transforms are being dropped, delayed, or published with excessive jitter.

---

## **⚠️ Common Pitfalls & Troubleshooting**

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **"Lookup would require extrapolation into the future"** | Clock mismatch or requesting `Time.now()` before transform arrived in buffer | Use `rclpy.time.Time()` (time 0) to request the newest transform, or add a timeout e.g. `Duration(seconds=0.1)` |
| **"Frame [target] does not exist"** | Typo in frame string or broadcaster hasn't started yet | Check frame names with `ros2 run tf2_ros tf2_echo` and ensure broadcaster is spinning |
| **TF Tree Disconnected ("No path between frames")** | Missing intermediate transform (e.g. `base_footprint` to `base_link`) | Run `view_frames` to locate which link in the tree chain is missing |
| **Sensors jump or oscillate violently** | Multiple nodes publishing contradictory transforms for the same parent-child pair | Ensure only ONE node broadcasts a specific frame relationship |
| **Inverted Translations** | Inverted target and source arguments in `lookup_transform` | Remember: `lookup_transform(target, source)` gives the pose of `source` expressed in `target`'s frame |

---

## **🎓 Summary**

✅ Implemented standard REP 105 mobile robot coordinate frame conventions  
✅ Understood quaternions and avoided Gimbal Lock in 3D rotations  
✅ Broadcasted latched static transforms using `StaticTransformBroadcaster`  
✅ Streamed high-frequency dynamic odometry using `TransformBroadcaster`  
✅ Queried transforms and computed spatial projections using `Buffer` and `TransformListener`  
✅ Inspected and debugged transform trees with `tf2_echo`, `view_frames`, and RViz2  

---

## **🚀 Next Steps**

Proceed to [`Lab_Exercises.md`](Lab_Exercises.md) for step-by-step hands-on exercises to build, test, and integrate the full TF2 pipeline!
