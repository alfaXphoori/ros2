# 📚 โมดูล 1: สถาปัตยกรรม ROS 2 และกลไกการสื่อสารหลัก
## (Module 1: ROS 2 Architecture & Core Communication Patterns)

---

## 🎯 วัตถุประสงค์การเรียนรู้
1. เข้าใจสถาปัตยกรรมแบบกระจายศูนย์ของ ROS 2 และบทบาทของ DDS (Data Distribution Service)
2. อธิบายความแตกต่างของรูปแบบการสื่อสารทั้ง 3 แบบ: Topics (Asynchronous Streaming), Services (Synchronous RPC), และ Actions (Long-running Preemptible Goal)
3. ปรับแต่ง Quality of Service (QoS Profiles) เช่น Reliability, Durability, และ History Policy ได้อย่างถูกต้องตามชนิดของข้อมูล
4. สร้าง Dynamic Parameters และจัดการ Callback ตรวจสอบความถูกต้องของค่าคอนฟิกแบบเรียลไทม์
5. ออกแบบระบบ Launch System ด้วยภาษา Python ที่รองรับการรับ Arguments, การโหลดค่าจาก YAML, และการสั่งรันโหนดอัตโนมัติ

---

## 🏛️ สถาปัตยกรรมระบบการสื่อสารใน ROS 2

```
┌────────────────────────────────────────────────────────┐
│                   ROS 2 Node Layer                     │
├───────────────┬───────────────────┬────────────────────┤
│ 1. Topics     │ 2. Services       │ 3. Actions         │
│ One-to-Many   │ One-to-One        │ Goal, Feedback     │
│ Data Stream   │ Request/Response  │ & Result           │
└───────┬───────┴─────────┬─────────┴──────────┬─────────┘
        │                 │                    │
        ▼                 ▼                    ▼
┌────────────────────────────────────────────────────────┐
│                   ROS Middleware (RMW)                 │
├────────────────────────────────────────────────────────┤
│          DDS Layer (Fast DDS / Cyclone DDS)            │
│  • Discovery (SPDP)  • QoS Enforcement  • Wire Format   │
└────────────────────────────────────────────────────────┘
```

---

## 📑 สารบัญเอกสารและปฏิบัติการ
- [ใบงานปฏิบัติการโมดูล 1 (Lab_Exercises.md)](Lab_Exercises.md)
  - **Lab 1.1:** การสื่อสารแบบ Topic Pub/Sub พร้อม Custom QoS (Sensor Data vs Reliable)
  - **Lab 1.2:** ระบบคำขอ-ตอบรับ Service & Client (Robot Power Management & Calculator)
  - **Lab 1.3:** ระบบสั่งภารกิจระยะยาว Action Server & Client (Waypoint Navigation Action)
  - **Lab 1.4:** การจัดการ Dynamic Parameter Callback และการโหลดค่าผ่าน YAML
  - **Lab 1.5:** การรวมศูนย์โหนดด้วย Modular Python Launch File
