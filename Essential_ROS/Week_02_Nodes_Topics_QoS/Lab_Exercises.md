# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 2: โครงสร้างโหนด, Topics และการจัดการ Quality of Service (QoS)
**วิชา:** AMR-101 Essential ROS 2 for Autonomous Mobile Robots  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** พื้นฐาน (Beginner)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายสัปดาห์ที่ 2](Readme.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. รันและทดสอบการสื่อสารแบบ Publish-Subscribe ผ่านโหนด `sensor_qos_publisher` และ `sensor_qos_subscriber`
2. ตรวจสอบและพิสูจน์การทำงานของ Latching Topic ด้วย `TRANSIENT_LOCAL` สำหรับ Late-joining Nodes
3. จำลองและแก้ปัญหาข้อผิดพลาด **QoS Incompatibility** ด้วยเครื่องมือ CLI เชิงลึก
4. ปรับปรุงโค้ด Python เพื่อเพิ่มการเผยแพร่ข้อมูลระดับพลังงานแบตเตอรี่ (`/sensor/battery_state`) ตามข้อกำหนดทางวิศวกรรม

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่รูทไดเรกทอรีของ repository วิชา
- Build แพ็กเกจ `amr_week02` (ament_python) — หลัง build แล้ว `run_lab.sh` จะ source `install/setup.bash` ให้อัตโนมัติ:
  ```bash
  ./docker/run_lab.sh colcon build --base-paths Essential_ROS --packages-select amr_week02
  # หรือ: make build PKG=amr_week02      ชุดทดสอบอัตโนมัติ: make test PKG=amr_week02
  ```
- ห้องแล็บใช้เครือข่ายร่วมกัน: ตั้ง `ROS_DOMAIN_ID` ของตนเองและ `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` ก่อนเรียก `run_lab.sh` ทุก Terminal

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 2.1: การรัน Publisher และการตรวจสอบ QoS ด้วย CLI
**เป้าหมาย:** สังเกตพฤติกรรมการ Publish ข้อมูลเซนเซอร์แบบ Best Effort

1. เปิด **Terminal 1** แล้วรันโหนด Publisher:
   ```bash
   ./docker/run_lab.sh ros2 run amr_week02 sensor_qos_publisher
   # แบบไม่ build: ./docker/run_lab.sh python3 Essential_ROS/Week_02_Nodes_Topics_QoS/src/sensor_qos_publisher.py
   ```
   **ผลลัพธ์ที่คาดหวัง:** โหนดแสดงสถานะ `[INFO] [sensor_qos_publisher]: 🚀 [SensorQoSPublisher] Node initialized and publishing...`

2. เปิด **Terminal 2** แล้วทดลองดักฟังสัญญาณอุณหภูมิด้วยคำสั่งพื้นฐาน:
   ```bash
   ./docker/run_lab.sh ros2 topic echo /sensor/temperature
   ```
   *สังเกต:* ใน ROS 2 Jazzy ข้อมูลจะแสดงได้ตามปกติ เพราะ `ros2 topic echo` ที่ไม่ระบุ QoS จะเลือก Reliability/Durability ให้ตรงกับ Publisher ที่ค้นพบเอง (ผลจริง: `data: 37.4647102355957`) — แต่ Subscriber ที่เราเขียนเองในโค้ด **ไม่มี** กลไกนี้ ต้องตั้ง QoS ให้เข้ากันได้เอง (ดู Lab 2.3)

3. ทดสอบใส่แฟล็ก QoS ให้ตรงกับ Publisher:
   ```bash
   ./docker/run_lab.sh ros2 topic echo --qos-reliability best_effort /sensor/temperature
   ```
   *ผลลัพธ์:* ข้อมูลอุณหภูมิจะไหลเข้ามาอย่างต่อเนื่อง (ผลจริง: `data: 36.11299514770508`) — ค่าที่ส่งเป็น `float32` จึงแสดงทศนิยมยาวเมื่อแปลงเป็น `float` ของ Python

4. ตรวจสอบข้อมูลเชิงลึกของท็อปปิก:
   ```bash
   ./docker/run_lab.sh ros2 topic info -v /sensor/temperature
   ```
   **คำถาม Checkpoint 2.1:**
   - [ ] ในส่วน Publisher count และ Subscription count มีจำนวนเท่าใด?
   - [ ] ค่านโยบาย Reliability และ Durability ที่แสดงใน Endpoint Info มีค่าเป็นอะไร?

---

### 🔹 Lab 2.2: การพิสูจน์พฤติกรรม Latching (Late-Joiner Verification)
**เป้าหมาย:** พิสูจน์ว่า `TRANSIENT_LOCAL` เก็บประวัติข้อความล่าสุดให้ผู้รับที่เปิดทีหลังจริงหรือไม่

1. ตรวจสอบให้แน่ใจว่า Terminal 1 (Publisher) กำลังรันอยู่
2. ใน **Terminal 2** รันคำสั่งดักฟัง `/robot/state` โดยใช้แฟล็ก `--qos-durability transient_local`:
   ```bash
   ./docker/run_lab.sh ros2 topic echo --qos-durability transient_local /robot/state
   ```
3. สังเกตว่าทันทีที่กด Enter แม้ Publisher จะยังไม่วนรอบส่งรอบใหม่ หน้าจอจะแสดงสถานะ **ล่าสุด** ที่ถูกแคชไว้ทันที — ถ้าเปิดภายใน 5 วินาทีแรกจะได้ `SYSTEM_READY: Battery=100%, Mode=NORMAL` ถ้าเปิดทีหลังจะได้ค่าที่อัปเดตล่าสุด (ผลจริงเมื่อเปิดหลัง Publisher ~20 วินาที):
   ```text
   data: 'SYSTEM_ACTIVE: Uptime=20.0s'
   ---
   ```
   ลองเปลี่ยนเป็น `--qos-durability volatile` จะไม่ได้ข้อความเก่าเลย (ต้องรอรอบอัปเดตถัดไปทุก 5 วินาที)
4. ทดสอบรัน `sensor_qos_subscriber` ใน **Terminal 3**:
   ```bash
   ./docker/run_lab.sh ros2 run amr_week02 sensor_qos_subscriber
   ```
   สังเกตข้อความ `📢 Latched Robot State Received` ที่ปรากฏขึ้นทันทีที่จับคู่สำเร็จ ก่อนรอบอัปเดตถัดไปของ Publisher

---

### 🔹 Lab 2.3: การจำลองและแก้ไขปัญหา QoS Mismatch
**เป้าหมาย:** ทำความเข้าใจอาการที่เกิดขึ้นเมื่อระบบเครือข่ายไม่ยอมส่งข้อมูลเนื่องจาก QoS ขัดแย้งกัน

1. ทดลองใช้ CLI จำลองการ Subscribe ด้วย QoS ที่ไม่เข้ากัน:
   ```bash
   # ท็อปปิก /sensor/temperature ส่งแบบ BEST_EFFORT
   # ลองบังคับให้ CLI รับแบบ RELIABLE
   ./docker/run_lab.sh ros2 topic echo --qos-reliability reliable /sensor/temperature
   ```
2. สังเกตผลลัพธ์: จะไม่มีข้อมูลถูกพิมพ์ออกมาแม้แต่ข้อความเดียว มีเพียงคำเตือนจริงจาก ROS 2:
   ```text
   [WARN] [...] [_ros2cli_164]: New publisher discovered on topic '/sensor/temperature', offering incompatible QoS. No messages will be received from it. Last incompatible policy: RELIABILITY
   ```
   และฝั่ง Publisher (Terminal 1) จะเตือน `New subscription discovered on topic 'sensor/temperature', requesting incompatible QoS. No messages will be sent to it.`
3. วินิจฉัยด้วยคำสั่ง `ros2 topic info -v`:
   ```bash
   ./docker/run_lab.sh ros2 topic info -v /sensor/temperature
   ```
   **คำถาม Checkpoint 2.3:**
   - [ ] หากระบบ Nav2 ของหุ่นยนต์ไม่ยอมรับข้อมูลจาก LaserScan ให้สันนิษฐานสาเหตุจาก QoS อย่างไร และจะแก้ไขอย่างไร?

---

### 🔹 Lab 2.4: การเขียนโค้ดเพิ่มท็อปปิกแบตเตอรี่ (Hands-on Code Enhancement)
**เป้าหมาย:** เพิ่มท็อปปิก `/sensor/battery` บนโหนด `sensor_qos_publisher.py`

ให้นักศึกษาแก้ไขไฟล์ `Essential_ROS/Week_02_Nodes_Topics_QoS/src/sensor_qos_publisher.py` เพื่อเพิ่ม:
1. Publisher ชื่อ `pub_battery` ส่งข้อความชนิด `std_msgs/msg/Float32` ไปยังท็อปปิก `sensor/battery` (ชื่อแบบ Relative → `/sensor/battery` เมื่อไม่มี Namespace)
2. กำหนด QoS Profile เป็น:
   - `ReliabilityPolicy.BEST_EFFORT`
   - `DurabilityPolicy.VOLATILE`
   - `HistoryPolicy.KEEP_LAST` พร้อม `depth=1`
3. ใน `timer_callback` ให้คำนวณระดับแบตเตอรี่จำลองลดลงทีละ $0.05\%$ ในแต่ละรอบ (เริ่มต้นที่ $100.0\%$)
4. Build ใหม่ (`colcon build ... --packages-select amr_week02`) แล้วทดสอบความถูกต้องด้วยคำสั่ง:
   ```bash
   ./docker/run_lab.sh ros2 topic echo --qos-reliability best_effort /sensor/battery
   ```

---

## 🏆 โจทย์ท้าทายระดับสูง (Challenge Exercises)
1. **Challenge 2.1:** สร้างโหนดชื่อ `battery_alarm_node.py` ที่ Subscribe ท็อปปิก `/sensor/battery` และหากแบตเตอรี่ต่ำกว่า $20.0\%$ ให้ส่งคำสั่งเตือนภัยผ่านการ Publish ข้อความ `CRITICAL_LOW_BATTERY` ไปยัง `/robot/state`
2. **Challenge 2.2:** ใช้คำสั่ง `ros2 topic hz` และ `ros2 topic bw` วัดค่าความถี่และแบนด์วิดท์ของทั้ง 3 ท็อปปิก พร้อมบันทึกผลและคำนวณขนาดแพ็กเก็ตเฉลี่ย

---

## 📦 สิ่งที่ต้องส่ง (Deliverables Checklist)
- [ ] ภาพบันทึกหน้าจอผลการทดสอบ `ros2 topic info -v /sensor/temperature`
- [ ] ภาพบันทึกหน้าจอการรับข้อมูลแบบ Latched Topic ของ `/robot/state`
- [ ] ภาพบันทึกหน้าจอการทำงานของท็อปปิก `/sensor/battery` ที่เขียนเพิ่ม
- [ ] โค้ดส่วนที่เพิ่มใน `sensor_qos_publisher.py` หรือไฟล์สคริปต์แยก
- [ ] คำตอบ Checkpoint 2.1 และ 2.3

---

## 📊 เกณฑ์การประเมินผล (Lab Grading Rubric - 100 คะแนน)
| รายการประเมิน | รายละเอียดการให้คะแนน | คะแนนเต็ม |
| :--- | :--- | :---: |
| **การทดสอบ Best Effort & Echo** | รัน Publisher และใช้ CLI รับข้อมูลด้วย QoS ที่ถูกต้อง | 20 |
| **การพิสูจน์ Latched State** | อธิบายและสาธิตการรับข้อมูลของ Late-joining Subscriber ได้สำเร็จ | 20 |
| **การวินิจฉัย QoS Mismatch** | อธิบายสาเหตุของข้อผิดพลาดและการวิเคราะห์ผ่าน `ros2 topic info -v` ได้ถูกต้อง | 20 |
| **การพัฒนาโค้ดเพิ่มท็อปปิกแบตเตอรี่** | เขียนโค้ดตามข้อกำหนด Lab 2.4 ถูกต้อง โค้ดคอมไพล์ผ่านและรันได้จริง | 30 |
| **โจทย์ท้าทายและความเรียบร้อยของรายงาน** | ทำ Challenge หรือส่งรายงานพร้อมผลวิเคราะห์อย่างละเอียด | 10 |
| **รวม** | | **100** |

---

## ⚠️ การแก้ปัญหาที่พบบ่อยในแล็บ (Troubleshooting)
| ปัญหา | สาเหตุ | การแก้ไข |
| :--- | :--- | :--- |
| `AttributeError: 'Node' object has no attribute 'pub_battery'` | ลืมประกาศ `self.pub_battery = self.create_publisher(...)` ใน `__init__` | ตรวจสอบการประกาศตัวแปร Publisher ในคอนสตรักเตอร์ |
| `ModuleNotFoundError: No module named 'rclpy'` | รันคำสั่งบน Host โดยตรงแทนที่จะรันผ่านคอนเทนเนอร์ | นำหน้าคำสั่งด้วย `./docker/run_lab.sh` เสมอ |
| `Package 'amr_week02' not found` | ยังไม่ได้ `colcon build` หรือ build ไว้แต่แก้โค้ดแล้วยังไม่ build ใหม่ | รัน `./docker/run_lab.sh colcon build --base-paths Essential_ROS --packages-select amr_week02` |
| `WARNING: topic [...] does not appear to be published yet` | คำสั่ง CLI เปิดเร็วเกินไป Discovery ยังไม่เสร็จ | รอ 1–2 วินาทีแล้วรันใหม่ หรือ `ros2 daemon start` ไว้ก่อน |
| ค่าตัวเลขแบตเตอรี่ไม่ยอมลด | ประกาศตัวแปรระดับแบตเตอรี่เป็น Local Variable ในฟังก์ชัน Callback | ให้เก็บค่าใน Instance Variable เช่น `self.battery_level` |


## 📟 ผลการรันจริง (Real Run Output)
บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29 — ไฟล์เต็ม: [`results/qos_lab_run.txt`](results/qos_lab_run.txt)

```console
$ ros2 run amr_week02 sensor_qos_publisher     # terminal 1
$ ros2 run amr_week02 sensor_qos_subscriber    # terminal 3, started 2 s after the publisher (late joiner)
[INFO] [1793242259.809630082] [sensor_qos_subscriber]: 📡 [SensorQoSSubscriber] Listening for sensor & state updates...
[INFO] [1793242261.525578214] [sensor_qos_subscriber]: 📢 Latched Robot State Received: "SYSTEM_READY: Battery=100%, Mode=NORMAL"
[INFO] [1793242261.813319452] [sensor_qos_subscriber]: Received Temperature: 36.50 °C
...
$ ros2 topic info -v /sensor/temperature
Type: std_msgs/msg/Float32

Publisher count: 1

Node name: sensor_qos_publisher
Node namespace: /
Topic type: std_msgs/msg/Float32
...
Endpoint type: PUBLISHER
...
QoS profile:
  Reliability: BEST_EFFORT
  History (Depth): UNKNOWN
  Durability: VOLATILE
  Lifespan: Infinite
  Deadline: Infinite
  Liveliness: AUTOMATIC
  Liveliness lease duration: Infinite

Subscription count: 0

$ ros2 topic hz /sensor/temperature   (stopped after 6 s)
	min: 0.500s max: 0.500s std dev: 0.00010s window: 3
average rate: 2.000
	min: 0.500s max: 0.500s std dev: 0.00012s window: 6
```

---

