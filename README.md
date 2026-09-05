# Yum Jukebox - ระบบคิวเพลงสำหรับร้านอาหาร

ระบบขอเพลงผ่าน QR Code สำหรับร้านยำปากเจ่อ ลูกค้าสแกน QR Code ด้วยมือถือ ค้นหาเพลง YouTube และส่งเข้าคิวได้ทันที เปิดหน้าจอ Player ไว้บน TV/จอมอนิเตอร์ของร้าน

- Live: https://yumpakjure.onrender.com
- สถานะ: test 68 OK

## ภาพรวม

| ส่วน | รายละเอียด |
|------|------------|
| Player `/` | จอร้าน — YouTube IFrame Player, คิว, ค้นหา + suggest, เพลงแนะนำ, volume, ข้ามเพลง, สุ่มอัตโนมัติ, QR |
| Request `/request/` | มือถือลูกค้า — ค้นหา + suggest, เพลงฮิตตาม genre, ขอเพลงรายเพลง, เพลงของฉัน, AI แนะนำเพลง |
| Backend | Django API — คิว, dedup, จำกัดโควตา, rate limit, ย้ายคิว, สถิติ, บล็อกวิดีโอ, AI |
| Deploy | Render (free) + Gunicorn + WhiteNoise, SQLite + LocMemCache |

## ฟีเจอร์

### หน้าจอเครื่องเล่น (Player `/`)

- คิวเพลง poll ทุก 3 วินาที เล่นทีละเพลง จบแล้วเล่นเพลงถัดไปอัตโนมัติ
- ค้นหาเพลง + suggest (autocomplete, debounce) พร้อม AbortController ยกเลิกคำขอเก่า + retry 1 ครั้งเมื่อ network fail (cold start)
- เพลงแนะนำ (hits) 15 เพลง + ปุ่มรีเฟรช
- Volume slider 0-100 + Mute (`player.setVolume / mute / unMute`)
- สุ่มเพลงอัตโนมัติเมื่อคิวว่าง (auto-random, เปิด/ปิดได้, มี guard ครบทุกทางเข้า + clearTimeout เมื่อปิด)
- ปุ่มเล่นทันทีข้ามคิว (priority) ผ่าน `/api/add-front/` แล้วตัดเพลงปัจจุบันเล่นเพลงใหม่เลย
- ข้ามโฆษณาอัตโนมัติ — `setInterval` 500ms กดปุ่ม `.ytp-ad-skip-button` ให้เอง
- Media Session API — ควบคุม play/pause/next จากแถบแจ้งเตือน/ล็อกจอ + เล่นพื้นหลังบนเบราว์เซอร์ที่รองรับ
- Dark/light mode (Tailwind `darkMode: 'class'` + `localStorage`)
- Toast แจ้งผล success/error 3 วินาที, skeleton "กำลังโหลด..." ตอน fetch
- ปุ่ม Share คัดลอกลิงก์ `/request/?q=title`
- QR Code + ปุ่มพิมพ์ QR
- จัดการคิวของเจ้าของร้าน: เลื่อนเพลงขึ้นเป็นคิวถัดไป (`/api/queue/move/`), ล้างคิว, ทำเครื่องหมายเล่นแล้ว (ต้อง `X-Player-Token`)

### หน้าขอเพลง (Request `/request/`)

- ช่องค้นหา real-time + suggest dropdown (AbortController + retry เหมือน player)
- เพลงฮิตตาม genre tabs: ทั้งหมด / ป๊อป / ร็อก / ลูกทุ่ง / TikTok → `/api/hits/?genre=`
- ปุ่มขอเพลงรายเพลงทุกผลลัพธ์
- การ์ด "เพลงถัดไปในคิว" แบบ CD หมุน (`animate-spin` 6s, หยุดเมื่อไม่มีเพลง) + ชื่อเพลง marquee เลื่อนอัตโนมัติ
- เพลงของฉัน (`client_id` เก็บใน `localStorage`, ลบของตัวเองได้) — จำกัด 5 คิว/คน
- AI แนะนำเพลง — กรอกอารมณ์/แนวที่อยากฟัง เรียก `/api/ai/recommend/` (DeepSeek + ค้นหา YouTube ต่อ, fallback 8 เพลงเมื่อไม่มี key)
- Dark/light mode, Toast, banner แนะนำให้เปิดในเบราว์เซอร์ภายนอกถ้าอยู่ใน LINE WebView

### ระบบคิว

- Dedup: `video_id` ซ้ำในคิวที่ยังไม่เล่น → `400 เพลงนี้อยู่ในคิวแล้ว`
- Limit 5 เพลง/คน: นับตาม `client_id` เกิน → `400 คุณมีเพลงในคิวครบ 5 เพลงแล้ว...`
- Rate limit: 30 req / 10s / IP → `429 Too many requests`
- ย้ายคิว: `POST /api/queue/move/` (`song_id` + `position: next/top`) เฉพาะเจ้าของร้าน
- กัน race: `finishingSongIds` Set + `finally fetchQueue`

### กรองเพลงที่เล่นไม่ได้ (Error 153)

- เพลงที่ YouTube ไม่อนุญาตให้ embed (Error 101/150/153 ฯลฯ) จะถูกข้ามทันทีแบบ soft-skip ทั้งฝั่ง player (`onError` 2,5,100,101,150,153 → ข้าม, error อื่น retry 1 ครั้ง) และฝั่ง server (เช็ค embeddability + `BLOCKED_VIDEO_IDS`)
- `FALLBACK_IDS` guard — 8 id เพลง fallback จะไม่ถูกบันทึกเป็น blocked ถาวร (`block_video` ตอบ `{"status":"skipped"}`)
- `POST /api/block/clear/` (owner-only) ล้างแถว FALLBACK_IDS เก่าออกจาก DB

### ค้นหา YouTube

- ลำดับ: YouTube Data API (multi-key rotation) → yt-dlp `ytsearch` → fallback 15 เพลงจริงหลายแนว
- Multi-key rotation: อ่าน keys ตามลำดับจาก `YOUTUBE_API_KEYS` (คั่นจุลภาค) + `YOUTUBE_API_KEY` + `key` + `YOUTUBE_API_KEY_2`; key ไหน quota หมด (403 quotaExceeded) หรือ network error ข้ามไป key ถัดไปอัตโนมัติ
- Frontend: AbortController + timeout 8 วิ + เช็ค `res.ok` + retry 1 ครั้งหลัง 800ms (รองรับ Render cold start)
- กรองผล: ตัดอัลบั้ม/ชาร์ต/เพลย์ลิสต์ยาว, ตัด AI/bot, ตัด non-music (สอน/vlog/game), ตัด blocked ids

### QR Code

- `GET /qr.png` สร้าง QR ไปยังหน้าขอเพลง (`PUBLIC_URL` ถ้าตั้งไว้ ไม่งั้นใช้ host ของ request) + ปุ่มพิมพ์บนหน้า player

### PWA

- `manifest.json` (standalone, theme `#f59e0b`) + `sw.js` (cache shell, network-first สำหรับ `/api/`)

### Device matrix

เมทริกซ์ทดสอบอุปกรณ์อยู่ใน `docs/superpowers/checklists/device-test-matrix.md` ครอบคลุม iPhone SE / 14 / 14 Pro Max, Pixel 7, iPad mini / Pro / gen 9, Laptop, Desktop กับเบราว์เซอร์ iOS Safari/Chrome, Android Chrome, Desktop Chrome/Safari/Firefox/Edge ข้อควรรู้หลัก: iOS ต้องแตะหน้าจอ 1 ครั้งเพื่อเปิดเสียง (autoplay policy), LINE WebView ให้เปิดในเบราว์เซอร์ภายนอก, เปิดครั้งแรกบน Render อาจช้าให้ retry หนึ่งครั้ง

## Stack

- Django 6.0 + Gunicorn + WhiteNoise
- SQLite + LocMemCache (hits 60s / suggest 30s)
- YouTube Data API v3 (multi-key) + yt-dlp (fallback search)
- YouTube IFrame API + Media Session API
- DeepSeek API (OpenAI-compatible) สำหรับ AI แนะนำเพลง
- Tailwind CSS (CDN, `darkMode: 'class'`)
- qrcode + Pillow

## โครงสร้างโปรเจค

```
mysong/
├── manage.py
├── db.sqlite3
├── Dockerfile
├── requirements.txt
├── .env.example
├── yum_jukebox/               # Project config
│   ├── settings.py            # CACHES, LOGGING, WhiteNoise, Security, PLAYER_TOKEN
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── docs/superpowers/
│   ├── plans/                 # แผน implementation
│   └── checklists/
│       ├── device-test-matrix.md
│       └── full-verification.md
└── music/
    ├── models.py              # SongQueue + BlockedVideo
    ├── views.py               # API + cache + dedup + rate limit + rotation + AI
    ├── urls.py
    ├── admin.py               # ปรับ list_display / filter แล้ว
    ├── tests.py               # 68 tests
    ├── static/music/
    │   ├── manifest.json      # PWA
    │   ├── sw.js              # Service Worker
    │   └── img/logo.jpg
    └── templates/
        ├── 404.html / 500.html
        └── music/
            ├── player.html    # TV/จอมอนิเตอร์ — queue, search+suggest, hits, volume, priority, move, QR, dark, toast
            └── request.html   # มือถือ — search+suggest, hits+genre tabs, ขอเพลงรายเพลง, CD spin, marquee, my songs, AI, dark
```

## Environment variables

| Name | จำเป็น | คำอธิบาย |
|------|--------|----------|
| `YOUTUBE_API_KEY` | แนะนำ | YouTube Data API v3 key หลัก (search ครั้งละ 100 units) |
| `YOUTUBE_API_KEY_2` | สำรอง | key สำรอง — rotation ข้ามมาอัตโนมัติเมื่อ key หลัก quota หมด |
| `YOUTUBE_API_KEYS` | ทางเลือก | หลาย key คั่นด้วยจุลภาค ใช้อันดับแรกสุดใน rotation |
| `PLAYER_TOKEN` | บน prod | โทเคนเจ้าของร้าน ส่งเป็น header `X-Player-Token` สำหรับ `/api/clear/`, `/api/played/`, `/api/queue/move/`, `/api/block/clear/` |
| `PUBLIC_URL` | บน prod | base URL สำหรับสร้าง QR (เช่น `https://yumpakjure.onrender.com`) ถ้าไม่ตั้งจะใช้ host ของ request |
| `DEEPSEEK_API_KEY` | ทางเลือก | ถ้าไม่ตั้ง AI recommend จะใช้ fallback 8 เพลง |
| `SECRET_KEY` | บน prod | Django secret key |
| `DEBUG` | — | `True`/`False` (prod ตั้ง `False`) |
| `ALLOWED_HOSTS` | บน prod | คั่นด้วยจุลภาค (มี default รวม `yumpakjure.onrender.com` อยู่แล้ว) |
| `CSRF_TRUSTED_ORIGINS` | บน prod | มี default `https://yumpakjure.onrender.com` อยู่แล้ว |

## URL Routing

| Path | Method | คำอธิบาย |
|------|--------|----------|
| `/` | GET | Player + QR + คิว + ค้นหา+แนะนำ + Volume + auto-random + priority + Share + dark + Toast |
| `/request/` | GET | Request (มือถือ) — search+suggest, hits+genre tabs, ขอเพลงรายเพลง, CD spin, marquee, my songs, AI |
| `/qr.png` | GET | QR Code ไปหน้าขอเพลง |
| `/healthz/` | GET | Health check `{"status":"ok"}` |
| `/api/search/?q=...` | GET | ค้นหา YouTube (API → yt-dlp → fallback 15) |
| `/api/suggest/?q=...` | GET | Autocomplete (30s cache) |
| `/api/hits/?genre=pop\|rock\|lukthung\|tiktok` | GET | เพลงแนะนำ 15 เพลง (60s cache) |
| `/api/add/` | POST | เพิ่มคิว — dedup 400, limit 5/คน 400, rate limit 429 |
| `/api/add-front/` | POST | เพิ่มหน้าคิว (priority, owner) |
| `/api/queue/` | GET | คิว `is_played=False` |
| `/api/queue/move/` | POST | ย้ายเพลงเป็นคิวถัดไป (owner, `song_id` + `position`) |
| `/api/played/<id>/` | GET/POST | ทำเครื่องหมายเล่นแล้ว (owner) |
| `/api/clear/` | POST | ล้างคิว (owner) |
| `/api/my-songs/?client_id=...` | GET | เพลงของฉัน |
| `/api/my-songs/<id>/delete/` | POST | ลบเพลงของฉัน (เช็ค `client_id`) |
| `/api/stats/` | GET | สถิติ `total_queued / total_played / top_songs[5]` |
| `/api/block/<video_id>/` | POST | บล็อกวิดีโอ (ข้าม FALLBACK_IDS) |
| `/api/block/clear/` | POST | ล้างแถว FALLBACK_IDS ออกจาก block list (owner) |
| `/api/ai/recommend/` | POST | AI แนะนำ 5 เพลงจาก `{"mood": "..."}` (DeepSeek + YouTube search + fallback) |
| `/admin/` | GET | Django Admin (ปรับแล้ว) |

## Models

### SongQueue

| Field | Type | หมายเหตุ |
|-------|------|----------|
| `title` | CharField(255) | ตัด 255 อักขระ |
| `video_id` | CharField(50) | Dedup ในคิวที่ยังไม่เล่น |
| `thumbnail` | URLField(500, null) | |
| `channel` | CharField(255, null) | |
| `audio_url` | URLField(1000, null) | |
| `requested_by` | CharField(100) | default "ลูกค้าในร้าน" |
| `client_id` | CharField(64) | จำกัด 5 คิว/คน |
| `is_played` | BooleanField | default False |
| `created_at` | DateTimeField | `ordering = ['created_at']` (ย้ายคิวใช้วิธีขยับเวลานี้) |

### BlockedVideo

| Field | Type | หมายเหตุ |
|-------|------|----------|
| `video_id` | CharField(50, unique) | |
| `reason` | CharField(100) | default "Error 153" |
| `created_at` | DateTimeField | |

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

## การทดสอบ

```bash
venv\Scripts\python.exe manage.py test music.tests -v2
# Ran 68 tests — OK
# ครอบคลุม: Player/Request render, queue, my-songs, clear, healthz, stats, suggest,
# search retry/abort, fallback 15, multi-key rotation, dedup, per-client limit (5),
# queue move, add-front priority, block + FALLBACK_IDS guard + block/clear,
# AI recommend, dark mode, CD spin, marquee, Media Session, ad skip,
# PWA manifest/SW, volume/genre, 404/500, owner auth (PLAYER_TOKEN)
```

## วิธีใช้งาน

1. เปิด `/` บน TV/จอมอนิเตอร์ของร้าน
2. ลูกค้าสแกน QR → `/request/` บนมือถือ
3. พิมพ์ค้นหา หรือเลือก Genre/AI แนะนำ → กด `ขอเพลง` (รายเพลง)
4. เพลงเข้าคิว เล่นอัตโนมัติ (muted) → แตะหน้าจอ Player 1 ครั้งเพื่อเปิดเสียง (iOS policy)
5. หมดคิวเปิด auto-random ได้, ข้ามเพลงได้, เจ้าของร้านย้ายคิว/เล่นทันที/ล้างคิวได้, พิมพ์ QR ได้

## Deploy บน Render

- ใช้ Gunicorn + WhiteNoise, `healthz/` เป็น health check path
- ตั้ง env: `SECRET_KEY`, `DEBUG=False`, `PLAYER_TOKEN`, `YOUTUBE_API_KEY` (+ `YOUTUBE_API_KEY_2` สำรอง), `PUBLIC_URL=https://yumpakjure.onrender.com`, `DEEPSEEK_API_KEY` (ถ้าใช้ AI)
- แผนฟรีหลับเมื่อไม่มีทราฟฟิก — เปิดครั้งแรกอาจช้า ~30-60 วินาทีแล้วค่อย retry/รีโหลดหนึ่งครั้ง (frontend มี retry ให้อยู่แล้ว)

## ข้อจำกัด

- iOS/Safari: autoplay ต้อง muted ก่อนเสมอ แตะหน้าจอ 1 ครั้งเพื่อเปิดเสียง
- YouTube Data API: search 1 ครั้งใช้ ~100 units — quota รวมคิดต่อ project ที่สร้าง key; หมดแล้ว rotation จะข้ามไป key ถัดไป ถ้าหมดทุก key ระบบตกไป yt-dlp/fallback อัตโนมัติ
- เพลงที่เจ้าของคลิปปิด embed เล่นไม่ได้ (Error 153) ระบบข้ามให้อัตโนมัติ
- ต้องมีเน็ตสำหรับ YouTube IFrame + Tailwind CDN
- โลโก้ `music/static/music/img/logo.jpg` ต้องมี (ใช้เป็น fallback thumbnail + PWA icon)
- LINE in-app WebView อาจหยุดเสียงพื้นหลัง — แนะนำให้ลูกค้าเปิดในเบราว์เซอร์ภายนอก

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│ Player (IFrame) │────▶│ Django Backend   │────▶│ YouTube     │
│ queue poll 3s   │     │ /api/queue/add/  │     │ Data API    │
│ search+suggest  │◀────│  multi-key rotate│     │ (100 u/req) │
│ hits 15         │     │ /api/hits/suggest│     │ → embed     │
│ volume/priority │     │ /api/stats/health│     │ Video ID    │
│ auto-random     │     │ cache/ratelimit  │     └─────────────┘
│ ad-skip/Media S.│     │ /api/ai/recommend│            │
│ dark/toast/PWA  │     │ (DeepSeek)       │            ▼
└─────────────────┘     └──────────────────┘     ┌─────────────┐
         │                       │               │ yt-dlp      │
         ▼                       ▼               │ ytsearch    │
┌─────────────────┐     ┌──────────────────┐     │ (fallback)  │
│ Request Mobile  │────▶│ 153 soft-skip +  │     └─────────────┘
│ search+suggest  │     │ FALLBACK_IDS     │            │
│ hits genre tabs │     │ guard + block    │            ▼
│ CD spin/marquee │     │ dedup/limit/move │     ┌─────────────┐
│ ขอเพลงรายเพลง   │     └──────────────────┘     │ Fallback 15 │
│ my songs + AI   │                              │ เพลงจริง    │
└─────────────────┘                              └─────────────┘
```
