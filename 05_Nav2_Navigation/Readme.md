# 🚀 โมดูล 5: ระบบนำทางอัตโนมัติ Navigation 2 (Nav2)
## (Module 5: Autonomous Mobile Robot Navigation with Nav2 Stack)

---

## 🎯 วัตถุประสงค์การเรียนรู้
1. เข้าใจสถาปัตยกรรมของ Nav2: Global Planner, Local Controller, 2D Costmaps, และ Recovery Behaviors
2. ศึกษาหลักการระบุตำแหน่งหุ่นยนต์ด้วยความน่าจะเป็น (Adaptive Monte Carlo Localization: AMCL)
3. ปรับแต่งพารามิเตอร์เลเยอร์ Costmap (Static, Obstacle, Inflation) เพื่อความปลอดภัยในการเคลื่อนที่
4. กำหนดจุดเป้าหมาย (2D Goal Pose) ผ่าน RViz2 และติดตามการสร้างเส้นทางหลบหลีกแบบ Dynamic
5. พัฒนาสคริปต์ลาดตระเวนหลายจุดตรวจ (Multi-Waypoint Patrol) แบบอัตโนมัติด้วยภาษา Python

---

## 🏛️ สถาปัตยกรรมของ Nav2 Stack

```
Goal Input:
  • RViz2 /goal_pose
  • Python Waypoint Script
            │
            ▼
┌────────────────────────────────────────────────────────┐
│                      bt_navigator                      │
│            (Behavior Tree Decision Engine)             │
└───────────┬────────────────────────────────┬───────────┘
            │                                │
            ▼                                ▼
┌───────────────────────┐        ┌───────────────────────┐
│    planner_server     │        │   controller_server   │
│  (Global Path: NavFn) │        │  (Trajectory: DWB)    │
│   • global_costmap    │        │   • local_costmap     │
└───────────────────────┘        └───────────┬───────────┘
                                             │
                                             ▼
                                      Topic: /cmd_vel
                                             │
                                             ▼
                                        Gazebo Sim
```

---

## 📑 สารบัญเอกสารและปฏิบัติการ
- [ใบงานปฏิบัติการโมดูล 5 (Lab_Exercises.md)](Lab_Exercises.md)
  - **Lab 5.1:** การรัน Map Server และ AMCL Localization
  - **Lab 5.2:** การตั้งค่า Initial Pose อัตโนมัติด้วย Python
  - **Lab 5.3:** การรัน Nav2 Bringup Stack เต็มรูปแบบ
  - **Lab 5.4:** การสั่งนำทางผ่าน RViz2 และปรับแต่ง Costmap Inflation
  - **Lab 5.5:** ภารกิจลาดตระเวน Multi-Waypoint Patrol ในคลังสินค้า
