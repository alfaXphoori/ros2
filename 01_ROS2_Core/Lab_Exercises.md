# 🛠️ ใบงานปฏิบัติการโมดูล 1: ROS 2 Core Communication Laboratory

---

## 📋 สารบัญการทดลอง
- [Lab 1.1: Custom QoS Pub/Sub สตรีมข้อมูลเซนเซอร์](#lab-11-custom-qos-pubsub-สตรีมข้อมูลเซนเซอร์)
- [Lab 1.2: Service & Client ระบบจัดการพลังงานหุ่นยนต์](#lab-12-service--client-ระบบจัดการพลังงานหุ่นยนต์)
- [Lab 1.3: Action Server & Client ภารกิจเคลื่อนที่สู่เป้าหมาย](#lab-13-action-server--client-ภารกิจเคลื่อนที่สู่เป้าหมาย)
- [Lab 1.4: Dynamic Parameter Callback & YAML Configuration](#lab-14-dynamic-parameter-callback--yaml-configuration)
- [Lab 1.5: Modular Python Launch System](#lab-15-modular-python-launch-system)

---

## Lab 1.1: Custom QoS Pub/Sub สตรีมข้อมูลเซนเซอร์

### 🎯 วัตถุประสงค์
1. สร้างโหนด Publisher และ Subscriber ด้วย `rclpy`
2. กำหนดนโยบาย Quality of Service (QoS) แบบ `BEST_EFFORT` สำหรับเซนเซอร์อัตราเร็วสูง และ `RELIABLE` กับ `TRANSIENT_LOCAL` สำหรับข้อมูลสถานะหุ่นยนต์

### 💻 โค้ดตัวอย่าง: `sensor_qos_publisher.py`
```python
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from std_msgs.msg import String, Float32

class SensorQoSPublisher(Node):
    def __init__(self):
        super().__init__('sensor_qos_publisher')
        
        # QoS สำหรับเซนเซอร์ความเร็วสูง (อนุญาตให้ตกหล่นได้ เน้นข้อมูลใหม่ล่าสุด)
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )
        
        # QoS สำหรับข้อมูลสถานะสำคัญ (ห้ามตกหล่น และเก็บค่าล่าสุดให้ผู้ที่เพิ่ง subscribe)
        state_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        self.pub_sensor = self.create_publisher(Float32, '/sensor/temperature', sensor_qos)
        self.pub_state = self.create_publisher(String, '/robot/state', state_qos)
        
        self.timer = self.create_timer(1.0, self.timer_callback)
        self.get_logger().info('✅ Sensor QoS Publisher Started')

    def timer_callback(self):
        msg = Float32()
        msg.data = 38.5
        self.pub_sensor.publish(msg)
```

### 📝 คำสั่งทดสอบ
```bash
python3 src/publisher_subscriber/sensor_qos_publisher.py
ros2 topic info /sensor/temperature --verbose
```

---

## Lab 1.2: Service & Client ระบบจัดการพลังงานหุ่นยนต์

### 🎯 วัตถุประสงค์
สร้าง Service Server สำหรับรับคำสั่งตรวจสอบระดับแบตเตอรี่ และสั่งเปิด/ปิดโหมดประหยัดพลังงาน (Power Saving Mode)

### 💻 คำสั่งทดสอบ Service ผ่าน CLI
```bash
# ตรวจสอบรายการ Service ที่กำลังทำงาน
ros2 service list

# ทดสอบเรียกใช้ Service เพื่อสลับโหมดพลังงาน
ros2 service call /robot/set_power_mode std_srvs/srv/SetBool "{data: true}"
```

---

## Lab 1.3: Action Server & Client ภารกิจเคลื่อนที่สู่เป้าหมาย

### 🎯 วัตถุประสงค์
สร้าง Action Server เพื่อรับเป้าหมายระยะทาง ส่งค่า Feedback ความคืบหน้าแบบ Real-time และสามารถยกเลิก (Cancel Goal) ได้กลางคัน

### 💻 คำสั่งทดสอบ Action ผ่าน CLI
```bash
# ส่ง Goal ไปยัง Action Server พร้อมรับ Feedback
ros2 action send_goal /navigate_distance example_interfaces/action/Fibonacci "{order: 5}" --feedback
```

---

## Lab 1.4: Dynamic Parameter Callback & YAML Configuration

### 🎯 วัตถุประสงค์
1. ประกาศพารามิเตอร์ของหุ่นยนต์ (Max Speed, Safety Margin, Fleet ID)
2. ผูก `add_on_set_parameters_callback` เพื่อตรวจจับและ Validate ค่าทันทีที่มีการเปลี่ยนแปลงโดยไม่ต้อง Restart โหนด

### 💻 คำสั่งทดสอบ Parameter
```bash
# ดูรายการพารามิเตอร์
ros2 param list

# เปลี่ยนแปลงค่าความเร็วสูงสุดแบบเรียลไทม์
ros2 param set /robot_controller max_linear_speed 1.5
```

---

## Lab 1.5: Modular Python Launch System

### 🎯 วัตถุประสงค์
สร้าง Launch file ที่ประกอบโหนดหลายตัวเข้าด้วยกัน พร้อมกำหนด Parameter จากไฟล์ YAML และ Namespace สำหรับควบคุมหุ่นยนต์หลายตัว (Multi-robot Fleet)
