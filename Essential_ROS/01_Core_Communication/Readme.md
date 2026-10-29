# 📚 โมดูล 1: สถาปัตยกรรม ROS 2 และกลไกการสื่อสารหลัก (ย้ายไปแล้ว)
## (Module 1: ROS 2 Architecture & Core Communication Patterns — moved)

> [!NOTE]
> เนื้อหาของโมดูลนี้ถูกแยกเป็นบทเรียนรายสัปดาห์ **Week 01 – Week 05** แล้ว แต่ละสัปดาห์เป็นแพ็กเกจ ROS 2 (`amr_week01` … `amr_week05`) ที่ build ด้วย `colcon` มีชุดทดสอบอัตโนมัติ และมีผลการรันจริงกำกับไว้
> โค้ดเดิมในโฟลเดอร์นี้ (`src/`, `launch/`, `Lab_Exercises.md`) เป็นสำเนาเก่าที่แยกทางและมีข้อบกพร่อง จึงถูกลบออก — ยังดูย้อนหลังได้จากประวัติ git

| หัวข้อเดิมของโมดูล 1 | สัปดาห์ | คู่มือบรรยาย | ใบงานปฏิบัติการ |
| :--- | :---: | :--- | :--- |
| สถาปัตยกรรม ROS 2, DDS Discovery, `ROS_DOMAIN_ID` | 01 | [Week 01 Readme](../Week_01_Environment_DDS/Readme.md) | [Week 01 Lab](../Week_01_Environment_DDS/Lab_Exercises.md) |
| Lab 1.1: Topic Pub/Sub + Custom QoS | 02 | [Week 02 Readme](../Week_02_Nodes_Topics_QoS/Readme.md) | [Week 02 Lab](../Week_02_Nodes_Topics_QoS/Lab_Exercises.md) |
| Lab 1.2: Service & Client (Power Management) | 03 | [Week 03 Readme](../Week_03_Services_Clients/Readme.md) | [Week 03 Lab](../Week_03_Services_Clients/Lab_Exercises.md) |
| Lab 1.3: Action Server & Client (Cancel / Preemption) | 04 | [Week 04 Readme](../Week_04_Actions_Preemption/Readme.md) | [Week 04 Lab](../Week_04_Actions_Preemption/Lab_Exercises.md) |
| Lab 1.4–1.5: Dynamic Parameters, YAML และ Python Launch | 05 | [Week 05 Readme](../Week_05_Parameters_Launch/Readme.md) | [Week 05 Lab](../Week_05_Parameters_Launch/Lab_Exercises.md) |

ระบบที่เคยเปิดด้วย `01_Core_Communication/launch/core_system.launch.py` ตอนนี้คือ:
```bash
./docker/run_lab.sh colcon build --base-paths Essential_ROS --packages-up-to amr_week05
./docker/run_lab.sh ros2 launch amr_week05 core_system.launch.py robot_ns:=amr_01 fleet_id:=AMR_01
```
