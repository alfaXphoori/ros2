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
- เข้าสู่รูทไดเรกทอรี `/mnt/sda/ros`
- ตรวจสอบไวยากรณ์สคริปต์ในสัปดาห์ที่ 3:
  ```bash
  python3 -m py_compile Essential_ROS/Week_03_Services_Clients/src/power_service_server.py
  python3 -m py_compile Essential_ROS/Week_03_Services_Clients/src/power_service_client.py
  ```

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 3.1: การเปิด Server และทดสอบยิงคำขอผ่าน CLI
**เป้าหมาย:** สังเกตพฤติกรรมของ Service Server และการใช้คำสั่ง `ros2 service call`

1. เปิด **Terminal 1** แล้วรันโหนดเซิร์ฟเวอร์:
   ```bash
   ./docker/run_lab.sh python3 Essential_ROS/Week_03_Services_Clients/src/power_service_server.py
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
   **ผลลัพธ์ที่คาดหวัง:**
   ```text
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
   ./docker/run_lab.sh python3 Essential_ROS/Week_03_Services_Clients/src/power_service_client.py true
   ```
   **ผลลัพธ์ที่คาดหวัง:**
   ```text
   [INFO] [power_service_client]: ✅ Service /robot/set_power_mode is online!
   [INFO] [power_service_client]: 🎉 Service Response: success=True, message="Power saving mode ENABLED: ..."
   ```

3. ทดสอบสั่งปิด Eco Mode:
   ```bash
   ./docker/run_lab.sh python3 Essential_ROS/Week_03_Services_Clients/src/power_service_client.py false
   ```

4. ปิด Terminal 1 (กด `Ctrl+C` ที่ Server) แล้วลองรัน Client อีกครั้งใน Terminal 2:
   ```bash
   ./docker/run_lab.sh python3 Essential_ROS/Week_03_Services_Clients/src/power_service_client.py true
   ```
   **คำถาม Checkpoint 3.2:**
   - [ ] เกิดอะไรขึ้นกับโปรแกรม Client เมื่อ Server ปิดตัวลง?
   - [ ] ฟังก์ชันใดที่ทำหน้าที่ป้องกันไม่ให้ Client แคชหลุดตั้งแต่ต้น? (`wait_for_service`)

---

### 🔹 Lab 3.3: การทดลองจำลองและวิเคราะห์ Deadlock
**เป้าหมาย:** สังเกตพฤติกรรมเมื่อโหนดเกิดสภาวะ Deadlock จากการเรียก synchronous call

1. พิจารณาโค้ดตัวอย่างที่ผิดพลาดต่อไปนี้ (อย่าเพิ่งรัน):
   ```python
   # โค้ดที่มีข้อผิดพลาด: การเรียก synchronous call ใน timer_callback
   def timer_callback(self):
       req = SetBool.Request()
       req.data = True
       # ข้อผิดพลาดมหันต์: cli.call() จะบล็อก thread เดี่ยวของ executor
       response = self.cli.call(req)  # <-- ค้างตรงนี้ตลอดกาล!
       self.get_logger().info(f'Done: {response.success}')
   ```
2. อธิบายในรายงาน: ทำไมการใช้ `self.cli.call_async(req)` พร้อม `future.add_done_callback(...)` จึงไม่เกิดปัญหานี้?

---

### 🔹 Lab 3.4: พัฒนาโหนดบริการหยุดฉุกเฉิน Emergency Stop (Hands-on Task)
**เป้าหมาย:** สร้างไฟล์สคริปต์ใหม่ชื่อ `emergency_stop_service.py` ภายในโฟลเดอร์ `src/`

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
