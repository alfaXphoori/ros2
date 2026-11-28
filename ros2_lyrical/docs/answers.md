# เฉลยแบบฝึกหัด

> เฉลยของ [exercises.md](exercises.md) · ทุกคำสั่งรันจริงจาก root ของ repo เมื่อ 2026-11-27 กับไฟล์ที่ commit ไว้ใน `captures/` ผลที่แสดงตัดมาเฉพาะส่วนที่ใช้ (`…` = ตัดออก) · `pk` และ `tsh` คือ shell function ในหัวข้อ "การเตรียมเครื่อง" ของ exercises.md และ `C=ros2_lyrical/captures`
>
> ลองทำเองก่อนเปิดเฉลย คำตอบเชิงตีความ (ข้อ 3.x, 4.x) มีได้หลายแบบ เกณฑ์คือทุกข้อสรุปต้องชี้กลับไปที่ตัวเลขในไฟล์ได้ และต้องบอกขอบเขตของข้อสรุป

---

## ภาค 1

### 1.1 port ของ RTPS

```bash
tsh -r /c/exp1_fastdds_default.pcap -T fields -e ip.src -e ip.dst -e udp.dstport 2>/dev/null | sort | uniq -c
tsh -r /c/exp4_samehost_shm.pcap    -T fields -e ip.src -e ip.dst -e udp.dstport 2>/dev/null | sort | uniq -c
```
```
# exp1
      4 172.20.0.2	172.20.0.3	7000
     18 172.20.0.2	172.20.0.3	7410
      7 172.20.0.2	172.20.0.3	7411
     11 172.20.0.2	239.255.0.1	7400
     25 172.20.0.3	172.20.0.2	7000
     60 172.20.0.3	172.20.0.2	7410
     15 172.20.0.3	172.20.0.2	7411
     10 172.20.0.3	239.255.0.1	7400
     …  (บรรทัดที่ไม่มี port: ARP, IGMP และ IP fragment ที่ไม่ใช่ชิ้นแรก)
# exp4
     58 127.0.0.1	127.0.0.1	7410
     19 127.0.0.1	127.0.0.1	7412
     16 127.0.0.1	239.255.0.1	7400
     16 172.17.0.2	239.255.0.1	7400
     …
```

| domain 0 | participant 0 | participant 1 |
|---|---|---|
| SPDP multicast = 7400 + 250·0 + 0 | 7400 | 7400 |
| metatraffic unicast = 7400 + 10 + 2·pid | 7410 | 7412 |
| user multicast = 7400 + 1 | 7401 | 7401 |
| user unicast = 7400 + 11 + 2·pid | 7411 | 7413 |

**คำตอบ:** `exp1` เห็น 7400 (multicast), 7410 และ 7411 ทั้งสองทิศ เพราะ talker และ listener อยู่คนละ container (คนละ network namespace) แต่ละตัวจึงเป็น participant แรกของ "เครื่อง" ตัวเองและได้ participant id 0 ทั้งคู่ ส่วน `exp4` มีสอง participant ใน namespace เดียวกัน ตัวที่สองจึงได้ id 1 และเห็น 7412 (metatraffic ของ participant 1) บน `lo` ไม่เห็น 7411/7413 เลยเพราะ user data ไปทาง SHM (ข้อ 1.4) ทั้งที่[ภาค 3 §5](03_wire_experiments.md#5-การทดลองที่-4-เครื่องเดียวกัน-fast-dds-shm)พบไฟล์ `fastdds_port7411` และ `fastdds_port7413` ใน `/dev/shm` ซึ่งตั้งชื่อตาม port เดียวกันนี้ port 7401 (user multicast) ไม่ปรากฏเพราะ endpoint ใน ROS ไม่ได้ใช้ multicast สำหรับข้อมูล และ port **7000** ไม่ได้มาจากสูตร เป็น unicast locator ที่ reader ของ `ros_discovery_info` ประกาศไว้ (สาเหตุในโค้ดยังเป็น [K] ตาม[ภาค 3 §2](03_wire_experiments.md#2-การทดลองที่-1-หนึ่ง-sample-ของ-talker-บนสายจริง))

### 1.2 แยกชั้นของ frame 198 B

```bash
pk frame ros2_lyrical/captures/exp1_fastdds_default.pcap 95 | head -6
```
```
frame 95: 198 B
  0000  62 1b 4b 57 a2 ac 42 8d e7 ce ea 36 08 00 45 00  b.KW..B....6..E.
  0010  00 b8 10 29 40 00 40 11 d1 de ac 14 00 03 ac 14  ...)@.@.........
  0020  00 02 b0 4f 1c f3 00 a4 58 e3 52 54 50 53 02 03  ...O....X.RTPS..
  …
```

**คำตอบ:** IPv4 total length ที่ offset 0x10 = `00 b8` = 184 (IP 20 + UDP 8 + RTPS 156), UDP length ที่ 0x26 = `00 a4` = 164 (UDP 8 + RTPS 156) จึงได้ 14 + 20 + 8 + 156 = 198 B ตรงกับ[ภาค 1 §5.4](01_network_stack_deep_dive.md#54-packet-จริงระดับ-byte-หนึ่ง-sample-บนสาย) บนสาย 1 GbE ต้องบวก FCS 4 + preamble/SFD 8 + IFG 12 = 222 byte-time = 1.776 µs ข้อความ 14 ตัวอักษรจึงใช้ byte บนสายราว 16 เท่าของตัวข้อความ

### 1.3 Discovery กับข้อมูลจริง

```bash
tsh -r /c/exp1_fastdds_default.pcap -q -z io,phs 2>/dev/null | grep -E 'udp|rtps'
pk sms ros2_lyrical/captures/exp1_fastdds_default.pcap DATA | grep -c 'writer 00.00.13.03'
tsh -r /c/exp1_fastdds_default.pcap -Y 'rtps && frame.len==198' -T fields -e frame.number 2>/dev/null | tr '\n' ' '
pk frame ros2_lyrical/captures/exp1_fastdds_default.pcap 162 | grep DATA
tsh -r /c/exp1_fastdds_default.pcap -Y 'frame contains "ros_discovery_info"' -V 2>/dev/null \
    | grep -E 'writerEntityId|entityId: Unknown|topic: ros' | head -4
```
```
      udp                                frames:150 bytes:55436
        rtps                             frames:137 bytes:53434
9
95 101 102 105 110 113 116 121 122 162
  [ 48] DATA               flags 0x05 len 44    reader 00.00.02.04 writer 00.00.01.03 SN 22 | payload 24 B: …
        writerEntityId: ENTITYID_BUILTIN_PUBLICATIONS_WRITER (0x000003c2)
                        entityId: Unknown (0x00000103)
                    topic: ros_discovery_info
```

**คำตอบ:** chatter 9 sample × 198 B = 1 782 B จาก RTPS 53 434 B = **3.3%** อีก 96.7% เป็น discovery (SPDP, SEDP, HEARTBEAT/ACKNACK, `ros_discovery_info`) ตรงกับตารางใน[ภาค 3 §2](03_wire_experiments.md#2-การทดลองที่-1-หนึ่ง-sample-ของ-talker-บนสายจริง) frame 162 ยาว 198 B เหมือนกันแต่มาจาก writer `00.00.01.03` ซึ่ง SEDP `DATA(w)` ประกาศว่าเป็น writer ของ topic `ros_discovery_info` บทเรียนคือ filter ตามขนาด frame ไม่พอ ต้องแยกตาม writerId (หรือชื่อ topic ใน SEDP) ข้อนี้นับเฉพาะ 14 วินาทีแรก สัดส่วนจะลดลงเมื่อรันนานขึ้นเพราะ discovery หลังช่วงเริ่มต้นมีแค่ SPDP ทุก 3 s กับ heartbeat

### 1.4 ทำไม `exp4` เห็น discovery แต่ไม่เห็นข้อมูล

```bash
pk sms ros2_lyrical/captures/exp4_samehost_shm.pcap DATA DATA_FRAG \
  | grep -o 'flags 0x.. .*writer [0-9a-f.]*' | awk '{print $1,$2,$NF}' | sort | uniq -c
```
```
     11 flags 0x03 00.00.03.c2
      8 flags 0x03 00.00.04.c2
      3 flags 0x03 00.01.00.c2
     21 flags 0x05 00.00.03.c2
     17 flags 0x05 00.00.04.c2
     40 flags 0x05 00.01.00.c2
```

**คำตอบ:** ทุก DATA มาจาก builtin writer (`…c2`: SPDP `00.01.00.c2`, SEDP publications `00.00.03.c2`, SEDP subscriptions `00.00.04.c2`) ไม่มี writer ที่ลงท้าย `03` และไม่มี DATA_FRAG เลย ทั้งที่ listener ได้ทุกข้อความ ข้อมูลจึงไปทาง Fast DDS SHM transport ซึ่งเปิดเป็น default เมื่อ participant อยู่บนเครื่องเดียวกัน ([ภาค 1 §3.1](01_network_stack_deep_dive.md#31-rmw_fastrtps_cpp--fast-dds-36x-default-v-เวอร์ชัน--k-รายละเอียด-protocol)) ส่วน discovery ยังวิ่งบน UDP เพราะ SPDP ต้องประกาศให้เครื่องอื่นใน subnet เห็นด้วย (multicast 7400 ออกทั้ง `lo` และ interface ของ container) และ SEDP ใช้ metatraffic unicast locator ของ UDP flags `0x03` คือ DATA ที่มีแค่ inline QoS (`STATUS_INFO` dispose/unregister ตอนปิด node) ตาม[ภาค 3 §5](03_wire_experiments.md#5-การทดลองที่-4-เครื่องเดียวกัน-fast-dds-shm)

---

## ภาค 2

### 2.1 บัญชี byte ของ RTPS message 156 B

```bash
pk frame ros2_lyrical/captures/exp1_fastdds_default.pcap 95 | tail -5
```
```
RTPS v2.3 vendor 01.0f guidPrefix 01 0f 11 31 1a 00 bc 0d 00 00 00 00
  [ 20] INFO_DST           flags 0x01 len 12    dst guidPrefix 01 0f 2c 17 1d 00 1c 48 00 00 00 00
  [ 36] INFO_TS            flags 0x01 len 8     time 1795512497.545006298
  [ 48] DATA               flags 0x05 len 44    reader 00.00.13.04 writer 00.00.13.03 SN 1 | payload 24 B: encap 0001 b'\x0f\x00\x00\x00Hello World: 1\x00\x00'
  [ 96] FASTDDS_STATISTICS flags 0x01 len 56
```

| ส่วน | offset | ขนาด |
|---|---|---|
| RTPS header (`RTPS`, 2.3, vendor 01.0f, guidPrefix 12) | 0 | 20 |
| INFO_DST (4 + 12) | 20 | 16 |
| INFO_TS (4 + 8) | 36 | 12 |
| DATA (4 + 44 = ส่วนคงที่ 20 + payload 24) | 48 | 48 |
| statistics `0x80` (4 + 56) | 96 | 60 |
| **รวม** | | **156** |

**คำตอบ:** ส่วนคงที่ 20 B ของ DATA คือ extraFlags 2 + octetsToInlineQos 2 + readerId 4 + writerId 4 + writerSN 8 ([ภาค 2 §2.2](02_wire_format_and_kernel.md#22-layout-ทีละ-field)) payload 24 B = `00 01 00 00` (encapsulation CDR_LE + options) + `0f 00 00 00` (ความยาว string 15 รวม `\0`, little-endian) + `"Hello World: 1\0"` 15 B + pad 1 B ตัว CDR เองจบที่ 23 B ส่วน pad 1 B มาจากการที่ submessage ของ RTPS ต้องยาวหาร 4 ลงตัว [K: กฎ alignment ของ submessage] ซึ่งเห็นได้จาก Zenoh ที่ส่ง payload เดียวกันเพียง 23 B (ข้อ 2.4)

### 2.2 DATA_FRAG และ IP fragment ของหนึ่งภาพ

```bash
pk sms ros2_lyrical/captures/exp2_image_reliable.pcap.gz DATA_FRAG | grep 'SN 3 ' | grep -o 'len [0-9]* .*' | sort | uniq -c
pk fragcount ros2_lyrical/captures/exp2_image_reliable.pcap.gz
pk sms ros2_lyrical/captures/exp2_image_reliable.pcap.gz DATA_FRAG | grep -o 'SN [0-9]*' | sort | uniq -c
```
```
      1 len 65356 reader 00.00.14.04 writer 00.00.14.03 SN 3 fragStart 10 inSub 1 fragSize 65324 sampleSize 921648
      …   (fragStart 1–14 เหมือนกันทุกบรรทัด: len 65356)
      1 len 7144  reader 00.00.14.04 writer 00.00.14.03 SN 3 fragStart 15 inSub 1 fragSize 65324 sampleSize 921648
datagrams ที่ถูก IP fragment: 99 · fragment ต่อ datagram: Counter({45: 91, 5: 7, 4: 1})
     18 SN 1
     21 SN 2
     15 SN 3
     15 SN 4
     28 SN 5
```

**คำตอบ:** SN 3 มี DATA_FRAG 15 ก้อน `fragmentSize` 65 324, `sampleSize` 921 648 ข้อมูลของก้อนสุดท้าย = 7 144 − 32 = 7 112 B และ 14 × 65 324 + 7 112 = 914 536 + 7 112 = **921 648** พอดี

ต่อ datagram เต็ม: RTPS = 20 + 16 + 12 + 36 + 65 324 + 60 = 65 468 B, UDP = 65 476 B, IP payload ต่อ fragment ที่ MTU 1500 = 1 480 B จึงได้ ceil(65 476 / 1 480) = **45** ชิ้น (44 × 1 480 + 356) ก้อนสุดท้าย: RTPS 7 256, UDP 7 264 → ceil(7 264 / 1 480) = **5** ชิ้น `fragcount` ยืนยัน: datagram 45 ชิ้น 91 ก้อน + 5 ชิ้น 7 ก้อน + 4 ชิ้น 1 ก้อน DATA_FRAG ทั้งไฟล์ 97 ก้อนเป็นก้อนเต็ม 91 และก้อนสุดท้าย (`fragStart 15`) 6 ก้อน (5 ภาพ + ส่งซ้ำ 1 ใน SN 5) ที่เหลือ 2 datagram ไม่ใช่ DATA_FRAG (ไม่ได้ไล่ว่าเป็นอะไร) ภาพหนึ่งภาพจึงเป็น 14 × 45 + 5 = 635 frame ตาม[ภาค 2 §2.4](02_wire_format_and_kernel.md#24-ตัวอย่างคำนวณ-sensor_msgsimage-640480-rgb8)

ตารางใน §2.4 ให้ก้อนสุดท้าย 7 116 B เพราะคำนวณจาก `sampleSize` 921 652 (สมมติ `frame_id = "camera"`) ส่วนสคริปต์ใช้ `"f0"` ซึ่งสั้นกว่า 4 B ไม่ใช่ความขัดแย้ง

### 2.3 การซ่อม fragment ด้วย NACK_FRAG

```bash
pk sms ros2_lyrical/captures/exp2_image_reliable.pcap.gz NACK_FRAG
pk sms ros2_lyrical/captures/exp2_image_reliable.pcap.gz DATA_FRAG HEARTBEAT ACKNACK NACK_FRAG | awk '/^frame/{f=$2} f>=744 && f<=900'
pk sms ros2_lyrical/captures/exp2_image_reliable.pcap.gz DATA_FRAG HEARTBEAT ACKNACK NACK_FRAG | awk '/^frame/{f=$2} f>=600 && f<=610'
```
```
frame 749 1795512599.460066 172.20.0.2 -> 172.20.0.3 ip.id 51279 MF=False
  [ 36] NACK_FRAG          flags 0x01 len 32    writer 00.00.14.03 SN 1 bitmapBase 4 numBits 3 -> ขอ fragment [4, 5, 6]
frame 1534 …  SN 2 bitmapBase 3 numBits 10 -> ขอ fragment [3, 4, 10, 11, 12]
frame 1764 …  SN 2 bitmapBase 12 numBits 1 -> ขอ fragment [12]
frame 3746 …  SN 5 bitmapBase 3 numBits 13 -> ขอ fragment [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
---
frame 744 1795512599.455322 172.20.0.3 -> 172.20.0.2 ip.id 12890 MF=True
  [ 48] DATA_FRAG          flags 0x01 len 7144  … SN 1 fragStart 15 …
frame 749 1795512599.460066 172.20.0.2 -> 172.20.0.3 ip.id 51279 MF=False
  [ 36] NACK_FRAG          flags 0x01 len 32    writer 00.00.14.03 SN 1 bitmapBase 4 numBits 3 -> ขอ fragment [4, 5, 6]
  [ 72] ACKNACK            flags 0x03 len 24
frame 750 1795512599.465302 172.20.0.3 -> 172.20.0.2 ip.id 12897 MF=True
  [ 48] DATA_FRAG          flags 0x01 len 65356 … SN 1 fragStart 4 …
frame 795 1795512599.465633 …
  [ 20] HEARTBEAT          flags 0x01 len 28    writer 00.00.14.03 firstSN 1 lastSN 1
frame 796 1795512599.465672 … SN 1 fragStart 5 …
frame 841 1795512599.465768 … SN 1 fragStart 6 …
frame 886 1795512599.465854 … HEARTBEAT … firstSN 1 lastSN 1
frame 887 1795512599.471821 172.20.0.2 -> 172.20.0.3 …
  [ 36] ACKNACK            flags 0x03 len 24
---
frame 607 1795512599.455067 172.20.0.3 -> 172.20.0.2 ip.id 12885 MF=False
  [ 20] HEARTBEAT          flags 0x01 len 28    writer 00.00.14.03 firstSN 1 lastSN 1
frame 608 …  DATA_FRAG … SN 1 fragStart 12 …
```

**คำตอบ:** NACK_FRAG ฉบับแรกคือ frame 749 bitmap `0xe0000000` (3 บิตแรกเป็น 1 นับจาก bitmapBase 4) จึงขอ fragment 4, 5, 6 ของ SN 1 writer ส่งซ้ำใน frame 750, 796, 841 ตามลำดับ แล้วปิดด้วย HEARTBEAT และ ACKNACK (frame 887)

- DATA_FRAG สุดท้าย (frame 744) → NACK_FRAG: 0.460066 − 0.455322 = **4.74 ms** แต่ถ้านับจาก HEARTBEAT ที่แทรกอยู่ระหว่าง DATA_FRAG (frame 607) ได้ 0.460066 − 0.455067 = **5.00 ms** ใกล้ `heartbeat_response_delay` 5 ms
- NACK_FRAG → DATA_FRAG ซ้ำก้อนแรก: 0.465302 − 0.460066 = **5.24 ms** ใกล้ `nack_response_delay` 5 ms

สอดคล้องกับค่า default ใน[ภาค 2 §2.3](02_wire_format_and_kernel.md#23-ค่าเวลา-default-ของ-fast-dds-36x) และลำดับการกู้คืนใน §2.5 แต่ยังไม่ใช่การพิสูจน์: เวลาทั้งหมดมาจาก capture ฝั่งผู้รับ (ความละเอียด 1 µs) เห็นเพียงไม่กี่ครั้ง และไม่ได้ trace ว่า timer ตัวไหนในโค้ดเป็นผู้ส่ง ถ้าจะยืนยันต้องใช้ tracing ฝั่ง writer/reader ข้อสังเกตเพิ่ม: capture เห็น fragment 4–6 ครั้งแรกครบ แต่ reader ยังต้องขอใหม่ แปลว่าทิ้งหลังจุดที่ tcpdump เห็น (ข้อ 3.1)

### 2.4 Zenoh sample 161 B

```bash
tsh -r /c/exp3_zenoh.pcap -Y 'frame.len==161' -T fields -e frame.number -e ip.src -e tcp.srcport -e ip.dst -e tcp.dstport -e tcp.len 2>/dev/null
tsh -r /c/exp3_zenoh.pcap -Y 'frame.number==142' -x 2>/dev/null
```
```
142	172.20.0.4	35545	172.20.0.3	57268	95
145	172.20.0.4	35545	172.20.0.3	57268	95
…   (8 frame)
0000  8a 93 a7 c1 eb d7 8e 97 af 36 6e eb 08 00 45 00   .........6n...E.
0010  00 93 1b e8 40 00 40 06 c6 4d ac 14 00 04 ac 14   ....@.@..M......
0020  00 03 8a d9 df b4 af 36 53 92 7e bb cc 0a 80 18   .......6S.~.....
0030  00 3f 58 b5 00 00 01 01 08 0a 9a 1b dd 86 91 8a   .?X.............
0040  6f 17 5d 00 25 e7 91 b6 08 1d 02 a1 90 d2 ea e8   o.].%...........
0050  aa ae d6 82 6b 10 24 7c cf 5d f0 b0 51 a8 4e a7   ....k.$|.]..Q.N.
0060  82 d1 9c f6 f2 f9 43 21 01 00 00 00 00 00 00 00   ......C!........
0070  69 be 75 75 47 f1 ea 18 10 c5 89 fb 05 d4 36 e0   i.uuG.........6.
0080  a1 d6 3d 56 87 be 42 25 fe 17 00 01 00 00 0f 00   ..=V..B%........
0090  00 00 48 65 6c 6c 6f 20 57 6f 72 6c 64 3a 20 31   ..Hello World: 1
00a0  00                                                .
```

**คำตอบ:** IPv4 total length `00 93` = 147, TCP data offset `0x80` = 8 word = 32 B (20 + timestamp option 12), TCP payload 95 B จึงได้ 14 + 20 + 32 + 95 = **161 B** TCP payload เริ่มที่ offset 0x42 ด้วย `5d 00` = u16 little-endian 0x005d = **93** = ความยาว batch ที่ตามมา (2 + 93 = 95) byte ถัดไป `25` คือ FRAME (`0x05` + flag R) และ `1d` คือ PUSH ตาม[ภาค 2 §4.1–§4.2](02_wire_format_and_kernel.md#42-framing-บน-tcp)

attachment อยู่ที่ offset 0x68–0x88 (33 B): sequence number `01 00 … 00` = 1 (8 B), source timestamp (8 B), ความยาว GID `10` = 16 (1 B), GID 16 B จากนั้น `17` = 23 คือความยาว payload และ payload 23 B ที่ 0x8a–0xa0 = `00 01 00 00` + `0f 00 00 00` + `"Hello World: 1\0"` ไม่มี pad เพราะ Zenoh ไม่บังคับ alignment แบบ submessage ของ RTPS byte `21` (= 33) ที่ 0x67 ก่อน attachment น่าจะเป็นความยาวของ extension และการแยก field ระหว่าง `1d` ถึง 0x66 เป็นการตีความตามลำดับ codec ที่ภาค 3 §4 ระบุว่ายังไม่ได้เทียบกับ Zenoh dissector [K]

### 2.5 `SO_RCVBUF` กับ `truesize`

```bash
grep -h 'rmem_max' ros2_lyrical/captures/results/rcvbuf_sweep_env.txt | head -3
python3 - <<'PY'
import csv
print('arm req rb_eff n_dgram(132480) n_dgram(97920) loss_pct rcvbuferr_med')
for r in csv.DictReader(open('ros2_lyrical/captures/results/rcvbuf_sweep_summary.csv')):
    if r['qos'] != 'be': continue
    rb = int(r['rb_eff_B'])
    print(r['arm'], r['req_bytes'] or '-', rb, rb // 132480, rb // 97920, r['loss_pct'], r['rcvbuferr_med'])
PY
```
```
host      net.core.rmem_max = 4194304
container net.core.rmem_max = 4194304
…
arm req rb_eff n_dgram(132480) n_dgram(97920) loss_pct rcvbuferr_med
noxml - 212992 1 2 5 4
106496 106496 212992 1 2 5 3.5
212992 212992 425984 3 4 5.6 2
524288 524288 1048576 7 10 0 0
1048576 1048576 2097152 15 21 0 0
2097152 2097152 4194304 31 42 0 0
4194304 4194304 8388608 63 85 0 0
8388608 8388608 8388608 63 85 0 0
oldbigbuf 4194304 8388608 63 85 0 0
sndonly - 212992 1 2 5 3
```

**คำตอบ:** ทุกแขนที่มี XML ได้ `rb_eff_B` = 2 × min(ค่าที่ขอ, 4 194 304) เช่น 106 496 → 212 992, 212 992 → 425 984, 8 388 608 → 8 388 608 (ถูก `rmem_max` จำกัด) ส่วน `noxml` และ `sndonly` ได้ `rmem_default` 212 992 โดยไม่คูณ 2 ตาม[ภาค 2 §5.3](02_wire_format_and_kernel.md#53-so_rcvbuf-นับอะไร-และทำไมภาพหายทั้งที่-cpu-ว่าง)

ที่ 212 992 buffer รับ datagram 65 KB ได้ 1–2 ก้อน (แล้วแต่ `truesize` 132 480 หรือ 97 920) ที่ 425 984 ได้ 3–4 ก้อน และยังหาย ส่วนที่ 1 048 576 ได้ 7–10 ก้อนและไม่หายเลยใน 8 run ภาพหนึ่งภาพมี 15 datagram buffer จึงไม่จำเป็นต้องจุทั้งภาพ เพราะ thread `dds.udp.7411` ระบายไปพร้อมกัน แต่ต้องจุส่วนที่มาถึงเร็วกว่าที่ thread ระบายได้ ข้อจำกัด: (1) `truesize` ทั้งสองค่าเป็นประมาณการ ยังไม่ได้วัดด้วย bpftrace (2) จุดตัดอยู่ระหว่าง 425 984 กับ 1 048 576 ซึ่งไม่ได้วัดค่าระหว่างกลาง (3) ผลขึ้นกับความเร็วที่ข้อมูลมาถึงบน `veth` (ข้อ 3.4) จำนวน datagram ที่ "พอ" บนสายจริงจึงอาจต่างไป (4) จำนวน run 5–8 ต่อแขน

---

## ภาค 3

### 3.1 capture เห็นครบ แต่ภาพหาย

```bash
for f in exp5_image_besteffort exp6_image_besteffort_bigbuf; do
  python3 ros2_lyrical/captures/scripts/sweep_pcap_stats.py ros2_lyrical/captures/$f.pcap.gz
done
```
```
{"frames": 12860, "datafrag_total": 300, "datafrag_unique": 300, …, "nackfrag": 0, "sn_seen": 20, "sn_complete": 20, "ip_frags_per_dgram": 45, …}
{"frames": 12860, "datafrag_total": 300, "datafrag_unique": 300, …, "nackfrag": 0, "sn_seen": 20, "sn_complete": 20, "ip_frags_per_dgram": 45, …}
```

**คำตอบ:** ทั้งสองไฟล์มี DATA_FRAG 300 ก้อน (20 × 15) และภาพที่ fragment ครบ 20/20 capture จึงไม่บอกว่าภาพหาย เพราะ tcpdump เห็น packet ที่ AF_PACKET tap (ขั้นที่ 6 ของตาราง RX ใน[ภาค 1 §5.5](01_network_stack_deep_dive.md#55-เส้นทางใน-linux-kernel-ทีละฟังก์ชัน-tx-และ-rx)) ก่อน IP reassembly และก่อนเข้า socket การทิ้งเกิดที่ `__udp_enqueue_schedule_skb` (ขั้นที่ 12) เมื่อ `sk_rcvbuf` เต็ม และนับใน `Udp RcvbufErrors` ของ `/proc/net/snmp` ซึ่งเป็น 45 ในรอบ 2026-11-24 ของ `exp5` (13/20 ภาพ) ตาม[ภาค 3 §6](03_wire_experiments.md#6-การทดลองที่-56-receive-buffer-ตัดสินว่าภาพจะรอดหรือไม่) ภาพ BEST_EFFORT ที่ขาด DATA_FRAG เดียวจะหายทั้งภาพ `exp6` ไม่ใช่การเปลี่ยนตัวแปรเดียว เพราะ `bigbuf.xml` ตั้ง send buffer ด้วย ปิด builtin transport (ไม่มี SHM) และใส่ให้ทั้งสองฝั่ง ([ภาค 3 §9.1](03_wire_experiments.md#91-ตัวแปรกวนในการทดลองที่-6)) นอกจากนี้ pcap ของ `exp6` capture คนละวันกับตัวนับในตาราง §6

### 3.2 อ่านผล rcvbuf sweep

```bash
python3 - <<'PY'
import csv
for r in csv.DictReader(open('ros2_lyrical/captures/results/rcvbuf_sweep_summary.csv')):
    if r['qos'] == 'be' and r['arm'] in ('noxml', 'sndonly', '524288'):
        print({k: r[k] for k in ('arm','n','rb_eff_B','tb_A_max','delivered_mean','delivered_min','loss_pct','rcvbuferr_med','rcvbuferr_min','rcvbuferr_max','datafrag_wire_mean','sn_complete_min')})
PY
```
```
{'arm': 'noxml', 'n': '8', 'rb_eff_B': '212992', 'tb_A_max': '212992', 'delivered_mean': '19', 'delivered_min': '19', 'loss_pct': '5', 'rcvbuferr_med': '4', 'rcvbuferr_min': '3', 'rcvbuferr_max': '5', 'datafrag_wire_mean': '300', 'sn_complete_min': '20'}
{'arm': '524288', 'n': '8', 'rb_eff_B': '1048576', 'tb_A_max': '212992', 'delivered_mean': '20', 'delivered_min': '20', 'loss_pct': '0', 'rcvbuferr_med': '0', 'rcvbuferr_min': '0', 'rcvbuferr_max': '0', 'datafrag_wire_mean': '300', 'sn_complete_min': '20'}
{'arm': 'sndonly', 'n': '5', 'rb_eff_B': '212992', 'tb_A_max': '8388608', 'delivered_mean': '19', 'delivered_min': '19', 'loss_pct': '5', 'rcvbuferr_med': '3', 'rcvbuferr_min': '2', 'rcvbuferr_max': '5', 'datafrag_wire_mean': '300', 'sn_complete_min': '20'}
```

| แขน | n | `SO_RCVBUF` ผู้รับ | send buffer ผู้ส่ง | ภาพที่ได้ | `RcvbufErrors` median (min–max) |
|---|---|---|---|---|---|
| `noxml` | 8 | 212 992 | 212 992 | 19/20 ทุก run | 4 (3–5) |
| `sndonly` | 5 | 212 992 | 8 388 608 | 19/20 ทุก run | 3 (2–5) |
| `524288` | 8 | 1 048 576 | 212 992 | 20/20 ทุก run | 0 (0–0) |

**คำตอบ:** ข้อมูลรองรับว่า บนเครื่องนี้ (veth, ภาพ 921 600 B ทุก 0.5 s, 2026-11-27) การเพิ่ม `SO_RCVBUF` ของผู้รับเพียงอย่างเดียวเป็น 1 048 576 ทำให้ภาพไม่หายใน 8/8 run ขณะที่การเพิ่ม send buffer ของผู้ส่ง (`sndonly`) ไม่เปลี่ยนผล ทุกแขนเห็น DATA_FRAG ครบ 300 ใน capture การสูญหายจึงอยู่ที่ socket ผู้รับ ข้อมูล**ไม่**รองรับ (1) อัตราการสูญหายบนเครือข่ายจริง เพราะ veth ส่งเร็วกว่า 1 GbE และเมื่อจำกัดอัตราที่ 1 Gbit/s ค่า default ก็ไม่หาย ([ภาค 3 §11](03_wire_experiments.md#11-การทดลองที่-9-จำกัดอัตราส่งด้วย-tc-จำลอง-link-1-gbits)) (2) ค่าที่พอดีระหว่าง 425 984 กับ 1 048 576 (3) ความน่าจะเป็นต่ำ ๆ เพราะ n = 5–8 และช่วงที่รายงานเป็น min–max ไม่ใช่ CI (4) กรณีไม่เปิด tcpdump ([ภาค 3 §12.1](03_wire_experiments.md#121-ข้อจำกัดของผลในภาคนี้))

### 3.3 latency ของข้อความเล็ก

```bash
python3 - <<'PY'
import csv
for r in csv.DictReader(open('ros2_lyrical/captures/results/latency_summary.csv')):
    if r['payload'] == 'small':
        print(r['config'], r['n_samples'], r['median_us'], f"[{r['median_ci_lo']}-{r['median_ci_hi']}]", r['p99_us'], f"[{r['p99_ci_lo']}-{r['p99_ci_hi']}]", r['publish_call_median_us'])
PY
```
```
small_cross 11700 754.3 [738.3-766.6] 879.2 [862.5-893.7] 207.3
small_same 11700 716.0 [701.4-726.2] 795.9 [782.2-808.2] 154.7
small_same_udp 11700 753.2 [746.5-759.5] 827.7 [816.9-842.9] 193.5
```

**คำตอบ:** (ก) `small_same_udp` กับ `small_cross` มี median 753.2 และ 754.3 µs ที่ CI ซ้อนกัน การ "อยู่ container เดียวกัน" โดยยังใช้ UDP จึงไม่ทำให้เร็วขึ้นที่ median ส่วน `small_same` (SHM) 716.0 [701.4–726.2] ไม่ซ้อนกับ 753.2 [746.5–759.5] จึงเร็วกว่าราว 37 µs ซึ่งเป็นผลของ SHM ที่ tail `veth` แย่กว่า loopback (p99 879.2 [862.5–893.7] เทียบ 827.7 [816.9–842.9] ไม่ซ้อนกัน) (ข) latency ส่วนใหญ่ไม่ได้อยู่ที่ transport: เฉพาะการเรียก `publish()` ใน rclpy ก็ใช้ median 155–207 µs แล้ว และผลต่างระหว่าง transport มีเพียงหลักสิบ µs จากราว 700–750 µs ข้อจำกัด ([ภาค 3 §10.6](03_wire_experiments.md#106-ข้อจำกัด)): วัดผ่าน rclpy, governor `powersave`, ไม่ pin CPU, วัดช่วงเวลาเดียว, `veth` ไม่ใช่ NIC จึงใช้ตัวเลขนี้เป็นขอบบนของ rmw/transport ไม่ใช่ค่าของ C++ node

### 3.4 จังหวะการมาถึงของภาพ

```bash
for f in exp5_image_besteffort exp6_image_besteffort_bigbuf; do
  python3 ros2_lyrical/captures/scripts/sweep_pcap_stats.py ros2_lyrical/captures/$f.pcap.gz
done
python3 - <<'PY'
import csv
for r in csv.DictReader(open('ros2_lyrical/captures/results/shaping_summary.csv')):
    if r['qos'] == 'be' and r['arm'] == 'noxml':
        print(r['shape'], r['n'], r['burst_ms_med'], r['gap_us_med'], r['loss_pct'], r['rcvbuferr_med'])
PY
```
```
{… "burst_ms_med": 1.042, "burst_ms_min": 0.925, "burst_ms_max": 1.941, "dgram_us_med": 46.0, "gap_us_med": 1.0, … "image_wire_us_1g": 7684.3, …}
{… "burst_ms_med": 3.601, "burst_ms_min": 1.026, "burst_ms_max": 4.658, "dgram_us_med": 163.0, "gap_us_med": 4.0, … "image_wire_us_1g": 7684.3, …}
none 8 3.454 3.10 5 4
tbf1g 5 7.633 11.92 0 0
wifi 5 95.499 151.16 13 0
```

| เงื่อนไข | burst ต่อภาพ median (ms) | ระยะห่าง IP fragment (µs) | ภาพหายที่ buffer default |
|---|---|---|---|
| veth 2026-11-24 (`exp5`) | 1.042 | 1 | 7/20 (ภาค 3 §6) |
| veth 2026-11-27 (`exp6`, และแถว `none` ของ shaping) | 3.601 (min 1.026) / 3.454 | 4 / 3.10 | 5% = ภาพแรกทุก run |
| `tbf1g` (1 Gbit/s) | 7.633 | 11.92 | 0 |
| 1 GbE คำนวณ (`image_wire_us_1g`) | 7.684 | | |

**คำตอบ:** veth ส่งภาพหนึ่งภาพเร็วกว่าสาย 1 GbE 2–7 เท่า และเร็วต่างกันตามวัน ในวันที่ทุกภาพมาถึงใน ~1 ms ภาพหาย 7/20 ในวันที่ภาพส่วนใหญ่ใช้ ~3.5 ms (เหลือภาพแรกที่ยังเร็ว ~1 ms) มีเพียงภาพแรกที่หาย และเมื่อบังคับให้ทุกภาพใช้ ~7.6 ms ด้วย tbf ไม่มีภาพหายเลยแม้ buffer เป็นค่า default สิ่งที่เป็น [V]: เวลาและจำนวนการสูญหายทุกตัว (จาก pcap และ CSV) สิ่งที่เป็นสมมติฐาน: ว่าความเร็วของการมาถึงเป็นสาเหตุของการสูญหาย (สอดคล้องกับกลไกใน[ภาค 2 §5.3](02_wire_format_and_kernel.md#53-so_rcvbuf-นับอะไร-และทำไมภาพหายทั้งที่-cpu-ว่าง) แต่ยังไม่ได้ทดลองแบบเปลี่ยนเฉพาะอัตราที่ buffer เดียวกันหลายระดับ) และสาเหตุที่ผู้ส่งช้าลงในวันที่ 27 (governor, kernel) ยังไม่ได้ตรวจ ([ภาค 3 §9.6](03_wire_experiments.md#96-เทียบกับข้อสรุปเดิม)) ข้อควรระวัง: `exp6` ใช้ `bigbuf.xml` คนละ config กับ `exp5` จึงใช้เทียบได้เฉพาะเรื่องจังหวะของวัน ไม่ใช่เรื่อง buffer

### 3.5 RELIABLE บน link ช้า

```bash
python3 - <<'PY'
import csv
for r in csv.DictReader(open('ros2_lyrical/captures/results/shaping_summary.csv')):
    if r['shape'] == 'wifi' and r['qos'] == 'rel':
        n = int(r['n']); drop = int(r['tcA_dropped_sum']); rt = float(r['retrans_mean'])
        print({k: r[k] for k in ('n','delivered_mean','datafrag_wire_mean','retrans_mean','nackfrag_mean','tcA_dropped_sum')})
        print('drops/run', drop / n, 'upper bound needed/retrans %', round(100 * drop / n / rt, 2), 'wire/needed', round(float(r['datafrag_wire_mean']) / 300, 2))
PY
```
```
{'n': '5', 'delivered_mean': '20', 'datafrag_wire_mean': '1520.2', 'retrans_mean': '1220.2', 'nackfrag_mean': '173.2', 'tcA_dropped_sum': '60'}
drops/run 12.0 upper bound needed/retrans % 0.98 wire/needed 5.07
```

**คำตอบ:** qdisc ฝั่งผู้ส่งทิ้งเฉลี่ย 12 frame ต่อ run ซึ่งทำให้ DATA_FRAG เสียได้อย่างมาก 12 ก้อน แต่ writer ส่งซ้ำเฉลี่ย 1 220.2 ก้อน (หลัง NACK_FRAG 173.2 ฉบับ) การส่งซ้ำที่จำเป็นจริงจึงไม่เกินราว **1%** และ traffic ภาพบนสายเป็น 1 520.2 / 300 = **5.07 เท่า** ของที่ต้องใช้ ทั้งที่ได้ครบ 20/20 สอดคล้องกับ[ภาค 3 §11.4](03_wire_experiments.md#114-ผล-v) ข้อ 4 ว่าภาระมาจากจังหวะ heartbeat/NACK เมื่อภาพหนึ่งใช้ ~95 ms มากกว่าจาก loss ข้อจำกัด: ขอบบนนี้นับเฉพาะ `tcA_dropped` (egress ของผู้ส่ง) ไม่รวม frame ที่ qdisc ฝั่งผู้รับอาจทิ้ง (เช่น NACK_FRAG/ACKNACK), ค่า netem "wifi" เป็นค่าที่เลือกเองไม่ใช่ Wi-Fi จริง และ n = 5 ([ภาค 3 §11.5](03_wire_experiments.md#115-ข้อจำกัดของการจำลอง))

---

## ภาค 4

### 4.1 control plane กับ data plane ของ Zenoh

```bash
tsh -r /c/exp3_zenoh.pcap -q -z conv,tcp 2>/dev/null | grep '<->'
tsh -r /c/exp3_zenoh.pcap -Y 'tcp.flags.syn==1' -T fields -e frame.number -e ip.src -e tcp.srcport -e ip.dst -e tcp.dstport -e tcp.flags.str 2>/dev/null
```
```
172.20.0.3:57268           <-> 172.20.0.4:35545                46 7895 bytes      54 7922 bytes     100 15 kB         1.711640000         8.7785
172.20.0.3:37302           <-> 172.20.0.2:7447                 21 1623 bytes      34 7398 bytes      55 9021 bytes     0.677594000         9.8127
4	172.20.0.3	37302	172.20.0.2	7447	··········S·
5	172.20.0.2	7447	172.20.0.3	37302	·······A··S·
60	172.20.0.3	57268	172.20.0.4	35545	··········S·
61	172.20.0.4	35545	172.20.0.3	57268	·······A··S·
```

| connection | ผู้เปิด (SYN) | frame | byte |
|---|---|---|---|
| listener 172.20.0.3:37302 → router 172.20.0.2:7447 | listener (frame 4) | 55 | 9 021 |
| listener 172.20.0.3:57268 → talker 172.20.0.4:35545 | listener (frame 60) | 100 | ~15 kB |

**คำตอบ:** sample 161 B ทั้ง 8 frame ในข้อ 2.4 วิ่งบน connection ตรงระหว่าง talker กับ listener ไม่ผ่าน router connection กับ router ใช้สำหรับ discovery (gossip, liveliness token) จึงเป็น control plane ส่วน connection ตรงเป็น data plane ตาม[ภาค 4 §2.3](04_architectures.md#23-zenoh-router-rmw_zenoh-default-v-ภาค-1-33) และข้อสังเกตเชิงสถาปัตยกรรมใน[ภาค 4 §1](04_architectures.md#1-rmw-เป็น-plugin-middleware-4-ตัวหลัง-c-abi-เดียวกัน) ใน capture นี้ฝ่ายที่เปิด connection ตรงคือ **listener** (SYN จาก 172.20.0.3:57268 ไปยัง port 35545 ของ talker) ซึ่งต่างจากประโยคใน[ภาค 3 §4](03_wire_experiments.md#4-การทดลองที่-3-sample-เดียวกันผ่าน-rmw_zenoh)ที่ว่า talker เปิด TCP ไปหา listener (แจ้งผู้ดูแลเอกสารแล้ว) เชิงเหตุผล: ถ้า router ล่มหลังจาก peer เชื่อมกันแล้ว data plane ที่มีอยู่ไม่ได้พึ่ง router แต่ node ที่เริ่มใหม่จะหากันไม่เจอเพราะ multicast scouting ปิดเป็น default ([ภาค 4 §2.4](04_architectures.md#24-เปรียบเทียบ) ระบุไว้เป็น [K]) การออกแบบจึงต้องถือว่า router เป็นจุดเสียของ discovery

### 4.2 ต้นทุนของ simple discovery

```bash
tsh -r /c/exp1_fastdds_default.pcap -Y 'ip.dst==239.255.0.1 && udp.dstport==7400' -T fields -e frame.number -e frame.time_relative -e ip.src -e frame.len 2>/dev/null
```
```
3	0.676586000	172.20.0.2	610
4	0.776743000	172.20.0.2	610
…   (frame 5, 6, 9, 10 ห่างกัน 0.1 s)
12	2.844703000	172.20.0.3	610
…   (frame 61, 85, 87, 90, 92 ห่างกัน 0.1 s)
99	4.177295000	172.20.0.2	610
104	6.345556000	172.20.0.3	610
109	7.177263000	172.20.0.2	610
115	9.345635000	172.20.0.3	610
120	10.177487000	172.20.0.2	610
124	12.345575000	172.20.0.3	610
167	12.641792000	172.20.0.3	190
169	13.177511000	172.20.0.2	610
170	14.314566000	172.20.0.2	190
```

**คำตอบ:** หลัง 6 ครั้งแรก (ห่างกัน 100 ms) แต่ละ participant ส่ง SPDP `DATA(p)` multicast ทุก **3.000 s** (4.177 → 7.177 → 10.177 → 13.177) ขนาด frame **610 B** (frame 190 B ตอนท้ายคือประกาศเลิกใช้ตอนปิด node) ประมาณการ: เครื่องหนึ่งรับ SPDP multicast N × 610 / 3 B/s คือราว 2.0 kB/s ที่ N = 10 และ 20.3 kB/s ที่ N = 100 (เป็น**ประมาณการ** ไม่รวมสำเนา unicast, SEDP, heartbeat และ `ros_discovery_info`) SPDP เองจึงไม่หนัก สิ่งที่โตเร็วคือ SEDP ที่เป็น O(N²) × จำนวน endpoint ([ภาค 2 §1.5](02_wire_format_and_kernel.md#15-สรุป-traffic-ของ-discovery-ต่อ-participant)) และใน `exp1` ที่มีเพียง 2 participant discovery ก็กิน 96.7% ของ byte RTPS ใน 14 วินาทีแรก (ข้อ 1.3) ควรเปลี่ยนไปใช้ Discovery Server หรือ Zenoh router เมื่อ multicast ใช้ไม่ได้หรือไม่เสถียร (Wi-Fi ที่ส่ง multicast ที่ basic rate, ข้าม subnet, ข้าม NAT) หรือเมื่อจำนวน participant/endpoint ทำให้ช่วงเริ่มระบบนานเกินรับได้ ซึ่งต้องวัด discovery convergence time จริง ([ภาค 4 §2.4](04_architectures.md#24-เปรียบเทียบ))

### 4.3 ออกแบบ pipeline กล้อง

```bash
python3 - <<'PY'
import csv
for r in csv.DictReader(open('ros2_lyrical/captures/results/latency_summary.csv')):
    if r['payload'] == 'image':
        print(r['config'], r['delivered_total'] + '/' + r['expected_total'], r['median_us'], r['p90_us'], r['p99_us'], r['max_us'], r['rcvbuf_errors_total'], r['publish_call_median_us'])
for r in csv.DictReader(open('ros2_lyrical/captures/results/shaping_summary.csv')):
    if r['shape'] == 'tbf1g':
        print('tbf1g', r['qos'], r['arm'], r['delivered_mean'], r['loss_pct'], r['rcvbuferr_med'], r['nackfrag_mean'], r['retrans_mean'], r['burst_ms_med'])
PY
```
```
image_cross_rel 1500/1500 7760.0 7998.4 8276.2 15893.2 130 3890.2
image_same_rel 1500/1500 5350.4 15686.4 15875.1 16851.1 0 1012.2
image_cross_be 1470/1500 7525.5 7756.1 7994.7 9400.2 126 3679.6
image_cross_rel_bigbuf 1500/1500 7706.7 7929.8 8150.2 9401.5 0 3852.0
tbf1g be noxml 20 0 0 0 0 7.633
tbf1g be 4194304 20 0 0 0 0 7.632
tbf1g rel noxml 20 0 0 20 3 7.721
```

ตัวอย่างคำตอบ (หน่วย µs ในผลข้างบน)

| ขา | ทางเลือก | ตัวเลขที่อ้าง | ความเสี่ยง |
|---|---|---|---|
| (ก) ในเครื่องเดียวกัน | ถ้า node อยู่ใน process เดียวกันได้ ใช้ composition + intra-process (0 copy, [ภาค 4 §4](04_architectures.md#4-data-path-ภายในเครื่องเดียวกัน)) ถ้าต้องข้าม process อย่าถือว่า SHM default ดีกว่าเสมอ | `image_same_rel` median 5.35 ms แต่ p90 15.69 และ p99 15.88 ms (bimodal) เทียบกับ UDP ข้าม container p99 8.28 ms; ฝั่งดีคือ `publish()` 1.01 เทียบ 3.89 ms | โหมด ~15 ms ของ SHM ยังไม่รู้สาเหตุ ([ภาค 3 §10.5](03_wire_experiments.md#105-การตีความ-จำกัดเฉพาะที่ข้อมูลรองรับ) ข้อ 5); ถ้า deadline ของงานต่ำกว่า ~16 ms ต้องวัดทางเลือกอื่น (loaned + data-sharing, `rosidl::Buffer`, UDPv4 ล้วน) ก่อนเลือก |
| (ข) ข้ามเครื่อง 1 GbE | BEST_EFFORT (ข้อมูลเซนเซอร์ ภาพใหม่มาแทนภาพเก่า) + `listenSocketBufferSize` ≥ 524 288 ที่ผู้รับเป็นค่าเผื่อ | `tbf1g` BE ได้ 20/20, `RcvbufErrors` 0 แม้ buffer default; บน veth ค่า default เสียภาพแรก (`image_cross_be` 1 470/1 500) และ buffer ใหญ่ทำให้ `RcvbufErrors` 130 → 0 และ max 15.89 → 9.40 ms; RELIABLE ที่ 1 Gbit/s มี NACK_FRAG 20 ฉบับและส่งซ้ำ 3 ก้อนต่อ run โดยไม่มีอะไรหาย | ภาพหนึ่งภาพใช้สาย 7.68 ms ที่ 10 Hz คือราว 7.7% ของ link; ที่ 30 fps เป็น 230 Mb/s (ภาค 2 §2.4); buffer default ยังเสี่ยงเมื่อ thread รับถูกหน่วง > ~0.5 ms |

สิ่งที่ต้องวัดเพิ่มก่อนใช้จริง: (1) ทำซ้ำบน NIC จริงสองเครื่องตาม protocol ใน[ภาค 3 §12.2](03_wire_experiments.md#122-protocol-สำหรับ-2-เครื่องจริง-ยังไม่ได้รัน) พร้อมตัวนับ `ethtool -S` (2) วัด `image_same` ด้วย `FASTDDS_BUILTIN_TRANSPORTS=UDPv4` และทางเลือก zero-copy เพื่อแยกสาเหตุของโหมด ~15 ms (3) วัดด้วย node C++ (rclcpp) และหลาย subscriber เพราะผลทั้งหมดในไฟล์นี้มาจาก rclpy และ subscriber ตัวเดียว
