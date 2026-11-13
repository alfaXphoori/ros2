# 🖼️ แผนภาพของโปรเจกต์ (Project Diagrams)

แผนภาพทั้งหมดในโปรเจกต์แบ่งออกเป็น 2 กลุ่ม:

1. **แผนภาพสถาปัตยกรรมแบบนิ่ง (`*.svg`):** สไตล์การ์ด (กล่องมุมโค้ง สีพาสเทล เงาบาง ป้ายหัวกลุ่มสีทึบ) render จากต้นฉบับ Mermaid ในโฟลเดอร์ [`src/`](src/)
2. **แผนภาพแอนิเมชัน (`anim-*.svg`):** แผนภาพเคลื่อนไหวสไตล์ ByteByteGo (Pure SVG + CSS `@keyframes` พร้อมตารางลำดับขั้นตอนด้านล่าง, ไม่ใช้ JavaScript จึงแสดงผลแอนิเมชันได้บน GitHub) สร้างจากสคริปต์ [`../../scripts/render_animated_diagrams.py`](../../scripts/render_animated_diagrams.py)

ส่วนตาราง ผลลัพธ์จาก terminal โค้ด และผังไดเรกทอรีคงเป็นข้อความ Markdown เพื่อให้ค้นหาและ copy ได้

## แก้ไขแผนภาพ

1. **แผนภาพนิ่ง:** แก้ไฟล์ `src/<ชื่อ>.mmd` (ไวยากรณ์ Mermaid ปกติ: `flowchart`, `sequenceDiagram`, `stateDiagram-v2`)
2. **แผนภาพแอนิเมชัน:** แก้ฟังก์ชัน builder ใน [`../../scripts/render_animated_diagrams.py`](../../scripts/render_animated_diagrams.py) (หรือตัวช่วยกลางใน [`../../scripts/anim_svg_ui.py`](../../scripts/anim_svg_ui.py))
3. รัน `make diagrams` ที่ root ของ repo (จะรันทั้ง `scripts/render_diagrams.sh` และ `scripts/render_animated_diagrams.py`)
4. เปิดไฟล์ `docs/diagrams/<ชื่อ>.svg` ดูผล แล้ว commit ทั้งไฟล์ต้นฉบับและ `.svg`

อย่าแก้ไฟล์ `.svg` ด้วยมือ เพราะจะถูกเขียนทับในการ render ครั้งถัดไป

## สิ่งที่ต้องมีในเครื่อง

- `docker` กับ image `minlag/mermaid-cli:11.4.2` (เปลี่ยนได้ด้วยตัวแปร `MMDC_IMAGE`)
- `python3` และ `libharfbuzz-subset0` (ใช้ตัดฟอนต์ให้เหลือเฉพาะตัวอักษรที่ใช้)
- `fonts-noto-core` และ `fonts-dejavu-core`

## ขั้นตอนภายใน

```
src/<ชื่อ>.mmd ──mmdc (ธีม mermaid-config.json)──▶ raw SVG ──diagram_postprocess.py──▶ <ชื่อ>.svg
```

- [`mermaid-config.json`](mermaid-config.json): ธีม `base` ฟอนต์ Noto Sans / Noto Sans Thai เส้นหนา 2px
- [`../../scripts/diagram_postprocess.py`](../../scripts/diagram_postprocess.py): ทำมุมโค้ง ใส่เงา ทำป้ายหัวกลุ่ม ใส่พื้นหลังการ์ดสีขาว และฝังฟอนต์แบบ subset เพื่อให้ภาษาไทยแสดงเหมือนกันทุกเครื่อง

## สีของ class (ใช้ใน `classDef`)

| class | ความหมาย | fill / stroke |
|---|---|---|
| `node`, `ros` | ROS 2 Node / Topic / Service / Action | `#dbeafe` / `#2563eb` |
| `sim`, `nav` | Gazebo Sim / Nav2 / SLAM / TF2 / Path | `#dcfce7` / `#16a34a` |
| `hw`, `sensor` | Hardware / `ros2_control` / Sensor / Camera | `#fef3c7` / `#d97706` |
| `sec`, `safety` | Security (SROS 2) / E-Stop / Fault / Exam | `#ffe4e6` / `#e11d48` |
| `bt`, `phase` | Behavior Tree / Lifecycle / Phase | `#ede9fe` / `#7c3aed` |
| `tool`, `doc` | CLI / Docker / Developer Tools / Docs | `#ffedd5` / `#ea580c` |
| `file`, `cfg` | Config YAML / URDF / SDF / Logs | `#f1f5f9` / `#64748b` |
