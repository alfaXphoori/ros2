# 🐳 Docker Environment Setup (ROS 2 Jazzy & Gazebo Sim)

สภาพแวดล้อมสำหรับรันทุกแล็บของวิชา (Essential Week 01–16 และ Advanced โมดูล 01–06) แบบเดียวกันทุกเครื่อง
ผลการรันจริงทุกชิ้นใน repo บันทึกจาก image นี้บนโฮสต์ Ubuntu 26.04 / Linux 7.0 (Ubuntu 26.04 ไม่มีแพ็กเกจ Jazzy ให้ติดตั้งตรง ๆ)

### แพ็กเกจที่ติดตั้งใน Image (`ros:lab-runner`, ดู [`Dockerfile`](Dockerfile))
- **OS Base:** `ros:jazzy-ros-base-noble` (Ubuntu 24.04) pin ด้วย digest แล้ว `apt-get dist-upgrade` ทั้งชุดเพื่อไม่ให้เวอร์ชันปนกัน
- **ROS 2:** Jazzy Jalisco (LTS)
- **Simulation:** Gazebo Sim 8.15 (Harmonic) + `ros_gz_bridge` + `ros_gz_sim` + `gz_ros2_control`
- **Visualization:** RViz2, `robot_state_publisher`, `joint_state_publisher(_gui)`, `tf2_tools`, `foxglove_bridge` (ดูผลแบบ headless)
- **Navigation & Mapping:** `navigation2`, `nav2_bringup`, `nav2_simple_commander`, `nav2_collision_monitor`, `nav2_loopback_sim`, `slam_toolbox`, `opennav_docking`
- **Control & Perception (Advanced):** `ros2_control`, `ros2_controllers`, `cv_bridge`, `vision_msgs`, `image_publisher`, `camera_calibration`, OpenCV 4.6 (`cv2.aruco` มี AprilTag 36h11)
- **Fleet & Middleware:** `rmf_fleet_adapter_python`, `rmw_zenoh_cpp`, `sros2`
- **Testing & Recording:** `launch_testing(_ros)`, `python3-pytest`, `rosbag2` + MCAP storage, `yamllint`, `xmllint`

**ไม่มีใน image (ต้องติดตั้งเองถ้าต้องการ):** `ultralytics`/PyTorch (YOLO เป็นแบบฝึกหัดเสริมของ Advanced 02 — ติดตั้งใน venv),
`micro_ros_agent` (ต้อง build จากซอร์สหรือใช้ image `microros/micro-ros-agent`), PCL / `perception_pcl`

### วิธีใช้งาน
```bash
make image                                # build image (ครั้งแรก ~6 GB)
./docker/run_lab.sh                       # interactive shell (source ROS 2 + install/ ให้อัตโนมัติ)
./docker/run_lab.sh ros2 doctor --report  # รันคำสั่งเดียว
make build && make test                   # colcon build + test ทุกแพ็กเกจในคอนเทนเนอร์
```
`run_lab.sh` จะ:
- mount repo ที่ `/workspace` และรันด้วย uid/gid ของผู้ใช้ (ไฟล์ที่สร้างไม่เป็นของ root) — ตั้ง `LAB_AS_ROOT=1` ถ้าจำเป็น
- ใช้ `--net host --ipc host` และส่งต่อ `ROS_DOMAIN_ID`, `RMW_IMPLEMENTATION`, `ROS_AUTOMATIC_DISCOVERY_RANGE`,
  `ROS_STATIC_PEERS`, `GZ_PARTITION`, `ROS_SECURITY_*` จากโฮสต์
- source `/workspace/install/setup.bash` ถ้ามี (หลัง `make build`) จึงใช้ `ros2 run amr_weekNN ...` ได้ทันที

> ห้องเรียนที่มีหลายเครื่องในวง LAN เดียวกัน: ตั้ง `ROS_DOMAIN_ID` คนละค่าต่อกลุ่ม หรือ
> `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` และใช้ `GZ_PARTITION` คนละค่าเพื่อไม่ให้ Gazebo ของแต่ละคนเห็นกัน

### การตั้งค่า X11 Forwarding สำหรับหน้าต่าง GUI (RViz2 / Gazebo)
หากรันบนเครื่อง Linux ที่มีหน้าจอ ให้รันคำสั่งนี้บน Host ก่อนเปิดคอนเทนเนอร์:
```bash
xhost +local:
```
ไม่มีจอ / รันบนเซิร์ฟเวอร์: ใช้ `headless:=true` ใน launch ของ Gazebo (`gz sim -s -r --headless-rendering`) และดูข้อมูลผ่าน
`ros2 launch foxglove_bridge foxglove_bridge_launch.xml` + Foxglove Studio (`ws://localhost:8765`)
