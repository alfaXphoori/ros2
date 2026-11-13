#!/usr/bin/env python3
"""Generate standalone animated ByteByteGo-style SVGs with synchronized step tables
for the ROS 2 & Gazebo Sim AMR repository.

Uses pure SVG + CSS @keyframes (no JavaScript, respects prefers-reduced-motion)
and embeds subsetted Noto Sans / Noto Sans Thai / DejaVu Sans WOFF fonts via
scripts/diagram_postprocess.py so Thai typography renders consistently everywhere.

Usage:
    scripts/render_animated_diagrams.py                 # render all animated diagrams
    scripts/render_animated_diagrams.py anim-ros2-dds   # render specific diagram(s)
"""

import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIAG_DIR = ROOT / "docs" / "diagrams"
sys.path.insert(0, str(Path(__file__).resolve().parent))

import diagram_postprocess  # noqa: E402
from anim_svg_ui import (  # noqa: E402
    BASE_CSS,
    SHARED_SYMBOLS,
    esc,
    kf_move,
    kf_pop,
    make_header,
    make_stage,
    make_step_table,
    node_card,
    pkt_chip,
    pop_pill,
)

FONT_SOURCES = [
    Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]


def build_anim_ros2_dds():
    dur = 12.0
    steps = [
        ("SPDP ประกาศตัวตน", "Node A (Domain 0) ยิง UDP Multicast 7400 ค้นหาเพื่อนร่วมเครือข่าย", 0.3, 3.0),
        ("แยกเครือข่าย Domain", "หุ่นยนต์ Domain 15 (พอร์ต 11150) ไม่รับแพ็กเก็ตของ Domain 0", 3.1, 5.8),
        ("SEDP จับคู่ Topic", "Node A และ Node B แลกเปลี่ยน Topic / QoS ผ่าน Unicast แล้วจับคู่กัน", 5.9, 8.8),
        ("Peer-to-Peer ตรง", "ส่งข้อมูล /cmd_vel และ /scan โดยตรง ไม่ต้องพึ่ง roscore กลาง", 8.9, 11.7),
    ]
    header = make_header(
        "ROS 2 DDS", "Discovery & Domain Isolation",
        "กลไกค้นหาโหนดอัตโนมัติ (SPDP/SEDP) และการแยกเครือข่ายหุ่นยนต์ด้วย ROS_DOMAIN_ID"
    )
    stage = make_stage(120, 324, "DDS Network: Domain 0 (Port 7400) vs Domain 15 (Port 11150)")

    n_a = node_card(44, 184, 210, 146, "Node A (Controller)", "ROS_DOMAIN_ID=0", "#eff6ff", "bb-app", "Pub: /cmd_vel", "#bfdbfe")
    n_dds = node_card(368, 184, 224, 146, "UDP Multicast / DDS", "Port = 7400 + 250×ID", "#fefce8", "bb-server", "SPDP + SEDP", "#fde68a")
    n_b = node_card(706, 184, 210, 134, "Node B (Motor Driver)", "ROS_DOMAIN_ID=0", "#f0fdf4", "bb-robot", "Sub: /cmd_vel", "#bbf7d0")
    n_x = node_card(706, 336, 210, 92, "Robot X (Isolated)", "Domain 15 : Port 11150", "#fff1f2", "", "Dropped ✗", "#fecdd3")

    paths = (
        '<path class="ant-blue" d="M254 257H364" marker-end="url(#bb-ah-blue)"/>'
        '<path class="ant-green" d="M592 251H702" marker-end="url(#bb-ah-green)"/>'
        '<path class="ant-red" d="M592 286L702 372" marker-end="url(#bb-ah-red)"/>'
        '<path class="ant" d="M254 226Q480 176 702 226" marker-end="url(#bb-ah)"/>'
    )

    anim_css = (
        kf_move("pk-spdp", dur, 0.3, 3.0, [(160, 257), (480, 257)])
        + kf_move("pk-drop", dur, 3.1, 5.8, [(480, 275), (650, 336), (760, 376)])
        + kf_pop("bd-iso", dur, 4.0, 5.9)
        + kf_move("pk-sedp", dur, 5.9, 8.8, [(480, 251), (780, 251)])
        + kf_move("pk-p2p", dur, 8.9, 11.7, [(160, 226), (480, 198), (780, 226)])
        + kf_pop("bd-ok", dur, 9.6, 11.7)
    )
    anim_els = (
        pkt_chip("pk-spdp", "SPDP :7400", "#93c5fd", 112)
        + pkt_chip("pk-drop", "คนละ Domain", "#fb7185", 116)
        + pkt_chip("pk-sedp", "SEDP Match", "#fde047", 112)
        + pkt_chip("pk-p2p", "Twist P2P", "#7de3b4", 108)
        + pop_pill("bd-iso", 640, 390, "คัดกรองทิ้ง (คนละพอร์ต)", "#e11d48")
        + pop_pill("bd-ok", 480, 180, "เชื่อมต่อ P2P สำเร็จ ✓", "#16a34a")
    )

    tbl, tbl_css, tbl_h = make_step_table(464, steps, dur, split_x=256)
    return "ROS 2 DDS Discovery & Domain Isolation", 464 + tbl_h + 24, header + stage + n_a + n_dds + n_b + n_x + paths + anim_els + tbl, anim_css + tbl_css


def build_anim_topic_qos():
    dur = 12.0
    steps = [
        ("ส่งข้อมูล BEST_EFFORT", "LiDAR / Sensor ส่งข้อมูลถี่สูงแบบไม่รอ Ack (เน้นความเร็ว)", 0.3, 3.0),
        ("จับคู่ QoS สำเร็จ", "Subscriber ตั้ง BEST_EFFORT (รับได้ทั้งคู่) → ข้อมูลไหลผ่านได้", 3.1, 5.9),
        ("QoS ไม่เข้ากัน!", "Subscriber ขอ RELIABLE จาก Publisher แบบ BEST_EFFORT → ถูกตัดการเชื่อมต่อ", 6.0, 8.9),
        ("TRANSIENT_LOCAL", "Latch ข้อมูลล่าสุด (เช่น /map หรือ /robot/state) ไว้ให้โหนดที่มาทีหลัง", 9.0, 11.7),
    ]
    header = make_header(
        "Topics & QoS", "Pub/Sub Compatibility Rule",
        "กฎทอง QoS_Rx ≤ QoS_Tx: ทำไม BEST_EFFORT ถึงคุยกับ RELIABLE บางทิศทางไม่ได้"
    )
    stage = make_stage(120, 324, "DDS QoS Matching: /scan (BEST_EFFORT) & /robot/state (TRANSIENT_LOCAL)")

    n_pub = node_card(44, 184, 210, 146, "Sensor Publisher", "BEST_EFFORT / VOLATILE", "#fefce8", "bb-lidar", "10 Hz Stream", "#fde68a")
    n_dds = node_card(368, 184, 224, 146, "DDS QoS Matcher", "ตรวจ Rx ≤ Tx", "#f8fafc", "bb-server", "Policy Check", "#cbd5e1")
    n_ok = node_card(706, 178, 210, 128, "Sub A (Compatible)", "BEST_EFFORT", "#f0fdf4", "bb-app", "รับข้อความ ✓", "#bbf7d0")
    n_bad = node_card(706, 320, 210, 108, "Sub B (Mismatch)", "ขอ RELIABLE จาก BEST", "#fff1f2", "", "เงียบสนิท ✗", "#fecdd3")

    paths = (
        '<path class="ant-amber" d="M254 257H364" marker-end="url(#bb-ah-amber)"/>'
        '<path class="ant-green" d="M592 242H702" marker-end="url(#bb-ah-green)"/>'
        '<path class="ant-red" d="M592 284L702 368" marker-end="url(#bb-ah-red)"/>'
    )

    anim_css = (
        kf_move("pk-sens", dur, 0.3, 3.0, [(150, 257), (480, 257)])
        + kf_move("pk-ok", dur, 3.1, 5.9, [(480, 242), (790, 242)])
        + kf_pop("bd-ok", dur, 4.0, 5.9)
        + kf_move("pk-bad", dur, 6.0, 8.9, [(480, 284), (630, 336)])
        + kf_pop("bd-bad", dur, 6.9, 8.9)
        + kf_move("pk-lat", dur, 9.0, 11.7, [(150, 257), (480, 257), (790, 242)])
        + kf_pop("bd-lat", dur, 9.8, 11.7)
    )
    anim_els = (
        pkt_chip("pk-sens", "LaserScan", "#fde047", 104)
        + pkt_chip("pk-ok", "Delivered", "#7de3b4", 104)
        + pkt_chip("pk-bad", "QoS Mismatch", "#fb7185", 122)
        + pkt_chip("pk-lat", "Latched State", "#93c5fd", 124)
        + pop_pill("bd-ok", 645, 212, "Rx ≤ Tx ผ่าน!", "#16a34a")
        + pop_pill("bd-bad", 620, 396, "Rx > Tx ปฏิเสธ!", "#e11d48")
        + pop_pill("bd-lat", 480, 180, "TRANSIENT_LOCAL ส่งย้อนหลัง ✓", "#2563eb")
    )

    tbl, tbl_css, tbl_h = make_step_table(464, steps, dur, split_x=256)
    return "ROS 2 Topic QoS Matching", 464 + tbl_h + 24, header + stage + n_pub + n_dds + n_ok + n_bad + paths + anim_els + tbl, anim_css + tbl_css


def build_anim_service_deadlock():
    dur = 12.0
    steps = [
        ("Timer ปลุกเธรด #1", "Timer Callback เรียก Service Client แบบ Async/Wait จาก Callback Group", 0.3, 3.0),
        ("ส่ง Request ออก DDS", "แพ็กเก็ตคำสั่ง /robot/set_power_mode ถูกส่งไปยัง Service Server", 3.1, 5.9),
        ("Server ประมวลผล", "Power Service Server สลับโหมดประหยัดพลังงานแล้วส่ง Response กลับ", 6.0, 8.8),
        ("เธรด #2 รับ Response", "MultiThreadedExecutor + ReentrantCallbackGroup หยิบผลลัพธ์ได้ ไม่ Deadlock!", 8.9, 11.7),
    ]
    header = make_header(
        "Services RPC", "Anti-Deadlock MultiThreadedExecutor",
        "แก้ปัญหา SingleThreadedExecutor ค้าง: แยกเธรดด้วย MultiThreadedExecutor + Callback Group"
    )
    stage = make_stage(120, 310, "Service Request-Response Flow (No Deadlock)")

    n_tmr = node_card(44, 184, 200, 146, "Timer Callback", "Thread #1 (กำลังรอ)", "#eff6ff", "bb-cpu", "ReentrantGroup", "#bfdbfe")
    n_cli = node_card(304, 184, 216, 146, "MultiThreaded Exec", "Pool ≥ 2 Threads", "#faf5ff", "bb-app", "Thread #2 ว่าง!", "#e9d5ff")
    n_srv = node_card(696, 184, 220, 146, "Service Server", "/robot/set_power_mode", "#f0fdf4", "bb-server", "std_srvs/SetBool", "#bbf7d0")

    paths = (
        '<path class="ant-blue" d="M244 242H300" marker-end="url(#bb-ah-blue)"/>'
        '<path class="ant-amber" d="M520 236H692" marker-end="url(#bb-ah-amber)"/>'
        '<path class="ant-green" d="M692 280H520" marker-end="url(#bb-ah-green)"/>'
        '<path class="ant-green" d="M300 280H244" marker-end="url(#bb-ah-green)"/>'
    )

    anim_css = (
        kf_move("pk-call", dur, 0.3, 3.0, [(144, 242), (412, 242)])
        + kf_move("pk-req", dur, 3.1, 5.9, [(412, 236), (790, 236)])
        + kf_pop("bd-srv", dur, 6.2, 8.6)
        + kf_move("pk-res", dur, 8.7, 11.7, [(790, 280), (412, 280), (144, 280)])
        + kf_pop("bd-ok", dur, 9.6, 11.7)
    )
    anim_els = (
        pkt_chip("pk-call", "call_async()", "#93c5fd", 112)
        + pkt_chip("pk-req", "SetBool: true", "#fde047", 114)
        + pkt_chip("pk-res", "success=True", "#7de3b4", 116)
        + pop_pill("bd-srv", 806, 360, "ประมวลผลเสร็จ ✓", "#16a34a")
        + pop_pill("bd-ok", 412, 360, "Thread #2 รับผลลัพธ์ ไม่ค้าง!", "#2563eb")
    )

    tbl, tbl_css, tbl_h = make_step_table(450, steps, dur, split_x=256)
    return "ROS 2 Service Anti-Deadlock", 450 + tbl_h + 24, header + stage + n_tmr + n_cli + n_srv + paths + anim_els + tbl, anim_css + tbl_css


def build_anim_action_preempt():
    dur = 12.0
    steps = [
        ("ส่ง Action Goal #1", "Client ส่งเป้าหมายเดินทาง + 128-bit UUID ผ่าน /send_goal service", 0.3, 2.9),
        ("สตรีม Feedback ต่อเนื่อง", "Server ตอบรับ ACCEPTED แล้วส่งระยะทางคงเหลือ (Feedback) ทุก 100 ms", 3.0, 5.9),
        ("ส่ง Goal #2 (Preempt)", "มีคำสั่งใหม่ฉุกเฉิน! Server สั่ง ABORT/PREEMPT งานเก่าแล้วรับงานใหม่", 6.0, 9.0),
        ("รับ Result สุดท้าย", "งานใหม่วิ่งจนจบแล้วส่ง Result (SUCCEEDED) กลับผ่าน /get_result", 9.1, 11.7),
    ]
    header = make_header(
        "Actions", "Goal, Feedback & Preemption",
        "โปรโตคอล Action (3 Services + 2 Topics): รองรับงานระยะยาว ดูความคืบหน้า และแทรกงานใหม่ได้"
    )
    stage = make_stage(120, 310, "Action Lifecycle: Goal Request → Feedback Stream → Preempt → Result")

    n_cli = node_card(44, 184, 210, 146, "Action Client", "navigate_action_client", "#eff6ff", "bb-app", "Goal UUID", "#bfdbfe")
    n_bus = node_card(356, 184, 248, 146, "Action Protocol (5 ช่อง)", "send / cancel / result + fb / status", "#fefce8", "bb-server", "Non-Blocking", "#fde68a")
    n_srv = node_card(706, 184, 210, 146, "Action Server", "navigate_action_server", "#f0fdf4", "bb-robot", "Reentrant Loop", "#bbf7d0")

    paths = (
        '<path class="ant-blue" d="M254 226H352" marker-end="url(#bb-ah-blue)"/>'
        '<path class="ant-blue" d="M604 226H702" marker-end="url(#bb-ah-blue)"/>'
        '<path class="ant-amber" d="M702 264H254" marker-end="url(#bb-ah-amber)"/>'
        '<path class="ant-green" d="M702 302H254" marker-end="url(#bb-ah-green)"/>'
    )

    anim_css = (
        kf_move("pk-g1", dur, 0.3, 2.9, [(150, 226), (480, 226), (790, 226)])
        + kf_move("pk-fb", dur, 3.0, 5.9, [(790, 264), (480, 264), (150, 264)])
        + kf_move("pk-g2", dur, 6.0, 9.0, [(150, 226), (480, 226), (790, 226)])
        + kf_pop("bd-pre", dur, 7.2, 9.1)
        + kf_move("pk-res", dur, 9.1, 11.7, [(790, 302), (480, 302), (150, 302)])
        + kf_pop("bd-done", dur, 9.8, 11.7)
    )
    anim_els = (
        pkt_chip("pk-g1", "Goal #1 (5m)", "#93c5fd", 112)
        + pkt_chip("pk-fb", "Feedback: 42%", "#fde047", 122)
        + pkt_chip("pk-g2", "Preempt Goal #2", "#fb7185", 132)
        + pkt_chip("pk-res", "SUCCEEDED ✓", "#7de3b4", 116)
        + pop_pill("bd-pre", 811, 360, "ยกเลิก Goal #1 ทันที!", "#e11d48")
        + pop_pill("bd-done", 480, 360, "จบภารกิจ Goal #2 ✓", "#16a34a")
    )

    tbl, tbl_css, tbl_h = make_step_table(450, steps, dur, split_x=256)
    return "ROS 2 Action Protocol & Preemption", 450 + tbl_h + 24, header + stage + n_cli + n_bus + n_srv + paths + anim_els + tbl, anim_css + tbl_css


def build_anim_tf2_transform():
    dur = 12.0
    steps = [
        ("อ่านค่าจาก LiDAR", "LiDAR ตรวจพบวัตถุที่พิกัด (1.20, 0.30, 0.00) ในเฟรม lidar_link", 0.3, 3.0),
        ("อ่าน Static TF", "StaticTransformBroadcaster ส่งค่าติดตั้ง LiDAR (+0.20, 0.0, +0.02) เข้า /tf_static", 3.1, 5.9),
        ("TF2 Buffer คำนวณ", "TransformListener ค้นหาสายสัมพันธ์ base_link → lidar_link จาก Ring Buffer 10 วิ", 6.0, 8.9),
        ("ได้พิกัดในฐานหุ่นยนต์", "แปลงพิกัดสำเร็จ: (1.40, 0.30, 0.02) ในเฟรม base_link พร้อมหลบหลีก", 9.0, 11.7),
    ]
    header = make_header(
        "TF2 Tree", "Coordinate Frame Transformation",
        "การแปลงพิกัดสิ่งกีดขวางจากมุมมองเซนเซอร์ (lidar_link) กลับเข้าศูนย์กลางหุ่นยนต์ (base_link)"
    )
    stage = make_stage(120, 310, "TF2 Pipeline: lidar_link (1.20, 0.30) → TF2 Buffer → base_link (1.40, 0.30)")

    n_lid = node_card(44, 184, 210, 146, "LiDAR Frame", "(1.20, 0.30, 0.00)", "#fefce8", "bb-lidar", "lidar_link", "#fde68a")
    n_tf = node_card(356, 184, 248, 146, "TF2 Buffer & Listener", "lookup_transform(base, lidar)", "#eff6ff", "bb-map", "/tf + /tf_static", "#bfdbfe")
    n_base = node_card(706, 184, 210, 146, "Robot Base Frame", "(1.40, 0.30, 0.02)", "#f0fdf4", "bb-robot", "base_link", "#bbf7d0")

    paths = (
        '<path class="ant-amber" d="M254 257H352" marker-end="url(#bb-ah-amber)"/>'
        '<path class="ant-green" d="M604 257H702" marker-end="url(#bb-ah-green)"/>'
        '<path class="ant-blue" d="M480 356V332" marker-end="url(#bb-ah-blue)"/>'
    )

    anim_css = (
        kf_move("pk-obs", dur, 0.3, 3.0, [(150, 257), (460, 257)])
        + kf_move("pk-tf", dur, 3.1, 5.9, [(480, 376), (480, 300)])
        + kf_pop("bd-calc", dur, 6.2, 8.8)
        + kf_move("pk-out", dur, 8.9, 11.7, [(490, 257), (790, 257)])
        + kf_pop("bd-ok", dur, 9.6, 11.7)
    )
    anim_els = (
        pkt_chip("pk-obs", "p_lidar (1.2, 0.3)", "#fde047", 136)
        + pkt_chip("pk-tf", "dx = +0.20 m", "#93c5fd", 114)
        + pkt_chip("pk-out", "p_base (1.4, 0.3)", "#7de3b4", 136)
        + pop_pill("bd-calc", 480, 180, "คูณ Homogeneous Matrix T", "#2563eb")
        + pop_pill("bd-ok", 811, 360, "แปลงพิกัดสำเร็จ ✓", "#16a34a")
    )

    tbl, tbl_css, tbl_h = make_step_table(450, steps, dur, split_x=256)
    return "TF2 Coordinate Transform Pipeline", 450 + tbl_h + 24, header + stage + n_lid + n_tf + n_base + paths + anim_els + tbl, anim_css + tbl_css


def build_anim_gazebo_bridge():
    dur = 12.0
    steps = [
        ("ส่งคำสั่งผ่าน E-Stop", "ความเร็วจาก /cmd_vel_in ผ่าน Emergency Stop Node (เช็กระยะหน้าหุ่น)", 0.3, 3.0),
        ("ros_gz_bridge แปลงสาร", "parameter_bridge แปลง Twist (CDR) เป็น Gazebo Protobuf เข้า DiffDrive", 3.1, 5.9),
        ("Gazebo Physics 1000 Hz", "ล้อหมุนจริงบนพื้นคลังสินค้า ยิงแสง GPU LiDAR + ส่งเวลา /clock กลับมา", 6.0, 8.9),
        ("ตรวจพบกำแพง < 0.25m", "LaserScan แจ้งระยะใกล้เกิน! E-Stop ตัดความเร็วเหลือ 0 ทันที (ห่าง ~0.33 m)", 9.0, 11.7),
    ]
    header = make_header(
        "Gazebo Bridge", "Actuators, Sensors & Safety Stop",
        "วงรอบจำลองเสมือนจริง: ros_gz_bridge เชื่อม ROS 2 กับ Gazebo Harmonic 8.15 พร้อมระบบ E-Stop"
    )
    stage = make_stage(120, 320, "Simulation Loop: ROS 2 Nodes ↔ parameter_bridge ↔ Gazebo Sim 8.15")

    n_estop = node_card(44, 184, 206, 146, "Emergency Stop Node", "Safety Shield < 0.25m", "#fff1f2", "bb-shield", "/cmd_vel_in → /cmd_vel", "#fecdd3")
    n_br = node_card(356, 184, 248, 146, "ros_gz_bridge", "CDR ↔ Protobuf", "#eff6ff", "bb-server", "/clock, /odom, /scan", "#bfdbfe")
    n_gz = node_card(706, 184, 210, 146, "Gazebo Sim Harmonic", "DiffDrive + GPU LiDAR", "#f0fdf4", "bb-robot", "Physics 1000 Hz", "#bbf7d0")

    paths = (
        '<path class="ant-blue" d="M250 232H352" marker-end="url(#bb-ah-blue)"/>'
        '<path class="ant-blue" d="M604 232H702" marker-end="url(#bb-ah-blue)"/>'
        '<path class="ant-amber" d="M702 284H604" marker-end="url(#bb-ah-amber)"/>'
        '<path class="ant-amber" d="M352 284H250" marker-end="url(#bb-ah-amber)"/>'
    )

    anim_css = (
        kf_move("pk-vel", dur, 0.3, 3.0, [(148, 232), (480, 232)])
        + kf_move("pk-gz", dur, 3.1, 5.9, [(480, 232), (800, 232)])
        + kf_move("pk-scan", dur, 6.0, 8.9, [(800, 284), (480, 284), (148, 284)])
        + kf_pop("bd-stop", dur, 9.2, 11.7)
    )
    anim_els = (
        pkt_chip("pk-vel", "/cmd_vel (0.3 m/s)", "#93c5fd", 132)
        + pkt_chip("pk-gz", "Gz Twist Proto", "#7de3b4", 122)
        + pkt_chip("pk-scan", "/scan (min 0.24m)", "#fde047", 136)
        + pop_pill("bd-stop", 147, 366, "E-STOP ตัดความเร็ว = 0!", "#e11d48")
    )

    tbl, tbl_css, tbl_h = make_step_table(460, steps, dur, split_x=256)
    return "Gazebo Bridge & Emergency Stop", 460 + tbl_h + 24, header + stage + n_estop + n_br + n_gz + paths + anim_els + tbl, anim_css + tbl_css


def build_anim_slam_loop():
    dur = 12.0
    steps = [
        ("Scan Matching", "SLAM Toolbox จับคู่ LaserScan ปัจจุบันเข้ากับ Scan ก่อนหน้าใน Pose Graph", 0.3, 3.0),
        ("เพิ่ม Node & Edge", "สร้างจุดพิกัดใหม่ในกราฟพร้อมขอบความสัมพันธ์จาก /odom", 3.1, 5.8),
        ("ตรวจพบ Loop Closure!", "หุ่นยนต์วนกลับมาจุดเดิมที่เคยสแกนไว้ → เกิด Loop Closure Edge", 5.9, 8.9),
        ("Ceres Solver ปรับแผนที่", "แก้สมการ Graph Optimization ลด Drift แล้วเขียนแผนที่ /map (200×199 @ 5cm)", 9.0, 11.7),
    ]
    header = make_header(
        "SLAM Toolbox", "Pose Graph & Ceres Loop Closure",
        "การสร้างแผนที่ 2 มิติและแก้ปัญหาแผนที่เบี้ยว (Odometry Drift) เมื่อหุ่นยนต์วนกลับมาจุดเดิม"
    )
    stage = make_stage(120, 310, "Online Async SLAM Pipeline: /scan + /odom → Pose Graph → Ceres → /map")

    n_in = node_card(44, 184, 200, 146, "Sensors & Odom", "/scan + /odom + /tf", "#fefce8", "bb-lidar", "20 Hz Input", "#fde68a")
    n_pg = node_card(356, 184, 248, 146, "SLAM Toolbox", "Scan Matcher + Pose Graph", "#eff6ff", "bb-cpu", "Loop Closure", "#bfdbfe")
    n_map = node_card(706, 184, 210, 146, "Occupancy Grid", "200×199 @ 0.05m", "#f0fdf4", "bb-map", "/map (89.4% Walls)", "#bbf7d0")

    paths = (
        '<path class="ant-amber" d="M244 257H352" marker-end="url(#bb-ah-amber)"/>'
        '<path class="ant-green" d="M604 257H702" marker-end="url(#bb-ah-green)"/>'
    )

    anim_css = (
        kf_move("pk-sc", dur, 0.3, 3.0, [(144, 257), (460, 257)])
        + kf_pop("bd-edge", dur, 3.3, 5.7)
        + kf_pop("bd-loop", dur, 6.0, 8.9)
        + kf_move("pk-map", dur, 9.0, 11.7, [(490, 257), (800, 257)])
        + kf_pop("bd-opt", dur, 9.6, 11.7)
    )
    anim_els = (
        pkt_chip("pk-sc", "Scan + Odom", "#fde047", 116)
        + pkt_chip("pk-map", "Updated /map", "#7de3b4", 118)
        + pop_pill("bd-edge", 480, 180, "+ Pose Node & Odom Edge", "#2563eb")
        + pop_pill("bd-loop", 480, 360, "Loop Closure Detected! ⚡", "#d97706")
        + pop_pill("bd-opt", 811, 360, "Ceres แก้ Drift สำเร็จ ✓", "#16a34a")
    )

    tbl, tbl_css, tbl_h = make_step_table(450, steps, dur, split_x=256)
    return "SLAM Toolbox Loop Closure", 450 + tbl_h + 24, header + stage + n_in + n_pg + n_map + paths + anim_els + tbl, anim_css + tbl_css


def build_anim_nav2_amcl():
    dur = 12.0
    steps = [
        ("AMCL ระบุตำแหน่ง", "Particle Filter เทียบ /scan กับแผนที่ /map แล้วส่ง TF map → odom", 0.3, 3.0),
        ("Costmap 2D ซ้อนเลเยอร์", "รวม Static + Obstacle + Inflation Layer (และ Keepout/Speed Filter)", 3.1, 5.9),
        ("Global Planner วางเส้นทาง", "NavFn (A*/Dijkstra) คำนวณเส้นทางหลักหลีกเลี่ยงกำแพงและเขตห้ามเข้า", 6.0, 8.9),
        ("DWB Controller ขับเคลื่อน", "คำนวณความเร็วปลอดภัย /cmd_vel วิ่งถึงเป้าหมาย (NavigateToPose 14.2s)", 9.0, 11.7),
    ]
    header = make_header(
        "Nav2 Stack", "AMCL, Costmaps, Planner & DWB",
        "วงจรนำทางอัตโนมัติ: รู้ตำแหน่ง (AMCL) → ประเมินพื้นที่อันตราย (Costmap) → วางแผนและควบคุม"
    )
    stage = make_stage(120, 320, "Nav2 Navigation Loop: AMCL → Costmap 2D → Planner → DWB → /cmd_vel")

    n_amcl = node_card(44, 184, 196, 146, "AMCL Localizer", "KLD Particle Filter", "#fefce8", "bb-lidar", "map → odom", "#fde68a")
    n_cost = node_card(272, 184, 196, 146, "Costmap 2D", "Static/Obs/Inflation", "#fff1f2", "bb-map", "Keepout + Speed", "#fecdd3")
    n_plan = node_card(500, 184, 196, 146, "NavFn Planner", "Global Path (A*)", "#eff6ff", "bb-doc", "compute_path", "#bfdbfe")
    n_ctrl = node_card(728, 184, 188, 146, "DWB Controller", "Local Trajectory", "#f0fdf4", "bb-robot", "Pub: /cmd_vel", "#bbf7d0")

    paths = (
        '<path class="ant-amber" d="M240 257H268" marker-end="url(#bb-ah-amber)"/>'
        '<path class="ant-red" d="M468 257H496" marker-end="url(#bb-ah-red)"/>'
        '<path class="ant-blue" d="M696 257H724" marker-end="url(#bb-ah-blue)"/>'
    )

    anim_css = (
        kf_move("pk-pose", dur, 0.3, 3.0, [(142, 257), (350, 257)])
        + kf_move("pk-grid", dur, 3.1, 5.9, [(370, 257), (580, 257)])
        + kf_move("pk-path", dur, 6.0, 8.9, [(598, 257), (810, 257)])
        + kf_pop("bd-goal", dur, 9.2, 11.7)
    )
    anim_els = (
        pkt_chip("pk-pose", "Pose + TF", "#fde047", 98)
        + pkt_chip("pk-grid", "Cost Grid", "#fb7185", 98)
        + pkt_chip("pk-path", "Global Path", "#93c5fd", 110)
        + pop_pill("bd-goal", 822, 366, "/cmd_vel ถึงเป้าใน 14.2s ✓", "#16a34a")
    )

    tbl, tbl_css, tbl_h = make_step_table(460, steps, dur, split_x=256)
    return "Nav2 Navigation Stack Loop", 460 + tbl_h + 24, header + stage + n_amcl + n_cost + n_plan + n_ctrl + paths + anim_els + tbl, anim_css + tbl_css


def build_anim_ros2_control():
    dur = 12.0
    steps = [
        ("อ่าน Encoder (read)", "Hardware Interface อ่านความเร็วล้อล่าสุดลง State Buffer (100 Hz)", 0.3, 3.0),
        ("รับคำสั่ง TwistStamped", "diff_drive_controller รับ /diff_drive_controller/cmd_vel (มาตรฐาน Jazzy)", 3.1, 5.9),
        ("คำนวณ IK (update)", "แปลง (v=0.5, ω=1.0) เป็นความเร็วล้อ ซ้าย 4.75 / ขวา 7.75 rad/s", 6.0, 8.9),
        ("สั่งขับมอเตอร์ (write)", "เขียน Command Buffer ส่งไปยัง Mock / Gazebo gz_ros2_control / MCU จริง", 9.0, 11.7),
    ]
    header = make_header(
        "ros2_control", "100 Hz Real-Time Control Loop",
        "วงรอบควบคุมมาตรฐานอุตสาหกรรม: read() → update() → write() ป้องกัน Jitter และแยกลอจิกจากฮาร์ดแวร์"
    )
    stage = make_stage(120, 320, "Control Loop (T = 10 ms): Controller Manager ↔ Hardware Interface ↔ Actuators")

    n_nav = node_card(44, 184, 206, 146, "Nav2 / Teleop", "TwistStamped Only", "#eff6ff", "bb-app", "v=0.5, ω=1.0", "#bfdbfe")
    n_cm = node_card(348, 184, 264, 146, "Controller Manager", "diff_drive_controller + JSB", "#fefce8", "bb-cpu", "read → update → write", "#fde68a")
    n_hw = node_card(710, 184, 206, 146, "Hardware Interface", "GenericSystem / Gazebo", "#f0fdf4", "bb-nic", "L:4.75 R:7.75 rad/s", "#bbf7d0")

    paths = (
        '<path class="ant-blue" d="M250 257H344" marker-end="url(#bb-ah-blue)"/>'
        '<path class="ant-amber" d="M710 228H616" marker-end="url(#bb-ah-amber)"/>'
        '<path class="ant-green" d="M616 286H710" marker-end="url(#bb-ah-green)"/>'
    )

    anim_css = (
        kf_move("pk-rd", dur, 0.3, 3.0, [(800, 228), (480, 228)])
        + kf_move("pk-cmd", dur, 3.1, 5.9, [(147, 257), (480, 257)])
        + kf_pop("bd-ik", dur, 6.1, 8.8)
        + kf_move("pk-wr", dur, 8.9, 11.7, [(480, 286), (800, 286)])
        + kf_pop("bd-ok", dur, 9.6, 11.7)
    )
    anim_els = (
        pkt_chip("pk-rd", "read() Encoders", "#fde047", 126)
        + pkt_chip("pk-cmd", "TwistStamped", "#93c5fd", 118)
        + pkt_chip("pk-wr", "write() 7.75 rad/s", "#7de3b4", 136)
        + pop_pill("bd-ik", 480, 180, "IK: ωL=4.75, ωR=7.75 rad/s", "#2563eb")
        + pop_pill("bd-ok", 813, 366, "ตรงตามทฤษฎี 100% ✓", "#16a34a")
    )

    tbl, tbl_css, tbl_h = make_step_table(460, steps, dur, split_x=256)
    return "ros2_control 100 Hz Loop", 460 + tbl_h + 24, header + stage + n_nav + n_cm + n_hw + paths + anim_els + tbl, anim_css + tbl_css


def build_anim_vision_docking():
    dur = 12.0
    steps = [
        ("รับภาพ & แปลง cv_bridge", "รับภาพจากกล้อง (sensor_data QoS) แปลงเข้า OpenCV หา Tag 36h11", 0.3, 3.0),
        ("solvePnP หาพิกัด 6-DoF", "คำนวณตำแหน่งแท่นชาร์จ 3 มิติได้แม่นระดับ 0.99 mm / 0.23°", 3.1, 5.9),
        ("opennav_docking", "Docking Server (DockRobot) ควบคุมความเร็วต่ำ 0.05 m/s ถอยเข้าซอง", 6.0, 8.9),
        ("จอดสนิทระดับมิลลิเมตร", "เทียบกับ Ground Truth คลาดเคลื่อนเพียง 2.2–14.5 mm (เทียบกับ 48.9 mm ถ้าปิดกล้อง)", 9.0, 11.7),
    ]
    header = make_header(
        "Vision + Docking", "AprilTag PnP & opennav_docking",
        "การผสานระบบมองเห็น 6-DoF เข้ากับ Nav2 Docking Server เพื่อถอยเข้าแท่นชาร์จความแม่นยำสูง"
    )
    stage = make_stage(120, 320, "Closed-Loop Precision Docking: Camera → solvePnP → opennav_docking → Dock")

    n_cam = node_card(44, 184, 196, 146, "Camera + cv_bridge", "AprilTag 36h11", "#fefce8", "bb-app", "sensor_data QoS", "#fde68a")
    n_pnp = node_card(272, 184, 206, 146, "solvePnP Tracker", "6-DoF Pose (0.99 mm)", "#eff6ff", "bb-cpu", "/detected_dock_pose", "#bfdbfe")
    n_dock = node_card(510, 184, 206, 146, "opennav_docking", "SimpleChargingDock", "#faf5ff", "bb-server", "DockRobot Action", "#e9d5ff")
    n_chg = node_card(748, 184, 168, 146, "Charging Dock", "ถอยจอด 0.05 m/s", "#f0fdf4", "bb-robot", "Error ≤ 15 mm", "#bbf7d0")

    paths = (
        '<path class="ant-amber" d="M240 257H268" marker-end="url(#bb-ah-amber)"/>'
        '<path class="ant-blue" d="M478 257H506" marker-end="url(#bb-ah-blue)"/>'
        '<path class="ant-green" d="M716 257H744" marker-end="url(#bb-ah-green)"/>'
    )

    anim_css = (
        kf_move("pk-img", dur, 0.3, 3.0, [(142, 257), (360, 257)])
        + kf_move("pk-tag", dur, 3.1, 5.9, [(375, 257), (600, 257)])
        + kf_move("pk-srv", dur, 6.0, 8.9, [(613, 257), (820, 257)])
        + kf_pop("bd-mm", dur, 9.1, 11.7)
    )
    anim_els = (
        pkt_chip("pk-img", "Image + Info", "#fde047", 110)
        + pkt_chip("pk-tag", "Dock Pose 3D", "#93c5fd", 114)
        + pkt_chip("pk-srv", "Reverse Servo", "#7de3b4", 118)
        + pop_pill("bd-mm", 832, 366, "จอดแม่น 2–14 mm ✓", "#16a34a")
    )

    tbl, tbl_css, tbl_h = make_step_table(460, steps, dur, split_x=256)
    return "Vision AprilTag & Precision Docking", 460 + tbl_h + 24, header + stage + n_cam + n_pnp + n_dock + n_chg + paths + anim_els + tbl, anim_css + tbl_css


def build_anim_openrmf_fleet():
    dur = 12.0
    steps = [
        ("แยก Namespace + Prefix", "หุ่นยนต์ /amr_01 และ /amr_02 ใช้ frame_prefix แยก TF ไม่ตีกัน", 0.3, 3.0),
        ("ส่งคำขอเส้นทางเข้าส่วนกลาง", "Fleet Adapter ส่งแผนเส้นทางของทั้ง 2 คันเข้า rmf_traffic_schedule", 3.1, 5.9),
        ("ตรวจพบการสวนทางช่องแคบ", "Schedule ตรวจพบจุดตัดเวลา-พื้นที่ (Conflict) แล้วเปิด Negotiation", 6.0, 8.9),
        ("จัดคิวหลีกทางอัตโนมัติ", "amr_02 หยุดรอในจุดพักชั่วคราวให้ amr_01 ผ่านก่อน ปลอดภัย 100%", 9.0, 11.7),
    ]
    header = make_header(
        "Open-RMF Fleet", "Multi-Robot Deconfliction",
        "การคุมฝูงหุ่นยนต์หลายคัน: แยก Namespace/TF และแก้ปัญหาทางแคบด้วย rmf_traffic_schedule"
    )
    stage = make_stage(120, 342, "Multi-Robot Fleet: /amr_01 & /amr_02 ↔ Fleet Adapter ↔ rmf_traffic_schedule")

    n_r1 = node_card(44, 176, 210, 128, "/amr_01", "frame_prefix: amr_01/", "#eff6ff", "bb-robot", "ไปข้างหน้า ✓", "#bfdbfe")
    n_r2 = node_card(44, 316, 210, 128, "/amr_02", "frame_prefix: amr_02/", "#fefce8", "bb-robot", "รอจังหวะ ⏸", "#fde68a")
    n_fa = node_card(366, 204, 228, 160, "RMF Fleet Adapter", "EasyFullControl Config", "#faf5ff", "bb-server", "nav_graph.yaml", "#e9d5ff")
    n_sch = node_card(706, 204, 210, 160, "rmf_traffic_schedule", "Space-Time Deconfliction", "#f0fdf4", "bb-shield", "QuickestFinish", "#bbf7d0")

    paths = (
        '<path class="ant-blue" d="M254 240H362" marker-end="url(#bb-ah-blue)"/>'
        '<path class="ant-amber" d="M254 366L362 312" marker-end="url(#bb-ah-amber)"/>'
        '<path class="ant-green" d="M594 284H702" marker-end="url(#bb-ah-green)"/>'
    )

    anim_css = (
        kf_move("pk-r1", dur, 0.3, 3.0, [(150, 240), (470, 240)])
        + kf_move("pk-r2", dur, 3.1, 5.9, [(150, 366), (310, 336), (470, 304)])
        + kf_move("pk-neg", dur, 6.0, 8.9, [(480, 284), (790, 284)])
        + kf_pop("bd-safe", dur, 9.1, 11.7)
    )
    anim_els = (
        pkt_chip("pk-r1", "amr_01 Path", "#93c5fd", 108)
        + pkt_chip("pk-r2", "amr_02 Path", "#fde047", 108)
        + pkt_chip("pk-neg", "Negotiation", "#7de3b4", 114)
        + pop_pill("bd-safe", 811, 404, "ไม่ชนกัน! ผ่านทีละคัน ✓", "#16a34a")
    )

    tbl, tbl_css, tbl_h = make_step_table(482, steps, dur, split_x=256)
    return "Open-RMF Multi-Robot Fleet", 482 + tbl_h + 24, header + stage + n_r1 + n_r2 + n_fa + n_sch + paths + anim_els + tbl, anim_css + tbl_css


def build_anim_capstone_mission():
    dur = 14.0
    steps = [
        ("Stage 0: Lifecycle Check", "ตรวจ Lifecycle ทั้ง 11 โหนดใน Nav2/Docking ต้องอยู่สถานะ ACTIVE 100%", 0.3, 2.8),
        ("Pick & Drop Cargo", "Nav2 + AMCL นำทางไปรับและส่งสินค้า (คลาดเคลื่อน ≤ 0.26 m / AMCL ≤ 0.09 m)", 2.9, 5.8),
        ("Docking & Undock", "AprilTag + DockRobot ถอยเข้าชาร์จแม่นยำ 2.2–4.5 mm แล้วถอยออก", 5.9, 9.0),
        ("E-Stop Fault Injection", "collision_monitor StopZone ตัดความเร็วใน 48–104 ms เหลือระยะห่าง 5.6–7.4 cm", 9.1, 11.8),
        ("Return Home & KPI", "กลับจุดเริ่มต้นพร้อมสรุปตาราง KPI 5/5 รอบ ผ่านเกณฑ์ระดับ Excellence!", 11.9, 13.7),
    ]
    header = make_header(
        "Capstone AMR", "7-Stage Warehouse Mission & KPIs",
        "ภาพรวมระบบคลังสินค้าบูรณาการเต็มรูปแบบ: Lifecycle + Nav2 + AprilTag Docking + E-Stop"
    )
    stage = make_stage(120, 320, "End-to-End Mission: Lifecycle → Pick/Drop → Dock/Undock → E-Stop → Home")

    n_lc = node_card(42, 184, 152, 146, "0. Lifecycle", "11/11 Active", "#faf5ff", "bb-cpu", "Supervisor", "#e9d5ff")
    n_nav = node_card(228, 184, 160, 146, "1-2. Pick/Drop", "Nav2 + AMCL", "#eff6ff", "bb-map", "Err 0.25 m", "#bfdbfe")
    n_dock = node_card(422, 184, 164, 146, "3-4. Dock/Undock", "AprilTag + Dock", "#f0fdf4", "bb-robot", "2.2–4.5 mm", "#bbf7d0")
    n_stop = node_card(620, 184, 156, 146, "5. E-Stop Test", "StopZone Guard", "#fff1f2", "bb-shield", "48–104 ms", "#fecdd3")
    n_kpi = node_card(808, 184, 110, 146, "6. Home", "5/5 PASS", "#fefce8", "bb-doc", "KPI OK", "#fde68a")

    paths = (
        '<path class="ant" d="M194 257H224" marker-end="url(#bb-ah)"/>'
        '<path class="ant-blue" d="M388 257H418" marker-end="url(#bb-ah-blue)"/>'
        '<path class="ant-green" d="M586 257H616" marker-end="url(#bb-ah-green)"/>'
        '<path class="ant-red" d="M776 257H804" marker-end="url(#bb-ah-red)"/>'
    )

    anim_css = (
        kf_move("pk-m1", dur, 0.3, 5.8, [(118, 257), (308, 257)])
        + kf_move("pk-m2", dur, 5.9, 9.0, [(308, 257), (504, 257)])
        + kf_move("pk-m3", dur, 9.1, 11.8, [(504, 257), (698, 257)])
        + kf_pop("bd-es", dur, 9.6, 11.8)
        + kf_move("pk-m4", dur, 11.9, 13.7, [(698, 257), (863, 257)])
        + kf_pop("bd-pass", dur, 12.2, 13.7)
    )
    anim_els = (
        pkt_chip("pk-m1", "Mission Nav", "#93c5fd", 104)
        + pkt_chip("pk-m2", "Dock 2.2mm", "#7de3b4", 104)
        + pkt_chip("pk-m3", "StopZone!", "#fb7185", 96)
        + pkt_chip("pk-m4", "5/5 PASS ✓", "#fde047", 104)
        + pop_pill("bd-es", 698, 366, "เบรกทัน ห่าง 6 cm!", "#e11d48")
        + pop_pill("bd-pass", 848, 160, "KPI ผ่านทุกด่าน ✓", "#16a34a")
    )

    tbl, tbl_css, tbl_h = make_step_table(460, steps, dur, split_x=256)
    return "Capstone Warehouse AMR Mission", 460 + tbl_h + 24, header + stage + n_lc + n_nav + n_dock + n_stop + n_kpi + paths + anim_els + tbl, anim_css + tbl_css


BUILDERS = {
    "anim-ros2-dds": build_anim_ros2_dds,
    "anim-topic-qos": build_anim_topic_qos,
    "anim-service-deadlock": build_anim_service_deadlock,
    "anim-action-preempt": build_anim_action_preempt,
    "anim-tf2-transform": build_anim_tf2_transform,
    "anim-gazebo-bridge": build_anim_gazebo_bridge,
    "anim-slam-loop": build_anim_slam_loop,
    "anim-nav2-amcl": build_anim_nav2_amcl,
    "anim-ros2-control": build_anim_ros2_control,
    "anim-vision-docking": build_anim_vision_docking,
    "anim-openrmf-fleet": build_anim_openrmf_fleet,
    "anim-capstone-mission": build_anim_capstone_mission,
}


def prepare_font_dir(tmp: Path) -> Path:
    for src in FONT_SOURCES:
        if not src.exists():
            raise FileNotFoundError(f"missing required font: {src}")
        (tmp / src.name).symlink_to(src)
    return tmp


def render_one(name: str, font_dir: Path) -> Path:
    title, height, body, extra_css = BUILDERS[name]()
    raw_for_fonts = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 {height}" '
        f'width="960" height="{height}" role="img">'
        f'<title>{esc(title)}</title>'
        f'{SHARED_SYMBOLS}'
        f'<rect width="960" height="{height}" rx="18" fill="#eceef9" stroke="#cbd5e1" stroke-width="2"/>'
        f'{body}</svg>'
    )
    faces = diagram_postprocess.font_faces(raw_for_fonts, font_dir)
    full_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 {height}" '
        f'width="960" height="{height}" role="img" style="background-color: transparent;">'
        f'<title>{esc(title)}</title>'
        f'<style>{faces}{BASE_CSS}{extra_css}</style>'
        f'{SHARED_SYMBOLS}'
        f'<rect width="960" height="{height}" rx="18" fill="#eceef9" stroke="#cbd5e1" stroke-width="2"/>'
        f'{body}</svg>'
    )
    ET.fromstring(full_svg)
    out = DIAG_DIR / f"{name}.svg"
    out.write_text(full_svg, encoding="utf-8")
    return out


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--list":
        for name in sorted(BUILDERS):
            print(name)
        return 0
    targets = sys.argv[1:] if len(sys.argv) > 1 else sorted(BUILDERS)
    unknown = [t for t in targets if t not in BUILDERS]
    if unknown:
        print(f"ERROR: unknown animated diagram(s): {unknown}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        font_dir = prepare_font_dir(Path(tmp))
        for name in targets:
            out = render_one(name, font_dir)
            print(f"  {out.name:<34s} {out.stat().st_size // 1024:5d} KB (animated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
