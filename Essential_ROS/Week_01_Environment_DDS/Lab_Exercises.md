# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 1: สภาพแวดล้อม สถาปัตยกรรม ROS 2 และเครือข่าย DDS
**วิชา:** AMR-101 Essential ROS 2 for Autonomous Mobile Robots  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** พื้นฐาน (Beginner)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายสัปดาห์ที่ 1](Readme.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. ติดตั้ง ตรวจสอบ และวินิจฉัยสภาพแวดล้อม **ROS 2 Jazzy Jalisco** บน Linux/Docker ได้อย่างถูกต้อง
2. ใช้งานคำสั่งเครือข่าย DDS ตรวจสอบการส่งสัญญาณค้นพบแบบ UDP Multicast (SPDP)
3. ปฏิบัติการแยกคลัสเตอร์เครือข่ายหุ่นยนต์ด้วย `ROS_DOMAIN_ID` และทดสอบพฤติกรรม Network Partitioning
4. ปรับแต่งไฟล์คอนฟิก DDS XML เพื่อจำกัด Interface เครือข่าย (Localhost Only vs Multicast)

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่รูทไดเรกทอรีของ repository วิชา (โฟลเดอร์ที่มี `docker/` และ `Essential_ROS/`)
- ตรวจสอบความพร้อมของ Docker Engine บนเครื่องโฮสต์:
  ```bash
  docker --version
  ```
- ทดสอบสิทธิ์การรัน Docker ผ่านสคริปต์แล็บ:
  ```bash
  ./docker/run_lab.sh ros2 --help
  ```
- Build แพ็กเกจของสัปดาห์นี้ (`amr_week01`) ด้วย colcon — `run_lab.sh` จะ source `install/setup.bash` ให้อัตโนมัติในครั้งถัดไป:
  ```bash
  ./docker/run_lab.sh colcon build --base-paths Essential_ROS --packages-select amr_week01
  # หรือใช้ Makefile: make build PKG=amr_week01   (ทดสอบอัตโนมัติ: make test PKG=amr_week01)
  ```
- **ห้องแล็บใช้เครือข่ายร่วมกัน:** ตั้ง `ROS_DOMAIN_ID` ตามที่อาจารย์จัดสรรและ `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` บนเครื่องโฮสต์ก่อนเรียก `run_lab.sh` (สคริปต์จะส่งต่อตัวแปรเข้าคอนเทนเนอร์)
> 💡 *หากยังไม่ได้ติดตั้ง สามารถดูขั้นตอนการติดตั้ง Native หรือ WSL2 อย่างละเอียดได้ที่ [คู่มือการติดตั้ง ROS 2](../../docs/ros2_installation_guide.md)*

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 1.0: การติดตั้งและตรวจสอบความพร้อมของระบบ (Installation & System Verification)
**เป้าหมาย:** ยืนยันการตั้งค่า Locale, การเข้าถึง Repository และความพร้อมของชุดเครื่องมือ ROS 2

1. ตรวจสอบเวอร์ชันของระบบปฏิบัติการและเคอร์เนล:
   ```bash
   cat /etc/os-release | grep -E "PRETTY_NAME|VERSION_ID"
   uname -r
   ```
2. ตรวจสอบความถูกต้องของ System Locale (ต้องเป็น UTF-8):
   ```bash
   locale | grep -E "LANG|LC_ALL"
   ```
   *ผลลัพธ์ที่ถูกต้อง:* ค่า `LANG` ควรมีค่าเป็น `en_US.UTF-8` หรือลงท้ายด้วย `.UTF-8`
3. ทดสอบการเรียกใช้งานคำสั่งแกนกลางของ ROS 2:
   ```bash
   ./docker/run_lab.sh ros2 pkg list | head -n 10
   ```
   *ผลลัพธ์ที่ถูกต้อง:* รายชื่อแพ็กเกจมาตรฐานของ ROS 2 Jazzy แสดงขึ้นมาอย่างน้อย 10 แพ็กเกจ

---

### 🔹 Lab 1.1: ตรวจสอบความสมบูรณ์ของสภาพแวดล้อมและรัน Diagnostic Script
**เป้าหมาย:** ทำความเข้าใจสถานะตัวแปรสภาพแวดล้อม (Environment Variables) และการทำงานของ ROS 2 Daemon

1. รันสคริปต์ตรวจสุขภาพระบบของสัปดาห์ที่ 1:
   ```bash
   ./docker/run_lab.sh ros2 run amr_week01 domain_check.sh
   # หรือแบบไม่ต้อง build: ./docker/run_lab.sh bash Essential_ROS/Week_01_Environment_DDS/src/domain_check.sh
   ```
   **ผลลัพธ์จริง** (`ROS_DOMAIN_ID=11`, ตัดมาจาก [`results/domain_check_and_doctor.txt`](results/domain_check_and_doctor.txt)):
   ```text
   ========================================================
   ROS 2 DDS & Network Diagnostic (Week 01)
   ========================================================
   [1/3] ROS 2 environment
     ROS_DISTRO                    : jazzy
     ROS_DOMAIN_ID                 : 11
     RMW_IMPLEMENTATION            : <not set -> rmw_fastrtps_cpp (Jazzy default)>
     ROS_AUTOMATIC_DISCOVERY_RANGE : LOCALHOST

   [2/3] RTPS ports for domain 11, participant 0
     Discovery multicast (SPDP, d0=0)  : 10150
     User data multicast (d2=1)        : 10151
     Discovery unicast   (SEDP, d1=10) : 10160
     User data unicast   (d3=11)       : 10161
     Port range of this domain         : 10150-10399
     OK: no overlap with the Linux ephemeral range 32768-60999

   [3/3] ROS 2 daemon
     The daemon is not running
   ========================================================
   ```
   ลองเปลี่ยน Domain ID เป็นอาร์กิวเมนต์ เช่น `domain_check.sh 7` (ได้ 9150) และ `domain_check.sh 120` (จะขึ้นคำเตือนเรื่อง Ephemeral Port)

2. ทดสอบรายงานระบบฉบับละเอียดด้วยคำสั่ง ROS 2 Doctor:
   ```bash
   ./docker/run_lab.sh ros2 doctor --report
   ```
   **คำถาม Checkpoint 1.1:**
   - [ ] RMW Implementation ปัจจุบันของระบบคือตัวใด? (`rmw_fastrtps_cpp` หรือ `rmw_cyclonedds_cpp`)
   - [ ] หมายเลข IP Address ที่คอนเทนเนอร์และโฮสต์แชร์ร่วมกันผ่าน `--net host` มีค่าเท่าใด?

---

### 🔹 Lab 1.2: การทดสอบ Discovery Protocol ผ่าน UDP Multicast
**เป้าหมาย:** สังเกตพฤติกรรมการส่งสัญญาณ Simple Participant Discovery Protocol (SPDP) ระหว่างสองเทอร์มินัล

1. เปิด **Terminal 1** แล้วรันคำสั่งรอรับสัญญาณ Multicast:
   ```bash
   ./docker/run_lab.sh ros2 multicast receive
   ```
   *(คำสั่งจะรอรับแพ็กเก็ต 1 แพ็กเก็ตที่กลุ่ม Multicast `225.0.0.1` พอร์ต UDP `49150` — เป็นการทดสอบว่าเครือข่ายส่ง Multicast ถึงกันได้ ส่วน SPDP ของ DDS จริงใช้กลุ่ม `239.255.0.1` พอร์ต $7400 + 250 \times$ Domain ID)*

2. เปิด **Terminal 2** แล้วส่งสัญญาณ Multicast Heartbeat:
   ```bash
   ./docker/run_lab.sh ros2 multicast send
   ```

3. สังเกตข้อความที่ปรากฏใน Terminal 1:
   ```text
   Waiting for UDP multicast datagram...
   Received from 192.168.31.249:55099: 'Hello World!'
   ```
   (ผลจริง: IP คือที่อยู่ของเครื่องโฮสต์ เพราะคอนเทนเนอร์ใช้ `--net host`; ฝั่ง Terminal 2 พิมพ์ `Sending one UDP multicast datagram...`)

   **คำถาม Checkpoint 1.2:**
   - [ ] หากเครือข่าย Wi-Fi ของห้องปฏิบัติการบล็อก UDP Multicast จะส่งผลต่อการค้นหากันของโหนดหุ่นยนต์อย่างไร?
   - [ ] ทางออกทางวิศวกรรมหากไม่สามารถใช้งาน Multicast ได้คืออะไร? (ใบ้: Unicast Discovery Server)

---

### 🔹 Lab 1.3: การทดสอบแยกแชนเนลด้วย `ROS_DOMAIN_ID`
**เป้าหมาย:** จำลองสถานการณ์หุ่นยนต์ 2 ฝูง (Fleet A และ Fleet B) ทำงานบนเครือข่ายเดียวกัน แต่ต้องการแยกข้อมูลไม่ให้ปะปนกัน

1. **จำลอง Fleet A (Domain ID = 10):**
   - Terminal 1: รัน Talker
     ```bash
     ./docker/run_lab.sh bash -c "export ROS_DOMAIN_ID=10 && ros2 run demo_nodes_py talker"
     ```
   - Terminal 2: รัน Listener ในโดเมนเดียวกัน
     ```bash
     ./docker/run_lab.sh bash -c "export ROS_DOMAIN_ID=10 && ros2 run demo_nodes_py listener"
     ```
   - *ผลลัพธ์:* Terminal 2 ได้รับข้อความ `[INFO] [listener]: I heard: [Hello World: 1]` ปกติ

2. **จำลอง Fleet B (Domain ID = 20):**
   - Terminal 3: รัน Listener ในโดเมน 20
     ```bash
     ./docker/run_lab.sh bash -c "export ROS_DOMAIN_ID=20 && ros2 run demo_nodes_py listener"
     ```
   - *ผลลัพธ์:* Terminal 3 เงียบสนิท ไม่ได้รับข้อความใดๆ จาก Talker โดเมน 10 (ผลรันจริงด้วยโดเมน 11/87 อยู่ใน [`results/domain_isolation.txt`](results/domain_isolation.txt): listener โดเมนเดียวกันได้ `I heard: [Hello World: 0]`... ส่วน listener อีกโดเมนได้ 0 ข้อความ)

3. ทดสอบคำสั่ง CLI `ros2 node list` ในแต่ละโดเมน:
   ```bash
   # ตรวจสอบในโดเมน 10 (จะเห็น talker และ listener)
   ./docker/run_lab.sh bash -c "export ROS_DOMAIN_ID=10 && ros2 node list"

   # ตรวจสอบในโดเมน 20 (จะเห็นเฉพาะ listener ของโดเมน 20)
   ./docker/run_lab.sh bash -c "export ROS_DOMAIN_ID=20 && ros2 node list"
   ```

---

### 🔹 Lab 1.4: การจำกัดการสื่อสารเฉพาะเครื่อง (Localhost Only Isolation)
**เป้าหมาย:** ป้องกันไม่ให้สัญญาณของหุ่นยนต์แพร่กระจายออกสู่เครือข่ายภายนอกระหว่างการพัฒนา (Security & Bandwidth Saving)

1. กำหนดตัวแปร `ROS_AUTOMATIC_DISCOVERY_RANGE`:
   ```bash
   ./docker/run_lab.sh bash -c "export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST && ros2 doctor"
   ```
2. ทดสอบว่าเมื่อเปิดโหมด LOCALHOST แล้ว เครื่องคอมพิวเตอร์อื่นใน Wi-Fi เดียวกันจะไม่สามารถมองเห็นท็อปปิกของเราได้

---

## 🏆 โจทย์ท้าทายระดับสูง (Challenge Exercises)
1. **Challenge 1.1:** เขียนสคริปต์ Bash ชื่อ `port_calculator.sh` ที่รับค่า `DOMAIN_ID` ผ่าน Command Line Argument แล้วคำนวณ:
   - Multicast Discovery Port
   - Unicast Metatraffic Base Port
   - User Traffic Unicast Port
   พร้อมแสดงผลลัพธ์ในรูปแบบตาราง
2. **Challenge 1.2:** ทดลองสลับ RMW Implementation เป็น Cyclone DDS โดยตั้งค่าตัวแปร `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` แล้วทดสอบรัน Talker/Listener เปรียบเทียบ CPU Usage

---

## 📦 สิ่งที่ต้องส่ง (Deliverables Checklist)
- [ ] ไฟล์ภาพบันทึกหน้าจอ (Screenshot) ผลการรัน `domain_check.sh` และ `ros2 doctor --report`
- [ ] ภาพบันทึกหน้าจอแสดงผลการทดลองแยก Domain ID 10 และ 20 พร้อมคำอธิบายผล
- [ ] คำตอบของคำถาม Checkpoint 1.1 และ 1.2 ลงในไฟล์รายงานผลการทดลอง
- [ ] สคริปต์ Challenge `port_calculator.sh` (ถ้ามี)

---

## 📊 เกณฑ์การประเมินผล (Lab Grading Rubric - 100 คะแนน)
| รายการประเมิน | รายละเอียดการให้คะแนน | คะแนนเต็ม |
| :--- | :--- | :---: |
| **ความพร้อมของระบบและ Diagnostic** | รัน `domain_check.sh` และ `ros2 doctor` ผ่าน พร้อมบันทึกภาพรายงานครบถ้วน | 20 |
| **การทดสอบ Multicast Discovery** | อธิบายหลักการของ SPDP และรัน `multicast send/receive` ได้ถูกต้อง | 20 |
| **การทดสอบ Network Partitioning** | ทำการแยก Domain ID 10 และ 20 และพิสูจน์การแยกสัญญาณผ่าน `ros2 node list` | 30 |
| **ความถูกต้องของคำตอบ Checkpoint** | ตอบคำถามเชิงทฤษฎีและเชื่อมโยงกับสถาปัตยกรรม DDS ได้อย่างสมบูรณ์ | 15 |
| **ความสมบูรณ์ของรายงานและโจทย์ท้าทาย** | รายงานเรียบร้อย โค้ด Challenge ทำงานถูกต้องตามสเปก | 15 |
| **รวม** | | **100** |

---

## ⚠️ การแก้ปัญหาที่พบบ่อยในแล็บ (Troubleshooting)
| ปัญหา | สาเหตุ | การแก้ไข |
| :--- | :--- | :--- |
| `ros2 multicast receive` เงียบตลอดเวลา | ไฟร์วอลล์ของเครื่องโฮสต์ (UFW) ปิดกั้น UDP Multicast (เครื่องมือนี้ใช้พอร์ต 49150) | รัน `sudo ufw allow 49150/udp` สำหรับการทดสอบ และ `sudo ufw allow 7400:7700/udp` สำหรับ DDS โดเมน 0–1 บนเครื่อง Host |
| `ros2: command not found` | ไม่ได้ source สภาพแวดล้อม ROS 2 | รันผ่าน `./docker/run_lab.sh <คำสั่ง>` ซึ่งมีการ source อัตโนมัติ |
| สัญญาณรบกวนจากเพื่อนในห้อง | ใช้ `ROS_DOMAIN_ID=0` ซ้ำกันทุกคน | ให้อาจารย์จัดสรรเลขประจำตัว เช่น `ROS_DOMAIN_ID = เลขที่นั่ง` |


## 📟 ผลการรันจริง (Real Run Output)
บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29 — ไฟล์เต็ม: [`results/domain_check_and_doctor.txt`](results/domain_check_and_doctor.txt), [`results/domain_isolation.txt`](results/domain_isolation.txt)
(Fleet A ใช้โดเมน 11 และ Fleet B ใช้โดเมน 87 แทน 10/20 เพราะเครื่องแล็บใช้ร่วมกัน)

```console
$ ROS_DOMAIN_ID=11 ros2 run demo_nodes_py talker          # terminal 1
$ ROS_DOMAIN_ID=11 ros2 run demo_nodes_py listener        # terminal 2
$ ROS_DOMAIN_ID=87 ros2 run demo_nodes_py listener        # terminal 3

$ ROS_DOMAIN_ID=11 ros2 node list
/listener
/talker

$ ROS_DOMAIN_ID=87 ros2 node list
/listener

--- terminal 2 (listener, domain 11):
[INFO] [1793242111.591571080] [listener]: I heard: [Hello World: 0]
[INFO] [1793242112.542117595] [listener]: I heard: [Hello World: 1]
...
--- terminal 3 (listener, domain 87): 0 messages received

$ export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST && ros2 doctor
/opt/ros/jazzy/lib/python3.12/site-packages/ros2doctor/api/__init__.py: 122: UserWarning: Fail to call PackageCheck class functions.

All 4 checks passed
```

---

