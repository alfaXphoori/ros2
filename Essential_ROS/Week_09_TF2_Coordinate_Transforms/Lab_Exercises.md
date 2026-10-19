# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 9: บรอดแคสต์และแปลงพิกัด TF2

---

## 💻 ขั้นตอนการทดลอง

### ขั้นตอนที่ 1: บรอดแคสต์พิกัดเซนเซอร์ LiDAR และกล้องแบบ Static
```bash
./docker/run_lab.sh python3 Essential_ROS/Week_09_TF2_Coordinate_Transforms/src/static_sensor_broadcaster.py
```

### ขั้นตอนที่ 2: รันโหนด TF Listener แปลงพิกัดสิ่งกีดขวาง
```bash
./docker/run_lab.sh python3 Essential_ROS/Week_09_TF2_Coordinate_Transforms/src/tf_obstacle_listener.py
```
*สังเกต:* พิกัดวัตถุในกล้องจะถูกแปลงเข้าสู่จุดศูนย์กลางของหุ่นยนต์ `base_link` แบบอัตโนมัติ

### ขั้นตอนที่ 3: ตรวจสอบโครงสร้างสายสัมพันธ์พิกัด
```bash
./docker/run_lab.sh ros2 run tf2_tools view_frames
```
