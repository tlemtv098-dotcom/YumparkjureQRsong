# Clear All Blocked Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สั่งเพลงไหนก็ติดลิขสิทธิ์หาย — ล้าง BlockedVideo ทั้งตารางเหลือ 3 id ตายตัว (Q73=A)

**Estimated tasks:** 2 | **Estimated time:** ~15 min | **Touches:** API / Tests

## Current Problem / Current Solution

- iPad สั่งเพลงไหนก็ขึ้นติดลิขสิทธิ์ทุกเพลง — `BlockedVideo` บน Render สะสมจาก auto-block 153 รัวมาหลายอาทิตย์จน `_is_blocked` จริงเกือบทุกเพลง
- มี `/api/block/clear/` owner-only แล้วแต่ลบแค่ FALLBACK_IDS (8) ไม่พอ

## Proposed Approach

- ขยาย `clear_blocked` (`music/views.py`): ลบทั้งตาราง `BlockedVideo` (เหลือ `BLOCKED_VIDEO_IDS` 3 ตัวตายตัวในโค้ดซึ่งไม่ได้อยู่ DB อยู่แล้ว) ตอบ deleted count — owner-only + POST เหมือนเดิม
- จุดเดียว ไม่แตะ guard/frontend/queue

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| เรียก clear | ลบแค่ 8 fallback (ได้ 0) | ลบทั้งหมด ได้ N |
| สั่งเพลงหลังล้าง | ติดลิขสิทธิ์ทุกเพลง | สั่งได้ปกติ |
| เพลงห้าม embed จริง | — | 153 แล้วโดนบล็อกใหม่เอง |

## Assumptions & Risks

- **Assumed:** สาเหตุคือ DB พิษ (ตาม Q73) — ถ้าไม่ใช่ ล้างแล้วก็ยังติด ต้องสืบต่อ
- **Risk:** เพลงห้าม embed จริงกลับมาให้เลือก → 153 แล้วบล็อกใหม่ (พฤติกรรมเดิมที่ออกแบบไว้)

## Impact

- แตะ `clear_blocked` จุดเดียว + test

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Clear all blocked]** - Lane A | Can run together: none | Must wait for: none | TDD slice: clears all rows -> change filter -> `manage.py test`
2. **[Regression test]** - Sequential | Can run together: none | Must wait for: Task 1 | TDD slice: clear-all test -> add test -> `manage.py test`

---

### Task 1: Clear all blocked

**Files:**

- Modify: `music/views.py` (`clear_blocked`)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_clear_blocked_clears_all():
    # create 3 blocked rows (1 fallback + 2 other) -> owner clear -> 0 rows remain
    pass
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (today keeps non-fallback rows).

- [ ] **Step 3: Implement the minimal code**

In `clear_blocked` only: `BlockedVideo.objects.all().delete()` (BLOCKED_VIDEO_IDS 3 ตัวอยู่ในโค้ดไม่กระทบ) keep owner check + response shape + route.

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

Only update tests in `music/tests.py` (adjust old clear-fallback-only test to clear-all; no prod code).

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun. No commit/push.
