# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 4: Action Server & Client นำทางระยะทาง

---

## 💻 ขั้นตอนการทดลอง

### ขั้นตอนที่ 1: รัน Action Server
```bash
./docker/run_lab.sh python3 Essential_ROS/Week_04_Actions_Preemption/src/navigate_action_server.py
```

### ขั้นตอนที่ 2: รัน Action Client แบบปกติ (รับผลลัพธ์จนจบ)
```bash
./docker/run_lab.sh python3 Essential_ROS/Week_04_Actions_Preemption/src/navigate_action_client.py
```

### ขั้นตอนที่ 3: รัน Action Client ทดสอบการกดยกเลิกภารกิจกลางคัน
```bash
./docker/run_lab.sh python3 Essential_ROS/Week_04_Actions_Preemption/src/navigate_action_client.py cancel
```
*สังเกต:* Action Server จะหยุดการประมวลผลทันที และรายงานสถานะ `Goal canceled by client request`
