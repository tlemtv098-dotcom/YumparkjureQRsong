# Album Everywhere and iPad Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** อัลบั้ม 1 ชม. โผล่ทั้งค้นหา+แนะนำ และรายงานสาเหตุ iPad Safari เล่นไม่ได้ (Q112=B)

**Estimated tasks:** 3 | **Estimated time:** ~45 min | **Touches:** API / Frontend / Tests / Docs

## Current Problem / Current Solution

- `_is_album_title` (backend `views.py:52`) + `isAlbumLike` (2 templates) กรอง `longplay|รวม.*เพลง|ชั่วโมง|อัลบั้ม|...` ออกจาก search/hits/add ทั้งระบบ + `add_to_queue` ปฏิเสธ 400 — ผู้ใช้อยากได้อัลบั้ม 1 ชม. กลับมาทั้งค้นหาและแนะนำ ( supersede การตัดสินใจกรองออกเดิมโดยชัดแจ้ง Q112=B)
- iPad Safari 153 ทุกวิดีโอที่ต้องใช้ JS API (เทส 4 ส่วนแล้ว) ยังไม่รู้สาเหตุระดับโครงสร้าง

## Proposed Approach

- ปลดกรองอัลบั้มทุกจุด: backend ลบ `_is_album_title` ออกจาก `youtube_api_search`, `search_youtube`, `search_song`, `hits`, `add_to_queue`/`add_to_queue_front` (คง `_is_chart_title`? ไม่ — chart ก็คืออัลบั้มรวม ปลดด้วย เหลือแค่ blocked/AI/non-music) + frontend ลบ `!isAlbumLike` ออกจาก filter ทั้ง 4 จุด (request filterBlockedSongs, player manualSearch/fetchHits) — เก็บฟังก์ชันไว้เฉยๆ ไม่ลบเพื่อไม่พัง test เก่าที่เช็คชื่อ? ไม่ — test เก่าเช็ค `isAlbumLike` มีอยู่ ถ้าลบออก test ตก ต้องอัปเดต test ด้วย
- Audit iPad (ไม่แก้โค้ด): ตรวจ API (keys/quota/params), player config (host/vars/origin/allow), YouTube permissions (embed/ITP/relay/DNS), โครงสร้าง (overlay/polling/SW cache) → เขียน `docs/superpowers/ipad-safari-audit.md` สรุปสาเหตุ + ทางเลือก

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| ค้นหา "รวมเพลง" | โดนกรอง/400 | โผล่ ขอได้ |
| hits | ไม่มีอัลบั้ม | มีอัลบั้มปนได้ |
| iPad สาเหตุ | กระจัดกระจาย | รายงานเดียวจบ |

## Assumptions & Risks

- **Assumed:** ปลดอัลบั้มแล้ว auto-random อาจสุ่มเจอ 1 ชม. — รับได้ (ผู้ใช้ขอเอง)
- **Assumed:** Task 2 ค้างของ playervars-revert (MinimalPlayerVars test ตก 1) — งานนี้จะแตะ tests.py อาจชน ต้องแก้ test อัลบั้มพร้อมกันและระวัง test เดิม
- **Risk:** อัลบั้มยาวมัก embed ไม่ได้ → 153 + auto-block กลับมาเยอะ — soft-skip/breaker รับมืออยู่

## Impact

- แตะ filter อัลบั้มทุกจุด + test + รายงาน audit 1 ไฟล์

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Unblock album backend+frontend]** - Lane A | Can run together: none | Must wait for: none | TDD slice: album passes filters -> remove album checks -> `manage.py test`
2. **[Fix tests for album]** - Sequential | Can run together: none | Must wait for: Task 1 | TDD slice: album tests green -> update tests -> `manage.py test`
3. **[iPad audit report]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: docs-only -> write audit -> verify file

---

### Task 1: Unblock album backend+frontend

**Files:**

- Modify: `music/views.py` (ลบ `_is_album_title` ออกจากทุก filter + add endpoints; เก็บฟังก์ชัน+CHART_RE ไว้เฉยๆ), `music/templates/music/player.html` (ลบ `!isAlbumLike` 2 จุด), `music/templates/music/request.html` (ลบ 1 จุด)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 3`
- Must wait for: `none`
- Race risk: `views.py` + 2 templates (worker เดียวทำรวดเดียว ไม่ขนานกับ Task 2)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_album_allowed():
    # mocked API returns Longplay title -> search/hits must include it
    pass
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (โดนกรองอยู่).

- [ ] **Step 3: Implement the minimal code**

ลบเฉพาะ `_is_album_title(...)` checks (คง blocked/AI/non-music/chart? — chart คืออัลบั้มรวม ลบด้วย เหลือ blocked/AI/non-music) ทั้ง backend+frontend ตาม grep 34 จุดที่เจอ (ไม่ลบฟังก์ชันทิ้ง)

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: PASS (ยกเว้น test อัลบั้มเก่าที่ต้องแก้ใน Task 2).

- [ ] **Step 5: Refactor only after green**

Rerun test. No commit/push.

---

### Task 2: Fix tests for album

**Files:**

- Modify: `music/tests.py`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1` (shared test file + ค้าง MinimalPlayerVars 1 fail จากงานก่อน — แก้รวมทีเดียว: อัปเดต Minimal test เป็น full-set + อัปเดต album tests เป็น allow)
- Race risk: `music/tests.py` shared — must run last among test edits

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

Album allow assertions.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL until Task 1 merged (+ Minimal 1 fail เก่ารอแก้รวม).

- [ ] **Step 3: Implement the minimal code**

Only `music/tests.py`: album tests → allow; MinimalPlayerVars test → full-set expectation (ปิดงานค้าง Task 2 ของ playervars-revert ไปด้วย).

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS (target 80+), plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun. No commit/push.

---

### Task 3: iPad audit report

**Files:**

- Create: `docs/superpowers/ipad-safari-audit.md`
- Inspect (read-only): `music/views.py` (`youtube_api_search` keys/params), `player.html` (host/vars/origin/allow), `embed_test.html` (4 sections), Render env names, SW cache version

**Parallelization:**

- Can run with: `Task 1`
- Must wait for: `none`
- Race risk: `none` (docs-only, read-only elsewhere)

- [ ] **Step 0: Docs-only exception**

No behavior test appropriate. Verification = file exists with 4 sections (API/PlayerConfig/Permissions/Structure) + verdict + next options.

- [ ] **Step 1: Write the report**

`docs/superpowers/ipad-safari-audit.md`: (1) API — keys/quota/params ที่ใช้ + วิธีเช็ค quota; (2) Player config — host/vars/origin/allow เทียบ bare page; (3) YouTube permissions — embed/ITP/relay/DNS/content-blocker checklist + ผลเทส 4 ส่วน; (4) Structure — overlay/polling/SW/v2 cache; verdict + ทางเลือก 3 ทาง (accept/รีโมต debug/ทดลอง host)

- [ ] **Step 2: Verify**

`Test-Path` + `manage.py test` green (untouched code paths).
