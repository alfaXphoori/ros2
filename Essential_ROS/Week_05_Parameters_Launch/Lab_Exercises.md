# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 5: Dynamic Parameters และสถาปัตยกรรม Python Launch System
**วิชา:** AMR-101 Essential ROS 2 for Autonomous Mobile Robots  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** พื้นฐาน (Beginner)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายสัปดาห์ที่ 5](Readme.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. ตรวจสอบ อ่านค่า และเปลี่ยนค่า **ROS 2 Parameters** แบบเรียลไทม์ผ่าน CLI
2. ทดสอบระบบความปลอดภัย **Parameter Validation** และสังเกตการปฏิเสธค่าผิดพลาด
3. เปิดระบบหุ่นยนต์แบบบูรณาการด้วย **Python Launch System** (`core_system.launch.py`)
4. สร้างและโหลดไฟล์การตั้งค่า **YAML Parameter File** เข้าสู่ระบบผ่านคำสั่งเปิดใช้งาน

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่รูทไดเรกทอรีของ repository วิชา
- Build แพ็กเกจ `amr_week05` พร้อมแพ็กเกจที่ Launch File ต้องใช้ (`amr_week02`–`amr_week04`):
  ```bash
  ./docker/run_lab.sh colcon build --base-paths Essential_ROS --packages-up-to amr_week05
  # หรือ: make build PKG=amr_week05      ชุดทดสอบอัตโนมัติ: make test PKG=amr_week05
  ```
- ตั้ง `ROS_DOMAIN_ID` ของตนเองและ `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` ก่อนเรียก `run_lab.sh` ทุก Terminal

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 5.1: การจัดการ Parameters ผ่าน CLI
**เป้าหมาย:** ทำความเข้าใจการตรวจสอบและแก้ไขพารามิเตอร์ของโหนดในขณะทำงาน

1. เปิด **Terminal 1** แล้วรันโหนดพารามิเตอร์:
   ```bash
   ./docker/run_lab.sh ros2 run amr_week05 fleet_parameters
   # แบบไม่ build: ./docker/run_lab.sh python3 Essential_ROS/Week_05_Parameters_Launch/src/fleet_parameters.py
   ```
   **ผลลัพธ์ที่คาดหวัง:**
   ```text
   [INFO] [fleet_parameters]: 🤖 [FleetParametersNode] Initialized: ID=AMR_ALPHA_01, MaxSpeed=0.8m/s, Margin=0.35m
   ```

2. เปิด **Terminal 2** แล้วเรียกดูรายชื่อพารามิเตอร์ทั้งหมดของโหนด:
   ```bash
   ./docker/run_lab.sh ros2 param list /fleet_parameters
   ```
   *จะปรากฏ* (ผลจริง — `start_type_description_service` และ `use_sim_time` เป็นพารามิเตอร์ที่ทุกโหนดใน Jazzy มีให้อัตโนมัติ):
   ```text
     enable_obstacle_stop
     fleet_id
     max_linear_speed
     safety_margin
     start_type_description_service
     use_sim_time
   ```
   ดูชนิดและข้อจำกัดด้วย `ros2 param describe /fleet_parameters max_linear_speed`

3. อ่านค่าความเร็วสูงสุดปัจจุบัน:
   ```bash
   ./docker/run_lab.sh ros2 param get /fleet_parameters max_linear_speed
   ```
   *ผลลัพธ์:* `Double value is: 0.8`

4. ทดลองปรับความเร็วเป็นค่าที่ปลอดภัย (เช่น 1.2 m/s):
   ```bash
   ./docker/run_lab.sh ros2 param set /fleet_parameters max_linear_speed 1.2
   ```
   *ผลลัพธ์:* `Set parameter successful` และใน Terminal 1 จะมี Log `[WARN] ... ⚡ max_linear_speed updated to: 1.2 m/s` (Log นี้มาจาก `add_post_set_parameters_callback` จึงพิมพ์เฉพาะเมื่อค่าถูกบันทึกจริง) — ตรวจว่าโหนดนำค่าไปใช้ด้วย `./docker/run_lab.sh ros2 topic echo --once /speed_limit` (ได้ `data: 1.2`)

---

### 🔹 Lab 5.2: การทดสอบระบบตรวจสอบความปลอดภัย (Validation Test)
**เป้าหมาย:** สังเกตการปฏิเสธค่าพารามิเตอร์ที่เป็นอันตรายต่อหุ่นยนต์

1. ทดลองตั้งค่าความเร็วเกินขีดจำกัดความปลอดภัย (เช่น 3.5 m/s):
   ```bash
   ./docker/run_lab.sh ros2 param set /fleet_parameters max_linear_speed 3.5
   ```
   **ผลลัพธ์ที่คาดหวัง:**
   ```text
   Setting parameter failed: Speed 3.5 is outside valid safety range [0.1, 2.5] m/s!
   ```
2. ทดลองตั้งค่าระยะเผื่อความปลอดภัยที่อันตรายเกินไป (`safety_margin` เป็น 0.05 m):
   ```bash
   ./docker/run_lab.sh ros2 param set /fleet_parameters safety_margin 0.05
   ```
   *ผลลัพธ์:* ถูกปฏิเสธพร้อมข้อความ `Setting parameter failed: safety_margin cannot be smaller than 0.1 m!`
3. ทดลองส่งค่าที่เป็นจำนวนเต็ม (ไม่มีจุดทศนิยม):
   ```bash
   ./docker/run_lab.sh ros2 param set /fleet_parameters max_linear_speed 1
   ```
   *ผลลัพธ์จริง:* `Setting parameter failed: Wrong parameter type, expected 'Type.DOUBLE' got 'Type.INTEGER'` — ข้อความนี้มาจาก rclpy (ชั้นที่ 1) ไม่ใช่จาก Callback ของเรา ลองเติม `print()` ใน `validate_parameters` แล้วสังเกตว่าไม่ถูกเรียกเลย

   **คำถาม Checkpoint 5.2:**
   - [ ] กลไก Dynamic Parameter Callback ช่วยป้องกันอุบัติเหตุในโรงงานอย่างไร?
   - [ ] หากไม่มีระบบ Validation หุ่นยนต์ที่รับค่า speed = 100 m/s จะเกิดพฤติกรรมอย่างไร?

---

### 🔹 Lab 5.3: การรันระบบ Core ด้วย Python Launch System
**เป้าหมาย:** เปิดใช้งานโหนดทั้งหมดพร้อมกันด้วยคำสั่งเดียวผ่าน `ros2 launch`

1. ปิดโปรเซสเดิมทั้งหมดในทุก Terminal (กด `Ctrl+C`)
2. รันสคริปต์ Launch ของระบบสื่อสารหลัก:
   ```bash
   ./docker/run_lab.sh ros2 launch amr_week05 core_system.launch.py
   ```
3. เปิดอีก Terminal หนึ่งแล้วตรวจสอบโหนดที่กำลังทำงาน:
   ```bash
   ./docker/run_lab.sh ros2 node list
   ```
   **ผลลัพธ์ที่คาดหวัง:** ต้องปรากฏครบทั้ง 4 โหนด:
   - `/sensor_qos_publisher`
   - `/power_service_server`
   - `/navigate_action_server`
   - `/fleet_parameters`

4. ตรวจสอบท็อปปิก, เซอร์วิส และแอ็กชันที่เปิดขึ้นพร้อมกัน:
   ```bash
   ./docker/run_lab.sh ros2 topic list
   ./docker/run_lab.sh ros2 service list
   ./docker/run_lab.sh ros2 action list
   ```
5. ปิด Launch แล้วรันใหม่แบบใส่ Namespace และ Fleet ID ของหุ่นยนต์:
   ```bash
   ./docker/run_lab.sh ros2 launch amr_week05 core_system.launch.py robot_ns:=amr_01 fleet_id:=AMR_01
   ```
   **ผลลัพธ์จริง** — ทุกโหนดและทุกอินเทอร์เฟซย้ายไปอยู่ใต้ `/amr_01`:
   ```text
   $ ros2 node list
   /amr_01/fleet_parameters
   /amr_01/navigate_action_server
   /amr_01/power_service_server
   /amr_01/sensor_qos_publisher

   $ ros2 topic list
   /amr_01/robot/state
   /amr_01/sensor/temperature
   /amr_01/speed_limit
   /parameter_events
   /rosout

   $ ros2 action list
   /amr_01/navigate_distance

   $ ros2 param get /amr_01/fleet_parameters fleet_id
   String value is: AMR_01
   ```

---

### 🔹 Lab 5.4: การสร้างไฟล์ YAML Parameter และโหลดผ่าน Launch
**เป้าหมาย:** จัดเก็บการตั้งค่าแบบรวมศูนย์ด้วย YAML

1. ดูไฟล์คอนฟิกตั้งต้นของแพ็กเกจ [`config/fleet_params.yaml`](config/fleet_params.yaml) (ใช้คีย์ `/**` จึงใช้ได้กับทุก Namespace) แล้วสร้างไฟล์ `my_fleet_config.yaml` ของตนเองด้วยคำสั่ง Dump:
   ```bash
   ./docker/run_lab.sh ros2 param dump /fleet_parameters
   ```
2. ทำความเข้าใจโครงสร้างของไฟล์ YAML สำหรับ ROS 2 Parameters:
   ```yaml
   /fleet_parameters:
     ros__parameters:
       enable_obstacle_stop: true
       fleet_id: AMR_BETA_99
       max_linear_speed: 1.5
       safety_margin: 0.5
   ```
3. โหลดไฟล์ผ่าน Launch Argument `params_file` (ค่า `fleet_id` จาก Launch Argument จะทับค่าในไฟล์):
   ```bash
   ./docker/run_lab.sh ros2 launch amr_week05 core_system.launch.py params_file:=/workspace/my_fleet_config.yaml
   ```
   (พาธต้องเป็นพาธภายในคอนเทนเนอร์ — repository ถูก mount ไว้ที่ `/workspace`)

---

## 🏆 โจทย์ท้าทายระดับสูง (Challenge Exercises)
1. **Challenge 5.1:** เพิ่ม Launch Argument `log_level` (ค่าปริยาย `info`) ใน `core_system.launch.py` แล้วส่งต่อให้ทุกโหนดผ่าน `ros_arguments=['--log-level', log_level]`
2. **Challenge 5.2:** เขียน Launch File ใหม่ที่ `IncludeLaunchDescription` ไฟล์ `core_system.launch.py` สองครั้งด้วย `robot_ns:=robot1` และ `robot_ns:=robot2` (คนละ `fleet_id`) แล้วพิสูจน์ด้วย `ros2 node list` ว่าไม่มีชื่อชนกัน

---

## 📦 สิ่งที่ต้องส่ง (Deliverables Checklist)
- [ ] ภาพบันทึกหน้าจอผลการสั่ง `ros2 param set` ทั้งกรณีสำเร็จและกรณีถูกปฏิเสธ (Validation Error)
- [ ] ภาพบันทึกหน้าจอผลการรัน `ros2 launch core_system.launch.py` พร้อมแสดง `ros2 node list` ครบ 4 โหนด
- [ ] ไฟล์บันทึกพารามิเตอร์ YAML จากคำสั่ง `ros2 param dump`
- [ ] คำตอบ Checkpoint 5.2

---

## 📊 เกณฑ์การประเมินผล (Lab Grading Rubric - 100 คะแนน)
| รายการประเมิน | รายละเอียดการให้คะแนน | คะแนนเต็ม |
| :--- | :--- | :---: |
| **การจัดการ Parameters ผ่าน CLI** | อ่านและเปลี่ยนค่าผ่านคำสั่ง `ros2 param` ได้คล่องแคล่ว | 20 |
| **การทดสอบ Parameter Validation** | สาธิตและอธิบายการปฏิเสธค่าผิดพลาดทั้งสองกรณีได้ถูกต้อง | 20 |
| **การใช้งาน Python Launch System** | รัน `core_system.launch.py` สำเร็จและมีโหนดขึ้นครบสมบูรณ์ | 30 |
| **การจัดการ YAML Configuration** | อธิบายโครงสร้างและการ dump พารามิเตอร์เป็น YAML | 20 |
| **ความเรียบร้อยของรายงานและโจทย์ท้าทาย** | รายงานละเอียด โค้ดคอมไพล์ผ่าน ไวยากรณ์ถูกต้อง | 10 |
| **รวม** | | **100** |

---

## ⚠️ การแก้ปัญหาที่พบบ่อยในแล็บ (Troubleshooting)
| ปัญหา | สาเหตุ | การแก้ไข |
| :--- | :--- | :--- |
| Launch ขึ้น `package 'amr_week02' not found` หรือ `executable ... not found` | ยังไม่ได้ build แพ็กเกจที่ Launch อ้างถึง | `./docker/run_lab.sh colcon build --base-paths Essential_ROS --packages-up-to amr_week05` |
| Parameter ไม่ยอมอัปเดต | ส่งชื่อโหนดไม่ครบ เช่น ขาด `/` ข้างหน้า | ตรวจสอบชื่อเต็มด้วย `ros2 node list` |
| ข้อความ SyntaxError ในไฟล์ Launch | เขียนไวยากรณ์ Python ใน Launch File ไม่ถูกต้อง | ตรวจสอบด้วย `python3 -m py_compile <launch_file>` |
| `Node not found` เมื่อ `ros2 param get /fleet_parameters ...` หลังใส่ `robot_ns` | โหนดย้ายไปอยู่ใต้ Namespace แล้ว | ใช้ชื่อเต็ม เช่น `/amr_01/fleet_parameters` |


## 📟 ผลการรันจริง (Real Run Output)
บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29 (รันด้วย `robot_ns:=amr_01`) — ไฟล์เต็ม: [`results/launch_and_params_run.txt`](results/launch_and_params_run.txt)

```console
$ ros2 param describe /amr_01/fleet_parameters max_linear_speed
Parameter name: max_linear_speed
  Type: double
  Description: Speed limit [m/s]
  Constraints:
    Additional constraints: 0.1 <= value <= 2.5

$ ros2 param set /amr_01/fleet_parameters safety_margin 0.05
Setting parameter failed: safety_margin cannot be smaller than 0.1 m!

$ ros2 param dump /amr_01/fleet_parameters
/amr_01/fleet_parameters:
  ros__parameters:
    enable_obstacle_stop: true
    fleet_id: AMR_01
    max_linear_speed: 1.2
    safety_margin: 0.35
    start_type_description_service: true
    use_sim_time: false

--- terminal 1 (ros2 launch) output:
...
[WARNING] [launch]: user interrupted with ctrl-c (SIGINT)
[WARNING] [launch]: user interrupted with ctrl-c (SIGINT) again, ignoring...
[INFO] [fleet_parameters-4]: sending signal 'SIGINT' to process[fleet_parameters-4]
[INFO] [navigate_action_server-3]: sending signal 'SIGINT' to process[navigate_action_server-3]
[INFO] [power_service_server-2]: sending signal 'SIGINT' to process[power_service_server-2]
[INFO] [sensor_qos_publisher-1]: sending signal 'SIGINT' to process[sensor_qos_publisher-1]
[INFO] [fleet_parameters-4]: process has finished cleanly [pid 97]
[INFO] [navigate_action_server-3]: process has finished cleanly [pid 96]
[INFO] [power_service_server-2]: process has finished cleanly [pid 95]
[INFO] [sensor_qos_publisher-1]: process has finished cleanly [pid 94]
```

---

