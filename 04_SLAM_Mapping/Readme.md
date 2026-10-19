# 🗺️ โมดูล 4: การสร้างแผนที่ 2 มิติด้วย SLAM Toolbox
## (Module 4: 2D Occupancy Grid Mapping & Graph SLAM)

---

## 🎯 วัตถุประสงค์การเรียนรู้
1. เข้าใจหลักการทำงานของ Graph-based SLAM, Scan Matching, และ Pose Graph Optimization
2. ปรับแต่งพารามิเตอร์ของ `slam_toolbox` ให้เหมาะสมกับสภาพแวดล้อมคลังสินค้าและอัตราสแกนของ LiDAR
3. ขับหุ่นยนต์สำรวจพื้นที่ใน Gazebo Sim เพื่อสร้างแผนที่ Occupancy Grid สด
4. สังเกตและวิเคราะห์ปรากฏการณ์ Loop Closure เมื่อหุ่นยนต์วนกลับมายังตำแหน่งเดิม
5. บันทึกและจัดการไฟล์แผนที่ `.pgm` (Image) และ `.yaml` (Metadata) สำหรับนำไปใช้ใน Nav2

---

## 🏛️ สถาปัตยกรรมของ SLAM Toolbox ใน ROS 2

```
  Sensor Data:
  • /scan (sensor_msgs/msg/LaserScan)
  • /tf & /odom (Transform Tree)
            │
            ▼
┌────────────────────────────────────────────────────────┐
│             async_slam_toolbox_node                    │
├────────────────────────────────────────────────────────┤
│ 1. Laser Scan Matching (Karto / Ceres Solver)          │
│ 2. Pose Graph Management (Nodes & Covariance Edges)    │
│ 3. Loop Closure Detection (Coarse to Fine Response)    │
│ 4. 2D Occupancy Grid Calculation (Ray Tracing)         │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
                     Topic: /map
           (nav_msgs/msg/OccupancyGrid)
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
             RViz2                   nav2_map_server
        (Map Display)             (Save to .pgm & .yaml)
```

---

## 📑 สารบัญเอกสารและปฏิบัติการ
- [ใบงานปฏิบัติการโมดูล 4 (Lab_Exercises.md)](Lab_Exercises.md)
  - **Lab 4.1:** การรัน SLAM Toolbox พร้อมเชื่อมต่อ Gazebo Simulation
  - **Lab 4.2:** การเปิด RViz2 ตรวจสอบการขยายตัวของแผนที่แบบเรียลไทม์
  - **Lab 4.3:** การบังคับสำรวจพื้นที่และทำให้เกิด Loop Closure
  - **Lab 4.4:** การสั่งบันทึกแผนที่ด้วย `nav2_map_server`
