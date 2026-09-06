# Embed Test API Section Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** /embed-test/ มีส่วน YT.Player API มินิมอลเทียบ iframe เปล่า แยก handshake vs flow (Q93=A)

**Estimated tasks:** 2 | **Estimated time:** ~15 min | **Touches:** Frontend / Tests

## Current Problem / Current Solution

- `/embed-test/` มีแค่ plain iframe (เล่นได้บน iPad) แต่ player จริงใช้ YT.Player API แล้ว 153 — ลด playerVars เหลือ 3 แล้วยัง 153 (Q90 ไม่หาย)
- แยกไม่ได้ว่าเป็นที่ API handshake หรือ flow เรียก (mute/loadVideoById/timing/polling)

## Proposed Approach

- เติมส่วนที่ 2 ใน `embed_test.html`: `YT.Player` เดียวกัน (nocookie host, playerVars `controls/origin/enablejsapi`) + ปุ่ม `โหลดและเล่น` เรียก `loadVideoById('ks7p6DA0dKk')` + `playVideo()` ตรงๆ ใน click handler (user gesture) + แสดง error code ถ้ามี
- วิธีอ่านผลบน iPad: ส่วน API เล่นได้ = handshake ปกติ ปัญหาอยู่ flow เรียกของ player จริง / ส่วน API ก็ 153 = handshake มีปัญหา

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| เทส iPad | มีแค่ iframe เปล่า | มี API มินิมอลเทียบด้วย |

## Assumptions & Risks

- **Assumed:** ปุ่มกด = user gesture ชัดเจน ตัดประเด็น autoplay policy ออก
- **Risk:** ไม่มี — หน้าแยก ไม่แตะ flow เดิม

## Impact

- แตะ `embed_test.html` จุดเดียว

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[API section]** - Lane A | Can run together: none | Must wait for: none | TDD slice: api section present -> add section -> `manage.py test`
2. **[Regression test]** - Sequential | Can run together: none | Must wait for: Task 1 | TDD slice: section test -> add test -> `manage.py test`

---

### Task 1: API section

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
def test_embed_test_has_api_section():
    html = self.client.get("/embed-test/").content.decode()
    assert "loadVideoById" in html
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (no API section today).

- [ ] **Step 3: Implement the minimal code**

In `embed_test.html` only: append section 2 — `<div id="api-player">` + `<script src="https://www.youtube.com/iframe_api">` + `new YT.Player` (nocookie, vars controls/origin/enablejsapi) + button `onclick` → `loadVideoById('ks7p6DA0dKk'); playVideo();` + `<p id="api-error">` showing `onError` code. Keep section 1 (plain iframe) untouched.

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
