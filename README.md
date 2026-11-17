# SCENEKPOP+ Directory

คลังรวมคลิปซับไทยและวาไรตี้ K-Pop จากช่อง [@SCENEKPOP](https://www.youtube.com/@SCENEKPOP) แบบแยกดูตามวงได้ (สไตล์เดียวกับ BunniesFlix)

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
