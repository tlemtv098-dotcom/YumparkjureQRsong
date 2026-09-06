# Breaker Full Stop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** trip แล้วหยุดสนิทไม่วนเอง แตะค่อยเล่นเพลงถัดไป (Q62=A)

**Estimated tasks:** 2 | **Estimated time:** ~20 min | **Touches:** Frontend / Tests

## Current Problem / Current Solution

- trip-skip (`15db0c9`): trip เรียก `skipSong` → `removePlayedSong` → `finally fetchQueue` → `userInteracted` จริงเลย `playNext` เอง → 153 เพลงถัดไป → skip วนรัวทั้งคิว ผู้ใช้เห็น "ข้ามเพลงรัวๆ เล่นไม่ได้"
- ผิดที่ผมเอง: คิดว่า trip branch ไม่มี playNext แล้วจบ แต่ลืม chain ใน `removePlayedSong`

## Proposed Approach

- เพิ่ม `let breakerTripped = false` ข้าง `consecutive153`
- trip branch: ตั้ง `breakerTripped = true` + `skipSong()` + โชว์ overlay/toast + return (เหมือนเดิม)
- `fetchQueue`/`playNext` auto-path: ถ้า `breakerTripped` ข้าม auto-play (โชว์ overlay อย่างเดียว)
- `handleOverlayTap`: ล้าง `breakerTripped = false` + `consecutive153 = 0` แล้ว `playNext()` เพลงถัดไปตามปกติ
- PLAYING สำเร็จล้างทั้งสอง flag (มี consecutive แล้ว เพิ่ม breaker)
- จุดเดียวใน `player.html`

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| trip 153x3 | skip แล้ววนเองทั้งคิว | ข้ามเพลงพังแล้วหยุดสนิท |
| แตะหลัง trip | ไม่แน่นอน (race) | ล้าง flag เล่นเพลงถัดไปชัวร์ |
| 153 เดี่ยว/คู่ | ข้ามปกติ | เท่าเดิม |

## Assumptions & Risks

- **Assumed:** `fetchQueue` auto-playNext เป็นตัววน (ตาม Q62)
- **Risk:** ถ้าแตะแล้วเพลงถัดไป 153 อีก จะนับ 1 ใหม่ trip ใหม่ที่ 3 — ถูกต้องตาม design

## Impact

- แตะ `player.html` ไม่เกิน 10 บรรทัด

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Full stop flag]** - Lane A | Can run together: none | Must wait for: none | TDD slice: tripped blocks autoplay -> add flag -> `manage.py test`
2. **[Regression test]** - Sequential | Can run together: none | Must wait for: Task 1 | TDD slice: flag test -> add test -> `manage.py test`

---

### Task 1: Full stop flag

**Files:**

- Modify: `music/templates/music/player.html` (counter decl, trip branch, fetchQueue/playNext auto-path, handleOverlayTap, PLAYING reset)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_breaker_tripped_blocks_autoplay():
    html = self.client.get("/").content.decode()
    assert "breakerTripped" in html
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (no flag today).

- [ ] **Step 3: Implement the minimal code**

In `player.html` only: declare flag; set on trip; guard auto-playNext paths (`fetchQueue` hasNewSongs/!currentSong branches + `playNext` entry? minimal: guard `fetchQueue` auto `playNext()` calls + `removePlayedSong` finally `fetchQueue` chain? simplest robust: guard inside `playNext()` first line `if (breakerTripped && !userTapOverride) return;`... worker to choose minimal correct: flag checked in `fetchQueue` auto branches AND cleared+playNext in tap handler. Keep polling running (fetchQueue still polls, just no auto-play).

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

Same as Task 1 Step 1 + assert tap handler clears flag.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL until Task 1 merged.

- [ ] **Step 3: Implement the minimal code**

Only add tests in `music/tests.py` (no prod code).

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun. No commit/push.
