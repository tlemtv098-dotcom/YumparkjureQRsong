# Unblock Fallback IDs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** hits ไม่ว่างเพราะ DB บล็อกเพลง fallback — ห้ามบล็อก 8 id จริง + มีทางล้างของเก่า (Q42=A)

**Estimated tasks:** 3 | **Estimated time:** ~30 min | **Touches:** API / Tests

## Current Problem / Current Solution

- Live: `home 200`, `/api/queue` OK, `/api/search` ได้ 5 เพลงจริง แต่ `/api/hits` คืน 0 → เพลงแนะนำว่าง เปิดเพลงจาก hits ไม่ได้
- สาเหตุ: `BlockedVideo` บน Render สะสมจาก auto-block (player `onPlayerError` POST `/api/block/` + `search_youtube` embed check) จนกรอง fallback 8 เพลงทิ้งหมดทุก path (`_is_blocked` เช็ค DB ทุกตัว)
- Local `test` 65 OK เพราะ DB test ว่าง — จับบัคนี้ไม่ได้

## Proposed Approach

- เพิ่ม `FALLBACK_IDS` (8 id ตรงกับ `_fallback_static`) ใน `music/views.py`
- `block_video`: ถ้า id อยู่ใน FALLBACK_IDS ตอบ `{"status":"skipped"}` ไม่บันทึก
- `search_youtube` embed auto-block: ข้าม FALLBACK_IDS ไม่ `get_or_create`
- เพิ่ม `POST /api/block/clear/` owner-only (`X-Player-Token` แบบ `clear_queue`) ลบแถว FALLBACK_IDS ออกจาก DB (ล้างของเก่าบน Render) — ไม่แตะแถวอื่น
- Trade-off: 8 เพลงนี้ไม่มีวันถูกบล็อกถาวร ถ้าเล่นไม่ได้จริงจะ soft-skip ข้ามให้เหมือนเดิม (memory-only)

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| 153 เพลง fallback บน iPad | เข้า DB ถาวร → hits ว่างถาวร | ไม่บันทึก → hits ไม่ว่าง |
| Render DB มี 8 id อยู่แล้ว | hits 0 ตลอด | เรียก clear 1 ครั้งกลับมา |
| เพลงอื่น error 153 | บล็อกปกติ | เท่าเดิม |

## Assumptions & Risks

- **Assumed:** 8 fallback id เล่นได้จริงส่วนใหญ่ (verify มานาน) — ถ้าตัวไหนเล่นไม่ได้จริง soft-skip จัดการรายครั้ง
- **Risk:** ถ้า Render DB ไม่ได้มี 8 id นี้ (สาเหตุอื่น) clear แล้ว hits ยัง 0 — ต้องสืบ filter อื่นต่อ

## Impact

- แตะ `block_video`, embed auto-block, เพิ่ม 1 endpoint owner-only — ไม่แตะ frontend/queue/player

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Guard fallback IDs]** - Lane A | Can run together: none | Must wait for: none | TDD slice: block fallback skipped -> guard block paths -> `manage.py test`
2. **[Clear-blocked endpoint]** - Lane B | Can run together: none | Must wait for: Task 1 | TDD slice: owner clears fallback rows -> add endpoint -> `manage.py test`
3. **[Regression tests]** - Sequential | Can run together: none | Must wait for: Task 1, Task 2 | TDD slice: fallback never blocked test -> add tests -> `manage.py test`

---

### Task 1: Guard fallback IDs

**Files:**

- Modify: `music/views.py` (FALLBACK_IDS + `block_video` + embed auto-block)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none` (views.py เดียว)
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_block_fallback_skipped():
    res = client.post('/api/block/ks7p6DA0dKk/')
    assert res.json()['status'] == 'skipped'
    assert BlockedVideo.objects.filter(video_id='ks7p6DA0dKk').count() == 0
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (today returns blocked + creates row).

- [ ] **Step 3: Implement the minimal code**

In `music/views.py` only: add `FALLBACK_IDS = {...8 ids...}` (ตรง `_fallback_static`); `block_video` return skipped if in set (still require owner? keep current behavior + skip); embed auto-block `get_or_create` skip if in set.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: PASS.

- [ ] **Step 5: Refactor only after green**

Rerun test. No commit/push.

---

### Task 2: Clear-blocked endpoint

**Files:**

- Modify: `music/views.py` (`clear_blocked`), `music/urls.py`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1` (same views.py area + test file)
- Race risk: `music/views.py` + `music/urls.py`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_clear_blocked_owner_only():
    # without token 403; with X-Player-Token deletes only FALLBACK_IDS rows, keeps others
    pass
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (no endpoint → 404).

- [ ] **Step 3: Implement the minimal code**

Add `POST /api/block/clear/` with `_is_owner` check (patternเดียวกับ `clear_queue`): `BlockedVideo.objects.filter(video_id__in=FALLBACK_IDS).delete()` return deleted count. Add route in `music/urls.py`.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: PASS.

- [ ] **Step 5: Refactor only after green**

Rerun test. No commit/push.

---

### Task 3: Regression tests

**Files:**

- Modify: `music/tests.py`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1, Task 2` (shared test file)
- Race risk: `music/tests.py` shared — must run last

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

Lock: `/api/hits/` with mocked empty live + DB containing blocked non-fallback ids still returns fallback 8 (fallback never filtered by DB).

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL until Tasks 1-2 merged.

- [ ] **Step 3: Implement the minimal code**

Only add tests in `music/tests.py` (no prod code).

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun. No commit/push.
