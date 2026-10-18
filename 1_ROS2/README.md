# 📚 ROS 2 Core Concepts & Tutorials

Master the fundamentals of **ROS 2 Jazzy** middleware with progressive hands-on tutorials covering publishers, subscribers, services, actions, and more.

## 📖 Tutorial Roadmap

Learn ROS 2 concepts in order, building from basic message passing to advanced system coordination:

### 📦 **00_Install** - Environment Setup
**Prerequisites & Installation Guide**
- ROS 2 Jazzy distribution installation
- Python 3.10+ environment setup
- Development tools and dependencies
- Verification and troubleshooting

[👉 Go to 00_Install →](00_Install/Readme.md)

---

### 🔄 **01_Publisher_Subscriber** - Message Passing Fundamentals
**Core Concept:** Asynchronous one-way communication between nodes

Learn how to:
- Create publisher nodes that send data
- Create subscriber nodes that receive data
- Use ROS 2 topics for data distribution
- Handle different message types
- Manage node lifecycle

**Key Examples:**
- `simple_publisher.py` - Basic publisher
- `simple_subscriber.py` - Basic subscriber
- `counter_publisher.py` - Publishing counter data
- `sensor_monitor.py` - Multi-sensor monitoring

**What You'll Build:**
- Publish sensor readings to topics
- Subscribe to multiple topics simultaneously
- Process real-time data streams

[👉 Go to 01_Publisher_Subscriber →](01_Publisher_Subscriber/Readme.md)

---

### 🔗 **02_Server_Client** - Request-Response Pattern
**Core Concept:** Synchronous bidirectional communication between nodes

Learn how to:
- Create service servers that respond to requests
- Create service clients that make requests
- Define service interfaces
- Handle blocking and non-blocking calls
- Implement complex request-response workflows

**Key Examples:**
- `add_two_ints_server.py` - Simple arithmetic service
- `add_two_ints_client.py` - Service client
- `database_server.py` - Persistent data service
- `robot_controller_server.py` - Robot command service

**What You'll Build:**
- Remote procedure calls between nodes
- Database query services
- Robot command interfaces
- Configuration services

[👉 Go to 02_Server_Client →](02_Server_Client/Readme.md)

---

### 💬 **03_Message** - Custom Message Types
**Core Concept:** Define structured data formats for communication

Learn how to:
- Design custom message structures (.msg files)
- Compile message definitions
- Use complex nested messages
- Handle arrays and variable-length data
- Work with timestamps and coordinate frames

**Key Examples:**
- `HardwareStatus.msg` - Hardware status message
- `RobotStatus.msg` - Robot state message
- `HardwareStatus_publish.py` - Publish custom messages
- `RobotStatus_safety_monitor.py` - Monitor custom messages

**What You'll Build:**
- Robot status messages with multiple fields
- Hardware telemetry structures
- Complex data hierarchies
- Type-safe communication protocols

[👉 Go to 03_Message →](03_Message/Readme.md)

---

### ⚙️ **04_Service** - Service Definition
**Core Concept:** Define request-response interfaces with custom types

Learn how to:
- Create service definitions (.srv files)
- Implement typed services
- Handle service request validation
- Implement error handling in services
- Create complex service workflows

**Key Examples:**
- `CalRectangle.srv` - Geometry calculation service
- `CalRect_server.py` - Rectangle calculation service
- `CalRect_client.py` - Service client
- `gripper_control_server.py` - Hardware control service

**What You'll Build:**
- Geometry calculation services
- Hardware control interfaces
- Computation services
- State management services

[👉 Go to 04_Service →](04_Service/Readme.md)

---

### ⚙️ **05_Parameters** - Dynamic Configuration
**Core Concept:** Runtime-adjustable node parameters

Learn how to:
- Declare and manage node parameters
- Set parameters at launch time
- Modify parameters at runtime
- Listen for parameter changes
- Validate parameter values
- Use parameter files (YAML)

**Key Examples:**
- `robot_config.yaml` - Configuration file
- `fleet_config.yaml` - Multi-robot configuration
- `robot_tag_publisher.py` - Basic parameter publisher
- `robot_tag_callback_pub.py` - Parameter change callbacks
- `robot_tag_validated_pub.py` - Parameter validation

**What You'll Build:**
- Configurable robot behavior
- Multi-robot fleet configuration
- Parameter validation systems
- Dynamic reconfiguration workflows

[👉 Go to 05_Parameters →](05_Parameters/Readme.md)

---

### 🎯 **06_Action** - Long-Running Tasks
**Core Concept:** Goal-oriented asynchronous communication with feedback

Learn how to:
- Create action servers that execute goals
- Create action clients that request goals
- Handle goal feedback during execution
- Implement goal cancellation
- Track goal progress and results
- Handle multiple concurrent goals

**Key Examples:**
- `count_until_server.py` - Counting action
- `count_until_client.py` - Action client
- `battery_charging_server.py` - Charging action
- `gripper_client.py` - Gripper control action
- `navigate_server.py` - Navigation action

**What You'll Build:**
- Robot navigation tasks
- Battery charging workflows
- Gripper control sequences
- Progress-trackable long-running operations
- Complex multi-step robot behaviors

[👉 Go to 06_Action →](06_Action/Readme.md)

---

### 🚀 **07_Launch** - System Composition
**Core Concept:** Launch multiple nodes with coordinated configuration

Learn how to:
- Create launch files for multi-node systems
- Pass arguments to launch files
- Set parameters during launch
- Remap topics between nodes
- Manage node namespaces
- Create launch hierarchies
- Debug launch configurations

**Key Examples:**
- Launch files for complete robot systems
- Multi-node application coordination
- Environment-specific configurations
- Conditional launch logic

**What You'll Build:**
- Complete robotic systems from multiple nodes
- Dev/test/production configurations
- Reusable launch file libraries
- Complex application orchestration

[👉 Go to 07_Launch →](07_Launch/Readme.md)

---

### 🤖 **08_URDF** - Robot Kinematic Modeling
**Core Concept:** Unified Robot Description Format for physical robot structure and visualization

Learn how to:
- Define robot links, visual appearance, collisions, and moments of inertia
- Connect links using joints (`continuous`, `fixed`, `revolute`, `prismatic`)
- Convert and optimize robot models using Xacro macros
- Run `robot_state_publisher` and `joint_state_publisher_gui`
- Visualize 3D robot models and TF coordinate frames in RViz2
- Match physical dimensions with Webots simulation parameters

**Key Examples:**
- `diff_drive_robot.urdf` - Complete 2-wheel + dual caster + LiDAR + Camera robot
- `display_urdf.launch.py` - Launch file for robot visualization in RViz2
- `diff_drive.rviz` - Default RViz2 configuration

**What You'll Build:**
- Differential drive mobile robot URDF matching Webots simulation
- Multi-sensor kinematic grounding (360° LiDAR and RGB Camera)
- Interactive joint control with GUI sliders
- Complete visualization pipeline

[👉 Go to 08_URDF →](08_URDF/Readme.md)

---

### 🧭 **09_TF2** - Coordinate Transforms & Tracking
**Core Concept:** Spatial coordinate transformations and frame tracking over time

Learn how to:
- Follow standard ROS coordinate conventions (REP 105: map → odom → base_footprint → base_link)
- Apply right-hand coordinate frames and optical camera frame standards (REP 103)
- Understand Euler angles vs. Quaternions and eliminate Gimbal Lock
- Broadcast static transforms with `StaticTransformBroadcaster`
- Stream dynamic odometry transforms with `TransformBroadcaster`
- Buffer and query spatial transforms with `tf2_ros.Buffer` and `TransformListener`
- Use CLI tools: `tf2_echo`, `view_frames`, and `tf2_monitor`

**Key Examples:**
- `static_sensor_tf.py` - Static broadcaster for LiDAR and Camera frames
- `dynamic_odom_tf.py` - Kinematic simulation and dynamic odometry broadcaster
- `tf_listener_node.py` - Listener node transforming sensor obstacle points

**What You'll Build:**
- Sensor coordinate transform broadcaster
- High-frequency dynamic odometry publisher (20 Hz)
- Sensor target coordinate transformer (sensor frame → robot chassis → world frame)
- Frame tree validation with PDF visualization

[👉 Go to 09_TF2 →](09_TF2/Readme.md)

---

## 📚 Learning Progression

```
00_Install (Foundation)
    ↓
01_Publisher_Subscriber (Async 1-way)
    ↓
02_Server_Client (Sync Request-Response)
    ↓
03_Message (Custom Types)
    ↓
04_Service (Typed Services)
    ↓
05_Parameters (Configuration)
    ↓
06_Action (Goal-Oriented)
    ↓
07_Launch (System Composition)
    ↓
08_URDF (Robot Kinematic Modeling)
    ↓
09_TF2 (Transformations & Frames)
```

---

## 🛠 Technology Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| ROS 2 | Jazzy | Middleware framework |
| Python | 3.10+ | Programming language |
| Ubuntu | 22.04 LTS | Operating system |
| DDS | CycloneDDS | Communication middleware |

---

## ⚡ Quick Start

### Prerequisites
```bash
# Ubuntu 22.04 LTS
# Python 3.10+
# ROS 2 Jazzy installed
```

### Running Your First Example

**Terminal 1 - Start the publisher:**
```bash
cd 1_ROS2/01_Publisher_Subscriber/src
python3 simple_publisher.py
```

**Terminal 2 - Start the subscriber:**
```bash
cd 1_ROS2/01_Publisher_Subscriber/src
python3 simple_subscriber.py
```

You should see messages being published and received!

---

## 🎓 Learning Outcomes

After completing all tutorials, you will understand:

✅ ROS 2 node and topic architecture  
✅ Publisher-subscriber pattern for data distribution  
✅ Service-client pattern for request-response communication  
✅ Custom message and service definitions  
✅ Action servers for goal-oriented tasks  
✅ Parameter management and configuration  
✅ Multi-node system coordination via launch files  
✅ Robot kinematic modeling with URDF, Xacro, and RViz2 visualization  
✅ Spatial coordinate transforms and frame tracking with TF2 (REP 105 & REP 103)  
✅ ROS 2 best practices and design patterns  

---

## 📊 Concept Relationship Diagram

```
┌─────────────────────────────────────────────────────┐
│                  ROS 2 Middleware                    │
│        (DDS Communication Infrastructure)           │
└─────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
    ┌────────┐      ┌─────────┐      ┌──────────┐
    │ Topics │      │ Services│      │ Actions  │
    │ (Async)│      │ (Sync)  │      │ (Goal)   │
    └────────┘      └─────────┘      └──────────┘
        │                 │                 │
    ┌───────────────────────────────────────────┐
    │          Parameters (Configuration)       │
    └───────────────────────────────────────────┘
        │
    ┌───────────────────────────────────────────┐
    │     Launch Files (System Composition)      │
    └───────────────────────────────────────────┘
        │
    ┌───────────────────────────────────────────┐
    │       08_URDF (Robot Kinematic Model)     │
    └─────────────────────┬─────────────────────┘
                          │
    ┌─────────────────────▼─────────────────────┐
    │    09_TF2 (Spatial Coordinate Transforms) │
    └───────────────────────────────────────────┘
```

---

## 🔍 ROS 2 Communication Patterns

| Pattern | Use Case | Sync/Async | Example |
|---------|----------|-----------|---------|
| **Topic** | Sensor data, continuous streams | Async | Camera feed, GPS data |
| **Service** | Database queries, computations | Sync | Calculate path, get status |
| **Action** | Long-running goals | Async + feedback | Navigate, pick & place |
| **Parameter** | Configuration values | On-demand | Robot speed, gains |
| **TF2 Transform** | Coordinate frame tracking | Streaming / Latched | Robot pose, sensor frames |
| **URDF Model** | Physical robot description | Latched parameter | RViz2 visual, collisions |

---

## 📝 How to Use These Tutorials

1. **Start with the prerequisites** (00_Install)
2. **Follow the learning progression** in order
3. **Read the Readme.md** in each tutorial folder
4. **Study the example code** (*.py files)
5. **Run the examples** step by step
6. **Modify and experiment** with the code
7. **Move to the next tutorial** when comfortable

---

## 🔗 Additional Resources

### Official ROS 2 Documentation
- [ROS 2 Documentation](https://docs.ros.org/en/jazzy/)
- [ROS 2 Concepts](https://docs.ros.org/en/jazzy/Concepts.html)
- [ROS 2 Python Client Library](https://docs.ros.org/en/jazzy/Tutorials/Client-Libraries.html)
- [ROS 2 TF2 Design & Tutorials](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Tf2/Tf2-Main.html)

### Key Concepts
- **Nodes:** Independent programs that communicate
- **Topics:** Named buses for asynchronous messaging
- **Services:** Request-response communication
- **Actions:** Goal-oriented communication with feedback
- **Parameters:** Configuration values
- **Messages:** Data structures for communication
- **URDF / Xacro:** Kinematic robot modeling and visual rendering
- **TF2:** Dynamic coordinate frame transformations

### Debugging Tools
- `ros2 topic list` - List all active topics
- `ros2 topic echo <topic>` - Monitor topic messages
- `ros2 service list` - List available services
- `ros2 param list` - List node parameters
- `ros2 run tf2_tools view_frames` - Visualize coordinate frames
- `ros2 run tf2_ros tf2_echo` - Echo live transform between frames
- `check_urdf` - Verify URDF robot model XML syntax
- `rqt_graph` - Visualize node communication
- `rqt_console` - View debug output

---

## 🚀 Next Steps

After mastering ROS 2 core concepts:

1. **Try the Webots Simulation** → [2_Webots/README.md](../2_Webots/README.md)
2. **Build Complete Systems** → Combine tutorials
3. **Deploy on Real Robots** → TurtleBot3, other platforms
4. **Explore Advanced Topics** → Transforms, navigation, manipulation

---

## 📞 Support & Questions

- 📖 Review the [main repository README](../README.md)
- 🐛 Check individual tutorial Readmes for specific issues
- 💬 Explore ROS Answers: https://answers.ros.org/
- 🌐 Repository: [phoori-gh/ros](https://github.com/phoori-gh/ros)

---

## 👤 Contributing

Found an issue or have improvements? Contributions are welcome!

- Report bugs and suggest improvements
- Share your own examples and modifications
- Help translate documentation
- Create pull requests with enhancements

---

**Ready to start? Begin with [00_Install →](00_Install/Readme.md)**

**Or jump to a specific concept:**
- 🔄 [Publishers & Subscribers](01_Publisher_Subscriber/Readme.md)
- 🔗 [Services & Clients](02_Server_Client/Readme.md)
- 💬 [Custom Messages](03_Message/Readme.md)
- ⚙️ [Services Definition](04_Service/Readme.md)
- ⚙️ [Parameters](05_Parameters/Readme.md)
- 🎯 [Actions](06_Action/Readme.md)
- 🚀 [Launch Files](07_Launch/Readme.md)
- 🤖 [URDF & Robot Modeling](08_URDF/Readme.md)
- 🧭 [TF2 & Coordinate Frames](09_TF2/Readme.md)

---

**Happy learning! 🤖 Let's master ROS 2 together!**
