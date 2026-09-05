# YouTube Multi-Key Rotation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ค้นหาไม่ fallback มั่วเมื่อ key หลัก quota หมด — วนใช้ key สำรองอัตโนมัติ

**Estimated tasks:** 2 | **Estimated time:** ~25 min | **Touches:** API / Tests

## Current Problem / Current Solution

- `youtube_api_search` อ่าน key เดียว (`YOUTUBE_API_KEY` หรือ `key`) ถ้า quota หมด (403 quotaExceeded) คืน `[]` ทันที → search ตกไป fallback 3 เพลงไม่ตรงคำ (Q19)
- Google Cloud โชว์ Errors 77% ที่ 500 requests — search กิน 100 units/ครั้ง โควต้า 10,000/วันหมดใน ~100 ครั้ง (Q20)
- ผู้ใช้มี key สำรองแล้ว (Q20=C) ส่งมาทางแชท — ห้าม commit ลง git เด็ดขาด ใช้ env เท่านั้น

## Proposed Approach

- อ่าน keys หลายตัวจาก env: `YOUTUBE_API_KEYS` (คั่นจุลภาค) + `YOUTUBE_API_KEY` + `key` + `YOUTUBE_API_KEY_2` รวมเป็น list ตามลำดับ
- `youtube_api_search` ลอง key ทีละตัว ถ้าเจอ 403 quotaExceeded/rateLimitExceeded ให้ลองตัวถัดไป ถ้า error อื่น (400/key invalid) หยุดทันที
- Key ไม่ถูกเขียนในโค้ด/test/log — test ใช้ key ปลอมเท่านั้น
- Trade-off: ได้ quota 2 เท่า (~200 ค้นหา/วัน) ไม่ใช่ไม่จำกัด — ควรทำประหยัด quota (Q20=A) ต่อภายหลัง

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| key หลัก quota หมด | fallback 3 เพลงไม่ตรงคำ | ลอง key สำรอง ได้ผลจริง |
| key เดียว invalid | `[]` → fallback | เท่าเดิม หยุดทันทีไม่วนมั่ว |
| key ใน git | ไม่มี (ดีอยู่แล้ว) | ยังไม่มี — env อย่างเดียว |

## Assumptions & Risks

- **Assumed:** ผู้ใช้ตั้ง `YOUTUBE_API_KEYS` (หรือ `YOUTUBE_API_KEY_2`) บน Render เอง — โค้ดอย่างเดียวไม่พอ
- **Assumed:** key สำรองยังไม่หมด quota และไม่ถูก restrict
- **Risk:** key ที่ส่งมาทางแชทหลุดใน log ถ้า print error รวม key — ห้าม log key เด็ดขาด
- **Risk:** ถ้าสอง key หมดพร้อมกัน กลับไป fallback เหมือนเดิม

## Impact

- ค้นหาตรงคำนานขึ้น 2 เท่าก่อนตก fallback
- ไม่แตะ frontend/queue/player logic

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Multi-key rotation]** - Lane A | Can run together: none | Must wait for: none | TDD slice: quota fail tries next key -> loop keys -> `manage.py test`
2. **[Regression tests]** - Sequential | Can run together: none | Must wait for: Task 1 | TDD slice: rotation tests -> add tests -> `manage.py test`

---

### Task 1: Multi-key rotation

**Files:**

- Modify: `music/views.py:91-142` (`youtube_api_search`)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_api_key_rotation_on_quota():
    # mock urlopen: first key 403 quotaExceeded, second key 200 with 1 item
    # assert results has 1 item (used second key)
    pass
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (current code returns [] on first 403).

- [ ] **Step 3: Implement the minimal code**

In `music/views.py` only:
- Add helper `def _youtube_api_keys():` returning ordered unique non-empty list from `YOUTUBE_API_KEYS` (split `,`), `YOUTUBE_API_KEY`, `key`, `YOUTUBE_API_KEY_2`.
- `youtube_api_search`: loop keys; on HTTP 403 with body containing `quotaExceeded`/`rateLimitExceeded`/`quota` continue to next key; on other HTTP errors return []; on success parse as today. Never log key values (log only key index).
- Keep params (`videoCategoryId=10`, `videoEmbeddable=true`, timeout 8s), filters (`_is_blocked`, `_is_album_title`, `_is_ai_title`, `_is_non_music`), 11-char check untouched.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: PASS.

- [ ] **Step 5: Refactor only after green**

Rerun test.

---

### Task 2: Regression tests

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

Same as Task 1 Step 1 + test single invalid key returns [] without looping forever + test no real key strings in repo (scan views.py for `AIza`).

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL until Task 1 merged.

- [ ] **Step 3: Implement the minimal code**

Only add tests in `music/tests.py` (no prod code). Use fake keys (`TESTKEY1`, `TESTKEY2`), never real keys.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun.
