# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 11: การจำลองขับเคลื่อนและระบบ Safety Shield

---

## 💻 ขั้นตอนการทดลอง

### ขั้นตอนที่ 1: รัน Gazebo World พร้อมสปอว์นหุ่นยนต์และเปิด Bridge
```bash
./docker/run_lab.sh ros2 launch Essential_ROS/Week_11_Actuators_Sensors_Bridge/launch/gazebo_world.launch.py
```

### ขั้นตอนที่ 2: รันโหนดตัดความเร็วฉุกเฉิน (Emergency Stop Shield)
```bash
./docker/run_lab.sh python3 Essential_ROS/Week_11_Actuators_Sensors_Bridge/src/emergency_stop_node.py
```

### ขั้นตอนที่ 3: ขับหุ่นยนต์พุ่งเข้าหาเสาหรือผนัง
```bash
./docker/run_lab.sh ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
*ผลลัพธ์ที่คาดหวัง:* เมื่อหุ่นยนต์เข้าใกล้เสาต่ำกว่า 0.35 ม. โหนด Emergency Stop จะตัดคำสั่งและหยุดหุ่นยนต์อัตโนมัติ
