# Rotation Continue on Network Error Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** network timeout แล้วลอง key ถัดไปแทน return ทันที (Q32=A)

**Estimated tasks:** 1 | **Estimated time:** ~10 min | **Touches:** API / Tests

## Current Problem / Current Solution

- `youtube_api_search` (`music/views.py:132-145`): `except urllib.error.HTTPError` 403 quota → `continue` ถูกแล้ว แต่ `except Exception` (timeout/URLError — เกิดบ่อยบน Render ฟรี) → `return []` ทันที key2 ไม่เคยถูกใช้ → fallback 3 เพลงไม่ตรงคำทั้งที่ key2 ใช้ได้ (เทสผ่านจากเครื่องแล้ว)

## Proposed Approach

- `except Exception` เปลี่ยน `return []` เป็น `continue` (log ว่า key ไหน network fail) ให้ตก `return []` แค่ตอนหมด loop
- จุดเดียว ไม่แตะอย่างอื่น (ตามกติกาผู้ใช้ + Q32)

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| key1 timeout บน Render | return [] → fallback | ลอง key2 → ได้ผลจริง |
| key1+key2 timeout คู่ | fallback (เท่าเดิม) | fallback (เท่าเดิม) |

## Assumptions & Risks

- **Assumed:** key2 บน Render เป็นค่าใหม่ project ใหม่แล้ว
- **Risk:** ถ้า Render ต่อ google ไม่ได้เลยทั้ง 2 key ยัง fallback — ต้องดู log ต่อ

## Impact

- จุดเดียวใน `youtube_api_search`

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Continue on network error + test]** - Lane A | Can run together: none | Must wait for: none | TDD slice: timeout tries next key -> change return to continue -> `manage.py test`

---

### Task 1: Continue on network error + test

**Files:**

- Modify: `music/views.py:143-145` (generic except)
- Modify: `music/tests.py` (1 regression test)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_network_error_tries_next_key():
    # first key raises URLError/timeout, second key 200 with 1 item -> results has 1 item
    pass
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (returns [] on first timeout today).

- [ ] **Step 3: Implement the minimal code**

In `music/views.py` generic `except Exception` (หลัง HTTPError): `print('YouTube API Error:', exc)` + `continue` แทน `return []` (log index key ด้วย ห้าม log ค่า key). `return []` เหลือแค่หลัง loop หมดทุก key.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Rerun test. No commit/push (รอผู้ใช้สั่ง).
