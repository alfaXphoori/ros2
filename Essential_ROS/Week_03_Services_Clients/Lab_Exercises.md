# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 3: ระบบ Service-Client และการป้องกันสภาวะ Deadlock
**วิชา:** AMR-101 Essential ROS 2 for Autonomous Mobile Robots  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** พื้นฐาน (Beginner)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายสัปดาห์ที่ 3](Readme.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. พัฒนาและเปิดใช้งาน **Service Server** สำหรับจัดการโหมดพลังงานของหุ่นยนต์ AMR
2. ทดสอบเรียกใช้ Service ผ่านคำสั่ง CLI และเขียนโหนด **Service Client** แบบ Asynchronous
3. จำลองสภาวะ **Deadlock** ในโหนด ROS 2 เพื่อทำความเข้าใจพฤติกรรมของ Single-Threaded Executor
4. พัฒนาโหนดบริการหยุดฉุกเฉิน `/robot/emergency_stop` ด้วยอินเตอร์เฟซ `std_srvs/srv/Trigger`

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่รูทไดเรกทอรีของ repository วิชา
- Build แพ็กเกจ `amr_week03` (ament_python) — หลัง build แล้ว `run_lab.sh` จะ source `install/setup.bash` ให้อัตโนมัติ:
  ```bash
  ./docker/run_lab.sh colcon build --base-paths Essential_ROS --packages-select amr_week03
  # หรือ: make build PKG=amr_week03      ชุดทดสอบอัตโนมัติ: make test PKG=amr_week03
  ```
- ตั้ง `ROS_DOMAIN_ID` ของตนเองและ `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` ก่อนเรียก `run_lab.sh` ทุก Terminal

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 3.1: การเปิด Server และทดสอบยิงคำขอผ่าน CLI
**เป้าหมาย:** สังเกตพฤติกรรมของ Service Server และการใช้คำสั่ง `ros2 service call`

1. เปิด **Terminal 1** แล้วรันโหนดเซิร์ฟเวอร์:
   ```bash
   ./docker/run_lab.sh ros2 run amr_week03 power_service_server
   # แบบไม่ build: ./docker/run_lab.sh python3 Essential_ROS/Week_03_Services_Clients/src/power_service_server.py
   ```
   **ผลลัพธ์ที่คาดหวัง:** โชว์ข้อความ `⚡ [PowerServiceServer] Service /robot/set_power_mode ready.`

2. เปิด **Terminal 2** แล้วตรวจสอบการมีอยู่ของ Service:
   ```bash
   ./docker/run_lab.sh ros2 service list | grep power_mode
   ```
   *จะปรากฏ:* `/robot/set_power_mode`

3. ทดสอบส่งคำสั่งเปิด Eco Mode ผ่าน CLI:
   ```bash
   ./docker/run_lab.sh ros2 service call /robot/set_power_mode std_srvs/srv/SetBool "{data: true}"
   ```
   **ผลลัพธ์จริง:**
   ```text
   waiting for service to become available...
   requester: making request: std_srvs.srv.SetBool_Request(data=True)

   response:
   std_srvs.srv.SetBool_Response(success=True, message='Power saving mode ENABLED: Max speed capped at 0.3 m/s, sensors throttled.')
   ```

4. ทดสอบส่งคำสั่งปิด Eco Mode (`data: false`):
   ```bash
   ./docker/run_lab.sh ros2 service call /robot/set_power_mode std_srvs/srv/SetBool "{data: false}"
   ```

---

### 🔹 Lab 3.2: การรัน Asynchronous Service Client ผ่าน Python
**เป้าหมาย:** ทดสอบโหนดไคลเอนต์ที่เขียนด้วย Python และส่งพารามิเตอร์ผ่าน Command Line Arguments

1. ให้ Terminal 1 (Server) รันอยู่ต่อเนื่อง
2. ใน **Terminal 2** รันไคลเอนต์เพื่อสั่งเปิด Eco Mode:
   ```bash
   ./docker/run_lab.sh ros2 run amr_week03 power_service_client true
   ```
   **ผลลัพธ์จริง:**
   ```text
   [INFO] [1793242470.096880256] [power_service_client]: ⏳ Service /robot/set_power_mode not available, waiting...
   [INFO] [1793242471.098164656] [power_service_client]: ⏳ Service /robot/set_power_mode not available, waiting...
   [INFO] [1793242471.598807733] [power_service_client]: ✅ Service /robot/set_power_mode is online!
   [INFO] [1793242471.937008353] [power_service_client]: 🎉 Service Response: success=True, message="Power saving mode ENABLED: Max speed capped at 0.3 m/s, sensors throttled."
   (exit 0)
   ```
   บรรทัด `not available, waiting...` 1–2 ครั้งแรกเกิดขึ้นแม้ Server รันอยู่ เพราะโปรเซสใหม่ต้องใช้เวลา DDS Discovery ประมาณ 1–2 วินาทีก่อนจะเห็น Service

3. ทดสอบสั่งปิด Eco Mode — อาร์กิวเมนต์ของ ROS (`--ros-args ...`) ต่อท้ายได้โดยไม่รบกวนค่า `false` เพราะโค้ดใช้ `rclpy.utilities.remove_ros_args()`:
   ```bash
   ./docker/run_lab.sh ros2 run amr_week03 power_service_client false --ros-args --log-level info
   ```

4. ปิด Terminal 1 (กด `Ctrl+C` ที่ Server) แล้วลองรัน Client อีกครั้งใน Terminal 2 (ให้รอไม่เกิน 3 วินาที):
   ```bash
   ./docker/run_lab.sh ros2 run amr_week03 power_service_client true --wait 3
   ```
   **ผลลัพธ์จริง:**
   ```text
   [INFO] [1793242485.479840564] [power_service_client]: ⏳ Service /robot/set_power_mode not available, waiting...
   [INFO] [1793242486.482134171] [power_service_client]: ⏳ Service /robot/set_power_mode not available, waiting...
   [ERROR] [1793242487.484014711] [power_service_client]: ❌ Service /robot/set_power_mode not available after 3 s
   [ros2run]: Process exited with failure 1
   (exit 1)
   ```
   **คำถาม Checkpoint 3.2:**
   - [ ] เกิดอะไรขึ้นกับโปรแกรม Client เมื่อ Server ปิดตัวลง?
   - [ ] ฟังก์ชันใดที่ทำหน้าที่ตรวจว่า Server พร้อมก่อนส่งคำขอ และเหตุใดจึงควรมีเวลารอสูงสุด (`--wait`) แทนการรอไม่รู้จบ? (`wait_for_service`)

---

### 🔹 Lab 3.3: การทดลองจำลองและวิเคราะห์ Deadlock
**เป้าหมาย:** สังเกตพฤติกรรมเมื่อโหนดเกิดสภาวะ Deadlock จากการเรียก synchronous call

1. พิจารณาโค้ดตัวอย่างที่ผิดพลาดต่อไปนี้:
   ```python
   # โค้ดที่มีข้อผิดพลาด: การเรียก synchronous call ใน timer_callback
   def timer_callback(self):
       req = SetBool.Request()
       req.data = True
       # ข้อผิดพลาดมหันต์: cli.call() จะบล็อก thread เดี่ยวของ executor
       response = self.cli.call(req)  # <-- ค้างตรงนี้ตลอดกาล!
       self.get_logger().info(f'Done: {response.success}')
   ```
2. ให้ Server (Terminal 1) รันอยู่ แล้วรันเดโมที่จำลองโค้ดข้างต้นจริง ([`src/deadlock_demo.py`](src/deadlock_demo.py) ใส่ `timeout_sec=3.0` ไว้เพื่อให้จบเองได้):
   ```bash
   ./docker/run_lab.sh ros2 run amr_week03 deadlock_demo --mode deadlock
   ./docker/run_lab.sh ros2 run amr_week03 deadlock_demo --mode fixed
   ```
   **ผลลัพธ์จริง:**
   ```text
   $ ros2 run amr_week03 deadlock_demo --mode deadlock
   [INFO] [1793242477.681160219] [deadlock_demo]: Calling /robot/set_power_mode synchronously (client.call) from inside a timer callback...
   [ERROR] [1793242480.681728307] [deadlock_demo]: 💥 DEADLOCK: no response after 3.0 s - the executor thread was blocked inside this callback and could not deliver the reply
   outcome: timeout
   (exit 0)
   
   $ ros2 run amr_week03 deadlock_demo --mode fixed
   [INFO] [1793242483.539736758] [deadlock_demo]: Calling /robot/set_power_mode synchronously (client.call) from inside a timer callback...
   [INFO] [1793242483.541472468] [deadlock_demo]: ✅ Response after 0.001 s: success=True (another executor thread delivered it)
   outcome: success
   (exit 0)
   ```
3. สังเกต Log ของ Server ใน Terminal 1: ในโหมด `deadlock` Server ตอบกลับทันที แต่ Client ยังได้ `None` — อธิบายในรายงานว่าเหตุใด และทำไม `--mode fixed` (`MultiThreadedExecutor` + `ReentrantCallbackGroup`) หรือการใช้ `self.cli.call_async(req)` พร้อม `future.add_done_callback(...)` จึงไม่เกิดปัญหานี้

---

### 🔹 Lab 3.4: พัฒนาโหนดบริการหยุดฉุกเฉิน Emergency Stop (Hands-on Task)
**เป้าหมาย:** สร้างไฟล์สคริปต์ใหม่ชื่อ `emergency_stop_service.py` ภายในโฟลเดอร์ `src/` แล้วเพิ่ม `'emergency_stop_service = amr_week03.emergency_stop_service:main'` ใน `entry_points` ของ [`setup.py`](setup.py) และ build ใหม่ เพื่อให้รันด้วย `ros2 run amr_week03 emergency_stop_service` ได้

**ข้อกำหนดทางวิศวกรรม:**
1. สร้าง Service Server ชื่อ `/robot/emergency_stop` โดยใช้อินเตอร์เฟซ `std_srvs/srv/Trigger`
2. โครงสร้างของ `std_srvs/srv/Trigger`:
   - Request: ไม่มีข้อมูลส่งเข้า
   - Response: `bool success`, `string message`
3. การทำงาน:
   - เมื่อได้รับสัญญาณ Request ให้ตั้งค่าสถานะ `self.is_stopped = True`
   - พิมพ์ Warning Log สีเหลือง: `🚨 EMERGENCY STOP TRIGGERED! Cutting all motor power.`
   - ตอบกลับ `response.success = True` และ `response.message = 'Robot halted safely.'`
4. ทดสอบความถูกต้องด้วยคำสั่ง:
   ```bash
   ./docker/run_lab.sh ros2 service call /robot/emergency_stop std_srvs/srv/Trigger "{}"
   ```

---

## 🏆 โจทย์ท้าทายระดับสูง (Challenge Exercises)
1. **Challenge 3.1:** เพิ่มฟังก์ชัน Reset ในโหนดหยุดฉุกเฉิน โดยสร้าง Service อีกตัวชื่อ `/robot/emergency_reset` เมื่อถูกเรียกจะปลดล็อกสถานะ `is_stopped = False`
2. **Challenge 3.2:** สร้างโหนด Client ที่เรียกใช้ `MultiThreadedExecutor` ร่วมกับ `ReentrantCallbackGroup` เพื่อส่งคำขอบริการพร้อมกันจาก 2 Thread คู่ขนาน

---

## 📦 สิ่งที่ต้องส่ง (Deliverables Checklist)
- [ ] ภาพบันทึกหน้าจอผลการทดสอบ `ros2 service call` ทั้งโหมดเปิดและปิด Eco Mode
- [ ] ภาพบันทึกหน้าจอการรัน `power_service_client.py` ทั้งสองสถานะ
- [ ] ไฟล์โค้ด `emergency_stop_service.py` ที่สร้างขึ้นใหม่ใน Lab 3.4
- [ ] ภาพบันทึกหน้าจอการทดสอบ Service `/robot/emergency_stop` ผ่าน CLI
- [ ] คำตอบ Checkpoint 3.2 และบทวิเคราะห์ Deadlock

---

## 📊 เกณฑ์การประเมินผล (Lab Grading Rubric - 100 คะแนน)
| รายการประเมิน | รายละเอียดการให้คะแนน | คะแนนเต็ม |
| :--- | :--- | :---: |
| **การทดสอบ Service ผ่าน CLI** | ควบคุมโหมดพลังงานผ่านคำสั่ง `ros2 service call` ได้ถูกต้อง | 20 |
| **การใช้งาน Asynchronous Client** | รันและส่ง Argument ผ่าน `power_service_client.py` ได้สมบูรณ์ | 20 |
| **การวิเคราะห์สภาวะ Deadlock** | อธิบายกลไกของ Thread และ Executor ได้อย่างถูกต้องตามหลักการ | 20 |
| **การพัฒนา Emergency Stop Service** | โค้ด Lab 3.4 ทำงานสมบูรณ์ ใช้ Trigger Interface ถูกต้อง | 30 |
| **ความเรียบร้อยของรายงานและโจทย์ท้าทาย** | รายงานละเอียด มีผลทดสอบและบทสรุปชัดเจน | 10 |
| **รวม** | | **100** |

---

## ⚠️ การแก้ปัญหาที่พบบ่อยในแล็บ (Troubleshooting)
| ปัญหา | สาเหตุ | การแก้ไข |
| :--- | :--- | :--- |
| `TypeError: 'Request' object is not callable` | ประกาศตัวแปรคำขอผิด เช่น ใส่ `SetBool.Request(...)` โดยไม่ได้นำเข้าคลาส | ตรวจสอบ `from std_srvs.srv import SetBool` |
| CLI ขึ้น error: `Invalid YAML` | ไม่ได้ใส่เครื่องหมายคำพูดรอบ dictionary หรือเว้นวรรคผิด | ใช้รูปแบบ: `"{data: true}"` หรือ `"{}"` สำหรับ Trigger |
| Client รันแล้วจบการทำงานทันทีโดยไม่ได้คำตอบ | ลืมสั่ง `rclpy.spin_until_future_complete(client, future)` | ตรวจสอบว่ามีคำสั่ง spin รอ future ครบถ้วน |
| `error: argument mode: invalid choice` หรืออ่านค่าผิดเมื่อรันผ่าน `ros2 launch` | อ่าน `sys.argv[1]` ตรงๆ ซึ่งอาจเป็น `--ros-args` | ใช้ `rclpy.utilities.remove_ros_args(sys.argv)` ก่อน parse อาร์กิวเมนต์ |


## 📟 ผลการรันจริง (Real Run Output)
บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29 — ไฟล์เต็ม: [`results/service_lab_run.txt`](results/service_lab_run.txt)

```console
$ ros2 run amr_week03 power_service_server     # terminal 1

$ ros2 service list | grep power_mode
/robot/set_power_mode

$ ros2 service call /robot/set_power_mode std_srvs/srv/SetBool "{data: false}"
waiting for service to become available...
requester: making request: std_srvs.srv.SetBool_Request(data=False)

--- terminal 1 (server) output:
[INFO] [1793242458.786830702] [power_service_server]: ⚡ [PowerServiceServer] Service /robot/set_power_mode ready.
[WARN] [1793242465.522718787] [power_service_server]: Power saving mode ENABLED: Max speed capped at 0.3 m/s, sensors throttled.
[INFO] [1793242468.525688456] [power_service_server]: Normal power mode RESTORED: Full speed 0.8 m/s enabled.
[WARN] [1793242471.933810309] [power_service_server]: Power saving mode ENABLED: Max speed capped at 0.3 m/s, sensors throttled.
...
```

---

