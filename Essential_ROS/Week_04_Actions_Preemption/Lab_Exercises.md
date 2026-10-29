# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 4: Action Protocol สำหรับงานระยะยาว และการยกเลิกเป้าหมาย
**วิชา:** AMR-101 Essential ROS 2 for Autonomous Mobile Robots  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** พื้นฐาน (Beginner)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายสัปดาห์ที่ 4](Readme.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. พัฒนาและเปิดใช้งาน **Action Server** สำหรับควบคุมลำดับระยะทางการเคลื่อนที่ของหุ่นยนต์
2. ส่งคำสั่ง Goal ผ่านคำสั่ง CLI พร้อมเปิดรับ Feedback แบบ Real-Time ด้วยแฟล็ก `-f`
3. พัฒนาโหนด **Action Client** ในภาษา Python ที่รองรับ Feedback Callback และ Result Callback
4. ทดสอบและตรวจสอบพฤติกรรมการยกเลิกเป้าหมายกลางคัน (**Cancellation**) และการแทนที่ด้วยเป้าหมายใหม่ (**Preemption**)

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่รูทไดเรกทอรีของ repository วิชา
- Build แพ็กเกจ `amr_week04` (ament_python) — หลัง build แล้ว `run_lab.sh` จะ source `install/setup.bash` ให้อัตโนมัติ:
  ```bash
  ./docker/run_lab.sh colcon build --base-paths Essential_ROS --packages-select amr_week04
  # หรือ: make build PKG=amr_week04      ชุดทดสอบอัตโนมัติ: make test PKG=amr_week04
  ```
- ตั้ง `ROS_DOMAIN_ID` ของตนเองและ `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` ก่อนเรียก `run_lab.sh` ทุก Terminal

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 4.1: การเปิด Server และทดสอบส่ง Goal ผ่าน CLI พร้อมสตรีม Feedback
**เป้าหมาย:** ทำความเข้าใจพฤติกรรมการส่งเป้าหมายและการรับสตรีม Feedback ทาง Command Line

1. เปิด **Terminal 1** แล้วรันโหนดเซิร์ฟเวอร์:
   ```bash
   ./docker/run_lab.sh ros2 run amr_week04 navigate_action_server
   # แบบไม่ build: ./docker/run_lab.sh python3 Essential_ROS/Week_04_Actions_Preemption/src/navigate_action_server.py
   ```
   **ผลลัพธ์ที่คาดหวัง:**
   ```text
   [INFO] [navigate_action_server]: 🏁 [NavigateActionServer] Ready to receive navigation distance goals.
   ```

2. เปิด **Terminal 2** แล้วตรวจสอบการมีอยู่ของ Action ในระบบ:
   ```bash
   ./docker/run_lab.sh ros2 action list -t
   ```
   *จะปรากฏ:* `/navigate_distance [example_interfaces/action/Fibonacci]`

3. ส่ง Goal ขนาด 6 สเต็ป พร้อมแฟล็ก `-f` เพื่อดูสตรีม Feedback สด:
   ```bash
   ./docker/run_lab.sh ros2 action send_goal -f /navigate_distance example_interfaces/action/Fibonacci "{order: 6}"
   ```
   **ผลลัพธ์จริง** (Feedback 5 ครั้ง ตัดตอนกลางออก — Goal `order: 6` ได้ 7 ตัวเลข เพราะ Server เริ่มจาก `[0, 1]` แล้วเพิ่มอีก `order - 1` ตัว):
   ```text
   Waiting for an action server to become available...
   Sending goal:
        order: 6

   Goal accepted with ID: e1c29fa196924e44b277d032e47c3313

   Feedback:
       sequence:
   - 0
   - 1
   - 1

   ...
   Result:
       sequence:
   - 0
   - 1
   - 1
   - 2
   - 3
   - 5
   - 8

   Goal finished with status: SUCCEEDED
   ```

---

### 🔹 Lab 4.2: การรัน Python Action Client รับผลลัพธ์สมบูรณ์
**เป้าหมาย:** ทดสอบการทำงานของ `navigate_action_client.py` ในสภาวะปกติ

1. ให้ Terminal 1 (Server) รันอยู่ต่อเนื่อง
2. ใน **Terminal 2** รันโหนด Action Client:
   ```bash
   ./docker/run_lab.sh ros2 run amr_week04 navigate_action_client
   ```
   **ผลลัพธ์จริง:**
   ```text
   [INFO] [1793242442.697342103] [navigate_action_client]: ⏳ Waiting for navigate_distance action server...
   [INFO] [1793242445.449600242] [navigate_action_client]: 🚀 Sending goal with order=6...
   [INFO] [1793242445.454683575] [navigate_action_client]: ✅ Goal accepted (id=518e10d5...) Executing...
   [INFO] [1793242445.460612350] [navigate_action_client]: 📊 Feedback received: sequence=[0, 1, 1]
   [INFO] [1793242445.959403152] [navigate_action_client]: 📊 Feedback received: sequence=[0, 1, 1, 2]
   [INFO] [1793242446.459976885] [navigate_action_client]: 📊 Feedback received: sequence=[0, 1, 1, 2, 3]
   [INFO] [1793242446.961430594] [navigate_action_client]: 📊 Feedback received: sequence=[0, 1, 1, 2, 3, 5]
   [INFO] [1793242447.461573889] [navigate_action_client]: 📊 Feedback received: sequence=[0, 1, 1, 2, 3, 5, 8]
   [INFO] [1793242447.962659189] [navigate_action_client]: 🏁 Goal finished: status=SUCCEEDED, sequence=[0, 1, 1, 2, 3, 5, 8]
   (exit 0)
   ```

---

### 🔹 Lab 4.3: การยกเลิกกลางคัน (Cancellation) และการแทนที่ด้วยเป้าหมายใหม่ (Preemption)
**เป้าหมาย:** พิสูจน์ว่าเมื่อเกิดเหตุการณ์ไม่คาดคิด ไคลเอนต์สามารถสั่งยกเลิกงานได้อย่างปลอดภัย และ Goal ใหม่สามารถแทนที่ Goal เดิมได้

1. รันไคลเอนต์ในโหมดยกเลิกภารกิจ (ส่ง Cancel หลัง 1.5 วินาที; รูปแบบเดิม `--cancel` ก็ใช้ได้):
   ```bash
   ./docker/run_lab.sh ros2 run amr_week04 navigate_action_client cancel
   ```
2. สังเกตการทำงานใน Terminal ทั้งสอง — ไคลเอนต์ต้อง **ได้สถานะ `CANCELED` แล้วออกจากโปรแกรมเอง** (ผลจริง):
   ```text
   [INFO] [1793242448.569637315] [navigate_action_client]: ⏳ Waiting for navigate_distance action server...
   [INFO] [1793242448.820180528] [navigate_action_client]: 🚀 Sending goal with order=6...
   [INFO] [1793242448.821784104] [navigate_action_client]: ✅ Goal accepted (id=0d1c6395...) Executing...
   [INFO] [1793242448.822987237] [navigate_action_client]: 📊 Feedback received: sequence=[0, 1, 1]
   [INFO] [1793242449.324273212] [navigate_action_client]: 📊 Feedback received: sequence=[0, 1, 1, 2]
   [INFO] [1793242449.824384242] [navigate_action_client]: 📊 Feedback received: sequence=[0, 1, 1, 2, 3]
   [WARN] [1793242450.322448677] [navigate_action_client]: 🛑 Sending cancel request now...
   [WARN] [1793242450.324227506] [navigate_action_client]: 🛑 Cancel request accepted by server.
   [INFO] [1793242450.325729869] [navigate_action_client]: 🏁 Goal finished: status=CANCELED, sequence=[0, 1, 1, 2, 3]
   (exit 0)
   ```
   ฝั่ง Server:
   ```text
   [WARN] [1793242450.323478451] [navigate_action_server]: Received request to cancel goal execution!
   [WARN] [1793242450.324825201] [navigate_action_server]: Goal canceled by client request.
   ```
3. รันโหมด Preemption: ส่ง Goal `order=10` แล้วหลัง 1.5 วินาทีส่ง Goal ใหม่ `order=4` ทับ:
   ```bash
   ./docker/run_lab.sh ros2 run amr_week04 navigate_action_client preempt --order 10
   ```
   **ผลลัพธ์จริง** (Goal แรก `ABORTED`, Goal ใหม่ `SUCCEEDED`; ตัดบรรทัด Feedback ออกเพื่อความสั้น):
   ```text
   [INFO] [1793242450.929344479] [navigate_action_client]: ⏳ Waiting for navigate_distance action server...
   [INFO] [1793242451.429942504] [navigate_action_client]: 🚀 Sending goal with order=10...
   [INFO] [1793242451.431535508] [navigate_action_client]: ✅ Goal accepted (id=f5c871be...) Executing...
   [WARN] [1793242452.932233308] [navigate_action_client]: 🔀 Sending a NEW goal (order=4) to preempt the running one...
   [INFO] [1793242452.932459004] [navigate_action_client]: 🚀 Sending goal with order=4...
   [INFO] [1793242452.933897809] [navigate_action_client]: ✅ Goal accepted (id=7bf81765...) Executing...
   [INFO] [1793242454.439636033] [navigate_action_client]: 🎯 Second goal finished: status=SUCCEEDED, sequence=[0, 1, 1, 2, 3]
   [INFO] [1793242454.439961172] [navigate_action_client]: 🏁 Goal finished: status=ABORTED, sequence=[0, 1, 1, 2, 3]
   (exit 0)
   ```
   **คำถาม Checkpoint 4.3:**
   - [ ] ผลลัพธ์ (Result) ที่ส่งกลับมาในกรณีที่ถูก Canceled มีความแตกต่างจาก SUCCEEDED อย่างไร?
   - [ ] เหตุใด Action Server ต้องคอยตรวจสอบ `goal_handle.is_cancel_requested` ในลูปเสมอ?
   - [ ] ถ้าเปลี่ยน `main()` ของ Server กลับไปใช้ `rclpy.spin(node)` (เธรดเดียว) Cancel ในข้อ 1 จะได้ผลอย่างไร และเพราะอะไร?
   - [ ] ทำไม Goal ที่ถูก Preempt จึงจบเป็น `ABORTED` ไม่ใช่ `CANCELED`?

---

### 🔹 Lab 4.4: การทดสอบนโยบายปฏิเสธ Goal ผิดพลาด (Goal Rejection)
**เป้าหมาย:** ตรวจสอบระบบป้องกันความปลอดภัยของหุ่นยนต์เมื่อได้รับเป้าหมายที่ไม่ถูกต้อง

1. ลองส่ง Goal ที่มีค่าระยะทางติดลบ (`order: -5`):
   ```bash
   ./docker/run_lab.sh ros2 action send_goal /navigate_distance example_interfaces/action/Fibonacci "{order: -5}"
   ```
2. สังเกตผลลัพธ์:
   - CLI จะรายงาน: `Goal was rejected.` (ผลจริง)
   - Server จะพิมพ์ Log: `[ERROR] [navigate_action_server]: Rejecting negative distance step goal.`

---

## 🏆 โจทย์ท้าทายระดับสูง (Challenge Exercises)
1. **Challenge 4.1:** สร้าง Action Interface สำหรับการทำความสะอาดพื้นของ AMR: `CleanArea.action` ที่มี:
   - Goal: `float32 area_square_meters`
   - Result: `float32 actual_cleaned_area`, `float32 battery_used`
   - Feedback: `float32 percent_completed`, `float32 current_power_draw`
2. **Challenge 4.2:** เขียนโหนด Action Server ที่สามารถรองรับ Goal ได้พร้อมกัน 2 งานโดยใช้ Queue หรือตอบ Reject หากมีงานเดิมกำลังทำงานอยู่

---

## 📦 สิ่งที่ต้องส่ง (Deliverables Checklist)
- [ ] ภาพบันทึกหน้าจอผลการทดสอบ `ros2 action send_goal -f` แสดง Feedback ครบทุกสเต็ป
- [ ] ภาพบันทึกหน้าจอการรัน `navigate_action_client.py` ในสภาวะปกติ (Succeeded)
- [ ] ภาพบันทึกหน้าจอการทดสอบยกเลิกภารกิจด้วยแฟล็ก `--cancel` ทั้งฝั่ง Client และ Server
- [ ] ภาพบันทึกหน้าจอการถูกปฏิเสธ Goal เมื่อส่งค่าติดลบใน Lab 4.4
- [ ] คำตอบ Checkpoint 4.3

---

## 📊 เกณฑ์การประเมินผล (Lab Grading Rubric - 100 คะแนน)
| รายการประเมิน | รายละเอียดการให้คะแนน | คะแนนเต็ม |
| :--- | :--- | :---: |
| **การทดสอบ Action CLI & Feedback** | รันส่ง Goal และแสดงผล Feedback ผ่าน CLI ถูกต้อง | 20 |
| **การใช้งาน Python Action Client** | รันไคลเอนต์และแสดงค่า Result ครบถ้วน | 20 |
| **การทดสอบ Goal Cancellation** | พิสูจน์การสั่ง Cancel และ Server ตอบสนองได้สมบูรณ์ | 25 |
| **การปฏิเสธ Goal ที่ไม่ถูกต้อง** | อธิบายและทดสอบตรรกะใน `goal_callback` ได้ถูกต้อง | 20 |
| **ความเรียบร้อยของรายงานและโจทย์ท้าทาย** | รายงานสมบูรณ์ ภาพประกอบและบทวิเคราะห์ชัดเจน | 15 |
| **รวม** | | **100** |

---

## ⚠️ การแก้ปัญหาที่พบบ่อยในแล็บ (Troubleshooting)
| ปัญหา | สาเหตุ | การแก้ไข |
| :--- | :--- | :--- |
| `AttributeError: 'GoalHandle' object has no attribute 'is_cancel_requested'` | พิมพ์ชื่อแอตทริบิวต์ผิด | ใน rclpy ให้ใช้ `goal_handle.is_cancel_requested` |
| Client ไม่ได้รับ Feedback | ไม่ได้ส่ง `feedback_callback` เข้าไปในเมธอด `send_goal_async` | ตรวจสอบอาร์กิวเมนต์: `send_goal_async(goal_msg, feedback_callback=...)` |
| Server ค้างไม่คืนสิทธิ์ให้ Client อื่น | ติดลูป Infinite Loop ใน `execute_callback` | ตรวจสอบเงื่อนไขการหลุดลูปและการเรียก `succeed()` |
| Cancel ไม่มีผล Goal จบเป็น `SUCCEEDED` | Server หมุนด้วย `rclpy.spin()` เธรดเดียว ขณะ `execute_callback` ใช้ `time.sleep()` | ใช้ `MultiThreadedExecutor` + `ReentrantCallbackGroup` แบบใน `navigate_action_server.py` |


## 📟 ผลการรันจริง (Real Run Output)
บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29 — ไฟล์เต็ม: [`results/action_lab_run.txt`](results/action_lab_run.txt)

```console
$ ros2 run amr_week04 navigate_action_server     # terminal 1

$ ros2 action list -t
/navigate_distance [example_interfaces/action/Fibonacci]

$ ros2 action info /navigate_distance
Action: /navigate_distance
Action clients: 0
Action servers: 1
    /navigate_action_server

$ ros2 action send_goal /navigate_distance example_interfaces/action/Fibonacci "{order: -5}"
Waiting for an action server to become available...
Sending goal:
     order: -5
```

---

