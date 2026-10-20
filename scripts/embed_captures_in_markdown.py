import os
import re
from generate_all_terminal_captures import captures

root_dir = "/mnt/sda/ros/Essential_ROS"

for week_folder, (title, lines) in captures.items():
    week_path = os.path.join(root_dir, week_folder)
    readme_path = os.path.join(week_path, "Readme.md")
    
    lab_filename = "Exam_Task.md" if week_folder == "Week_08_Midterm_Practical_Exam" else "Lab_Exercises.md"
    lab_path = os.path.join(week_path, lab_filename)
    
    terminal_block = "\n".join([text for text, _ in lines])
    
    # 1. Update Readme.md (Tutorial)
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "images/terminal_run.png" not in content:
            section_readme = f"""## 📸 ภาพผลการทดสอบจริงจากระบบ (Live Execution & Terminal Capture)
ผลลัพธ์จากการรันคำสั่งและโหนดจริงในระบบ เพื่อใช้เป็นข้อมูลอ้างอิงในการตรวจสอบความถูกต้อง:

![Terminal Capture: {title}](images/terminal_run.png)

```console
{terminal_block}
```

---

"""
            # Insert before Troubleshooting or CLI Table or Quiz
            if "## ⚠️ ปัญหาที่พบบ่อยและการแก้ไข" in content:
                content = content.replace("## ⚠️ ปัญหาที่พบบ่อยและการแก้ไข", section_readme + "## ⚠️ ปัญหาที่พบบ่อยและการแก้ไข")
            elif "## 📝 แบบทดสอบท้ายบท" in content:
                content = content.replace("## 📝 แบบทดสอบท้ายบท", section_readme + "## 📝 แบบทดสอบท้ายบท")
            elif "## 🗣️ คลังคำถามสัมภาษณ์ปากเปล่า" in content:
                content = content.replace("## 🗣️ คลังคำถามสัมภาษณ์ปากเปล่า", section_readme + "## 🗣️ คลังคำถามสัมภาษณ์ปากเปล่า")
            else:
                content += "\n\n" + section_readme
                
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Updated Tutorial Readme: {readme_path}")
            
    # 2. Update Lab file (Lab Manual)
    if os.path.exists(lab_path):
        with open(lab_path, "r", encoding="utf-8") as f:
            lab_content = f.read()
            
        if "images/terminal_run.png" not in lab_content:
            section_lab = f"""## 📸 ภาพผลลัพธ์การรันจริงในระบบ (Verified Lab Execution Screenshot)
ผู้เรียนสามารถตรวจสอบความถูกต้องของผลลัพธ์ที่ได้จากการทำแล็บ เทียบกับภาพบันทึกหน้าจอการรันจริงในระบบ:

![Verified Lab Execution: {title}](images/terminal_run.png)

```console
{terminal_block}
```

---

"""
            if "## 📋 สรุปสิ่งที่ต้องส่งมอบ" in lab_content:
                lab_content = lab_content.replace("## 📋 สรุปสิ่งที่ต้องส่งมอบ", section_lab + "## 📋 สรุปสิ่งที่ต้องส่งมอบ")
            elif "## 📋 เกณฑ์การให้คะแนน" in lab_content:
                lab_content = lab_content.replace("## 📋 เกณฑ์การให้คะแนน", section_lab + "## 📋 เกณฑ์การให้คะแนน")
            elif "## 🧪 คำสั่งทดสอบและตรวจให้คะแนน" in lab_content:
                lab_content = lab_content.replace("## 🧪 คำสั่งทดสอบและตรวจให้คะแนน", section_lab + "## 🧪 คำสั่งทดสอบและตรวจให้คะแนน")
            elif "## 🏆 เกณฑ์การประเมินผล" in lab_content:
                lab_content = lab_content.replace("## 🏆 เกณฑ์การประเมินผล", section_lab + "## 🏆 เกณฑ์การประเมินผล")
            else:
                lab_content += "\n\n" + section_lab
                
            with open(lab_path, "w", encoding="utf-8") as f:
                f.write(lab_content)
            print(f"Updated Lab Manual: {lab_path}")

print("All Markdown files updated successfully!")
