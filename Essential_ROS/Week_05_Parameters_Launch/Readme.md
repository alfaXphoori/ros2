# 📖 Week 05: Dynamic Parameters และสถาปัตยกรรม Python Launch System
**เวลาเรียน:** บรรยาย 2 ชั่วโมง | ปฏิบัติการ 3 ชั่วโมง | ศึกษาค้นคว้าด้วยตนเอง 4 ชั่วโมง  
**วิชาบังคับก่อน:** [สัปดาห์ที่ 4: Action Protocol สำหรับงานระยะยาว และการยกเลิกเป้าหมาย](../Week_04_Actions_Preemption/Readme.md)  
**เอกสารปฏิบัติการ:** [ใบงานแล็บสัปดาห์ที่ 5](Lab_Exercises.md)

---

## 🎯 วัตถุประสงค์การเรียนรู้ (Learning Objectives)
เมื่อจบบทเรียนนี้ ผู้เรียนจะสามารถ:
1. **อธิบายสถาปัตยกรรมพารามิเตอร์ระดับโหนด (Node-Level Parameters)** ใน ROS 2 และเปรียบเทียบข้อแตกต่างเชิงลึกกับระบบ Parameter Server กลางใน ROS 1
2. **วิเคราะห์กลไกบริการเบื้องหลัง (Under-the-Hood Services)** 6 รายการที่ ROS 2 สร้างให้อัตโนมัติในทุกๆ โหนดสำหรับการจัดการพารามิเตอร์
3. **เขียนโปรแกรมตรวจสอบความถูกต้องแบบไดนามิก (Dynamic Parameter Callback)** ด้วย `add_on_set_parameters_callback` และกำหนดเงื่อนไขความปลอดภัย (Safety Boundaries)
4. **ออกแบบระบบเปิดทำงานอัตโนมัติ (Automation Bringup)** ด้วย Python Launch System โดยใช้ `LaunchDescription`, `DeclareLaunchArgument`, `ExecuteProcess`, และ `Node`
5. **จัดโครงสร้างคอนฟิกแบบรวมศูนย์ด้วย YAML Files** พร้อมจัดการระบบจัดกลุ่มเนมสเปซ (`PushRosNamespace`) สำหรับการควบคุมฝูงหุ่นยนต์หลายตัว (Multi-Robot Fleet)

---

## ⏱️ แผนการสอน 2 ชั่วโมง (Lecture Outline)
| ช่วงเวลา | หัวข้อ | กิจกรรมการเรียนรู้ |
| :---: | :--- | :--- |
| **00:00 - 00:30** | พารามิเตอร์ระดับโหนด (Node-Level) vs ROS 1 Parameter Server | บรรยายวิวัฒนาการ, Strongly-typed system, และ 6 DDS Services ภายใต้ Parameter Interface |
| **00:30 - 01:00** | Dynamic Parameter Callbacks & Safety Validation Rules | วิเคราะห์การทำงานของ `SetParametersResult`, การปฏิเสธค่าอันตราย และ Parameter Events Topic |
| **01:00 - 01:30** | สถาปัตยกรรม Python Launch System | ถอดรหัสโครงสร้างเชิงโปรแกรม (Programmatic Launch), การใช้ Substitutions, Launch Arguments, และ Event Handlers |
| **01:30 - 02:00** | Multi-Robot Namespacing, YAML Hierarchy และเตรียมตัวเข้าสู่ Lab | เจาะลึกโค้ด `fleet_parameters.py` และ `core_system.launch.py` พร้อมสาธิตคำสั่ง CLI |

---

## 🏛️ สถาปัตยกรรมระบบ (Architectural Deep Dive)

### 1. วิวัฒนาการของระบบ Parameters: จาก ROS 1 สู่ ROS 2
ใน ROS 1 พารามิเตอร์ทั้งหมดถูกบันทึกไว้ใน `roscore` (Centralized Parameter Server) ซึ่งมีข้อจำกัดอย่างมาก:
- หากโหนด Master มีปัญหา ข้อมูลคอนฟิกทั้งหมดจะสูญหายทันที
- โหนดไม่สามารถรับทราบได้ว่ามีผู้อื่นมาแอบแก้ไขค่าพารามิเตอร์ (ไม่มี Callback แจ้งเตือนแบบ native)
- ไม่มีระบบตรวจสอบชนิดข้อมูลที่เข้มงวด (Dynamically typed)

ใน ROS 2 แนวคิดได้รับการออกแบบใหม่ให้เป็น **การกระจายศูนย์ (Distributed Node-Level Parameters)**:
- แต่ละโหนดทำหน้าที่เป็นผู้ครอบครองและดูแลพารามิเตอร์ของตนเอง (Self-contained)
- ทุกพารามิเตอร์เป็น **Strongly Typed**: `PARAMETER_BOOL`, `PARAMETER_INTEGER`, `PARAMETER_DOUBLE`, `PARAMETER_STRING`, `PARAMETER_BYTE_ARRAY`, `PARAMETER_BOOL_ARRAY`, `PARAMETER_INTEGER_ARRAY`, `PARAMETER_DOUBLE_ARRAY`, `PARAMETER_STRING_ARRAY`
- รองรับการปรับแต่งค่าแบบเรียลไทม์ขณะที่หุ่นยนต์กำลังเคลื่อนที่ (On-the-fly Reconfiguration)

```mermaid
graph TD
    subgraph ROS1_Arch ["ROS 1 Architecture (Centralized)"]
        Master["roscore (Parameter Server)"]
        R1Node1["Node 1"] -->|Get/Set| Master
        R1Node2["Node 2"] -->|Get/Set| Master
    end

    subgraph ROS2_Arch ["ROS 2 Architecture (Decentralized & Event-Driven)"]
        R2Node1["Node: /amr_01/motor_controller<br/>[Owns: max_speed, kp, ki]"]
        R2Node2["Node: /amr_01/laser_filter<br/>[Owns: scan_angle, range_min]"]
        CLI["CLI / GUI Manager"]
        
        CLI -->|~/set_parameters Service| R2Node1
        CLI -->|~/set_parameters Service| R2Node2
        R2Node1 -.->|/parameter_events Topic| CLI
    end

    style ROS1_Arch fill:#ffebee,stroke:#c62828,stroke-width:2px
    style ROS2_Arch fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
```

---

### 2. บริการเบื้องหลัง 6 รายการที่ซ่อนอยู่ (Under-the-Hood Parameter Services)
เมื่อใดก็ตามที่โหนด ROS 2 ถูกสร้างขึ้น ตัว Node Base จะลงทะเบียน **6 Services และ 1 Topic** สำหรับจัดการพารามิเตอร์ภายใต้เนมสเปซของโหนดนั้น (`~/`) โดยอัตโนมัติ:

1. **`~/describe_parameters` (`rcl_interfaces/srv/DescribeParameters`):**
   - ส่งคืนคำอธิบาย (Description), ขอบเขตค่าที่ยอมรับได้ (FloatingPointRange / IntegerRange), และสถานะ Read-only ของพารามิเตอร์
2. **`~/get_parameter_types` (`rcl_interfaces/srv/GetParameterTypes`):**
   - ขอตรวจสอบรหัสชนิดข้อมูล (`ParameterType`) ของแต่ละตัวแปร
3. **`~/get_parameters` (`rcl_interfaces/srv/GetParameters`):**
   - อ่านค่าพารามิเตอร์ตามรายชื่อตัวแปรที่ระบุ
4. **`~/list_parameters` (`rcl_interfaces/srv/ListParameters`):**
   - แสดงรายชื่อพารามิเตอร์ทั้งหมดที่โหนดนั้นได้ประกาศไว้
5. **`~/set_parameters` (`rcl_interfaces/srv/SetParameters`):**
   - ปรับเปลี่ยนค่าพารามิเตอร์ และส่งสัญญาณเรียก Callback ตรวจสอบความถูกต้อง
6. **`~/set_parameters_atomically` (`rcl_interfaces/srv/SetParametersAtomically`):**
   - ปรับเปลี่ยนพารามิเตอร์หลายตัวพร้อมกันแบบ Atomic (ถ้ามีตัวใดตัวหนึ่งไม่ผ่าน ทุกตัวจะถูก Rollback ยกเลิกทั้งหมด)
7. **`/parameter_events` (`rcl_interfaces/msg/ParameterEvent` [Topic]):**
   - บรอดแคสต์เหตุการณ์แจ้งเตือนทุกครั้งที่มีการ New, Changed, หรือ Deleted พารามิเตอร์ในเครือข่าย

---

### 3. Dynamic Validation & Parameter Descriptors
เพื่อป้องกันไม่ให้ผู้ใช้งานหรือสคริปต์ภายนอกใส่ค่าที่เป็นอันตราย เช่น ป้อนความเร็วหุ่นยนต์ $100\text{ m/s}$ หรือระยะเซฟตี้ติดลบ ROS 2 จัดเตรียมสองชั้นการป้องกัน:

```mermaid
flowchart TD
    Request["Request: Set Parameter<br/>(e.g., max_linear_speed = 5.0)"]
    
    subgraph Node_Validation ["กระบวนการตรวจสอบภายในโหนด"]
        TypeCheck{"ชนิดข้อมูลตรงหรือไม่?<br/>(ParameterType.PARAMETER_DOUBLE)"}
        RangeCheck{"อยู่ในช่วงปลอดภัยหรือไม่?<br/>(0.1 <= speed <= 2.5)"}
        ApplyParam["อัปเดตตัวแปรภายใน<br/>self.max_speed = 5.0<br/>successful = True"]
        RejectParam["ปฏิเสธคำขอ<br/>successful = False<br/>reason = 'Speed outside range!'"]
    end
    
    Response["ส่งผลลัพธ์ SetParametersResult กลับไปยังผู้ขอ"]

    Request --> TypeCheck
    TypeCheck -- ไม่ตรง --> RejectParam
    TypeCheck -- ตรง --> RangeCheck
    RangeCheck -- อยู่นอกช่วง --> RejectParam
    RangeCheck -- ถูกต้อง --> ApplyParam
    RejectParam --> Response
    ApplyParam --> Response
```

---

### 4. สถาปัตยกรรม Python Launch System
ต่างจาก ROS 1 ที่ใช้ภาษา XML ใน ROS 2 การเขียน Launch File ใช้ **ภาษา Python บริสุทธิ์** ซึ่งมีข้อได้เปรียบมหาศาล:
- **Programmatic Control:** สามารถเขียน `if`, `for`, อ่าน Environment Variables, ตรวจจับไฟล์ในดิสก์ และคำนวณทางคณิตศาสตร์ได้
- **Event-Driven Architecture:** รองรับการดักจับเหตุการณ์ เช่น เมื่อโหนดเซนเซอร์ตาย ให้รันโหนดรีสตาร์ท (`OnProcessExit`)
- **Substitutions:** มีระบบแทนที่ค่าตัวแปรแบบ Lazy Evaluation เช่น `LaunchConfiguration`, `EnvironmentVariable`, `PathJoinSubstitution`

```mermaid
classDiagram
    class LaunchDescription {
        +add_action(action)
        +entities: List[LaunchDescriptionEntity]
    }
    class DeclareLaunchArgument {
        +name: str
        +default_value: str
        +description: str
    }
    class Node {
        +package: str
        +executable: str
        +namespace: str
        +parameters: List
        +remappings: List
    }
    class ExecuteProcess {
        +cmd: List[str]
        +output: str
    }
    class IncludeLaunchDescription {
        +launch_description_source
    }

    LaunchDescription *-- DeclareLaunchArgument
    LaunchDescription *-- Node
    LaunchDescription *-- ExecuteProcess
    LaunchDescription *-- IncludeLaunchDescription
```

---

## 🛠️ การวิเคราะห์โค้ดตัวอย่างในโมดูล (Code Walkthrough)

### 1. [`fleet_parameters.py`](file:///mnt/sda/ros/Essential_ROS/Week_05_Parameters_Launch/src/fleet_parameters.py)
โหนดจำลองการควบคุมพารามิเตอร์ความปลอดภัยของฝูงหุ่นยนต์:
- **การประกาศพารามิเตอร์เริ่มต้น ([L17-L20](file:///mnt/sda/ros/Essential_ROS/Week_05_Parameters_Launch/src/fleet_parameters.py#L17-L20)):**
  ```python
  self.declare_parameter('fleet_id', 'AMR_ALPHA_01')
  self.declare_parameter('max_linear_speed', 0.8)
  self.declare_parameter('safety_margin', 0.35)
  self.declare_parameter('enable_obstacle_stop', True)
  ```
  การประกาศพารามิเตอร์ต้องระบุชื่อและค่าเริ่มต้น (Default Value) เสมอ เพื่อกำหนดโครงสร้างประเภทข้อมูลตั้งต้น
- **การลงทะเบียน Dynamic Callback ([L23](file:///mnt/sda/ros/Essential_ROS/Week_05_Parameters_Launch/src/fleet_parameters.py#L23)):**
  ```python
  self.add_on_set_parameters_callback(self.parameters_callback)
  ```
  ผูกฟังก์ชันตรวจสอบความถูกต้องเข้ากับระบบ เมื่อมีคำสั่ง `ros2 param set` หรือคำขอจากเครือข่าย ฟังก์ชันนี้จะถูกเรียกทันที
- **ตรรกะการตรวจสอบความปลอดภัย (Validation Logic) ([L31-L58](file:///mnt/sda/ros/Essential_ROS/Week_05_Parameters_Launch/src/fleet_parameters.py#L31-L58)):**
  ```python
  def parameters_callback(self, params):
      result = SetParametersResult()
      result.successful = True
      for param in params:
          if param.name == 'max_linear_speed':
              if param.type_ != ParameterType.PARAMETER_DOUBLE:
                  result.successful = False
                  result.reason = 'max_linear_speed must be a floating point number.'
                  return result
              if not (0.1 <= param.value <= 2.5):
                  result.successful = False
                  result.reason = f'Speed {param.value} is outside valid safety range [0.1, 2.5] m/s!'
                  return result
  ```
  หากพบค่าที่ไม่ปลอดภัย ระบบจะปฏิเสธคำขอทันที ทำให้ค่าคอนฟิกเดิมไม่ถูกแก้ไขและส่งข้อความเตือนกลับไปยังผู้ส่ง

---

### 2. [`core_system.launch.py`](file:///mnt/sda/ros/Essential_ROS/Week_05_Parameters_Launch/launch/core_system.launch.py)
ไฟล์ Launch ที่ทำหน้าที่เปิดระบบสื่อสารพื้นฐานของ AMR แบบครบวงจร:
- **การประกาศอาร์กิวเมนต์ ([L15-L28](file:///mnt/sda/ros/Essential_ROS/Week_05_Parameters_Launch/launch/core_system.launch.py#L15-L28)):**
  ```python
  robot_namespace_arg = DeclareLaunchArgument(
      'robot_ns',
      default_value='',
      description='Optional namespace for multi-robot isolation'
  )
  ```
  ช่วยให้ผู้ใช้งานสามารถระบุค่าผ่าน CLI ได้ เช่น `ros2 launch core_system.launch.py robot_ns:=amr_01`
- **การรวมโปรเซสหลายสัปดาห์เข้าด้วยกัน ([L39-L65](file:///mnt/sda/ros/Essential_ROS/Week_05_Parameters_Launch/launch/core_system.launch.py#L39-L65)):**
  สคริปต์นี้ผสานการทำงานของ:
  1. `sensor_qos_publisher` (สัปดาห์ที่ 2)
  2. `power_service_server` (สัปดาห์ที่ 3)
  3. `navigate_action_server` (สัปดาห์ที่ 4)
  4. `fleet_parameters` (สัปดาห์ที่ 5)
  เข้าสู่คอนเทนเนอร์เดียวกัน ทำให้สามารถเริ่มระบบทั้งหุ่นยนต์ได้ด้วยคำสั่งเดียว

---

## ⌨️ ตารางคำสั่ง CLI สำคัญ
| คำสั่ง | คำอธิบาย | ตัวอย่างการใช้งาน |
| :--- | :--- | :--- |
| `ros2 param list` | แสดงรายชื่อพารามิเตอร์ทั้งหมดของทุกโหนดในระบบ | `ros2 param list` |
| `ros2 param get <node> <param>` | อ่านค่าพารามิเตอร์ปัจจุบันของโหนด | `ros2 param get /fleet_parameters max_linear_speed` |
| `ros2 param set <node> <param> <val>` | ปรับเปลี่ยนค่าพารามิเตอร์แบบ On-the-fly | `ros2 param set /fleet_parameters max_linear_speed 1.5` |
| `ros2 param dump <node>` | บันทึกค่าพารามิเตอร์ปัจจุบันของโหนดลงไฟล์ YAML | `ros2 param dump /fleet_parameters > my_params.yaml` |
| `ros2 param load <node> <yaml_file>` | โหลดค่าพารามิเตอร์จากไฟล์ YAML เข้าสู่โหนดที่กำลังรัน | `ros2 param load /fleet_parameters my_params.yaml` |
| `ros2 launch <pkg_or_path> <file>` | รันระบบผ่านสคริปต์ Python Launch | `ros2 launch Essential_ROS/Week_05_Parameters_Launch/launch/core_system.launch.py` |

---

## 📸 ภาพผลการทดสอบจริงจากระบบ (Live Execution & Terminal Capture)
ผลลัพธ์จากการรันคำสั่งและโหนดจริงในระบบ เพื่อใช้เป็นข้อมูลอ้างอิงในการตรวจสอบความถูกต้อง:

![Terminal Capture: Terminal — Week 05: Dynamic Parameter Validation & Reconfigure](images/terminal_run.png)

```console
user@amr-dev:~/ros$ ./docker/run_lab.sh python3 Essential_ROS/Week_05_Parameters_Launch/src/fleet_parameters.py &
[INFO] [fleet_parameters]: 🤖 [FleetParametersNode] Initialized: ID=AMR_ALPHA_01, MaxSpeed=0.8m/s, Margin=0.35m
user@amr-dev:~/ros$ ./docker/run_lab.sh ros2 param get /fleet_parameters max_linear_speed
Double value is: 0.8
user@amr-dev:~/ros$ ./docker/run_lab.sh ros2 param set /fleet_parameters max_linear_speed 1.2
[WARN] [fleet_parameters]: ⚡ max_linear_speed updated to: 1.2 m/s
Set parameter successful
user@amr-dev:~/ros$ ./docker/run_lab.sh ros2 param set /fleet_parameters max_linear_speed 3.5
Setting parameter failed: Speed 3.5 is outside valid safety range [0.1, 2.5] m/s!
user@amr-dev:~/ros$ [CHECKPOINT PASSED: DYNAMIC CALLBACK REJECTED UNSAFE SPEED VALUES]
```

---

## ⚠️ ปัญหาที่พบบ่อยและการแก้ไข (Troubleshooting)

| ที่ | อาการที่พบ (Symptom) | สาเหตุรากเหง้า (Root Cause) | แนวทางแก้ไข (Resolution) |
|:---:| :--- | :--- | :--- |
| 1 | **เรียก `get_parameter()` แล้วโปรแกรม Crash: `ParameterNotDeclaredException`** | พยายามอ่านค่าพารามิเตอร์ที่ยังไม่ได้เรียก `self.declare_parameter()` | ต้องประกาศพารามิเตอร์พร้อมค่า Default เสมอในส่วน `__init__` ของโหนด |
| 2 | **สั่ง `ros2 param set` ผ่าน CLI แล้วติด Error ปฏิเสธค่า** | ค่าที่ส่งเข้าไปไม่ผ่านเงื่อนไขใน `add_on_set_parameters_callback` (เช่น ป้อนค่าความเร็วเกินช่วงปลอดภัย) | ตรวจสอบข้อความ `reason` ในเทอร์มินัล และปรับค่าให้อยู่ในช่วงที่กำหนด |
| 3 | **Launch file ไม่พบไฟล์สคริปต์ปลายทาง (`FileNotFoundError`)** | การอ้างอิง Relative Path ใน Launch File ไม่ตรงกับ Working Directory ขณะรัน | ใช้ `os.path.dirname(os.path.realpath(__file__))` หรือ `get_package_share_directory()` เพื่อหา Absolute Path ที่แน่นอน |
| 4 | **ส่ง Argument ผ่าน CLI แล้ว Launch File ไม่นำค่าไปใช้** | ดึงค่าตัวแปรผ่าน Python ธรรมดาแทนที่จะใช้ `LaunchConfiguration` | ใช้ `LaunchConfiguration('arg_name')` ในการส่งต่อค่าไปยังโหนด |
| 5 | **ไฟล์ YAML โหลดไม่เข้าโหนด (`Invalid parameter file`)** | โครงสร้าง Indentation ของ YAML ไม่ตรง หรือลืมระบุ Node Name และ Namespace ให้ตรงกับโหนดจริง | ตรวจสอบโครงสร้าง: บรรทัดแรกต้องเป็น `/**:` หรือ `/<node_name>:` ตามด้วย `ros__parameters:` (ขีดล่าง 2 ตัว) |
| 6 | **ข้อผิดพลาด Parameter Type Mismatch เมื่อ Set ผ่าน CLI** | ส่งค่าจำนวนเต็ม (Integer) ให้กับพารามิเตอร์ประเภท Double เช่น ใส่ `1` แทนที่จะเป็น `1.0` | ระบุทศนิยมให้ชัดเจน เช่น `ros2 param set /node speed 1.0` |

---

## 📝 แบบทดสอบท้ายบท (Self-Assessment Quiz)

1. **คำถาม:** สถาปัตยกรรมพารามิเตอร์ของ ROS 2 แตกต่างจาก Parameter Server ของ ROS 1 ในมิติของการกระจายข้อมูล (Distribution) อย่างไร?
2. **คำถาม:** จงระบุชื่อ ROS 2 Service 2 รายการที่ถูกสร้างขึ้นอัตโนมัติภายในโหนดเพื่อใช้สำหรับตรวจสอบและปรับแต่งค่าพารามิเตอร์?
3. **คำถาม:** ในการสร้าง Dynamic Parameter Callback ด้วย `add_on_set_parameters_callback` ฟังก์ชันจะต้อง Return อ็อบเจกต์ชนิดใดกลับคืนมา?
4. **คำถาม:** ข้อใดคือผลลัพธ์ที่จะเกิดขึ้นเมื่อฟังก์ชัน Callback ส่งคืนค่า `result.successful = False` พร้อมระบุ `result.reason`?
5. **คำถาม:** เหตุใด ROS 2 จึงเปลี่ยนจากการเขียน Launch File ด้วย XML (แบบ ROS 1) มาใช้ภาษา Python บริสุทธิ์?
6. **คำถาม:** อ็อบเจกต์ใดใน `launch.actions` ที่ใช้สำหรับประกาศรับค่าตัวแปรเสริมจากหน้าต่างเทอร์มินัล (CLI Arguments)?
7. **คำถาม:** ในโครงสร้างไฟล์ YAML สำหรับคอนฟิกพารามิเตอร์ของ ROS 2 คีย์เวิร์ดที่ใช้เปิดบล็อกพารามิเตอร์ต้องมีเครื่องหมายขีดล่างกี่ตัว?
8. **คำถาม:** หากต้องการตั้งค่าพารามิเตอร์ให้มีผลกับทุกโหนดในระบบโดยไม่เจาะจงชื่อโหนด ในไฟล์ YAML จะต้องใช้สัญลักษณ์ใดแทนชื่อโหนด?
9. **คำถาม:** คำสั่ง CLI ใดที่ใช้ในการ Export ค่าพารามิเตอร์ปัจจุบันทั้งหมดของโหนดออกมาเป็นไฟล์ YAML?
10. **คำถาม:** ความแตกต่างระหว่างการใช้ `Node` action กับ `ExecuteProcess` action ใน ROS 2 Launch File คืออะไร?

<details>
<summary>🔍 ดูเฉลยคำตอบพร้อมคำอธิบายอย่างละเอียด</summary>

1. **ตอบ:** ใน ROS 1 พารามิเตอร์ทั้งหมดจะถูกจัดเก็บรวมกันที่ศูนย์กลางในโหนด `roscore` (Centralized) หาก Master ดับ ข้อมูลทั้งหมดจะหาย แต่ใน ROS 2 พารามิเตอร์จะถูกกระจายไปเป็น **คุณสมบัติเฉพาะตัวของแต่ละโหนด (Decentralized & Node-Level)** แต่ละโหนดดูแลและจัดการพารามิเตอร์ของตนเองโดยตรง
2. **ตอบ:** ตัวอย่างบริการเช่น `~/get_parameters` (สำหรับอ่านค่า), `~/set_parameters` (สำหรับเขียนค่า), `~/describe_parameters` (สำหรับดูรายละเอียด), และ `~/list_parameters` (สำหรับดูรายชื่อ)
3. **ตอบ:** อ็อบเจกต์ชนิด **`rcl_interfaces.msg.SetParametersResult`** ซึ่งมีฟิลด์หลักคือ `successful` (bool) และ `reason` (string)
4. **ตอบ:** คำขอปรับเปลี่ยนค่าจะถูกปฏิเสธทันที (Rejected), พารามิเตอร์ของโหนดจะคงค่าเดิมไว้ไม่เปลี่ยนแปลง, และข้อความเหตุผลใน `result.reason` จะถูกส่งกลับไปแสดงผลทางหน้าจอของผู้สั่ง
5. **ตอบ:** เพื่อให้ผู้พัฒนาสามารถ **ควบคุมตรรกะเชิงโปรแกรม (Programmatic Flexibility)** ได้อย่างเต็มรูปแบบ เช่น การใช้เงื่อนไข `if-else`, ลูป `for`, การตรวจสอบสภาพแวดล้อมระบบปฏิบัติการ, และการจัดการ Event Handlers เมื่อมีโหนดปิดตัวลง ซึ่งไม่สามารถทำได้คล่องตัวในไฟล์ XML
6. **ตอบ:** **`launch.actions.DeclareLaunchArgument`** โดยทำงานร่วมกับ `launch.substitutions.LaunchConfiguration` ในการดึงค่าไปใช้งาน
7. **ตอบ:** ต้องมีเครื่องหมายขีดล่าง 2 ตัว คือ **`ros__parameters:`** (ดับเบิลอันเดอร์สกอร์)
8. **ตอบ:** ใช้สัญลักษณ์ Wildcard คือ **`/**:`**
9. **ตอบ:** `ros2 param dump <node_name>` เช่น `ros2 param dump /fleet_parameters > params.yaml`
10. **ตอบ:** 
    - `Node` action (จาก `launch_ros.actions`) ถูกออกแบบมาสำหรับรัน ROS 2 C++/Python Nodes โดยเฉพาะ รองรับการใส่เนมสเปซ, พารามิเตอร์, และการ Remap ท็อปปิกได้อย่างสะดวก
    - `ExecuteProcess` action (จาก `launch.actions`) เป็นคำสั่งระดับต่ำสำหรับรันโพรเซสหรือโปรแกรมใดๆ บนระบบปฏิบัติการ (รวมถึงสคริปต์ Python เดี่ยวๆ คำสั่ง Bash หรือโปรแกรมภายนอกที่ไม่ใช่แพ็กเกจ ROS 2)
</details>

---

## 📚 แหล่งอ้างอิงและศึกษาเพิ่มเติม
- [About ROS 2 Parameters](https://docs.ros.org/en/jazzy/Concepts/Basic/About-Parameters.html)
- [ROS 2 Launch System Architecture](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Launch/Launch-Main.html)
- [Using YAML Files for Parameters](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Using-Parameters-In-A-Class-Python.html)
- [Design Architecture: ROS 2 Launch Design](https://design.ros2.org/articles/roslaunch.html)
