# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 13: สถาปัตยกรรม Nav2 Stack และระบบ Costmap 2D
**วิชา:** AMR-101 Essential ROS 2 for Autonomous Mobile Robots  
**เวลาปฏิบัติการ:** 3 ชั่วโมง  
**ระดับ:** พื้นฐาน (Beginner)  
**เอกสารประกอบการบรรยาย:** [คู่มือบรรยายสัปดาห์ที่ 13](Readme.md)

---

## 🎯 วัตถุประสงค์การทดลอง (Lab Objectives)
1. แสดงผลและตรวจสอบ **Global Costmap** และ **Local Costmap** ในโปรแกรม RViz2
2. วิเคราะห์ค่าความเข้มของสีตามรหัสอันตราย (Cost Values: Free=0, Inscribed=253, Lethal=254)
3. สังเกตและทดสอบพฤติกรรม **Marking** (เพิ่มสิ่งกีดขวางสด) และ **Clearing / Raytracing** (ลบสิ่งกีดขวางที่หายไป)
4. ปรับจูนพารามิเตอร์ **`cost_scaling_factor`** และกำหนดรูปทรง **`footprint`** เพื่อให้หุ่นยนต์วิ่งผ่านทางแคบได้

---

## 📋 ข้อกำหนดก่อนเริ่มปฏิบัติการ (Prerequisites & Setup)
- เข้าสู่รูทไดเรกทอรี `/mnt/sda/ros`
- ตรวจสอบไฟล์คอนฟิก Costmap:
  ```bash
  cat Essential_ROS/Week_13_Nav2_Costmaps_Layers/config/costmap_params.yaml
  ```

---

## 🧪 ขั้นตอนการทดลอง (Step-by-Step Lab Tasks)

### 🔹 Lab 13.1: การเปิดแสดงผล Costmap ใน RViz2
**เป้าหมาย:** สังเกตความแตกต่างระหว่างเลเยอร์แผนที่คงที่และแผนที่รอบตัวหุ่นยนต์

1. เปิดระบบจำลองโกดังสินค้าใน **Terminal 1**:
   ```bash
   ./docker/run_lab.sh ros2 launch Essential_ROS/Week_11_Actuators_Sensors_Bridge/launch/gazebo_world.launch.py
   ```

2. ใน **Terminal 2** เปิดระบบแสดงผล URDF (เพื่อให้มี TF ของหุ่นยนต์ครบถ้วน):
   ```bash
   ./docker/run_lab.sh ros2 launch Essential_ROS/Week_07_URDF_Robot_Modeling/launch/display_urdf.launch.py use_gui:=false
   ```

3. ในหน้าต่าง RViz2:
   - เพิ่ม Display ชนิด `Map` โดยเลือก Topic เป็น `/global_costmap/costmap`
   - กำหนด Color Scheme เป็น `costmap` (สังเกตแถบสี: น้ำเงิน=ปลอดภัย, ม่วง/แดง=อันตราย)
   - เพิ่ม Display อีกตัวชนิด `Map` โดยเลือก Topic เป็น `/local_costmap/costmap`
   - สังเกตกรอบสี่เหลี่ยม $3 \times 3$ เมตร ที่เคลื่อนที่ตามจุดศูนย์กลางของหุ่นยนต์ตลอดเวลา

---

### 🔹 Lab 13.2: การตรวจสอบค่าตัวเลขคอสต์และการกระจายตัว (Cost Values & Gradient)
**เป้าหมาย:** สุ่มตรวจสอบค่า Cost ในข้อมูลดิบของข้อความ OccupancyGrid

1. ดักฟังข้อมูลดิบของ Local Costmap:
   ```bash
   ./docker/run_lab.sh ros2 topic echo --once /local_costmap/costmap --field data
   ```
2. สังเกตตัวเลขในอาเรย์:
   - ค่า `0`: ทางเดินโล่งที่ไม่มีความเสี่ยง
   - ค่า `254`: ขอบกำแพงหรือสิ่งกีดขวางที่ LiDAR สแกนเจอ
   - ค่า `253`: รัศมีตัวถังหุ่นยนต์รอบสิ่งกีดขวาง (Inscribed Radius)
   - ค่าระหว่าง `1 - 252`: ค่าความเสี่ยงที่ค่อยๆ ลดหลั่นลงมาตามระยะห่าง

   **คำถาม Checkpoint 13.2:**
   - [ ] รัศมี Inscribed Radius ของหุ่นยนต์ตัวนี้มีค่ากี่เมตรเมื่อคำนวณจาก Footprint กว้าง 0.28m และยาว 0.40m?
   - [ ] (แนวคิด: ครึ่งหนึ่งของความกว้าง $= 0.14$ m คือระยะที่สั้นที่สุดจากจุดศูนย์กลางถึงขอบตัวถัง)

---

### 🔹 Lab 13.3: การทดสอบกลไก Marking และ Clearing แบบเรียลไทม์
**เป้าหมาย:** พิสูจน์ว่าเมื่อมีวัตถุตัดหน้า Costmap จะมาร์กจุดสีแดง และเมื่อวัตถุหายไป ระบบจะล้างค่ากลับเป็นสีน้ำเงิน

1. ขับหุ่นยนต์ไปหยุดอยู่หน้ากล่องสินค้าหรือสิ่งกีดขวาง
2. สังเกตใน RViz2 ว่ามีจุดสีม่วง/แดง (Obstacle Cost) ปรากฏขึ้นตรงตำแหน่งที่ LiDAR ยิงไปโดน
3. ทดลองถอยหลังหุ่นยนต์ออกมา หรือเลี้ยวหันหัวไปทางอื่น
4. สังเกตแนวเส้น Raytrace: บริเวณที่แสงเลเซอร์ส่องทะลุผ่านจะถูกล้างค่ากลับเป็น $0$ (Free Space) ทันที

---

### 🔹 Lab 13.4: การปรับจูน `cost_scaling_factor` สำหรับทางแคบ (Hands-on Tuning)
**เป้าหมาย:** แก้ปัญหาหุ่นยนต์ไม่ยอมเดินผ่านช่องทางเดินแคบ (Doorway / Narrow Corridor)

1. ตรวจสอบค่าพารามิเตอร์ปัจจุบัน:
   ```bash
   ./docker/run_lab.sh ros2 param get /local_costmap/local_costmap inflation_layer.cost_scaling_factor
   ```
   *ค่าเริ่มต้นคือ 3.0*

2. ทดลองปรับค่า `cost_scaling_factor` เป็น $7.0$ แบบเรียลไทม์:
   ```bash
   ./docker/run_lab.sh ros2 param set /local_costmap/local_costmap inflation_layer.cost_scaling_factor 7.0
   ```
3. สังเกตการเปลี่ยนแปลงบนหน้าจอ RViz2:
   - รัศมีความชันของสีแดงจะหดตัวแคบลงชิดขอบสิ่งกีดขวางมากขึ้น
   - พื้นที่สีน้ำเงินเข้ม (ปลอดภัย) บริเวณตรงกลางทางเดินจะกว้างขึ้น ทำให้หุ่นยนต์สามารถวางแผนเส้นทางผ่านได้

---

## 🏆 โจทย์ท้าทายระดับสูง (Challenge Exercises)
1. **Challenge 13.1:** เพิ่มเลเยอร์พิเศษ `RangeSensorLayer` เพื่อนำข้อมูลจากเซนเซอร์ Ultrasonic (Sonar) เข้ามาร่วมมาร์กสิ่งกีดขวางใน Costmap
2. **Challenge 13.2:** ปรับแต่ง Footprint ของหุ่นยนต์ในกรณีที่ต้องลากรถพ่วง (Trailer) ยาว 1.2 เมตร และสังเกตการขยายตัวของ Inscribed Cost รอบตัวถัง

---

## 📦 สิ่งที่ต้องส่ง (Deliverables Checklist)
- [ ] ภาพบันทึกหน้าจอ RViz2 แสดง Global Costmap และ Local Costmap พร้อม Color Scheme แบบ `costmap`
- [ ] ภาพบันทึกหน้าจอการเปลี่ยนแปลงของ Inflation Decay เมื่อปรับค่า `cost_scaling_factor` จาก 3.0 เป็น 7.0
- [ ] ภาพบันทึกหน้าจอแสดงผลการทดสอบ Marking และ Clearing เมื่อมีสิ่งกีดขวางเข้ามาในระยะสายตา
- [ ] คำตอบ Checkpoint 13.2

---

## 📊 เกณฑ์การประเมินผล (Lab Grading Rubric - 100 คะแนน)
| รายการประเมิน | รายละเอียดการให้คะแนน | คะแนนเต็ม |
| :--- | :--- | :--- :
| **การเปิดและตั้งค่าแสดงผล Costmap** | แสดงผล Global และ Local Costmap ใน RViz2 ได้ถูกต้อง | 25 |
| **ความเข้าใจรหัสค่าตัวเลข Cost** | วิเคราะห์และอธิบายค่า 0, 253, 254, 255 ได้ถูกต้องตามหลักการ | 20 |
| **การพิสูจน์ Marking & Clearing** | สาธิตและบันทึกภาพกระบวนการเพิ่มและล้างสิ่งกีดขวางได้ชัดเจน | 25 |
| **การปรับจูนพารามิเตอร์ Inflation** | ปรับค่า `cost_scaling_factor` ผ่าน CLI และวิเคราะห์ผลกระทบได้ถูกต้อง | 20 |
| **ความเรียบร้อยของรายงานและโจทย์ท้าทาย** | รายงานละเอียด ภาพประกอบครบถ้วน บทวิเคราะห์เชิงลึก | 10 |
| **รวม** | | **100** |

---

## ⚠️ การแก้ปัญหาที่พบบ่อยในแล็บ (Troubleshooting)
| ปัญหา | สาเหตุ | การแก้ไข |
| :--- | :--- | :--- |
| Local Costmap ไม่ยอมเลื่อนตามหุ่นยนต์ | เฟรม `global_frame` ของ Local Costmap ไม่ได้ตั้งเป็น `odom` | ตรวจสอบว่าในคอนฟิกตั้ง `global_frame: odom` และ `rolling_window: true` |
| หน้าต่าง RViz2 ขึ้น Error สีเหลือง: `No map received` | ท็อปปิก Costmap ยังไม่ถูก Publish จากระบบ Nav2 | ตรวจสอบว่าโหนด Nav2 อยู่ในสถานะ `Active` ใน Lifecycle Manager |
| หุ่นยนต์ชนมุมกำแพงตอนเลี้ยว | ตั้งค่า `footprint` เล็กกว่าขนาดตัวถังจริง | ขยายมิติตัวเลขในพิกัด Footprint ให้ครอบคลุมรัศมีการสวิงของล้อและมุมตัวถัง |
