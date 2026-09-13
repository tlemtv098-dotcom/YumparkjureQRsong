# PlayerVars Revert Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ย้อน playerVars กลับชุดเต็ม 9 ตัวตอนที่ iPad เล่นได้ (Q110=A)

**Estimated tasks:** 2 | **Estimated time:** ~15 min | **Touches:** Frontend / Tests

## Current Problem / Current Solution

- `f431b9b` ลด playerVars เหลือ 3 ตัว (`controls/origin/enablejsapi`) + `safePlayMuted()` ใน `onReady` แต่ iPad ยัง 153 — ผู้ใช้ยืนยันว่าชุดเต็ม 9 ตัวตอนก่อนเล่นได้
- ชุดเต็มเดิม (`f431b9b^`): `autoplay/mute/controls/modestbranding/rel:0/playsinline/iv_load_policy:3/fs/origin/enablejsapi` + host nocookie, ไม่มี widget_referrer

## Proposed Approach

- คืน playerVars 9 ตัวเป๊ะตาม `f431b9b^` + ลบ `safePlayMuted()` ที่เติมใน `onReady` (กลับสภาพเดิมทั้งหมด)
- คง host nocookie, allow patch, breaker, queue logicทั้งหมด

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| iPad เล่น | 153 (3 vars) | ลุ้นเหมือนตอนเล่นได้ (9 vars) |

## Assumptions & Risks

- **Assumed:** ความจำผู้ใช้ถูกว่าตอน 9 vars เล่นได้
- **Risk:** ถ้ายัง 153 แปลว่าไม่ใช่ vars — ต้องสืบต่อ ไม่ย้อนอย่างอื่นแล้ว

## Impact

- แตะ `playerVars` + `onReady` 1 บรรทัดใน `player.html`

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Revert playerVars]** - Lane A | Can run together: none | Must wait for: none | TDD slice: 9 vars present -> restore block -> `manage.py test`
2. **[Regression test]** - Sequential | Can run together: none | Must wait for: Task 1 | TDD slice: full-set test -> update test -> `manage.py test`

---

### Task 1: Revert playerVars

**Files:**

- Modify: `music/templates/music/player.html` (playerVars block + onReady safePlayMuted line)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_player_full_vars():
    html = self.client.get("/").content.decode()
    assert "'mute': 1" in html and "'playsinline': 1" in html
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (minimal 3 vars today; note existing MinimalPlayerVars test will conflict — update it in Task 2).

- [ ] **Step 3: Implement the minimal code**

Restore exact block: `'autoplay': 1, 'mute': 1, 'controls': 1, 'modestbranding': 1, 'rel': 0, 'playsinline': 1, 'iv_load_policy': 3, 'fs': 1, 'origin': ..., 'enablejsapi': 1`. Remove the added `safePlayMuted()` line in onReady (keep rest of onReady). Keep host nocookie.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: PASS (except MinimalPlayerVars test — fix in Task 2).

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

Full-set markers present.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL until Task 1 merged (plus old minimal test must be updated to full-set expectation).

- [ ] **Step 3: Implement the minimal code**

Update `MinimalPlayerVarsRegressionTests` → full-set expectation (or rename). Only `music/tests.py`.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun. No commit/push.
