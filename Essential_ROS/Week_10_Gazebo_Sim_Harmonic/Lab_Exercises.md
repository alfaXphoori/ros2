# 🛠️ ใบงานปฏิบัติการสัปดาห์ที่ 10: สร้างและตรวจสอบโลกจำลอง Gazebo

---

## 💻 ขั้นตอนการทดลอง

### ขั้นตอนที่ 1: ตรวจสอบความถูกต้องของโครงสร้าง SDF World
```bash
./docker/run_lab.sh gz sdf -k Essential_ROS/Week_10_Gazebo_Sim_Harmonic/worlds/warehouse.sdf
```
*ผลลัพธ์ที่คาดหวัง:* `Validating Essential_ROS/Week_10_Gazebo_Sim_Harmonic/worlds/warehouse.sdf. Success!`

### ขั้นตอนที่ 2: รัน Gazebo Sim เปิดโลกคลังสินค้า 3D
```bash
./docker/run_lab.sh gz sim Essential_ROS/Week_10_Gazebo_Sim_Harmonic/worlds/warehouse.sdf
```
