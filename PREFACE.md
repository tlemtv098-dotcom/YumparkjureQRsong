# คำนำ (Preface)

## ระบบจัดการคิวเพลงร้านอาหาร (Yum Jukebox)

เอกสารชุดนี้จัดทำขึ้นเพื่อเป็นแนวทางในการพัฒนา ระบบจัดการคิวเพลงสำหรับร้านอาหาร (Yum Jukebox) ซึ่งเป็นระบบที่พัฒนาด้วย Django Framework เพื่อให้ลูกค้าสามารถขอเพลงผ่าน QR Code และเจ้าของร้านสามารถจัดการคิวเพลงได้อย่างมีประสิทธิภาพ

---

## 🎯 วัตถุประสงค์ของโปรเจกต์

1. **ลดภาระงานพนักงาน** - ลูกค้าสแกน QR Code ขอเพลงเอง ไม่ต้องเรียกพนักงาน
2. **รองรับทุกอุปกรณ์** - ทำงานบน Desktop, Android, iPhone, iPad ได้ครบ
3. **แก้ปัญหา iOS** - แก้ปัญหา YouTube Embed บน iOS 15+ (Error 153) ด้วย Audio Worker
4. **Real-time Sync** - คิวเพลงอัปเดตแบบ Real-time ทุกอุปกรณ์
5. **จัดการเพลย์ลิสต์** - เจ้าของร้านจัดการเพลย์ลิสต์ ได้หลายสาขา

---

## 🏗️ สถาปัตยกรรมระบบ (System Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Desktop    │  │   Android   │  │   iOS       │         │
│  │  (Chrome)   │  │   (Chrome)  │  │  (Safari)   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                      Django Backend                         │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐  │
│  │   Player     │ │   Request    │ │      Queue API     │  │
│  │   (Owner)    │ │   (Customer) │ │   (Real-time)      │  │
│  └──────────────┘ └──────────────┘ └────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Audio Worker (yt-dlp)                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  YouTube → yt-dlp → Audio URL → HTML5 <audio>          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 เทคโนโลยีหลัก (Tech Stack)

| Layer | Technology | Version |
|-------|------------|---------|
| **Backend** | Django | 6.0.6 |
| **Database** | SQLite (Dev) / PostgreSQL (Prod) | 3.x / 15+ |
| **Frontend** | Vanilla JS + Tailwind CSS | ES6+ / 3.x |
| **Audio Extraction** | yt-dlp | Latest |
| **Real-time** | Polling (3s interval) | - |
| **SSL/HTTPS** | mkcert (Dev) / Render TLS (Prod) | - |
| **Deployment** | Render.com (Free Tier) | - |
| **Container** | Docker (Optional) | - |

---

## 🎯 ฟีเจอร์หลัก (Key Features)

### 1. **Customer Request Page** (`/request/`)
- สแกน QR Code เข้าหน้าขอเพลง
- ค้นหาเพลง YouTube แบบ Real-time
- เพิ่มเพลงเข้าคิวได้ทันที
- ดูสถานะเพลงของตัวเอง

### 2. **Owner Player Dashboard** (`/`)
- ควบคุมเล่น/หยุด/ข้ามเพลง
- จัดการคิวเพลง (เลื่อนลำดับ, ลบ, เพิ่มด่วน)
- Auto-random mode (สุ่มเพลงเมื่อคิวหมด)
- เพลงแนะนำ (Hits) จาก YouTube Trending
- จัดการเพลย์ลิสต์ (สร้าง, แก้ไข, ลบ, โหลด)

### 3. **Audio Fallback System (iOS Fix)**
- ตรวจจับ iOS Safari/Chrome อัตโนมัติ
- ใช้ yt-dlp ดึง Audio URL ตรงๆ
- เล่นผ่าน HTML5 `<audio>` element
- รองรับ Media Session API (Lock screen controls)
- รองรับ Background Playback

### 4. **Playlist Management**
- สร้าง/แก้ไข/ลบ เพลย์ลิสต์
- เพิ่ม/ลบเพลงในเพลย์ลิสต์
- โหลดเพลย์ลิสต์เข้าคิวทันที
- Sync ระหว่างอุปกรณ์ (LocalStorage + Server)

### 5. **QR Code System**
- Generate QR Code สำหรับหน้าขอเพลง
- พิมพ์ QR Code วางโต๊ะ
- รองรับ Multiple branches (หลายสาขา)

---

## 🔐 ระบบสิทธิ์ (Permissions)

| Role | สิทธิ์ |
|------|--------|
| **Customer** | ขอเพลง, ดูคิวของตัวเอง, ดูเพลงแนะนำ |
| **Owner/Staff** | จัดการคิว, ควบคุม Player, จัดการเพลย์ลิสต์, ดูสถิติ |
| **Admin** | จัดการ User, Genre, Tag, Block/Good Video, สถิติระบบ |

---

## 🌐 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Render.com (Free Tier)                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Django App (Gunicorn + WhiteNoise)                 │   │
│  │  - Static files: WhiteNoise                          │   │
│  │  - Database: PostgreSQL (Render managed)            │   │
│  │  - Environment Variables: Render Dashboard          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
    ┌──────────────────┐        ┌──────────────────┐
    │  Audio Worker    │        │  Audio Worker    │
    │  (Local +        │  OR    │  (Oracle Cloud   │
    │  Cloudflare      │        │  Free Tier)      │
    │  Tunnel)         │        │                  │
    └──────────────────┘        └──────────────────┘
              │                        │
              └────────────┬────────────┘
                           ▼
              ┌────────────────────────┐
              │      YouTube API       │
              │    (yt-dlp extract)    │
              └────────────────────────┘
```

---

## 📱 รองรับ Platform

| Platform | Video Playback | Audio Playback | Status |
|----------|----------------|----------------|--------|
| **Desktop Chrome/Edge/Firefox** | ✅ YouTube Iframe | ✅ Audio Fallback | ✅ Full |
| **Android Chrome/Firefox** | ✅ YouTube Iframe | ✅ Audio Fallback | ✅ Full |
| **iOS Safari** | ❌ Error 153 | ✅ Audio Only | ✅ Audio Only |
| **iOS Chrome** | ❌ Error 153 | ✅ Audio Only | ✅ Audio Only |
| **iPad Safari** | ❌ Error 153 | ✅ Audio Only | ✅ Audio Only |

> **หมายเหตุ:** iOS 15+ บล็อก YouTube iframe (Error 153) เนื่องจาก ITP + Private Relay → ใช้ Audio Worker แทน

---

## 🔧 Local Development Setup

```bash
# 1. Clone & Setup
git clone <repo-url>
cd mysong
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. SSL Certificate (HTTPS Local)
mkcert -install
mkcert localhost 127.0.0.1 ::1

# 3. Run Development Server (HTTPS)
python manage.py runserver_plus --cert-file localhost+2.pem --key-file localhost+2-key.pem 0.0.0.0:8000

# 4. Access
# Local: https://127.0.0.1:8000
# LAN: https://<your-lan-ip>:8000
```

---

## 📋 Checklist ก่อน Deploy Production

- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` ตั้งค่าใน Environment Variable
- [ ] `ALLOWED_HOSTS` รวม domain production
- [ ] `DATABASE_URL` PostgreSQL (Render managed)
- [ ] `AUDIO_WORKER_URL` ชี้ไปที่ Audio Worker
- [ ] `WORKER_API_KEY` ตั้งค่า API Key
- [ ] `SECRET_KEY` ไม่ใช่ default
- [ ] `CSRF_TRUSTED_ORIGINS` รวม domain production
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`

---

## 📞 Support & Maintenance

| Task | Frequency | Owner |
|------|-----------|-------|
| Update yt-dlp | Weekly | Dev |
| Check Render Logs | Daily | Dev |
| Monitor Audio Worker | Daily | Dev |
| Backup Database | Daily (Auto) | Render |
| Update Dependencies | Monthly | Dev |
| Security Patches | Monthly | Dev |

---

## 📞 ช่องทางติดต่อ

- **Line:** [Line ID]
- **Email:** [Email Address]
- **GitHub:** [Repository URL]

---

---

*เอกสารนี้จัดทำโดยทีมพัฒนา Yum Jukebox*  
*Last Updated: 2025-01-15*  
*Version: 1.0.0*

---

*End of Preface*