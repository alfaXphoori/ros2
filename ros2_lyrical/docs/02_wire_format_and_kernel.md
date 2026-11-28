# ROS 2 Lyrical Luth: Network Stack เชิงลึก ภาค 2 (wire format, reliability, Fast DDS internals, Zenoh framing, kernel accounting, latency budget)

> **ลำดับการอ่าน:** ขั้นที่ 7–8 จาก 8 ([ดูทั้งหมด](../README.md#ลำดับการอ่าน)) · ก่อนหน้า: [ภาค 3](03_wire_experiments.md) · จบที่หัวข้อวิจัย [§7](#7-ทิศทางวิจัยที่ตามมาโดยตรงจากหัวข้อ-16)

> เอกสารต่อยอดจาก `01_network_stack_deep_dive.md` (ต่อไปเรียกว่า "ภาค 1") ไม่ทำซ้ำเนื้อหาเดิม
> ร่างโดย Claude Fable 5.2 แล้วตรวจทานและแก้ไขโดย Claude Opus 5.5 · สถานะ ณ 2026-11-24 · เครื่องที่ใช้ตรวจ: Ubuntu 26.04.1, Linux 7.0.0-43-generic, NIC `r8169` (RTL8168h), CPU Intel i3-12100

> **อัปเดต:** หลายข้อในเอกสารนี้ได้รับการยืนยันด้วย packet capture จริงแล้วใน[ภาค 3](03_wire_experiments.md) ได้แก่ frame 198 B, INFO_DST 16 B, statistics 60 B, fragmentSize 65 324 B, 15 DATA_FRAG, 45 IP fragment, Zenoh length prefix และ attachment 33 B ส่วน sampleSize จริงคือ 921 648 B (เอกสารนี้คำนวณได้ 921 652 B เพราะสมมติ `frame_id = "camera"` แต่สคริปต์ทดลองใช้ `"f0"`… ดูหัวข้อ 2.4)

**วัตถุประสงค์การเรียนรู้** อ่านภาคนี้จบแล้วควรทำได้ดังนี้
1. ถอด SPDP/SEDP ParameterList และบอกได้ว่า participant เปิดเผยข้อมูลอะไรบนสาย (§1)
2. ถอด DATA_FRAG, HEARTBEAT, ACKNACK, NACK_FRAG ทีละ field และอธิบายลำดับการซ่อม fragment ที่หายพร้อมค่าเวลา default (§2.1–§2.3, §2.5)
3. คำนวณ `fragmentSize`, จำนวน DATA_FRAG, IP fragment และเวลาบนสายของภาพ 640×480 rgb8 (§2.4)
4. ถอด Zenoh บน TCP: length prefix, FRAME/PUSH/PUT และ attachment ของ `rmw_zenoh_cpp` (§4)
5. คำนวณ `SO_RCVBUF` ที่ kernel ใช้จริงและจำนวน datagram 65 KB ที่ buffer รับได้ตาม `truesize` โดยแยกผลวัดออกจากประมาณการ (§3.3, §5.3, §6)
6. วางแผนวัด latency รายช่วงข้ามชั้น พร้อมตัวแปร เครื่องมือ และแนวปฏิบัติของการทดลอง แล้วเลือกหัวข้อวิจัยจาก R1–R13 (§6.4–§6.6, §7)

**พื้นฐานที่ควรมี** ภาค 1 §3–§5 และภาค 3 §2, §4.1–§4.2 และ §5.1 (การทดลองที่ 1–6 ตามลำดับการอ่านใน README) · bitmap/bit flag และ little-endian · อ่าน C struct ได้ · ใช้ Wireshark หรือ tshark เบื้องต้น

แบบฝึกหัด: [exercises.md ภาค 2](exercises.md#ภาค-2) · คำศัพท์: [glossary.md](glossary.md) · สรุปย่อหนึ่งหน้า: [cheatsheet.md](cheatsheet.md)

## 0. วิธีอ่านเอกสารนี้

**ระดับความเชื่อมั่น**

- **[V: แหล่ง]** ตรวจกับ source code หรือเครื่องจริงแล้ว ระบุแหล่งไว้ในวงเล็บ รายการ commit อยู่ในหัวข้อ 9
- **[K]** ความรู้มาตรฐานที่ยังไม่ได้ตรวจกับ source ของเวอร์ชันนี้
- **ประมาณการ** ตัวเลขที่คำนวณหรือประเมินเอง แสดงเหตุผลกำกับทุกครั้ง ไม่ใช่ผลวัด

**ข้อจำกัดสำคัญของการตรวจรอบนี้**

1. เครื่องที่ใช้ตรวจ**ไม่มี ROS 2 ติดตั้ง** (`/opt/ros` ไม่มี) ตอนเขียนเอกสารนี้จึงยังไม่มี packet capture และทุกข้อที่ติด [V] ในส่วน wire format หมายถึง "ตรงกับโค้ดที่ serialize/parse field นั้น" ไม่ใช่ "เห็นบนสายแล้ว" ภายหลังได้ capture จริงจาก Docker (`ros:lyrical-ros-base` + package จาก apt) แล้วใน[ภาค 3](03_wire_experiments.md) ข้อที่ยืนยันด้วย capture แล้วจะระบุเป็น [V: capture ภาค 3 …] ส่วนข้อที่ไม่ได้ระบุยังเป็นผลจากการอ่านโค้ดเท่านั้น
2. OMG DDSI-RTPS 2.5 PDF ไม่ได้เปิดอ่านโดยตรง ค่าคงที่ของ protocol ตรวจไขว้ 2 แหล่งแทน คือ Wireshark `packet-rtps.c` และ header ของ Fast DDS 3.6.x
3. พฤติกรรมของ Fast DDS ขึ้นกับ option ตอน build สองตัว (`SECURITY`, `FASTDDS_STATISTICS`) ซึ่งเปลี่ยน byte บนสายจริง ดูหัวข้อ 3.7 เอกสารนี้ระบุทั้งสองกรณีเมื่อผลต่างกัน
4. คำสั่ง `bpftrace`/`perf` ในเอกสารยังไม่ได้รัน (ต้องใช้ root) ตรวจแล้วเฉพาะว่า symbol และ tracepoint ที่อ้างมีอยู่ใน `/proc/kallsyms` ของเครื่องนี้ (ส่วน userspace วัดแล้วด้วย ros2_tracing โดยไม่ใช้ root ดูหัวข้อ 6.5)

---

## 1. Discovery บนสาย ระดับ byte

### 1.1 โครงสร้างร่วม: ParameterList

ข้อมูล discovery ทั้ง SPDP และ SEDP เป็น `DATA` submessage (id `0x15`) ที่ payload ไม่ใช่ CDR ธรรมดา แต่เป็น **ParameterList**

```
serializedPayload:
  00 03 00 00              encapsulation = PL_CDR_LE (0x0003), options = 0
  repeat:
    u16 parameterId (LE)   u16 length (LE, หาร 4 ลงตัว)   value[length]
  01 00 00 00              PID_SENTINEL (0x0001), length 0
```

- encapsulation id: `CDR_BE 0x0000`, `CDR_LE 0x0001`, `PL_CDR_BE 0x0002`, `PL_CDR_LE 0x0003`, `CDR2_LE 0x0007`, `D_CDR2_LE 0x0009`, `PL_CDR2_LE 0x000b` [V: Wireshark `packet-rtps.c` `ENCAPSULATION_*`]
- Fast DDS เขียน header นี้ด้วย `ParameterList::writeEncapsulationToCDRMsg` คือ octet 0, octet `PL_CDR_LE - msg_endian`, u16 0 [V: Fast DDS `src/cpp/fastdds/core/policy/ParameterList.cpp`]
- ปิดท้ายด้วย `PID_SENTINEL` เสมอ [V: `ParticipantProxyData.cpp` เรียก `add_parameter_sentinel` เป็นบรรทัดสุดท้าย]

### 1.2 SPDP `DATA(p)`: ประกาศ participant

**ซองนอก**

| field | ค่า | สถานะ |
|---|---|---|
| ปลายทาง | UDP multicast `239.255.0.1`, port `7400 + 250·domain` | [V: `UDPv4Transport.h` `DEFAULT_METATRAFFIC_MULTICAST_ADDRESS`, `PortParameters.hpp` portBase 7400, domainIDGain 250] |
| writerId | `0x000100c2` (SPDP builtin participant writer) | [V: Fast DDS `EntityId_t.hpp`, Wireshark `ENTITYID_BUILTIN_PARTICIPANT_WRITER`] |
| readerId | `0x000100c7` หรือ `ENTITYID_UNKNOWN` | ค่า `0x000100c7` [V] ส่วนว่า Fast DDS ใส่ค่าใดจริง [K] |
| entity kind byte สุดท้าย | `0xc2` = builtin writer with key, `0xc7` = builtin reader with key | [V: Wireshark `ENTITYKIND_BUILTIN_*`] |
| ความน่าเชื่อถือ | best-effort, ส่งซ้ำตามคาบ | [K: spec] |

**ลำดับ parameter ที่ Fast DDS 3.6.x เขียนจริง** (เรียงตามลำดับในฟังก์ชัน `ParticipantProxyData::write_to_cdr_message`) [V: ลำดับและเงื่อนไขจาก `src/cpp/rtps/builtin/data/ParticipantProxyData.cpp`; PID จาก `ParameterTypes.hpp` ตรวจไขว้กับ Wireshark; ความยาวจาก `PARAMETER_*_LENGTH`]

| # | PID | ค่า | value length | ขนาดบนสาย (รวม header 4 B) | เนื้อหา |
|---|---|---|---|---|---|
| 1 | `PID_PROTOCOL_VERSION` | `0x0015` | 4 | 8 | major, minor, pad 2 |
| 2 | `PID_VENDORID` | `0x0016` | 4 | 8 | `01 0f` = eProsima, pad 2 |
| 3 | `PID_PRODUCT_VERSION` | `0x8000` | 4 | 8 | vendor-specific (bit 15 = 1) |
| 4 | `PID_DOMAIN_ID` | `0x000f` | 4 | 8 | domain id |
| 5 | `PID_EXPECTS_INLINE_QOS` | `0x0043` | 4 | 8 | เขียนเฉพาะเมื่อเป็น true |
| 6 | `PID_PARTICIPANT_GUID` | `0x0050` | 16 | 20 | guidPrefix 12 B + entityId `00 00 01 c1` |
| 7 | `PID_NETWORK_CONFIGURATION_SET` | `0x8007` | 4 | 8 | vendor-specific |
| 8 | `PID_MACHINE_ID` | `0x8003` | แปรผัน | แปรผัน | string, เขียนเมื่อไม่ว่าง |
| 9 | `PID_METATRAFFIC_MULTICAST_LOCATOR` | `0x0033` | 24 | 28 ต่อ locator | kind 4 + port 4 + address 16 |
| 10 | `PID_METATRAFFIC_UNICAST_LOCATOR` | `0x0032` | 24 | 28 ต่อ locator | ปลายทางของ SEDP |
| 11 | `PID_DEFAULT_UNICAST_LOCATOR` | `0x0031` | 24 | 28 ต่อ locator | ปลายทางของ user data |
| 12 | `PID_DEFAULT_MULTICAST_LOCATOR` | `0x0048` | 24 | 28 ต่อ locator | |
| 13 | `PID_PARTICIPANT_LEASE_DURATION` | `0x0002` | 8 | 12 | seconds i32 + fraction u32 |
| 14 | `PID_BUILTIN_ENDPOINT_SET` | `0x0058` | 4 | 8 | bitmask ดูด้านล่าง |
| 15 | `PID_ENTITY_NAME` | `0x0062` | แปรผัน | แปรผัน | ชื่อ participant |
| 16 | `PID_USER_DATA` | `0x002c` | แปรผัน | แปรผัน | ROS 2 ใส่ enclave ที่นี่ |
| 17 | `PID_PROPERTY_LIST` | `0x0059` | แปรผัน | แปรผัน | เขียนเมื่อมี property |
| 18 | `PID_IDENTITY_TOKEN` / `PID_PERMISSIONS_TOKEN` / `PID_PARTICIPANT_SECURITY_INFO` | `0x1001` / `0x1002` / `0x1005` | แปรผัน | แปรผัน | เฉพาะเมื่อเปิด DDS-Security |
| 19 | `PID_WIREPROTOCOL_CONFIG` | `0x8300` | แปรผัน | แปรผัน | เฉพาะเมื่อส่ง optional QoS |
| 20 | `PID_SENTINEL` | `0x0001` | 0 | 4 | |

รายละเอียดที่ควรรู้

- **Locator = 24 B** เสมอ ทั้ง IPv4/IPv6 โดย IPv4 อยู่ 4 byte ท้ายของ address 16 B [V: `CDRMessage::add_locator` เขียน `kind` i32, `port` u32, `address[16]`] เครื่องที่มีหลาย interface จึงเพิ่ม 28 B ต่อ interface ต่อชนิด locator
- **SHM locator**: Fast DDS ใช้ `LOCATOR_KIND_SHM = 16 + FASTDDS_VERSION_MAJOR` = 19 ใน 3.x [V: `static_assert` ใน `SharedMemGlobal.hpp`] ส่วน Wireshark รู้จัก `LOCATOR_KIND_SHMEM = 0x01000000` ซึ่งเป็นของ RTI [V: `packet-rtps.c`] Wireshark จึงไม่แสดง locator SHM ของ Fast DDS ว่าเป็น SHM
- **`PID_BUILTIN_ENDPOINT_SET`** บิตที่เกี่ยวข้อง [V: Fast DDS `BuiltinEndpoints.hpp`]: bit 0/1 participant announcer/detector, bit 2/3 publication announcer/detector, bit 4/5 subscription announcer/detector, bit 10/11 participant message writer/reader (ใช้ทำ liveliness), bit 12–15 TypeLookup service, bit 16–21 และ 26–27 เป็นชุด secure ค่าที่คาดว่าจะเห็นใน simple discovery ที่ไม่มี security คือ `0x00000c3f` หรือมากกว่าถ้ามี TypeLookup [K: ผลรวมบิตยังไม่ได้ยืนยันด้วย capture]
- **enclave ของ ROS 2**: `rmw_fastrtps` เขียน `USER_DATA` เป็นสตริง `"enclave=%s;"` พร้อม NUL ปิดท้าย และตั้งชื่อ participant (`PID_ENTITY_NAME`) เป็นค่า enclave เช่นกัน [V: `rmw_fastrtps_shared_cpp/src/participant.cpp` บรรทัด 287–297] enclave default `/` จะได้ `enclave=/;\0` = 11 B ขนาดบนสายของ parameter นี้ = 4 (header) + 4 (sequence length) + 11 + 1 (pad) = 20 B (คำนวณจากกฎ alignment; ตรงกับ capture: `PID_USER_DATA` length 16 + header 4 = 20 B [V: capture ภาค 3 `exp1_fastdds_default.pcap` frame 3])
- **ROS_AUTOMATIC_DISCOVERY_RANGE** เปลี่ยนเนื้อหา SPDP โดยตรง: `LOCALHOST` และ `OFF` ล้าง `metatrafficMulticastLocatorList` แล้วใส่ unicast locator เปล่าเพื่อกันไม่ให้สร้าง multicast locator default และ `OFF` จำกัด participant ไว้ที่ 1 [V: `participant.cpp` บรรทัด 189–215]

**ขนาดรวมและคาบการส่ง**

- ขนาด: ส่วนคงที่ (รายการ 1–4, 6, 7, 13, 14, 20) = 8+8+8+8+20+8+12+8+4 = 84 B บวก locator 28 B ต่อรายการ บวก string/property ประมาณการก่อนวัดว่า `DATA(p)` ของ node ทั่วไปบนเครื่อง 1 interface อยู่ราว 250–400 B (ประมาณการจากผลรวมข้างต้นบวก machine id และ property list) **ค่าที่วัดได้จริงใหญ่กว่านั้น** [V: capture ภาค 3 `exp1_fastdds_default.pcap` frame 3]: ParameterList (`serializedPayload` รวม encapsulation 4 B) = **452 B**, DATA submessage 476 B, RTPS message (UDP payload) 568 B และ Ethernet frame **610 B** (ตัวเลข 610 B ใน[ภาค 3](03_wire_experiments.md) คือขนาด frame) ส่วนที่เกินประมาณการมาจาก `PID_PROPERTY_LIST` 204 B (`PARTICIPANT_TYPE`, `fastdds.physical_data.host/user/process`), `PID_MACHINE_ID` 44 B และ default unicast locator 2 รายการ (SHM kind 19 + UDPv4) นอกเหนือจาก metatraffic unicast 1 รายการ (ใน capture นี้ไม่มี metatraffic multicast locator ใน `DATA(p)`): 84 + 44 + 3×28 + 12 (`ENTITY_NAME`) + 20 (`USER_DATA`) + 204 + 4 = 452 B
- คาบ: `leaseDuration` = 20 s, `leaseDuration_announcementperiod` = 3 s, initial announcements `count` = 5 ห่างกัน 100 ms [V: `RTPSParticipantAttributes.hpp` บรรทัด 231–277] แต่บนสายจะเห็น **`DATA(p)` 6 ฉบับ** ห่างกัน 100 ms เพราะ `BuiltinProtocols::enable()` เรียก `announceParticipantState(true)` ทันที 1 ครั้งก่อน แล้ว timer จึงส่งอีก 5 ครั้งตาม `count` จากนั้นจึงเปลี่ยนเป็นคาบ 3 s [V: Fast DDS tag `v3.6.2` `BuiltinProtocols.cpp` บรรทัด 157–163, `PDP.cpp` บรรทัด 543–552, 1486–1509] ตรงกับ capture: listener ส่ง SPDP multicast ไป 239.255.0.1:7400 ที่ t = 0, 100, 200, 300, 400, 500 ms (frame 3–6, 9, 10) แล้วฉบับถัดไปที่ 3.5 s [V: capture ภาค 3 `exp1_fastdds_default.pcap`]
- ผลตามมา: participant ที่หายไปเงียบ ๆ (ไฟดับ, สายหลุด) จะถูกตัดออกจาก graph หลังผ่านไปได้ถึง 20 s ตามค่า default

### 1.3 SEDP `DATA(w)` / `DATA(r)`: ประกาศ endpoint

| | publication | subscription | สถานะ |
|---|---|---|---|
| writerId | `0x000003c2` | `0x000004c2` | [V: `EntityId_t.hpp`, Wireshark] |
| readerId | `0x000003c7` | `0x000004c7` | [V] |
| ความน่าเชื่อถือ | reliable + transient-local ผ่าน unicast ไปยัง `METATRAFFIC_UNICAST_LOCATOR` | เหมือนกัน | [K: spec] |

parameter หลักของ `DATA(w)` ตามลำดับใน `WriterProxyData::write_to_cdr_message` [V: `src/cpp/rtps/builtin/data/WriterProxyData.cpp`; PID จาก `ParameterTypes.hpp`]

| PID | ค่า | ตัวอย่างสำหรับ talker บน `/chatter` |
|---|---|---|
| `PID_ENDPOINT_GUID` | `0x005a` | guidPrefix + entityId ลงท้าย `03` (user writer, no key) |
| `PID_NETWORK_CONFIGURATION_SET` | `0x8007` | |
| `PID_UNICAST_LOCATOR` / `PID_MULTICAST_LOCATOR` | `0x002f` / `0x0030` | เฉพาะเมื่อ endpoint มี locator ของตัวเอง |
| `PID_PARTICIPANT_GUID` | `0x0050` | |
| `PID_TOPIC_NAME` | `0x0005` | `"rt/chatter"` |
| `PID_TYPE_NAME` | `0x0007` | `"example_interfaces::msg::dds_::String_"` (demo talker ของ Lyrical ใช้ `example_interfaces` ไม่ใช่ `std_msgs` [V: capture ภาค 3 `exp1_fastdds_default.pcap`]) |
| `PID_KEY_HASH` | `0x0070` | |
| `PID_TYPE_MAX_SIZE_SERIALIZED` | `0x0060` | |
| `PID_PROTOCOL_VERSION`, `PID_VENDORID` | `0x0015`, `0x0016` | |
| `PID_DURABILITY` | `0x001d` | เขียนเมื่อ `should_be_sent` (ค่าจริงบนสายของ PID QoS ในตารางนี้และเงื่อนไขที่ส่ง ดู [§1.6](#16-qos--byte-บนสาย)) |
| `PID_DEADLINE`, `PID_LATENCY_BUDGET`, `PID_LIVELINESS` | `0x0023`, `0x0027`, `0x001b` | เขียนเมื่อไม่ใช่ default |
| `PID_RELIABILITY` | `0x001a` | kind: `BEST_EFFORT = 1`, `RELIABLE = 2` [V: `QosPolicies.hpp`] บน `DATA(w)` เขียน**เฉพาะเมื่อ BEST_EFFORT** (RELIABLE เป็น default ของ writer) ส่วน `DATA(r)` มีทุกตัว [V: capture `exp1_fastdds_default.pcap`: `DATA(w)` 21 ฉบับไม่มี PID นี้, `DATA(r)` 17 ฉบับมีทุกฉบับ; `exp16_qos_mm_rel.pcap` frame 35 = writer BEST_EFFORT ตาม §1.6] |
| `PID_LIFESPAN`, `PID_OWNERSHIP`, `PID_DESTINATION_ORDER`, `PID_PRESENTATION`, `PID_PARTITION` | `0x002b`, `0x001f`, `0x0025`, `0x0021`, `0x0029` | เขียนเมื่อไม่ใช่ default |
| `PID_USER_DATA` | `0x002c` | ROS 2 ใส่ type hash ที่นี่ |
| `PID_DATASHARING` | `0x8006` | เขียนเมื่อเปิด data-sharing |
| `PID_TYPE_INFORMATION` | `0x0075` | XTypes TypeInformation |
| `PID_PROPERTY_LIST` | `0x0059` | |
| `PID_DATA_REPRESENTATION` | `0x0073` | |
| `PID_HISTORY` | `0x0040` | เขียน**เฉพาะเมื่อไม่ใช่ KEEP_LAST depth 1** (default ของ DDS) เช่น `rt/chatter` ของ demo talker = KEEP_LAST 7 [V: capture `exp16_qos_tl_d1.pcap` frame 42: writer KEEP_LAST 1 ไม่มี PID นี้, `tl_d10` = KEEP_LAST 10, `tl_all` = KEEP_ALL depth 10; `exp1_fastdds_default.pcap`: SEDP `DATA` 57 ฉบับ (19 ฉบับเป็น dispose/unregister ไม่มี ParameterList) มี PID นี้ 36 ฉบับ ที่ไม่มีคือ writer ของ `ros_discovery_info` (KEEP_LAST 1) ตาม §1.6] |
| `PID_SENTINEL` | `0x0001` | |

- **ชื่อ topic**: prefix `rt` (topic), `rq` (service request), `rr` (service reply) [V: `rmw_fastrtps_shared_cpp/src/namespace_prefix.cpp`]
- **ชื่อ type**: `<package>::<msg|srv>::dds_::<Name>_` [V: `TypeSupport_impl.cpp` บรรทัด 311–314]
- **การเข้ารหัส string**: u32 ความยาวรวม NUL + ตัวอักษร + pad ให้ครบ 4 [K: CDR] ดังนั้น `"rt/chatter"` = 4 + 11 + 1 = 16 B (parameter รวม 20 B) และ `"example_interfaces::msg::dds_::String_"` (38 ตัวอักษร) = 4 + 39 + 1 = 44 B (parameter รวม 48 B) (คำนวณ; ตรงกับ capture: `PID_TOPIC_NAME` length 16 และ `PID_TYPE_NAME` length 44 ซึ่งมี string length 39 [V: capture ภาค 3 `exp1_fastdds_default.pcap`])
- **type hash**: `rmw_dds_common` เข้ารหัสเป็น `"typehash=RIHS01_<hex 64 ตัว>;"` ลงใน `USER_DATA` ของ endpoint [V: `rmw_dds_common/src/qos.cpp` บรรทัด 715] ความยาว 9 + 71 + 1 = 81 ตัวอักษร ทุก endpoint จึงแบกเพิ่มราว 90 B (คำนวณ)

### 1.4 ROS graph ขี่อยู่บน DDS อย่างไร: `ros_discovery_info`

SPDP/SEDP รู้จักแค่ participant กับ endpoint ไม่รู้จัก "node" ROS 2 จึงเพิ่ม topic ผู้ใช้ธรรมดาอีกหนึ่งตัวเพื่อบอกว่า endpoint ใดเป็นของ node ใด

| รายการ | ค่า | สถานะ |
|---|---|---|
| ชื่อ topic บน DDS | `ros_discovery_info` (ไม่มี prefix `rt/` เพราะ `avoid_ros_namespace_conventions = true`) | [V: `rmw_fastrtps_cpp/src/init_rmw_context_impl.cpp`] |
| QoS ฝั่ง publisher | RELIABLE, TRANSIENT_LOCAL, KEEP_LAST depth 1 | [V: ไฟล์เดียวกัน] |
| QoS ฝั่ง subscription | RELIABLE, TRANSIENT_LOCAL, KEEP_ALL (comment ในโค้ดระบุว่าถ้ารองรับ keyed topic จะใช้ KEEP_LAST 1 ได้) | [V] |
| type | `rmw_dds_common/msg/ParticipantEntitiesInfo` | [V: ไฟล์ `.msg`] |
| ผู้อ่าน | thread เฉพาะใน rmw (`std::thread(node_listener, context)`) เรียก `__rmw_take` แล้วอัปเดต graph cache | [V: `rmw_fastrtps_shared_cpp/src/listener_thread.cpp`] |

```
ParticipantEntitiesInfo:  Gid gid;  NodeEntitiesInfo[] node_entities_info_seq
NodeEntitiesInfo:         string<=256 node_namespace;  string<=256 node_name;
                          Gid[] reader_gid_seq;  Gid[] writer_gid_seq
Gid:                      char[16] data
```
[V: `rmw_dds_common/msg/*.msg` branch `lyrical`]

**แบบจำลองขนาด (ประมาณการ)** สำหรับ process ที่มี node `N` ตัว แต่ละตัวมี reader `R` และ writer `W`:

```
size ≈ 4 (encapsulation) + 16 (gid) + 4 (seq len)
       + N × [ (4 + |ns| + 1 + pad) + (4 + |name| + 1 + pad) + 4 + 16·R + 4 + 16·W ]
```

เนื่องจาก topic นี้ไม่มี key และเก็บ KEEP_LAST 1 ข้อความแต่ละฉบับจึงต้องบรรจุ**สถานะทั้งหมดของ participant** [V: QoS และ type] ส่วนที่ว่า rmw ส่งฉบับใหม่ทุกครั้งที่สร้าง/ทำลาย node หรือ endpoint เป็น [K] (ยังไม่ได้ไล่โค้ด `rmw_dds_common::Context`) ถ้าเป็นจริง ต้นทุนช่วง startup จะเป็น O(E²) byte ต่อ participant เมื่อ E คือจำนวน endpoint: process ที่มี 20 node × 20 endpoint (E = 400) จะส่งราว 400 ฉบับ ขนาดเฉลี่ยราว 3.3 KB รวมประมาณ 1.3 MB ต่อผู้รับหนึ่งราย (ประมาณการ: Σ 16·k สำหรับ k = 1..400 ≈ 1.28 MB ไม่รวมชื่อ node) ดูข้อเสนอวิจัย R6

### 1.5 สรุป traffic ของ discovery ต่อ participant

| ชั้น | อะไรวิ่ง | ความถี่ | ต้นทุนเติบโตตาม |
|---|---|---|---|
| SPDP | `DATA(p)` frame 610 B ใน capture ภาค 3 (ก่อนวัดประมาณการไว้ 250–400 B) | ทุก 3 s + 6 ครั้งแรกทุก 100 ms (1 ครั้งตอน enable + `count` 5) [V] | จำนวน participant (multicast) |
| SEDP | `DATA(w)`/`DATA(r)` ต่อ endpoint + HEARTBEAT/ACKNACK | ครั้งเดียวต่อคู่ participant แล้ว heartbeat ตามคาบ | participant² × endpoint [K] |
| ROS graph | `ParticipantEntitiesInfo` ทั้งก้อน | ทุกครั้งที่ graph เปลี่ยน [K] | endpoint² ต่อ participant (ประมาณการ) |

### 1.6 QoS → byte บนสาย

QoS ของ ROS 2 ไปถึงสายได้ 2 ทาง: (1) เป็น parameter ใน ParameterList ของ SEDP `DATA(w)`/`DATA(r)` ซึ่งส่งครั้งเดียวต่อคู่ participant (ดู §1.3) และ (2) เป็นพฤติกรรมของ reliable protocol (HEARTBEAT/ACKNACK/DATA ที่ส่งซ้ำ) หรือ traffic ของ builtin endpoint บางตัว หัวข้อนี้อ่านทางแรกระดับ byte จาก capture ของ[การทดลองที่ 16 ในภาค 3 §3](03_wire_experiments.md#3-qos-บนสาย-การทดลองที่-16) ส่วนทางที่สอง (พฤติกรรมขณะรัน) สรุปไว้ท้ายหัวข้อพร้อมลิงก์ไปยังผลใน ภาค 3 §3.2–3.7 (`rclpy` + `rmw_fastrtps_cpp` + Fast DDS 3.6.2, 2 container, UDPv4, topic `/qos_demo` ชนิด `std_msgs/String`) ทุกบรรทัดที่ยกมาถอดด้วย [`tools/rtps_peek.py`](../tools/rtps_peek.py) (โหมด `sedp`, `params`, `stats` และ option `-v` ที่เพิ่มสำหรับหัวข้อนี้) และตรวจไขว้กับ tshark 4.6.4 ใน image แล้วสำหรับ ACKNACK (bitmap, count, F), HEARTBEAT (firstSN/lastSN, count, flag F/L), INFO_TS, GAP และ PID durability/reliability/history/liveliness/deadline/lifespan [V: tshark `-V` บน frame ที่อ้างในหัวข้อนี้ ค่าตรงกันทุก field]

**ตารางสรุป** (frame = เลข frame ใน `captures/exp16_qos_<case>.pcap`, นับแบบ Wireshark; DATA(w) ที่ถูก IP fragment นับที่ frame สุดท้ายของ datagram)

| QoS policy | PID | ส่งเมื่อไร (Fast DDS 3.6.2 ที่สังเกตได้) | การเข้ารหัสค่า | traffic ขณะรัน | สถานะ |
|---|---|---|---|---|---|
| durability | `0x001d` | ทุก `DATA(w)` และ `DATA(r)` รวม VOLATILE | u32 kind: 0 VOLATILE, 1 TRANSIENT_LOCAL | TRANSIENT_LOCAL: writer ส่ง sample ที่ยังอยู่ใน history ซ้ำให้ reader ที่มาทีหลัง (DATA + INFO_TS เดิม) | [V: `tl_d10` frame 43 (w), 26 (r); `vol_d10` frame 42] |
| reliability | `0x001a` | `DATA(r)` ทุกตัว (RELIABLE); `DATA(w)` **เฉพาะเมื่อ BEST_EFFORT** (RELIABLE เป็น default ของ writer จึงไม่ส่ง) | u32 kind (1 BEST_EFFORT, 2 RELIABLE) + `max_blocking_time` Duration_t 8 B (ค่าที่เห็น 0.1 s ทุกตัว) | RELIABLE: HEARTBEAT/ACKNACK; BEST_EFFORT: ไม่มี | [V: `mm_rel` frame 35 (w BEST_EFFORT), 42 (r RELIABLE); `tl_d10` frame 43 ไม่มี PID นี้] |
| history | `0x0040` | **เฉพาะเมื่อไม่ใช่ KEEP_LAST 1** (default ของ DDS) | u32 kind (0 KEEP_LAST, 1 KEEP_ALL) + i32 depth (KEEP_ALL ยังส่ง depth 10 ของ rclpy ไปด้วย) | ไม่มี traffic ของตัวเอง แต่กำหนดว่า SN ใดยังส่งซ้ำได้ (ดู[ภาค 3 §3.2](03_wire_experiments.md#32-transient_local-สิ่งที่ส่งซ้ำให้-reader-ที่มาทีหลัง) และ[§3.3](03_wire_experiments.md#33-history-depth-ตอนมี-packet-loss-gap)) | [V: `tl_d10` frame 43 = KEEP_LAST 10; `tl_all` frame 43 = KEEP_ALL depth 10; `tl_d1` frame 42 ไม่มี PID นี้] |
| resource limits | `0x0041` | ไม่พบใน capture ใดเลย (rclpy ไม่ได้ตั้ง แม้แต่ KEEP_ALL) | 3 × i32 | - | [V: ไม่มีใน 11 capture] |
| liveliness | `0x001b` | เมื่อไม่ใช่ default (rclpy `SYSTEM_DEFAULT` = ไม่ส่ง) | u32 kind (0 AUTOMATIC, 1 MANUAL_BY_PARTICIPANT, 2 MANUAL_BY_TOPIC) + lease Duration_t | AUTOMATIC: `DATA(m)` จาก builtin writer `00.02.00.c2` ทุก 1.000 s ที่ lease 1.5 s; MANUAL_BY_TOPIC: HEARTBEAT ที่ตั้ง flag L ต่อการ assert 1 ครั้ง | [V: `live_auto` frame 24, `live_man` frame 35] |
| deadline | `0x0023` | เมื่อไม่ใช่ infinite ทั้ง w และ r | Duration_t | ไม่มี (ตรวจที่ปลายทั้งสองเอง) | [V: `dl_ls` frame 24, 44] |
| lifespan | `0x002b` | เมื่อไม่ใช่ infinite (ตั้งที่ writer) | Duration_t | ไม่มี | [V: `dl_ls` frame 24] |
| ownership, destination order, presentation, partition, latency budget | `0x001f`, `0x0025`, `0x0021`, `0x0029`, `0x0027` | ไม่พบ (rclpy ไม่มี API ตั้ง) | kind u32 / Duration_t / sequence<string> | - | [K: `WriterProxyData.cpp` เขียนเมื่อไม่ใช่ default ตาม §1.3] |

**Duration_t บนสาย** = i32 seconds + u32 fraction (หน่วย 2⁻³² s) ไม่ใช่ nanoseconds: lease 1.5 s เป็น `01 00 00 00 | 00 00 00 80` (fraction `0x80000000`), max_blocking_time 0.1 s เป็น fraction `0x1999999a` [V: `live_man` frame 35, tshark แสดง `1.500000 sec (1s + 0x80000000)`] ค่า infinite คือ `0x7fffffff` / `0xffffffff` [K: spec]

**การแปลง QoS ของ rclpy ไปเป็น DDS QoS ที่ตรวจได้จาก capture** ค่า enum ของ rmw ไม่ใช่ค่าบนสาย: log ของ node พิมพ์ `QoSProfile(reliability=1, durability=1 หรือ 2, liveliness=1 หรือ 3)` (enum ของ rmw: RELIABLE = 1, TRANSIENT_LOCAL = 1, VOLATILE = 2, AUTOMATIC = 1, MANUAL_BY_TOPIC = 3) แต่บนสายเป็น RELIABLE = 2, TRANSIENT_LOCAL = 1, VOLATILE = 0, AUTOMATIC = 0, MANUAL_BY_TOPIC = 2 [V: `qos_node_logs.txt` เทียบกับ `sedp` ของ case เดียวกัน] depth และ history ของ `QoSProfile` ไปเป็น `PID_HISTORY` ตรงตัว, `liveliness_lease_duration`/`deadline`/`lifespan` ไปเป็น Duration_t ค่าเดียวกัน, durability และ reliability ตรงตัว ส่วน `max_blocking_time` 0.1 s ไม่ได้มาจาก rclpy (rclpy ไม่มี field นี้) [V: `qos_summary.csv` คอลัมน์ `qos_DATA_w`/`qos_DATA_r` ทุก case] ค่า 0.1 s คือ default ของ Fast DDS ใน [§2.3](#23-ค่าเวลา-default-ของ-fast-dds-36x) ข้อสังเกตเพิ่ม: endpoint ของ `ros_discovery_info` ประกาศ durability TRANSIENT_LOCAL โดยไม่มี `PID_HISTORY` (= KEEP_LAST 1) ฝั่ง writer และ KEEP_ALL depth 1 ฝั่ง reader ตรงกับตารางใน §1.4 [V: `tl_all` frame 43]

ตัวอย่าง ParameterList ของ `DATA(w)` (`params`, ตัดเหลือส่วน QoS):

```
$ python3 ros2_lyrical/tools/rtps_peek.py params ros2_lyrical/captures/exp16_qos_tl_all.pcap 43
(datagram reassembled from IP fragments in frames [42, 43])
frame 43 172.21.0.3 -> 172.21.0.2 DATA writer 00.00.03.c2 reader 00.00.03.c7 SN 4
    [104] 0x0005 TOPIC_NAME                           len 16   'rt/qos_demo'
    [208] 0x001d DURABILITY                           len 4    TRANSIENT_LOCAL
    [416] 0x0040 HISTORY                              len 8    KEEP_ALL, depth 10
    [428] 0x0001 SENTINEL                             len 0
```

**พฤติกรรมขณะรันที่เห็นบนสาย** (ผลวัดเต็ม, ลำดับ submessage และเลข frame อยู่ใน[ภาค 3 §3](03_wire_experiments.md#3-qos-บนสาย-การทดลองที่-16))

- **TRANSIENT_LOCAL**: writer บอกช่วง SN ที่ยังอยู่ใน history ด้วย `firstSN` ของ HEARTBEAT แล้วส่งซ้ำเฉพาะช่วงนั้นให้ reader ที่มาทีหลัง (DATA + INFO_TS เวลา publish เดิม) โดยไม่ใช้ GAP: [ภาค 3 §3.2](03_wire_experiments.md#32-transient_local-สิ่งที่ส่งซ้ำให้-reader-ที่มาทีหลัง)
- **history depth ตอนมี packet loss**: RELIABLE + KEEP_LAST 1 ไม่ขอ SN ที่หายซ้ำเลย ส่วน depth ที่พอรับช่วงที่หายซ่อมได้ครบด้วย ACKNACK ฉบับเดียว และไม่พบ GAP submessage ใน capture ใดเลย: [ภาค 3 §3.3](03_wire_experiments.md#33-history-depth-ตอนมี-packet-loss-gap)
- **liveliness**: AUTOMATIC ส่ง `DATA(m)` จาก builtin writer `00.02.00.c2` ตามคาบ ส่วน MANUAL_BY_TOPIC ใช้ HEARTBEAT ที่ตั้ง flag L ต่อการ assert แต่ละครั้ง และไม่มี packet แจ้ง "lost": [ภาค 3 §3.4](03_wire_experiments.md#34-liveliness)
- **deadline และ lifespan**: มีเฉพาะ PID ใน SEDP ไม่มี traffic ขณะรัน บังคับใช้ในเครื่องล้วน ๆ: [ภาค 3 §3.5](03_wire_experiments.md#35-deadline-และ-lifespan)
- **QoS ไม่เข้ากัน**: SEDP แลกกันครบ แต่ writer ไม่ส่ง user DATA (แม้แต่ HEARTBEAT) และมีเพียง warning ฝั่ง subscriber: [ภาค 3 §3.6](03_wire_experiments.md#36-qos-ไม่เข้ากัน)
- **สิ่งที่ไม่ปรากฏบนสาย**: ค่า default (KEEP_LAST 1, RELIABLE ของ writer, liveliness/deadline/lifespan ที่เป็น default) ฝั่งรับต้องเติม default ของ DDS ไม่ใช่ของ ROS 2 และไม่มี packet ใดบอก deadline miss, lifespan expiry หรือ liveliness lost: [ภาค 3 §3.7](03_wire_experiments.md#37-สิ่งที่ไม่ปรากฏบนสาย)

---

## 2. Reliable protocol บนสาย

### 2.1 ค่าคงที่ของ submessage

| submessage | id | flag (bit 0 = E endianness ทุกตัว) | สถานะ |
|---|---|---|---|
| `PAD` | `0x01` | | [V: Fast DDS `RTPS_messages.hpp` `SubmessageId`, Wireshark `SUBMESSAGE_*`] |
| `ACKNACK` | `0x06` | F final = `0x02` | [V: Wireshark `FLAG_ACKNACK_F`; Fast DDS `AckNackMsg.hpp` ใช้ `BIT(1)`] |
| `HEARTBEAT` | `0x07` | F final = `0x02`, L liveliness = `0x04` | [V: `HeartbeatMsg.hpp` `BIT(1)`, `BIT(2)`; Wireshark `FLAG_HEARTBEAT_F`] |
| `GAP` | `0x08` | | [V] |
| `INFO_TS` | `0x09` | I invalidate = `0x02` | [V: Wireshark `FLAG_INFO_TS_T`] |
| `INFO_SRC` | `0x0c` | | [V] |
| `INFO_DST` | `0x0e` | | [V] |
| `NACK_FRAG` | `0x12` | | [V] |
| `HEARTBEAT_FRAG` | `0x13` | | [V] |
| `DATA` | `0x15` | Q inline QoS = `0x02`, D data = `0x04`, K key = `0x08` | [V: Wireshark `FLAG_RTPS_DATA_*`] |
| `DATA_FRAG` | `0x16` | Q = `0x02`, K = `0x04` | [V: Wireshark `FLAG_RTPS_DATA_FRAG_*`] |
| `SEC_BODY`/`SEC_PREFIX`/`SEC_POSTFIX`/`SRTPS_PREFIX`/`SRTPS_POSTFIX` | `0x30`–`0x34` | | [V: Wireshark] |
| vendor-specific | `0x80` ขึ้นไป | Fast DDS ใช้ `0x80` เป็น statistics submessage (หัวข้อ 3.7) | [V: `RTPSStatisticsMessages.hpp`] |

ทุก submessage ขึ้นต้นด้วย header 4 B: `id` u8, `flags` u8, `octetsToNextHeader` u16 [V: `RTPSMESSAGE_SUBMESSAGEHEADER_SIZE = 4`]

### 2.2 Layout ทีละ field

ขนาดด้านล่างนับจากลำดับการเรียก `CDRMessage::add*` ในโค้ด Fast DDS 3.6.x [V: `src/cpp/rtps/messages/submessages/*.hpp`, `CDRMessage.cpp`]

**HEARTBEAT (32 B)**: writer บอกว่ามี sequence number ช่วงใดให้ขอได้
```
07 fl len16 | readerId 4 | writerId 4 | firstSN 8 | lastSN 8 | count 4
```
ตรงกับค่าคงที่ `heartbeat_message_length = 32` ใน `BaseWriter::calculate_max_payload_size` [V]

**ACKNACK (28–56 B)**: reader ตอบว่าได้ครบถึงไหนและขาดตัวใด
```
06 fl len16 | readerId 4 | writerId 4 | SequenceNumberSet | count 4
SequenceNumberSet = bitmapBase 8 | numBits 4 | bitmap 4 × ceil(numBits/32)
```
- `bitmapBase` = SN แรกที่ยังไม่ได้รับ ทุก SN ที่ต่ำกว่านี้ถือว่า ack แล้ว บิตที่เป็น 1 = ขอให้ส่งซ้ำ [K: spec]
- Fast DDS จำกัด bitmap ที่ 8 word = 256 บิต [V: `std::array<uint32_t, 8>` ใน `CDRMessage::addSequenceNumberSet`] ACKNACK หนึ่งฉบับจึงขอซ้ำได้ไม่เกิน 256 sample ติดกัน
- set ว่าง: เขียน `numBits = 0` และไม่มี bitmap [V] จึงได้ขนาดต่ำสุด 4 + 8 + 12 + 4 = 28 B

**GAP**: writer บอกว่า SN ช่วงนี้จะไม่มีวันส่ง (เช่นถูกลบออกจาก history แล้ว)
```
08 fl len16 | readerId 4 | writerId 4 | gapStart 8 | gapList (SequenceNumberSet)
```
ความหมาย: `[gapStart, gapList.base)` ไม่เกี่ยวข้องทั้งช่วง บวกกับ SN ที่บิตเป็น 1 ใน `gapList` [K: spec; ลำดับ field V]

**DATA_FRAG header (36 B)**
```
16 fl len16 | extraFlags 2 | octetsToInlineQos 2 (= 28) | readerId 4 | writerId 4 | writerSN 8
            | fragmentStartingNum 4 (เริ่มที่ 1) | fragmentsInSubmessage 2 | fragmentSize 2 | sampleSize 4
            | [inlineQos] | fragment data
```
- `octetsToInlineQos` = 28 สำหรับ DATA_FRAG และ 16 สำหรับ DATA [V: `RTPSMESSAGE_OCTETSTOINLINEQOS_DATAFRAGSUBMSG`, `..._DATASUBMSG` ใน `CDRMessage_t.hpp`]
- Fast DDS ส่ง**หนึ่ง fragment ต่อหนึ่ง submessage เสมอ** (`addUInt16(msg, 1)` พร้อม comment `we are sending one fragment`) [V: `DataMsg.hpp` บรรทัด 110]
- `fragmentSize` เป็น **u16** fragment จึงใหญ่ได้ไม่เกิน 65535 B ตามรูปแบบบนสาย [V: `addUInt16(msg, change->getFragmentSize())`]
- `sampleSize` = ความยาว serialized payload ทั้งก้อน [V: `addUInt32(msg, change->serializedPayload.length)`]
- ตรงกับค่าคงที่ `data_frag_submessage_header_length = 36` [V]

**NACK_FRAG**: reader ขอ fragment ที่ขาดของ sample เดียว
```
12 fl len16 | readerId 4 | writerId 4 | writerSN 8 | FragmentNumberSet | count 4
FragmentNumberSet = bitmapBase 4 | numBits 4 | bitmap 4 × ceil(numBits/32)   (สูงสุด 256 บิต)
```
[V: `AckNackMsg.hpp` `addSubmessageNackFrag`, `CDRMessage::addFragmentNumberSet`]

### 2.3 ค่าเวลา default ของ Fast DDS 3.6.x

| พารามิเตอร์ | default | ที่มา |
|---|---|---|
| writer `heartbeat_period` | **3 s** | [V: `WriterAttributes.hpp` บรรทัด 63] |
| writer `initial_heartbeat_delay` | 12 ms | [V: บรรทัด 61] |
| writer `nack_response_delay` | 5 ms | [V: บรรทัด 65] |
| writer `nack_supression_duration` | 0 | [V: บรรทัด 67] |
| reader `heartbeat_response_delay` | 5 ms | [V: `ReaderAttributes.hpp` บรรทัด 51] |
| reader `initial_acknack_delay` | 70 ms | [V: บรรทัด 49] |
| `ReliabilityQosPolicy.max_blocking_time` | 100 ms | [V: `QosPolicies.hpp` บรรทัด 580] |

ใน `rmw_fastrtps_cpp/src/publisher.cpp`, `rmw_fastrtps_shared_cpp/src/qos.cpp`, `participant.cpp` และ `utils.cpp` ของ branch `lyrical` ไม่พบโค้ดที่แก้ค่า heartbeat เหล่านี้ [V: grep คำว่า `heartbeat` ในไฟล์ทั้งสี่ ได้ 0 รายการ] จึงคาดว่า ROS 2 ใช้ค่า default ข้างต้น เว้นแต่ผู้ใช้ตั้งผ่าน XML profile

**เงื่อนไขการแนบ HEARTBEAT ไปกับ DATA** [V: `StatefulWriter::send_heartbeat_piggyback_nts_`, `StatefulWriter.cpp` บรรทัด 1919–1941]

เมื่อ `separate_sending = false` (default [V: `WriterAttributes.hpp` บรรทัด 131]) writer จะแนบ HEARTBEAT ท้าย DATA ก็ต่อเมื่อข้อใดข้อหนึ่งเป็นจริง
1. `history_->isFull()`
2. `next_all_acked_notify_sequence_ < get_seq_num_min()`
3. จำนวนครั้งที่ message group เกิน send buffer เปลี่ยนไปจากรอบก่อน

นอกเหนือจากนี้ reader จะได้ HEARTBEAT จาก timer ตามคาบเท่านั้น ข้อสังเกตนี้นำไปสู่สมมติฐาน R2: เวลากู้คืนหลัง packet หายของ topic RELIABLE ที่ส่งไม่ถี่อาจถูกกำหนดด้วย `heartbeat_period` 3 s มากกว่าด้วยเครือข่าย (ยังไม่ได้วัด และยังไม่ได้ไล่ทุกเส้นทางที่เรียก `send_heartbeat_nts_`)

### 2.4 ตัวอย่างคำนวณ: `sensor_msgs/Image` 640×480 `rgb8`

**ขนาด payload** (XCDR1 little-endian, สมมติ `frame_id = "camera"`)

| field | byte |
|---|---|
| encapsulation header | 4 |
| `header.stamp` (i32 + u32) | 8 |
| `header.frame_id` = u32 len + `"camera\0"` + pad 1 | 12 |
| `height`, `width` | 8 |
| `encoding` = u32 len + `"rgb8\0"` | 9 |
| `is_bigendian` + pad 2 | 3 |
| `step` | 4 |
| `data` = u32 len + 921 600 | 921 604 |
| **รวม (`sampleSize`)** | **921 652** |

(คำนวณจากกฎ alignment ของ CDR; `sampleSize` นับรวม encapsulation 4 B [V: capture ภาค 3 `exp2_image_reliable.pcap.gz` ดูด้านล่าง])

**ผลวัดใน[ภาค 3](03_wire_experiments.md):** `sampleSize` = **921 648 B** ในทุก DATA_FRAG ของ `exp2` และ `exp5` ต่างจากตารางข้างบน 4 B เพราะ [`img_pub.py`](../captures/scripts/img_pub.py) ตั้ง `frame_id` เป็น `f"f{k}"` (`"f0"`…`"f4"` ใน exp2, ถึง `"f19"` ใน exp5) ซึ่งเป็น u32 len + `"f0\0"` 3 B + pad 1 (หรือ `"f10\0"` 4 B ไม่มี pad) = 8 B แทน 12 B ของ `"camera"` (921 652 − 4 = 921 648) ไล่ byte ใน DATA_FRAG แรก (frame 107) แล้วตรงทุก field: encapsulation `00 01 00 00`, stamp 0 (8 B), len 3 + `"f0\0"` + pad 1, height 480, width 640, len 5 + `"rgb8\0"`, `is_bigendian` 0 + pad 2, step 1920, len 921 600 แล้วตามด้วย data ที่ offset 48 นับจากต้น `serializedPayload` ผลรวม 4 + 921 644 = 921 648 จึงยืนยันว่า `sampleSize` นับรวม encapsulation header (ถ้าไม่นับจะเป็น 921 644) จำนวน fragment ยังเป็น 15 เท่าเดิม

**ขนาด fragment ที่ Fast DDS เลือก** [V: `BaseWriter::get_max_allowed_payload_size` + `calculate_max_payload_size` + `RTPSParticipantImpl::calculateMaxDataSize`]

```
maxMessageSize (UDP และ SHM default)            = 65 500   [V: s_maximumMessageSize, TransportInterface.hpp]
− RTPS header                                   =     20   → 65 480
− INFO_DST 16 − INFO_TS 12 − DATA_FRAG hdr 36 − HEARTBEAT 32 = 96
− statistics submessage (ถ้า build ด้วย FASTDDS_STATISTICS)  = 60
ปัดลงให้หาร 4 ลงตัว (& ~3)
```

| build | fragment size | จำนวน DATA_FRAG | fragment สุดท้าย |
|---|---|---|---|
| `FASTDDS_STATISTICS=OFF` | 65 384 | **15** (14 เต็ม + 1) | 6 276 B |
| `FASTDDS_STATISTICS=ON` (default ของ CMake upstream) | 65 324 | **15** (14 เต็ม + 1) | 7 116 B |

**ต่อหนึ่ง DATA_FRAG เต็ม** (กรณีส่งถึง participant เดียวจึงมี INFO_DST)

- RTPS message = 20 + 16 + 12 + 36 + fragment (+ 60) = **65 468 B** ทั้งสอง build (ส่วน 32 B ที่กันไว้ให้ HEARTBEAT จะถูกใช้เมื่อเข้าเงื่อนไขในหัวข้อ 2.3 แล้วได้ 65 500 B พอดี)
- UDP datagram = 65 476 B → IP payload ต่อ fragment ที่ MTU 1500 = 1480 B → **45 IP fragment** (44 × 1480 + 356)
- DATA_FRAG สุดท้าย (6 360 หรือ 7 260 B) → 5 IP fragment
- **รวมทั้งภาพ: 14 × 45 + 5 = 635 Ethernet frame**
- byte-time บนสาย = UDP 923 032 B + 635 × (IP 20 + Ethernet 14 + FCS 4 + preamble 8 + IFG 12) = **959 862 B** (กรณีไม่มี statistics; มี statistics = 960 762 B)
- เวลาบนสาย: **7.68 ms ที่ 1 GbE**, 76.8 ms ที่ 100 Mb/s; ที่ 30 fps ใช้ 230 Mb/s; เพดานที่ 1 GbE ≈ 130 fps (คำนวณ)

หมายเหตุ: link ของเครื่องที่ใช้ตรวจ negotiate ได้ 100 Mb/s [V: `ethtool enp2s0`] ภาพ 640×480 rgb8 ที่ 30 fps (230 Mb/s) จึงส่งผ่าน link นี้ไม่ได้

### 2.5 ถ้า IP fragment หายหนึ่งชิ้น

**ชั้น kernel ฝั่งรับ**

1. fragment อีก 44 ชิ้นค้างอยู่ใน reassembly queue (`ip_defrag` → `ip_frag_queue`) [V: symbol มีใน kallsyms]
2. queue หมดอายุเมื่อครบ `ipfrag_time` = **30 s** บนเครื่องนี้ [V: `sysctl net.ipv4.ipfrag_time`; `IP_FRAG_TIME (30 * HZ)` ใน `include/net/ip.h` v7.0] แล้ว `ip_expire` ทิ้งทั้ง queue
3. หน่วยความจำที่ค้าง: comment ใน kernel ระบุว่า "A 64K fragment consumes 129736 bytes (44*2944)+200" [V: `net/ipv4/ip_fragment.c` v7.0 บรรทัด 667–668] เพดาน `ipfrag_high_thresh` = 4 MiB [V: sysctl และโค้ดบรรทัด 674] จึงรองรับ datagram 64K ที่ประกอบไม่เสร็จได้พร้อมกันราว 4 194 304 / 129 736 ≈ **32 ก้อน** (คำนวณ)
4. `ipfrag_max_dist` = 64 [V: sysctl และโค้ดบรรทัด 683]

ผลที่ตามมา (ประมาณการ): ที่ 30 fps มี 450 datagram/s ถ้า loss ต่อ frame p = 0.1% datagram 65 KB จะเสีย 1 − (1 − p)^45 = 4.4% คือราว 20 ก้อน/s แต่ละก้อนค้าง 30 s จึงชนเพดาน 32 ก้อนภายในราว 1.6 s หลังจากนั้น fragment ใหม่มีโอกาสถูกปฏิเสธจนกว่า queue เก่าจะหมดอายุ (พฤติกรรมตอนเกิน `high_thresh` เป็น [K]) นี่คือเหตุผลเชิงปริมาณของคำแนะนำ `ipfrag_time=3` และเพิ่ม `ipfrag_high_thresh` ในภาค 1

**ชั้น RTPS**

| QoS | สิ่งที่หาย | เส้นทางกู้คืน |
|---|---|---|
| BEST_EFFORT | **ทั้ง sample 921 652 B** reader ทิ้ง sample ที่ประกอบไม่ครบเมื่อ fragment ของ SN ที่ใหม่กว่ามาถึง แล้วเรียก `on_sample_lost` [V: `StatelessReader::process_data_frag_msg` บรรทัด 780–801] | ไม่มี |
| RELIABLE | DATA_FRAG 1 ก้อน (65 384 B) | (1) reader เก็บ fragment ที่ได้ด้วย `add_fragments` (memcpy ลง payload ของ CacheChange) [V: `StatefulReader::process_data_frag_msg`, `CacheChange.hpp`] (2) เมื่อ HEARTBEAT มาถึง ตั้ง timer `heartbeat_response_delay` 5 ms (3) `StatefulReader::send_acknack` ตรวจว่า SN ที่ขาดเป็น sample ที่ประกอบค้างหรือไม่ ถ้าใช่ส่ง `NACK_FRAG(SN, ชุด fragment ที่ขาด)` แล้วตามด้วย `ACKNACK` [V: `StatefulReader.cpp` บรรทัด 1690–1735] (4) writer รอ `nack_response_delay` 5 ms แล้ว `perform_nack_response` ส่งกลับเข้า flow controller ด้วย `add_old_sample` [V: `StatefulWriter.cpp` บรรทัด 1944–1960] (5) ส่ง DATA_FRAG ซ้ำ = **45 IP fragment** |

**ตัวขยายความเสียหาย (คำนวณ)**

| loss ต่อ frame (p) | P(datagram 65 KB รอด) = (1−p)^45 | P(ภาพรอดแบบ best-effort) = (1−p)^635 | จำนวน DATA_FRAG ที่ต้องส่งซ้ำต่อภาพโดยเฉลี่ย (reliable) |
|---|---|---|---|
| 0.001% | 99.96% | 99.4% | 0.006 |
| 0.01% | 99.55% | 93.8% | 0.063 |
| 0.1% | 95.6% | 53.0% | 0.62 |
| 1% | 63.6% | 0.17% | 5.1 |

- frame 1514 B หายหนึ่งชิ้น ทำให้ต้องส่งซ้ำ 65 468 B: ตัวขยาย **45 เท่า**
- เวลากู้คืนขั้นต่ำ ≈ เวลารอ HEARTBEAT ถัดไป + 5 ms + 5 ms + เวลาส่ง 45 frame (0.54 ms ที่ 1 GbE) (ประมาณการจากค่า default ในหัวข้อ 2.3)

---

## 3. Fast DDS 3.6.x ส่วนที่แตะ OS

### 3.1 เส้นทางส่ง: class และ syscall

```
rmw_publish                                      [tracepoint rmw_publish: V rmw_fastrtps_shared_cpp/src/rmw_publish.cpp]
 └ DataWriter::write → DataWriterImpl → WriterHistory::set_fragments   (ตัดสินว่าต้อง fragment หรือไม่)
    └ FlowController (sync: ส่งใน thread ผู้เรียก)
       └ StatefulWriter / StatelessWriter::deliver_sample_nts
          └ RTPSMessageGroup::add_data / add_data_frag  (ประกอบ header + INFO_DST + INFO_TS + submessage)
             └ SenderResource → UDPTransportInterface::send
                ├ setsockopt(SOL_SOCKET, SO_SNDTIMEO)        ← ทุกครั้งที่ส่ง
                └ asio socket.send_to(buffers, endpoint)     ← gather send
```
[V: ชื่อ class/ไฟล์ทั้งหมดมีใน tree ของ branch `3.6.x`; ลำดับการเรียกช่วงบนเป็น [K] ยกเว้นส่วนที่อ้างบรรทัด]

ข้อเท็จจริงที่ตรวจแล้ว

1. **ROS 2 Lyrical ส่งแบบ synchronous เป็น default**: `publishing_mode_t publishing_mode = publishing_mode_t::SYNCHRONOUS;` เปลี่ยนได้ด้วย `RMW_FASTRTPS_PUBLICATION_MODE=ASYNCHRONOUS` [V: `rmw_fastrtps_shared_cpp/src/participant.cpp` บรรทัด 300–327] ดังนั้น `sendmsg` ถูกเรียกจาก **thread ของผู้ใช้ที่เรียก `publish()`** ไม่ใช่ thread ภายใน และคาดว่า `publish()` ของภาพ 1 MB จะ block จนส่งครบ 15 datagram (ข้อสรุปจากโหมด sync; ยังไม่ได้วัด)
2. **syscall สองครั้งต่อ datagram**: `UDPTransportInterface::send` เรียก `setsockopt(..., SO_SNDTIMEO, ...)` ก่อน `send_to` ทุกครั้งบน non-Windows [V: `UDPTransportInterface.cpp` บรรทัด 608–619]
3. **gather send**: `send_to` รับ `std::vector<NetworkBuffer>` payload ถูกอ้างอิงเป็น buffer แยก ไม่ถูกคัดลอกมาต่อกับ header ใน user space เมื่อ payload มี `payload_owner` (`copy_data = (nullptr == change.serializedPayload.payload_owner)`) [V: `RTPSMessageGroup.cpp` บรรทัด 599] ส่วนว่า asio แปลงเป็น `sendmsg` + `iovec` เป็น [K] (ไม่ได้อ่าน source ของ asio)
4. **ปฏิเสธ datagram ที่ใหญ่กว่า send buffer**: `if (total_bytes > configuration()->sendBufferSize) return false;` [V: บรรทัด 582]
5. **ไม่ใช้ non-blocking โดย default**: `non_blocking_send = false` [V: `BuiltinTransports.hpp`, `UDPTransportInterface.cpp` บรรทัด 293] ถ้าเปิดแล้ว socket buffer เต็ม โค้ดจะ log "UDP send would have blocked. Packet is dropped." [V: บรรทัด 625]
6. **memory policy**: rmw ตั้ง `PREALLOCATED_WITH_REALLOC_MEMORY_MODE` ให้ทั้ง writer, reader และ builtin endpoint [V: `publisher.cpp` บรรทัด 252, `subscription.cpp` บรรทัด 413, `participant.cpp` บรรทัด 333–336]
7. **`transport_priority` ไม่ถูกใช้ทั้ง UDP และ TCP**: พารามิเตอร์ถูก comment ชื่อทิ้งในทั้งสอง transport (`const int32_t /* transport_priority */`) และ grep `IP_TOS|IPV6_TCLASS|SO_PRIORITY|dscp|DSCP` ใน `src/` กับ `include/` ของ 3.6.x ได้ 0 รายการ [V: `UDPTransportInterface.cpp` บรรทัด 543, `TCPTransportInterface.cpp` บรรทัด 1498] (ภาค 1 §6 แก้ตามข้อนี้แล้ว) ส่วน Cyclone DDS มี field `m_diffserv` ใน `ddsi_udp.c` แต่ยังไม่ได้ไล่ว่าใช้อย่างไร

### 3.2 Thread model

ชื่อ thread ด้านล่างเป็น format string ที่ส่งให้ `create_thread` จึงมองเห็นได้ใน `top -H`, `ps -L`, `perf sched` [V: grep `create_thread` ใน 3.6.x]

| ชื่อ thread | จำนวน | หน้าที่ | ที่มา |
|---|---|---|---|
| `dds.udp.<port>` | 1 ต่อ input locator (port) | วน `receive_from` แบบ blocking แล้วเรียก `MessageReceiver::OnDataReceived` ใน thread เดียวกัน | [V: `UDPChannelResource.cpp` บรรทัด 50, 62–79] |
| `dds.shm.<port>` | 1 ต่อ SHM port | รอ descriptor จาก port ring buffer | [V: `SharedMemChannelResource.hpp` บรรทัด 178] |
| `dds.shm.wdog` | 1 ต่อ process | watchdog ตรวจ port ที่ค้าง | [V: `SharedMemWatchdog.hpp` บรรทัด 126] |
| `dds.ev.<id>` | 1 ต่อ participant | timer event: periodic heartbeat, nack response, heartbeat response, SPDP announce, lease | [V: `RTPSParticipantImpl.cpp` บรรทัด 595] |
| `dds.asyn.<participant>.<index>` | 1 ต่อ async flow controller | ส่งแบบ asynchronous และ**ส่งซ้ำ** (`add_old_sample`) | [V: `FlowControllerImpl.hpp` บรรทัด 1116–1119] |
| `dds.dsha.<id>` | 1 ต่อ reader ที่ใช้ data-sharing | รอ notification | [V: `DataSharingListener.cpp` บรรทัด 107–110] |
| (thread ของ rmw) | 1 ต่อ context | อ่าน `ros_discovery_info` | [V: `listener_thread.cpp`] |

ข้อสังเกต
- การ parse RTPS, การประกอบ fragment และ callback `on_data_available` ทำงานใน `dds.udp.<port>` thread เดียวต่อ port ถ้า callback ช้า socket buffer ของ port นั้นจะไม่ถูกระบาย
- `ThreadSettings` (scheduling policy, priority, affinity, stack size) ตั้งแยกต่อชนิด thread ได้ [V: มี `include/fastdds/rtps/attributes/ThreadSettings.hpp` และ `get_thread_config_for_port`] รายละเอียด field เป็น [K]

### 3.3 ขนาด socket buffer ที่ Fast DDS ขอจริง

- `sendBufferSize` และ `receiveBufferSize` default = **0** [V: `SocketTransportDescriptor.hpp` บรรทัด 59–60]
- เมื่อเป็น 0: อ่านค่าปัจจุบันของ socket (ค่า default ของระบบ) ถ้าต่ำกว่า `maxMessageSize` ให้ยกขึ้นเป็น `maxMessageSize` แล้วพยายาม `set_option` ถ้าไม่สำเร็จให้ลดลงครึ่งหนึ่งไปเรื่อย ๆ จนถึงค่าต่ำสุด [V: `asio_helpers.hpp` `configure_buffer_size`, `try_setting_buffer_size`]
- บนเครื่องนี้ `net.core.rmem_default = wmem_default = 212992`, `rmem_max = 4194304` [V: sysctl] socket รับของ Fast DDS จึงเริ่มที่ราว 208 KiB ผลต่อการรับภาพอยู่ในหัวข้อ 5.3 วัดจริงด้วย `ss` ([ภาค 3 §4.2.5](03_wire_experiments.md#425-ตรวจตัวแปร-ค่าที่-kernel-ใช้จริงและสิ่งที่ไม่เปลี่ยน-v)): `<rtps><listenSocketBufferSize>N` ให้ `SO_RCVBUF` = 2 × min(N, `rmem_max`) บน listen socket ทุกตัว เช่น ขอ 212 992 ได้ 425 984 และขอ 8 MiB ได้ 8 388 608 เท่ากับขอ 4 MiB [V: ภาค 3 §4.2.5]

### 3.4 SHM transport ในระดับ OS

**ชื่อ object** (domain ของ SHM manager คือสตริง `"fastdds"` [V: `SharedMemTransport.cpp` บรรทัด 42 `#define SHM_MANAGER_DOMAIN ("fastdds")`; ไม่พบ prefix `fastrtps_` ในไฟล์ที่ตรวจ]; directory คือ `/dev/shm` บน Linux [V: `SharedDir.hpp`])

| object | ชื่อ | บทบาท | ที่มา |
|---|---|---|---|
| port segment | `fastdds_port<port_id>` | `PortNode` + ring buffer ของ descriptor | [V: `SharedMemGlobal.hpp` บรรทัด 1050] |
| port mutex | `fastdds_port<port_id>_mutex` | named mutex ตอนเปิด/สร้าง port | [V: บรรทัด 1079] |
| port lock file | `fastdds_port<port_id>_el` (exclusive) หรือ `_sl` (shared) | ตรวจ zombie port ด้วย file lock | [V: บรรทัด 928–984] |
| data segment | `fastdds_<uuid hex>` 1 ต่อ participant | buffer ของ datagram ที่ participant นี้ส่ง | [V: `SharedMemManager.hpp` บรรทัด 540] |
| segment lock | `fastdds_<uuid>_el` | บอกว่าเจ้าของยังมีชีวิต | [V: บรรทัด 546] |

`port_id` ใช้สูตรเดียวกับ UDP (`getUnicastPort(domainId, i)`) [V: `SharedMemTransport.cpp` บรรทัด 732] จึงเห็นไฟล์ชื่อเช่น `fastdds_port7411` (ตัวอย่างชื่อคำนวณจากสูตร; `ls /dev/shm` ในการทดลองที่ 4 ของ[ภาค 3](03_wire_experiments.md) เห็น `fastdds_port7411` จริง พร้อม `fastdds_port7000`/`7001`/`7413`)

**ค่าคงที่** [V: `SharedMemTransportDescriptor.hpp`, `SharedMemGlobal.hpp`]

| ค่า | default |
|---|---|
| segment size | **512 KiB** (`shm_implicit_segment_size = 512 * 1024` เมื่อ descriptor ระบุ 0) |
| port queue capacity | 512 descriptor |
| healthy check timeout | 1000 ms |
| `maxMessageSize` | **65 500** (constructor ตั้ง `maxMessageSize = s_maximumMessageSize`) |
| ABI version | 5 (`CURRENT_ABI_VERSION`, มี `static_assert` = 2 + major) |
| listener สูงสุดต่อ port | 1024 (`LISTENERS_STATUS_SIZE`) |

**กลไก**

1. ฝั่งส่ง `SharedMemTransport::send` เรียก `copy_to_shared_buffer` ซึ่ง `alloc_buffer` จาก data segment ของตัวเอง แล้ว **`memcpy` ทุก NetworkBuffer ลง segment** หนึ่งครั้ง ไม่ว่าจะมีผู้รับกี่ port (comment `Only copy the first time`) [V: `SharedMemTransport.cpp` บรรทัด 464–523]
2. จากนั้น push `BufferDescriptor { source_segment_id, buffer_node_offset, validity_id }` ลง ring buffer ของแต่ละ port ปลายทาง [V: `SharedMemGlobal.hpp` บรรทัด 71–90, `Port::try_push`]
3. ring buffer เป็น multi-producer multi-consumer ใช้ `std::atomic` กับ compare-exchange บนคู่ `(write_p, free_cells)` และ ref counter ต่อ cell = จำนวน listener [V: `MultiProducerConsumerRingBuffer.hpp`]
4. การปลุกผู้รับใช้ `RobustInterprocessCondition` ซึ่งสร้างจาก `boost::interprocess::interprocess_semaphore` pool 512 ตัว และ `interprocess_mutex` [V: `RobustInterprocessCondition.hpp`, `SharedMemSegment.hpp`] การที่ semaphore/mutex เหล่านี้ลงไปเป็น `futex` เป็น [K]
5. ผู้ส่งกู้คืน buffer ที่ผู้รับตายคาได้ด้วย `validity_id` (24 บิต), `enqueued_count`, `processing_count` (อย่างละ 20 บิต) ที่อัดอยู่ใน atomic 64 บิตตัวเดียว [V: `SharedMemManager.hpp` `BufferNode::Status`]
6. เมื่อ segment เต็มและกู้คืนไม่ได้ `alloc_buffer` โยน exception แล้ว `send` ถือว่าสำเร็จ (comment `Segment overflow with discard policy doesn't return error`) [V: `SharedMemTransport.cpp` บรรทัด 534–543] คือ**ทิ้งเงียบ**

**นัยสำหรับข้อความใหญ่** (ประมาณการจากค่าข้างต้น): เพราะ SHM ก็ใช้ `maxMessageSize` 65 500 ภาพ 921 652 B จึงยังถูกตัดเป็น 15 DATA_FRAG เหมือน UDP แต่ละก้อนถูกจองใน segment 512 KiB ซึ่งจุได้ราว 8 ก้อน ถ้าผู้รับระบายไม่ทัน ก้อนที่ 9 เป็นต้นไปเสี่ยงถูกทิ้งตามข้อ 6 ดูสมมติฐาน R5

### 3.5 Data-sharing delivery

- segment ของ payload pool: `fast_datasharing_<guidPrefix>_<entityId>` ของ writer; segment ของ notification: ชื่อรูปแบบเดียวกันจาก GUID ของ reader [V: `DataSharingPayloadPool.hpp` บรรทัด 89–91, 350–360; `DataSharingNotification.hpp` บรรทัด 94–125]
- writer แจ้ง reader ด้วย `new_data.store(true)` แล้ว `notification_cv.notify_all()` [V: `DataSharingNotification.hpp` บรรทัด 58–61]
- data-sharing ไม่ส่ง fragment (comment ใน `StatefulReader::process_data_frag_msg`: `Datasharing communication will never send fragments`) [V]
- **ใน ROS 2 Lyrical data-sharing ถูกปิดเป็น default**: `rmw_fastrtps_cpp` เรียก `writer_qos.data_sharing().off()` และ `reader_qos.data_sharing().off()` เมื่อไม่ได้ตั้ง `RMW_FASTRTPS_USE_QOS_FROM_XML` (`leave_middleware_default_qos == false`) [V: `publisher.cpp` บรรทัด 245–256, `subscription.cpp` บรรทัด 412–417 และ 684–688] (ภาค 1 §3.1 แก้ตามข้อนี้แล้ว)

### 3.6 Flow controller

- descriptor: `name` (default `"FastDDSFlowControllerDefault"`), `scheduler` (default `FIFO`), `max_bytes_per_period` (default 0 = ไม่จำกัด), `period_ms` (default 100), `sender_thread` [V: `FlowControllerDescriptor.hpp`, `FlowControllerConsts.cpp`]
- scheduler policy: `FIFO`, `ROUND_ROBIN`, `HIGH_PRIORITY`, `PRIORITY_WITH_RESERVATION` [V: `FlowControllerSchedulerPolicy.hpp`]
- implementation เป็น template `FlowControllerImpl<PublishMode, SampleScheduler>` มี publish mode 4 แบบ: PureSync, Sync, Async, LimitedAsync [V: `FlowControllerFactory.cpp`, `FlowControllerImpl.hpp`] comment ระบุว่า PureSync ใช้กับ writer แบบ volatile best-effort
- เมื่อจำกัด bandwidth ขนาด fragment จะถูกบีบตาม: `get_max_payload()` คืน `max_bytes_per_period` สำหรับ LimitedAsync และ `BaseWriter::get_max_allowed_payload_size` ใช้ค่าน้อยสุดระหว่าง flow controller, participant และ writer [V: `FlowControllerImpl.hpp` บรรทัด 1531–1543, `BaseWriter.cpp` บรรทัด 176–188]
- ผลข้างเคียง: flow controller ที่ตั้ง `max_bytes_per_period` เล็กกว่า MTU จะบังคับให้ fragment ระดับ RTPS เล็กพอที่ไม่เกิด IP fragmentation ซึ่งเป็นวิธีแก้ปัญหาหัวข้อ 2.5 ที่ทำได้ด้วย config ล้วน (ข้อสรุปจากโค้ด; ยังไม่ได้ทดลอง) ดูตาราง tuning และผลวัดใน[ภาค 3 §4.4](03_wire_experiments.md#44-dds-tuning-ต่อ-rmw-การทดลองที่-13)

### 3.7 Build option ที่เปลี่ยน byte บนสาย

| option (CMake) | default upstream 3.6.x | ผลบนสาย | ที่มา |
|---|---|---|---|
| `SECURITY` | **OFF** | protocol version ใน RTPS header: **2.3 เมื่อ ON, 2.2 เมื่อ OFF** (`#if HAVE_SECURITY ... ProtocolVersion_t(2, 3) #else ... (2, 2)`; comment อ้าง DDSSEC11-93) | [V: `CMakeLists.txt` บรรทัด 278, `include/fastdds/rtps/common/Types.hpp` บรรทัด 108–117] |
| `FASTDDS_STATISTICS` | **ON** | ทุก RTPS message ที่ส่งมี submessage id `0x80` ยาว **60 B** ต่อท้าย (header 4 + `StatisticsSubmessageData` 56) และ fragment size ลดลง 60 B | [V: `CMakeLists.txt` บรรทัด 428, `RTPSStatisticsMessages.hpp`, `RTPSMessageGroup.cpp` บรรทัด 973–984, `BaseWriter.cpp`] |
| `SHM_TRANSPORT_DEFAULT` | ON | มี SHM ใน builtin transport | [V: `CMakeLists.txt` บรรทัด 326] |

- ขนาด 56 B ของ `StatisticsSubmessageData` คำนวณจาก layout: `Locator_t` 24 + `TimeStamp` 8 + `Sequence` (u64, u64, u16 + padding) 24 (คำนวณจากนิยาม struct; ยังไม่ได้ compile `sizeof` แต่บนสายเห็น header `80 01 38 00` คือ length 56 B ตรงกัน [V: capture ภาค 3])
- `colcon.pkg` ของ Fast DDS ไม่มี cmake-args เพิ่ม [V] การ build จาก `ros2.repos` ด้วย colcon โดยไม่ใส่ flag จึงได้ SECURITY=OFF, STATISTICS=ON
- **binary `.deb` ของ Lyrical build ด้วย `-DSECURITY=ON`** และไม่ได้แตะ `FASTDDS_STATISTICS` (จึงเป็น ON ตาม default) [V: `ros2-gbp/fastdds-release` branch `debian/lyrical/resolute/fastdds` ไฟล์ `debian/rules`] ผู้ที่ติดตั้งจาก apt จึงควรเห็น protocol version **2.3** และ statistics submessage `0x80` ต่อท้าย ส่วนผู้ที่ build จาก source ด้วย colcon โดยไม่ใส่ flag จะได้ 2.2 ยืนยันด้วย capture แล้ว: `ros-lyrical-fastdds 3.6.2` จาก apt ส่ง `"RTPS" 02 03` และทุก RTPS message ลงท้ายด้วย submessage `0x80` [V: capture ภาค 3 `exp1_fastdds_default.pcap`]
- `add_stats_submsg()` ถูกเรียกเมื่อ compile ด้วย `FASTDDS_STATISTICS` ทุกครั้งที่ส่ง (ยกเว้น DATA ที่ไม่ fragment และเกิน 65 kB) ไม่ขึ้นกับว่าเปิด statistics module ตอน runtime หรือไม่ [V: `RTPSMessageGroup.cpp` บรรทัด 393–400]

**ผลต่อ frame ตัวอย่างของภาค 1** (`example_interfaces/msg/String "Hello World: 1"`, `serializedPayload` 24 B) (คำนวณ; แถวสุดท้ายตรงกับ capture)

| ส่วนประกอบ | UDP payload | Ethernet frame |
|---|---|---|
| RTPS 20 + INFO_TS 12 + DATA 24 + payload 24 (frame สังเคราะห์เดิมของภาค 1) | 80 | 122 |
| + INFO_DST 16 (เมื่อผู้รับทั้งหมดอยู่ใน participant เดียว) | 96 | 138 |
| + statistics 60 | 140 | 182 |
| + ทั้งสองอย่าง | 156 | 198 (frame 95 ใน `exp1_fastdds_default.pcap` ซึ่งภาค 1 §5.4 ใช้เป็นตัวอย่างแล้ว [V: capture ภาค 3]) |

`INFO_DST` ยาว 16 B รวม header (header 4 + guidPrefix 12; `info_dst_message_length = 16` ใน `BaseWriter.cpp` [V]) ถูกเพิ่มเมื่อ `current_dst_ != destination_guid_prefix` โดย `current_dst_` เริ่มที่ `c_GuidPrefix_Unknown` [V: `RTPSMessageGroup.cpp` บรรทัด 429, 520–524] เงื่อนไขที่ `destination_guid_prefix()` คืนค่าที่ไม่ใช่ unknown เป็น [K]

---

## 4. `rmw_zenoh_cpp` บนสาย

เวอร์ชันที่ตรวจ: `zenoh_cpp_vendor/CMakeLists.txt` ของ branch `lyrical` pin zenoh-c commit `07b0d43…` พร้อม comment "This corresponds to zenoh-c 1.10.1 plus few fixes" [V] source ของ protocol อ่านจาก tag `1.10.1` ของ `eclipse-zenoh/zenoh` ส่วน "few fixes" ไม่ได้ตรวจ

> **หมายเหตุเวอร์ชัน (ตรวจภายหลังจาก binary ที่ติดตั้งจริง):** ใน image ที่ใช้ทดลองของ[ภาค 3](03_wire_experiments.md) (`lyrical-wire:exp` = `ros:lyrical-ros-base` + apt) `ros-lyrical-rmw-zenoh-cpp` และ `ros-lyrical-zenoh-cpp-vendor` เป็น **0.10.6** ซึ่งภายในเป็น **zenoh-c 1.8.0** (`#define ZENOH_C "1.8.0"` ใน `zenoh_configure.h`, `zenohc.pc` Version 1.8.0), **zenoh-cpp 1.9.0** (`zenohcxx.pc`) และ crate **zenoh (Rust) 1.8.0** ที่ git commit `2687c51…` (string `v1.8.0-2687c51352121f006e3a603ce07925a8ad0b295c` และ path `.cargo/git/checkouts/zenoh-…/2687c51/` ใน `libzenohc.so`) [V: `dpkg -l` และไฟล์ใน `/opt/ros/lyrical/opt/zenoh_cpp_vendor/`] ไม่ใช่ 1.10.1 ตาม comment ของ branch `lyrical` ที่อ่านข้างต้น (branch น่าจะถูกเลื่อนหลังจาก build `.deb` นี้ แต่ยังไม่ได้ตรวจ) ลำดับ field ในหัวข้อนี้อ่านจาก source 1.10.1 จึงยังไม่ได้เทียบกับ 1.8.0 ทีละ field แต่ field ที่ยืนยันด้วย capture แล้ว (length prefix, attachment 33 B, CDR payload) ตรงกับที่อธิบายไว้

### 4.1 ชั้นของ message

Zenoh แบ่ง 3 ชั้น แต่ละชั้นมี header 1 byte ที่ 5 บิตล่างเป็น id และ 3 บิตบนเป็น flag [V: แผนภาพใน doc comment ของ `commons/zenoh-protocol/src/transport/frame.rs`, `network/push.rs`, `zenoh/put.rs`]

| ชั้น | message id | ที่มา |
|---|---|---|
| Transport | `OAM 0x00`, `INIT 0x01`, `OPEN 0x02`, `CLOSE 0x03`, `KEEP_ALIVE 0x04`, `FRAME 0x05`, `FRAGMENT 0x06`, `JOIN 0x07` | [V: `transport/mod.rs` `pub mod id`] |
| Network | `INTEREST 0x19`, `RESPONSE_FINAL 0x1a`, `RESPONSE 0x1b`, `REQUEST 0x1c`, `PUSH 0x1d`, `DECLARE 0x1e`, `OAM 0x1f` | [V: `network/mod.rs`] |
| Zenoh (body) | `OAM 0x00`, `PUT 0x01`, `DEL 0x02`, `QUERY 0x03`, `REPLY 0x04`, `ERR 0x05` | [V: `zenoh/mod.rs`] |

- protocol version byte = `0x09` [V: `zenoh-protocol/src/lib.rs` `VERSION`]
- จำนวนเต็มเข้ารหัสแบบ variable-length 7 บิตต่อ byte, บิตสูง = มี byte ต่อ, สูงสุด 9 byte สำหรับ u64 [V: `zenoh-codec/src/core/zint.rs`]

### 4.2 Framing บน TCP

```
TCP stream:  [len u16 LE] [batch ≤ 65535 B]  [len u16 LE] [batch] ...
batch:       FRAME hdr 1 | seq num (varint) | [exts] | NetworkMessage, NetworkMessage, ...
```

- stream transport ไม่รักษาขอบเขต message จึงนำหน้าทุก batch ด้วยความยาว 16 บิต little-endian [V: doc comment ใน `frame.rs`, `fragment.rs`, `keepalive.rs`]
- batch สูงสุด 65535 B: `BatchSize = u16`, `batch_size::UNICAST = u16::MAX`; config ของ ROS ตั้ง `batch_size: 65535` [V: `transport/mod.rs`; `DEFAULT_RMW_ZENOH_SESSION_CONFIG.json5`]
- `FRAME` flag: `R` reliable channel, `Z` มี extension; หนึ่ง FRAME บรรจุหลาย NetworkMessage ที่ใช้ sequence number ร่วมกันได้ [V: `frame.rs`]
- `FRAGMENT` flag: `R`, `M` more, `Z`; ใช้เมื่อ NetworkMessage ใหญ่กว่า batch หรือ MTU ของ link มี extension Start และ Stop (Stop = fragment ที่เหลือถูกทิ้ง) [V: `fragment.rs`]
- `KEEP_ALIVE`: ไม่ต้องส่งถ้ามี data อื่นวิ่งในช่วงนั้น [V: `keepalive.rs`] ROS ตั้ง `lease: 60000` ms และ `keep_alive: 2` [V: config] คาบ keep-alive จึงเป็น 30 s (คำนวณจาก lease / keep_alive ตามคำอธิบายใน config)
- sequence number resolution 32 บิต [V: config]
- TCP socket ตั้ง `TCP_NODELAY` [V: `zenoh-link-tcp/src/unicast.rs` บรรทัด 56–57] และรองรับ `so_sndbuf`, `so_rcvbuf`, DSCP ผ่าน config ของ endpoint [V: `zenoh-link-tcp/src/utils.rs`]
- batching แบบ adaptive เปิดอยู่ (`batching.enabled: true`, `time_limit: 1` ms) ทำงานเมื่อมี back-pressure [V: config] tx queue ต่อ priority = 2 batch, 8 priority [V: config]
- rx `buffer_size: 65535`, defragmentation สูงสุด `max_message_size: 1073741824` (1 GiB) [V: config]
- lifecycle ของ session: `INIT` (syn/ack) → `OPEN` (syn/ack) → `FRAME`/`FRAGMENT`/`KEEP_ALIVE` → `CLOSE` [V: id และมีไฟล์ `init.rs`, `open.rs`; ลำดับ handshake [K]]

### 4.3 Key expression ที่ `rmw_zenoh_cpp` ใช้

[V: `docs/design.md` branch `lyrical`]

- **topic / service**: `<domain_id>/<fully_qualified_name>/<type_name>/<type_hash>`
  ```
  0/chatter/std_msgs::msg::dds_::String_/RIHS01_df668c740482bbd48fb39d76a70dfd4bd59db1288021743503259e948f6b1a18
  ```
- **liveliness token ของ node**:
  ```
  @ros2_lv/<domain_id>/<session_id>/<node_id>/<node_id>/NN/<mangled_enclave>/<mangled_namespace>/<node_name>
  ```
- **liveliness token ของ endpoint** (`MP` publisher, `MS` subscription, `SS` service server, `SC` service client):
  ```
  @ros2_lv/<domain_id>/<session_id>/<node_id>/<entity_id>/<kind>/<mangled_enclave>/<mangled_namespace>/<node_name>/<mangled_qualified_name>/<type_name>/<type_hash>/<qos>[/<backends>]
  @ros2_lv/0/8b20917502ee955ac4476e0266340d5c/0/10/MP/%/%/talker/%chatter/std_msgs::msg::dds_::String_/RIHS01_df66…1a18/::,7:,:,:,,
  ```
  mangle = แทน `/` ด้วย `%`; `@ros2_lv` เป็น hermetic namespace ที่ `*` และ `**` ไม่ match
- **ช่องเพิ่มสำหรับ `rosidl::Buffer`**: `<topic key>/_buf_cpu` (กลุ่ม CPU ร่วม) และ `<topic key>/_buf/<gid>` (ต่อ subscriber) [V: `design.md` บรรทัด 593–608]

เทียบกับ DDS: ข้อมูลที่ SEDP + `ros_discovery_info` ส่งเป็น ParameterList และ CDR นั้น Zenoh อัดลงในสตริง key ของ liveliness token ทั้งหมด token หนึ่งตัวของ endpoint ยาวราว 200 ตัวอักษร (นับจากตัวอย่างข้างบน) และไม่มีข้อความ "ทั้ง participant" ที่โตตามจำนวน endpoint แบบหัวข้อ 1.4

### 4.4 หนึ่ง `publish()` กลายเป็นอะไร

`rmw_zenoh_cpp` เรียก `AdvancedPublisher::put(payload, options)` โดย [V: `rmw_zenoh_cpp/src/detail/rmw_publisher_data.cpp`, `design.md`]

- payload = CDR ที่ serialize ด้วย Fast-CDR (`CdrVersion::DDS_CDR`) [V: `detail/cdr.cpp`]
- **attachment 33 B**: sequence number i64 LE (8) + source timestamp ns i64 LE (8) + ความยาว GID 1 byte (ปัจจุบัน 16 เสมอ) + GID 16 [V: `design.md` บรรทัด 361–365, `attachment_helpers.cpp`]
- QoS → Zenoh: RELIABLE → `Z_RELIABILITY_RELIABLE`; default `Z_CONGESTION_CONTROL_DROP`; RELIABLE + KEEP_ALL → `Z_CONGESTION_CONTROL_BLOCK` [V: `rmw_publisher_data.cpp` `create_publisher_endpoint`]
- TRANSIENT_LOCAL → เปิด publication cache (`max_samples = depth`) และถ้า RELIABLE ด้วยจะเปิด sample-miss detection แบบ `HeartbeatSporadic` คาบ 500 ms [V: `SAMPLE_MISS_DETECTION_HEARTBEAT_PERIOD 500`]
- timestamping เปิดทุก mode เพราะ publication cache ต้องใช้ [V: config พร้อม comment `ROS setting`] ทุก `PUT` จึงมี flag `T` และ timestamp
- SHM: ถ้าเปิดและขนาด ≥ threshold จะ `alloc_gc_defrag` จาก SHM provider ถ้าล้มเหลว fallback เป็น allocation ปกติ [V: `rmw_publisher_data.cpp` บรรทัด 534–550]

**โครงของ byte** (ลำดับ field [V: `zenoh-codec` `network/push.rs`, `zenoh/put.rs`]; ขนาดแต่ละ field เป็นประมาณการเพราะเป็น varint ภายหลัง capture ใน[ภาค 3](03_wire_experiments.md) วัดได้เฉพาะขนาดรวม length prefix, attachment และ CDR payload ส่วนการแบ่ง field ที่เหลือยังถอดด้วยมือ ไม่ได้ตรวจด้วย Zenoh dissector)

```
len16 | FRAME hdr | sn | PUSH hdr | key_scope [key_suffix] | [QoS ext] | PUT hdr | timestamp | [encoding]
      | [sinfo ext] | attachment ext (33 B + header) | payload len (varint) | CDR payload
```

| ส่วน | ขนาด (ประมาณการ) | เหตุผล |
|---|---|---|
| length prefix | 2 | [V] |
| FRAME header + sequence number | 2–6 | header 1 + varint ของ u32 |
| PUSH header + key scope | 2–4 | key ที่ declare แล้วส่งเป็น id ตัวเลข [K] |
| QoS extension | 0–3 | เขียนเมื่อไม่ใช่ `QoSType::DEFAULT` [V: codec] |
| PUT header | 1 | |
| timestamp | 10–26 | เวลา varint ของ u64 (สูงสุด 9) + ZenohId ความยาว 1 + สูงสุด 16 [K: รูปแบบ ZenohId] |
| attachment extension | ≈ 35–36 | 33 B + ext header + ความยาว |
| payload length | 1 | varint ของ 23 (เห็น `0x17` บนสาย [V: capture ภาค 3]) |
| CDR ของ `"Hello World: 1"` | 23 | encapsulation 4 + string length 4 + 14 ตัวอักษร + NUL 1 = 23 B ไม่มี padding ท้าย [V: capture ภาค 3 `exp3_zenoh.pcap` frame 142] ส่วน RTPS ใน `exp1` เป็น 24 B เพราะ `serializedPayload` ของ DATA มี byte `00` ต่อท้ายอีก 1 ตัว (DATA length 44 = 20 + 24) |
| **รวม TCP payload** | **≈ 76–102** (วัดจริง **95 B** รวม length prefix [V: capture ภาค 3]) | |

เทียบกับ RTPS/UDP ของข้อความเดียวกัน (UDP payload 80–156 B ตามหัวข้อ 3.7) (ประมาณการทั้งคู่; ผลวัดใน[ภาค 3](03_wire_experiments.md): RTPS UDP payload 156 B ใน frame 198 B เทียบกับ Zenoh TCP payload 95 B ใน frame 161 B)

| | RTPS/UDP (Fast DDS) | Zenoh/TCP |
|---|---|---|
| L4 header | UDP 8 | TCP 20 + options (โดยทั่วไป 12 สำหรับ timestamp [K]) |
| middleware overhead ต่อ sample เล็ก | 56–132 B | ≈ 53–79 B |
| ACK | ACKNACK ระดับ RTPS เมื่อมี HEARTBEAT | TCP ACK ของ kernel (delayed ACK) |
| หลาย sample ต่อ packet | message grouping ต่อ writer | FRAME รวมข้าม topic ได้ใน session เดียว + adaptive batching |

สรุป: สำหรับข้อความเล็ก overhead ต่อ sample ของสองระบบอยู่ในระดับเดียวกัน ข้อได้เปรียบของ Zenoh อยู่ที่ชั้น discovery และพฤติกรรมกับข้อความใหญ่มากกว่า

### 4.5 ภาพ 921 652 B ผ่าน Zenoh/TCP (ประมาณการ)

- NetworkMessage ใหญ่กว่า batch → ตัดเป็น `FRAGMENT` ราว **15 batch** (ceil(≈921.7 KB / 65.5 KB))
- TCP ตัดเป็น segment ตาม MSS: ที่ MTU 1500 พร้อม timestamp option ได้ 1448 B → ราว **637 segment** ใกล้เคียง 635 frame ของ RTPS
- ความต่างอยู่ที่ loss: TCP ส่งซ้ำ **1 segment (1448 B)** ต่อ frame ที่หาย ไม่ใช่ 45 frame และไม่มี IP fragmentation จึงไม่แตะ `ipfrag_*`
- ต้นทุนที่แลกมา: head-of-line blocking ทุก topic ที่ใช้ session และ priority เดียวกันรอ segment ที่หาย และ congestion control ของ TCP ลด rate หลัง loss [K]
- ฝั่ง kernel: TCP ใช้ TSO/GSO และ GRO ได้เต็มที่ NIC ของเครื่องนี้เปิด `tx-tcp-segmentation: on` [V: `ethtool -k enp2s0`] ขณะที่ `tx-udp-segmentation: off [fixed]` [V: `ethtool -k enp2s0`]
- **ผลวัด (การทดลองที่ 12):** จำนวน FRAGMENT ต่อภาพตรงกับประมาณการ แต่ความยาว batch ไม่ใช่ 65 535 B ตัวเลขทั้งหมดอยู่ใน[ภาค 3 §4.5](03_wire_experiments.md#45-ภาพ-640480-ผ่าน-zenohtcp-การทดลองที่-12)

---

## 5. Kernel ลึกกว่าชื่อฟังก์ชัน

### 5.1 `struct sk_buff` เฉพาะ field ที่กำหนดพฤติกรรมของ ROS traffic

ขนาดบนเครื่องนี้: `sizeof(struct sk_buff)` = **232 B**, `sizeof(struct skb_shared_info)` = **320 B**, `CONFIG_MAX_SKB_FRAGS` = 17, cache line 64 B [V: `bpftool btf dump file /sys/kernel/btf/vmlinux`, `/boot/config-7.0.0-43-generic`]

```
head ──► ┌──────────────┐
         │ headroom     │  ที่ว่างให้ชั้นล่างเติม header (skb_push)
data ──► ├──────────────┤
         │ linear data  │  len − data_len byte
tail ──► ├──────────────┤
         │ tailroom     │
end  ──► ├──────────────┤
         │ skb_shared_info: nr_frags, frags[17], frag_list, gso_size, gso_segs, gso_type, dataref
         └──────────────┘
```

| field | ความหมาย | เกี่ยวกับ ROS อย่างไร |
|---|---|---|
| `head`, `data`, `tail`, `end` | ขอบเขต buffer เชิงเส้น | [V: `include/linux/skbuff.h` v7.0 บรรทัด 1092–1095] |
| `len`, `data_len` | ความยาวรวม และส่วนที่อยู่นอก linear area (ใน `frags[]` หรือ `frag_list`) | datagram ที่ประกอบจาก IP fragment มีข้อมูลกระจายหลายชิ้น `recvmsg` ต้องเดินทุกชิ้น [V: field; K: ผลต่อ recvmsg] |
| `truesize` | หน่วยความจำจริงที่ skb นี้กิน = data buffer + `sk_buff` + `skb_shared_info` (`SKB_TRUESIZE(X) = X + SKB_DATA_ALIGN(232) + SKB_DATA_ALIGN(320)` = X + 576 บนเครื่องนี้) | **ตัวที่ถูกหักจาก `SO_RCVBUF`** ไม่ใช่ `len` ดูหัวข้อ 5.3 [V: macro บรรทัด 273–275; 576 คำนวณจากขนาดใน BTF] |
| `ip_summed` | `CHECKSUM_NONE 0`, `CHECKSUM_UNNECESSARY 1`, `CHECKSUM_COMPLETE 2`, `CHECKSUM_PARTIAL 3` | TX: `PARTIAL` = ให้ NIC คำนวณ ใช้ได้เฉพาะ datagram ที่ไม่ถูก IP fragment (หัวข้อ 5.2) RX: r8169 ตั้ง `UNNECESSARY` เมื่อ hardware ตรวจผ่าน [V: บรรทัด 248–251; `r8169_main.c` บรรทัด 4759] |
| `csum_start`, `csum_offset` | ตำแหน่งที่ NIC ต้องเริ่มคำนวณและเขียน checksum | [V: บรรทัด 1042–1043] |
| `shinfo->gso_size`, `gso_segs`, `gso_type` | ขนาด segment เมื่อเป็น GSO; UDP ใช้ `SKB_GSO_UDP_L4 = 1 << 17` | [V: บรรทัด 598–606, 705] |
| `shinfo->frag_list` | สาย skb ลูก ใช้กับ IP reassembly และ GRO แบบ fraglist | [V: บรรทัด 601] |
| `napi_id` | NAPI instance ที่รับ packet ใช้โดย busy polling | [V: บรรทัด 1058] |
| `tstamp`, `priority`, `mark`, `hash` | timestamp, qdisc class, netfilter mark, flow hash (RPS/RFS) | [V] `priority` มาจาก `SO_PRIORITY` ซึ่ง Fast DDS 3.6.x ไม่ตั้ง (หัวข้อ 3.1 ข้อ 7) |

### 5.2 Checksum, GSO, GRO และ zero-copy กับ RTPS

**ทำไม datagram 65 KB ของ RTPS เสีย offload ทุกอย่าง** [V: `net/ipv4/ip_output.c` v7.0 `__ip_append_data` บรรทัด 999–1003, `ip_generic_getfrag` บรรทัด 933–947]

```c
if (transhdrlen &&
    length + fragheaderlen <= mtu &&
    rt->dst.dev->features & (NETIF_F_HW_CSUM | NETIF_F_IP_CSUM) &&
    (!(flags & MSG_MORE) || cork->gso_size) && ...)
        csummode = CHECKSUM_PARTIAL;
```

1. datagram ที่ใหญ่กว่า MTU ไม่ผ่านเงื่อนไข `length + fragheaderlen <= mtu` จึงไม่ได้ `CHECKSUM_PARTIAL`
2. เมื่อไม่ใช่ `CHECKSUM_PARTIAL` การ copy จาก user ใช้ `csum_and_copy_from_iter_full` คือ **คำนวณ checksum ด้วย CPU ไปพร้อมกับ copy** ทุก byte
3. `MSG_ZEROCOPY` ต้องการทั้ง `NETIF_F_SG` และ `csummode == CHECKSUM_PARTIAL` (บรรทัด 1007–1030) datagram ที่ต้อง fragment จึง**ใช้ zero-copy ไม่ได้** kernel จะ copy ตามปกติ

**UDP GSO / GRO**

| รายการ | ค่า | ที่มา |
|---|---|---|
| `UDP_SEGMENT` | 103 (setsockopt หรือ cmsg, ค่าเป็น u16 = ขนาด segment) | [V: `include/uapi/linux/udp.h`, `udp.c` `__udp_cmsg_send`] |
| `UDP_GRO` | 104 | [V] |
| `UDP_MAX_SEGMENTS` | 128 (`1 << 7`) | [V: `include/linux/udp.h` บรรทัด 133] |
| เงื่อนไข GSO | `hlen + min(datalen, gso_size) > fragsize` → error; `datalen > gso_size * UDP_MAX_SEGMENTS` → error | [V: `udp_send_skb` บรรทัด 1139–1164] |
| UDP GRO ฝั่งรับทำงานเมื่อ | socket เปิด `UDP_GRO`, หรือ device มี `NETIF_F_GRO_FRAGLIST`, หรือไม่มี socket และมี `NETIF_F_GRO_UDP_FWD` | [V: `net/ipv4/udp_offload.c` บรรทัด 809–813] |
| NIC ของเครื่องนี้ | `tx-udp-segmentation: off [fixed]`, `rx-gro-list: off`, `rx-udp-gro-forwarding: off`, `generic-segmentation-offload: on` | [V: `ethtool -k enp2s0`] |

ความหมาย: UDP GSO ไม่ได้ส่ง "datagram ใหญ่หนึ่งก้อน" แต่ส่ง**หลาย datagram ขนาด `gso_size`** ด้วย syscall และการเดิน stack ครั้งเดียว แต่ละ datagram เป็น UDP สมบูรณ์ที่มี header ของตัวเอง middleware ที่จะใช้ต้องตั้ง fragment ระดับ RTPS ให้เท่ากับ `gso_size` (ไม่เกิน MTU − 28) และทำให้ทุก segment เป็น RTPS message ที่ parse ได้ด้วยตัวเอง

**middleware ใน Lyrical ใช้หรือไม่** [V: grep `UDP_SEGMENT|UDP_GRO|MSG_ZEROCOPY|SO_ZEROCOPY|io_uring|sendmmsg|recvmmsg|SO_BUSY_POLL` ใน source]

| โครงการ | ผล |
|---|---|
| Fast DDS 3.6.x (`src/`, `include/`) | **0 รายการ** |
| Cyclone DDS `releases/11.0.x` (`src/`) | **0 รายการ** |
| Zenoh 1.10.1 (repo หลัก, `*.rs`) | ไม่พบ `UDP_SEGMENT`/`UDP_GRO`/`ZEROCOPY`/`sendmmsg`/`recvmmsg`/`BUSY_POLL`; มี feature `uring` (crate `zenoh-uring`, ใช้ `io-uring = 0.7.10`) สำหรับฝั่ง RX แต่ไม่อยู่ใน default features และ `zenoh_cpp_vendor` build ด้วย `--features=shared-memory zenoh/transport_serial` เท่านั้น |

ข้อจำกัดของการตรวจ: grep ครอบคลุมเฉพาะ repo ที่ระบุ ไม่รวม dependency (asio, tokio, quinn) และไม่ได้ตรวจ Connext ซึ่งเป็น closed source

**`MSG_ZEROCOPY`** [V: `Documentation/networking/msg_zerocopy.rst`, `net/core/sock.c` v7.0 บรรทัด 1590–1605]

- `SO_ZEROCOPY` ตั้งได้กับ socket ตระกูล INET/INET6 ที่เป็น TCP หรือ UDP (`SOCK_DGRAM` + `IPPROTO_UDP`) และตระกูล RDS; เอกสาร kernel ระบุว่า feature นี้ implement สำหรับ TCP, UDP และ VSOCK
- เอกสาร kernel ระบุว่า "Copy avoidance is not a free lunch" และได้ผลกับ write ที่ใหญ่กว่าราว 10 KB
- การแจ้งว่า kernel เลิกใช้ page แล้วมาทาง error queue ของ socket (`recvmsg(MSG_ERRQUEUE)`)
- เหตุที่ RTPS stack ยังไม่ใช้ (วิเคราะห์): (ก) datagram ใหญ่ถูก IP fragment จึงไม่เข้าเงื่อนไขตามข้อ 3 ข้างบน (ข) payload ต้องคงอยู่และห้ามแก้จนกว่าจะได้ notification ซึ่งต้องผูกกับอายุของ CacheChange ใน history (ค) ต้องเพิ่ม thread หรือ poll สำหรับ error queue

**io_uring zero-copy receive (zcrx)** [V: `Documentation/networking/iou-zcrx.rst`, `io_uring/zcrx.c` v7.0]

- โค้ดรับผ่าน `tcp_read_sock` และเอกสารอธิบายเฉพาะ TCP (flow steering ตัวอย่างเป็น `flow-type tcp6`) ต้องการ header/data split, flow steering และ RSS จาก NIC
- จึงใช้กับ RTPS/UDP ไม่ได้ในเวอร์ชันนี้ ผู้ที่อาจใช้ได้คือ transport แบบ TCP (Zenoh, Fast DDS `LARGE_DATA`) บน NIC ระดับ server การที่ r8169 ไม่รองรับ header/data split เป็น [K]

### 5.3 `SO_RCVBUF` นับอะไร และทำไมภาพหายทั้งที่ CPU ว่าง

**กฎ** [V: `net/core/sock.c` v7.0 `__sock_set_rcvbuf` บรรทัด 974–993; `net/ipv4/udp.c` `__udp_enqueue_schedule_skb` บรรทัด 1700–1775]

1. `setsockopt(SO_RCVBUF, val)`: kernel เก็บ `sk_rcvbuf = max(min(val, rmem_max) × 2, SOCK_MIN_RCVBUF)` comment ในโค้ดอธิบายว่าคูณ 2 เพื่อชดเชย overhead ของ `struct sk_buff` ค่า default จาก `rmem_default` **ไม่ถูกคูณ 2**
2. ตอน enqueue ใช้ `size = skb->truesize` แล้วตรวจ
   ```c
   if (rmem + size > rcvbuf) {
           if (rcvbuf > INT_MAX >> 1) goto drop;
           /* Accept the packet if queue is empty. */
           if (rmem) goto drop;
   }
   ```
   คือทิ้งทันทีเมื่อเกิน ยกเว้นคิวว่างซึ่งรับได้หนึ่ง packet เสมอ
3. เมื่อ `rmem > rcvbuf / 2` kernel เรียก `skb_condense` เพื่อลด `truesize`
4. Linux 7.0 มีคิวกลางต่อ NUMA node (`udp_prod_queue`, `llist`) ก่อนย้ายเข้า `sk_receive_queue` ภายใต้ lock ครั้งเดียว [V: บรรทัด 1717–1760; `struct udp_prod_queue` ขนาด 64 B ใน BTF] โครงสร้างนี้ต่างจาก kernel 6.x รุ่นก่อน ชื่อ symbol และจุด probe จึงควรตรวจใหม่ตามเวอร์ชัน
5. tracepoint ที่ยิงตอนทิ้ง: `udp:udp_fail_queue_rcv_skb`, `sock:sock_rcvqueue_full`, `skb:kfree_skb` พร้อม reason [V: `__traceiter_*` มีใน kallsyms]

**packet เล็กกินบัฟเฟอร์เร็วกว่าที่คิด (ประมาณการ)**

- `truesize` ต่ำสุดเชิงทฤษฎี = 576 B + data buffer แม้ payload มีไม่กี่สิบ byte
- frame 122–198 B ของ `"Hello World: 1"`: data buffer มาจาก small-head cache ของ `__alloc_skb` (เข้าเงื่อนไข `len <= SKB_WITH_OVERHEAD(SKB_SMALL_HEAD_CACHE_SIZE)` ใน `napi_alloc_skb` [V: `net/core/skbuff.c` v7.0 บรรทัด 850–856]) ประมาณการ `truesize` ราว 768–1024 B
- `sk_rcvbuf` default 212 992 B จึงรับได้ราว 200–280 packet ซึ่งบรรจุ CDR จริงเพียง 5–7 KB หรือราว 3% ของบัฟเฟอร์
- ตัวเลขนี้ต้องวัดจริง: `sudo bpftrace -e 'kprobe:__udp_enqueue_schedule_skb { @ts = hist(((struct sk_buff *)arg1)->truesize); }'` (ยังไม่ได้รัน)

**datagram 65 KB กินเท่าไร (ประมาณการ)**

| แหล่งของตัวเลข `truesize` ต่อ fragment 1500 B | ต่อ datagram 45 fragment | จำนวน datagram ที่ `sk_rcvbuf` 212 992 รับได้ |
|---|---|---|
| comment ใน kernel: 2944 B [V: `ip_fragment.c` บรรทัด 668] | 132 480 B | **1** |
| คำนวณสำหรับ r8169: `napi_alloc_skb(1514)` → `SKB_DATA_ALIGN(1514 + 64) + SKB_DATA_ALIGN(320) + SKB_DATA_ALIGN(232)` = 1600 + 320 + 256 = 2176 B | 97 920 B | **2** |

(ค่า `NET_SKB_PAD` = 64 และ `NET_IP_ALIGN` = 0 บน x86-64 เป็น [K]; การที่ `truesize` ของ skb หลัง reassembly เท่ากับผลรวมของทุก fragment เป็น [K] โดยมี `inet_frag_reasm_finish` ปรับ `truesize` [V: symbol และโค้ด `inet_fragment.c` บรรทัด 503–553])

ผลตามมาสำหรับภาพ 15 datagram: ที่ 1 GbE datagram เต็มมาถึงห่างกันราว 545 µs (คำนวณ: (65 476 + 45 × 58) × 8 / 10⁹) socket ที่ค่า default รองรับได้ 1–2 ก้อน thread `dds.udp.<port>` จึงต้อง `recvmsg` ให้ทันภายใน 0.5–1 ms ทุกรอบ ถ้า thread ถูกหน่วงนานกว่านั้นครั้งเดียว (ถูก preempt, callback ผู้ใช้ทำงานใน thread เดียวกัน, page fault) DATA_FRAG จะถูกทิ้งที่ socket ทั้งที่ CPU เฉลี่ยยังว่าง นี่เป็นคำอธิบายเชิงกลไกของอาการ "ภาพหายเมื่อใช้ค่า default" ที่ต้องยืนยันด้วยการทดลอง R4

### 5.4 softirq budget และ ksoftirqd

| พารามิเตอร์ | ค่าบนเครื่องนี้ | ความหมาย | ที่มา |
|---|---|---|---|
| `net.core.netdev_budget` | 300 | packet สูงสุดต่อรอบ `net_rx_action` รวมทุก NAPI | [V: sysctl; `Documentation/admin-guide/sysctl/net.rst`] |
| `net.core.netdev_budget_usecs` | 2000 | เวลาสูงสุดต่อรอบ (µs) | [V: sysctl; `dev.c` v7.0 บรรทัด 7893–7896] |
| `net.core.dev_weight` | 64 | budget ต่อ NAPI ต่อครั้ง (backlog device) | [V: sysctl] ค่า weight 64 ของ NAPI driver เป็น [K] |
| `time_squeeze` | ตัวนับใน `softnet_data` | เพิ่มเมื่อ budget หรือเวลาหมดทั้งที่ยังมีงาน | [V: `dev.c` บรรทัด 7935–7938] อ่านได้จากคอลัมน์ที่ 3 ของ `/proc/net/softnet_stat` [K] |
| `MAX_SOFTIRQ_TIME` | 2 ms | เพดานเวลาของ `handle_softirqs` ก่อนส่งต่อให้ ksoftirqd | [V: `kernel/softirq.c` v7.0 บรรทัด 543] |
| `MAX_SOFTIRQ_RESTART` | 10 | จำนวนรอบ restart สูงสุด | [V: บรรทัด 544] |
| `gro_flush_timeout` ของ `enp2s0` | 20 000 ns | software IRQ coalescing | [V: `/sys/class/net/enp2s0/gro_flush_timeout`] |
| `napi_defer_hard_irqs` ของ `enp2s0` | 1 | | [V: sysfs] |
| `net.core.gro_normal_batch` | 8 | | [V: sysctl] |

- r8169 เปิด software coalescing เองตอน probe: `netdev_sw_irq_coalesce_default_on(dev)` ซึ่งตั้ง `gro_flush_timeout` = 20000 [V: `r8169_main.c` บรรทัด 5758; `dev.c` บรรทัด 12005] ค่าบน sysfs ตรงกัน ผลคือ packet ที่มาถึงเดี่ยว ๆ อาจถูกหน่วงเพิ่มได้ถึงราว 20 µs ก่อนส่งขึ้น stack (ขนาดของผลเป็นประมาณการจากค่า timer; ยังไม่ได้วัด)
- ภาพหนึ่งภาพ = 635 frame มากกว่า `netdev_budget` 300 จึงใช้ `net_rx_action` อย่างน้อย 3 รอบ (คำนวณ) ถ้า softirq ทำงานต่อเนื่องเกิน 2 ms หรือ restart ครบ 10 รอบ งานที่เหลือย้ายไป `ksoftirqd/N` ซึ่งเป็น thread ปกติที่ต้องแย่ง CPU กับ thread ของผู้ใช้ [V: ค่าคงที่; K: ผลต่อ latency]
- เครื่องนี้ build ด้วย `CONFIG_PREEMPT_LAZY=y`, `CONFIG_PREEMPT_DYNAMIC=y`, `CONFIG_HZ=1000`, ไม่ใช่ `PREEMPT_RT` [V: `/boot/config-7.0.0-43-generic`]
- บน PREEMPT_RT: softirq ถูก preempt ได้ (comment `PREEMPT_RT makes BH preemptible` [V: `softirq.c` บรรทัด 135]) และ IRQ handler เป็น thread ถ้า thread ของแอปมี priority แบบ real-time สูงกว่า thread ที่ประมวลผล NET_RX แอปจะแย่ง CPU จากเส้นทางรับ packet ของตัวเองได้ [K] ต้องออกแบบ priority ของ IRQ thread, `dds.udp.*` และ executor ร่วมกัน

### 5.5 จาก `sock_def_readable` ถึง thread ของผู้ใช้

```
__udp_enqueue_schedule_skb
 └ sk->sk_data_ready = sock_def_readable                   [tracepoint sock:sk_data_ready]
    └ skwq_has_sleeper(wq) ? wake_up_interruptible_sync_poll(&wq->wait, EPOLLIN|...)
       └ __wake_up_sync_key → __wake_up_common → เรียก func ของแต่ละ wait entry
          ├ blocking recvmsg:  receiver_wake_function → autoremove_wake_function → try_to_wake_up
          └ epoll:             ep_poll_callback → ปลุกผู้รอใน ep_poll → ep_send_events
             try_to_wake_up → select_task_rq_fair → ttwu_do_activate → wakeup_preempt
                                                    [sched:sched_waking, sched:sched_wakeup]
 ... context switch [sched:sched_switch] ...
 __skb_recv_udp คืน skb → udp_recvmsg → skb_copy_datagram_iter → กลับ user space
```
[V: เนื้อ `sock_def_readable` จาก `sock.c` v7.0 บรรทัด 3602–3615; ทุก symbol ในแผนภาพมีใน kallsyms ของเครื่องนี้; ลำดับการเรียกระหว่าง symbol เป็น [K]]

- Fast DDS ใช้ blocking `receive_from` ต่อ port [V: `UDPChannelResource.cpp`] จึงเป็นกิ่ง `receiver_wake_function` ไม่ใช่ epoll ส่วน Zenoh ใช้ async runtime ของ Rust ซึ่งคาดว่าเป็นกิ่ง epoll [K]
- คำว่า `sync` ใน `wake_up_interruptible_sync_poll` เป็น hint ถึง scheduler ว่าผู้ปลุกกำลังจะหยุดทำงาน [K]
- จาก packet ถึง callback ของผู้ใช้มี wakeup **สองครั้ง**: (1) softirq → `dds.udp.<port>` ผ่าน socket wait queue (2) `dds.udp.<port>` → executor thread ผ่าน condition variable ของ rmw (futex) [K: ครั้งที่สอง]
- latency ของ wakeup แต่ละครั้ง = เวลาออกจาก idle state ของ CPU ปลายทาง + เวลารอใน run queue + context switch ตัวแปรที่คุมได้: C-state (`cpuidle`), affinity, scheduling class, และ PREEMPT_RT [K]

### 5.6 Busy polling

- `CONFIG_NET_RX_BUSY_POLL=y`; `net.core.busy_read = 0`, `net.core.busy_poll = 0` (ปิด) [V: config, sysctl]
- socket ใหม่ทุกตัวรับค่าเริ่มต้นจาก sysctl: `sk->sk_ll_usec = READ_ONCE(sysctl_net_busy_read)` [V: `sock.c` v7.0 บรรทัด 3748] และตั้งรายตัวได้ด้วย `SO_BUSY_POLL`, `SO_PREFER_BUSY_POLL`, `SO_BUSY_POLL_BUDGET` [V: `sock.c` บรรทัด 1233–1243]
- เส้นทางรับของ UDP เรียก `sk_busy_loop` เมื่อ `sk_can_busy_loop(sk)` ก่อนจะหลับรอ [V: `udp.c` v7.0 บรรทัด 2025–2028] และ UDP บันทึก NAPI id ด้วย `sk_mark_napi_id` [V: บรรทัด 2364]
- นัย: เพราะ Fast DDS ใช้ blocking read ต่อ port การตั้ง `sysctl -w net.core.busy_read=50` น่าจะเปิด busy polling ให้ thread `dds.udp.*` ได้**โดยไม่แก้โค้ด middleware** แลกกับ CPU หนึ่ง core ต่อ thread ที่กำลังรอ (ข้อสรุปจากโค้ด; ยังไม่ได้ทดลอง ดู R7)

### 5.7 ข้อเท็จจริงเฉพาะ driver `r8169` ที่กระทบผลวัด

- เส้นทางรับ**คัดลอกทุก packet**: `rtl_rx` เรียก `napi_alloc_skb(&tp->napi, pkt_size)` แล้ว `skb_copy_to_linear_data(skb, rx_buf, pkt_size)` จาก buffer DMA ขนาด 16 KiB − 1 (`R8169_RX_BUF_SIZE`) ที่จองด้วย `alloc_pages_node` ไม่ได้ใช้ page pool [V: `drivers/net/ethernet/realtek/r8169_main.c` v7.0 บรรทัด 72, 4162, 4816–4827]
- ยังเรียก `napi_gro_receive()` ซึ่งใน v7.0 เป็น `static inline` ห่อ `gro_receive_skb(&napi->gro, skb)` [V: `include/linux/netdevice.h` v7.0 บรรทัด 4251–4255; `r8169_main.c` บรรทัด 4840; kallsyms มี `gro_receive_skb` ไม่มี `napi_gro_receive`]
- ผลวัด latency/CPU บน r8169 จึงรวม copy เพิ่มหนึ่งรอบและ coalescing 20 µs ซึ่ง NIC ระดับ server (เช่นที่ใช้ page pool) ไม่มี ไม่ควรนำตัวเลขไปเทียบข้าม driver โดยตรง

---

## 6. แบบจำลอง latency / CPU / memory bandwidth

**ทุกตัวเลขในหัวข้อนี้เป็นประมาณการ** ไม่ใช่ผลวัด ใช้เพื่อบอกว่าช่วงใดน่าจะเป็นคอขวดและควรวางเครื่องมือวัดตรงไหน สมมติฐานของแบบจำลอง: CPU desktop รุ่นปัจจุบันที่ความถี่คงที่, 1 GbE, MTU 1500, Fast DDS UDP (ไม่ใช้ SHM), sync publish, kernel ไม่ใช่ RT, ระบบว่าง

> **ผลวัดจริง:** latency end-to-end ที่วัดแล้ว (rclpy, Docker `veth` และ SHM, 30 รอบต่อ config, p99 พร้อม 95% CI) อยู่ใน[ภาค 3 §7.1](03_wire_experiments.md#71-latency-end-to-end-ที่วัดจริงด้วย-rclpy-การทดลองที่-8) ตารางข้างล่างวางคู่กับประมาณการเท่าที่มีกรณีใกล้เคียงกัน **ไม่ใช่การเทียบแบบเดียวกัน**: ประมาณการคิดสำหรับ C++ ข้ามเครื่องจริงบน 1 GbE ส่วนผลวัดผ่าน rclpy (รวม Python ทั้งสองฝั่ง) บน `veth` ในเครื่องเดียว (ไม่มีเวลาบนสาย ไม่มี NIC/driver) จึงควรอ่านผลวัดของข้อความเล็กเป็นขอบบนคร่าวๆ ที่ถูกครอบงำด้วย rclpy และผลวัดของภาพเป็นกรณีที่ขาดเวลาบนสาย 7.68 ms ไป ตัวเลขประมาณการในหัวข้อนี้ไม่ได้แก้ตามผลวัด
>
> | กรณี | ประมาณการ (หัวข้อนี้) | วัดจริง (ภาค 3 §7.1) median / p99 [95% CI] |
> |---|---|---|
> | ข้อความเล็ก ข้ามเครื่อง/ข้าม container | ≈ 15–150 µs (§6.1, C++, 1 GbE, CDR ≈ 100 B) | 754 [738–767] / 879 [862–894] µs (`small_cross`: `std_msgs/String` 64 ตัวอักษร, rclpy, `veth`) |
> | ภาพ 640×480 rgb8 ข้ามเครื่อง/ข้าม container | ≈ 9–11 ms (§6.2, ในนั้นเป็นเวลาบนสาย 7.68 ms) | 7.76 [7.72–7.80] / 8.28 [8.15–8.39] ms (`image_cross_rel`, rclpy, `veth`, RELIABLE, 10 Hz) |

ค่าพื้นฐานที่ใช้ (ทั้งหมด [K] ระดับ order of magnitude)

| สัญลักษณ์ | ค่า | เหตุผล |
|---|---|---|
| `B_copy` | ≈ 10 GB/s | memcpy ของ buffer ที่ใหญ่กว่า L2 บน DDR4/DDR5 single thread; buffer เล็กใน L1 เร็วกว่านี้หลายเท่า |
| `B_csum` | ≈ 5–10 GB/s | copy พร้อมคำนวณ checksum |
| `t_sys` | ≈ 0.1–0.3 µs | เข้า-ออก syscall เปล่า (รวม mitigation) |
| `t_pkt_tx` | ≈ 0.5–1.5 µs/packet | UDP → IP → qdisc → driver ต่อ skb |
| `t_pkt_rx` | ≈ 0.5–2 µs/packet | driver poll → GRO → IP → UDP enqueue ต่อ skb |
| `t_wake` | ≈ 2–50 µs | ขึ้นกับ C-state ของ CPU ปลายทาง; idle ลึกอาจเกิน 100 µs |
| wire | 8 ns/byte ที่ 1 GbE | |

### 6.1 ข้อความเล็ก: CDR ≈ 100 B (frame ≈ 206–282 B ตาม build)

| # | ช่วง | ประมาณการ | เหตุผล | วัดด้วย |
|---|---|---|---|---|
| 1 | serialize | 0.1–0.5 µs | field ไม่กี่ตัว + memcpy 100 B | `rclcpp_publish` → `rmw_publish` (ros2_tracing) |
| 2 | Fast DDS writer + ประกอบ message | 1–5 µs | lock ของ history, เพิ่ม change, RTPSMessageGroup | `rmw_publish` → `sys_enter_sendmsg` |
| 3 | `setsockopt(SO_SNDTIMEO)` | 0.2–0.5 µs | syscall เพิ่มตามหัวข้อ 3.1 | `syscalls:sys_enter_setsockopt` |
| 4 | `sendmsg` ถึง driver | 1–3 µs | `t_sys` + `t_pkt_tx` + copy 200 B | `sys_enter_sendmsg` → `net:net_dev_xmit` |
| 5 | สาย + switch | 2–2.5 µs + store-and-forward | 230–306 byte-time × 8 ns; switch เพิ่มอย่างน้อยหนึ่ง frame time | timestamp ของ NIC หรือ capture สองจุด |
| 6 | IRQ → softirq → socket | 2–25 µs | `t_pkt_rx` + coalescing 0–20 µs (r8169) | `irq:irq_handler_entry` → `sock:sk_data_ready` |
| 7 | ปลุก `dds.udp.*` | 2–50 µs | `t_wake` | `sched:sched_waking` → `sched:sched_switch` |
| 8 | `recvmsg` + parse RTPS + เข้า history | 1–5 µs | | `sys_exit_recvmsg` → `rmw_take` |
| 9 | ปลุก executor | 2–50 µs | `t_wake` ครั้งที่สอง | `sched:*` กรองตาม tid |
| 10 | take + deserialize | 0.5–2 µs | | `rmw_take` → `callback_start` |
| | **รวม** | **≈ 15–150 µs** | ผลรวมขอบล่างและขอบบน | `rclcpp_publish` → `callback_start` ข้ามเครื่อง (ต้อง sync นาฬิกา) |

ข้อสรุปของแบบจำลอง: สำหรับข้อความเล็ก wakeup สองครั้ง (ข้อ 7, 9) และ coalescing (ข้อ 6) กินสัดส่วนมากที่สุด การ serialize และ copy แทบไม่มีผล มาตรการที่ควรทดลองจึงเป็น busy polling, affinity, C-state และ executor แบบ event ไม่ใช่ zero-copy

### 6.2 ข้อความใหญ่: ภาพ 921 652 B (15 DATA_FRAG, 635 frame)

| # | ช่วง | ประมาณการ | เหตุผล |
|---|---|---|---|
| 1 | serialize | ≈ 90–150 µs | copy 0.92 MB ที่ `B_copy` (อาจเร็วกว่าถ้าต้นทางอยู่ใน cache) |
| 2 | `sendmsg` × 15 | ≈ 0.5–1.2 ms | ต่อ datagram: copy + checksum 65 KB (7–13 µs) + จอง 45 skb + `t_pkt_tx` × 45 (22–68 µs) |
| 3 | สาย | **7.68 ms** | คำนวณในหัวข้อ 2.4; ผู้ส่งถูก back-pressure ที่ qdisc/driver เพราะสร้าง packet ได้เร็วกว่าสาย |
| 4 | softirq รับ 635 frame | ≈ 0.4–1.5 ms | `t_pkt_rx` × 635 + copy ใน r8169 (0.92 MB ≈ 90 µs) + reassembly |
| 5 | `recvmsg` × 15 | ≈ 0.1–0.2 ms | copy 0.92 MB + เดิน frag list |
| 6 | Fast DDS ประกอบ fragment | ≈ 0.1 ms | memcpy 0.92 MB ลง CacheChange |
| 7 | wakeup | ≈ 0.01–0.1 ms | เหมือนข้อความเล็ก ไม่มีนัยสำคัญที่ขนาดนี้ |
| 8 | deserialize | ≈ 0.1–0.4 ms | copy 0.92 MB + จองหน่วยความจำ; ถ้า allocator ขอ page ใหม่จะมี page fault ราว 225 ครั้ง |
| | **รวม** | **≈ 9–11 ms** | ช่วง 2–5 ซ้อนทับกับช่วง 3 บางส่วน จึงไม่ใช่ผลบวกตรง |

ข้อสรุปของแบบจำลอง: ที่ 1 GbE **เวลาบนสายคิดเป็นราว 70–85%** ของ latency ภาพเดี่ยว การลด copy จึงช่วย latency ได้น้อย แต่ช่วย CPU และ cache ที่ 10 GbE สัดส่วนกลับด้าน (สาย 0.77 ms) และต้นทุนต่อ packet กับ copy กลายเป็นคอขวด

### 6.3 แบบจำลอง copy และ memory bandwidth

**จำนวนรอบที่ payload ถูกแตะด้วย CPU** บนเส้นทาง Fast DDS UDP ข้ามเครื่อง

| # | รอบ | สถานะ |
|---|---|---|
| 1 | serialize: message → payload ใน history pool | [K] |
| 2 | `sendmsg`: user → skb พร้อม checksum | [V: `ip_generic_getfrag`] |
| 3 | driver RX: buffer DMA → skb (เฉพาะ r8169) | [V: `rtl_rx`] |
| 4 | `recvmsg`: skb → buffer ของ `dds.udp.*` | [V: ภาค 1 ตรวจชื่อฟังก์ชันแล้ว] |
| 5 | ประกอบ fragment: buffer รับ → CacheChange (เฉพาะข้อความที่ถูก fragment) | [V: `CacheChange.hpp` `add_fragments` ใช้ `memcpy`] |
| 6 | deserialize: payload → message | [K] |

ขั้น gather send (หัวข้อ 3.1 ข้อ 3) ไม่เพิ่มรอบ copy ใน user space เทียบกับภาค 1 ซึ่งนับ 4 รอบสำหรับข้อความที่ไม่ fragment (ไม่นับ DMA) ข้อความใหญ่บน r8169 จึงมี **6 รอบ**

**สูตร**

```
ปริมาณ copy ต่อวินาที   C = N_copy × S × f
ภาระบน memory bus      ≈ 2 × C          (อ่านต้นทาง + เขียนปลายทาง; มากกว่านี้ถ้ามี read-for-ownership)
สัดส่วน CPU ที่ใช้ copy  ≈ C / B_copy     (ของหนึ่ง core)
```

| กรณี | S | f | N_copy | C | สัดส่วนของ core ที่ `B_copy` = 10 GB/s |
|---|---|---|---|---|---|
| VGA rgb8 | 0.92 MB | 30 Hz | 6 | 166 MB/s | 1.7% |
| 1080p rgb8 | 6.2 MB | 30 Hz | 6 | 1.1 GB/s | 11% |
| 4K rgb8 | 24.9 MB | 30 Hz | 6 | 4.5 GB/s | 45% |
| point cloud 2 MB | 2 MB | 10 Hz | 6 | 120 MB/s | 1.2% |

(คำนวณจากสูตร; `B_copy` เป็น [K])

ข้อสังเกตเพิ่มเติมที่แบบจำลองเชิงเส้นไม่ครอบคลุม
- เมื่อ S ใหญ่กว่า L2 ต่อ core (1.25 MiB บน i3-12100: L2 รวม 5 MiB / 4 core [V: `lscpu`]) ทุกรอบ copy ไล่ข้อมูลของ thread นั้นออกจาก L2 ทำให้โค้ดหลัง copy ช้าลงด้วย
- copy แต่ละรอบเกิดบน thread และอาจคนละ core (ผู้ส่ง, softirq, `dds.udp.*`, executor) ต้นทุนจึงกระจาย ไม่รวมอยู่ใน core เดียว
- ที่ 4K 30 Hz เวลาบนสาย 1 GbE (≈ 207 ms ต่อภาพ) เกินคาบ 33 ms ไปแล้ว copy จึงไม่ใช่ข้อจำกัดแรก

### 6.4 แผนวัดให้ครบทุกช่วง

tracepoint ของ ros2_tracing ที่ยืนยันว่ามีใน branch `lyrical` [V: `tracetools/include/tracetools/tp_call.h`]: `rclcpp_publish`, `rcl_publish`, `rmw_publish`, `rmw_take`, `rcl_take`, `rclcpp_take`, `callback_start`, `callback_end`, `rclcpp_executor_execute` และ rmw ทั้งสองตัวเรียก `TRACETOOLS_TRACEPOINT(rmw_publish, …)` ก่อนส่ง [V: `rmw_fastrtps_shared_cpp/src/rmw_publish.cpp`, `rmw_zenoh_cpp/src/detail/rmw_publisher_data.cpp`]

| ช่วง | จุดเริ่ม | จุดจบ |
|---|---|---|
| user → rmw | `ros2:rclcpp_publish` | `ros2:rmw_publish` |
| rmw → kernel | `ros2:rmw_publish` | `syscalls:sys_enter_sendmsg` |
| kernel TX | `syscalls:sys_enter_sendmsg` | `net:net_dev_xmit` |
| สาย | `net:net_dev_xmit` (เครื่อง A) | `net:netif_receive_skb` (เครื่อง B) ต้องใช้ PTP หรือ hardware timestamp |
| kernel RX | `net:netif_receive_skb` | `sock:sk_data_ready` |
| wakeup 1 | `sched:sched_waking` (ปลายทาง `dds.udp.*`) | `sched:sched_switch` เข้า thread นั้น |
| middleware RX | `syscalls:sys_exit_recvmsg` | `ros2:rmw_take` |
| wakeup 2 + executor | `sched:sched_waking` (ปลายทาง executor) | `ros2:callback_start` |
| การทิ้ง | `skb:kfree_skb` (reason), `sock:sock_rcvqueue_full`, `udp:udp_fail_queue_rcv_skb`, kprobe `ip_expire`, `/proc/net/softnet_stat`, `nstat` | |

kernel tracepoint ในตาราง [V: `__traceiter_net_dev_xmit`, `netif_receive_skb`, `sk_data_ready`, `sock_rcvqueue_full`, `udp_fail_queue_rcv_skb`, `kfree_skb`, `napi_poll`, `sched_waking`, `sched_wakeup`, `sched_switch` มีใน kallsyms]

การจับคู่ event ของ packet เดียวกันข้ามชั้น: ใช้ `writerSN` ของ RTPS (offset คงที่ใน DATA/DATA_FRAG ตามหัวข้อ 2.2) หรือ sequence number ใน attachment ของ rmw_zenoh (8 byte แรก) เป็น key ร่วมระหว่าง user-space trace กับ eBPF ที่อ่าน payload ของ skb (แนวทาง; ยังไม่ได้ทำ)

### 6.5 ระเบียบวิธีวัด: clock sync และ trace จริงหนึ่ง sample

หัวข้อนี้มีสองส่วน ส่วนแรกเป็น **protocol** สำหรับวัด latency ทางเดียวข้ามสองเครื่อง (ยังไม่ได้รันบน 2 เครื่อง ต่อยอดข้อ 10 ของ[ภาค 3 §8.2](03_wire_experiments.md#82-protocol-สำหรับ-2-เครื่องจริง-ยังไม่ได้รัน) และหมายเหตุ two-host ใน `run_latency.sh --help`) ส่วนที่สอง (ฉ.–ช.) ชี้ไปยัง trace จริงหนึ่ง sample ใน[ภาค 3 §7.2](03_wire_experiments.md#72-trace-หนึ่ง-sample-ข้ามชั้น-การทดลองที่-17) และช่วงที่ยังต้องใช้ kernel tracing

#### ก. นาฬิกาที่เครื่องมือแต่ละตัวในชุดนี้อ่าน

| เครื่องมือ | นาฬิกา | หมายเหตุ |
|---|---|---|
| `lat_pub.py` / `lat_sub.py` | `--clock monotonic` (default) หรือ `--clock realtime` [V: `lat_pub.py` บรรทัด 36, `lat_sub.py` บรรทัด 31] | ข้ามเครื่องต้องใช้ `realtime` ที่ sync แล้ว: CLOCK_MONOTONIC ของสองเครื่องมีจุดเริ่มต่างกัน (นับจาก boot) เทียบกันไม่ได้ |
| tcpdump / tshark | CLOCK_REALTIME ของ kernel ตอน packet ผ่าน tap [K]; ความละเอียด µs เป็น default ต้องสั่ง `--time-stamp-precision=nano` ถ้าต้องการ ns | `-j adapter_unsynced` / `adapter` ใช้ hardware timestamp ของ NIC ได้เฉพาะเมื่อ `tcpdump -J -i <if>` แสดงชนิดนั้น บน veth ของการทดลองนี้มีแค่ `host` [V: `trace_env.txt`] |
| LTTng-UST (ros2_tracing) | CLOCK_MONOTONIC เป็น cycle (ns) + `offset` ใน metadata ที่ใช้แปลงเป็น realtime [V: metadata ของ trace ภาค 3 §7.2 `clock { name = "monotonic"; freq = 1000000000; offset = ... }`] | babeltrace2 แสดงเป็น realtime โดย default (`--clock-cycles` แสดงค่าดิบ) offset ถูกบันทึกตอนสร้าง session จึงผิดได้ถ้า realtime ถูก **step** ระหว่างนั้น |
| `rmw_publish.timestamp` / `rmw_take.source_timestamp` / RTPS INFO_TS | CLOCK_REALTIME ของผู้ส่ง (source timestamp) [V: ค่าเดียวกันทั้งสามที่ใน ภาค 3 §7.2.1] | ใช้เป็น key จับคู่ข้ามชั้นได้ และถ้านาฬิกา sync แล้วใช้คำนวณ latency ทางเดียวได้โดยไม่ต้องแก้แอป |

ข้อควรระวัง [K]: (1) การปรับ realtime แบบ **slew** (chrony/NTP ปรับความถี่) มีผลกับ CLOCK_MONOTONIC ด้วย แต่การ **step** (`chronyc makestep`, ตั้งเวลาใหม่, leap second) เปลี่ยนเฉพาะ realtime จึงทำให้ offset monotonic→realtime ที่ LTTng บันทึกไว้ผิด ควรตรวจว่าไม่มี step ระหว่าง run (ดู `chronyc tracking` "Last offset" และ log ของ chrony) (2) container บนเครื่องเดียวกันใช้นาฬิกาของ kernel host ร่วมกัน (ไม่มี time namespace ใน `docker run` ปกติ) การทดลองบน veth จึงไม่ต้อง sync แต่ก็**ไม่ได้ทดสอบ**ปัญหานาฬิกาเลย (3) CLOCK_REALTIME ระหว่างสองเครื่องต่างกันด้วย offset + drift ซึ่งเปลี่ยนตามเวลาและอุณหภูมิ ต้องวัดก่อนและหลังทุก run ไม่ใช่ครั้งเดียว

#### ข. สถานะของเครื่องที่ใช้ทดลอง (อ่านอย่างเดียว 2026-11-27) [V: `trace_host_clock_state.txt`]

- NIC `enp2s0` (driver `r8169` ตาม[§5.7](#57-ข้อเท็จจริงเฉพาะ-driver-r8169-ที่กระทบผลวัด)) `ethtool -T`: `software-transmit`, `software-receive`, `software-system-clock`, **`PTP Hardware Clock: none`**, hardware transmit/receive modes `none` จึง**ทำ PTP แบบ hardware timestamping ไม่ได้** ได้แค่ PTP แบบ software (`ptp4l -S`) ไม่มี `/dev/ptp*`
- นาฬิกาซิงก์ด้วย chrony กับ NTP server สาธารณะผ่าน internet (stratum 3, root delay 186 ms) `chronyc tracking`: System time ช้ากว่า NTP 1.04 ms, RMS offset 367 µs, update interval ราว 1027 s ความแม่นระดับนี้ใช้วัด latency ระดับร้อย µs ข้ามเครื่องไม่ได้
- ไม่มี linuxptp (`ptp4l`, `phc2sys`, `pmc`) ติดตั้งบน host, clocksource `tsc`

#### ค. Protocol: chrony บน LAN (เมื่อ NIC ไม่มี hardware timestamp)

ความแม่นที่คาดได้ [K]: chrony กับ server บน LAN เดียวกันที่ใช้ software timestamp ได้ offset ระดับสิบถึงร้อย µs; ถ้าทั้งสองฝั่งเปิด kernel/hardware timestamping ของ NTP (`hwtimestamp`) ได้ต่ำลงระดับ µs เดียว ตัวเลขนี้ต้องยืนยันด้วยขั้นตอนตรวจข้างล่างทุกครั้ง ไม่ควรอ้างจากเอกสาร

1. เลือกเครื่องหนึ่งเป็น server (หรือใช้ server ของ LAN) อีกเครื่องเป็น client ไม่ใช้ server บน internet ระหว่างการวัด
2. server `/etc/chrony/chrony.conf`: `local stratum 8` และ `allow <subnet ของ LAN>`; client: `server <ip server> iburst minpoll 0 maxpoll 0 xleave` และ `hwtimestamp *` (ถ้าไม่มี hardware timestamp chrony จะถอยไปใช้ kernel software timestamp เอง) แล้ว `sudo systemctl restart chrony` ทั้งสองเครื่อง (เป็นการแก้ host: ผู้ใช้ทำเอง)
3. รอให้ลู่เข้า (อย่างน้อยหลายสิบ poll) จนค่า `chronyc sourcestats` คอลัมน์ `Std Dev` คงที่
4. **ก่อนและหลังทุก run** บันทึก `chronyc tracking` (System time, RMS offset, Skew) และ `chronyc sourcestats -v` ลงไฟล์ env ของ run

#### ง. Protocol: linuxptp (เมื่อ NIC มี hardware timestamp)

1. ตรวจ `ethtool -T <if>` ทั้งสองเครื่อง: ต้องมี `hardware-transmit`, `hardware-receive`, `hardware-raw-clock` และ `PTP Hardware Clock: <n>` (ไม่ใช่ `none`) และ `Hardware Receive Filter Modes` ที่รับ PTP ได้ (`ptpv2-event` หรือ `all`) ถ้ามีแค่ `software-transmit`/`software-receive` (เช่น r8169 ข้างบน) ใช้ได้เพียง `ptp4l -S` ซึ่งไม่ดีกว่า chrony มากนัก
2. ทั้งสองเครื่อง: `sudo ptp4l -i <if> -m -H` (เครื่องหนึ่งจะเป็น grandmaster ตาม BMCA; บังคับให้อีกเครื่องเป็น slave ด้วย `-s`) แล้ว `sudo phc2sys -s <if> -c CLOCK_REALTIME -w -m` เพื่อปรับนาฬิการะบบตาม PHC ปิด chrony/timesyncd ระหว่างนั้นเพื่อไม่ให้แย่งกันปรับ
3. ตรวจ: log ของ `ptp4l` บรรทัด `master offset <ns> s2 freq ...` (state `s2` = locked) และของ `phc2sys` บรรทัด `CLOCK_REALTIME phc offset <ns>`; query สถานะด้วย `sudo pmc -u -b 0 'GET CURRENT_DATA_SET'` (`offsetFromMaster`, `meanPathDelay`) และ `'GET TIME_STATUS_NP'`
4. บันทึกก่อนและหลังทุก run: ค่าสูงสุดของ |master offset| และ |phc offset| ใน 60 s ก่อนเริ่มและหลังจบ

#### จ. ตรวจอิสระและแปลง offset เป็นขอบเขตความไม่แน่นอน

- **ping-pong สองทาง** (ไม่ขึ้นกับ chrony/PTP): A ส่งข้อความพร้อม `t1` (realtime ของ A), B บันทึก `t2` และตอบกลับทันทีพร้อม `t3`, A บันทึก `t4` แล้ว offset ≈ ((t2 − t1) − (t4 − t3)) / 2 และ RTT = (t4 − t1) − (t3 − t2) ทำซ้ำหลายร้อยครั้ง ใช้ค่าจากคู่ที่ RTT ต่ำสุด (แบบเดียวกับ NTP) ทำได้ด้วย `lat_pub.py`/`lat_sub.py` คู่ที่สองในทิศกลับ (ต้องเพิ่ม mode echo: ยังไม่มีใน script)
- **ทดสอบความสมมาตร:** วัด latency ทางเดียว A→B และ B→A พร้อมกันด้วยนาฬิกาที่ sync แล้ว ถ้าเส้นทางสมมาตร median ของสองทิศควรใกล้กัน ผลต่างครึ่งหนึ่งเป็นตัวประมาณ offset ที่เหลือ (รวม asymmetry ของเส้นทาง ซึ่งแยกจาก offset ไม่ได้ด้วยวิธีสองทางใด ๆ)
- **ขอบเขต:** ให้ `ε` = max(|offset| ก่อน run, |offset| หลัง run, |offset จาก ping-pong|) latency ทางเดียวที่วัดได้ `L` มีความไม่แน่นอน ±`ε` (ไม่ใช่ ±`ε`/√n เพราะ offset เป็น bias ร่วมของทุก sample ไม่ใช่ noise อิสระ) รายงาน `L` คู่กับ `ε` เสมอ และตีความเฉพาะผลต่างระหว่างแขนที่มากกว่า 2`ε` หรือแขนที่วัดในช่วงเวลาสลับกันภายใต้ offset เดียวกัน
- **บันทึกในไฟล์ env** (เพิ่มจากรายการ ก. ของ[ภาค 3 §8.2](03_wire_experiments.md#82-protocol-สำหรับ-2-เครื่องจริง-ยังไม่ได้รัน)): วิธี sync (chrony/PTP HW/PTP SW), `ethtool -T` ของทั้งสองเครื่อง, output ของ `chronyc tracking`/`sourcestats` หรือ `pmc` ก่อนและหลัง, ผล ping-pong (offset, RTT ต่ำสุด), `ε` ที่ใช้, clock ที่แต่ละเครื่องมือใช้ (`--clock`, `--time-stamp-precision`, `tcpdump -J`) และ clocksource ของ kernel

#### ฉ. trace จริงหนึ่ง sample (การทดลองที่ 17) เทียบกับ §6.1

trace หนึ่ง sample ข้ามชั้นโดยไม่ใช้สิทธิ์ host (LTTng-UST ใน container + tcpdump สองฝั่ง จับคู่ด้วย source timestamp) อยู่ใน[ภาค 3 §7.2](03_wire_experiments.md#72-trace-หนึ่ง-sample-ข้ามชั้น-การทดลองที่-17) และตารางเทียบรายแถวกับ §6.1 อยู่ใน[ภาค 3 §7.2.4](03_wire_experiments.md#724-เทียบกับแบบจำลอง-latency-ของภาค-2-61) โดยย่อ: ชั้น rclcpp/rcl/rmw ที่ ros2_tracing เห็นรวมกันราว 10 µs ส่วนเวลาที่เหลือกว่า 90% อยู่ในสองช่วงที่ต้องใช้ kernel tracing ข้อสรุปของ §6.1 เรื่อง wakeup และ coalescing จึงยังไม่ได้รับการยืนยันหรือปฏิเสธ

#### ช. ช่วงที่ยังไม่ได้สังเกต และเงื่อนไขบน host (protocol)

ช่วงที่ยังมองไม่เห็น: `rmw_publish` → `sys_enter_sendmsg` → `net:net_dev_xmit` (ฝั่งส่ง), `net:netif_receive_skb` → `sock:sk_data_ready` → `sched_waking`/`sched_switch` ของ `dds.udp.*` → `sys_exit_recvmsg` → การปลุก executor (ฝั่งรับ) ตามตาราง §6.4

สถานะของเครื่องนี้ [V: `trace_env.txt`, ตรวจแบบอ่านอย่างเดียว]: `kernel.perf_event_paranoid` = 4 (ค่าเฉพาะของ Ubuntu: ผู้ใช้ทั่วไปใช้ `perf_event_open` ไม่ได้เลย [K]), `kernel.unprivileged_bpf_disabled` = 2, `kernel.kptr_restrict` = 1, tracefs (`/sys/kernel/tracing`) อ่านไม่ได้, ไม่มี LTTng kernel module (`lttng-modules`) สำหรับ kernel 7.0.0-44, มี `bpftrace` และ `perf` บน host

เงื่อนไขที่**ผู้ใช้**ต้องทำเอง (ไม่มี script ใดในชุดนี้ทำให้) แล้วจึงเติมช่วงที่เหลือได้:

1. ทางที่ง่ายที่สุด: รัน `bpftrace` ด้วย `sudo` บน host (ใช้ได้กับ container เพราะ kernel เดียวกัน) ด้วย one-liner ใน[ภาค 1 §5.5](01_network_stack_deep_dive.md#55-เส้นทางใน-linux-kernel-ทีละฟังก์ชัน-tx-และ-rx) และ tracepoint ในตาราง §6.4 พร้อมกับ `run_trace.sh` โดยกรองด้วย `comm` (`talker`, `listener`, `dds.udp.*`) และพิมพ์ `nsecs` (CLOCK_MONOTONIC) ซึ่งเทียบกับ cycle ดิบของ LTTng ได้โดยตรงโดยไม่ต้องใช้ offset
2. หรือ `sudo perf record -e 'syscalls:sys_enter_sendmsg,net:net_dev_xmit,net:netif_receive_skb,sock:sk_data_ready,sched:sched_waking,sched:sched_switch' -a -k CLOCK_MONOTONIC` ระหว่าง run (`-k` ให้ perf ใช้ monotonic แบบเดียวกับ LTTng)
3. หรือติดตั้ง `lttng-modules-dkms` บน host แล้วใช้ `lttng enable-event -k ...` จาก session บน host (session ใน container โหลด module ไม่ได้และไม่ควรได้)
4. ทางที่ต้องลดความปลอดภัยของ host ชั่วคราว (ไม่แนะนำบนเครื่องที่ใช้ร่วมกัน): `sudo sysctl kernel.perf_event_paranoid=-1` (หรือให้ capability `CAP_PERFMON`/`CAP_BPF` เฉพาะ binary) แล้วคืนค่าเดิมหลังวัด

key ร่วมระหว่าง kernel trace กับ user trace: วิธีที่เสนอใน §6.4 (อ่าน `writerSN` จาก payload ของ skb) ใช้ได้ หรือใช้ source timestamp (INFO_TS อยู่ที่ offset คงที่ของ RTPS message ที่ Fast DDS สร้าง) ซึ่งตรงกับ field ใน `rmw_publish`/`rmw_take` อยู่แล้ว

### 6.6 Template การทดลอง: ตัวแปร เครื่องมือ และแนวปฏิบัติ

จุดวัดรายช่วงอยู่ใน §6.4 ส่วนนาฬิกาและขอบเขตความไม่แน่นอนอยู่ใน §6.5 หัวข้อนี้รวม template การทดลองที่ย้ายมาจาก §8 ของภาค 1 เพื่อให้ระเบียบวิธีอยู่ที่เดียว

**ตัวแปรอิสระ**: RMW × transport (UDP / SHM / Buffer backend) × payload size × QoS (reliability, history depth) × executor × kernel (generic / PREEMPT_RT) × จำนวน subscriber

**ตัวแปรตาม**: end-to-end latency (ใช้ timestamp จาก ros2_tracing: `rclcpp_publish` → `rmw_publish` → `rmw_take` → `callback_start` แยกรายช่วงต่อตาม §6.4), jitter, throughput, CPU (%/core), memory, message loss, discovery time

**เครื่องมือ**
- Benchmark: `apex.ai performance_test`, `irobot ros2-performance` (ตรวจว่ารองรับ Lyrical หรือยัง)
- Tracing: `ros2_tracing` + `tracetools_analysis`; ฝั่ง kernel ใช้ LTTng kernel events (`net_dev_xmit`, `netif_receive_skb`, `sched_switch`) หรือ tracepoint ชุดเดียวกันผ่าน `bpftrace`/`perf` ตามตาราง §6.4 (ต้องมีสิทธิ์บน host ตาม §6.5 ช.)
- Kernel: `bpftrace`, `perf sched`, `nstat`
- Packet: Wireshark (มี dissector สำหรับ RTPS; Zenoh มี dissector แยก)

**แนวปฏิบัติ**: ปิด CPU frequency scaling (`performance` governor), isolate core (`isolcpus`, `nohz_full`), ทำซ้ำ ≥30 รอบ, รายงาน p99/p99.9 ไม่ใช่แค่ค่าเฉลี่ย, ระบุเวอร์ชัน (`ros2 doctor --report` ใน Lyrical รายงาน env ได้ด้วย) และเมื่อวัดทางเดียวข้ามเครื่องให้รายงานขอบเขต offset ของนาฬิกาคู่กับผลตาม §6.5 จ.

ตัวอย่างสลับ RMW ระหว่างการทดลอง:
```bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp   # | rmw_cyclonedds_cpp | rmw_zenoh_cpp | rmw_connextdds
export FASTDDS_BUILTIN_TRANSPORTS=UDPv4       # บังคับไม่ใช้ SHM เพื่อวัด kernel path
# Zenoh + SHM
ros2 run rmw_zenoh_cpp rmw_zenohd &
export ZENOH_CONFIG_OVERRIDE='transport/shared_memory/enabled=true'
```

---

## 7. ทิศทางวิจัยที่ตามมาโดยตรงจากหัวข้อ 1–6

ทุกข้อเป็นข้อเสนอ งานที่เกี่ยวข้องเบื้องต้นของแต่ละข้ออยู่ใน[หัวข้อ 7.1](#71-งานที่เกี่ยวข้องของ-r1r9-ฉบับร่าง) (ตรวจเพียงระดับชื่อเรื่องและบทคัดย่อ ยังไม่ได้ยืนยันว่าไม่มีใครทำหัวข้อเดียวกันแล้ว)

ข้อเสนอ 7 ข้อที่ย้ายมาจากภาค 1 §7 (จับคู่กับ R1–R9 และข้อที่ไม่มีคู่เสนอเป็น R10–R13) อยู่ใน[หัวข้อ 7.4](#74-ข้อเสนอเพิ่มเติมจากภาค-1-นอก-r1r9) ข้อจำกัดด้านความตรงของแต่ละข้ออยู่ใน[หัวข้อ 7.2](#72-ข้อจำกัดด้านความตรง-threats-to-validity-ของ-r1r9) และแผนสู่ paper ของ R4 และ R2 ใน[หัวข้อ 7.3](#73-เส้นทางสู่-paper-แผนสำหรับ-r4-และ-r2-แผน-ยังไม่ได้ทำ)

**R1. RTPS fragment ขนาดไม่เกิน MTU ร่วมกับ UDP GSO/GRO** (จาก 2.4, 2.5, 5.2)
- สมมติฐาน: ตั้ง fragment ระดับ RTPS ≈ 1 400 B แล้วส่งเป็นชุดด้วย `UDP_SEGMENT` (สูงสุด 128 segment ต่อ syscall) จะ (ก) ลดตัวขยายการส่งซ้ำจาก 45 เหลือ 1 (ข) เลิกพึ่ง IP reassembly (ค) ได้ checksum offload คืน โดยต้นทุน syscall ต่อ byte ไม่แย่กว่า datagram 65 KB
- วัด: goodput และ p99 latency ของภาพ 0.9/6.2/24.9 MB ที่ loss 0, 0.01, 0.1, 1% (ฉีดด้วย `tc netem`) เทียบ 3 แบบ: default 65 KB, fragment เล็กโดยไม่มี GSO (ทำได้ทันทีด้วย `maxMessageSize` หรือ flow controller ตามหัวข้อ 3.6), fragment เล็ก + GSO (ต้องแก้ `UDPTransportInterface::send`) นับ `ReasmFails`, DATA_FRAG ที่ส่งซ้ำ, CPU ต่อ MB
- ข้อควรระวัง: bitmap ของ NACK_FRAG จำกัด 256 บิต ภาพ 0.92 MB จะมีราว 660 fragment ต้องใช้หลาย NACK_FRAG

**R2. เวลากู้คืนของ RELIABLE ถูกกำหนดด้วย `heartbeat_period` หรือไม่** (จาก 2.3)
- สมมติฐาน: สำหรับ topic RELIABLE ที่ history ไม่เต็ม เวลาตั้งแต่ packet หายจนได้ sample มีการกระจายกว้างถึง 3 s และลดลงเป็นสัดส่วนเมื่อลด `heartbeat_period`
- วัด: ทิ้ง packet ที่เลือกด้วย eBPF/`tc` ตาม `writerSN` บันทึกเวลาระหว่าง `rmw_publish` กับ `callback_start` ของ SN นั้น แปรค่า `heartbeat_period` (3 s, 500 ms, 100 ms, 20 ms), อัตราส่ง, history depth และนับ HEARTBEAT/ACKNACK ต่อวินาทีเป็นต้นทุน

**R3. ผลของ build option ต่อ overhead บนสาย** (จาก 3.7)
- สมมติฐาน: `FASTDDS_STATISTICS=ON` เพิ่ม 60 B ต่อ datagram ซึ่งเป็น 30–40% ของ frame สำหรับข้อความเล็ก และเพิ่มงานต่อ send (ค้น locator ใน collection) แต่ไม่มีผลวัดได้กับข้อความใหญ่
- สิ่งที่ทำแล้ว: capture ใน[ภาค 3](03_wire_experiments.md) ยืนยันว่า binary `.deb` ของ Lyrical ส่ง RTPS 2.3 และมี statistics submessage 60 B ในทุก RTPS message (คือ build แบบ `SECURITY=ON`, `FASTDDS_STATISTICS=ON`) ใน frame `"Hello World: 1"` 198 B ส่วนนี้คิดเป็น 60/198 ≈ 30%
- วัด (ยังไม่ได้ทำ): build Fast DDS แบบ `FASTDDS_STATISTICS=OFF` เพิ่ม แล้วเทียบ throughput และ CPU ต่อ send ของข้อความ 16–256 B ที่อัตราสูงระหว่างสอง build

**R4. ขนาด socket buffer ขั้นต่ำเชิงทฤษฎีจาก `truesize`** (จาก 5.3)
- สมมติฐาน: อัตราทิ้งที่ socket ของภาพขนาด S ทำนายได้จากแบบจำลอง `sk_rcvbuf / (truesize ต่อ datagram)` กับการกระจายของเวลาที่ `dds.udp.*` ถูกหน่วง และค่า `SO_RCVBUF` ที่พอดีคือ (จำนวน DATA_FRAG ต่อ sample × truesize ต่อ datagram × จำนวน sample ที่ต้องการรองรับ)
- วัด: histogram ของ `skb->truesize` ที่ `__udp_enqueue_schedule_skb` แยกตาม driver (r8169 เทียบ NIC ที่ใช้ page pool), `sock:sock_rcvqueue_full`, scheduling delay ของ `dds.udp.*` จาก `perf sched timehist`, แปร `rmem_default` ตั้งแต่ 208 KiB ถึง 32 MiB

**R5. SHM transport กับข้อความที่ใหญ่กว่า segment** (จาก 3.4)
- สมมติฐาน: ที่ค่า default (segment 512 KiB, `maxMessageSize` 65 500) การส่งข้อความ > 512 KiB ผ่าน SHM มีการทิ้ง fragment แบบเงียบเมื่อผู้รับช้า และ latency ไม่ดีกว่า UDP loopback อย่างที่คาด เพราะยัง fragment และ copy เท่าเดิม
- วัด: latency, loss และ `overflows_count` (มี log ตอนปิด segment) ของข้อความ 64 KiB–32 MiB เทียบ 4 แบบ: SHM default, SHM ที่ขยาย `segment_size` และ `maxMessageSize`, UDP loopback, data-sharing (ต้องเปิดเองตามหัวข้อ 3.5)

**R6. ต้นทุน discovery และ graph เมื่อขยายขนาดระบบ** (จาก 1.4, 1.5, 4.3)
- สมมติฐาน: byte รวมที่ใช้ให้ graph ลู่เข้าของ DDS โตแบบกำลังสองตามจำนวน endpoint ต่อ participant (`ros_discovery_info`) และตามจำนวน participant (SEDP) ขณะที่ liveliness token ของ Zenoh โตเชิงเส้น
- วัด: นับ byte และเวลาจนกว่า `ros2 node list` ครบ สำหรับ node 10–500 ตัว จัดเป็น 1 node/process เทียบ component container ที่รวมหลาย node ใน participant เดียว แยกนับ SPDP, SEDP, `ros_discovery_info`, liveliness token

**R7. Busy polling โดยไม่แก้ middleware** (จาก 5.6, 6.1)
- สมมติฐาน: `net.core.busy_read` 50–200 µs ลด p99 latency ของข้อความเล็กบน Fast DDS UDP ได้ใกล้เคียงกับผลรวมของช่วง 6–7 ในตาราง 6.1 โดยแลกกับ CPU หนึ่ง core ต่อ port ที่ active และไม่มีผลกับ rmw_zenoh ถ้า runtime ใช้ epoll (ต้องใช้ `net.core.busy_poll` แทน)
- วัด: p50/p99/p99.9 และ CPU ต่อ thread เทียบ busy_read 0/50/200 บน kernel generic และ PREEMPT_RT ร่วมกับการปิด `gro_flush_timeout` ของ r8169

**R8. `MSG_ZEROCOPY` สำหรับ RTPS หลังทำ R1** (จาก 5.2, 6.3)
- สมมติฐาน: zero-copy TX ให้ผลเมื่อ S ≥ หลายร้อย KB และ link ≥ 10 GbE เท่านั้น ที่ 1 GbE ผลต่อ latency ต่ำกว่า 5% เพราะสายเป็นคอขวด (ตาราง 6.2) แต่ลด CPU ฝั่งส่งได้ตามสูตรในหัวข้อ 6.3
- วัด: CPU ต่อ MB และ LLC miss ฝั่งส่งด้วย `perf stat` เทียบ copy กับ zerocopy ที่ S = 64 KiB–32 MiB บน 1 และ 10 GbE; ต้องออกแบบการผูกอายุ payload กับ notification จาก error queue

**R9. ผลของ driver ต่อผล benchmark ของ ROS 2** (จาก 5.7)
- สมมติฐาน: ผลต่างระหว่าง NIC ระดับ consumer (r8169: copy ทุก packet, sw coalescing 20 µs) กับ NIC ที่ใช้ page pool มีขนาดเทียบได้กับผลต่างระหว่าง RMW ในบาง workload จึงต้องรายงาน driver และค่า coalescing ในทุก benchmark
- วัด: workload เดียวกันบน NIC สองชนิด พร้อมแปร `gro_flush_timeout`, `napi_defer_hard_irqs`, `ethtool -C`

### 7.1 งานที่เกี่ยวข้องของ R1–R9 (ฉบับร่าง)

> **สถานะ (2026-11-27):** รวบรวมจาก web search (IEEE Xplore, ACM DL, Elsevier/ScienceDirect, arXiv, LIPIcs/ECRTS, เอกสาร kernel และเอกสารทางการของ ROS 2 / Fast DDS) **ยังไม่ได้อ่านฉบับเต็มของงานใด** คำอธิบายในตารางมาจากชื่อเรื่องและบทคัดย่อเท่านั้น ตัวเลขที่ยกมาต้องตรวจกับต้นฉบับก่อนอ้างใน paper งานที่เป็น preprint บน arXiv ควรค้นซ้ำว่ามีฉบับตีพิมพ์แล้วหรือไม่ และคอลัมน์ "ช่องว่างที่ R นี้เติม" เป็นข้อสันนิษฐาน ยังไม่ได้ทำ systematic search

| R | งานที่เกี่ยวข้อง | เกี่ยวข้องอย่างไร | ช่องว่างที่ R นี้เติม (ข้อสันนิษฐาน) |
|---|---|---|---|
| R1 | [Optimizing ROS 2 Communication for Wireless Robotic Systems](https://arxiv.org/abs/2508.11366) (arXiv 2025) | ชี้ว่า DDS ไม่รู้เรื่อง IP fragmentation เสีย packet เดียวต้องส่ง RTPS message ใหม่ทั้งก้อน เสนอให้ message ≤ MTU และใช้ `LARGE_DATA` ผ่าน XML | ไม่พบว่าใช้ UDP GSO/GRO เพื่อชดเชยต้นทุน syscall ของ fragment เล็ก |
| R1 | [Poster: How to Send Large Data in ROS 2](https://ieeexplore.ieee.org/abstract/document/11192433/) (IEEE) | การส่งข้อมูลใหญ่ใน ROS 2 โดยตรง | ยังไม่ได้อ่านฉบับเต็ม ต้องตรวจว่าครอบคลุม GSO หรือไม่ |
| R1 | [QUIC is not Quick Enough over Fast Internet](https://arxiv.org/abs/2310.09423) (arXiv 2023); de Bruijn, [UDP GSO, LPC 2018 (draft)](https://webcf.waybackmachine.org/web/20200809183245/http://vger.kernel.org/lpc_net2018_talks/willemdebruijn-lpc2018-udpgso-paper-DRAFT-1.pdf) | หลักฐานจากฝั่ง QUIC ว่า GSO/GRO มีผลมากกับ throughput ของ UDP และที่มาของ `UDP_SEGMENT` | เป็นงานด้าน QUIC/HTTP3 ยังไม่ได้นำไปใช้กับ RTPS |
| R2 | [An Analytical Latency Model of the Data Distribution Service in ROS 2](https://ieeexplore.ieee.org/document/11044454/) (IEEE) | แบบจำลอง closed-form ของ latency แบบ RELIABLE รายงาน error เฉลี่ย 6.88% ใน 35 กรณี | **ใกล้ R2 มากที่สุด** ต้องอ่านว่าแยกผลของ `heartbeat_period` ไว้แล้วหรือยัง |
| R2 | [Probabilistic Latency Analysis of the DDS in ROS 2](https://arxiv.org/abs/2508.10413) (arXiv 2025) | จำลอง reliable delivery บนเครือข่ายไร้สายที่มี loss ด้วย dynamic programming โดยมี heartbeat period เป็นพารามิเตอร์ ตรวจกับ 270 กรณี | R2 วัดจาก trace ราย `writerSN` บนสายจริง ใช้ทดสอบแบบจำลองนี้ได้โดยตรง |
| R2 | [StreamRTPS](https://arxiv.org/abs/2606.14214) (arXiv 2026); [Response-time analysis ของ DDS, ECRTS 2023](https://drops.dagstuhl.de/opus/volltexte/2023/18038/pdf/LIPIcs-ECRTS-2023-9.pdf) | StreamRTPS ตรวจจับ loss ก่อนถึงรอบ heartbeat ส่วน ECRTS ให้ขอบเขต worst-case ของ latency | R2 ให้การกระจายเชิงประจักษ์เพื่อเทียบกับทั้งสองแบบ |
| R3 | [Analyzing Interoperability and Security Overhead of ROS2 DDS Middleware](https://ieeexplore.ieee.org/document/9837282/) (IEEE); [Security and Performance Considerations in ROS 2](https://arxiv.org/abs/1809.09566) (arXiv 2018) | วัด overhead ที่มาจากการตั้งค่า middleware (ด้าน security) | ไม่พบงานที่วัด overhead ของ `FASTDDS_STATISTICS` โดยเฉพาะ (ข้อสันนิษฐาน) |
| R4 | [ROS 2 DDS tuning guide](https://docs.ros.org/en/lyrical/How-To-Guides/DDS-tuning.html); [Fast DDS Large Data](https://fast-dds.docs.eprosima.com/en/latest/fastdds/use_cases/large_data/large_data.html) | แนะนำ `rmem_max` ≈ 4 MB จากการทดลองของผู้เขียน และอธิบายว่า buffer เต็มทำให้ทิ้ง packet | เป็นคำแนะนำเชิงปฏิบัติ ไม่มีแบบจำลองจาก `truesize` ที่ทำนายขนาด buffer ได้ ไม่พบงานวิชาการ |
| R5 | [ROS 2 Agnocast](https://arxiv.org/abs/2506.16882) (arXiv 2025); [Sensor-in-Memory](https://arxiv.org/abs/2510.11448) (arXiv 2025) | เทียบ zero-copy IPC กับ CycloneDDS, iceoryx, Fast DDS SHM และ Zenoh รายงานว่า latency ของ iceoryx กับ unsized type โตตามขนาดข้อความ | ไม่พบงานที่ศึกษาพฤติกรรมของ Fast DDS SHM เมื่อข้อความใหญ่กว่า segment (การทิ้งเงียบ, `overflows_count`) |
| R6 | [When Discovery Becomes a Storm](https://arxiv.org/abs/2608.02242) (arXiv 2026); [Bloom filter-based discovery for DDS](https://doi.org/10.1016/j.jpdc.2011.05.001) (JPDC 2011); [CFDP](https://www.dre.vanderbilt.edu/~schmidt/PDF/debs2014_submission_163.pdf) (DEBS 2014, venue ยังไม่ยืนยัน); [b-DDS: broker-embedded DDS](https://www.sciencedirect.com/science/article/abs/pii/S2452414X25001323) (Elsevier 2025) | แบบจำลอง discovery บนเครือข่ายไร้สาย งานลด traffic ของ SPDP/SEDP และ b-DDS ที่วัด network traffic เทียบกับ DDS มาตรฐาน | ไม่พบงานที่เทียบ DDS (รวม `ros_discovery_info`) กับ liveliness token ของ Zenoh ที่จำนวน node สูง ส่วนตัวเลขลด 97–99.9% ของ [Zenoh](https://zenoh.io/blog/2021-03-23-discovery/) เป็นตัวเลขที่ vendor วัดเอง |
| R7 | [KBP: kernel busy poll สำหรับ VM/container](https://global.ieice.org/en_transactions/communications/10.1587/transcom.2021EBT0004/_pdf) (IEICE Trans. 2022); [Understanding Host Network Stack Latency](https://dl.acm.org/doi/10.1145/3789240.3829115) (ACM SIGCOMM 2026); [The IX Operating System](https://dl.acm.org/doi/10.1145/2997641) (ACM TOCS); [Understanding Delays in AF_XDP-based Applications](https://arxiv.org/abs/2402.10513) (arXiv 2024) | busy polling ลด tail latency โดยแลกกับ CPU (SIGCOMM: p99 ≈ 19 → 14 µs ที่ CPU 100%) ส่วน IX และ AF_XDP เป็นทางเลือกที่ข้าม network stack ปกติไป | ไม่พบงานที่วัดกับ ROS 2/DDS |
| R8 | [Linux kernel: MSG_ZEROCOPY](https://docs.kernel.org/networking/msg_zerocopy.html); [High-Performance DBMSs with io_uring](https://arxiv.org/abs/2512.04859) (arXiv 2025) | เอกสาร kernel ระบุว่าคุ้มเมื่อเขียนครั้งละมากกว่าราว 10 KB เท่านั้น และไม่รับประกันว่าจะไม่ copy งาน io_uring พบว่า zero-copy receive คุ้มเมื่อข้อความเกินราว 1 KiB | ไม่พบงานที่ใช้ `MSG_ZEROCOPY` กับ RTPS |
| R9 | [Latency Analysis of ROS2 Multi-Node Systems](https://ieeexplore.ieee.org/document/9591166/) (IEEE); Maruyama et al., [Exploring the performance of ROS2](https://doi.org/10.1145/2968478.2968502) (EMSOFT 2016); [OSRF TSC RMW report: reproducing](https://osrf.github.io/TSC-RMW-Reports/humble/eclipse-cyclonedds-report/reproducing.html) | benchmark ROS 2 ที่ใช้อ้างกันทั่วไป และวิธีทำซ้ำด้วย `performance_test` | ไม่พบงานที่รายงานหรือแปร driver/NIC และค่า coalescing ว่าเป็นตัวแปรของ benchmark |

งานภาพรวมที่ควรอ้างในส่วน related work ทั่วไป: [ROS 2 in a Nutshell: A Survey](https://doi.org/10.1145/3815113) (ACM Computing Surveys, ยังไม่ได้ตรวจปีและเล่ม), [A Survey on Experimental Performance Evaluation of DDS Implementations](https://arxiv.org/abs/2310.16630) (arXiv 2023, ใช้กับการออกแบบการทดลอง RELIABLE/BEST_EFFORT), [Runtime verification of cause–effect latency in black-box systems](https://www.sciencedirect.com/science/article/pii/S0950584926001618) (Elsevier, วิธีวัด end-to-end), [ros2_tracing](https://ieeexplore.ieee.org/document/9772997/) (IEEE, เครื่องมือ trace สำหรับ R2/R7), [A Survey of Real-Time Support in ROS 2](https://arxiv.org/abs/2601.10722) (arXiv 2026), [ROS 2: Design, Architecture, and Uses In The Wild](https://arxiv.org/abs/2211.07752) และงานเทียบ middleware ([edge-to-edge/edge-to-cloud](https://arxiv.org/abs/2309.07496), [Zenoh/MQTT/Kafka/DDS](https://arxiv.org/abs/2303.09419), [FastDDS/Zenoh/vSomeIP](https://arxiv.org/abs/2505.02734))

ขั้นต่อไป: อ่านฉบับเต็มของงานในแถว R2 และ R1 ก่อน (ใกล้หัวข้อมากที่สุด) แล้วค้นแบบ systematic ด้วย query เดียวกันใน IEEE Xplore, ACM DL, Scopus บันทึก query, วันที่ และจำนวนผลไว้ในตารางนี้

### 7.2 ข้อจำกัดด้านความตรง (threats to validity) ของ R1–R9

ข้อจำกัดที่ใช้ร่วมกันทุกข้อ (veth ไม่ใช่สาย, CPU เดียวกัน, tcpdump เพิ่มภาระ, จังหวะเปลี่ยนข้ามวัน, `rmem_max` ของ host, workload เดียว) อยู่ใน[ภาค 3 §8.1](03_wire_experiments.md#81-ข้อจำกัดของผลในภาคนี้) และ protocol 2 เครื่องใน[ภาค 3 §8.2](03_wire_experiments.md#82-protocol-สำหรับ-2-เครื่องจริง-ยังไม่ได้รัน) ตารางนี้ระบุเฉพาะข้อที่เป็นของแต่ละทิศทาง (I = internal, E = external, C = construct)

| R | ภัยหลักเฉพาะทิศทางนี้ | วิธีลด |
|---|---|---|
| R1 | I: ลด fragment ด้วย `maxMessageSize`/flow controller เปลี่ยนจำนวน syscall และจังหวะส่งไปพร้อมกัน ผลต่อ loss แยกจากผลต่อ pacing ไม่ได้ · E: veth ไม่มี GSO segmentation ใน hardware (ไม่มี NIC) ผลของ `UDP_SEGMENT` บน veth อาจต่างจาก NIC ที่ทำ USO | แขนควบคุมที่ pacing เท่ากันแต่ขนาด fragment ต่าง; วัดบน NIC จริงที่ `ethtool -k` แสดง `tx-udp-segmentation` |
| R2 | C: "เวลากู้คืน" ต้องนิยามจากเวลาที่ fragment หายจริงถึง `callback_start` ของ SN นั้น ไม่ใช่ latency รวม · I: `tc netem loss` สุ่ม ทิ้งได้ทั้ง DATA, HEARTBEAT และ ACKNACK (ภาค 3 §4.3.4 ข้อ 2 แสดงการส่งซ้ำโดยไม่มีอะไรหายเมื่อ link ช้า) · E: ค่า default ของ heartbeat/NACK เป็นของ Fast DDS 3.6.x (§2.3) เวอร์ชันอื่นหรือ Cyclone ใช้ค่าต่างกัน | ทิ้งแบบกำหนดได้ตาม `writerSN`; นับ HEARTBEAT/NACK ที่หายแยกออกมา; บันทึกเวอร์ชันและค่าที่ตั้งจริงจาก XML ทุก run |
| R3 | C: build `FASTDDS_STATISTICS=OFF` ต้อง compile เองจึงเปลี่ยน compiler flag/เวอร์ชันได้พร้อมกัน · E: ผลต่อ CPU ขึ้นกับจำนวน locator ของ statistics (ไม่มี subscriber ของ statistics topic ในการทดลอง) | build ทั้งสองแบบจาก source เดียวกันด้วย flag เดียวกัน ต่างเฉพาะ option นั้น; ตรวจ byte บนสาย (60 B) ยืนยันว่า build ถูก |
| R4 | E: veth ไม่มี NIC ring, coalescing และ driver copy (r8169 คัดลอกทุก packet ลง skb ใหม่ §5.7) `truesize` ต่อ datagram บน veth จึงไม่ใช่ของ NIC จริง · I: อัตราการมาถึงบน veth เร็วกว่า 1 GbE 2–10 เท่า (ภาค 3 §4.3.3) และเปลี่ยนข้ามวัน · C: `RcvbufErrors` นับ datagram ไม่ใช่ภาพ | วัด `truesize` จริงด้วย kprobe บนทั้ง veth และ NIC; แปรอัตราด้วย `--shape tbf1g`; รายงานทั้งระดับ datagram และภาพ |
| R5 | C: SHM ทิ้งแบบเงียบ ไม่มีตัวนับใน kernel ต้องพึ่ง `overflows_count` ใน log ตอนปิด segment · I: `/dev/shm` ของ Docker default 64 MB จำกัดขนาด segment ที่ขยายได้ | ตั้ง `--shm-size` ให้พอและบันทึก; นับ sample ที่ผู้รับได้เทียบที่ส่งต่อ SN |
| R6 | E: การวาง node บน container/เครื่องเดียวทำให้ multicast discovery ไม่ผ่าน switch จริง (ไม่มี IGMP snooping/AP) · I: เวลาที่ "graph ลู่เข้า" ขึ้นกับคาบ SPDP announcement และ `ros2 node list` daemon cache | ใช้ capture นับ byte แทนเวลาอย่างเดียว; ปิด ros2 daemon หรือรีสตาร์ททุก run |
| R7 | E: veth ไม่มี NAPI ของ NIC จริงที่ busy polling ทำงานด้วย (busy poll ต้องมี NAPI ID ของ RX queue) ผลบน veth ไม่ได้บอกอะไรเกี่ยวกับ NIC · I: governor `powersave` และ C-state เปลี่ยน baseline ของ wakeup | ทำบน NIC จริงเท่านั้น; ตรึง governor/C-state และบันทึก; ต้องมี clock sync ตาม §6.5 |
| R8 | C: `MSG_ZEROCOPY` อาจ copy อยู่ดี (kernel ตัดสินเอง) ต้องนับ `SO_EE_CODE_ZEROCOPY_COPIED` · E: ผลขึ้นกับ IOMMU และ NIC | อ่าน error queue ทุก send และรายงานสัดส่วนที่ copy จริง |
| R9 | I: เปลี่ยน NIC มักเปลี่ยนเครื่อง/slot/CPU ไปด้วย · E: ตัวอย่าง NIC 2 ชนิดไม่พอสรุปเป็น "driver class" | ใช้เครื่องเดียวกันสลับ NIC (PCIe card) และแปร coalescing บน NIC เดียวกันก่อน (ภายใน driver) |

### 7.3 เส้นทางสู่ paper: แผนสำหรับ R4 และ R2 (แผน ยังไม่ได้ทำ)

ทั้งสองแผนในหัวข้อนี้เป็นแผนงาน **ไม่มีผลใหม่ที่อ้างว่าวัดแล้ว** ตัวเลข pilot ที่ยกมาทั้งหมดมาจากไฟล์ใน `captures/results/` ที่ระบุ

#### 7.3.1 R4: ทำนายขนาด receive buffer ขั้นต่ำจาก `truesize`

**คำถามวิจัย** RQ1: การทิ้งที่ socket ของภาพ UDP แบบ fragment ทำนายได้จากแบบจำลอง `sk_rcvbuf` ÷ (`truesize` ต่อ datagram × จำนวน datagram ที่ค้างในคิว) หรือไม่ RQ2: ค่าขั้นต่ำของ `SO_RCVBUF` ที่ไม่ทิ้งขึ้นกับอัตราการมาถึงและ driver มากเพียงใด

**สมมติฐานที่หักล้างได้**
- H1: สำหรับภาพขนาด S ที่อัตราการมาถึงคงที่ มีค่า `SO_RCVBUF` วิกฤต B* ที่ความน่าจะเป็นของภาพหายลดจาก > 0.5 เป็น < 0.05 ภายในช่วงไม่เกิน 2 เท่าของ B* และ B* อยู่ภายใน ±25% ของค่าทำนาย (จำนวน DATA_FRAG ที่ค้างสูงสุด × `truesize` เฉลี่ยต่อ datagram) หักล้างได้ถ้าช่วงเปลี่ยนกว้างกว่านี้หรือ B* อยู่นอกช่วงทำนาย
- H2: B* ลดลงเมื่ออัตราการมาถึงลดลง (veth → `tbf1g`) หักล้างได้ถ้า B* ที่ `tbf1g` ไม่ต่ำกว่าที่ veth
- H3: B* เป็นสัดส่วนกับ S (จำนวน DATA_FRAG ต่อภาพ) ที่อัตราเดียวกัน
- H4: `truesize` ต่อ datagram 65 KB บน r8169 ต่างจาก veth (r8169 จอง skb ใหม่ต่อ packet §5.7) และทำให้ B* ต่างกันตามสัดส่วน

**ออกแบบการทดลอง (ใช้ harness เดิม)**
- ใช้ได้ทันที: `run_rcvbuf_sweep.sh --arms <bytes>,... --sizes LIST --reps N --qos be --shape none|tbf1g --keep-pcap N` (แขน `<bytes>` ตั้ง `listenSocketBufferSize` เฉพาะผู้รับ), ตัวนับ `RcvbufErrors`/`sockdrops` และ `burst_ms` ต่อ run จาก `rcvbuf_sweep.py`/`sweep_pcap_stats.py`, โหมดสองเครื่อง `--role sub|pub --net host --iface` (ยังไม่ทดสอบบน hardware)
- ต้องเพิ่ม: (1) option ขนาดภาพใน `img_pub.py`/`img_sub.py` (ตอนนี้ 640×480 rgb8 คงที่) (2) option อัตราของ `--shape` (ตอนนี้ `tbf1g` ตายตัวที่ 1 gbit) (3) script bpftrace เก็บ histogram ของ `skb->truesize` ที่ `__udp_enqueue_schedule_skb` และ `sk_rmem_alloc` สูงสุดต่อ run (ต้องใช้ root: เงื่อนไขบน host ตาม §6.5 ช) (4) ตัววิเคราะห์ logistic fit ของ B*
- ตัวแปรอิสระ: `SO_RCVBUF` จริง (ขอ 262 144–1 048 576 ถี่ขึ้นรอบช่วง 425 984–1 048 576 ที่ pilot ยังไม่ได้วัด), S (0.3/0.9/2.8 MB), อัตรา (veth, tbf 1 g, tbf 500 m), driver (veth, r8169, NIC ที่ใช้ page pool)
- ตัวแปรตาม: สัดส่วนภาพที่หายต่อ run, `RcvbufErrors` ต่อภาพ, `truesize` ต่อ datagram, `sk_rmem_alloc` สูงสุด
- ควบคุม: container ใหม่ทุก run, ลำดับแขนสุ่มในแต่ละรอบ (`--seed`), tcpdump เปิดทุกแขน, บันทึก governor/ความถี่ CPU, ผู้ส่งไม่มี XML, ไม่มีงานอื่น (lock)
- จำนวน: 20 run ต่อจุด (20 ภาพต่อ run) ราว 8 จุด × 3 อัตรา × 3 ขนาด ≈ 1 440 run ประมาณ 7 ชั่วโมงที่ ~18 s/run (จากระยะเวลา 1477 s ต่อ 81 run ใน pilot) แบ่งเป็นหลายช่วง
- สถิติ: หน่วยอิสระคือ run (ภาพใน run เดียวกันไม่อิสระ: pilot เห็นภาพแรกหายทุก run) จึงใช้ cluster bootstrap ระดับ run สำหรับ CI ของสัดส่วนภาพหาย, logistic regression (ภาพหาย ~ log `SO_RCVBUF` × อัตรา) พร้อม CI ของ B* จาก bootstrap, effect size เป็น risk difference ระหว่างแขน การเลือกนี้เพราะผลเป็น 0/1 ใกล้ขอบ (0% หรือ 5%) ซึ่ง CI แบบ normal ใช้ไม่ได้
- รูปและตารางที่คาดว่าจะมี: Fig. 1 สัดส่วนภาพหาย (แกน y) เทียบ `SO_RCVBUF` จริง (แกน x, log) แยกเส้นตามอัตรา; Fig. 2 B* ที่วัดได้ (y) เทียบ B* ทำนาย (x) พร้อมเส้น y = x; Fig. 3 histogram ของ `truesize` (x: byte, y: จำนวน) แยกตาม driver; Fig. 4 `RcvbufErrors` ต่อ run (y) เทียบ `burst_ms` ของภาพ (x); Table 1 สภาพแวดล้อมและค่า `ss` ที่ kernel ใช้จริงทุกแขน

**pilot ที่มีแล้ว** [V: `rcvbuf_sweep_summary.csv`, `shaping_summary.csv`]: บน veth แขน `noxml` (`SO_RCVBUF` 212 992) ได้ 19 จาก 20 ภาพทุก run (n = 8, `RcvbufErrors` median 4), แขน 212992 (ได้จริง 425 984) หาย 5.6% (median 2), ตั้งแต่ 1 048 576 ขึ้นไปไม่หายเลย ทุกแขนมี DATA_FRAG บนสายครบ 300 ก้อน; เมื่อจำกัดอัตราด้วย `tbf1g` แขน `noxml` ไม่หายเลย (n = 5, `RcvbufErrors` 0) โดย `burst_ms_med` เพิ่มจาก 3.454 เป็น 7.633 ms ข้อมูลนี้สนับสนุนทิศทางของ H1–H2 แต่**แสดงไม่ได้**ว่า B* อยู่ตรงไหนระหว่าง 425 984 กับ 1 048 576, ไม่มีค่า `truesize` (ต้องใช้ root), มีขนาดภาพเดียว และไม่มี NIC จริง

**ตำแหน่งเทียบงานอื่น** แถว R4 ของ[§7.1](#71-งานที่เกี่ยวข้องของ-r1r9-ฉบับร่าง) (ROS 2 DDS tuning guide, Fast DDS Large Data ซึ่งให้ค่าแนะนำเชิงปฏิบัติ) และแถว R9 (benchmark ที่ไม่รายงาน driver) **ประเภท venue:** workshop หรือ short paper ด้าน robotics software/middleware หรือ track experience/measurement ของ conference ด้าน embedded/real-time systems (ตรวจ scope ของ venue จริงก่อนส่ง)

**checklist** (1) เพิ่ม option ขนาดภาพและอัตรา (2) script bpftrace `truesize` + ขออนุญาต root บนเครื่องทดลอง (3) pilot ช่วงละเอียด 1 วัน (4) ชุดเต็มบน veth + tbf (5) ทำซ้ำบน 2 เครื่องจริงตาม ภาค 3 §8.2 พร้อม NIC สองชนิด (6) วิเคราะห์ + ร่าง paper

#### 7.3.2 R2: เวลากู้คืนของ RELIABLE กับ `heartbeat_period`

**คำถามวิจัย** RQ1: หลัง DATA/DATA_FRAG หายหนึ่งชิ้น เวลาจนกว่า sample นั้นถึง `callback_start` กระจายอย่างไร และถูกกำหนดด้วย `heartbeat_period` (default 3 s, §2.3) หรือด้วยข้อความถัดไปที่ทำให้ reader รู้ว่าขาด RQ2: การส่งซ้ำที่ไม่จำเป็น (repair ของสิ่งที่ไม่ได้หาย) เพิ่มขึ้นอย่างไรเมื่อ link ช้า

**สมมติฐานที่หักล้างได้**
- H1: สำหรับ topic ที่ส่งไม่ถี่ (คาบ ≥ `heartbeat_period`) เมื่อ sample สุดท้ายของช่วงหาย median ของเวลากู้คืนอยู่ในช่วง [0.25, 0.75] × `heartbeat_period` และ p99 ≤ `heartbeat_period` + `nack_response_delay` + RTT
- H2: เมื่อมี sample ถัดไปตามมาเร็วกว่า `heartbeat_period` เวลากู้คืนลดเหลือระดับคาบของ sample ถัดไป (reader เห็นช่องว่างของ SN) ไม่ขึ้นกับ `heartbeat_period`
- H3: จำนวน DATA_FRAG ที่ส่งซ้ำต่อภาพบน link ที่ช้ากว่าเวลาในการส่งภาพหนึ่งภาพเพิ่มขึ้นเมื่อ `heartbeat_period` ลดลง แม้ loss คงที่

**ออกแบบการทดลอง (ใช้ harness เดิม)**
- ใช้ได้ทันที: `run_rcvbuf_sweep.sh --qos rel --shape tbf1g|wifi --keep-pcap N` (นับ NACK_FRAG, DATA_FRAG ส่งซ้ำ ต่อ run), `run_latency.sh --configs image_cross_rel,small_cross` (latency ต่อ sample แต่ไม่ฉีด loss), และวิธีของ[ภาค 3 §7.2](03_wire_experiments.md#72-trace-หนึ่ง-sample-ข้ามชั้น-การทดลองที่-17) (`run_trace.sh`: source timestamp เป็น key ร่วมของ `rmw_publish`, frame และ `rmw_take` จึงได้เวลาต่อ SN ทุกชั้นโดยไม่ต้องใช้ root)
- ต้องเพิ่ม: (1) XML profile ของ data writer ที่ตั้ง heartbeat period (template แบบ `socket_buffer_only.xml.in`; ชื่อ element ต้องตรวจกับ `fastdds_profiles.xsd` ใน image) (2) การทิ้งแบบกำหนดได้ตาม `writerSN` เช่น `tc filter ... u32` ที่ offset ของ writerSN หรือ eBPF `tc` program ใน netns ของผู้ส่ง (`--cap-add NET_ADMIN` พอสำหรับ `tc` แต่การโหลด eBPF ต้องมี `CAP_BPF`: เงื่อนไขบน host) ทางสำรองที่ไม่ต้องใช้สิทธิ์คือ `netem loss` แบบสุ่มแล้วใช้ capture ระบุว่า SN ใดหาย (3) ตัววิเคราะห์ pcap ต่อ SN: เวลา DATA แรก, NACK, การส่งซ้ำ, ถึงผู้รับ (4) `run_trace.sh` รุ่นที่รับ QoS/อัตรา/ขนาดข้อความ (ตอนนี้ใช้ `demo_nodes_cpp` 1 Hz ข้อความเล็ก)
- ตัวแปรอิสระ: `heartbeat_period` (3 s, 500 ms, 100 ms, 20 ms ตาม R2), คาบการส่ง (0.1, 1, 5 s), ขนาด (ข้อความเล็ก, ภาพ 0.9 MB), loss (กำหนดได้ 1 SN ต่อ 10; สุ่ม 0.02% ต่อ frame), อัตรา link (veth, tbf 1 g, `wifi`)
- ตัวแปรตาม: เวลากู้คืนต่อ SN ที่หาย (`rmw_publish` → `callback_start` ของ SN นั้น ลบด้วย median ของ SN ที่ไม่หาย), HEARTBEAT/ACKNACK/NACK_FRAG ต่อวินาที, DATA_FRAG ส่งซ้ำต่อภาพแยกเป็นจำเป็น/ไม่จำเป็น (เทียบกับ frame ที่ netem ทิ้งจริง)
- ควบคุม: depth/history เท่ากัน, ผู้รับไม่ช้า (callback ว่าง), `SO_RCVBUF` 8 MiB เพื่อไม่ให้มี loss ที่ socket ปน (ภาค 3 §4.2 แสดงว่าค่านี้ไม่ทิ้ง), เวอร์ชัน Fast DDS ตรึงด้วย image
- จำนวน: ≥ 200 SN ที่หายต่อเงื่อนไข (เพื่อประมาณ p95 ของเวลากู้คืนได้) ที่ heartbeat 3 s ต้องใช้เวลานาน จึงใช้ 50 SN ที่หายที่ 3 s และ 200 ที่ค่าอื่น
- สถิติ: เวลากู้คืนรายงานเป็น median/p95 พร้อม bootstrap CI (การกระจายไม่ปกติ มีขอบบนที่ `heartbeat_period`), ทดสอบ H1 ด้วยการเทียบการกระจายกับ uniform(0, `heartbeat_period`) (Kolmogorov–Smirnov) และ effect size เป็นอัตราส่วน median ระหว่างค่า `heartbeat_period`
- รูปและตาราง: Fig. 1 ECDF ของเวลากู้คืน (x: ms, log) แยกเส้นตาม `heartbeat_period`; Fig. 2 median เวลากู้คืน (y) เทียบ `heartbeat_period` (x) แยกตามคาบการส่ง; Fig. 3 DATA_FRAG ส่งซ้ำต่อภาพ (y) เทียบ `heartbeat_period` (x) แยกตาม link; Fig. 4 timeline ของ SN หนึ่ง (DATA, HB, NACK, repair, take) จาก pcap + trace; Table 1 ค่าเวลา default ที่ใช้จริงและเวอร์ชัน

**pilot ที่มีแล้ว** [V]: (1) RELIABLE บน veth ที่ `noxml` ซ่อมทุก datagram ที่ socket ทิ้งด้วย NACK_FRAG 1 ฉบับต่อ run และ DATA_FRAG ส่งซ้ำเฉลี่ย 4.4 ต่อ run (`rcvbuf_sweep_summary.csv`, n = 5) (2) `tbf1g` RELIABLE มี NACK_FRAG 20 ต่อ run และส่งซ้ำ 3 ก้อนโดยไม่มี loss (`shaping_summary.csv`, n = 5) (3) `wifi` RELIABLE ได้ 20/20 แต่ DATA_FRAG บนสายเฉลี่ย 1 520.2 ต่อ run (ต้องใช้ 300), NACK_FRAG เฉลี่ย 173.2 และส่งซ้ำเฉลี่ย 1 220.2 (`shaping_summary.csv`) (4) talker 1 Hz ใน exp17 มี HEARTBEAT ของ `rt/chatter` 13 frame ใน 39 s (ราว 1 ต่อ 3 s ตาม default) แต่ละอันตามหลัง DATA 0.32–0.98 ms (`trace_heartbeat_check.txt`) pilot (2)–(3) สนับสนุนส่วน RQ2/H3 ว่าการส่งซ้ำไม่จำเป็นมีจริงและโตเมื่อ link ช้า แต่**ยังไม่มีเวลากู้คืนต่อ SN เลย**, ไม่ได้แปร `heartbeat_period` และ loss ใน pilot ไม่ได้ควบคุม

**ตำแหน่งเทียบงานอื่น** แถว R2 ของ[§7.1](#71-งานที่เกี่ยวข้องของ-r1r9-ฉบับร่าง): analytical latency model ของ DDS ใน ROS 2 (IEEE) และ probabilistic latency analysis (arXiv 2025) เป็นแบบจำลอง; StreamRTPS และ response-time analysis (ECRTS 2023) ให้กลไกทางเลือกและขอบเขต worst-case งานนี้ให้การกระจายเชิงประจักษ์ต่อ SN สำหรับทดสอบแบบจำลองเหล่านั้น จึงต้องอ่านฉบับเต็มของสองงานแรกก่อนเพื่อไม่ทำซ้ำ **ประเภท venue:** conference/workshop ด้าน real-time หรือ robotics middleware ที่รับ measurement study (ตรวจ scope จริงก่อน)

**checklist** (1) อ่านฉบับเต็มของงานในแถว R2 (2) XML heartbeat + ตัวทิ้งตาม SN (3) ขยาย `run_trace.sh` ให้รับ QoS/อัตรา (4) pilot 1 เงื่อนไข ตรวจว่าวัดเวลากู้คืนได้ครบชั้น (5) ชุดเต็มบน veth + tbf (6) ทำซ้ำบน 2 เครื่องพร้อม clock sync ตาม §6.5 (7) วิเคราะห์ + ร่าง paper

### 7.4 ข้อเสนอเพิ่มเติมจากภาค 1 (นอก R1–R9)

ย้ายมาจากภาค 1 §7 (ช่องว่างงานวิจัย 7 ข้อ เป็นข้อเสนอที่ยังไม่ได้ตรวจว่ามีคนทำแล้วหรือไม่) ข้อที่ไม่มีคู่ใน R1–R9 เสนอเป็น R10–R13 ซึ่งยังเป็นเพียงข้อเสนอ ยังไม่มีงานที่เกี่ยวข้องใน §7.1 และ threats ใน §7.2 ข้อที่ซ้อนกับ R เดิมบางส่วนเก็บไว้เฉพาะส่วนที่ R เดิมไม่ครอบคลุม

| ข้อในภาค 1 เดิม | คู่ใน R1–R9 | ส่วนที่อยู่นอก R1–R9 |
|---|---|---|
| 1 `rosidl::Buffer` backend RDMA/RoCE/AF_XDP | ไม่มี (R7 ใน §7.1 อ้าง AF_XDP เพียงเป็นทางเลือก) | ทั้งข้อ: R10 |
| 2 kernel zero-copy (`MSG_ZEROCOPY`, io_uring zero-copy RX, UDP GSO/GRO) | R8 (`MSG_ZEROCOPY`), R1 (GSO/GRO) | io_uring zero-copy RX (รายการข้างล่าง) |
| 3 EventsCBGExecutor บน PREEMPT_RT | บางส่วน: R7 (วัดบน PREEMPT_RT แต่ตัวแปรคือ busy polling) | การเทียบ executor: R11 |
| 4 เปรียบเทียบ 4 Tier-1 RMW | บางส่วน: R6 (discovery 10–500 node), R9 (การรายงาน driver ใน benchmark) | benchmark ข้าม RMW ทั้งชุด (รายการข้างล่าง) |
| 5 Zenoh SHM | ไม่มี (R5 ศึกษาเฉพาะ SHM ของ Fast DDS) | ทั้งข้อ: R12 |
| 6 Content Filtered Topic | ไม่มี | ทั้งข้อ: R13 |
| 7 observability pipeline (หายที่ชั้นไหน) | บางส่วน: R4 (การทิ้งที่ socket), R2 (การซ่อมของ RELIABLE) และระเบียบวิธีใน §6.4–6.6 | pipeline ที่รวมทุกชั้น (รายการข้างล่าง) |

**R10 (ข้อเสนอ). `rosidl::Buffer` backend สำหรับ RDMA / RoCE / AF_XDP**: interface ถูกออกแบบให้ backend เป็น "memory substrate or transport technology" และมี discovery hook ต่อ peer (ภาค 1 §2.4) จึงเหมาะจะทำ backend ที่ส่ง descriptor ผ่าน DDS แล้วส่ง payload ผ่าน RDMA verbs (ข้ามเครื่องแบบ zero-copy)

**R11 (ข้อเสนอ). ประเมิน EventsCBGExecutor**: วัด latency distribution (p50/p99/p99.9) บน PREEMPT_RT เทียบกับ executor อื่น และวัดร่วมกับ SHM ของแต่ละ RMW

**R12 (ข้อเสนอ). Zenoh SHM**: ค่า default ปิดไว้เพราะ "until fully tested" ซึ่งเป็นโอกาสทำ characterization (pool size, threshold 512 B) และหาจุดเสีย ใช้แบบการวัดของ R5 ได้

**R13 (ข้อเสนอ). Content Filtered Topic**: `rcl_subscription_is_cft_supported` ช่วยให้วัดผลการกรองฝั่ง writer (ลด bandwidth) ข้าม RMW ได้อย่างเป็นระบบ

ส่วนที่ขยาย R เดิม
- **Kernel zero-copy** (ข้อ 2 เดิม): ทดลองใช้ `MSG_ZEROCOPY` (TX), io_uring zero-copy RX (มีใน Linux รุ่นใหม่), UDP GSO/GRO ใน Fast DDS UDP transport แล้ววัด CPU/throughput ของข้อความ ≥1 MB ส่วนที่ R8/R1 ยังไม่ครอบคลุมคือ io_uring zero-copy RX ซึ่ง §5.2 พบว่าในเวอร์ชันนี้รับผ่าน TCP เท่านั้น จึงทดลองได้กับ transport แบบ TCP (Zenoh, Fast DDS `LARGE_DATA`) ไม่ใช่ RTPS/UDP
- **เปรียบเทียบ 4 Tier-1 RMW บน Lyrical** (ข้อ 4 เดิม): ระบบเดียวกันกับ payload 64 B–32 MB ภายใต้ intra-host (UDP lo / SHM) และ inter-host (Ethernet 1/10 GbE, Wi-Fi 6) รวมถึงช่วง discovery time ตอนมี node 10–500 ตัว
- **Observability pipeline** (ข้อ 7 เดิม): ใช้ rosbag2 message-loss events + ros2_tracing snapshot mode + eBPF kernel drop (`kfree_skb` reason) เพื่อตอบว่า **หายที่ชั้นไหน** (rmw history / socket buffer / reassembly / NIC) [ภาค 3 §7.2](03_wire_experiments.md#72-trace-หนึ่ง-sample-ข้ามชั้น-การทดลองที่-17) ทำส่วน userspace + capture แล้ว ส่วน kernel ยังต้องใช้สิทธิ์ root (§6.5 ช.)

---

## 8. ประเด็นที่ยังเปิดอยู่

ข้อขัดกับภาค 1 ที่เคยรวบรวมไว้ในหัวข้อนี้ (10 ข้อ) แก้ในภาค 1 ครบแล้ว (ข้อความที่แก้ส่วนใหญ่ติดป้าย "แก้ไข 2026-11-24 ตามภาค 2" หรือ "แก้ไข 2026-11-27 ตาม capture ภาค 3") หลักฐานของแต่ละข้ออยู่ในเนื้อหาของภาคนี้ (§2.4, §3.1, §3.4, §3.5, §3.7, §5.2, §5.7) และไม่พบข้อขัดแย้งในส่วน kernel function chain, สูตร port และค่าของ Zenoh config ที่ภาค 1 อ้าง ผลการทดลองที่ภาคนี้ยังไม่ได้ระบุอยู่ใน[ภาค 3 §8.4](03_wire_experiments.md#84-ประเด็นที่ยังเปิดอยู่-ผลที่เอกสารภาค-12-ยังไม่ได้ระบุ)

**สิ่งที่ยังไม่ได้ verify**

1. ค่า `PID_BUILTIN_ENDPOINT_SET` บนสายเทียบกับที่ทำนายใน §1.2 และผลทั้งหมดบน NIC จริง (r8169): capture ใน[ภาค 3](03_wire_experiments.md) ผ่าน `veth` ทั้งหมด
2. **OMG DDSI-RTPS 2.5** ไม่ได้อ่านต้นฉบับ ความหมายของ field (เช่น ความหมายของ bitmap, GAP) เป็น [K]
3. พฤติกรรมของ `rmw_dds_common::Context` ว่าส่ง `ParticipantEntitiesInfo` เมื่อใดบ้าง (หัวข้อ 1.4)
4. เส้นทางเต็มของ HEARTBEAT ใน `StatefulWriter` (ตรวจเฉพาะ `send_heartbeat_piggyback_nts_` และค่า default) ข้อสรุปเรื่องเวลากู้คืน 3 s เป็นสมมติฐาน
5. รายละเอียดการส่งซ้ำเฉพาะ fragment ที่ขอใน NACK_FRAG ฝั่ง writer (ตรวจถึง `perform_nack_response` → `add_old_sample`)
6. source ของ asio (ว่า `send_to` แบบหลาย buffer ลงเป็น `sendmsg` + iovec) และพฤติกรรมของ `get_option` ต่อ `SO_RCVBUF` บน Linux
7. `sizeof(StatisticsSubmessageData)` = 56 คำนวณจากนิยาม struct ไม่ได้ compile
8. การแบ่ง field ภายใน `PUT` ของ Zenoh (ขนาดรวมวัดแล้ว: TCP payload 95 B ใน[ภาค 3](03_wire_experiments.md)), รูปแบบ ZenohId ใน timestamp, handshake INIT/OPEN และความต่างของ codec ระหว่าง zenoh 1.8.0 (`2687c51`) ที่อยู่ใน `.deb` จริงกับ source 1.10.1 ที่ใช้อ่าน (ดูหมายเหตุเวอร์ชันในหัวข้อ 4)
9. `truesize` จริงของ packet แต่ละขนาดบนเครื่องนี้ และพฤติกรรมเมื่อ frag memory เกิน `ipfrag_high_thresh`
10. คำสั่ง `bpftrace`/`perf` ทั้งหมดยังไม่ได้รัน (ยังเป็นเช่นนั้น: เครื่องทดลองปิด kernel tracing สำหรับผู้ใช้ทั่วไป ดูเงื่อนไขบน host ใน[หัวข้อ 6.5](#65-ระเบียบวิธีวัด-clock-sync-และ-trace-จริงหนึ่ง-sample) ส่วน userspace ของตาราง 6.4 วัดแล้วด้วย ros2_tracing ใน[ภาค 3 §7.2](03_wire_experiments.md#72-trace-หนึ่ง-sample-ข้ามชั้น-การทดลองที่-17))
11. ตัวเลขทั้งหมดในหัวข้อ 6.1–6.3 เป็นประมาณการ ([ภาค 3 §7.2.4](03_wire_experiments.md#724-เทียบกับแบบจำลอง-latency-ของภาค-2-61) เทียบแถวของ 6.1 กับ trace จริงหนึ่ง run บน `veth`: ชั้น rclcpp/rcl/rmw สอดคล้องในระดับ µs แต่ช่วงที่รวม kernel ยาวกว่าประมาณการราว 1 ลำดับขนาด และยังแยกภายในไม่ได้) และคอลัมน์ "วัดด้วย" ของแถว 1 ใน §6.1 อาจต้องแก้ เพราะการ serialize ของ `rmw_fastrtps` น่าจะเกิดหลัง tracepoint `rmw_publish` (ยังไม่ได้ตรวจ source)
12. Cyclone DDS และ Connext ไม่ได้วิเคราะห์ในระดับเดียวกับ Fast DDS; Connext เป็น closed source
13. Wireshark dissector อ่านจาก branch `master` ไม่ใช่ release ที่มากับ Ubuntu 26.04

---

## 9. Sources (ตรวจเมื่อ 2026-11-24)

**Fast DDS** — `eProsima/Fast-DDS` branch `3.6.x`, commit `daf9116dd83fc321c5eaedfb8e6fde98dec8e355`, `package.xml` version 3.6.2
https://github.com/eProsima/Fast-DDS/tree/3.6.x
- `CMakeLists.txt`, `colcon.pkg`
- `include/fastdds/rtps/common/{Types,CDRMessage_t,EntityId_t,VendorId_t,PortParameters,CacheChange}.hpp`
- `include/fastdds/rtps/messages/RTPS_messages.hpp`
- `include/fastdds/dds/core/policy/{ParameterTypes,QosPolicies}.hpp`
- `include/fastdds/rtps/builtin/data/BuiltinEndpoints.hpp`
- `include/fastdds/rtps/attributes/{RTPSParticipantAttributes,WriterAttributes,ReaderAttributes,BuiltinTransports,ThreadSettings}.hpp`
- `include/fastdds/rtps/transport/{TransportInterface,TransportDescriptorInterface,SocketTransportDescriptor}.hpp`, `shared_mem/SharedMemTransportDescriptor.hpp`
- `include/fastdds/rtps/flowcontrol/{FlowControllerDescriptor,FlowControllerSchedulerPolicy}.hpp`
- `src/cpp/rtps/messages/{RTPSMessageGroup,CDRMessage}.cpp`, `submessages/{DataMsg,HeartbeatMsg,AckNackMsg,GapMsg}.hpp`
- `src/cpp/rtps/writer/{BaseWriter,StatefulWriter}.cpp`, `src/cpp/rtps/reader/{StatefulReader,StatelessReader,WriterProxy}.cpp`, `src/cpp/rtps/history/WriterHistory.cpp`
- `src/cpp/rtps/participant/RTPSParticipantImpl.cpp`
- `src/cpp/rtps/builtin/data/{ParticipantProxyData,WriterProxyData}.cpp`, `src/cpp/fastdds/core/policy/ParameterList.cpp`
- `src/cpp/rtps/transport/{UDPTransportInterface,UDPChannelResource,TCPTransportInterface}.cpp`, `UDPv4Transport.h`, `asio_helpers.hpp`
- `src/cpp/rtps/transport/shared_mem/{SharedMemGlobal,SharedMemManager,MultiProducerConsumerRingBuffer,SharedMemChannelResource}.hpp`, `SharedMemTransport.cpp`, `SharedMemTransportDescriptor.cpp`
- `src/cpp/utils/shared_memory/{SharedMemSegment,SharedDir,RobustInterprocessCondition,SharedMemWatchdog}.hpp`
- `src/cpp/rtps/DataSharing/{DataSharingPayloadPool,DataSharingNotification}.hpp`, `DataSharingListener.cpp`
- `src/cpp/rtps/flowcontrol/{FlowControllerImpl.hpp,FlowControllerFactory.cpp,FlowControllerConsts.cpp}`
- `src/cpp/statistics/rtps/messages/{RTPSStatisticsMessages,OutputTrafficManager}.hpp`

**rmw_fastrtps** — `ros2/rmw_fastrtps` branch `lyrical`, commit `c7b3078f8fc8347bb5d4743538dd8f63f8f22c84`
- `rmw_fastrtps_shared_cpp/src/{participant,rmw_publish,namespace_prefix,listener_thread,TypeSupport_impl,qos,utils}.cpp`
- `rmw_fastrtps_cpp/src/{publisher,subscription,init_rmw_context_impl}.cpp`

**rmw_dds_common** — `ros2/rmw_dds_common` branch `lyrical`, commit `2f00e6e9208e925d61330ea92f857b2e67d595ab`
- `rmw_dds_common/msg/{ParticipantEntitiesInfo,NodeEntitiesInfo,Gid}.msg`, `rmw_dds_common/src/qos.cpp`

**rmw_zenoh** — `ros2/rmw_zenoh` branch `lyrical`, commit `f21083b3fafb93454412c4840fff2468724954a9`
- `docs/design.md`, `zenoh_cpp_vendor/CMakeLists.txt`
- `rmw_zenoh_cpp/config/DEFAULT_RMW_ZENOH_SESSION_CONFIG.json5`
- `rmw_zenoh_cpp/src/detail/{rmw_publisher_data,rmw_subscription_data,attachment_helpers,cdr}.cpp`

**Zenoh** — `eclipse-zenoh/zenoh` tag `1.10.1`, commit `1211779c3647f5a96713dade452c546a07823580`
- `commons/zenoh-protocol/src/lib.rs`, `transport/{mod,frame,fragment,keepalive}.rs`, `network/{mod,push}.rs`, `zenoh/{mod,put}.rs`, `core/wire_expr.rs`
- `commons/zenoh-codec/src/core/zint.rs`, `network/push.rs`, `zenoh/put.rs`
- `io/zenoh-links/zenoh-link-tcp/src/{lib,unicast,utils}.rs`, `io/zenoh-transport/src/uring.rs`, `zenoh/Cargo.toml`, `io/zenoh-transport/Cargo.toml`, `Cargo.toml`

**Cyclone DDS** — `eclipse-cyclonedds/cyclonedds` branch `releases/11.0.x`, commit `c6fbafb7d45fb3c32f65b8f1f858df1c980dfaaf` (ใช้เฉพาะ grep ในหัวข้อ 5.2 และ 3.1)

**ros2_tracing** — `ros2/ros2_tracing` branch `lyrical`, commit `1bbbcfd0570f575e2adaa85d6df45d69db08eab8`: `tracetools/include/tracetools/tp_call.h`

**ros2.repos** — https://github.com/ros2/ros2/blob/lyrical/ros2.repos (ยืนยัน branch ของแต่ละ repo)

**Wireshark** — `wireshark/wireshark` branch `master`, `epan/dissectors/packet-rtps.c` (commit ล่าสุดของไฟล์ `f9832b3355ecab9744a8a618357cb025d1a2653d`, 2026-11-15)

**Linux kernel** — `torvalds/linux` tag `v7.0`
https://github.com/torvalds/linux/tree/v7.0
- `include/linux/skbuff.h`, `include/linux/netdevice.h`, `include/linux/udp.h`, `include/uapi/linux/udp.h`, `include/net/{sock,ip,busy_poll}.h`
- `net/ipv4/{udp,udp_offload,ip_output,ip_fragment,inet_fragment}.c`
- `net/core/{sock,dev,skbuff,datagram}.c`, `kernel/softirq.c`, `io_uring/zcrx.c`
- `drivers/net/ethernet/realtek/r8169_main.c`
- `Documentation/networking/ip-sysctl.rst`, `Documentation/admin-guide/sysctl/net.rst` (tag `v7.0`); `Documentation/networking/msg_zerocopy.rst`, `Documentation/networking/iou-zcrx.rst` (อ่านจาก `master` ซึ่งขณะนั้นเป็น 7.4-rc4 ไม่ใช่ v7.0)

**เครื่องที่ใช้ตรวจ** (Linux 7.0.0-43-generic, Ubuntu 26.04.1)
- `/proc/kallsyms` (การมีอยู่ของ symbol และ `__traceiter_*`)
- `bpftool btf dump file /sys/kernel/btf/vmlinux` (ขนาด struct)
- `/boot/config-7.0.0-43-generic`
- `sysctl net.core.*`, `net.ipv4.ipfrag_*`
- `ethtool`, `ethtool -k`, `ethtool -i enp2s0`; `/sys/class/net/enp2s0/{gro_flush_timeout,napi_defer_hard_irqs}`; `lscpu`

**ROS release packaging** — `ros2-gbp/fastdds-release` branch `debian/lyrical/resolute/fastdds`, `debian/rules` (`-DSECURITY=ON`)
