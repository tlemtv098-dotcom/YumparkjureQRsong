# Search Buttons Wrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ปุ่มผลค้นหาไม่ทะลุจอแนวตั้ง — จอเล็กปุ่มลงบรรทัดใหม่ จอใหญ่คงเดิม (Q39=A)

**Estimated tasks:** 2 | **Estimated time:** ~20 min | **Touches:** Frontend / Tests

## Current Problem / Current Solution

- แถวผลค้นหา `player.html` (`manual-results`) เป็น `flex items-center gap-2` ปุ่ม `เล่นทันที` + `เล่นทันที (ข้ามคิว)` วางข้างกันตลอด จอเล็ก (iPad แนวตั้ง/โทรศัพท์) ปุ่มล้นขอบถูกตัด (Q39)
- แถว `hit-list` ลายเดียวกัน (`เล่น` + `เล่น (ข้ามคิว)`) ล้นเหมือนกันในรูป

## Proposed Approach

- ทั้งสองแถวใน `player.html` เท่านั้น: การ์ดเป็น `flex-wrap`, กลุ่มปุ่ม `w-full sm:w-auto` + `justify-end` — จอเล็ก (`<sm`) ปุ่มลงบรรทัดใหม่เต็มแถวชิดขวา จอใหญ่ (`sm+`) วางข้างกันเหมือนเดิม
- ไม่แตะสี/ข้อความ/JS/request ฝั่ง request (ปุ่มเดียวไม่ล้น)

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| จอเล็กแนวตั้ง | ปุ่มถูกตัดขอบ | ปุ่มลงบรรทัดใหม่ครบ 2 ปุ่ม |
| จอใหญ่ | 2 ปุ่มข้างกัน | เท่าเดิม |

## Assumptions & Risks

- **Assumed:** breakpoint `sm` (640px) ตรงกับจอที่ล้น — iPad แนวตั้งกว้าง 768 อยู่ใน `sm+`... ถ้ารูปถ่ายจาก panel แคบ (~400px) ต้องใช้ breakpoint ใหญ่กว่า
- **Risk:** ถ้ายังล้นที่ 768 ต้องขยับเป็น `md:` — ระบุไว้ให้ worker วัดจาก panel ไม่ใช่จอ

## Impact

- แตะเฉพาะ class Tailwind ของ 2 แถวใน `player.html`

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Buttons wrap]** - Lane A | Can run together: none | Must wait for: none | TDD slice: wrap classes present -> edit classes -> `manage.py test`
2. **[Regression test]** - Sequential | Can run together: none | Must wait for: Task 1 | TDD slice: wrap test -> add test -> `manage.py test`

---

### Task 1: Buttons wrap

**Files:**

- Modify: `music/templates/music/player.html` (`manualSearch` row template + `renderHitList` row template — class attributes only)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_search_buttons_wrap():
    html = self.client.get("/").content.decode()
    assert "flex-wrap" in html
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (no flex-wrap in row templates today — verify; if present for other reasons, assert on button wrapper `w-full sm:w-auto` instead).

- [ ] **Step 3: Implement the minimal code**

In `player.html` row templates only (manual-results + hit-list):
- card div: add `flex-wrap` (keep `flex items-center gap-2`)
- wrap the 2 buttons in `<div class="flex gap-1 w-full sm:w-auto justify-end flex-shrink-0">...</div>` (buttons keep own classes/text/onclick)
- title div keeps `flex-1 min-w-0` so it shrinks; add `basis-full sm:basis-auto`? No — keep simple: card wraps, text div `flex-1 min-w-0`, button group `w-full sm:w-auto`
- NOTE: panel แคบ (~400px) แม้บน iPad แนวตั้ง — ถ้า `sm:` ยังล้นให้ใช้ `md:` แทน แล้วระบุในผล

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

Same as Task 1 Step 1 (lock wrap classes in player rows).

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL until Task 1 merged.

- [ ] **Step 3: Implement the minimal code**

Only add test in `music/tests.py` (no prod code).

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun. No commit/push.
