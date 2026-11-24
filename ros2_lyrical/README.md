# ROS 2 Lyrical Luth: Network Stack

เอกสารวิจัยเรื่อง network stack ของ ROS 2 Lyrical Luth (พฤษภาคม 2026, LTS ถึง 2031) ไล่ตั้งแต่ `publish()` ใน user space ผ่าน rmw และ DDS ลงไปถึง Linux kernel ไปจนถึงการส่งข้ามเครื่อง มีทั้งการวิเคราะห์จาก source code และผลการทดลองจริงที่ capture packet ไว้

![OSI 7 layer เทียบกับ ROS 2 Lyrical](diagrams/anim-osi-vs-ros2-lyrical.svg)

## เอกสาร

| ภาค | เนื้อหา |
|---|---|
| [ภาค 1: Network Stack Deep Dive](ros2_lyrical_network_stack_deep_dive.md) | ภาพรวม stack, เทียบกับ OSI, RMW ทั้ง 4 ตัว, discovery, transport, packet anatomy และเส้นทางใน kernel ขา TX/RX |
| [ภาค 2: Wire format, reliability, kernel accounting](ros2_lyrical_network_stack_deeper.md) | RTPS ระดับ byte, DATA_FRAG/NACK_FRAG, Zenoh framing, การคิด `truesize` ของ SO_RCVBUF และ latency budget |
| [ภาค 3: ผลการทดลองจริง (packet capture)](ros2_lyrical_wire_experiments.md) | การทดลอง 6 ชุดใน Docker พร้อม pcap เทียบคำทำนายกับสิ่งที่เกิดบนสายจริง |

## Interactive 3D lab

[**Lyrical Packet Lab**](https://alfaxphoori.github.io/ros2/ros2_lyrical/interactive/lyrical-packet-lab.html) (ต้องใช้เบราว์เซอร์ที่รองรับ WebGL) จำลอง 4 hosts ที่ต่อผ่าน switch มีทั้งหมด 20 บท

- บทที่ 1–16 ครอบคลุม topic, service, action, serialize, syscall, kernel TX/RX, packet bytes, kernel call path, SHM, `rosidl::Buffer`, discovery, Zenoh และ observability
- บทที่ 17–20 เล่นผลการทดลองจริงซ้ำ ([#lesson-17](https://alfaxphoori.github.io/ros2/ros2_lyrical/interactive/lyrical-packet-lab.html#lesson-17))

ไฟล์ `interactive/lyrical-packet-lab.src.html` เป็นต้นฉบับ ส่วน `lyrical-packet-lab.html` คือไฟล์ที่ build แล้วสำหรับ GitHub Pages

## โครงสร้างโฟลเดอร์

```
ros2_lyrical/
├── ros2_lyrical_network_stack_deep_dive.md   ภาค 1
├── ros2_lyrical_network_stack_deeper.md      ภาค 2
├── ros2_lyrical_wire_experiments.md          ภาค 3
├── diagrams/        animated SVG 8 ภาพ (stack, OSI, packet, kernel path, capture จริง, rcvbuf)
├── interactive/     Lyrical Packet Lab (3D, Three.js)
├── captures/        pcap จากการทดลอง (กรอง hostname ของเครื่องออกแล้ว)
│   └── scripts/     Dockerfile และ run_experiments.sh สำหรับทำซ้ำ
└── tools/           สคริปต์ Python ที่สร้าง SVG 7 จาก 8 ภาพใน diagrams/ (anim-lyrical-packet-path.svg เขียนด้วยมือ)
```

## ทำซ้ำ

```bash
# รันการทดลองทั้ง 6 ชุด (ต้องมี Docker) ผลจะอยู่ใน captures/scripts/out/
cd ros2_lyrical/captures/scripts && ./run_experiments.sh

# สร้าง SVG ใหม่
python3 ros2_lyrical/tools/gen_stack_osi_svgs.py      ros2_lyrical/diagrams
python3 ros2_lyrical/tools/gen_packet_kernel_svgs.py  ros2_lyrical/diagrams
python3 ros2_lyrical/tools/gen_capture_svgs.py        ros2_lyrical/diagrams
```

> `run_experiments.sh` ไม่ได้กรอง traffic อื่นออกจาก pcap ถ้าจะเผยแพร่ไฟล์ที่ capture เอง ให้กรองตามวิธีในภาค 3 ก่อน เพราะ mDNS ของเครื่อง host อาจติดชื่อเครื่องมาด้วย
