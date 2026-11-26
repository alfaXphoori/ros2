# ROS 2 Lyrical Luth: Network Stack

เอกสารวิจัยเรื่อง network stack ของ ROS 2 Lyrical Luth (พฤษภาคม 2026, LTS ถึง 2031) ไล่ตั้งแต่ `publish()` ใน user space ผ่าน rmw และ DDS ลงไปถึง Linux kernel ไปจนถึงการส่งข้ามเครื่อง มีทั้งการวิเคราะห์จาก source code และผลการทดลองจริงที่ capture packet ไว้

![OSI 7 layer เทียบกับ ROS 2 Lyrical](diagrams/anim-osi-vs-ros2-lyrical.svg)

## เอกสาร

อ่านตามลำดับได้ แต่ละภาคอ้างอิงกันด้วยหมายเลขภาค

| ภาค | ไฟล์ | เนื้อหา |
|---|---|---|
| 1 | [docs/01_network_stack_deep_dive.md](docs/01_network_stack_deep_dive.md) | ภาพรวม stack, เทียบกับ OSI, RMW ทั้ง 4 ตัว, discovery, transport, packet anatomy และเส้นทางใน kernel ขา TX/RX |
| 2 | [docs/02_wire_format_and_kernel.md](docs/02_wire_format_and_kernel.md) | RTPS ระดับ byte, DATA_FRAG/NACK_FRAG, Zenoh framing, การคิด `truesize` ของ SO_RCVBUF, latency budget และหัวข้อวิจัย R1–R9 |
| 3 | [docs/03_wire_experiments.md](docs/03_wire_experiments.md) | การทดลอง 6 ชุดใน Docker พร้อม pcap เทียบคำทำนายกับสิ่งที่เกิดบนสายจริง |
| 4 | [docs/04_architectures.md](docs/04_architectures.md) | rmw plugin และ internals ของ middleware 4 ตัว, discovery 3 แบบ, topic/service/action บน DDS และ Zenoh, data path ในเครื่องเดียวกัน 6 ทาง, deployment (LAN, fleet, cloud, micro-ROS), security และตารางเลือกสถาปัตยกรรม |

## หน้า interactive (GitHub Pages)

| หน้า | เนื้อหา |
|---|---|
| [**Data Paths**](https://alfaxphoori.github.io/ros2/ros2_lyrical/interactive/data-paths.html) | เทียบเส้นทางการส่ง 10 แบบ (intra-process, UDP loopback, Fast DDS SHM, Zenoh SHM, loaned message, `rosidl::Buffer`, DDS UDP, ภาพ RELIABLE, ภาพ BEST_EFFORT, Zenoh TCP) แบบภาพเคลื่อนไหว พร้อมจุดที่ CPU copy payload และ packet จริงจาก capture แยกสีตามชั้น |
| [**Lyrical Packet Lab**](https://alfaxphoori.github.io/ros2/ros2_lyrical/interactive/lyrical-packet-lab.html) | ฉาก 3D (ต้องใช้ WebGL) จำลอง 4 hosts ต่อผ่าน switch มี 20 บท บทที่ 1–16 ครอบคลุม topic, service, action, serialize, syscall, kernel TX/RX, packet bytes, SHM, `rosidl::Buffer`, discovery, Zenoh และ observability บทที่ 17–20 เล่นผลการทดลองจริงซ้ำ ([#lesson-17](https://alfaxphoori.github.io/ros2/ros2_lyrical/interactive/lyrical-packet-lab.html#lesson-17)) |

`interactive/lyrical-packet-lab.src.html` เป็นต้นฉบับของ Packet Lab ส่วน `lyrical-packet-lab.html` คือไฟล์เดียวกันที่ห่อด้วย `<html>`/`<head>`/`<body>` สำหรับ GitHub Pages แก้ไฟล์หนึ่งแล้วต้องแก้อีกไฟล์ให้ตรงกัน

## โครงสร้างโฟลเดอร์

```
ros2_lyrical/
├── README.md        หน้านี้
├── docs/            เอกสารภาค 1–4
├── diagrams/        animated SVG 14 ภาพที่เอกสารฝังไว้
├── interactive/     data-paths.html, Lyrical Packet Lab (3D, Three.js)
├── captures/        pcap จากการทดลอง (กรอง hostname ของเครื่องออกแล้ว)
│   └── scripts/     Dockerfile, run_experiments.sh และไฟล์ประกอบสำหรับทำซ้ำ
└── tools/           rtps_peek.py (ถอด packet) และสคริปต์สร้าง SVG
```

## ทำซ้ำและตรวจผล

```bash
# รันการทดลองทั้ง 6 ชุด (ต้องมี Docker) ผลจะอยู่ใน ros2_lyrical/captures/scripts/out/
ros2_lyrical/captures/scripts/run_experiments.sh

# ถอด packet จาก pcap โดยไม่ต้องมี tshark (ใช้แค่ Python standard library)
python3 ros2_lyrical/tools/rtps_peek.py frame ros2_lyrical/captures/exp1_fastdds_default.pcap 95
python3 ros2_lyrical/tools/rtps_peek.py sms   ros2_lyrical/captures/exp2_image_reliable.pcap.gz NACK_FRAG

# สร้าง SVG ใหม่ (13 จาก 14 ภาพ; anim-lyrical-packet-path.svg เขียนด้วยมือ)
python3 ros2_lyrical/tools/gen_stack_osi_svgs.py      ros2_lyrical/diagrams
python3 ros2_lyrical/tools/gen_packet_kernel_svgs.py  ros2_lyrical/diagrams
python3 ros2_lyrical/tools/gen_capture_svgs.py        ros2_lyrical/diagrams
python3 ros2_lyrical/tools/gen_architecture_svgs.py   ros2_lyrical/diagrams
```

> `run_experiments.sh` ไม่ได้กรอง traffic อื่นออกจาก pcap ถ้าจะเผยแพร่ไฟล์ที่ capture เอง ให้กรองตามวิธีใน[ภาค 3 §8](docs/03_wire_experiments.md#8-วิธีทำซ้ำ) ก่อน เพราะ mDNS ของเครื่อง host อาจติดชื่อเครื่องมาด้วย
