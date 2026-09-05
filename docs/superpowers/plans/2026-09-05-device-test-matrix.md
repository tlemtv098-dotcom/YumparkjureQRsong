# Device Test Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ตารางเทสหลายรุ่น (iPhone SE/14, Pixel 7, iPad mini/Pro/gen 9, Android, Desktop) + วิธีเพิ่ม custom device

**Estimated tasks:** 1 | **Estimated time:** ~15 min | **Touches:** Docs

## Current Problem / Current Solution

- รูปรายการคือ Chrome DevTools presets ฝั่งเบราว์เซอร์ เพิ่มในโค้ดไม่ได้ (Q15=A)
- โค้ดรองรับทุกขนาดจอแล้ว (`viewport-fit=cover`, `safe-area`, `touch-action`, Tailwind responsive) แต่ไม่มีตารางเทสหลายรุ่นเป็นเอกสาร
- อยากเล่นได้ทั้งหมดทุกแพลตฟอร์ม — ต้องมีเมทริกซ์เทส + วิธีเพิ่มรุ่นเองใน DevTools

## Proposed Approach

- เพิ่ม `docs/superpowers/checklists/device-test-matrix.md`: ตารางรุ่น (ขนาดจอ, เบราว์เซอร์ที่เทส, ผล) + วิธี Add custom device ใน DevTools (iPad gen 9: 810x1080) + ข้อจำกัด playback ต่อ OS (iOS ต้องแตะครั้งเดียว, 153 ข้ามให้)
- Docs-only ไม่แตะโค้ด

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| อยากเทส iPad gen 9 | ไม่มีขนาดบอก | 810x1080 + วิธี add |
| อยากรู้รุ่นไหนเล่นได้ | กระจัดกระจาย | ตารางเดียวครบ |

## Assumptions & Risks

- **Assumed:** โค้ด responsive ครอบคลุมแล้ว ไม่ต้องแก้โค้ด
- **Risk:** ไม่มี — docs-only

## Impact

- เทสหลายรุ่นเป็นระบบ

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Device matrix doc]** - Lane A | Can run together: none | Must wait for: none | TDD slice: docs-only exception -> write file -> verify file exists + `manage.py test`

---

### Task 1: Device matrix doc

**Files:**

- Create: `docs/superpowers/checklists/device-test-matrix.md`
- Test: `music/tests.py` (no change — run to confirm green)

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Docs-only exception: no failing behavior test appropriate (no prod code change). Verification = file exists with required sections + `manage.py test` still green.

- [ ] **Step 1: Write the file**

Create `docs/superpowers/checklists/device-test-matrix.md` with: ตารางรุ่น (Responsive, iPhone SE 375x667, iPhone 14 390x844, iPhone 14 Pro Max 430x932, Pixel 7 412x915, iPad mini 768x1024, iPad Pro 1024x1366, iPad gen 9 810x1080, Laptop 1440x900, Desktop 1920x1080) + เบราว์เซอร์ต่อรุ่น (iOS Safari/Chrome, Android Chrome, Desktop Chrome/Safari/Firefox/Edge) + วิธี Add custom device + ข้อจำกัด playback (iOS tap ครั้งเดียว, 153 ข้าม, cold start retry).

- [ ] **Step 2: Verify**

`Test-Path` ไฟล์ + `venv\Scripts\python.exe manage.py test music.tests -v2` PASS (58 tests).
