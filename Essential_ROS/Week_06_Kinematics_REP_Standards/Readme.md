# 📖 Week 06: มาตรฐานวิศวกรรมพิกัด (REP 103/105) และจลนศาสตร์ AMR

---

## 🎯 วัตถุประสงค์การเรียนรู้
1. มาตรฐาน REP 103: กฎมือขวา (X-หน้า, Y-ซ้าย, Z-บน) หน่วยเมตรและเรเดียน
2. มาตรฐาน REP 105: ลำดับพิกัดหุ่นยนต์ (`earth` -> `map` -> `odom` -> `base_footprint` -> `base_link`)
3. สมการจลนศาสตร์ Differential Drive (Forward & Inverse Kinematics) และ Odometry Dead Reckoning

---

## 📐 สมการจลนศาสตร์ Differential Drive
$$v_R = v + \frac{\omega L}{2}, \quad v_L = v - \frac{\omega L}{2}$$
$$x_{k+1} = x_k + v \cos(\theta_k) \Delta t, \quad y_{k+1} = y_k + v \sin(\theta_k) \Delta t, \quad \theta_{k+1} = \theta_k + \omega \Delta t$$
เมื่อ $L$ คือระยะห่างระหว่างล้อ และ $r$ คือรัศมีล้อ
