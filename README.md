# 🌶️ Yum Jukebox - ระบบคิวเพลงสำหรับร้านอาหาร

ระบบขอเพลงผ่าน QR Code สำหรับร้านยำปากเจ่อ ลูกค้าสแกน QR Code ด้วยมือถือ ค้นหาเพลง YouTube และส่งเข้าคิวได้ทันที

## ฟีเจอร์หลัก

- **หน้าจอเครื่องเล่น** - แสดง YouTube Player พร้อม QR Code สำหรับสแกนขอเพลง
- **หน้าขอเพลง** - ค้นหาเพลงจาก YouTube แล้วส่งเข้าคิว
- **ระบบคิวเพลง** - จัดคิวเพลงอัตโนมัติ เล่นทีละเพลง หมดแล้วเล่นเพลงถัดไป
- **QR Code Generator** - สร้าง QR Code ให้ลูกค้าสแกนเข้าหน้าขอเพลงได้ทันที
- **กรองเพลงที่เล่นไม่ได้** - บล็อก Video ID ที่ YouTube ไม่อนุญาตให้ embed (Error 153)
- **รีเฟรชเพลงแนะนำอัตโนมัติ** - โหลดเพลงฮิตใหม่ทุกครั้งที่เข้าหน้าขอเพลง
- **พิมพ์ QR Code** - ปุ่มพิมพ์ QR Code จากหน้าจอเครื่องเล่น

## Stack

- Django 6.0
- SQLite
- yt-dlp (YouTube search)
- YouTube IFrame API
- Tailwind CSS (CDN)
- qrcode (Python)

## โครงสร้างโปรเจค

```
mysong/
├── manage.py                  # Django management script
├── db.sqlite3                 # SQLite database
├── yum_jukebox/               # Project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── music/                     # Main app
    ├── models.py              # SongQueue model
    ├── views.py               # Views + YouTube API + blocked video filtering
    ├── urls.py                # URL routing
    ├── templates/music/
    │   ├── player.html        # หน้าจอเครื่องเล่น (TV/จอมอนิเตอร์)
    │   └── request.html       # หน้าขอเพลง (มือถือลูกค้า)
    └── migrations/
```

## วิธีติดตั้งและรัน

```bash
# สร้าง virtual environment
python -m venv venv
venv\Scripts\activate

# ติดตั้ง dependencies
pip install django yt-dlp qrcode

# สร้าง database
python manage.py migrate

# รันเซิร์ฟเวอร์
python manage.py runserver 0.0.0.0:8000
```

## URL Routing

| Path | คำอธิบาย |
|------|----------|
| `/` | หน้าจอเครื่องเล่น + QR Code + คิวเพลง + ปุ่มพิมพ์ QR |
| `/request/` | หน้าขอเพลงสำหรับลูกค้า (มือถือ) |
| `/qr.png` | รูป QR Code สำหรับสแกน |
| `/api/search/?q=...` | ค้นหาเพลงจาก YouTube |
| `/api/add/` | POST - เพิ่มเพลงเข้าคิว |
| `/api/queue/` | ดึงคิวเพลงทั้งหมด |
| `/api/played/<id>/` | ทำเครื่องหมายว่าเพลงถูกเล่นแล้ว |
| `/api/clear/` | ล้างคิวทั้งหมด |
| `/api/my-songs/?client_id=...` | ดึงเพลงที่ตัวเองขอ |
| `/api/my-songs/<id>/delete/` | ลบเพลงที่ตัวเองขอ |
| `/api/hits/` | ดึงเพลงฮิตแนะนำ (สุ่มจาก YouTube) |
| `/admin/` | Django Admin |

## Model: SongQueue

| Field | Type | คำอธิบาย |
|-------|------|----------|
| `title` | CharField(255) | ชื่อเพลง |
| `video_id` | CharField(50) | YouTube Video ID |
| `thumbnail` | URLField(500) | URL รูป thumbnail |
| `channel` | CharField(255) | ชื่อช่อง YouTube |
| `requested_by` | CharField(100) | ชื่อผู้ขอเพลง (default: "ลูกค้าในร้าน") |
| `client_id` | CharField(50) | ID ของลูกค้า (สำหรับจัดการเพลงตัวเอง) |
| `is_played` | BooleanField | สถานะว่าเล่นแล้วหรือยัง |
| `created_at` | DateTimeField | เวลาที่สร้าง (auto) |

## ฟีเจอร์เพิ่มเติม

### 1. กรองเพลงที่เล่นไม่ได้ (Error 153)
- **Server-side** (`views.py`): `BLOCKED_VIDEO_IDS` set กรองใน `/api/search/` และ `/api/hits/`
- **Client-side** (`request.html`): `blockedVideoIds` Set กรองเพิ่มเติม
- Video ID ที่บล็อก: `jNQXAC9IVRw` (Me at the zoo), `dQw4w9WgXcQ` (Never Gonna Give You Up), `qguo-j5PxBE` (ซ่อน(ไม่)หา - Jeff Satur)

### 2. รีเฟรชเพลงแนะนำ
- โหลดเพลงฮิตใหม่จาก YouTube ทุกครั้งที่เข้าหน้า `/request/`
- กดปุ่ม "รีเฟรชเพลง" เพื่อโหลดใหม่ได้ตลอด

### 3. สถานะคิวของตัวเอง (หน้าขอเพลง)
- แสดงตำแหน่งคิว: "คิวของคุณ: ลำดับที่ X"
- แสดง "กำลังเล่นเพลงของคุณ!" เมื่อถึงคิว
- แสดง "เพลงของคุณเล่นแล้ว" เมื่อจบ
- หายอัตโนมัติหลัง 3.5 วินาที

### 4. ปุ่มพิมพ์ QR Code (หน้าจอเครื่องเล่น)
- กด "🖨️ พิมพ์ QR Code" เปิด QR Code ในแท็บใหม่
- รองรับ popup blocked (fallback ไปหน้า `/qr.png` โดยตรง)

### 5. Race Condition Fix
- `finishingSongIds` Set ป้องกันการ skip/end ซ้ำ
- `fetchQueue()` ใน `finally` block รับประกันการโหลดคิวถัดไป

### 6. YouTube Error Handling
- Error 153 (embedding disabled): skip ทันที
- Error อื่นๆ: retry 1 ครั้ง แล้วค่อย skip

## วิธีใช้งาน

1. เปิดหน้า `/` บนจอมอนิเตอร์หรือ TV ในร้าน
2. ลูกค้าสแกน QR Code บนหน้าจอด้วยมือถือ
3. พิมพ์ชื่อเพลงที่ต้องการ แล้วกด "ขอเพลง"
4. เพลงจะเข้าคิวและเล่นอัตโนมัติบนหน้าจอมอนิเตอร์
5. หมดเพลงจะแสดง "รอเพลงจากลูกค้า..."
6. กดปุ่ม "ข้ามเพลง" เพื่อข้ามไปเพลงถัดไปได้
7. กด "🖨️ พิมพ์ QR Code" เพื่อพิมพ์ QR Code ไปแปะที่อื่น

## การทดสอบ

```bash
# รัน unit tests
python manage.py test music
# ผลลัพธ์: 28 tests passed
```

## หมายเหตุ

- ต้องมีอินเทอร์เน็ตสำหรับ YouTube API และ Tailwind CDN
- รูปภาพแบนเนอร์ `1.png` และ `2.jpg` ต้องวางไว้ที่ `music/static/music/img/`
- หากพบเพลงเล่นไม่ได้ ให้เพิ่ม Video ID ลงใน `BLOCKED_VIDEO_IDS` ใน `views.py` และ `blockedVideoIds` ใน `request.html`