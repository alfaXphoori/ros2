# 📖 Week 02: โครงสร้างโหนด, Topics และการจัดการ QoS

---

## 🎯 วัตถุประสงค์การเรียนรู้
1. โครงสร้างการเขียน Node ด้วย `rclpy` ตามหลักการเชิงวัตถุ (OOP)
2. กลไก Publish-Subscribe Pattern
3. นโยบาย Quality of Service (QoS) และกฎความเข้ากันได้ (QoS Compatibility)

---

## 🏗️ ทฤษฎี QoS (Quality of Service)
- **Reliability:** `BEST_EFFORT` (เน้นความเร็ว) vs `RELIABLE` (รับประกันการส่งถึง)
- **Durability:** `TRANSIENT_LOCAL` (เก็บข้อความล่าสุดไว้ให้ Subscriber ที่เพิ่งเชื่อมต่อ) vs `VOLATILE` (ไม่เก็บย้อนหลัง)
- **กฎความเข้ากันได้:** Subscriber จะรับข้อความได้ก็ต่อเมื่อระดับบริการที่ร้องขอ $\le$ ระดับบริการที่ Publisher ให้
