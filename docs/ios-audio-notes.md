# iPad Safari Audit — เล่นไม่ได้ (Error 153)

> วิธีตรวจ: อ่านโค้ดอย่างเดียว ไม่แก้โค้ด (`views.py`, `player.html`, `embed_test.html`, `sw.js`, `settings.py` + git history)

## 1. API — keys / params / timeout / quota

- **Keys rotation** (`music/views.py:103-114` `_youtube_api_keys`): ลำดับ `YOUTUBE_API_KEYS` (comma-separated, หลายคีย์) → `YOUTUBE_API_KEY` → `key` → `YOUTUBE_API_KEY_2`; ตัดค่าว่าง + dedupe; ไม่ log ค่าคีย์
- **Failover**: `youtube_api_search` วนทีละคีย์ — 403 quota/rate-limit → `continue` คีย์ถัดไป; network error → คีย์ถัดไป; error อื่น → `[]` ทันที (ไม่มี yt-dlp fallback ใน search path)
- **Params** (`views.py:126-136`): `part=snippet`, `type=video`, `maxResults≤50`, `regionCode=TH`, `videoCategoryId=10` (Music), `videoEmbeddable=true`, `videoSyndicated=true`
- **Timeout 8s**: `urlopen(..., timeout=8)` ทั้ง search และ `video_duration` (`views.py:140,721`); DeepSeek 10s (`views.py:613`)
- **Quota**: search 1 ครั้ง = **100 units**; default quota 10,000 units/วัน → ~100 search/วัน/คีย์ (ยังไม่รวม `videos.list` ของ duration API)
- **เช็ค quota**: Google Cloud Console → APIs & Services → Enabled APIs → YouTube Data API v3 → Quotas (ดูกราฟ % ใช้ไป + ตั้ง alert); ถ้า 403 quotaExceeded ใน log Render = หมด ให้เพิ่มคีย์ใน `YOUTUBE_API_KEYS`
- **สรุป**: API ฝั่ง server ปกติ — คอมเล่นได้ = keys/quota ไม่ใช่สาเหตุ iPad 153

## 2. Player config — host / playerVars / origin / allow

- **Host**: `https://www.youtube-nocookie.com` (เลี่ยง ITP/Private Relay cookie blocking) — `player.html:614`
- **playerVars @HEAD (f431b9b)**: minimal 3 ตัว `controls=1, origin, enablejsapi=1` — เหมือน bare page; ตัด `autoplay/mute/modestbranding/rel/playsinline/iv_load_policy/fs` ออกแล้วเรียก `safePlayMuted()` ใน onReady
- **Working tree ตอนนี้**: มี uncommitted change (เลนขนาน ไม่ใช่ไฟล์นี้) เติม 9 vars กลับ + ตัด `safePlayMuted()` — รายงานนี้อ้าง HEAD/f431b9b เป็นหลัก
- **origin**: `window.location.origin` + `enablejsapi: 1`
- **allow attr**: `autoplay; encrypted-media; fullscreen; picture-in-picture` + `allowFullscreen` — patch ใน onReady 200ms + ตอน `visibilitychange` กลับมา (quirk iOS Safari)
- **Overlay**: `#sound-overlay` เดียว → `handleOverlayTap()` (unmute + playVideo ใน user gesture; iOS ยิง `playVideo` ซ้ำหลัง 50ms)
- **Diff vs bare `embed_test` sec 1**: sec 1 = plain `<iframe nocookie/embed/...>` ไม่มี JS API → **เล่นได้**; player จริง = `new YT.Player` (JS API handshake) → **153** แม้ vars เหลือ 3 ตัวเท่า sec 2 → ต่างที่ JS API handshake ไม่ใช่จำนวน vars

## 3. YouTube permissions / environment

- **Embed checks ฝั่ง server**: API params `videoEmbeddable/videoSyndicated=true` กรองตั้งแต่ต้นทาง + `_is_embeddable` (yt-dlp: `playable_in_embed`, availability, playabilityStatus — เทียบเท่าเช็ค oEmbed/embed) ใช้เฉพาะ hits deep-check; search path ไม่เรียก (ช้า + Render 429/bot)
- **Checklist iPad ที่ต้องไล่**:
  - [ ] ITP: Settings → Safari → ปิด `Prevent Cross-Site Tracking` แล้วลองใหม่
  - [ ] Private Relay: Settings → iCloud → ปิด Private Relay (Wi-Fi) แล้วลองใหม่
  - [ ] DNS: ลอง DNS ปกติ (เอา custom DNS/adblock DNS ออก)
  - [ ] Content blocker: ปิด Safari extensions/adblock ทั้งหมด
  - [ ] โหมด: ปิด `Request Desktop Website`, ลอง Safari ปกติ (ไม่ใช่ Private), ลอง Chrome บน iPad เทียบ
- **ผลเทส 4 ส่วน** (`embed_test.html`, วิดีโอ `ks7p6DA0dKk`):
  - sec 1 plain iframe (nocookie, ไม่มี JS) → **เล่นได้**
  - sec 2 YT.Player minimal (`controls/origin/enablejsapi`, `loadVideoById` ใน click) → **153**
  - sec 3 YT.Player พร้อม `videoId` ตั้งแต่สร้าง → **153**
  - sec 4 YT.Player ไม่มี `origin` → **153**
  - สรุป: **JS API ใช้ไม่ได้บน iPad เครื่องนี้** (ทุกท่าที่ผ่าน `new YT.Player` พัง; iframe เปล่ารอด)
- **Mobile-data test**: ใน repo **ไม่มีผลบันทึก** — ต้องเทส: ปิด Wi-Fi → เปิด Cellular → โหลด `/embed-test/` sec 2–4; ถ้าเล่นได้ = เน็ตเวิร์ก/Wi-Fi (DNS/filter) เป็นสาเหตุ; ถ้ายัง 153 = ตัวเครื่อง (ITP/Relay/policy)

## 4. Structure — overlay / polling / SW / breaker

- **Overlay เดียว**: `#sound-overlay` เท่านั้น (ไม่มี overlay ซ้อน); `fetchQueue` มี `show/hideSoundOverlay` helpers; กฎ iPad reload: ยังไม่มี gesture → โชว์ overlay อย่างเดียว **ไม่เรียก `playNext`** (กัน 153)
- **Polling 3s**: `pollInterval=3000` (`player.html:1437-1451`); เพลงใหม่เข้า → fast-poll 1s นาน 10s แล้วกลับ 3s; `pagehide` หยุด poll, `pageshow` (bfcache) กลับมา fetch ใหม่
- **SW**: `CACHE_NAME = "yum-juke-v2"` (`sw.js:1`); `/api/*` = network-first (ไม่ cache คิว); shell (`/`, `/request/`, logo, manifest) cache-first; ไม่แตะ YouTube iframe (ไม่เกี่ยว 153)
- **Breaker + full-stop** (`06b8334/15db0c9/e4e7e7c`): `consecutive153>=3` → `breakerTripped=true`, ข้ามเพลงพัง (`skipSong`), โชว์ overlay + toast "ตรวจพบปัญหาเล่นไม่ได้หลายเพลงติด", **หยุดสนิท** (`playNext` return ทันทีถ้า trip) จนกว่าแตะ overlay (รีเซ็ตตัวนับ); รีเซ็ตเมื่อ PLAYING สำเร็จ; 153 เดี่ยว/คู่ = soft-skip เดิม + POST `/api/block` + toast "ข้ามเพลงที่เล่นไม่ได้"
- **NoAPI escape hatch** (`6d3a34a`, `?noapi=1`): plain iframe + timer จาก `/api/duration/` — ทางรอดถ้า JS API พังถาวรบนเครื่องนั้น

## Verdict

- **ฝั่งโค้ดหมดแล้ว**: minimal vars (f431b9b) → ยัง 153; ตัด origin (sec 4) → ยัง 153; nocookie host → ยัง 153; เหลือสาเหตุระดับ **device/network** (ITP / Private Relay / DNS / content-blocker / policy บน iPad เครื่องนี้)
- **3 ทางเลือก**:
  1. **Accept** — iPad เครื่องนี้ใช้เป็น request-only (ขอเพลง) + เปิด `?noapi=1` ถ้าจะเล่น; ไม่ไล่ต่อ
  2. **Remote debug via Mac** — เสียบ iPad → Safari Web Inspector ดู console/network ตอน 153 ว่าเป็น handshake/block ตัวไหน
  3. **Host experiment** — ลองสลับ `host` กลับ `youtube.com` (หรือ `www.youtube.com`) บน iPad เครื่องนี้ เทียบ nocookie ว่าฝั่งไหนรอด
