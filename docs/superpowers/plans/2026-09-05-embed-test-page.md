# Embed Test Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** หน้า /embed-test/ วิดีโอเดียวไม่มีโค้ดซับซ้อน แยกให้ได้ว่า 153 มาจากโค้ดหรือสิ่งแวดล้อม (Q87=A)

**Estimated tasks:** 2 | **Estimated time:** ~15 min | **Touches:** API / Tests

## Current Problem / Current Solution

- iPad 153 ทุกเพลง คอมเล่นได้ (Q53=A, Q86=B) — โค้ดฝั่งเว็บตรวจหมดแล้ว (breaker live, DB สะอาด, embed 200) แต่แยกไม่ได้ว่าเป็นที่ player config เราหรือสิ่งแวดล้อม iPad
- ต้องการ bare iframe เปล่าๆ เทียบกับ player จริง

## Proposed Approach

- เพิ่ม `GET /embed-test/` render template เปล่าๆ: plain `<iframe src="https://www.youtube-nocookie.com/embed/ks7p6DA0dKk">` (ข้างกัน — เล่นได้ชัวร์ทุกที่) + ปุ่มเปิด/ปิด + แสดงผล ไม่ใช้ IFrame API ไม่ใช้ JS ซับซ้อน ไม่ใช้ overlay/polling
- วิธีอ่านผลบน iPad: หน้านี้เล่นได้ + หน้าหลัก 153 = player config เราผิด → รื้อ config; หน้านี้ก็ 153 = สิ่งแวดล้อม (เน็ต/เครื่อง) → หยุดแก้โค้ด

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| เทส iPad | เดา | หน้าเปล่าเล่นได้/ไม่ได้ = คำตอบชัด |

## Assumptions & Risks

- **Assumed:** `ks7p6DA0dKk` embed ได้ทุกที่ (oEmbed 200 + คอมเล่นได้)
- **Risk:** ไม่มี — หน้าแยก ไม่แตะ flow เดิม

## Impact

- เพิ่ม 1 view + 1 route + 1 template + 1 test — ไม่แตะของเดิม

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Embed test page]** - Lane A | Can run together: none | Must wait for: none | TDD slice: 200 + iframe present -> add view/route/template -> `manage.py test`
2. **[Regression test]** - Sequential | Can run together: none | Must wait for: Task 1 | TDD slice: route test -> add test -> `manage.py test`

---

### Task 1: Embed test page

**Files:**

- Create: `music/templates/music/embed_test.html`
- Modify: `music/views.py` (add `embed_test` view), `music/urls.py` (add route)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_embed_test_page():
    res = self.client.get('/embed-test/')
    assert res.status_code == 200
    assert 'youtube-nocookie.com/embed/ks7p6DA0dKk' in res.content.decode()
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (404, no route).

- [ ] **Step 3: Implement the minimal code**

Add view (plain render, no context needed), route `path('embed-test/', ...)`, template: minimal HTML + `<iframe width="100%" height="360" src="https://www.youtube-nocookie.com/embed/ks7p6DA0dKk" allow="autoplay; encrypted-media; fullscreen" allowfullscreen>` + heading. No IFrame API, no JS (except none), no overlay.

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
