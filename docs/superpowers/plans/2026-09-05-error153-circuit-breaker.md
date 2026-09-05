# Error 153 Circuit Breaker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 153 รัวทุกเพลงบน iPad แล้วหยุดเอง ไม่ล้างคิว ไม่พิษ DB (Q48=A)

**Estimated tasks:** 2 | **Estimated time:** ~20 min | **Touches:** Frontend / Tests

## Current Problem / Current Solution

- iPad Gen 9 กดเล่นแล้ว 153 รัวทุกเพลง คิวโดนล้างทีละเพลง + เข้า DB ทีละเพลง (`player.html:621-645` `onError` → `blockedVideoIds.add` + POST `/api/block/` + `skipSong` + `playNext` ใน 500ms วนไปเรื่อย)
- 153 รัวทุกเพลง = เป็นที่เครื่อง (ITP/Private Relay/cookie) ไม่ใช่ที่เพลง แต่โค้ดปฏิบัติเหมือนเพลงเสียทีละเพลง

## Proposed Approach

- เพิ่ม `let consecutive153 = 0` ข้าง `last153Time` (`player.html:352`)
- ใน `onError` 153: `consecutive153++`; ถ้า `< 3` ทำเหมือนเดิม (skip + playNext); ถ้า `>= 3` หยุด loop: ไม่เรียก `skipSong`/`playNext`/`fetchQueue` ต่อ, ไม่ POST block เพลงที่ 3+, โชว์ `sound-overlay` พร้อม toast `ตรวจพบปัญหาเล่นไม่ได้หลายเพลงติด แตะเพื่อลองใหม่` ให้ user แตะแล้ว `consecutive153 = 0` เริ่มใหม่
- รีเซ็ต `consecutive153 = 0` เมื่อ `PLAYING` สำเร็จ (`onPlayerStateChange`) และใน `handleOverlayTap`
- ไม่แตะ backend/queue/153 ครั้งเดี่ยว

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| 153 เพลงเดียว | ข้าม + บล็อก | เท่าเดิม |
| 153 ติดกัน 3 เพลง | ล้างคิวต่อ + พิษ DB | หยุด โชว์แตะเพื่อลองใหม่ ไม่บันทึกเพิ่ม |
| เพลงเล่นได้ | — | รีเซ็ตตัวนับ |

## Assumptions & Risks

- **Assumed:** 3 ครั้งติด = device issue (ตาม Q48)
- **Risk:** เพลงเสียจริง 3 ตัวติดจะหยุดเร็ว — แตะทีเดียวเล่นต่อได้ รับได้

## Impact

- แตะ `onError` + `onPlayerStateChange` + `handleOverlayTap` ใน `player.html` จุดเดียว

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Circuit breaker]** - Lane A | Can run together: none | Must wait for: none | TDD slice: breaker trips at 3 -> add counter -> `manage.py test`
2. **[Regression test]** - Sequential | Can run together: none | Must wait for: Task 1 | TDD slice: breaker test -> add test -> `manage.py test`

---

### Task 1: Circuit breaker

**Files:**

- Modify: `music/templates/music/player.html:352` (counter), `:629-645` (153 branch), PLAYING reset, `handleOverlayTap` reset
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_player_has_153_breaker():
    html = self.client.get("/").content.decode()
    assert "consecutive153" in html
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (no counter today).

- [ ] **Step 3: Implement the minimal code**

In `player.html` only: `let consecutive153 = 0` ข้าง `last153Time`; 153 branch นับ + trip ที่ 3 (หยุด skip/playNext/block, โชว์ overlay + toast ไทย); reset ที่ PLAYING + overlay tap. ไม่แตะ backend.

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

Same as Task 1 Step 1 + assert reset on PLAYING/handler present.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL until Task 1 merged.

- [ ] **Step 3: Implement the minimal code**

Only add tests in `music/tests.py` (no prod code).

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun. No commit/push.
