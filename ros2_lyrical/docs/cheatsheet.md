# สรุปย่อหนึ่งหน้า (Cheat sheet)

> ตัวเลขทุกตัวคัดลอกจากเอกสารตามลิงก์ (ไม่ได้วัดใหม่ในหน้านี้) · คำศัพท์: [glossary.md](glossary.md) · แบบฝึกหัด: [exercises.md](exercises.md)

## Port ของ RTPS

PB = 7400, DG = 250, PG = 2, d0 = 0, d1 = 10, d2 = 1, d3 = 11 ([ภาค 1 §3.1](01_network_stack_deep_dive.md#31-rmw_fastrtps_cpp--fast-dds-36x-default-v-เวอร์ชัน--k-รายละเอียด-protocol))

| ใช้ทำอะไร | สูตร | domain 0, pid 0 | domain 0, pid 1 | เห็นใน capture |
|---|---|---|---|---|
| SPDP multicast (`239.255.0.1`) | PB + DG·d + d0 | 7400 | 7400 | `exp1`, `exp4` |
| metatraffic unicast (SPDP/SEDP) | PB + DG·d + d1 + PG·pid | 7410 | 7412 | `exp1` 7410; `exp4` 7410 และ 7412 |
| user multicast | PB + DG·d + d2 | 7401 | 7401 | ไม่เห็น |
| user unicast | PB + DG·d + d3 + PG·pid | 7411 | 7413 | `exp1` 7411 (frame 95) |

ใน `exp1` talker กับ listener อยู่คนละ container จึงได้ pid 0 ทั้งคู่ ส่วน `exp4` มีสอง participant ใน namespace เดียวจึงเห็น 7412 (ตรวจด้วย `tsh -r /c/<pcap> -T fields -e udp.dstport` ใน[แบบฝึกหัด 1.1](exercises.md#ภาค-1)) port 7000 ที่เห็นเพิ่มเป็น locator ของ reader `ros_discovery_info` ไม่ได้มาจากสูตร ([ภาค 3 §2](03_wire_experiments.md#2-การทดลองที่-1-หนึ่ง-sample-ของ-talker-บนสายจริง)) Discovery Server ใช้ port 11811 [K] และ Zenoh router ใช้ TCP 7447

## ตัวแปรแวดล้อม

ตรวจแล้วว่าชื่อปรากฏใน `/opt/ros/lyrical` ของ image `lyrical-wire:exp` (grep ในไฟล์ `.so`/`.py`/header เมื่อ 2026-11-27) ยกเว้นที่ติด [K]

| ตัวแปร | ใช้ทำอะไร | ดู |
|---|---|---|
| `ROS_DOMAIN_ID` | เลือก domain (port ฐาน 7400 + 250·id) ภาค 3 §10 ใช้ 100–129 แยกแต่ละรอบ | [ภาค 4 §5.1](04_architectures.md#51-หุ่นยนต์หลายเครื่องคอมพิวเตอร์บน-lan-เดียว-a-ในภาพ) |
| `RMW_IMPLEMENTATION` | `rmw_fastrtps_cpp` (default) \| `rmw_cyclonedds_cpp` \| `rmw_zenoh_cpp` \| `rmw_connextdds` | [ภาค 4 §1](04_architectures.md#1-rmw-เป็น-plugin-middleware-4-ตัวหลัง-c-abi-เดียวกัน) |
| `ROS_AUTOMATIC_DISCOVERY_RANGE` / `ROS_STATIC_PEERS` | ขอบเขต discovery (`SUBNET`/`LOCALHOST`/`OFF`/`SYSTEM_DEFAULT`) / peer แบบ unicast คั่นด้วย `;` | [ภาค 4 §2.1](04_architectures.md#2-discovery-architecture) |
| `ROS_DISCOVERY_SERVER` | ที่อยู่ Discovery Server `ip:port;…` (CLI ต้อง `ROS_SUPER_CLIENT=TRUE` [K]) | [ภาค 4 §2.2](04_architectures.md#22-fast-dds-discovery-server-k) |
| `FASTDDS_DEFAULT_PROFILES_FILE` (`FASTRTPS_DEFAULT_PROFILES_FILE` ชื่อเดิม) | XML profile ของ Fast DDS เช่น `bigbuf.xml`, `listenSocketBufferSize` | [ภาค 3 §9.1–§9.2](03_wire_experiments.md#9-การทดลองที่-7-sweep-ขนาด-receive-buffer-แก้ตัวแปรกวนของการทดลองที่-56) |
| `FASTDDS_BUILTIN_TRANSPORTS` | `DEFAULT`, `UDPv4` (ปิด SHM), `SHM`, `LARGE_DATA` | [ภาค 1 §3.1](01_network_stack_deep_dive.md#31-rmw_fastrtps_cpp--fast-dds-36x-default-v-เวอร์ชัน--k-รายละเอียด-protocol) |
| `RMW_FASTRTPS_USE_QOS_FROM_XML` | ให้ rmw ใช้ QoS จาก XML (จำเป็นสำหรับ data-sharing) | [ภาค 2 §3.5](02_wire_format_and_kernel.md#35-data-sharing-delivery) |
| `CYCLONEDDS_URI` | XML config ของ Cyclone (`SocketReceiveBufferSize`, `MaxMessageSize`) ดูภาค 3 §13 | [ภาค 1 §3.2](01_network_stack_deep_dive.md#32-rmw_cyclonedds_cpp--cyclone-dds-110x-v-เวอร์ชัน--k-รายละเอียด) |
| `ZENOH_ROUTER_CONFIG_URI` / `ZENOH_SESSION_CONFIG_URI` / `ZENOH_CONFIG_OVERRIDE` / `ZENOH_ROUTER_CHECK_ATTEMPTS` | config ของ router/session, override `key/path=value;…`, การรอ router | [ภาค 1 §3.3](01_network_stack_deep_dive.md#33-rmw_zenoh_cpp-tier-1-v-จาก-readmeconfig-branch-lyrical) |
| `ROS_SECURITY_KEYSTORE` / `_ENABLE` / `_STRATEGY` / `_ENCLAVE_OVERRIDE` | SROS2 (`Enforce` = ปฏิเสธเมื่อไม่มี credential) ดูภาค 3 §17 | [ภาค 4 §6.1](04_architectures.md#61-sros2-dds-security-k-omg-dds-security-v11--เอกสาร-sros2) |
| `TRACETOOLS_RUNTIME_DISABLE` | ปิด ros2_tracing ตอน runtime (`=1`) | [ภาค 1 §0](01_network_stack_deep_dive.md#0-ข้อเท็จจริงหลักของ-lyrical-ที่เกี่ยวกับ-network-v) |

## sysctl ที่เกี่ยวข้อง (อ่านอย่างเดียว ไม่ได้แก้ในการทดลอง)

| sysctl | ค่าที่บันทึก | ผล | ดู |
|---|---|---|---|
| `net.core.rmem_default` / `wmem_default` | 212 992 / 212 992 | `SO_RCVBUF`/`SO_SNDBUF` เมื่อไม่ตั้ง (ไม่คูณ 2) | [ภาค 3 §1](03_wire_experiments.md#1-สภาพแวดล้อมการทดลอง) |
| `net.core.rmem_max` / `wmem_max` | 4 194 304 / 4 194 304 | เพดาน `setsockopt`: ได้ 2 × min(ขอ, max) ไม่ใช่ค่าต่อ netns ใน container | [ภาค 3 §9.3](03_wire_experiments.md#93-ตรวจตัวแปร-ค่าที่-kernel-ใช้จริงและสิ่งที่ไม่เปลี่ยน-v) |
| `net.ipv4.ipfrag_time` | 30 s | fragment ที่ค้างถูกทิ้งเมื่อครบ | [ภาค 2 §2.5](02_wire_format_and_kernel.md#25-ถ้า-ip-fragment-หายหนึ่งชิ้น) |
| `net.ipv4.ipfrag_high_thresh` / `ipfrag_max_dist` | 4 MiB (≈ 32 datagram 64K ค้างพร้อมกัน, คำนวณ) / 64 | เพดานหน่วยความจำ reassembly | [ภาค 2 §2.5](02_wire_format_and_kernel.md#25-ถ้า-ip-fragment-หายหนึ่งชิ้น) |
| `net.core.netdev_budget` / `netdev_budget_usecs` / `dev_weight` | 300 / 2000 / 64 | budget ของ NET_RX softirq ต่อรอบ | [ภาค 2 §5.4](02_wire_format_and_kernel.md#54-softirq-budget-และ-ksoftirqd) |
| `net.core.busy_read` / `busy_poll` | 0 / 0 (ปิด) | busy polling ของ socket (R7, ยังไม่ได้ทดลอง) | [ภาค 2 §5.6](02_wire_format_and_kernel.md#56-busy-polling) |
| `net.core.netdev_max_backlog`, `net.ipv4.udp_mem` | ไม่ได้บันทึกค่า | อยู่ในรายการที่ต้องบันทึกของ protocol 2 เครื่อง | [ภาค 3 §12.2](03_wire_experiments.md#122-protocol-สำหรับ-2-เครื่องจริง-ยังไม่ได้รัน) |

ค่าที่แนะนำทั่วไป (`ipfrag_time=3`, `rmem_max` ใหญ่) อยู่ใน[ภาค 1 §5.3](01_network_stack_deep_dive.md#53-คอขวดคลาสสิกของ-ros-2-ในระดับ-kernel) และผลวัดของการปรับค่าดูภาค 3 §15

## คำสั่งที่ใช้บ่อย

```bash
pk()  { python3 ros2_lyrical/tools/rtps_peek.py "$@"; }                 # stdlib only, อ่าน .pcap.gz ได้
tsh() { docker run --rm --network none -v "$PWD/ros2_lyrical/captures:/c:ro" lyrical-wire:exp tshark "$@"; }
pk frame     <pcap> <n>              # hex + ถอด RTPS หนึ่ง frame
pk sms       <pcap> NACK_FRAG DATA_FRAG HEARTBEAT ACKNACK DATA   # ทุก submessage ของชนิดที่ระบุ
pk strings   <pcap> <n>              # string ใน SPDP (property list, enclave)
pk fragcount <pcap>                  # IP fragment ต่อ datagram
python3 ros2_lyrical/captures/scripts/sweep_pcap_stats.py <pcap>   # DATA_FRAG, ภาพครบ, burst ต่อภาพ (JSON)
tsh -r /c/<pcap> -Y 'rtps.sm.id == 0x12'         # NACK_FRAG (0x15 DATA, 0x16 DATA_FRAG, 0x07 HEARTBEAT, 0x06 ACKNACK)
tsh -r /c/<pcap> -Y 'rtps && frame.len==198' -O rtps
tsh -r /c/<pcap> -q -z conv,tcp                  # Zenoh: connection ไป router :7447 และ peer
tcpdump -i <if> -w out.pcap 'udp portrange 7400-7500 or tcp port 7447'   # capture (ต้องมีสิทธิ์)
ss -uamn                                         # rb/tb ของ socket และ d (drop) ต่อ socket
nstat -az | grep -E 'UdpRcvbufErrors|UdpInErrors|ReasmFails|ReasmTimeout'
grep -E '^(Udp|Ip):' /proc/net/snmp              # RcvbufErrors, InErrors, ReasmReqds/OKs/Fails
ros2 doctor --report                             # สภาพแวดล้อม/middleware
```

| สคริปต์ (`captures/scripts/`) | ทำอะไร | เวลาที่บันทึกไว้ |
|---|---|---|
| `run_experiments.sh` | การทดลองที่ 1–6 + pcap ที่กรองแล้ว + `summary.txt` | 107 s และ 102 s ([ภาค 3 §8](03_wire_experiments.md#8-วิธีทำซ้ำ)) |
| `run_rcvbuf_sweep.sh` | การทดลองที่ 7 (sweep `SO_RCVBUF`) และ `--shape tbf1g\|wifi` (การทดลองที่ 9) | 81 run 1 477 s; tbf 275 s, wifi 274 s ([ภาค 3 §9.2](03_wire_experiments.md#9-การทดลองที่-7-sweep-ขนาด-receive-buffer-แก้ตัวแปรกวนของการทดลองที่-56), [§11.2](03_wire_experiments.md#112-setup)) |
| `run_latency.sh` | การทดลองที่ 8 (7 config × 30 รอบ, rclpy) | 1 584 s ([ภาค 3 §10.2](03_wire_experiments.md#10-การทดลองที่-8-latency-ที่วัดจริง-end-to-end-rclpy)) |

## ตัวเลขหลักของชุดเอกสาร

| ตัวเลข | ค่า | ที่มา |
|---|---|---|
| หนึ่ง sample `"Hello World: 1"` (Fast DDS) | frame 198 B = 14 + 20 + 8 + RTPS 156 (header 20, INFO_DST 16, INFO_TS 12, DATA 48, statistics 60) | [ภาค 1 §5.4](01_network_stack_deep_dive.md#54-packet-จริงระดับ-byte-หนึ่ง-sample-บนสาย), [ภาค 3 §2](03_wire_experiments.md#2-การทดลองที่-1-หนึ่ง-sample-ของ-talker-บนสายจริง) |
| sample เดียวกันผ่าน Zenoh/TCP | 161 B (TCP 32, Zenoh 95, prefix `5d 00`, attachment 33 B) | [ภาค 3 §4](03_wire_experiments.md#4-การทดลองที่-3-sample-เดียวกันผ่าน-rmw_zenoh) |
| chatter เทียบ traffic ทั้งหมด 14 s แรก | 3.3% (9 × 198 B จาก 53 434 B) | [ภาค 3 §2](03_wire_experiments.md#2-การทดลองที่-1-หนึ่ง-sample-ของ-talker-บนสายจริง) |
| SPDP `DATA(p)` | 610 B, ทุก 3 s หลัง 6 ครั้งแรกห่าง 100 ms | [ภาค 3 §2](03_wire_experiments.md#2-การทดลองที่-1-หนึ่ง-sample-ของ-talker-บนสายจริง) |
| ภาพ 640×480 rgb8 | `sampleSize` 921 648 B, `fragmentSize` 65 324 B, 15 DATA_FRAG, 45 IP fragment ต่อ datagram (UDP 65 476 B), 635 frame | [ภาค 3 §3](03_wire_experiments.md#3-การทดลองที่-2-ภาพ-640480-rgb8-แบบ-reliable), [ภาค 2 §2.4](02_wire_format_and_kernel.md#24-ตัวอย่างคำนวณ-sensor_msgsimage-640480-rgb8) |
| ภาพหนึ่งภาพบน 1 GbE (คำนวณ) | 7.68 ms; ที่ 30 fps = 230 Mb/s | [ภาค 2 §2.4](02_wire_format_and_kernel.md#24-ตัวอย่างคำนวณ-sensor_msgsimage-640480-rgb8), [ภาค 3 §11.1](03_wire_experiments.md#11-การทดลองที่-9-จำกัดอัตราส่งด้วย-tc-จำลอง-link-1-gbits) |
| `SO_RCVBUF` จริง | 2 × min(ขอ, `rmem_max`); default 212 992 ไม่คูณ 2 | [ภาค 3 §9.3](03_wire_experiments.md#93-ตรวจตัวแปร-ค่าที่-kernel-ใช้จริงและสิ่งที่ไม่เปลี่ยน-v) |
| BEST_EFFORT ที่ buffer default บน veth | 13/20 (`RcvbufErrors` 45) เมื่อ 2026-11-24; 19/20 ทุก run เมื่อ 2026-11-27 | [ภาค 3 §6](03_wire_experiments.md#6-การทดลองที่-56-receive-buffer-ตัดสินว่าภาพจะรอดหรือไม่), [§9.4](03_wire_experiments.md#94-ผล-best_effort-20-ภาพต่อ-run-v) |
| จุดที่ภาพเลิกหาย (veth) | `SO_RCVBUF` 425 984 ยังหาย, 1 048 576 ไม่หาย | [ภาค 3 §9.6](03_wire_experiments.md#96-เทียบกับข้อสรุปเดิม) |
| RELIABLE ที่ buffer default | ได้ 20/20, NACK_FRAG 1 ต่อ run, ส่งซ้ำ = `RcvbufErrors` (4–5) | [ภาค 3 §9.5](03_wire_experiments.md#95-ผล-reliable-20-ภาพต่อ-run-5-run-ต่อแขน-v) |
| burst ต่อภาพ | veth ~1.04 ms (11-24), ~3.5 ms (11-27); tbf 1 Gbit/s 7.63 ms; wifi จำลอง 95.5 ms | [ภาค 3 §11.3](03_wire_experiments.md#113-เวลาที่ภาพหนึ่งภาพมาถึงผู้รับ-v-capture-ฝั่งรับ-ความละเอียด-1-µs) |
| tc 1 Gbit/s | buffer default ไม่หาย (0 `RcvbufErrors` ใน 15 run) | [ภาค 3 §11.4](03_wire_experiments.md#114-ผล-v) |
| wifi จำลอง | BE หาย 13–15%; REL ได้ครบแต่ DATA_FRAG 1 520.2 ต่อ run (≈ 5 เท่าของ 300) | [ภาค 3 §11.4](03_wire_experiments.md#114-ผล-v) |
| latency ข้อความเล็ก (rclpy) | median 754 µs (veth), 753 (UDP loopback), 716 (SHM); `publish()` 155–207 µs | [ภาค 3 §10.3](03_wire_experiments.md#103-ผลหลัก) |
| latency ภาพ (rclpy) | ข้าม container 7.76 ms (p99 8.28); SHM ในเครื่อง bimodal ~5 / ~15–16 ms | [ภาค 3 §10.3](03_wire_experiments.md#103-ผลหลัก) |
| SHM ของ Fast DDS | segment 549 408 B ต่อ participant (512 KiB + header), port `fastdds_port<N>` | [ภาค 3 §5](03_wire_experiments.md#5-การทดลองที่-4-เครื่องเดียวกัน-fast-dds-shm), [ภาค 2 §3.4](02_wire_format_and_kernel.md#34-shm-transport-ในระดับ-os) |
| ค่าเวลา reliable default | heartbeat 3 s, `heartbeat_response_delay` 5 ms, `nack_response_delay` 5 ms | [ภาค 2 §2.3](02_wire_format_and_kernel.md#23-ค่าเวลา-default-ของ-fast-dds-36x) |
