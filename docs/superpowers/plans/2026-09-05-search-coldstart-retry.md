# Search Cold-Start Retry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ค้นหาครั้งแรกหลัง idle ไม่ขึ้น เกิดข้อผิดพลาด — ลองใหม่เอง 1 ครั้ง + ข้อความไทยชัดเจน

**Estimated tasks:** 3 | **Estimated time:** ~30 min | **Touches:** Frontend / Tests

## Current Problem / Current Solution

- ค้นหาขึ้น `เกิดข้อผิดพลาด` (player) / `ค้นหาไม่สำเร็จ` (request) เป็นบางครั้ง เฉพาะครั้งแรกหลังเปิดเว็บทิ้งไว้นาน (Q7=A, Q8=A)
- สาเหตุ: Render free cold start — request แรกห้อย/timeout/connection refused → `catch` โชว์ toast ทันที ไม่ลองซ้ำ
- Abort timeout 8 วิมี guard เงียบแล้ว ไม่ใช่สาเหตุ (ตรวจโค้ดแล้ว)

## Proposed Approach

- ทั้งสองหน้า: `catch` ที่ไม่ใช่ AbortError ให้ retry `fetch /api/search` อีก 1 ครั้งหลัง 800ms ด้วย controller ใหม่ ถ้าสำเร็จ render ปกติ ถ้าล้มเหลวครั้งที่สองค่อย toast
- Player: เปลี่ยน toast ครั้งที่สองเป็น `เชื่อมต่อเซิร์ฟเวอร์ไม่สำเร็จ ลองใหม่อีกครั้ง` (ไทยชัดเจนกว่า `เกิดข้อผิดพลาด`)
- Request: คงข้อความ `ค้นหาไม่สำเร็จ ลองใหม่นะ` เดิม (ไทยอยู่แล้ว)
- Trade-off: request เพิ่ม 1 ครั้งเฉพาะตอนล้มเหลวครั้งแรกเท่านั้น ไม่กระทบเคสปกติ

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| ค้นหาครั้งแรกหลัง idle, server sleep | toast error ทันที | ลองใหม่เอง 1 ครั้ง สำเร็จเงียบ |
| ล้มสองครั้งติด (เน็ตหลุดจริง) | toast ทันทีครั้งแรก | toast ครั้งที่สอง ข้อความชัด |
| ค้นหาปกติ server ตื่น | 1 request | 1 request เท่าเดิม |

## Assumptions & Risks

- **Assumed:** สาเหตุคือ cold start (Q8=A) ไม่ใช่ API key หมด — ถ้า key หมด retry ก็ล้มแล้ว toast ตามเดิม
- **Risk:** retry เพิ่มโหลด server 1 request เฉพาะตอน fail — รับได้
- **Risk:** ถ้า server ดับยาว retry ก็ไม่ช่วย — toast ครั้งที่สองบอกให้ลองใหม่

## Impact

- error บางครั้งหายไปโดยไม่ต้องแตะต้อง backend
- ไม่แตะ queue/player/153 logic

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Player search retry]** - Lane A | Can run together: Task 2 | Must wait for: none | TDD slice: retry + Thai message present -> add retry -> `manage.py test`
2. **[Request search retry]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: retry present, message kept -> add retry -> `manage.py test`
3. **[Regression tests]** - Sequential | Can run together: none | Must wait for: Task 1, Task 2 | TDD slice: retry tests -> add tests -> `manage.py test`

---

### Task 1: Player search retry

**Files:**

- Modify: `music/templates/music/player.html:1031-1075` (`manualSearch` fetch/catch)
- Test: `music/tests.py` (content check only)

**Parallelization:**

- Can run with: `Task 2`
- Must wait for: `none`
- Race risk: `none` (only player.html)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_player_search_retries_once():
    html = self.client.get("/").content.decode()
    assert "manualSearchRetry" in html or html.count("/api/search/") >= 2
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (no retry in manualSearch today).

- [ ] **Step 3: Implement the minimal code**

In `player.html` `manualSearch` only: extract fetch into inner `doFetch(isRetry)`; on `catch` non-AbortError and `!isRetry`, wait 800ms then call once more with fresh AbortController + 8s timeout; on second failure show `เชื่อมต่อเซิร์ฟเวอร์ไม่สำเร็จ ลองใหม่อีกครั้ง`. Keep AbortError silent, keep `manual-loading` hidden on all paths, keep filters/debounce untouched.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: PASS.

- [ ] **Step 5: Refactor only after green**

Rerun test.

---

### Task 2: Request search retry

**Files:**

- Modify: `music/templates/music/request.html:245-287` (`searchSong` fetch/catch)
- Test: `music/tests.py` (content check only)

**Parallelization:**

- Can run with: `Task 1`
- Must wait for: `none`
- Race risk: `none` (only request.html)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_request_search_retries_once():
    html = self.client.get("/request/").content.decode()
    assert "searchRetry" in html or html.count("/api/search/") >= 2
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL.

- [ ] **Step 3: Implement the minimal code**

Same retry pattern as Task 1; keep Thai message `ค้นหาไม่สำเร็จ ลองใหม่นะ` and `#loading` behavior.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: PASS.

- [ ] **Step 5: Refactor only after green**

Rerun test.

---

### Task 3: Regression tests

**Files:**

- Modify: `music/tests.py`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1, Task 2` (shared test file)
- Race risk: `music/tests.py` shared — must run last

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_search_coldstart_retry_and_message():
    # player: retry marker + Thai message; request: retry marker
    pass
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL until Tasks 1-2 merged.

- [ ] **Step 3: Implement the minimal code**

Only add/adjust tests in `music/tests.py`. Assert player contains retry + `เชื่อมต่อเซิร์ฟเวอร์ไม่สำเร็จ`; request contains retry.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun.
