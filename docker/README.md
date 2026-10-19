# 🐳 Docker Environment Setup (ROS 2 Jazzy & Gazebo Sim)

สภาพแวดล้อมจำลองระดับวิศวกรรมที่ติดตั้งแพ็กเกจสมบูรณ์พร้อมรันทุกแล็บในวิชา

### แพ็กเกจที่ติดตั้งใน Image
- **OS Base:** Ubuntu 24.04 LTS (Noble Numbat)
- **ROS 2:** Jazzy Jalisco (LTS)
- **Simulation:** Gazebo Sim 8.15+ (Harmonic) + `ros_gz_bridge` + `ros_gz_sim`
- **Visualization:** RViz2, `robot_state_publisher`, `joint_state_publisher_gui`
- **Navigation:** `navigation2`, `nav2_bringup`, `nav2_simple_commander`
- **Mapping:** `slam_toolbox` (Online Async SLAM)

### วิธีเข้าสู่สภาพแวดล้อม
```bash
cd docker
./run_lab.sh
```

### การตั้งค่า X11 Forwarding สำหรับหน้าต่าง GUI (RViz2 / Gazebo)
หากรันบนเครื่อง Linux ที่มีหน้าจอ ให้รันคำสั่งนี้บน Host ก่อนเปิดคอนเทนเนอร์:
```bash
xhost +local:root
```
