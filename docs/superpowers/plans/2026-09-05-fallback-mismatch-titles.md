# Fallback Mismatched Titles Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เพลงชื่อผิดหายจากเพลงแนะนำ — ลบ 2 fallback ที่ id ไม่ตรงชื่อออก

**Estimated tasks:** 2 | **Estimated time:** ~15 min | **Touches:** API / Tests

## Current Problem / Current Solution

- ผู้ใช้เห็นเพลงชื่อผิดในเพลงแนะนำ จำไม่ได้ว่าเพลงไหน (Q13=C)
- ที่รู้แน่ชัด 2 ตัวใน `_fallback_static` (`music/views.py`): `9bZkp7q19f0` ตั้งชื่อ `ธาตุทองซาวด์ - YOUNGOHM` แต่ id คือ PSY Gangnam Style, `kJQP7kiw5Fk` ตั้งชื่อ `ลืมไปแล้วว่ายังไง - Silly Fools` แต่ id คือ Despacito — รูป/เพลงไม่ตรงชื่อ
- ชื่อจาก live YouTube API มาจาก YouTube ตรงๆ แก้ไม่ได้ ต้องแก้แค่ fallback

## Proposed Approach

- ลบ 2 entries (`9bZkp7q19f0`, `kJQP7kiw5Fk`) ออกจากทุกสำเนา `_fallback_static` เหลือ 8 entries ที่ id ตรงชื่อชัวร์
- Trade-off: fallback เหลือ 8 — live API ให้ 15 ปกติอยู่แล้ว ไม่กระทบ (ตาม Q11/Q12 เดิม)

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| API ตาย → fallback | มีธาตุทองซาวด์รูป PSY + ลืมไปแล้วฯรูป Despacito | 8 เพลงชื่อตรงรูปทั้งหมด |
| API ปกติ | 15 เพลง live | เท่าเดิม ไม่กระทบ |

## Assumptions & Risks

- **Assumed:** 8 entries ที่เหลือ id ตรงชื่อจริง (ใช้มานาน)
- **Risk:** ถ้าผู้ใช้เห็นชื่อผิดจาก live API (YouTube ตั้งเอง) แก้ไม่ได้ — ต้องขอดูชื่อเพลงนั้นอีกครั้ง

## Impact

- ชื่อผิดที่รู้แน่ชัดหายไป
- ไม่แตะ template/queue/player logic

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Remove 2 mismatched entries]** - Lane A | Can run together: none | Must wait for: none | TDD slice: mismatch ids absent -> delete entries -> `manage.py test`
2. **[Regression test]** - Sequential | Can run together: none | Must wait for: Task 1 | TDD slice: mismatch test -> add test -> `manage.py test`

---

### Task 1: Remove 2 mismatched entries

**Files:**

- Modify: `music/views.py` (ทุกสำเนา `_fallback_static` — hits + ai_recommend ถ้ามี)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_fallback_has_no_mismatched_ids():
    # 9bZkp7q19f0 (PSY) และ kJQP7kiw5Fk (Despacito) ต้องไม่อยู่ใน fallback
    pass
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (ทั้งสอง id ยังอยู่).

- [ ] **Step 3: Implement the minimal code**

ลบ dict entries ของ `9bZkp7q19f0` และ `kJQP7kiw5Fk` ออกจากทุก `_fallback_static` เหลือ 8 entries ไม่แตะ filter/cache/dedup logic.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: PASS.

- [ ] **Step 5: Refactor only after green**

Rerun test.

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

Same as Task 1 Step 1 (lock: 2 ids ไม่อยู่ใน fallback ที่ serve ผ่าน /api/hits/ ตอน mock live ว่าง).

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL until Task 1 merged.

- [ ] **Step 3: Implement the minimal code**

Only add test in `music/tests.py` (no prod code).

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun.
