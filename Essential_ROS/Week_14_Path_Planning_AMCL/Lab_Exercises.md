# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 14: การนำทางอัตโนมัติด้วย Nav2 Stack

---

## 💻 ขั้นตอนการทดลอง

### ขั้นตอนที่ 1: รัน Nav2 Bringup เต็มรูปแบบ
```bash
./docker/run_lab.sh ros2 launch Essential_ROS/Week_14_Path_Planning_AMCL/launch/nav2_bringup.launch.py
```

### ขั้นตอนที่ 2: ระบุตำแหน่งเริ่มต้นของหุ่นยนต์อัตโนมัติ
```bash
./docker/run_lab.sh python3 Essential_ROS/Week_14_Path_Planning_AMCL/src/amcl_initial_pose.py
```

### ขั้นตอนที่ 3: สั่งเป้าหมายปลายทาง
คลิกปุ่ม **Nav2 Goal** บน RViz2 เพื่อสั่งให้หุ่นยนต์คำนวณเส้นทางและขับหลบเสาโกดังอัตโนมัติ
