# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 2: โหนด QoS Publisher & Subscriber

---

## 💻 ขั้นตอนการทดลอง

### ขั้นตอนที่ 1: รันโหนด Publisher
```bash
./docker/run_lab.sh python3 Essential_ROS/Week_02_Nodes_Topics_QoS/src/sensor_qos_publisher.py
```

### ขั้นตอนที่ 2: รันโหนด Subscriber ในอีกหน้าต่าง
```bash
./docker/run_lab.sh python3 Essential_ROS/Week_02_Nodes_Topics_QoS/src/sensor_qos_subscriber.py
```
*สังเกต:* Subscriber จะได้รับข้อความ Latched Robot State ทันทีที่เปิดขึ้นมา

### ขั้นตอนที่ 3: ตรวจสอบรายละเอียด QoS ผ่าน CLI
```bash
./docker/run_lab.sh ros2 topic info /sensor/temperature --verbose
```
