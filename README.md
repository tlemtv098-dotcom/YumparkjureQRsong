# 🌶️ Yum Jukebox - ระบบคิวเพลงสำหรับร้านอาหาร

ระบบขอเพลงผ่าน QR Code สำหรับร้านยำปากเจ่อ ลูกค้าสแกน QR Code ด้วยมือถือ ค้นหาเพลง YouTube และส่งเข้าคิวได้ทันที

## ฟีเจอร์หลัก

- **หน้าจอเครื่องเล่น (Player)** - YouTube IFrame Player พร้อม QR Code, คิวเพลง, ค้นหาเพลง + Autocomplete, เพลงแนะนำ (Genre), Volume/Mute, Share, Toast
- **หน้าขอเพลง (Request)** - ค้นหาเพลง + Autocomplete, เพลงฮิตตาม Genre (ป๊อป/ร็อก/ลูกทุ่ง/TikTok), ปุ่มขอเพลงรายเพลง, เพลงของฉัน, Toast
- **ระบบคิวเพลงอัตโนมัติ** - จัดคิว เล่นทีละเพลง จบแล้วเล่นเพลงถัดไปอัตโนมัติ + กันซ้ำ + จำกัด 5 เพลง/คน
- **QR Code Generator** - สร้าง QR Code ให้ลูกค้าสแกนเข้าหน้าขอเพลงได้ทันที + ปุ่มพิมพ์
- **PWA** - ติดตั้งเป็นแอปได้ (manifest + service worker, offline shell)
- **กรองเพลงที่เล่นไม่ได้** - บล็อก Video ID ที่ YouTube ไม่อนุญาตให้ embed (Error 153) + auto-skip

## Stack

- Django 6.0 + Gunicorn + WhiteNoise
- SQLite + LocMemCache (hits 60s / suggest 30s)
- yt-dlp (YouTube search)
- YouTube IFrame API (pure — no audio fallback)
- Tailwind CSS (CDN)
- qrcode + Pillow

## โครงสร้างโปรเจค

```
mysong/
├── manage.py
├── db.sqlite3
├── Dockerfile
├── railway.toml
├── requirements.txt
├── yum_jukebox/               # Project config
│   ├── settings.py            # CACHES, LOGGING, WhiteNoise, Security
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── music/
    ├── models.py              # SongQueue
    ├── views.py               # API + cache + dedup + rate limit + healthz/stats
    ├── urls.py
    ├── admin.py               # ปรับ list_display / filter แล้ว
    ├── tests.py               # 42 tests
    ├── static/music/
    │   ├── manifest.json      # PWA
    │   ├── sw.js              # Service Worker
    │   └── img/logo.jpg
    └── templates/
        ├── 404.html / 500.html
        └── music/
            ├── player.html    # TV/จอมอนิเตอร์ — queue, search+suggest, hits+genre, volume, toast
            └── request.html   # มือถือ — search+suggest, hits+genre tabs, ขอเพลงรายเพลง, my songs, toast
```

## วิธีติดตั้งและรัน

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
# Player:  http://localhost:8000/
# Request: http://localhost:8000/request/
# Health:  http://localhost:8000/healthz/
# Stats:   http://localhost:8000/api/stats/
```

## URL Routing

| Path | คำอธิบาย |
|------|----------|
| `/` | Player + QR + คิว + ค้นหา+แนะนำ(Genre) + Volume + Share + Toast |
| `/request/` | Request (มือถือ) — search+suggest, hits+genre tabs, ขอเพลงรายเพลง, my songs |
| `/qr.png` | QR Code |
| `/healthz/` | Health check `{"status":"ok"}` (Railway) |
| `/api/search/?q=...` | ค้นหา YouTube (ytsearch5) |
| `/api/suggest/?q=...` | Autocomplete (30s cache) |
| `/api/hits/?genre=pop\|rock\|lukthung\|tiktok` | เพลงแนะนำ 8 เพลง (60s cache) |
| `/api/add/` | POST เพิ่มคิว — dedup 400, limit 5/คน 400, rate limit 429 |
| `/api/queue/` | คิว `is_played=False` |
| `/api/played/<id>/` | ทำเครื่องหมายเล่นแล้ว |
| `/api/clear/` | ล้างคิว |
| `/api/my-songs/?client_id=...` | เพลงของฉัน |
| `/api/my-songs/<id>/delete/` | ลบของฉัน |
| `/api/stats/` | สถิติ `total_queued / total_played / top_songs[5]` |
| `/admin/` | Django Admin (ปรับแล้ว) |

## Model: SongQueue

| Field | Type | หมายเหตุ |
|-------|------|----------|
| `title` | CharField(255) | ตัด 255 อักขระ |
| `video_id` | CharField(50) | Dedup ในคิว |
| `thumbnail` | URLField(500) | |
| `channel` | CharField(255) | |
| `requested_by` | CharField(100) | default "ลูกค้าในร้าน" |
| `client_id` | CharField(64) | จำกัด 5 คิว/คน |
| `is_played` | BooleanField | |
| `created_at` | DateTimeField | `ordering = ['created_at']` |

## ฟีเจอร์เพิ่มเติม

### 1. ค้นหา + Autocomplete
- Player: ปุ่ม “ค้นหาเพลง / เลือกเพลงแนะนำ” → แผงค้นหา + แนะนำ
- Request: ช่องค้นหา real-time
- API: `/api/suggest/?q=` static Thai list, 300ms debounce suggest / 500ms search

### 2. เพลงแนะนำ + Genre Tabs
- Request: tabs ทั้งหมด / ป๊อป / ร็อก / ลูกทุ่ง / TikTok → `/api/hits/?genre=`
- Player: Section “เพลงแนะนำ” 8 เพลง + รีเฟรช

### 3. UX Polish (ใหม่)
- Toast มุมล่าง (`showToast` success/error 3s)
- Volume slider 0-100 + ปุ่ม Mute (`player.setVolume / mute/unMute`)
- Skeleton “กำลังโหลด...” ตอน fetch
- Share ปุ่ม 🔗 คัดลอกลิงก์ `/request/?q=title`

### 4. กรองเพลงเล่นไม่ได้
- Server `BLOCKED_VIDEO_IDS` + Client `blockedVideoIds` — `jNQXAC9IVRw`, `dQw4w9WgXcQ`, `qguo-j5PxBE` ฯลฯ

### 5. Queue Hardening
- Dedup: `video_id` ซ้ำในคิวยังไม่เล่น → `400 เพลงนี้อยู่ในคิวแล้ว`
- Limit 5/คน: `client_id` เกิน 5 → `400 คุณมีเพลงในคิวครบ 5 เพลงแล้ว...`
- Rate limit: 30 req / 10s / IP → `429 Too many requests`
- Race fix: `finishingSongIds` Set + `finally fetchQueue`

### 6. Performance
- `LocMemCache`: hits 60s, suggest 30s

### 7. Security & Ops
- `LOGGING` console INFO, `SECURE_*` เมื่อ `DEBUG=False`, `WhiteNoise`, `Dockerfile` (python:3.12-slim + gunicorn 2 workers), `railway.toml` healthcheck `/healthz/`, CSP-friendly

### 8. PWA
- `manifest.json` (standalone, theme #f59e0b), `sw.js` cache shell + network-first /api/

### 9. YouTube Error & Autoplay
- Error 2,5,100,101,150,153 → skip ทันที, อื่น retry 1 ครั้ง
- `mute:1` → `playVideo()` → user click/touch → `unMute()`

### 10. Error Pages
- `404.html` / `500.html` สไตล์ร้านยำ + ปุ่มกลับหน้าแรก

## วิธีใช้งาน

1. เปิด `/` บน TV/จอมอนิเตอร์
2. ลูกค้าสแกน QR → `/request/` บนมือถือ
3. พิมพ์ค้นหา หรือเลือก Genre → กด `ขอเพลง` (รายเพลง)
4. เพลงเข้าคิว เล่นอัตโนมัติ (muted) → แตะหน้าจอ Player เพื่อเปิดเสียง
5. ปรับ Volume ได้, Share ลิงก์ได้, หมดเพลง auto next, `ข้ามเพลง` ได้, `พิมพ์ QR` ได้

## การทดสอบ

```bash
python manage.py test music --verbosity=1
# Ran 42 tests in ~0.7s — OK
# ครอบคลุม: Player/Request render, queue, my-songs, clear, healthz, stats, suggest, dedup, per-client limit (5), queue API, PWA manifest/SW, volume/genre/checkbox, 404/500
```

## หมายเหตุ

- ต้องมีเน็ตสำหรับ YouTube IFrame + Tailwind CDN
- โลโก้ `music/static/music/img/logo.jpg` ต้องมี
- เพลงเล่นไม่ได้ → เพิ่ม Video ID ใน `BLOCKED_VIDEO_IDS` (`views.py` + 2 templates)
- YouTube IFrame ไม่ต้อง API Key แต่ต้องอนุญาต embed

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│ Player (IFrame) │────▶│ Django Backend   │────▶│ YouTube     │
│ queue poll 3s   │     │ /api/queue/add/  │     │ embed       │
│ search+suggest  │◀────│ /api/hits/suggest│     │ Video ID    │
│ hits+genre      │     │ /api/stats/health│     │ → Player    │
│ volume/toast/PWA│     │ cache/ratelimit  │     │             │
└─────────────────┘     └──────────────────┘     └─────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌──────────────────┐
│ Request Mobile  │────▶│ yt-dlp ytsearch  │
│ search+suggest  │     │ 5/10 + Blocked   │
│ hits genre tabs │     │ filter           │
│ ขอเพลงรายเพลง   │     └──────────────────┘
└─────────────────┘
```
