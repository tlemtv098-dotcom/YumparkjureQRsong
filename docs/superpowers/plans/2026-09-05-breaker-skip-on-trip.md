# Breaker Skip on Trip Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** breaker trip แล้วข้ามเพลงพังด้วย แตะเล่นเพลงถัดไปได้ ไม่ค้างเพลงเดิม (Q58=A)

**Estimated tasks:** 2 | **Estimated time:** ~15 min | **Touches:** Frontend / Tests

## Current Problem / Current Solution

- `player.html` breaker (`06b8334`): 153 ครั้งที่ 3 `return` เลย ไม่เรียก `skipSong` → `currentSong` ค้างเพลงพัง แตะ overlay (`handleOverlayTap`) รีเซ็ตตัวนับแต่เจอ `currentSong` เดิมเลย `playVideo` เพลงเดิม → 153 วนไม่รู้จบ ผู้ใช้เห็น "เล่นไม่ได้" (ก่อนแก้ปุ่มเล่นได้เพราะยังไม่มี breaker ตอนนั้นผู้ใช้จำสลับกับปุ่มเพราะเวลาใกล้กัน)
- diff `2672694..HEAD` ยืนยันปุ่มเป็น class อย่างเดียว ไม่เกี่ยว

## Proposed Approach

- ใน trip branch (`consecutive153 >= 3`) ก่อน `return`: เรียก `skipSong()` เพื่อล้าง `currentSong` พังออกจากคิว (ยังไม่ POST block, ยังไม่ playNext/fetchQueue — คงเจตนา breaker หยุด loop) แล้วโชว์ overlay + toast เดิม
- ผล: แตะ → `!currentSong && queue.length > 0` → `playNext()` เพลงถัดไป ไม่วนเพลงเดิม
- จุดเดียว ไม่แตะ threshold/backend

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| trip ครั้งที่ 3 | currentSong ค้าง แตะวนเพลงเดิม | ข้ามเพลงพัง แตะเล่นเพลงถัดไป |
| 153 เดี่ยว/คู่ | ข้ามปกติ | เท่าเดิม |

## Assumptions & Risks

- **Assumed:** `skipSong` ปลอดภัยตอน trip (แค่ลบออกจากคิว local + fetch played)
- **Risk:** ถ้า iPad บล็อกทุกเพลงจริง แตะแล้วจะ 153 เพลงถัดไปจน trip ใหม่ — แต่ไม่ค้างเพลงเดิมแล้ว

## Impact

- แตะ `onError` trip branch ใน `player.html` 2-3 บรรทัด

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Skip on trip]** - Lane A | Can run together: none | Must wait for: none | TDD slice: trip skips song -> add skipSong -> `manage.py test`
2. **[Regression test]** - Sequential | Can run together: none | Must wait for: Task 1 | TDD slice: trip test -> add test -> `manage.py test`

---

### Task 1: Skip on trip

**Files:**

- Modify: `music/templates/music/player.html` (trip branch `consecutive153 >= 3`)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_breaker_trip_skips_song():
    html = self.client.get("/").content.decode()
    # trip branch must call skipSong (grep markers)
    assert "consecutive153 >= 3" in html
```

(refine: assert skipSong appears inside trip block — worker to define exact marker, e.g. read lines around `>= 3` and assert `skipSong()` between trip `if` and its `return`)

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (trip returns without skip today).

- [ ] **Step 3: Implement the minimal code**

In trip branch only: add `try { skipSong(); } catch(e) {}` before `return` (after overlay/toast lines). Keep: no POST block, no playNext, no fetchQueue on trip. Keep `< 3` flow untouched.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: PASS.

- [ ] **Step 5: Refactor only after green**

Rerun test. No commit/push.

---

### Task 2: Regression test

**Files:**

- Modify: `music/tests.py`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1` (shared test file)
- Race risk: `music/tests.py` shared — must run last

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

Same as Task 1 Step 1 (lock trip-skips behavior).

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL until Task 1 merged.

- [ ] **Step 3: Implement the minimal code**

Only add test in `music/tests.py` (no prod code).

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun. No commit/push.
