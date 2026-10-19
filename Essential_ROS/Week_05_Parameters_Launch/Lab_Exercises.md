# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 5: พารามิเตอร์แบบพลวัตและ Launch System

---

## 💻 ขั้นตอนการทดลอง

### ขั้นตอนที่ 1: รันระบบรวมผ่าน Launch File
```bash
./docker/run_lab.sh ros2 launch Essential_ROS/Week_05_Parameters_Launch/launch/core_system.launch.py fleet_id:=AMR_PRO_01
```

### ขั้นตอนที่ 2: ตรวจสอบและเปลี่ยนค่าพารามิเตอร์ขณะทำงาน
```bash
# ตรวจสอบรายการพารามิเตอร์
./docker/run_lab.sh ros2 param list

# เปลี่ยนค่าความเร็วเป็น 1.2 m/s (ผ่านการตรวจสอบ)
./docker/run_lab.sh ros2 param set /fleet_parameters max_linear_speed 1.2

# เปลี่ยนค่าความเร็วเป็น 4.0 m/s (ไม่ผ่านการตรวจสอบความปลอดภัย -> Reject)
./docker/run_lab.sh ros2 param set /fleet_parameters max_linear_speed 4.0
```
