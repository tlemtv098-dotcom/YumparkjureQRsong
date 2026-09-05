# Search Fallback Pool Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ค้นหาตอน API ใช้ไม่ได้แล้วได้เพลงตรงคำค้นบ่อยขึ้น — ขยาย fallback 5 → 15 เพลงจริงหลายแนว

**Estimated tasks:** 2 | **Estimated time:** ~30 min | **Touches:** API / Tests

## Current Problem / Current Solution

- Live บน Render ต่อ googleapis ไม่ได้ทั้ง 2 key (Live ใหม่สุดแล้วยัง fallback — Q34=B, Q35=A) ค้นหาเลยตก fallback 5 เพลงเดิมทุกคำที่ไม่ตรง substring → ผู้ใช้เห็น "เพลงไรไม่รู้ 3 เพลง"
- `search_song` fallback (`music/views.py:185-191`) มีแค่ 5 เพลง (ข้างกัน/ถ้าเธอ/แฟนเก่าคนโปรด/แค่เธอ/รักแรกพบ) คำค้นอื่นไม่ตรงเลยได้ `fallback[:3]` เดิมๆ

## Proposed Approach

- ขยาย `search_song` fallback เป็น 15 เพลงจริงหลายแนว (รัก/อกหัก/สนุก/ลูกทุ่ง/ป๊อป) โดยเอา id จริงที่ verify แล้ว: 8 ตัวเดิม + 5 ตัวจากผล API จริงคำว่า `เพลงรัก` (OYPiXBIgvJ8, P5sHZRicEXg, vMUeFBHwzSI, FFhL0UcYVTc, g1UQm2IGhLA — ได้จาก API ตอบจริง) + อีก ~2 คำค้นผ่าน API (กิน quota ~200 units แจ้งผู้ใช้แล้ว)
- ทุก id ต้อง verify `hqdefault` 200 ผ่าน curl ก่อนใส่ (ฟรี ไม่กิน quota)
- Trade-off: เสีย quota ~200-300 units ครั้งเดียว แลก fallback ตรงคำค้นบ่อยขึ้นถาวร

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| ค้นหา "เพลงรัก" ตอน API ดับ | ได้ ข้างกัน/ถ้าเธอ/แฟนเก่าฯ ไม่ตรง | ได้เพลงรัก Three Man Down ตรงคำ |
| ค้นหาคำทั่วไป | ตรงบ้างไม่ตรงบ้าง (5 เพลง) | ตรงบ่อยขึ้น (15 เพลงหลายแนว) |
| API ปกติ | ผลจริง 5 เพลง | เท่าเดิม ไม่กระทบ |

## Assumptions & Risks

- **Assumed:** id จาก API response จริง + thumb 200 = ใช้ได้ (verify ซ้ำด้วย curl)
- **Risk:** เสีย quota ~200-300 units ครั้งเดียว — แจ้งผู้ใช้แล้ว (Q35)
- **Risk:** fallback ยังไม่ครอบคลุมทุกคำค้น — ดีขึ้นแต่ไม่ 100%

## Impact

- แตะ `search_song` fallback อย่างเดียว ไม่แตะ live path/hits/queue

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Expand fallback to 15 verified]** - Lane A | Can run together: none | Must wait for: none | TDD slice: fallback count + thumbs valid -> add entries -> `manage.py test`
2. **[Regression test]** - Sequential | Can run together: none | Must wait for: Task 1 | TDD slice: fallback relevance test -> add test -> `manage.py test`

---

### Task 1: Expand fallback to 15 verified

**Files:**

- Modify: `music/views.py:185-191` (`search_song` fallback list)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_search_fallback_pool_size():
    # fallback list in search_song has >= 15 entries (count via mocked empty API + nonsense query, assert len >= 10 after filters)
    pass
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (currently 5 → nonsense query returns 3).

- [ ] **Step 3: Implement the minimal code**

In `music/views.py` `search_song` fallback only:
- เก็บ 5 ตัวเดิม + เพิ่ม 10 ตัว: 5 ตัวจากผล API `เพลงรัก` (OYPiXBIgvJ8 เพลงรัก-Three Man Down, P5sHZRicEXg, vMUeFBHwzSI, FFhL0UcYVTc, g1UQm2IGhLA — title/channel ตาม API response ตรงๆ) + อีก ~5 ตัวจาก API queries `เพลงอกหัก`, `เพลงลูกทุ่ง` (ค้นผ่าน API จริงครั้งละ 100 units รวม ~200 — ใช้ key2)
- ทุก id verify `https://i.ytimg.com/vi/{id}/hqdefault.jpg` 200 ผ่าน curl ก่อนใส่ (ไม่กิน quota)
- thumbnail ใช้ `https://i.ytimg.com/vi/{id}/hqdefault.jpg` ทุกตัว title/channel ตาม API ตรงๆ ห้ามแต่ง
- ไม่แตะ filter logic, live path, hits fallback

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

Same as Task 1 Step 1 + assert ค้นหา `เพลงรัก` ตอน mock API ว่างได้ผลที่มี `รัก` ใน title (relevance).

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL until Task 1 merged.

- [ ] **Step 3: Implement the minimal code**

Only add tests in `music/tests.py` (no prod code).

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun. No commit/push.
