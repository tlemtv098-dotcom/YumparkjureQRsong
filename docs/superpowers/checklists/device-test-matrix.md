# Device Test Matrix

> **Goal:** ตารางเทสหลายรุ่น (iPhone SE/14, Pixel 7, iPad mini/Pro/gen 9, Android, Desktop) + วิธีเพิ่ม custom device ใน Chrome DevTools

**Deploy URL:** `https://yumpakjure.onrender.com/` (หรือ Render URL ปัจจุบัน)
**โค้ดรองรับ:** `viewport-fit=cover`, `safe-area`, `touch-action`, Tailwind responsive (docs-only — ไม่แตะโค้ด)

## How to verify

1. เปิด Chrome DevTools Device Toolbar (Ctrl+Shift+M) เลือกแต่ละรุ่นด้านล่าง
2. ทำ 5 ขั้นตอน: เปิดเว็บ → ค้นหาเพลง → เพิ่มคิว → แตะ overlay → เล่น/ข้าม
3. ติ๊กช่องถ้าผ่าน ไม่ติ๊ก = ถ่าย error console มา

## Device matrix

| # | รุ่น (Viewport) | ขนาด (w×h) | เบราว์เซอร์ที่เทส | ผ่าน |
|---|----------------|------------|-------------------|------|
| 1 | Responsive | ปรับเอง | Desktop Chrome | ☐ |
| 2 | iPhone SE | 375×667 | iOS Safari / iOS Chrome | ☐ |
| 3 | iPhone 14 | 390×844 | iOS Safari / iOS Chrome | ☐ |
| 4 | iPhone 14 Pro Max | 430×932 | iOS Safari / iOS Chrome | ☐ |
| 5 | Pixel 7 | 412×915 | Android Chrome | ☐ |
| 6 | iPad mini | 768×1024 | iOS Safari / iOS Chrome | ☐ |
| 7 | iPad Pro | 1024×1366 | iOS Safari / iOS Chrome | ☐ |
| 8 | iPad gen 9 (custom — ดูวิธีเพิ่มด้านล่าง) | 810×1080 | iOS Safari / iOS Chrome | ☐ |
| 9 | Laptop | 1440×900 | Desktop Chrome / Safari / Firefox / Edge | ☐ |
| 10 | Desktop | 1920×1080 | Desktop Chrome / Safari / Firefox / Edge | ☐ |

## How to add a custom device in Chrome DevTools

รุ่นอย่าง iPad gen 9 (810×1080) ไม่มีใน preset — ต้องเพิ่มเอง:

1. เปิด Chrome DevTools (F12) → คลิกเฟือง **Settings** (มุมขวาบนของ DevTools)
2. เลือกแท็บ **Devices** (ซ้ายมือ)
3. คลิก **Add custom device**
4. กรอกตัวอย่าง iPad gen 9:
   - **Name:** `iPad gen 9`
   - **Width:** `810`
   - **Height:** `1080`
   - **Device pixel ratio:** `2`
   - **User agent string:** ใช้ default (ว่างไว้) หรือคัดลอก Safari on iPad
   - **Device type:** `Tablet`
5. คลิก **Add** → ปิด Settings
6. เปิด Device Toolbar (Ctrl+Shift+M) → เลือก `iPad gen 9` จาก dropdown Dimensions

## Playback limits per OS

- **iOS (Safari/Chrome) — tap once (autoplay policy):** iOS บล็อก autoplay ที่มีเสียง ต้องแตะ `#queue-overlay` ("แตะเพื่อเปิดเสียง") หนึ่งครั้งก่อนเล่นครั้งแรก ทุกอุปกรณ์ iOS ใช้ uniform tap-gate เดียวกัน
- **Error 153 auto-skip:** เพลงที่ embed ไม่ได้ (VEVO / major label) search จะกรองออกก่อน ถ้ายังหลุดมา player จะ soft-skip อัตโนมัติ: toast `เพลงนี้เล่นไม่ได้ (ลิขสิทธิ์) → ข้ามไปเพลงถัดไป` + จำใน `blockedVideoIds` (memory-only ไม่ POST /api/block)
- **Render cold-start retry:** Deploy ฟรีบน Render หลับเมื่อไม่มีทราฟฟิก เปิดครั้งแรกอาจช้า/timeout ให้รอ ~30–60 วินาทีแล้วกด retry/รีโหลดหนึ่งครั้ง
- **Background audio via Media Session:** เสียงพื้นหลังอาศัย Media Session API — ล็อกจอ/สลับแอปเพลงยังเล่นต่อได้บนเบราว์เซอร์ที่รองรับ (iOS Safari, Android Chrome, Desktop Chrome/Edge/Safari/Firefox); LINE in-app WebView อาจหยุด — ให้เปิดในเบราว์เซอร์ภายนอกผ่าน banner

## Sign-off

- Date: ___________
- Tester: ___________
- Result: ☐ PASS (ติ๊กครบ) / ☐ FAIL (ระบุช่องที่ fail)
