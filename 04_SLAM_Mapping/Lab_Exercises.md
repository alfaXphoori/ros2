# 🛠️ ใบงานปฏิบัติการโมดูล 4: 2D SLAM Mapping Hands-on Laboratory

---

## 📋 สารบัญการทดลอง
- [Lab 4.1: การรันโหนด SLAM Toolbox](#lab-41-การรันโหนด-slam-toolbox)
- [Lab 4.2: การตรวจสอบแผนที่บน RViz2](#lab-42-การตรวจสอบแผนที่บน-rviz2)
- [Lab 4.3: การสำรวจพื้นที่และ Loop Closure](#lab-43-การสำรวจพื้นที่และ-loop-closure)
- [Lab 4.4: การบันทึกแผนที่](#lab-44-การบันทึกแผนที่)

---

## Lab 4.1: การรันโหนด SLAM Toolbox

ตรวจสอบว่าโลกจำลอง Gazebo ในโมดูล 3 กำลังทำงานอยู่และเผยแพร่ท็อปปิก `/scan` กับ `/tf` จากนั้นเปิด Terminal ใหม่แล้วรัน:

```bash
ros2 launch launch/online_async_slam.launch.py
```
> **ข้อสังเกต:** โหนดจะสร้างท็อปปิก `/map` และ `/map_metadata`

---

## Lab 4.2: การตรวจสอบแผนที่บน RViz2

เปิด RViz2 แล้วเพิ่มการแสดงผล:
1. **Displays Panel** $\rightarrow$ คลิก **Add**
2. เลือก **Map** $\rightarrow$ ตั้ง Topic เป็น `/map`
3. เลือก **LaserScan** $\rightarrow$ ตั้ง Topic เป็น `/scan`

---

## Lab 4.3: การสำรวจพื้นที่และ Loop Closure

- ขับหุ่นยนต์ด้วย `teleop_twist_keyboard` รอบคลังสินค้า
- วนกลับมายังจุดเริ่มต้น สังเกตว่าเส้นขอบกำแพงที่เคยเอียงเล็กน้อยจะถูก Ceres Solver ดึงปรับให้ตรงและเชื่อมสนิทกัน (Loop Closure)

---

## Lab 4.4: การบันทึกแผนที่

เมื่อสำรวจครบถ้วนแล้ว ให้สั่งบันทึกแผนที่ด้วย Map Saver CLI:
```bash
ros2 run nav2_map_server map_saver_cli -f maps/my_warehouse_map
```
ตรวจสอบว่าได้ไฟล์ `my_warehouse_map.pgm` และ `my_warehouse_map.yaml` ถูกสร้างขึ้นเรียบร้อยแล้ว
