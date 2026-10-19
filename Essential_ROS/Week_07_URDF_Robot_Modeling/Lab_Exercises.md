# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 7: ตรวจสอบและแสดงผลโมเดล URDF

---

## 💻 ขั้นตอนการทดลอง

### ขั้นตอนที่ 1: ตรวจสอบความถูกต้องของโมเดล URDF ด้วย check_urdf
```bash
./docker/run_lab.sh check_urdf Essential_ROS/Week_07_URDF_Robot_Modeling/urdf/diff_drive_robot.urdf
```
*ผลลัพธ์ที่คาดหวัง:* แสดงความสัมพันธ์ของ Links ทั้ง 7 ชิ้น โดยมี Root Link เป็น `base_footprint`

### ขั้นตอนที่ 2: เปิดแสดงผลบน RViz2
```bash
./docker/run_lab.sh ros2 launch Essential_ROS/Week_07_URDF_Robot_Modeling/launch/display_urdf.launch.py
```
*สังเกต:* ตรวจสอบการหมุนของล้อซ้ายและขวาผ่านแผง Joint State Publisher GUI
