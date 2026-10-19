# 🔌 Tutorial: Nav2 Precision Docking Server (`opennav_docking`)

---

## 🎯 วัตถุประสงค์การเรียนรู้
1. เข้าใจข้อจำกัดของ AMCL ในการระบุตำแหน่งละเอียดระดับมิลลิเมตรเพื่อเสียบขั้วชาร์จไฟ
2. ใช้งาน **Nav2 Docking Server (`opennav_docking`)** ซึ่งเป็นฟีเจอร์ใหม่มาตรฐานใน ROS 2 Jazzy
3. เข้าใจขั้นตอน Staging Pose -> Detection -> Dock Approach -> Contact Verification -> Undocking
4. ออกแบบ Behavior Tree สำหรับระบบชาร์จไฟอัตโนมัติ

---

## 🔄 ลำดับขั้นตอนการทำงาน (Docking Lifecycle)

```mermaid
sequenceDiagram
    participant BT as Behavior Tree
    participant Nav as Nav2 Planner/Controller
    participant Dock as Docking Server
    participant Vision as AprilTag / Laser Detector
    participant Robot as AMR Base

    BT->>Nav: 1. เคลื่อนที่ไปยัง Staging Pose (0.6 ม. หน้าแท่นชาร์จ)
    Nav-->>BT: ถึงจุด Staging Pose แล้ว
    BT->>Dock: 2. สั่งเริ่ม Docking Action (`dock_robot`)
    Dock->>Vision: 3. ตรวจจับตำแหน่งมาร์กเกอร์แท่นชาร์จ
    Vision-->>Dock: ส่งพิกัดแม่นยำระดับมิลลิเมตร
    Dock->>Robot: 4. เคลื่อนที่ความเร็วต่ำ (Closed-loop Servoing 0.05 m/s)
    Robot-->>Dock: สัมผัสขั้วชาร์จสำเร็จ (Charging Contact OK)
    Dock-->>BT: Action Succeeded (หุ่นยนต์เริ่มชาร์จไฟ)
```

---

## 📂 ไฟล์คอนฟิกและ Behavior Tree
- **ไฟล์พารามิเตอร์ของ Docking Server:** [`config/docking_server_params.yaml`](config/docking_server_params.yaml)
- **ไฟล์ Behavior Tree:** [`behavior_trees/dock_and_charge_bt.xml`](behavior_trees/dock_and_charge_bt.xml)
