# 🖼️ แผนภาพของหลักสูตร (Course Diagrams)

แผนภาพทุกภาพในหลักสูตร (Flowchart, Sequence Diagram, State Diagram) เป็นไฟล์ SVG สไตล์การ์ด (กล่องมุมโค้ง สีพาสเทล เงาบาง ป้ายหัวกลุ่มสีทึบ) ที่ render จากต้นฉบับ Mermaid ในโฟลเดอร์ [`src/`](src/) ส่วนตาราง ผลลัพธ์จาก terminal โค้ด และผังไดเรกทอรีคงเป็นข้อความ Markdown เพื่อให้ค้นหาและ copy ได้

## แก้ไขแผนภาพ

1. แก้ไฟล์ `src/<ชื่อ>.mmd` (ไวยากรณ์ Mermaid ปกติ: `flowchart`, `sequenceDiagram`, `stateDiagram-v2`)
2. รัน `make diagrams` ที่ root ของ repo หรือ `scripts/render_diagrams.sh <ชื่อ>` เพื่อ render เฉพาะภาพนั้น
3. เปิดไฟล์ `docs/diagrams/<ชื่อ>.svg` ดูผล แล้ว commit ทั้ง `.mmd` และ `.svg`

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
