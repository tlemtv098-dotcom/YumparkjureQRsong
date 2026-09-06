# Embed Test No-Origin Section Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** /embed-test/ เพิ่มส่วนที่ 4 ไม่มี origin เทียบว่าตั้งค่านี้คือสาเหตุ 153 (Q105=A)

**Estimated tasks:** 2 | **Estimated time:** ~15 min | **Touches:** Frontend / Tests

## Current Problem / Current Solution

- ลด playerVars เหลือ 3 แล้วยัง 153 บน iPad — เหลือ `origin` ตัวเดียวที่ต่างจากหน้าเปล่า (Q105)

## Proposed Approach

- เติมส่วนที่ 4 ใน `embed_test.html`: `new YT.Player('noorigin-player', {host nocookie, videoId ks7p6DA0dKk, playerVars {'controls':1,'enablejsapi':1}})` (ไม่มี origin) + ปุ่มเล่น + โชว์ error
- วิธีอ่านผล: ส่วน 4 เล่นได้ = origin มีปัญหา / ส่วน 4 ก็ 153 = ไม่ใช่ origin

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| เทส iPad | 3 ส่วน | 4 ส่วน (+noorigin) |

## Assumptions & Risks

- **Assumed:** API ไม่ใส่ origin ยังทำงาน ( less secure แต่เทสได้)
- **Risk:** ไม่มี — หน้าแยก ไม่แตะ flow เดิม

## Impact

- แตะ `embed_test.html` จุดเดียว

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[No-origin section]** - Lane A | Can run together: none | Must wait for: none | TDD slice: marker present -> add section -> `manage.py test`
2. **[Regression test]** - Sequential | Can run together: none | Must wait for: Task 1 | TDD slice: section test -> add test -> `manage.py test`

---

### Task 1: No-origin section

**Files:**

- Modify: `music/templates/music/embed_test.html`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_embed_test_has_noorigin_section():
    html = self.client.get("/embed-test/").content.decode()
    assert "noorigin-player" in html
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (no section 4 today).

- [ ] **Step 3: Implement the minimal code**

In `embed_test.html` only: append section 4 — `<div id="noorigin-player">` + button `noorigin-play-btn` (playVideo only) + `<p id="noorigin-error">` + player config nocookie host, videoId ks7p6DA0dKk, vars controls/enablejsapi (NO origin), onError → noorigin-error.

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
