# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 1: ตรวจสอบระบบและเครือข่าย DDS

---

## 🎯 วัตถุประสงค์การทดลอง
1. ตรวจสอบความพร้อมของสภาพแวดล้อม ROS 2 Jazzy บน Docker
2. ทดสอบการสื่อสารแบบ Multicast และวิเคราะห์การแยกกลุ่มเครือข่ายด้วย `ROS_DOMAIN_ID`

---

## 💻 ขั้นตอนการทดลอง

### ขั้นตอนที่ 1: ตรวจสอบความพร้อมของระบบ
รันสคริปต์วินิจฉัยสภาพแวดล้อม:
```bash
./docker/run_lab.sh bash Essential_ROS/Week_01_Environment_DDS/src/domain_check.sh
```

### ขั้นตอนที่ 2: ทดสอบการสื่อสาร Multicast
เปิดสอง Terminal:
```bash
# Terminal 1: รอรับแพ็กเก็ต Multicast
./docker/run_lab.sh ros2 multicast receive

# Terminal 2: ส่งแพ็กเก็ตทดสอบ
./docker/run_lab.sh ros2 multicast send
```
*ผลลัพธ์ที่คาดหวัง:* Terminal 1 จะแสดงข้อความ `Received from ...: Hello World!`

### ขั้นตอนที่ 3: ทดสอบการแยกซับเน็ตด้วย ROS_DOMAIN_ID
1. รัน Talker ใน Domain ID = 10:
   ```bash
   ./docker/run_lab.sh bash -c "export ROS_DOMAIN_ID=10 && ros2 run demo_nodes_py talker"
   ```
2. รัน Listener ใน Domain ID = 20:
   ```bash
   ./docker/run_lab.sh bash -c "export ROS_DOMAIN_ID=20 && ros2 run demo_nodes_py listener"
   ```
*ผลลัพธ์ที่คาดหวัง:* Listener จะไม่ได้รับข้อความใดๆ แสดงว่าเครือข่ายถูกแยกกันอย่างสมบูรณ์
