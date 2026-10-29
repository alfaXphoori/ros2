# 🤖 โมดูล 2: การสร้างโมเดลหุ่นยนต์ 3 มิติ และระบบแปลงพิกัด TF2 (ย้ายแล้ว)

> [!NOTE]
> โมดูลนี้ถูกแยกเป็นรายสัปดาห์แล้ว เนื้อหา โค้ด และไฟล์ URDF ฉบับปัจจุบัน (แก้บั๊ก Inertia ของล้อ, มีชุดทดสอบอัตโนมัติ และผลการรันจริง) อยู่ในโฟลเดอร์ด้านล่าง
> ไฟล์เดิมในโฟลเดอร์นี้ (`urdf/diff_drive_robot.urdf`, `launch/display_urdf.launch.py`, `Lab_Exercises.md`) ถูกลบออกเพื่อไม่ให้มีโมเดลหุ่นยนต์สองฉบับที่ไม่ตรงกัน

| หัวข้อเดิมในโมดูล 2 | ไปที่ |
| :--- | :--- |
| REP 103/105, ลำดับชั้นเฟรม `map → odom → base_footprint → base_link`, จลนศาสตร์ Differential Drive | [สัปดาห์ที่ 6: Kinematics & REP Standards](../Week_06_Kinematics_REP_Standards/Readme.md) |
| URDF, Visual/Collision/Inertial, เทนเซอร์ความเฉื่อย, `robot_state_publisher`, RViz2 | [สัปดาห์ที่ 7: URDF Robot Modeling](../Week_07_URDF_Robot_Modeling/Readme.md) ([ใบงาน](../Week_07_URDF_Robot_Modeling/Lab_Exercises.md)) |
| สอบปฏิบัติกลางภาค (URDF + Node + Launch) | [สัปดาห์ที่ 8: Midterm Practical Exam](../Week_08_Midterm_Practical_Exam/Readme.md) ([ใบสั่งงานข้อสอบ](../Week_08_Midterm_Practical_Exam/Exam_Task.md)) |
| TF2 Static Broadcaster, Buffer & Listener, Optical Frame, `view_frames` | [สัปดาห์ที่ 9: TF2 Coordinate Transforms](../Week_09_TF2_Coordinate_Transforms/Readme.md) ([ใบงาน](../Week_09_TF2_Coordinate_Transforms/Lab_Exercises.md)) |

โมเดลหุ่นยนต์ของรายวิชาอยู่ในแพ็กเกจ `amr_week07`:
```bash
./docker/run_lab.sh colcon build --base-paths Essential_ROS --packages-up-to amr_week07
./docker/run_lab.sh check_urdf Essential_ROS/Week_07_URDF_Robot_Modeling/urdf/diff_drive_robot.urdf
./docker/run_lab.sh ros2 launch amr_week07 display_urdf.launch.py
```
ในโค้ด Python/launch ให้อ้างไฟล์ผ่าน `get_package_share_directory('amr_week07')` + `urdf/diff_drive_robot.urdf`
