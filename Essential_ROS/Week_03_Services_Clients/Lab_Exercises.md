# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 3: ระบบ Service-Client จัดการพลังงาน

---

## 💻 ขั้นตอนการทดลอง

### ขั้นตอนที่ 1: รัน Service Server
```bash
./docker/run_lab.sh python3 Essential_ROS/Week_03_Services_Clients/src/power_service_server.py
```

### ขั้นตอนที่ 2: ทดสอบเรียกใช้ Service ผ่าน CLI
```bash
./docker/run_lab.sh ros2 service call /robot/set_power_mode std_srvs/srv/SetBool "{data: true}"
```

### ขั้นตอนที่ 3: ทดสอบเรียกใช้ Service ผ่าน Client Node ใน Python
```bash
./docker/run_lab.sh python3 Essential_ROS/Week_03_Services_Clients/src/power_service_client.py true
```
