# 🛠️ ใบงานปฏิบัติการโมดูล 5: Nav2 Stack Hands-on Laboratory

---

## 📋 สารบัญการทดลอง
- [Lab 5.1: การรัน Nav2 Bringup Stack](#lab-51-การรัน-nav2-bringup-stack)
- [Lab 5.2: การกำหนดพิกัดเริ่มต้นหุ่นยนต์](#lab-52-การกำหนดพิกัดเริ่มต้นหุ่นยนต์)
- [Lab 5.3: การสั่งนำทางสู่เป้าหมายด้วย 2D Goal Pose](#lab-53-การสั่งนำทางสู่เป้าหมายด้วย-2d-goal-pose)
- [Lab 5.4: ภารกิจลาดตระเวนจุดตรวจคลังสินค้าอัตโนมัติ](#lab-54-ภารกิจลาดตระเวนจุดตรวจคลังสินค้าอัตโนมัติ)

---

## Lab 5.1: การรัน Nav2 Bringup Stack

```bash
ros2 launch launch/nav2_bringup.launch.py autostart:=true
```
ตรวจสอบว่าโหนด Lifecycle ทุกตัวเปลี่ยนสถานะเป็น **Active** และท็อปปิก `/map`, `/global_costmap/costmap`, `/local_costmap/costmap` เริ่มเผยแพร่ข้อมูล

---

## Lab 5.2: การกำหนดพิกัดเริ่มต้นหุ่นยนต์

สามารถทำได้ 2 รูปแบบ:
1. **ผ่าน RViz2 GUI:** คลิกปุ่ม `2D Pose Estimate` ลากลูกศรบนจุดเริ่มต้น
2. **ผ่านสคริปต์อัตโนมัติ:**
   ```bash
   python3 src/amcl_initial_pose.py --ros-args -p x:=0.0 -p y:=0.0 -p theta:=0.0
   ```

---

## Lab 5.3: การสั่งนำทางสู่เป้าหมายด้วย 2D Goal Pose

1. เปิด RViz2 ตรวจสอบ Costmap รอบกำแพงและสิ่งกีดขวาง
2. คลิกปุ่ม `Nav2 Goal` ลากลูกศรชี้ไปยังช่องทางเดินระหว่างชั้นวางสินค้า
3. สังเกตเส้นทาง Global Path สีน้ำเงิน/เขียว และการที่หุ่นยนต์เร่งความเร็วพร้อมหลบสิ่งกีดขวางได้อย่างนุ่มนวล

---

## Lab 5.4: ภารกิจลาดตระเวนจุดตรวจคลังสินค้าอัตโนมัติ

รันภารกิจลาดตระเวนอัตโนมัติทั้ง 5 สถานี:
```bash
python3 src/waypoint_patrol.py
```
**ตัวอย่างผลลัพธ์บนคอนโซล:**
```text
📍 [1/5] Navigating to: Station 1: Receiving Dock
   Target: X=2.00, Y=2.00, Yaw=0.00
✅ Arrived at Station 1: Receiving Dock! Dwelling for 3.0s...
📍 [2/5] Navigating to: Station 2: Storage Aisle B
   Target: X=2.00, Y=-2.00, Yaw=-1.57
✅ Arrived at Station 2: Storage Aisle B! Dwelling for 3.0s...
...
🎉 All patrol stations visited successfully!
```
