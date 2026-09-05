# Fallback Prune Verified IDs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** รูปขาวในเพลงแนะนำหาย — ตัด fallback เหลือ 10 id จริงที่รูปโหลดชัวร์

**Estimated tasks:** 2 | **Estimated time:** ~20 min | **Touches:** API / Tests

## Current Problem / Current Solution

- hits `เพลงแนะนำ` บางรูปขาว (Q10=A) เพราะ `_fallback_static` ใน `music/views.py:285-311` มี 25 entries แต่ 15 ตัวหลัง (บรรทัด 296-310: `OPf0YbXqDm0`, `09R8_2nJtjg` 10 ตัวอักษรใช้ไม่ได้, `2Vv-BfVoq4g` 10 ตัวอักษรใช้ไม่ได้, `QH2-TGUlwu4`, `JGwWNGJdvx8`, `dT6d1y9R8X2`, `e8F2kL9m3Qp`, `f4J7hN2b5Vc`, `g6K3pX8q1Wz`, `h9L2vC5n8Bm`, `j2M5bN8c1Xk`, `k5P8qW2e6Rt`, `m3R8sK1p5XQ`, `n9V2wQ4t6Yz`, `p4L6jH2k8Mn`) เป็น id สมมติ/สั้นผิด รูป `hqdefault` 404 แล้ว `onerror` โชว์โลโก้พื้นขาวเลยดูขาว
- `onerror` fallback มีครบทั้งสองหน้าแล้ว ไม่ต้องแตะ template

## Proposed Approach

- ตัด `_fallback_static` เหลือ 10 entries บรรทัด 286-295 (`ks7p6DA0dKk`, `zwvv71slEYc`, `L1k0wkQ6uww`, `yEbv0QiI1Ns`, `s-MZid-59Hc`, `rc7KnQAh_1I`, `I9ZIq7ynvdU`, `9bZkp7q19f0`, `Bk4O_3WF8II`, `kJQP7kiw5Fk`) ลบบรรทัด 296-310 ทั้งหมด
- ทำกับทุกสำเนา `_fallback_static` ใน `views.py` (hits + ai_recommend ถ้ามี) ให้ตรงกัน
- Trade-off: fallback เหลือ 10 แทน 25 — live API ให้ 15 ปกติอยู่แล้ว fallback แทบไม่ถูกใช้ (ตาม Q11 ที่อนุมัติ)

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| API ตาย → fallback 25 ตัว | 15 ตัวรูป 404 → โลโก้ขาว | 10 ตัวรูปโหลดครบทุกรูป |
| API ปกติ | 15 เพลง live | เท่าเดิม ไม่กระทบ |

## Assumptions & Risks

- **Assumed:** 10 id ที่เหลือรูปโหลดจริง (ใช้มานานตั้งแต่ fallback 5 ตัวแรก + `Bk4O_3WF8II` ที่แก้แล้ว)
- **Risk:** `9bZkp7q19f0` รูปโหลดแต่เป็นปก PSY ไม่ตรงชื่อธาตุทองซาวด์ — เหลือไว้เพราะไม่ขาว รอ id จริง YOUNGOHM ภายหลัง
- **Risk:** pad `len(dedup) < 15` จาก fallback 10 ตัวไม่เต็ม 15 เมื่อ live ว่าง — รับได้เพราะ live ปกติให้ครบ

## Impact

- รูปขาวใน hits หาย
- ไม่แตะ template/queue/player logic

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Prune fallback to 10 verified]** - Lane A | Can run together: none | Must wait for: none | TDD slice: fallback all thumbs valid -> delete 15 fake entries -> `manage.py test`
2. **[Regression test]** - Sequential | Can run together: none | Must wait for: Task 1 | TDD slice: fallback ids valid test -> add test -> `manage.py test`

---

### Task 1: Prune fallback to 10 verified

**Files:**

- Modify: `music/views.py:285-311` (`_fallback_static` hits) + สำเนาอื่นของ `_fallback_static` ถ้ามี (ai_recommend)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none` (views.py เดียว  микроорганизмов — sequential to avoid races)
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_fallback_thumbs_are_valid_ids():
    import re
    from music.views import _fallback_static if hasattr else None
```

(ปรับตามโครงจริง: import fallback list แล้ว assert ทุก id ตรง `^[A-Za-z0-9_-]{11}$` และ thumbnail ตรง id)

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (มี `09R8_2nJtjg`, `2Vv-BfVoq4g` แค่ 10 ตัวอักษร + id สมมติ)

- [ ] **Step 3: Implement the minimal code**

ลบ entries บรรทัด 296-310 (15 ตัว) เหลือ 10 ตัวบรรทัด 286-295 ทำทุกสำเนา `_fallback_static` ให้ตรงกัน ไม่แตะ logic filter/cache/dedup

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

Same as Task 1 Step 1 (lock: ทุก fallback id 11 ตัวอักษร + thumbnail ตรง id).

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL until Task 1 merged.

- [ ] **Step 3: Implement the minimal code**

Only add test in `music/tests.py` (no prod code).

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun.
