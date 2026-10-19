# 📖 Week 09: ระบบพิกัดสัมพัทธ์และการแปลงพิกัด (TF2 Transformation System)

---

## 🎯 วัตถุประสงค์การเรียนรู้
1. โครงสร้างและกฎของ TF Tree (ห้ามมี Loop หรือ Parent ซ้ำซ้อน)
2. Static vs Dynamic Broadcasters (`/tf_static` vs `/tf`)
3. การใช้งาน `tf2_ros::Buffer` และ Listener สำหรับแปลงพิกัดจุดเป้าหมาย

---

## 📐 สมการแปลงพิกัด
$$P_{\text{base}} = T_{\text{base}}^{\text{sensor}} \times P_{\text{sensor}}$$
เมื่อ $T_{\text{base}}^{\text{sensor}}$ คือเมทริกซ์การแปลงแบบโฮโมจีเนียส (Homogeneous Transformation Matrix) ขนาด $4 \times 4$
