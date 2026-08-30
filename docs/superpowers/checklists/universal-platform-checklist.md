# Universal Platform Verification Checklist

> **Goal:** ยืนยันว่าเว็บเล่นได้เหมือนกันทุกแพลตฟอร์มหลังแก้ Error 153 + uniform tap-gate

**Deploy URL:** `https://yumpakjure.onrender.com/` (หรือ Render URL ปัจจุบัน)
**Branch:** `master` หลัง merge 2026-08-31-universal-platform-support

## How to verify

1. เปิดแต่ละอุปกรณ์/เบราว์เซอร์ ด้านล่าง
2. ทำ 5 ขั้นตอน: เปิดเว็บ → ค้นหาเพลง → เพิ่มคิว → แตะ overlay → เล่น/ข้าม
3. ติ๊กช่องถ้าผ่าน ไม่ติ๊ก = ถ่าย error console มา

| # | อุปกรณ์/เบราว์เซอร์ | เปิดเว็บ | ค้นหา (ไม่เจอ 153) | เพิ่มคิว | แตะเพื่อเปิดเสียง | เล่น | ข้ามเพลง (153 soft-skip) | หมายเหตุ |
|---|----------------------|-----------|---------------------|-----------|---------------------|--------|---------------------------|-----------|
| 1 | iPhone Safari | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | |
| 2 | iPhone Chrome (iPhone 13) | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | เคสหลักที่เคย error 153 |
| 3 | iPad Safari + Chrome | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ปิด Request Desktop Website |
| 4 | Android Chrome | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | |
| 5 | Desktop Chrome / Safari / Firefox | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ต้อง tap ครั้งแรกแล้ว |
| 6 | LINE in-app WebView (สแกน QR ใน LINE) | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ควรเห็น banner เปิดในเบราว์เซอร์ภายนอก |

## Expected after fix

- **Search/Hits:** ไม่โชว์เพลงที่ embed ไม่ได้ (VEVO/Major label ที่เคย 153 หายจาก list)
- **Player:** ทุกที่โชว์ `#queue-overlay` แตะเพื่อเปิดเสียง ก่อนเล่นครั้งแรก (uniform tap-gate)
- **Error 153:** ถ้ายังหลุดมา soft-skip: toast `เพลงนี้เล่นไม่ได้ (ลิขสิทธิ์) → ข้ามไปเพลงถัดไป` + `blockedVideoIds` memory-only ไม่ POST /api/block
- **LINE WebView:** เห็น banner `เปิดในเบราว์เซอร์ภายนอก` + serviceWorker ไม่ลงทะเบียน
- **Host:** `https://www.youtube.com` + `playsinline webkit-playsinline`

## Quick console checks

- Chrome DevTools Device Toolbar (iPhone 14 Pro / iPad / Galaxy S20): Network `youtube.com` 200, Console ไม่มี Error 5/150/153 ค้าง
- Render Logs: `search_youtube` ไม่ return `raw[:5]` ที่ยังบล็อก

## Sign-off

- Date: ___________
- Tester: ___________
- Result: ☐ PASS (ติ๊กครบ) / ☐ FAIL (ระบุช่องที่ fail)
