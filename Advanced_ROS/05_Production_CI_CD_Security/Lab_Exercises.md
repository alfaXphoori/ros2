# 🛠️ ใบงานปฏิบัติการที่ 5: Lifecycle State Machine, การทดสอบอัตโนมัติ และ SROS 2
**วิชา:** AMR-201 Advanced ROS 2 & Industrial Fleet Robotics  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** ขั้นสูง (Advanced)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายบทที่ 5](README.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. รันโหนด `lifecycle_laser_sensor` และสังเกตสถานะเริ่มต้น (`Unconfigured`)
2. ใช้คำสั่ง ROS 2 Lifecycle CLI ควบคุมการเปลี่ยนผ่านสถานะ `configure` → `activate` → `deactivate` → `cleanup` / `shutdown`
3. พิสูจน์ด้วย `ros2 topic hz` ว่า `LifecyclePublisher` ไม่ส่งข้อมูลในสถานะ `Inactive` และหยุดจริงหลัง `shutdown`
4. รันชุดทดสอบอัตโนมัติด้วย `colcon test` (`launch_testing` + `pytest`)
5. สร้าง Keystore/Enclave ของ SROS 2 และรัน talker/listener แบบ `Enforce` พร้อมพิสูจน์ว่าโหนดที่ไม่มีใบรับรองรับข้อมูลไม่ได้
6. (ทางเลือก) สลับ middleware เป็น `rmw_zenoh_cpp`

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่ไดเรกทอรีโครงการ `/mnt/sda/ros` และแยกกลุ่มตัวเองก่อนทุก Terminal:
  ```bash
  export ROS_DOMAIN_ID=21 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
  ```
- ตรวจสอบความพร้อมของ `lifecycle_msgs` แล้ว build แพ็กเกจ:
  ```bash
  ./docker/run_lab.sh ros2 interface list | grep -i lifecycle
  ./docker/run_lab.sh colcon build --base-paths Advanced_ROS --packages-select amr_adv05
  ```

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 5.1: รัน Lifecycle Sensor Node และตรวจสอบสถานะ
1. Terminal 1 — รันโหนด:
   ```bash
   ./docker/run_lab.sh ros2 run amr_adv05 lifecycle_laser_sensor
   # หรือโดยไม่ต้อง build: ./docker/run_lab.sh python3 Advanced_ROS/05_Production_CI_CD_Security/src/lifecycle_laser_sensor.py
   ```
   *Log ที่เห็นจริง:* `[lifecycle_laser_sensor]: [LifecycleLaserSensor] Created in UNCONFIGURED state.`

2. Terminal 2 — ตรวจสอบสถานะและ transition ที่ทำได้:
   ```bash
   ./docker/run_lab.sh ros2 lifecycle get /lifecycle_laser_sensor
   ./docker/run_lab.sh ros2 lifecycle list /lifecycle_laser_sensor
   ```
   *ผลลัพธ์จริง:* `unconfigured [1]` และ transition ที่ทำได้คือ `configure [1]`, `shutdown [5]`

---

### 🔹 Lab 5.2: ควบคุมการเปลี่ยนสถานะและการส่งผ่านข้อมูล
1. สั่ง `configure` แล้ววัดอัตราข้อมูล (กด Ctrl-C หลัง ~5 วินาที):
   ```bash
   ./docker/run_lab.sh ros2 lifecycle set /lifecycle_laser_sensor configure
   ./docker/run_lab.sh ros2 topic hz /scan_managed
   ```
   *ข้อสังเกต:* ไม่มี `average rate` ใดๆ แม้ publisher ถูกสร้างแล้ว (สถานะ `inactive [2]`)

2. สั่ง `activate`:
   ```bash
   ./docker/run_lab.sh ros2 lifecycle set /lifecycle_laser_sensor activate
   ./docker/run_lab.sh ros2 topic hz /scan_managed
   ./docker/run_lab.sh ros2 topic echo --once --no-arr /scan_managed
   ```
   *ผลจริง:* `average rate: 9.998` (~10 Hz) และ `angle_increment: 0.01745...` (= 2π/360) — ตรวจว่า `angle_min`/`angle_max`/`angle_increment` สอดคล้องกับจำนวนลำแสง 360

3. สั่ง `deactivate` แล้ววัดอีกครั้ง → ข้อมูลหยุดทันที

4. สั่ง `activate` อีกครั้ง แล้วสั่ง `shutdown` **ขณะ Active**:
   ```bash
   ./docker/run_lab.sh ros2 lifecycle set /lifecycle_laser_sensor activate
   ./docker/run_lab.sh ros2 lifecycle set /lifecycle_laser_sensor shutdown
   ./docker/run_lab.sh ros2 lifecycle get /lifecycle_laser_sensor
   ./docker/run_lab.sh ros2 topic hz /scan_managed
   ```
   *ผลจริง:* `finalized [4]` และไม่มีข้อมูลออกมาอีก

**คำถาม Checkpoint 5.1:**
- หากเซนเซอร์ตรวจจับว่าอุณหภูมิของบอร์ดร้อนเกิน 85°C โค้ดควรเรียกใช้ Transition ใดเพื่อหยุดการทำงานของเซนเซอร์โดยไม่ต้องปิดโปรเซสทิ้ง? (ดู `trigger_deactivate()` ของ `rclpy.lifecycle.LifecycleNode`)
- เปิดดู `on_shutdown()` ใน [`src/lifecycle_laser_sensor.py`](src/lifecycle_laser_sensor.py): ถ้าลบการเรียก `self._release()` ออก ขั้นตอนที่ 4 จะให้ผลอย่างไร? ลองแล้ว build ใหม่ แล้วรันข้อ Lab 5.3 ดูว่ากรณีทดสอบใดล้มเหลว

---

### 🔹 Lab 5.3: รันชุดทดสอบ Integration Test ด้วย launch_testing
1. รันการทดสอบอัตโนมัติ:
   ```bash
   ./docker/run_lab.sh colcon test --base-paths Advanced_ROS --packages-select amr_adv05 --event-handlers console_direct+
   ./docker/run_lab.sh colcon test-result --verbose
   # หรือรันเฉพาะไฟล์ (หลัง build): ./docker/run_lab.sh launch_test Advanced_ROS/05_Production_CI_CD_Security/test/test_lifecycle_launch.py
   ```
2. อ่าน [`test/test_lifecycle_launch.py`](test/test_lifecycle_launch.py) และอธิบายว่าการทดสอบแต่ละข้อตรวจอะไร และทำไมต้องรอ `settle` ก่อนเริ่มนับข้อความ

---

### 🔹 Lab 5.4: SROS 2 — Keystore, Enclave และโหมด Enforce
1. สร้าง keystore และ enclave ของ talker/listener (ตั้ง `ROS_DOMAIN_ID` ก่อน เพราะถูกเขียนลงใน `permissions.xml`):
   ```bash
   KS=Advanced_ROS/05_Production_CI_CD_Security/sros2_keystore     # .gitignore แล้ว
   ./docker/run_lab.sh ros2 security create_keystore $KS
   ./docker/run_lab.sh ros2 security create_enclave $KS /talker_listener/talker
   ./docker/run_lab.sh ros2 security create_enclave $KS /talker_listener/listener
   ./docker/run_lab.sh ros2 security list_enclaves $KS
   grep -A2 "<domains>" $KS/enclaves/talker_listener/talker/permissions.xml
   ```
2. เปิด security แบบ Enforce ใน **ทุก Terminal ที่จะรันโหนดที่ปลอดภัย** (path ต้องเป็น path ภายใน container):
   ```bash
   export ROS_SECURITY_KEYSTORE=/workspace/Advanced_ROS/05_Production_CI_CD_Security/sros2_keystore
   export ROS_SECURITY_ENABLE=true
   export ROS_SECURITY_STRATEGY=Enforce
   ```
3. ลองรัน talker **โดยไม่ใส่ enclave** → ต้องล้มเหลวด้วย `couldn't find all security files!`:
   ```bash
   ./docker/run_lab.sh ros2 run demo_nodes_py talker
   ```
4. รันคู่ที่ปลอดภัย (Terminal 1 และ 2):
   ```bash
   ./docker/run_lab.sh ros2 run demo_nodes_py talker   --ros-args --enclave /talker_listener/talker
   ./docker/run_lab.sh ros2 run demo_nodes_py listener --ros-args --enclave /talker_listener/listener
   ```
5. Terminal 3 — **เปิด Terminal ใหม่ที่ไม่ได้ export `ROS_SECURITY_*`** (แต่ใช้ `ROS_DOMAIN_ID` เดียวกัน) แล้วรัน listener ธรรมดา:
   ```bash
   ./docker/run_lab.sh ros2 run demo_nodes_py listener --ros-args -r __node:=intruder
   ```
   *ผลจริง:* Terminal 2 ได้ `I heard: [Hello World: N]` ทุกวินาที ส่วน Terminal 3 ไม่ได้รับอะไรเลย
6. ทดสอบแบบอัตโนมัติ (สร้าง keystore ใน temp dir และลบเองเมื่อจบ):
   ```bash
   ./docker/run_lab.sh python3 -m pytest -v Advanced_ROS/05_Production_CI_CD_Security/test/test_sros2_enforce.py
   ```
7. เมื่อเสร็จ ลบ keystore (มี private key ของ CA): `rm -rf Advanced_ROS/05_Production_CI_CD_Security/sros2_keystore`

**คำถาม Checkpoint 5.2:**
- ข้อ 3 ล้มเหลวเพราะ `Enforce` หรือเพราะ handshake ของ DDS-Security? ข้อ 5 ล่ะ? (อธิบายความต่าง)
- ถ้าสร้าง enclave ตอน `ROS_DOMAIN_ID=21` แล้วรันโหนดที่ domain 22 จะเกิดอะไรขึ้น? เพราะเหตุใด?

---

### 🔹 Lab 5.5 (ทางเลือก): DDS vs Zenoh
```bash
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
./docker/run_lab.sh ros2 run rmw_zenoh_cpp rmw_zenohd         # Terminal 1: router
./docker/run_lab.sh ros2 run demo_nodes_py talker             # Terminal 2
./docker/run_lab.sh ros2 run demo_nodes_py listener           # Terminal 3
./docker/run_lab.sh bash -c 'ros2 doctor --report | grep -A3 "RMW MIDDLEWARE"'
# Terminal 4: listener แบบ Fast DDS จะไม่ได้ยิน talker แบบ Zenoh
RMW_IMPLEMENTATION=rmw_fastrtps_cpp ./docker/run_lab.sh ros2 run demo_nodes_py listener
```
**คำถาม:** listener ใน Terminal 4 ได้ยิน talker หรือไม่ (ผลรันจริง: `0` บรรทัด)? เพราะอะไร และถ้าระบบมีทั้งหุ่นยนต์ที่ใช้ DDS และที่ใช้ Zenoh ต้องออกแบบอย่างไร?

---

## 📟 ผลการรันจริง (Real Run Output)

บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29 — ฉบับเต็ม: [`results/lifecycle_cli.txt`](results/lifecycle_cli.txt), [`results/sros2_enforce.txt`](results/sros2_enforce.txt), [`results/dds_vs_zenoh.txt`](results/dds_vs_zenoh.txt), [`results/colcon_test.txt`](results/colcon_test.txt)

```console
$ ros2 lifecycle list /lifecycle_laser_sensor
- configure [1]
	Start: unconfigured
	Goal: configuring
- shutdown [5]
	Start: unconfigured
	Goal: shuttingdown
$ ros2 lifecycle set /lifecycle_laser_sensor deactivate
Transitioning successful
$ ros2 topic hz /scan_managed    # (4 s window)
[hz window closed]
----- node log (Terminal 1) -----
[INFO] [1793242321.806568451] [lifecycle_laser_sensor]: [LifecycleLaserSensor] Created in UNCONFIGURED state.
[INFO] [1793242333.435405326] [lifecycle_laser_sensor]: Configuring hardware connection and buffers...
[INFO] [1793242333.508270438] [lifecycle_laser_sensor]: Configured successfully. Transitioned to INACTIVE.
[INFO] [1793242341.142614299] [lifecycle_laser_sensor]: Activating node: starting laser emission & timer...
[WARN] [1793242352.768896796] [lifecycle_laser_sensor]: Deactivating node: pausing laser emission...
[INFO] [1793242358.997172400] [lifecycle_laser_sensor]: Activating node: starting laser emission & timer...
[INFO] [1793242362.077857899] [lifecycle_laser_sensor]: Shutting down sensor node permanently.
```

```console
$ ./docker/run_lab.sh ros2 security list_enclaves Advanced_ROS/05_Production_CI_CD_Security/sros2_keystore
/talker_listener/listener
/talker_listener/talker
# Terminal 1 (secured):
[INFO] [1793242131.411051832] [talker]: Publishing: "Hello World: 0"
# Terminal 2 (secured):
[INFO] [1793242131.421782129] [listener]: I heard: [Hello World: 0]
# Terminal 3 (NO ROS_SECURITY_* variables, same ROS_DOMAIN_ID):
(no output: the unauthenticated participant is not matched by the secured talker; 0 'I heard' lines in 12 s)
```

---

## 📊 เกณฑ์การให้คะแนน (Evaluation Rubrics)
| รายการประเมิน | คะแนนเต็ม | เกณฑ์การพิจารณา |
| :--- | :---: | :--- |
| **1. ความเข้าใจวงจรชีวิต Lifecycle Node** | 30 | สาธิตการเปลี่ยนผ่านสถานะครบ รวมถึง shutdown จาก Active และอธิบายการคืนทรัพยากรได้ |
| **2. ความเข้าใจพฤติกรรม LifecyclePublisher** | 20 | แสดงหลักฐาน `topic hz` ของสถานะ Inactive vs Active vs Finalized ได้ถูกต้อง |
| **3. ทักษะการรันชุดทดสอบ launch_testing** | 15 | สั่งรัน `colcon test` และวิเคราะห์ผลการทดสอบได้ถูกต้อง |
| **4. SROS 2 Enforce** | 25 | สร้าง keystore/enclave รันคู่ secure ได้ และอธิบายความต่างระหว่าง `Enforce` กับ DDS-Security handshake ได้ |
| **5. ความเรียบร้อยและการบันทึกผล** | 10 | บันทึก Log และตอบคำถาม Checkpoint ครบถ้วน |
| **รวม** | **100** | |
