# 📖 Week 07: การสร้างแบบจำลอง 3 มิติ (URDF) และ Inertia Matrix

---

## 🎯 วัตถุประสงค์การเรียนรู้
1. โครงสร้าง URDF XML: Links, Joints, Visual, Collision และ Inertial
2. ชนิดของ Joint: `fixed`, `continuous`, `revolute`
3. การคำนวณ Moment of Inertia Tensor สำหรับรูปทรงมาตรฐาน
4. การใช้งาน `robot_state_publisher` และ RViz2 Visualizer

---

## 📐 สมการ Inertia Matrix
- **ทรงกระบอก (Cylinder มวล $m$, รัศมี $r$, ยาว $h$):**
  $$I_{zz} = \frac{1}{2}mr^2, \quad I_{xx} = I_{yy} = \frac{1}{12}m(3r^2 + h^2)$$
- **กล่องสี่เหลี่ยม (Box มวล $m$, กว้าง $w$, ยาว $d$, สูง $h$):**
  $$I_{xx} = \frac{1}{12}m(h^2 + d^2), \quad I_{yy} = \frac{1}{12}m(w^2 + h^2), \quad I_{zz} = \frac{1}{12}m(w^2 + d^2)$$
