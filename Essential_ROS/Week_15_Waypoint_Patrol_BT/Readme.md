# 📖 Week 15: ระบบลาดตระเวนจุดตรวจอัตโนมัติ (Waypoint Patrol) และ Behavior Trees
**เวลาเรียน:** บรรยาย 2 ชั่วโมง | ปฏิบัติการ 3 ชั่วโมง | ศึกษาค้นคว้าด้วยตนเอง 4 ชั่วโมง  
**วิชาบังคับก่อน:** [สัปดาห์ที่ 14: การวางแผนเส้นทาง, คอนโทรลเลอร์ และ AMCL Localization](../Week_14_Path_Planning_AMCL/Readme.md)  
**เอกสารปฏิบัติการ:** [ใบงานแล็บสัปดาห์ที่ 15](Lab_Exercises.md)

---

## 🎯 วัตถุประสงค์การเรียนรู้ (Learning Objectives)
เมื่อจบบทเรียนนี้ ผู้เรียนจะสามารถ:
1. **วิเคราะห์ข้อได้เปรียบทางสถาปัตยกรรมของ Behavior Trees (BTs)** เหนือ Finite State Machines (FSM) ในการขจัดปัญหาการระเบิดของจำนวนสถานะ (State Explosion Problem)
2. **เข้าใจกลไกการส่งสัญญาณกระตุ้น (Tick Propagation)** และสถานะการคืนค่า 3 รูปแบบ (`SUCCESS`, `FAILURE`, `RUNNING`)
3. **จำแนกประเภทและตรรกะการประมวลผลของโหนดใน Behavior Tree**: Control Nodes (`Sequence`, `Fallback`, `ReactiveSequence`, `RecoveryNode`), Decorators, และ Action/Condition Nodes
4. **วิเคราะห์โครงสร้างไฟล์ต้นไม้พฤติกรรมมาตรฐานของ Nav2** (`navigate_to_pose_w_replanning_and_recovery.xml`) และระบบกระดานดำ (Blackboard Data Sharing)
5. **พัฒนาโปรแกรมควบคุมภารกิจลาดตระเวนหลายสถานี (Multi-Station Waypoint Patrol)** ด้วยภาษา Python ผ่าน Action Client และ `nav2_simple_commander` API

---

## ⏱️ แผนการสอน 2 ชั่วโมง (Lecture Outline)
| ช่วงเวลา | หัวข้อ | กิจกรรมการเรียนรู้ |
| :---: | :--- | :--- |
| **00:00 - 00:35** | วิวัฒนาการจาก Finite State Machines สู่ Behavior Trees (BTs) | เปรียบเทียบข้อจำกัดของ State Explosion ใน FSM กับความยืดหยุ่นของ BTs |
| **00:35 - 01:05** | ไวยากรณ์และกลไกของ Behavior Trees: Control, Decorator, Action Nodes | อธิบายสถานะการคืนค่า 3 แบบ, การ Tick ตามลำดับชั้น, และ Blackboard Ports |
| **01:05 - 01:35** | พฤติกรรมการกู้คืนเมื่อติดขัด (Recovery Behaviors: Spin, BackUp, Wait, Clear) | วิเคราะห์ Recovery Node ในการล้าง Costmap และหมุนตัวกู้สถานการณ์ |
| **01:35 - 02:00** | Code Walkthrough: `waypoint_patrol.py`, Nav2 Simple Commander และเตรียม Lab | เจาะลึกโค้ดภารกิจ 5 สถานี พร้อมการหน่วงเวลาปฏิบัติงาน (Dwell Time) และ CLI |

---

## 🏛️ สถาปัตยกรรมระบบ (Architectural Deep Dive)

### 1. ทำไมระบบหุ่นยนต์สมัยใหม่จึงเลือกใช้ Behavior Trees แทน FSM?
ในการออกแบบการตัดสินใจของหุ่นยนต์อัตโนมัติ:
- **Finite State Machines (FSM):**
  - เมื่อระบบมีภารกิจซับซ้อนขึ้น (เช่น ต้องนำทาง หลบคน ชาร์จแบต เบรกฉุกเฉิน กู้คืนเมื่อติดหล่ม) จำนวนสถานะ ($N$) จะส่งผลให้เส้นเชื่อมเงื่อนไขการเปลี่ยนสถานะ (Transitions) เพิ่มขึ้นแบบทวีคูณ $\mathcal{O}(N^2)$ จนเกิดสภาวะ **"State Explosion"** หรือโค้ดพันกันเหมือนสปาเกตตีที่ยากต่อการทดสอบและบำรุงรักษา
- **Behavior Trees (BTs):**
  - ออกแบบเป็นโครงสร้างต้นไม้แบบลำดับชั้น (Hierarchical Directed Tree) แต่ละโหนดทำหน้าที่อิสระต่อกัน (Composability & Modularity)
  - ขับเคลื่อนด้วยสัญญาณรอบเวลาที่เรียกว่า **"Tick"** ส่งลงมาจากโหนดราก (Root) จากบนลงล่าง และจากซ้ายไปขวา
  - คืนสถานะการประมวลผลกลับมาเพียง 3 สถานะมาตรฐานเสมอ:
    1. **`SUCCESS`**: โหนดประมวลผลงานเสร็จสมบูรณ์
    2. **`FAILURE`**: โหนดประมวลผลล้มเหลวหรือไม่ผ่านเงื่อนไข
    3. **`RUNNING`**: โหนดยังประมวลผลไม่เสร็จ (เช่น หุ่นยนต์กำลังอยู่ระหว่างขับเคลื่อน) จะถูก Tick ซ้ำในรอบเวลาถัดไป

```mermaid
graph TD
    subgraph FSM_Problem ["FSM: ข้อจำกัด State Explosion"]
        S1["Navigating"] <--> S2["Obstacle Avoidance"]
        S2 <--> S3["Recovery Spin"]
        S3 <--> S1
        S1 <--> S4["Emergency Stop"]
        S2 <--> S4
        S3 <--> S4
        S4 <--> S5["Recharging"]
        S1 <--> S5
    end

    subgraph BT_Solution ["Behavior Tree: ลำดับชั้นแบบโมดูลาร์"]
        Root["Root: RecoveryNode"]
        NavSeq["Sequence: Nav Loop"]
        Plan["Action: ComputePath"]
        Control["Action: FollowPath"]
        RecovFall["Fallback: Recoveries"]
        Clear["ClearCostmap"]
        Spin["Spin 360°"]

        Root --> NavSeq
        NavSeq --> Plan
        NavSeq --> Control
        Root --> RecovFall
        RecovFall --> Clear
        RecovFall --> Spin
    end

    style FSM_Problem fill:#ffebee,stroke:#c62828,stroke-width:2px
    style BT_Solution fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
```

---

### 2. ชนิดของโหนดใน Behavior Tree (BehaviorTree.CPP Taxonomy)

```mermaid
classDiagram
    class TreeNode {
        +tick() NodeStatus
        +status: SUCCESS | FAILURE | RUNNING
    }
    class ControlNode {
        +children: List[TreeNode]
    }
    class DecoratorNode {
        +child: TreeNode
    }
    class LeafNode {
    }
    class ActionNode {
        +execute()
    }
    class ConditionNode {
        +check() bool
    }

    TreeNode <|-- ControlNode
    TreeNode <|-- DecoratorNode
    TreeNode <|-- LeafNode
    LeafNode <|-- ActionNode
    LeafNode <|-- ConditionNode
    ControlNode <|-- Sequence
    ControlNode <|-- Fallback
    ControlNode <|-- ReactiveSequence
    ControlNode <|-- RecoveryNode
```

#### ก. Control Nodes (โหนดควบคุมลำดับการประมวลผล):
1. **`Sequence` ($\rightarrow$):** ประมวลผลโหนดลูกทีละตัวจากซ้ายไปขวา
   - หากลูกคืนค่า `SUCCESS`: ขยับไปรันลูกตัวถัดไป
   - หากลูกคืนค่า `RUNNING`: หยุดรอและส่ง `RUNNING` กลับคืนไปหาพ่อ
   - หากลูกตัวใดตัวหนึ่งคืนค่า `FAILURE`: **ยุติทันทีและส่ง `FAILURE` กลับคืนไปหาพ่อ** (เงื่อนไข "และ" - AND Logic)
2. **`Fallback` / Selector ($?$):** ประมวลผลโหนดลูกทีละตัวจากซ้ายไปขวา
   - หากลูกคืนค่า `SUCCESS`: **ยุติทันทีและส่ง `SUCCESS` กลับคืนไปหาพ่อ**
   - หากลูกคืนค่า `RUNNING`: หยุดรอและส่ง `RUNNING`
   - หากลูกคืนค่า `FAILURE`: ลองรันลูกตัวถัดไปเพื่อแก้ตัว (เงื่อนไข "หรือ" - OR Logic นิยมใช้ในระบบกู้คืน)
3. **`ReactiveSequence`:** เหมือน Sequence แต่ในทุกๆ รอบ Tick จะกลับไปประเมินเงื่อนไขของลูกตัวแรกๆ ซ้ำเสมอ แม้ว่าลูกตัวปัจจุบันกำลัง `RUNNING` อยู่ เพื่อตอบสนองต่อเหตุการณ์ฉุกเฉินได้ทันท่วงที
4. **`RecoveryNode`:** รับลูก 2 ตัว: ลูกตัวแรกคือ Action หลัก (เช่น การเดิน) หากล้มเหลวจะสลับไปรันลูกตัวที่สองคือ Recovery (เช่น หมุนตัวหรือล้างแผนที่) แล้ววนกลับมารันลูกตัวแรกใหม่ตามจำนวนรอบที่กำหนด

#### ข. Decorator Nodes (โหนดตกแต่งครอบพฤติกรรม):
- `RateController`: กำหนดความถี่ในการ Tick ลูกตัวนั้น เช่น วางแผนเส้นทางใหม่จำกัดที่ 1 Hz
- `Inverter`: สลับผลลัพธ์จาก `SUCCESS` เป็น `FAILURE` และจาก `FAILURE` เป็น `SUCCESS`
- `RetryNode`: สั่งให้รันลูกซ้ำใหม่ $N$ ครั้งเมื่อเกิดข้อผิดพลาดก่อนจะยอมแพ้

#### ค. การแชร์ข้อมูลผ่านกระดานดำ (Blackboard Architecture):
โหนดต่างๆ ใน Behavior Tree สื่อสารและแลกเปลี่ยนตัวแปรกันผ่าน **Blackboard**:
- โหนด `ComputePathToPose` มี Output Port ชื่อ `path` นำผลลัพธ์ไปเขียนลง Blackboard
- โหนด `FollowPath` มี Input Port ชื่อ `path` เข้าไปอ่านค่าเส้นทางนั้นจาก Blackboard มาขับเคลื่อนมอเตอร์

---

### 3. สถาปัตยกรรมภารกิจลาดตระเวน (Waypoint Patrol Architecture)
ในการใช้งานหุ่นยนต์จริงในคลังสินค้า หุ่นยนต์จะต้องเดินทางเป็นลำดับผ่านจุดตรวจที่กำหนดไว้ล่วงหน้า (Waypoints Mission):

```mermaid
stateDiagram-v2
    [*] --> Station1 : เริ่มต้นภารกิจ (Start Mission)
    Station1 --> Station2 : เดินทางสำเร็จ & Dwell 3s (โหลดสินค้า)
    Station2 --> Station3 : เดินทางสำเร็จ & Dwell 3s (ตรวจสอบสต็อก)
    Station3 --> Station4 : เดินทางสำเร็จ & Dwell 3s (ส่งมอบสินค้า)
    Station4 --> Station5 : เดินทางสำเร็จ & Dwell 3s (จุดชาร์จไฟ)
    Station5 --> [*] : จบภารกิจสมบูรณ์ (Mission Complete)

    Station1 --> Recovery : เกิดสิ่งกีดขวางติดขัด
    Station2 --> Recovery : เกิดสิ่งกีดขวางติดขัด
    Station3 --> Recovery : เกิดสิ่งกีดขวางติดขัด
    Station4 --> Recovery : เกิดสิ่งกีดขวางติดขัด
    Recovery --> Station1 : แก้ไขสำเร็จ รันต่อ
    Recovery --> Station2 : แก้ไขสำเร็จ รันต่อ
```

---

## 🛠️ การวิเคราะห์โค้ดตัวอย่างในโมดูล (Code Walkthrough)

### 1. [`src/waypoint_patrol.py`](src/waypoint_patrol.py)
สคริปต์ควบคุมภารกิจลาดตระเวนคลังสินค้า 5 สถานี (`ros2 run amr_week15 waypoint_patrol --ros-args -p use_sim_time:=true`):
- **ตารางภารกิจลาดตระเวน** — ทุกสถานีอยู่ในพื้นที่ว่างของ **แผนที่จริง** และห่างสิ่งกีดขวางเกิน `inflation_radius` 0.55 m (ตรวจโดย `test/test_waypoints.py`):
  ```python
  PATROL_WAYPOINTS = [
      {'name': 'Station 1: Receiving Dock', 'x': 2.0, 'y': 3.5, 'yaw': 0.0, 'dwell': 3.0},
      {'name': 'Station 2: Storage Aisle B', 'x': 2.0, 'y': -2.0, 'yaw': -1.57, 'dwell': 3.0},
      {'name': 'Station 3: Quality Check', 'x': -2.0, 'y': -2.0, 'yaw': 3.14, 'dwell': 3.0},
      {'name': 'Station 4: Shipping Dock', 'x': -2.0, 'y': 3.5, 'yaw': 1.57, 'dwell': 3.0},
      {'name': 'Station 5: Charging Base', 'x': 0.0, 'y': 0.0, 'yaw': 0.0, 'dwell': 2.0},
  ]
  ```
  (เวอร์ชันเดิมวาง Station 1 และ 4 ไว้ที่ $(\pm 2, 2)$ ซึ่งเป็น **ตำแหน่งกลางเสา** ใน `warehouse.sdf` — ไปไม่ถึงแน่นอน จึงย้ายไปด้านหลังเสาที่ $y = 3.5$)
- **การส่ง Goal:** `make_goal()` แปลงมุม Yaw เป็น Quaternion ($q_z = \sin(\psi/2)$, $q_w = \cos(\psi/2)$) แล้วส่งด้วย `send_goal_async()`
- **การตรวจผลลัพธ์จริง:**
  ```python
  status = self.navigate(wp)          # final GoalStatus of the action
  if status == GoalStatus.STATUS_SUCCEEDED:
      ...  # dwell, count as arrived
  else:
      self.get_logger().error(f"[{idx}/{n}] {wp['name']}: {name} after {dt:.1f} s")
  ```
  เวอร์ชันเดิมรอ `get_result_async()` เสร็จแล้วพิมพ์ "Arrived" ทุกครั้ง **แม้ Nav2 จะ ABORTED** — ตอนนี้นับเฉพาะ `STATUS_SUCCEEDED`, ยกเลิก goal ที่เกิน `goal_timeout` (120 s) และ **exit code 1** ถ้ามีสถานีใดล้มเหลว
- **รอ Nav2 พร้อมก่อน:** ถาม `/bt_navigator/get_state` จนเป็น `active` (ถ้าส่ง goal เร็วเกินไป bt_navigator จะตอบ `Action server is inactive. Rejecting the goal.`)
- **Dwell ด้วยเวลาจำลอง:** `self.sleep()` วน `spin_once` ตามนาฬิกาของโหนด (sim time) แทน `time.sleep()` ที่บล็อก callback; พารามิเตอร์ `dwell_scale` ใช้ย่อเวลาพักในการทดสอบ

### 2. [`behavior_trees/patrol_nav_to_pose.xml`](behavior_trees/patrol_nav_to_pose.xml) — Behavior Tree ของเราเอง
ดัดแปลงจาก `navigate_to_pose_w_replanning_and_recovery.xml` ของ Nav2:
```xml
<RateController hz="1.0">
  <RecoveryNode number_of_retries="1" name="ComputeAndSmoothPath">
    <Sequence name="PlanThenSmooth">
      <ComputePathToPose goal="{goal}" path="{raw_path}" planner_id="GridBased" .../>
      <SmoothPath unsmoothed_path="{raw_path}" smoothed_path="{path}" smoother_id="simple_smoother" .../>
    </Sequence>
    <ClearEntireCostmap service_name="global_costmap/clear_entirely_global_costmap"/>
  </RecoveryNode>
</RateController>
<RecoveryNode number_of_retries="1" name="FollowPath">
  <FollowPath path="{path}" controller_id="FollowPath" .../>
  ...
```
- เส้นทางจาก planner (`{raw_path}`) ถูกส่งผ่าน `smoother_server` (`SmoothPath`) ก่อน แล้ว controller ติดตาม `{path}` ที่เรียบแล้ว — ตัวอย่างการส่งข้อมูลผ่าน **Blackboard**
- Recovery แบบ RoundRobin: ล้าง costmap → `Spin` 90° → `Wait` 3 s → `BackUp` 0.3 m (ใช้ `behavior_server` ของสัปดาห์ที่ 14)
- โหลดผ่านพารามิเตอร์ `default_nav_to_pose_bt_xml` ของ `bt_navigator` ([`launch/patrol_system.launch.py`](launch/patrol_system.launch.py) ส่ง path ของไฟล์นี้ให้ `amr_week14/nav2_bringup.launch.py` ทางอาร์กิวเมนต์ `nav_to_pose_bt_xml`)
- `bt_navigator` แปลง XML ตอน **activate**: ถ้า XML ผิดหรือมีโหนดที่ไม่รู้จัก โหนดจะ activate ไม่ผ่าน (ทดลองจริงไว้ใน [`results/bt_load_check.txt`](results/bt_load_check.txt): `Node not recognized: NoSuchNode` → `Failed to bring up all requested nodes`)

### 3. การทดสอบอัตโนมัติ
- [`test/test_waypoints.py`](test/test_waypoints.py): ทุกสถานีอยู่ในเซลล์ว่างของแผนที่จริงและห่างเซลล์ occupied > 0.55 m (ไม่ตกในเขต lethal/inscribed), BT XML ถูกต้องและใช้เฉพาะโหนดที่ Nav2 มี
- [`test/test_patrol_launch.py`](test/test_patrol_launch.py): Gazebo headless + Nav2 + BT ของเรา → `bt_navigator` active ด้วยไฟล์ BT นี้, แล้วรัน `waypoint_patrol` จริง ต้องได้ `5/5 stations SUCCEEDED` (exit code 0) และหุ่นยนต์กลับถึงจุดชาร์จจริงใน Gazebo

---

## ⌨️ ตารางคำสั่ง CLI สำคัญ
| คำสั่ง | คำอธิบาย | ตัวอย่างการใช้งาน |
| :--- | :--- | :--- |
| `ros2 launch amr_week15 patrol_system.launch.py` | Simulation + Nav2 + BT ของสัปดาห์นี้ | `ros2 launch amr_week15 patrol_system.launch.py headless:=true` |
| `ros2 run amr_week15 waypoint_patrol` | รันภารกิจลาดตระเวนอัตโนมัติ 5 สถานี | `ros2 run amr_week15 waypoint_patrol --ros-args -p use_sim_time:=true` |
| `ros2 action send_goal /follow_waypoints ...` | ส่งภารกิจจุดตรวจหลายจุดพร้อมกันผ่าน Nav2 Action CLI (ให้บริการโดย `waypoint_follower` ที่ launch ของสัปดาห์ที่ 14 เปิดไว้) | `ros2 action send_goal /follow_waypoints nav2_msgs/action/FollowWaypoints "{poses: [{header: {frame_id: map}, pose: {position: {x: 1.0, y: -1.0}, orientation: {w: 1.0}}}, {header: {frame_id: map}, pose: {position: {x: -1.0, y: -1.0}, orientation: {w: 1.0}}}]}"` |
| `ros2 param get /bt_navigator default_nav_to_pose_bt_xml` | ตรวจสอบไฟล์คอนฟิก XML ของ Behavior Tree ที่ระบบกำลังใช้งาน | `ros2 param get /bt_navigator default_nav_to_pose_bt_xml` |
| `ros2 action list -t` | แสดงรายชื่อ Action Servers ทั้งหมดที่เกี่ยวกับภารกิจ | `ros2 action list -t` |

---

## 📟 ผลการรันจริง (Real Run Output)
บันทึกจากการรันจริงใน ros:lab-runner (ROS 2 Jazzy, Gazebo Sim 8.15.0) บน Linux 7.0 เมื่อ 2026-10-29
(ฉบับเต็ม: [`results/waypoint_patrol_run.txt`](results/waypoint_patrol_run.txt), การตรวจการโหลด BT: [`results/bt_load_check.txt`](results/bt_load_check.txt))

```console
$ ros2 launch amr_week15 patrol_system.launch.py headless:=true   # terminal 1
$ ros2 param get /bt_navigator default_nav_to_pose_bt_xml
String value is: /workspace/.colcon/c/install/amr_week15/share/amr_week15/behavior_trees/patrol_nav_to_pose.xml
$ ros2 run amr_week15 waypoint_patrol --ros-args -p use_sim_time:=true
[INFO] [1793246902.779426712] [waypoint_patroller]: Waiting for Nav2 (bt_navigator active, /navigate_to_pose)...
[INFO] [1793246904.054665454] [waypoint_patroller]: [1/5] Navigating to Station 1: Receiving Dock (x=2.00, y=3.50, yaw=0.00)
[INFO] [1793246920.529044781] [waypoint_patroller]: [1/5] Station 1: Receiving Dock: SUCCEEDED after 16.4 s, dwelling 3.0 s
[INFO] [1793246923.548490325] [waypoint_patroller]: [2/5] Navigating to Station 2: Storage Aisle B (x=2.00, y=-2.00, yaw=-1.57)
[INFO] [1793246947.872586855] [waypoint_patroller]: [2/5] Station 2: Storage Aisle B: SUCCEEDED after 24.2 s, dwelling 3.0 s
[INFO] [1793246950.899491906] [waypoint_patroller]: [3/5] Navigating to Station 3: Quality Check (x=-2.00, y=-2.00, yaw=3.14)
[INFO] [1793246965.173777686] [waypoint_patroller]: [3/5] Station 3: Quality Check: SUCCEEDED after 14.2 s, dwelling 3.0 s
[INFO] [1793246968.192004624] [waypoint_patroller]: [4/5] Navigating to Station 4: Shipping Dock (x=-2.00, y=3.50, yaw=1.57)
[INFO] [1793246992.966556927] [waypoint_patroller]: [4/5] Station 4: Shipping Dock: SUCCEEDED after 24.5 s, dwelling 3.0 s
[INFO] [1793246995.990225090] [waypoint_patroller]: [5/5] Navigating to Station 5: Charging Base (x=0.00, y=0.00, yaw=0.00)
[INFO] [1793247014.562584142] [waypoint_patroller]: [5/5] Station 5: Charging Base: SUCCEEDED after 18.4 s, dwelling 2.0 s
[INFO] [1793247016.588136858] [waypoint_patroller]: Patrol finished: 5/5 stations SUCCEEDED in 111.6 s (sim time)
(exit code 0)
$ ros2 action send_goal /follow_waypoints nav2_msgs/action/FollowWaypoints {poses: [{header: {frame_id: map}, pose: {position: {x: 1.0, y: -1.0}, orientation: {w: 1.0}}}, {header: {frame_id: map}, pose: {position: {x: -1.0, y: -1.0}, orientation: {w: 1.0}}}]}
Waiting for an action server to become available...
Sending goal:
...
Goal accepted with ID: 4660d390f5904bdb8aab2eb244025072

Result:
    missed_waypoints: []
error_code: 0
error_msg: ''

Goal finished with status: SUCCEEDED
$ ros2 run amr_week11 ground_truth_pose
diff_drive_robot ground truth: x=-0.802 y=-1.064 yaw=0.243 rad (13.9 deg)
```
ผลวัด: ทั้ง 5 สถานี `SUCCEEDED` ใช้เวลารวม 111.6 วินาที (เวลาจำลอง รวม dwell 14 วินาที); `/follow_waypoints` 2 จุดก็ `SUCCEEDED` และหุ่นยนต์จบที่ $(-0.80, -1.06)$ ห่างจุดสุดท้าย $(-1.0, -1.0)$ 0.21 m (ภายใน `xy_goal_tolerance` 0.25 m)

---

## ⚠️ ปัญหาที่พบบ่อยและการแก้ไข (Troubleshooting)

| ที่ | อาการที่พบ (Symptom) | สาเหตุรากเหง้า (Root Cause) | แนวทางแก้ไข (Resolution) |
|:---:| :--- | :--- | :--- |
| 1 | **หุ่นยนต์ไม่ยอมเดินทางไปยังสถานีที่ 2 หลังจบสถานีแรก** | สคริปต์ลืมรอผลลัพธ์ `get_result_future` ทำให้ส่ง Goal ตัวใหม่ไปขัดจังหวะตัวเก่า | ตรวจสอบว่ามีคำสั่ง `spin_until_future_complete` รอจนกว่า Result จะเสร็จสมบูรณ์ |
| 2 | **หุ่นยนต์หมุนตัวควงสว่านอยู่กับที่เมื่อถึงจุดหมาย** | พารามิเตอร์ `yaw_goal_tolerance` ตั้งไว้ละเอียดเกินไป มอเตอร์ปรับองศาไม่ถึง | ขยายค่า `yaw_goal_tolerance` ในคอนฟิกเป็น $0.15 - 0.25\text{ rad}$ |
| 3 | **สคริปต์ Python ค้างที่ `spin_until_future_complete`** | โหนดถูกสั่ง spin ซ้อนกันในมากกว่าหนึ่งเธรด หรือเกิด Deadlock | ตรวจสอบว่าไม่มีลูป `rclpy.spin()` อื่นรันค้างอยู่ในเธรดเดียวกัน |
| 4 | **Behavior Tree ล่มทันทีที่เกิดสิ่งกีดขวาง** | ในไฟล์ XML ไม่มีโครงสร้าง `RecoveryNode` หรือไม่มี `ClearEntireCostmap` รองรับ | เพิ่มบล็อก Fallback และ Recovery Actions เพื่อให้ระบบมีโอกาสกู้คืนสถานการณ์ |
| 5 | **Action Server `/navigate_to_pose` not available / goal ถูก reject** | โหนด `bt_navigator` หรือสแต็ก Nav2 ยังไม่ได้เปิดทำงาน หรือยังไม่ `active` (log: `Action server is inactive. Rejecting the goal.`) | รอ `Managed nodes are active` แล้วตรวจสอบด้วย `ros2 lifecycle get /bt_navigator` |
| 7 | **สคริปต์พิมพ์ว่าถึงสถานีแล้ว แต่หุ่นยนต์ไม่ได้ไปถึง** | ไม่ได้ตรวจ `GoalStatus` ของผลลัพธ์ (ABORTED ก็ทำให้ future เสร็จเหมือนกัน) | ตรวจ `result.status == GoalStatus.STATUS_SUCCEEDED` เสมอ และ exit non-zero เมื่อล้มเหลว |
| 8 | **Goal ABORTED ทันทีที่บางสถานี** | พิกัดสถานีอยู่ในสิ่งกีดขวางหรือในเขต inflation (เช่น กลางเสาที่ $(\pm 2, 2)$) | ตรวจพิกัดเทียบแผนที่จริงด้วย `test_waypoints.py` |
| 6 | **Dwell Time ทำให้การสื่อสารของ ROS ขาดหาย** | ใช้ฟังก์ชัน `time.sleep()` ธรรมดาในลูป Event-driven หลักจนบล็อก Callback (และไม่สนใจ sim time) | วน `rclpy.spin_once()` จนถึงเวลาที่ต้องการตามนาฬิกาของโหนด (ดู `WaypointPatroller.sleep()`) หรือใช้ ROS 2 Timer |

---

## 📝 แบบทดสอบท้ายบท (Self-Assessment Quiz)

1. **คำถาม:** สภาวะ State Explosion ใน Finite State Machines (FSM) คืออะไร และ Behavior Trees แก้ปัญหานี้ได้อย่างไร?
2. **คำถาม:** สถานะการคืนค่า 3 รูปแบบของโหนดใน Behavior Tree ได้แก่อะไรบ้าง?
3. **คำถาม:** จงอธิบายความแตกต่างของตรรกะการทำงานระหว่างโหนดควบคุมแบบ `Sequence` และ `Fallback`?
4. **คำถาม:** โหนดควบคุมแบบ `ReactiveSequence` มีพฤติกรรมแตกต่างจาก `Sequence` ธรรมดาอย่างไรในขณะที่มีโหนดลูกกำลังทำงานอยู่ในสถานะ `RUNNING`?
5. **คำถาม:** ในระบบนำทาง Nav2 โครงสร้าง `RecoveryNode` ทำหน้าที่อะไรเมื่อการเคลื่อนที่หลักล้มเหลว?
6. **คำถาม:** โครงสร้าง Blackboard ใน Behavior Tree มีประโยชน์และหน้าที่อย่างไร?
7. **คำถาม:** ในงานวิศวกรรมหุ่นยนต์บริการและโลจิสติกส์ การกำหนดช่วงเวลาหน่วง (Dwell Time) ณ แต่ละจุด Waypoint มีความจำเป็นอย่างไร?
8. **คำถาม:** ในข้อความ `geometry_msgs/msg/PoseStamped` การระบุ `header.frame_id = 'map'` มีความสำคัญอย่างไรต่อการนำทาง?
9. **คำถาม:** ไลบรารี `nav2_simple_commander` ในภาษา Python ช่วยลดความซับซ้อนในการพัฒนาโปรแกรมนำทางอย่างไร?
10. **คำถาม:** สัญญาณ "Tick" ในสถาปัตยกรรม Behavior Tree มีทิศทางการไหลของสัญญาณอย่างไรในโครงสร้างต้นไม้?

<details>
<summary>🔍 ดูเฉลยคำตอบพร้อมคำอธิบายอย่างละเอียด</summary>

1. **ตอบ:** **State Explosion** คือสภาวะที่จำนวนสถานะและการเชื่อมโยงเงื่อนไข (Transitions) เพิ่มขึ้นอย่างมหาศาลแบบทวีคูณ ($\mathcal{O}(N^2)$) เมื่อระบบมีพฤติกรรมซับซ้อนขึ้น ทำให้โค้ดพันกันยุ่งเหยิง Behavior Trees แก้ปัญหานี้โดยใช้ **โครงสร้างลำดับชั้นแบบต้นไม้ (Hierarchical Tree)** ที่แต่ละโหนดเป็นโมดูลอิสระต่อกัน สามารถนำมาประกอบใหม่หรือขยายพฤติกรรมได้ง่ายโดยไม่กระทบส่วนอื่น
2. **ตอบ:**
   - **`SUCCESS`**: การประมวลผลสำเร็จสมบูรณ์
   - **`FAILURE`**: การประมวลผลล้มเหลวหรือไม่ผ่านเกณฑ์
   - **`RUNNING`**: กำลังอยู่ระหว่างการประมวลผล (จะถูก Tick ซ้ำในรอบถัดไป)
3. **ตอบ:**
   - **`Sequence` ($\rightarrow$):** ประมวลผลลูกจากซ้ายไปขวา และจะสำเร็จก็ต่อเมื่อ **ลูกทุกตัวสำเร็จทั้งหมด (AND Logic)** หากมีตัวใดล้มเหลวจะหยุดและคืนค่า Failure ทันที
   - **`Fallback` ($?$):** ประมวลผลลูกจากซ้ายไปขวา และจะสำเร็จทันทีเมื่อ **พบลูกตัวแรกที่สำเร็จ (OR Logic)** หากลูกล้มเหลวจะขยับไปรันลูกตัวถัดไปเพื่อแก้ตัว
4. **ตอบ:** ในทุกๆ รอบสัญญาณ Tick โหนด **`ReactiveSequence` จะวนกลับไปตรวจสอบประเมินเงื่อนไขของโหนดลูกตัวแรกๆ ซ้ำเสมอ** แม้ว่าลูกตัวปัจจุบันกำลัง `RUNNING` อยู่ ทำให้หากมีเงื่อนไขความปลอดภัยหรือสิ่งกีดขวางกะทันหันเกิดขึ้น ระบบจะสามารถยกเลิกการทำงานและตอบสนองได้ทันที
5. **ตอบ:** รับหน้าที่เป็นตัวกักกันความผิดพลาด โดยหาก Action หลัก (เช่น การเดิน) ล้มเหลว จะสลับไปรัน **พฤติกรรมการกู้คืน (Recovery Actions)** เช่น ล้างแผนที่ Costmap, หมุนตัวสำรวจรอบทิศ (Spin), หรือถอยหลังตั้งหลัก (BackUp) แล้วค่อยกลับไปลองรัน Action หลักใหม่อีกครั้ง
6. **ตอบ:** ทำหน้าที่เป็น **หน่วยความจำส่วนกลาง (Shared Memory / Data Bus)** ที่เปิดให้โหนดต่างๆ ภายในต้นไม้สามารถส่งผ่านและแชร์ตัวแปรข้อมูลระหว่างกันได้อย่างอิสระผ่านระบบ Ports (Input/Output Ports) เช่น การส่งต่อพิกัดเส้นทางจาก Planner ไปยัง Controller
7. **ตอบ:** จำลองและจัดสรรเวลาสำหรับให้หุ่นยนต์ **หยุดนิ่งเพื่อปฏิบัติงานจริง ณ สถานีนั้นๆ** เช่น การรอให้แขนกลยกกล่องสินค้าขึ้นแท่นวาง การรอเปิด-ปิดประตูลิฟต์อัตโนมัติ หรือการหยุดเทียบแท่นชาร์จประจุไฟฟ้า
8. **ตอบ:** เพื่อระบุอย่างชัดเจนว่าพิกัด $(X, Y, Z)$ ของจุดหมายปลายทางนั้น **อ้างอิงอยู่บนระนาบแผนที่โลกสากล (Global Map Frame)** ซึ่งเป็นพิกัดถาวรที่ไม่มีการเคลื่อนที่ตามตัวหุ่นยนต์
9. **ตอบ:** ช่วยห่อหุ้ม (Wrap) การเชื่อมต่อ Action Clients, การจัดการ Transform และการจัดการสถานะความคืบหน้าที่ซับซ้อนของ Nav2 ให้กลายเป็นคำสั่งภาษา Python สั้นๆ ที่เข้าใจง่าย เช่น `goToPose()`, `followWaypoints()`, และ `isTaskComplete()`
10. **ตอบ:** ไหลลงมาจาก **โหนดราก (Root) จากบนลงล่าง (Top-Down) และจากซ้ายไปขวา (Left-to-Right)** ตามลำดับกิ่งก้านของต้นไม้
</details>

---

## 📚 แหล่งอ้างอิงและศึกษาเพิ่มเติม
- [BehaviorTree.CPP Official Documentation](https://www.behaviortree.dev/)
- [Nav2 Behavior Trees Navigation Concepts](https://docs.nav2.org/concepts/index.html#behavior-trees)
- [Nav2 Simple Commander API Guide](https://docs.nav2.org/commander_api/index.html)
- [Colledanchise, Pettersson: Behavior Trees in Robotics and AI: An Introduction (CRC Press)](https://arxiv.org/abs/1709.00084)
