# Hits Recent Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เพลงแนะนำทั้งสองหน้า (player+request) เป็นเพลงฮิตพึ่งอัปช่วงนี้ อัปเดตตลอด (Q135=A ชาร์ต+ค้นหาล่าสุด)

**Estimated tasks:** 2 | **Estimated time:** ~30 min | **Touches:** API / Frontend

## Current Problem / Current Solution

- `hits` ใช้ query คงที่ `เพลงไทยฮิต/เพลงฮิต 2025` + fallback 8 เพลงคงที่ + cache 60s แยก `player/request/ios` → ดูซ้ำเดิม
- ต้องการฮิตล่าสุด อัปเดตตลอด

## Proposed Approach

- `hits` query กว้าง + สด: เพิ่ม `ชาร์ตเพลงไทย 2026`, `เพลงมาแรง ตอนนี้`, `เพลงฮิต TikTok 2026`, `เพลงใหม่ 2026` + ใส่ `publishedAfter` หรือ `order=date` ไม่ได้ (search ไม่มี) → ใช้ `q` สด + `cache` ลดเหลือ 30s + `shuffle` + `dedup` + fallback สด (สุ่ม fallback ใหม่ทุกครั้ง)
- Frontend `fetchHits` ทุก 60s + หลัง `add`/`clear` + `visibilitychange` → อัปเดตตลอด
- ทั้งสองหน้าใช้ `?player=1` vs `?` เดิม แต่ชาร์ตเหมือนกัน แค่ `player` รวมอัลบั้มได้

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| hits | เดิม 60s ซ้ำ | 30s สด + query ใหม่ 2026/ชาร์ต/มาแรง |
| อัปเดต | กดรีเฟรชเอง | auto 60s + กลับหน้าแล้วโหลดใหม่ |

## Assumptions & Risks

- **Assumed:** YouTube search `q` มีเพลงใหม่พอ, ไม่ต้อง trending API แยก
- **Risk:** query ใหม่ 2026 อาจได้ผลน้อย → fallback 8 เพลงเดิมช่วย

## Impact

- แตะ `views.py` (hits queries + cache 30s), `player.html` + `request.html` (auto refresh interval)

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Hits recent queries + 30s cache]** - Lane A | Can run together: none | Must wait for: none | TDD slice: GET /api/hits/ returns 2026 query results -> update views.py -> `manage.py test`
2. **[Frontend auto update]** - Lane A | Can run together: none | Must wait for: Task 1 | TDD slice: fetchHits every 60s -> update player/request html -> `manage.py check`

---

### Task 1: Hits recent queries + 30s cache

**Files:**

- Modify: `music/views.py` (hits)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `views.py`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

`GET /api/hits/` with mock `search_youtube` should be called with query containing `2026` or `ชาร์ต`

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test -v2`. Expected: FAIL

- [ ] **Step 3: Implement the minimal code**

`views.py hits`: queries เพิ่ม `ชาร์ตเพลงไทย 2026`, `เพลงมาแรง 2026`, `เพลงฮิต TikTok 2026`, `เพลงใหม่ 2026` + `cache.set(...,30)` แทน 60 + `random.shuffle` + fallback สด

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test` PASS

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 2: Frontend auto update

**Files:**

- Modify: `music/templates/music/player.html` (fetchHits interval), `music/templates/music/request.html` (same)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1`
- Race risk: `player.html` + `request.html` (different files, okay)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` (visual).

- [ ] **Step 1: Write the failing test**

`player.html` contains `setInterval(fetchHits, 60000)` or `30000`

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Check `player.html` has `30000` not `60000`

- [ ] **Step 3: Implement the minimal code**

`player.html` + `request.html`: `setInterval(fetchHits, 60000)` + `document.addEventListener('visibilitychange', ... fetchHits)` + หลัง `add`/`clear` เรียก `fetchHits`

- [ ] **Step 4: Run the test and confirm it passes**

`manage.py check` PASS

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.
