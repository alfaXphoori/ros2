# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 6: จลนศาสตร์และการคำนวณ Odometry

---

## 💻 ขั้นตอนการทดลอง

### ขั้นตอนที่ 1: รันโหนดคำนวณจลนศาสตร์และ Odometry
```bash
./docker/run_lab.sh python3 Essential_ROS/Week_06_Kinematics_REP_Standards/src/diff_drive_kinematics.py
```

### ขั้นตอนที่ 2: ส่งคำสั่งความเร็วเดินหน้าและเลี้ยวโค้ง
```bash
# สั่งเดินหน้าความเร็ว 0.4 m/s พร้อมเลี้ยว 0.5 rad/s
./docker/run_lab.sh ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.4}, angular: {z: 0.5}}" -r 10
```

### ขั้นตอนที่ 3: ตรวจสอบตำแหน่งพิกัด Odometry ที่คำนวณได้
```bash
./docker/run_lab.sh ros2 topic echo /odom_calculated
```
*สังเกต:* พิกัดตำแหน่ง $X, Y$ และมุม Orientation จะเพิ่มขึ้นตามจลนศาสตร์การเลี้ยวโค้ง
