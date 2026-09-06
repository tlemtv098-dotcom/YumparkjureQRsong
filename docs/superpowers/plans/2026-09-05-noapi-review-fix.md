# NoAPI Review Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สั่งเพลงในโหมด noapi แล้วเล่นได้จริง — รีวิว flow หาบัคแก้จุดเดียว (Q102=A)

**Estimated tasks:** 2 | **Estimated time:** ~30 min | **Touches:** Frontend / Tests

## Current Problem / Current Solution

- `?noapi=1` ขึ้น live แล้ว (NOAPI markers ครบ, `/api/duration/` 200) แต่สั่งเพลงแล้วไม่เล่นบน iPad
- ผู้ต้องสงสัย: guard ข้าม `new YT.Player` ไม่ครบ (API สร้างทับ div), `playNext` ไม่ route ไป noapi ทุกทาง, timer duration ไม่ตั้ง, overlay บัง, `onYouTubeIframeAPIReady` ยังรัน

## Proposed Approach

- อ่าน `playNextNoApi` + จุดเรียก `playNext` ทั้งหมด + `onYouTubeIframeAPIReady` + overlay flow ใน noapi mode หาจุดที่ทำให้ไม่เล่น (เช่น guard หลุด, timer ไม่ตั้ง, iframe โดนเขียนทับ)
- แก้จุดเดียวที่เจอ + test ล็อค ไม่รื้อโหมด

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| ?noapi=1 สั่งเพลง | ไม่เล่น (สาเหตุในโค้ด) | เล่นผ่าน plain iframe |

## Assumptions & Risks

- **Assumed:** บัคอยู่ในโค้ด noapi (live พร้อมหมดแล้ว)
- **Risk:** ถ้ารีวิวไม่เจอบัคชัด ต้องเทสบน iPad จริงทีละจุด

## Impact

- แตะ `player.html` จุดที่เจอจุดเดียว

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Review + fix noapi]** - Lane A | Can run together: none | Must wait for: none | TDD slice: failing behavior test -> fix one point -> `manage.py test`
2. **[Regression test]** - Sequential | Can run together: none | Must wait for: Task 1 | TDD slice: noapi test -> add test -> `manage.py test`

---

### Task 1: Review + fix noapi

**Files:**

- Modify: `music/templates/music/player.html` (noapi branch only)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_noapi_flow_markers():
    html = self.client.get("/").content.decode()
    # markers proving noapi path is complete (guard + timer + iframe swap)
    assert "playNextNoApi" in html and "window.noapiTimer" in html
```

(refine markers after reading code: must cover the fixed point, e.g. guard in onYouTubeIframeAPIReady + timer set + overlay handling)

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL at the missing/broken point found in review.

- [ ] **Step 3: Implement the minimal code**

Fix the ONE point found (candidates: guard `new YT.Player` in noapi; route all `playNext` callers; set/clear `noapiTimer`; hide overlay in noapi). Keep normal API flow byte-identical in behavior.

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

Same as Task 1 Step 1.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL until Task 1 merged.

- [ ] **Step 3: Implement the minimal code**

Only add tests in `music/tests.py` (no prod code).

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun. No commit/push.
