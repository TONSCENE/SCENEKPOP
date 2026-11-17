# SCENEKPOP+ Directory

คลังรวมคลิปซับไทยและวาไรตี้ K-Pop จากช่อง [@SCENEKPOP](https://www.youtube.com/@SCENEKPOP) แบบแยกดูตามวงได้ ครบทั้งรายการวาไรตี้, Weverse / IG Live, รายการวิทยุ และสเตจต่างๆ

## ลิงก์หลัก
- **หน้าเว็บออนไลน์ (GitHub Pages)**: https://tonscene.github.io/SCENEKPOP/
- **GitHub Repository**: https://github.com/TONSCENE/SCENEKPOP
- **YouTube**: https://www.youtube.com/@SCENEKPOP
- **Patreon (ซับไทยพิเศษ & สนับสนุนช่อง)**: https://www.patreon.com/c/SCENEKPOP

---

## ลิงก์แยกตามวง (นำไปแชร์ต่อได้เลย)

| วง / หมวดหมู่ | จำนวนคลิป | ลิงก์เปิดดูเฉพาะวง |
| :--- | :---: | :--- |
| **QWER** | 115 | https://tonscene.github.io/SCENEKPOP/#group=qwer |
| **Hearts2Hearts** | 75 | https://tonscene.github.io/SCENEKPOP/#group=hearts2hearts |
| **RESCENE** | 50 | https://tonscene.github.io/SCENEKPOP/#group=rescene |
| **tripleS** | 19 | https://tonscene.github.io/SCENEKPOP/#group=triples |
| **KiiiKiii** | 19 | https://tonscene.github.io/SCENEKPOP/#group=kiiikiii |
| **BABYMONSTER** | 14 | https://tonscene.github.io/SCENEKPOP/#group=babymonster |
| **TUIDE** | 14 | https://tonscene.github.io/SCENEKPOP/#group=tuide |
| **ILLIT** | 11 | https://tonscene.github.io/SCENEKPOP/#group=illit |
| **NMIXX** | 5 | https://tonscene.github.io/SCENEKPOP/#group=nmixx |
| **TWICE** | 5 | https://tonscene.github.io/SCENEKPOP/#group=twice |
| **MEOVV** | 4 | https://tonscene.github.io/SCENEKPOP/#group=meovv |
| **LE SSERAFIM** | 4 | https://tonscene.github.io/SCENEKPOP/#group=le_sserafim |
| **KISS OF LIFE** | 3 | https://tonscene.github.io/SCENEKPOP/#group=kiss_of_life |
| **Billlie** | 3 | https://tonscene.github.io/SCENEKPOP/#group=billlie |
| **i-dle** | 3 | https://tonscene.github.io/SCENEKPOP/#group=idle |
| **IVE** | 2 | https://tonscene.github.io/SCENEKPOP/#group=ive |
| **TREASURE** | 2 | https://tonscene.github.io/SCENEKPOP/#group=treasure |
| **ALLDAY PROJECT** | 2 | https://tonscene.github.io/SCENEKPOP/#group=allday_project |
| **XG** | 2 | https://tonscene.github.io/SCENEKPOP/#group=xg |
| **Chuu & Arin** | 2 | https://tonscene.github.io/SCENEKPOP/#group=chuu_arin |
| **aespa** | 1 | https://tonscene.github.io/SCENEKPOP/#group=aespa |
| **วงอื่นๆ & รายการพิเศษ** | 23 | https://tonscene.github.io/SCENEKPOP/#group=other_kpop |

---

## วิธีอัปเดตคลิปใหม่จาก YouTube อัตโนมัติ
เมื่ออัปโหลดคลิปใหม่ลงช่อง `@SCENEKPOP` ให้รัน:
```bash
python3 sync_channel.py
```
หากต้องการอัปเดตและ Push ขึ้น GitHub Pages ในคำสั่งเดียว:
```bash
python3 deploy.py --sync "Add latest videos"
```

## การตั้งค่าการแยกวง (`group_config.json`)
- แก้ไขหรือเพิ่มวงใหม่ได้ที่ `group_config.json` ในหัวข้อ `"groups"`
- หากมีคลิปที่ชื่อคลิปไม่มีชื่อวง สามารถใส่ ID คลิปลงใน `"video_overrides"` ได้โดยตรง เช่น `"VIDEO_ID": ["qwer"]`
