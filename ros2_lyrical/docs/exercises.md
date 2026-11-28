# แบบฝึกหัด: ROS 2 Lyrical Network Stack

> ใช้ประกอบ[ภาค 1](01_network_stack_deep_dive.md)–[ภาค 4](04_architectures.md) · เฉลยอยู่ใน [answers.md](answers.md) · คำศัพท์ใน [glossary.md](glossary.md) · สรุปคำสั่งและตัวเลขใน [cheatsheet.md](cheatsheet.md)

ทุกข้อตอบได้จากไฟล์ใน repo นี้เท่านั้น ไม่ต้องรันการทดลองใหม่ ได้แก่ pcap ใน [`captures/`](../captures/), CSV ใน [`captures/results/`](../captures/results/) และสคริปต์ใน [`captures/scripts/`](../captures/scripts/) กับ [`tools/`](../tools/) แต่ละภาคเรียงจากง่ายไปยาก (ระดับ: ง่าย / กลาง / ยาก)

## การเตรียมเครื่อง

รันทุกคำสั่งจาก root ของ repo (โฟลเดอร์ที่มี `ros2_lyrical/`) ตั้ง shell function สองตัวนี้ไว้ก่อน

```bash
# ถอด RTPS ด้วย Python standard library (อ่าน .pcap และ .pcap.gz ได้โดยตรง)
pk()  { python3 ros2_lyrical/tools/rtps_peek.py "$@"; }
# tshark ใน image ของภาค 3 แบบไม่มี network (อ่าน .pcap.gz ได้โดยตรง; stderr มีคำเตือนเรื่อง root ให้ทิ้งด้วย 2>/dev/null)
tsh() { docker run --rm --network none -v "$PWD/ros2_lyrical/captures:/c:ro" lyrical-wire:exp tshark "$@"; }
```

ถ้ายังไม่มี image `lyrical-wire:exp` ให้ build ตาม[ภาค 3 §8](03_wire_experiments.md#8-วิธีทำซ้ำ) หรือใช้ Wireshark บนเครื่องตัวเองแทน (ต้อง `gunzip` ไฟล์ `.gz` ก่อน) ข้อที่ใช้ `pk` อย่างเดียวไม่ต้องมี Docker

| pcap | การทดลอง (ภาค 3) |
|---|---|
| `exp1_fastdds_default.pcap` | 1: `demo_nodes_cpp` talker → listener ข้าม container |
| `exp2_image_reliable.pcap.gz` | 2: ภาพ 640×480 rgb8 RELIABLE 5 ภาพ |
| `exp3_zenoh.pcap` | 3: talker/listener ผ่าน `rmw_zenoh_cpp` + router |
| `exp4_samehost_shm.pcap` | 4: talker + listener ใน container เดียวกัน (`tcpdump -i any`) |
| `exp5_image_besteffort.pcap.gz` | 5: ภาพ BEST_EFFORT 20 ภาพ, buffer ค่าเริ่มต้น (2026-11-24) |
| `exp6_image_besteffort_bigbuf.pcap.gz` | 6: เหมือนข้อ 5 แต่ใช้ `bigbuf.xml` (2026-11-27) |

---

## ภาค 1

### 1.1 คำนวณ port ของ RTPS แล้วหาในสาย (ง่าย)

- **เป้าหมาย:** ใช้สูตร port ใน[ภาค 1 §3.1](01_network_stack_deep_dive.md#31-rmw_fastrtps_cpp--fast-dds-36x-default-v-เวอร์ชัน--k-รายละเอียด-protocol) คำนวณ port ของ domain 0 สำหรับ participant id 0 และ 1 (SPDP multicast, metatraffic unicast, user multicast, user unicast) แล้วตรวจว่า port ใดปรากฏจริงใน `exp1` และ `exp4`
- **ไฟล์:** `exp1_fastdds_default.pcap`, `exp4_samehost_shm.pcap`
- **คำใบ้:** `tsh -r /c/<file> -T fields -e ip.src -e ip.dst -e udp.dstport 2>/dev/null | sort | uniq -c` ใน `exp1` แต่ละ container มี participant ตัวเดียว ส่วนใน `exp4` มีสอง participant บน network namespace เดียวกัน
- **รูปแบบคำตอบ:** ตาราง port ที่คำนวณได้ 8 ค่า, รายการ port ที่เห็นในแต่ละไฟล์ และคำอธิบายหนึ่งย่อหน้าว่าทำไม `exp4` มี 7412 แต่ `exp1` ไม่มี และ port ใดที่ไม่ได้มาจากสูตร

### 1.2 แยกชั้นของ frame 198 B (ง่าย)

- **เป้าหมาย:** แยก frame 95 ของ `exp1` เป็น Ethernet / IPv4 / UDP / RTPS แล้วยืนยัน IPv4 total length, UDP length และขนาด RTPS message จากค่าใน header เอง (ไม่ใช่นับจากเอกสาร) จากนั้นคำนวณ byte-time บนสาย 1 GbE
- **ไฟล์:** `exp1_fastdds_default.pcap`
- **คำใบ้:** `pk frame ros2_lyrical/captures/exp1_fastdds_default.pcap 95` IPv4 total length อยู่ที่ offset 0x10–0x11, UDP length ที่ 0x26–0x27 (big-endian ทั้งคู่)
- **รูปแบบคำตอบ:** 14 + 20 + 8 + N = 198 พร้อมค่า hex ของ length ทั้งสอง field และจำนวน byte-time (รวม FCS, preamble, IFG)

### 1.3 Discovery กับข้อมูลจริง: ใครกิน bandwidth (กลาง)

- **เป้าหมาย:** นับจำนวน sample ของ `/chatter` ใน `exp1` และสัดส่วน byte ของมันเทียบกับ RTPS ทั้งไฟล์
- **ไฟล์:** `exp1_fastdds_default.pcap`
- **คำใบ้:** `tsh -r /c/exp1_fastdds_default.pcap -q -z io,phs` ให้ byte รวมของ RTPS ระวัง: filter `frame.len==198` ได้ 10 frame แต่ไม่ใช่ chatter ทั้งหมด ให้แยกด้วย writerId ของ chatter (`pk sms ... DATA | grep 'writer 00.00.13.03'`) แล้วดูว่า frame ที่เกินมาคือ writer ตัวใด
- **รูปแบบคำตอบ:** จำนวน sample, byte, % ของ RTPS และหนึ่งประโยคว่า frame 198 B ที่ไม่ใช่ chatter มาจากไหน

### 1.4 ทำไม `exp4` เห็น discovery แต่ไม่เห็นข้อมูล (กลาง)

- **เป้าหมาย:** พิสูจน์จาก pcap ว่าใน `exp4` ไม่มี DATA/DATA_FRAG จาก user writer เลย แล้วอธิบายว่าข้อมูลไปทางไหนและทำไม discovery ยังวิ่งบน UDP
- **ไฟล์:** `exp4_samehost_shm.pcap` (link type 276, Linux cooked v2)
- **คำใบ้:** `pk sms ros2_lyrical/captures/exp4_samehost_shm.pcap DATA DATA_FRAG | grep -o 'flags 0x.. .*writer [0-9a-f.]*' | awk '{print $1,$2,$NF}' | sort | uniq -c` ไบต์สุดท้ายของ entityId `0xc2` = builtin writer, `0x03` = user writer ไม่มี key
- **รูปแบบคำตอบ:** ตารางนับ submessage ตาม writer, ข้อสรุปว่ามี user writer หรือไม่ และหนึ่งย่อหน้าเชื่อมกับ[ภาค 1 §3.1](01_network_stack_deep_dive.md#31-rmw_fastrtps_cpp--fast-dds-36x-default-v-เวอร์ชัน--k-รายละเอียด-protocol) (SHM default) และ[ภาค 3 §5](03_wire_experiments.md#5-การทดลองที่-4-เครื่องเดียวกัน-fast-dds-shm)

---

## ภาค 2

### 2.1 บัญชี byte ของ RTPS message 156 B (ง่าย)

- **เป้าหมาย:** แยก RTPS message ของ frame 95 (`exp1`) เป็น header และ submessage ทุกตัว ตรวจว่า `octetsToNextHeader` ของแต่ละตัวบวกกันได้ 156 แล้วถอด CDR payload 24 B ทีละ byte
- **ไฟล์:** `exp1_fastdds_default.pcap`
- **คำใบ้:** `pk frame ...exp1_fastdds_default.pcap 95` แสดง offset `[20] [36] [48] [96]` ของแต่ละ submessage ขนาดของ submessage = 4 + `len`
- **รูปแบบคำตอบ:** ตาราง (ชื่อ, offset, ขนาด) ที่รวมได้ 156 และการแยก payload เป็น encapsulation / length / string / padding พร้อมเหตุผลของ padding

### 2.2 นับ DATA_FRAG และ IP fragment ของหนึ่งภาพ (กลาง)

- **เป้าหมาย:** สำหรับภาพ SN 3 ใน `exp2` หา `fragmentSize`, `sampleSize`, จำนวน DATA_FRAG และขนาดข้อมูลของ fragment สุดท้าย แล้วนับจำนวน IP fragment ต่อ datagram ทั้งไฟล์ เทียบกับการคำนวณใน[ภาค 2 §2.4](02_wire_format_and_kernel.md#24-ตัวอย่างคำนวณ-sensor_msgsimage-640480-rgb8)
- **ไฟล์:** `exp2_image_reliable.pcap.gz`
- **คำใบ้:** `pk sms <file> DATA_FRAG | grep 'SN 3 '` และ `pk fragcount <file>` ขนาดข้อมูลของ fragment = `len` − 32 (ส่วนคงที่ของ DATA_FRAG หลัง header 4 B)
- **รูปแบบคำตอบ:** สมการ 14 × fragmentSize + ขนาดสุดท้าย = sampleSize, จำนวน 45/5 IP fragment พร้อมการคำนวณ ceil(UDP datagram / 1480) และคำอธิบายว่าทำไมขนาด fragment สุดท้ายต่างจากตารางใน §2.4 อยู่ 4 B

### 2.3 ไล่การซ่อม fragment ด้วย NACK_FRAG (กลาง)

- **เป้าหมาย:** ใน `exp2` หา NACK_FRAG ฉบับแรก ถอด bitmap ว่าขอ fragment ไหน หา DATA_FRAG ที่ส่งซ้ำตามมา แล้ววัดเวลา (1) จาก DATA_FRAG สุดท้ายของ SN 1 ถึง NACK_FRAG และ (2) จาก NACK_FRAG ถึง DATA_FRAG ซ้ำก้อนแรก เทียบกับค่า default ใน[ภาค 2 §2.3](02_wire_format_and_kernel.md#23-ค่าเวลา-default-ของ-fast-dds-36x)
- **ไฟล์:** `exp2_image_reliable.pcap.gz`
- **คำใบ้:** `pk sms <file> NACK_FRAG` แล้ว `pk sms <file> DATA_FRAG HEARTBEAT ACKNACK NACK_FRAG | awk '/^frame/{f=$2} f>=744 && f<=900'` เวลาอยู่ในคอลัมน์ที่ 3 ของบรรทัด `frame`
- **รูปแบบคำตอบ:** หมายเลข frame ของ NACK_FRAG และ DATA_FRAG ซ้ำ, fragment ที่ขอ, เวลา 2 ช่วงเป็น ms และข้อสรุปว่าสอดคล้องกับ `heartbeat_response_delay` / `nack_response_delay` หรือไม่ (บอกด้วยว่าทำไมข้อสรุปนี้ยังไม่ใช่การพิสูจน์)

### 2.4 ถอด Zenoh sample 161 B (กลาง)

- **เป้าหมาย:** ใน `exp3` หา frame ที่บรรจุ `"Hello World: 1"` แยกเป็น Ethernet / IPv4 / TCP / Zenoh ถอด length prefix และหา attachment 33 B กับ CDR payload ตาม[ภาค 2 §4.2](02_wire_format_and_kernel.md#42-framing-บน-tcp) และ[ภาค 3 §4](03_wire_experiments.md#4-การทดลองที่-3-sample-เดียวกันผ่าน-rmw_zenoh)
- **ไฟล์:** `exp3_zenoh.pcap`
- **คำใบ้:** `tsh -r /c/exp3_zenoh.pcap -Y 'frame.len==161' -T fields -e frame.number -e ip.src -e tcp.srcport -e ip.dst -e tcp.dstport -e tcp.len` แล้ว `tsh -r /c/exp3_zenoh.pcap -Y 'frame.number==142' -x` ความยาว GID 16 B นำหน้าด้วย byte `0x10`
- **รูปแบบคำตอบ:** 14 + 20 + 32 + 95, ค่า prefix เป็น hex และฐานสิบ, offset ของ attachment (sequence 8 + timestamp 8 + GID len 1 + GID 16) และ payload 23 B พร้อมคำอธิบายว่าทำไม RTPS pad เป็น 24 B แต่ Zenoh ไม่ pad

### 2.5 `SO_RCVBUF` กับ `truesize`: buffer รับ datagram ได้กี่ก้อน (ยาก)

- **เป้าหมาย:** จาก `rcvbuf_sweep_summary.csv` ตรวจกฎ `SO_RCVBUF` = 2 × min(ค่าที่ขอ, `rmem_max`) ทุกแขน แล้วใช้ค่า `truesize` ต่อ datagram 65 KB สองค่าใน[ภาค 2 §5.3](02_wire_format_and_kernel.md#53-so_rcvbuf-นับอะไร-และทำไมภาพหายทั้งที่-cpu-ว่าง) (97 920 และ 132 480 B ซึ่งเป็นประมาณการ) คำนวณจำนวน datagram ที่ buffer ของแต่ละแขนรับได้ แล้วเทียบกับคอลัมน์ `loss_pct`
- **ไฟล์:** `captures/results/rcvbuf_sweep_summary.csv`, `rcvbuf_sweep_env.txt`
- **คำใบ้:** อ่านด้วย `python3 -c 'import csv ...'` เลือกคอลัมน์ `arm, req_bytes, rb_eff_B, loss_pct, rcvbuferr_med` และหา `rmem_max` ใน env
- **รูปแบบคำตอบ:** ตารางแขน → `rb_eff_B` → จำนวน datagram (ช่วงตาม truesize สองค่า) → loss, ข้อสรุปเรื่องจุดที่การสูญหายหายไป และข้อจำกัดอย่างน้อย 2 ข้อ (ตัวเลข truesize ยังไม่ได้วัด, ภาพหนึ่งภาพมี 15 datagram ไม่จำเป็นต้องอยู่ใน buffer พร้อมกัน ฯลฯ)

---

## ภาค 3

### 3.1 capture เห็นครบ แต่ภาพหาย (ง่าย)

- **เป้าหมาย:** นับ DATA_FRAG และจำนวนภาพที่ fragment ครบใน `exp5` และ `exp6` แล้วอธิบายว่าทำไม capture เห็นครบทั้งสองไฟล์ ทั้งที่[ภาค 3 §6](03_wire_experiments.md#6-การทดลองที่-56-receive-buffer-ตัดสินว่าภาพจะรอดหรือไม่)รายงานว่า `exp5` ได้รับเพียง 13/20 ภาพ ภาพหายที่ชั้นไหน และตัวนับใดยืนยัน
- **ไฟล์:** `exp5_image_besteffort.pcap.gz`, `exp6_image_besteffort_bigbuf.pcap.gz`
- **คำใบ้:** `python3 ros2_lyrical/captures/scripts/sweep_pcap_stats.py <file>` (ดู `datafrag_total`, `sn_complete`) หรือ `pk sms <file> DATA_FRAG | grep -o 'SN [0-9]*' | sort | uniq -c` จุดที่ tcpdump เห็น packet อยู่ในตาราง RX ของ[ภาค 1 §5.5](01_network_stack_deep_dive.md#55-เส้นทางใน-linux-kernel-ทีละฟังก์ชัน-tx-และ-rx)
- **รูปแบบคำตอบ:** ตัวเลข 2 ไฟล์, ชื่อฟังก์ชันใน kernel ที่ทิ้ง, ชื่อตัวนับ และหนึ่งประโยคว่าทำไม `exp6` ไม่ใช่การทดลองที่เปลี่ยนตัวแปรเดียว ([ภาค 3 §9.1](03_wire_experiments.md#91-ตัวแปรกวนในการทดลองที่-6))

### 3.2 อ่านผล rcvbuf sweep แบบมีขอบเขต (กลาง)

- **เป้าหมาย:** เทียบแขน `noxml`, `sndonly` และ `524288` ใน `rcvbuf_sweep_summary.csv` แล้วเขียนข้อสรุปหนึ่งย่อหน้าที่บอกทั้งสิ่งที่ข้อมูลรองรับและสิ่งที่ไม่รองรับ
- **ไฟล์:** `captures/results/rcvbuf_sweep_summary.csv`
- **คำใบ้:** คอลัมน์ `n, rb_eff_B, tb_A_max, delivered_mean, loss_pct, rcvbuferr_med, datafrag_wire_mean, sn_complete_min` ข้อจำกัดอยู่ใน[ภาค 3 §12.1](03_wire_experiments.md#121-ข้อจำกัดของผลในภาคนี้)
- **รูปแบบคำตอบ:** ตาราง 3 แถว, ข้อสรุป 2–3 ประโยค และข้อจำกัดอย่างน้อย 3 ข้อ

### 3.3 latency: SHM ช่วยข้อความเล็กแค่ไหน (กลาง)

- **เป้าหมาย:** จาก `latency_summary.csv` เทียบ `small_cross`, `small_same_udp` และ `small_same` ที่ median และ p99 พร้อม 95% CI แล้วตอบว่า (ก) ความต่างจาก "อยู่ container เดียวกัน" กับจาก "SHM" แยกได้หรือไม่ (ข) ส่วนใหญ่ของ latency อยู่ที่ใด
- **ไฟล์:** `captures/results/latency_summary.csv`
- **คำใบ้:** คอลัมน์ `median_us, median_ci_lo, median_ci_hi, p99_us, p99_ci_lo, p99_ci_hi, publish_call_median_us` CI สองช่วงที่ไม่ซ้อนกันคือหลักฐานว่าต่างกัน
- **รูปแบบคำตอบ:** ตาราง 3 config, ผลต่างเป็น µs, ข้อสรุปพร้อมข้อจำกัดจาก[ภาค 3 §10.6](03_wire_experiments.md#106-ข้อจำกัด)

### 3.4 จังหวะการมาถึงของภาพ: veth สองวันกับ 1 Gbit/s (ยาก)

- **เป้าหมาย:** วัดระยะเวลาที่ภาพหนึ่งภาพใช้บนสาย (IP fragment แรก → สุดท้าย) ใน `exp5` (2026-11-24) และ `exp6` (2026-11-27) แล้วเทียบกับแถว `tbf1g` ใน `shaping_summary.csv` และค่าคำนวณ 7.684 ms ของ 1 GbE ใช้ผลนี้อธิบายว่าทำไมการสูญหายที่ buffer ค่าเริ่มต้นเปลี่ยนไปตามวันและหายไปเมื่อจำกัดอัตรา
- **ไฟล์:** `exp5_image_besteffort.pcap.gz`, `exp6_image_besteffort_bigbuf.pcap.gz`, `captures/results/shaping_summary.csv`
- **คำใบ้:** `sweep_pcap_stats.py` ให้ `burst_ms_med`, `burst_ms_min`, `gap_us_med`, `image_wire_us_1g` เชื่อมกับกลไกใน[ภาค 2 §5.3](02_wire_format_and_kernel.md#53-so_rcvbuf-นับอะไร-และทำไมภาพหายทั้งที่-cpu-ว่าง) และ[ภาค 3 §9.6](03_wire_experiments.md#96-เทียบกับข้อสรุปเดิม)
- **รูปแบบคำตอบ:** ตาราง burst (ms) ของ 3 เงื่อนไข, ข้อสรุป 1 ย่อหน้า และระบุว่าส่วนไหนเป็น [V] ส่วนไหนเป็นสมมติฐาน

### 3.5 RELIABLE บน link ช้า: การส่งซ้ำที่จำเป็นจริง (ยาก)

- **เป้าหมาย:** จากแถว `wifi,rel,noxml` ใน `shaping_summary.csv` คำนวณขอบบนของสัดส่วน DATA_FRAG ที่ส่งซ้ำเพื่อซ่อมสิ่งที่หายจริง (ใช้จำนวน frame ที่ qdisc ทิ้ง) และ overhead ของ traffic ภาพเทียบกับ 300 DATA_FRAG ที่จำเป็น
- **ไฟล์:** `captures/results/shaping_summary.csv`
- **คำใบ้:** คอลัมน์ `n, datafrag_wire_mean, retrans_mean, nackfrag_mean, tcA_dropped_sum` frame ที่หายหนึ่ง frame ทำให้ DATA_FRAG เสียได้อย่างมากหนึ่งก้อน
- **รูปแบบคำตอบ:** ตัวเลข 3–4 ค่า, ขอบบนเป็น %, ข้อสรุปพร้อมข้อจำกัดของการจำลอง "wifi" ([ภาค 3 §11.5](03_wire_experiments.md#115-ข้อจำกัดของการจำลอง))

---

## ภาค 4

### 4.1 control plane กับ data plane ของ Zenoh (กลาง)

- **เป้าหมาย:** ใน `exp3` แยก TCP connection ทั้งหมด บอกว่าแต่ละ connection เป็นของใคร (router :7447 หรือ peer) ใครเป็นฝ่ายเปิด (SYN) และ byte ที่วิ่งในแต่ละ connection แล้วโยงกับ[ภาค 4 §2.3](04_architectures.md#23-zenoh-router-rmw_zenoh-default-v-ภาค-1-33)
- **ไฟล์:** `exp3_zenoh.pcap` (capture ที่ listener 172.20.0.3; router .2, talker .4)
- **คำใบ้:** `tsh -r /c/exp3_zenoh.pcap -q -z conv,tcp` และ `tsh -r /c/exp3_zenoh.pcap -Y 'tcp.flags.syn==1' -T fields -e frame.number -e ip.src -e tcp.srcport -e ip.dst -e tcp.dstport -e tcp.flags.str`
- **รูปแบบคำตอบ:** ตาราง 2 connection (ปลายทั้งสอง, ผู้เปิด, frame, byte), ข้อสรุปว่า sample ของ chatter ผ่าน router หรือไม่ และผลต่อการออกแบบเมื่อ router ล่ม (ตอบเชิงเหตุผล ไม่ต้องอ้างผลวัด)

### 4.2 ต้นทุนของ simple discovery (กลาง)

- **เป้าหมาย:** วัดคาบของ SPDP `DATA(p)` และขนาด frame จาก `exp1` แล้วประมาณการ byte/s ของ SPDP ที่เครื่องหนึ่งเครื่องต้องรับเมื่อมี N = 10 และ 100 participant ใน domain เดียวกัน ใช้ผลประกอบการเลือก discovery ตาม[ภาค 4 §2.4](04_architectures.md#24-เปรียบเทียบ)
- **ไฟล์:** `exp1_fastdds_default.pcap`
- **คำใบ้:** `tsh -r /c/exp1_fastdds_default.pcap -Y 'ip.dst==239.255.0.1 && udp.dstport==7400' -T fields -e frame.number -e frame.time_relative -e ip.src -e frame.len` (นับเฉพาะ multicast และช่วงหลัง 6 ครั้งแรก)
- **รูปแบบคำตอบ:** คาบ (s), ขนาด (B), สูตรและผลประมาณการ (ระบุว่าเป็นประมาณการ ไม่รวม SEDP และ unicast) และข้อเสนอว่าเมื่อไรควรเปลี่ยนไปใช้ Discovery Server หรือ Zenoh router

### 4.3 ออกแบบ pipeline กล้องจากตัวเลขที่วัดได้ (ยาก)

- **เป้าหมาย:** หุ่นยนต์มีกล้อง 640×480 rgb8 ที่ 10 Hz ต้องส่งภาพไปยัง (ก) node ประมวลผลในเครื่องเดียวกัน และ (ข) คอมพิวเตอร์อีกเครื่องผ่าน 1 GbE เลือกเส้นทาง/QoS/การตั้งค่า buffer สำหรับแต่ละขา โดยอ้างตัวเลขจาก `latency_summary.csv` (`image_*`) และ `shaping_summary.csv` อย่างน้อยขาละ 2 ตัวเลข แล้วบอกว่าต้องวัดอะไรเพิ่มก่อนนำไปใช้จริง
- **ไฟล์:** `captures/results/latency_summary.csv`, `captures/results/shaping_summary.csv`, [ภาค 4 §4](04_architectures.md#4-data-path-ภายในเครื่องเดียวกัน) และ [§8](04_architectures.md#8-ตารางเลือกสถาปัตยกรรม)
- **คำใบ้:** ดู median กับ p90/p99 ของ `image_same_rel` เทียบ `image_cross_rel` (และ[ภาค 3 §10.5](03_wire_experiments.md#105-การตีความ-จำกัดเฉพาะที่ข้อมูลรองรับ) ข้อ 5) และแถว `tbf1g` ทั้ง BE/REL
- **รูปแบบคำตอบ:** ตารางการตัดสินใจ 2 แถว (ขา, ทางเลือก, ตัวเลขที่อ้าง, ความเสี่ยง) และรายการสิ่งที่ต้องวัดเพิ่ม 3 ข้อ
