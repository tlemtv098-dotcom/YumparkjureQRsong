# Minimal PlayerVars Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** player ใช้ playerVars แค่ origin+enablejsapi+controls เหมือนหน้าเปล่าที่ iPad เล่นได้ (Q90=A)

**Estimated tasks:** 2 | **Estimated time:** ~20 min | **Touches:** Frontend / Tests

## Current Problem / Current Solution

- หน้าเปล่า `/embed-test/` (nocookie + ไม่มี playerVars) เล่นได้บน iPad แต่ player จริง (`player.html:600-614`) ใส่ 9 ตัว (`autoplay/mute/controls/modestbranding/rel/playsinline/iv_load_policy/fs/origin/enablejsapi`) แล้ว 153 ทุกเพลงบน iPad — ตัวต่างเดียวคือ playerVars
- `mute/autoplay` ตั้งต้นจะหาย ต้องสั่ง `player.mute()` + `playVideo()` ผ่าน API หลัง ready (โค้ดมี `safePlayMuted` อยู่แล้ว)

## Proposed Approach

- `playerVars` เหลือ `{'controls': 1, 'origin': window.location.origin, 'enablejsapi': 1}` ลบ `autoplay/mute/modestbranding/rel/playsinline/iv_load_policy/fs`
- ชดเชย: `onReady` เรียก `safePlayMuted()` ทันที (mute+play ผ่าน API แทน playerVars) — คง autoplay-muted behavior เดิม
- คง host nocookie, allow patch, overlay, breaker, queue logicทั้งหมด

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| iPad เล่น | 153 (9 vars) | ลุ้นเหมือนหน้าเปล่า (3 vars) |
| Desktop | เล่นได้ | ต้องยังเล่นได้ (verify via tests + live) |

## Assumptions & Risks

- **Assumed:** สาเหตุคือ playerVars ตัวใดตัวหนึ่ง ไม่ใช่ host/JS flow
- **Risk:** ถ้ายัง 153 แปลว่าไม่ใช่ playerVars ต้องสืบต่อ (loadVideoById/flow)

## Impact

- แตะ `playerVars` + `onReady` ใน `player.html` ไม่เกิน 15 บรรทัด

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Minimal playerVars]** - Lane A | Can run together: none | Must wait for: none | TDD slice: 3 vars present -> trim vars -> `manage.py test`
2. **[Regression test]** - Sequential | Can run together: none | Must wait for: Task 1 | TDD slice: config test -> add test -> `manage.py test`

---

### Task 1: Minimal playerVars

**Files:**

- Modify: `music/templates/music/player.html:600-622` (YT.Player config + onReady)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_player_minimal_vars():
    html = self.client.get("/").content.decode()
    assert "'enablejsapi': 1" in html and "'mute': 1" not in html
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (`'mute': 1` still present).

- [ ] **Step 3: Implement the minimal code**

In `player.html` YT.Player config only: playerVars → `{'controls': 1, 'origin': window.location.origin, 'enablejsapi': 1}`; onReady เพิ่ม `safePlayMuted()` ทันทีหลัง `isPlayerReady = true` (ก่อน fetchQueue). Keep host nocookie, allow patch, everything else.

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

Only add test in `music/tests.py` (no prod code).

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun. No commit/push.
