# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 12: การสร้างและบันทึกแผนที่คลังสินค้า

---

## 💻 ขั้นตอนการทดลอง

### ขั้นตอนที่ 1: รัน Online Asynchronous SLAM
```bash
./docker/run_lab.sh ros2 launch Essential_ROS/Week_12_SLAM_Mapping_Ceres/launch/online_async_slam.launch.py
```

### ขั้นตอนที่ 2: ขับหุ่นยนต์สำรวจพื้นที่โกดัง
```bash
./docker/run_lab.sh ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
*ขับวนกลับมายังจุดเริ่มต้นเพื่อให้ Ceres Solver ทำการปิด Loop Closure*

### ขั้นตอนที่ 3: บันทึกแผนที่คลังสินค้า
```bash
./docker/run_lab.sh ros2 run nav2_map_server map_saver_cli -f /mnt/sda/ros/Essential_ROS/Week_12_SLAM_Mapping_Ceres/maps/warehouse_map
```
