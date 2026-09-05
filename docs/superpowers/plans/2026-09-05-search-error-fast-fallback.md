# Search Error Fast Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ค้นหาไม่ขึ้น error ทั้งสองหน้าทุกคำ — abort request เก่า + timeout 8 วิ + API ก่อน fallback ทันที

**Estimated tasks:** 4 | **Estimated time:** ~40 min | **Touches:** API / Frontend / Tests

## Current Problem / Current Solution

- ค้นหาขึ้น error ทั้ง player (`เกิดข้อผิดพลาด`) และ request (`ค้นหาไม่สำเร็จ`) ทุกคำ (Q1=C, Q2=A)
- `search_youtube` ลอง API (8s) → yt-dlp fallback (Render 429/bot, ช้า) → `_is_embeddable` ทีละวิดีโอ (3s/ตัว) รวมเกิน 30 วิ → frontend `fetch` ห้อยแล้ว `catch`
- Frontend `fetch("/api/search/")` ไม่มี AbortController/timeout, player ไม่เช็ค `res.ok` → request เก่าค้างซ้อน

## Proposed Approach

- Backend: `search_song` fast path — `youtube_api_search` ว่างคืน fallback static ทันที ไม่เรียก yt-dlp/`_is_embeddable` ใน path ค้นหา (เก็บ deep check ไว้แค่ `hits`)
- Frontend ทั้งสองหน้า: AbortController ยกเลิกตัวเก่าเมื่อพิมพ์ใหม่ + timeout 8 วิ + เช็ค `res.ok` + ซ่อน loading ทุก path
- Trade-off: ยอมได้เพลงน้อย (API 5 + fallback 3) ดีกว่าค้าง — ตาม Q3 option A ที่อนุมัติ

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| พิมพ์ "ข้างกัน" รัวๆ | request เก่าค้างซ้อน ค้าง loading/error | abort ตัวเก่า เหลือตัวล่าสุด + timeout 8 วิ |
| API key หมด/quota | รอ yt-dlp 10-30 วิแล้ว error | คืน fallback 3 เพลงทันที (<1 วิ) |
| /api/search 500/timeout | toast error ค้าง | toast + ซ่อน loading + โชว์ fallback |

## Assumptions & Risks

- **Assumed:** `YOUTUBE_API_KEY` มีบน Render — API path เร็วพอ
- **Assumed:** ยอมรับ fallback 3 เพลงเมื่อ API ว่าง (ตาม Q3)
- **Risk:** ถ้า API key หมด จะได้แค่ fallback 3 เพลงซ้ำๆ — รับได้ดีกว่า error
- **Risk:** ตัด `_is_embeddable` ออกจาก search อาจหลุดเพลง 153 มาบ้าง — player soft-skip จัดการต่อ

## Impact

- ค้นหาไม่ error ทั้งสองหน้า
- ผลลัพธ์เร็ว <8 วิเสมอ
- ไม่แตะ queue/player/153 logic

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Backend search fast]** - Lane A | Can run together: Task 2, Task 3 | Must wait for: none | TDD slice: slow API returns fallback <5s -> remove yt-dlp/embed from search path -> `manage.py test`
2. **[Player manualSearch abort]** - Lane B | Can run together: Task 1, Task 3 | Must wait for: none | TDD slice: abort + timeout hides loading -> add AbortController -> `manage.py test`
3. **[Request searchSong abort]** - Lane C | Can run together: Task 1, Task 2 | Must wait for: none | TDD slice: abort + timeout hides loading -> add AbortController -> `manage.py test`
4. **[Regression tests]** - Sequential | Can run together: none | Must wait for: Task 1, Task 2, Task 3 | TDD slice: search fast + abort tests -> add tests -> `manage.py test`

---

### Task 1: Backend search fast

**Files:**

- Modify: `music/views.py:145-250` (`search_youtube`, `search_song`)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 2`, `Task 3`
- Must wait for: `none`
- Race risk: `none` (only views.py; tests updated in Task 4)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code. This task must follow RED -> GREEN -> REFACTOR.

- [ ] **Step 1: Write the failing test**

```python
def test_search_returns_fast_when_api_empty():
    with mock.patch("music.views.youtube_api_search", return_value=[]):
        start = time.time()
        res = self.client.get("/api/search/?q=ข้างกัน")
        assert res.status_code == 200
        assert time.time() - start < 5
        assert isinstance(res.json()["results"], list)
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected result: FAIL because current `search_youtube` calls yt-dlp + `_is_embeddable` (slow, Render 429) before fallback.

- [ ] **Step 3: Implement the minimal code**

In `music/views.py` only:
- `search_youtube`: API path returns `api_results[:max_results]` directly (already); when `api_results` empty, return `[]` immediately — do NOT call yt-dlp/`_is_embeddable` in search path (keep those helpers for `hits` only).
- `search_song`: when `results` empty, return filtered static fallback (5 entries) immediately as today, but ensure the fallback filter cannot empty it silently — if filtered empty, return `fallback[:3]` (keep blocked filter).
- Keep `videoCategoryId=10`, `videoEmbeddable=true`, 8s timeout untouched.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected result: PASS.

- [ ] **Step 5: Refactor only after green**

Keep behavior unchanged, rerun test.

---

### Task 2: Player manualSearch abort

**Files:**

- Modify: `music/templates/music/player.html:1024-1067` (`manualSearch`, timers)
- Test: `music/tests.py` (content check only)

**Parallelization:**

- Can run with: `Task 1`, `Task 3`
- Must wait for: `none`
- Race risk: `none` (only player.html)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_player_search_has_abort():
    res = self.client.get("/")
    html = res.content.decode()
    assert "AbortController" in html
    assert "manual-loading" in html
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (no AbortController in player.html today).

- [ ] **Step 3: Implement the minimal code**

In `player.html` only:
- Add `let manualSearchAbort = null;` near `manualSearchTimer`.
- In `manualSearch()`: abort previous controller, create new one, pass `signal` to `fetch`, add 8000ms timeout abort.
- Check `res.ok` before `res.json()`; on `!ok` throw to catch.
- Ensure `manual-loading` hidden in success AND catch AND abort paths; on abort, silently return (no toast).
- Keep `blockedVideoIds`, `isAlbumLike`, `isAI`, `escapeHtml`, debounce untouched.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: PASS.

- [ ] **Step 5: Refactor only after green**

Rerun test.

---

### Task 3: Request searchSong abort

**Files:**

- Modify: `music/templates/music/request.html:245-281` (`searchSong`)
- Test: `music/tests.py` (content check only)

**Parallelization:**

- Can run with: `Task 1`, `Task 2`
- Must wait for: `none`
- Race risk: `none` (only request.html)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_request_search_has_abort():
    res = self.client.get("/request/")
    html = res.content.decode()
    assert "AbortController" in html
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (no AbortController in request.html today).

- [ ] **Step 3: Implement the minimal code**

In `request.html` only:
- Add `let searchAbort = null;` near `searchTimer`.
- Same abort + 8s timeout + `res.ok` check + hide `#loading` on all paths as Task 2.
- Keep `filterBlockedSongs`, `escapeHtml`, debounce untouched.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: PASS.

- [ ] **Step 5: Refactor only after green**

Rerun test.

---

### Task 4: Regression tests

**Files:**

- Modify: `music/tests.py`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1, Task 2, Task 3` (touches shared test file + verifies all lanes)
- Race risk: `music/tests.py` shared — must run last

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_search_fast_fallback_and_abort():
    # backend: mocked empty API -> fallback list, fast
    # frontend: both templates contain AbortController + loading ids
    pass
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL until Tasks 1-3 merged.

- [ ] **Step 3: Implement the minimal code**

Only add/adjust tests in `music/tests.py` (no prod code). Assert: search with mocked empty API returns list fast; `/` contains `AbortController` + `manual-loading`; `/request/` contains `AbortController` + `loading`.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `venv\Scripts\python.exe manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun.
