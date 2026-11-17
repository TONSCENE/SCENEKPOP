# SCENEKPOP+ Directory

คลังรวมคลิปซับไทยและวาไรตี้ K-Pop จากช่อง [@SCENEKPOP](https://www.youtube.com/@SCENEKPOP) และ [Patreon](https://www.patreon.com/c/SCENEKPOP) แบบแยกดูตามวงได้ ครบทั้งรายการวาไรตี้, Weverse / IG Live, รายการวิทยุ, สเตจ และคลิปพิเศษ

## ลิงก์หลัก
- **หน้าเว็บออนไลน์ (GitHub Pages)**: https://tonscene.github.io/SCENEKPOP/
- **GitHub Repository**: https://github.com/TONSCENE/SCENEKPOP
- **YouTube**: https://www.youtube.com/@SCENEKPOP
- **Patreon (ซับไทยพิเศษ & สนับสนุนช่อง)**: https://www.patreon.com/c/SCENEKPOP

---

## ลิงก์แยกตามวง (นำไปแชร์ต่อได้เลย — รวม 406 คลิป: YouTube 359 + Patreon 47)

| วง / หมวดหมู่ | จำนวนคลิป | ลิงก์เปิดดูเฉพาะวง |
| :--- | :---: | :--- |
| **QWER** | 115 | https://tonscene.github.io/SCENEKPOP/#group=qwer |
| **Hearts2Hearts** | 74 | https://tonscene.github.io/SCENEKPOP/#group=hearts2hearts |
| **RESCENE** | 51 | https://tonscene.github.io/SCENEKPOP/#group=rescene |
| **tripleS** | 20 | https://tonscene.github.io/SCENEKPOP/#group=triples |
| **KiiiKiii** | 19 | https://tonscene.github.io/SCENEKPOP/#group=kiiikiii |
| **ILLIT** | 19 | https://tonscene.github.io/SCENEKPOP/#group=illit |
| **Veiled Cup** | 18 | https://tonscene.github.io/SCENEKPOP/#group=veiled_cup |
| **LE SSERAFIM** | 16 | https://tonscene.github.io/SCENEKPOP/#group=le_sserafim |
| **BABYMONSTER** | 15 | https://tonscene.github.io/SCENEKPOP/#group=babymonster |
| **TUIDE** | 15 | https://tonscene.github.io/SCENEKPOP/#group=tuide |
| **i-dle** | 15 | https://tonscene.github.io/SCENEKPOP/#group=idle |
| **HyeMiLeeYeChaePa** | 12 | https://tonscene.github.io/SCENEKPOP/#group=hyemileeyechaepa |
| **SMTM12 & MILLI** | 12 | https://tonscene.github.io/SCENEKPOP/#group=smtm12_milli |
| **NMIXX** | 5 | https://tonscene.github.io/SCENEKPOP/#group=nmixx |
| **KISS OF LIFE** | 5 | https://tonscene.github.io/SCENEKPOP/#group=kiss_of_life |
| **TWICE** | 5 | https://tonscene.github.io/SCENEKPOP/#group=twice |
| **MEOVV** | 4 | https://tonscene.github.io/SCENEKPOP/#group=meovv |
| **Billlie** | 3 | https://tonscene.github.io/SCENEKPOP/#group=billlie |
| **IVE** | 2 | https://tonscene.github.io/SCENEKPOP/#group=ive |
| **TREASURE** | 2 | https://tonscene.github.io/SCENEKPOP/#group=treasure |
| **ALLDAY PROJECT** | 2 | https://tonscene.github.io/SCENEKPOP/#group=allday_project |
| **XG** | 2 | https://tonscene.github.io/SCENEKPOP/#group=xg |
| **Chuu & Arin** | 2 | https://tonscene.github.io/SCENEKPOP/#group=chuu_arin |
| **AKMU** | 2 | https://tonscene.github.io/SCENEKPOP/#group=akmu |
| **aespa** | 1 | https://tonscene.github.io/SCENEKPOP/#group=aespa |
| **วงอื่นๆ & รายการพิเศษ** | 5 | https://tonscene.github.io/SCENEKPOP/#group=other_kpop |

---

## วิธีอัปเดตคลิปใหม่จาก YouTube อัตโนมัติ (รองรับตรวจรูปปกด้วย Gemini Vision)
เมื่ออัปโหลดคลิปใหม่ลงช่อง `@SCENEKPOP` ให้รัน:
```bash
python3 sync_channel.py
```
- หากคลิปใหม่ไม่มีชื่อวงในชื่อคลิปหรือคำอธิบาย ระบบจะส่งรูปปกคลิปให้ **Gemini Vision** (ใช้ `GEMINI_API_KEY` จาก `.env`) ช่วยวิเคราะห์รูปปกและแยกวงให้อัตโนมัติ
- หากต้องการอัปเดตและ Push ขึ้น GitHub Pages ในคำสั่งเดียว:
```bash
python3 deploy.py --sync "Add latest videos"
```

## การตั้งค่าการแยกวง (`group_config.json`)
- แก้ไขหรือเพิ่มวงใหม่ได้ที่ `group_config.json` ในหัวข้อ `"groups"`
- หากมีคลิปที่ชื่อคลิปไม่มีชื่อวง สามารถใส่ ID คลิปลงใน `"video_overrides"` ได้โดยตรง เช่น `"VIDEO_ID": ["qwer"]`
