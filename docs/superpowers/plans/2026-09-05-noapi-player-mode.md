# No-API Player Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** หน้า player เล่นได้บน iPad ที่ JS API ใช้ไม่ได้ โดยสลับ iframe เปล่าต่อเพลง + จับเวลาจบเพลง (Q99 custom = ใช้หน้า player, Q100 upcoming)

**Estimated tasks:** 4 | **Estimated time:** ~90 min | **Touches:** API / Frontend / Tests

## Current Problem / Current Solution

- เทส 3 ส่วนบน iPad Gen 9: iframe เปล่าเล่นได้, YT.Player 2 แบบ (blank+load, prefilled) 153 หมด → JS API ใช้บน iPad นี้ไม่ได้เลย (Q93-Q98)
- player หลักต้องใช้ JS API (ended event, mute/play) เลยเล่นไม่ได้บน iPad นี้

## Proposed Approach

- โหมด `?noapi=1` (หรือปุ่มสลับใน player): ไม่สร้าง `YT.Player` เลย ใช้ plain `<iframe src="nocookie/embed/{id}?autoplay=1&rel=0">` สลับทีละเพลง
- จบเพลงจับด้วย timer: backend endpoint ใหม่ `GET /api/duration/?id=` ใช้ YouTube `videos.list(contentDetails)` (1 unit/เพลง, cache 24 ชม.) ส่ง `duration_sec` มาให้ frontend `setTimeout` เล่นเพลงถัดไป
- ควบคุมเสียง/หยุด: ใช้ native controls ใน iframe (ผู้ใช้กดเอง) + ปุ่มข้ามเพลงของเว็บ (เปลี่ยน src)
- คงโหมด API เดิมเป็นหลัก โหมด noapi ใช้เฉพาะ iPad ที่มีปัญหา (query param ไม่กระทบผู้ใช้อื่น)

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| iPad นี้เปิด player | 153 ทุกเพลง เล่นไม่ได้ | `?noapi=1` สลับ iframe เล่นได้ทีละเพลง |
| เครื่องอื่น | API mode | เท่าเดิม (default ไม่เปลี่ยน) |

## Assumptions & Risks

- **Assumed:** plain iframe เล่นได้บน iPad นี้จริง (ส่วนที่ 1 พิสูจน์แล้ว)
- **Assumed:** duration จาก `videos.list` ถูกต้องพอสำหรับ timer (คลาดเคลื่อนนิดหน่อย + โฆษณา รับได้)
- **Risk:** ไม่มี ended event จริง — ถ้า user กดหยุดใน iframe เอง timer ยังเดิน ต้องกดข้ามเอง
- **Risk:** โฆษณา YouTube ทำให้เวลาคลาด — รับได้ (ข้ามเองได้)

## Impact

- เพิ่ม 1 endpoint + 1 โหมดใน `player.html` (แยก code path ชัดเจน) — ไม่แตะ flow API เดิม

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Duration endpoint]** - Lane A | Can run together: Task 2 | Must wait for: none | TDD slice: duration JSON -> add endpoint -> `manage.py test`
2. **[No-API frontend mode]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: noapi markers present -> add mode -> `manage.py test`
3. **[Regression tests]** - Sequential | Can run together: none | Must wait for: Task 1, Task 2 | TDD slice: mode tests -> add tests -> `manage.py test`
4. **[Push]** - Manual | Can run together: none | Must wait for: Task 3 | TDD slice: n/a -> commit+push -> Live verify

---

### Task 1: Duration endpoint

**Files:**

- Modify: `music/views.py` (add `video_duration`), `music/urls.py` (add route)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 2`
- Must wait for: `none`
- Race risk: `none` (backend vs frontend files)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_duration_endpoint():
    res = self.client.get("/api/duration/?id=ks7p6DA0dKk")
    assert res.status_code == 200
    assert "duration_sec" in res.json()
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (404, no route).

- [ ] **Step 3: Implement the minimal code**

In `music/views.py`: `def video_duration(request):` GET `id` → validate 11-char → cache `dur:{id}` 24h → call YouTube `videos.list(part=contentDetails)` ด้วย key แรกที่ใช้ได้ (reuse `_youtube_api_keys`) → parse ISO8601 duration → `{"duration_sec": n}` (default 180 ถ้า fail). `music/urls.py`: `path('api/duration/', ...)`.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: PASS.

- [ ] **Step 5: Refactor only after green**

Rerun test. No commit/push.

---

### Task 2: No-API frontend mode

**Files:**

- Modify: `music/templates/music/player.html` (noapi branch only)
- Test: `music/tests.py` (content check only)

**Parallelization:**

- Can run with: `Task 1`
- Must wait for: `none`
- Race risk: `none` (template vs backend)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_player_has_noapi_mode():
    html = self.client.get("/").content.decode()
    assert "noapi" in html
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL.

- [ ] **Step 3: Implement the minimal code**

In `player.html` only: ถ้า URL มี `?noapi=1` → ข้าม `new YT.Player` ทั้งหมด ใช้ `playNextNoApi()`: ตั้ง `#player` innerHTML เป็น plain iframe `nocookie/embed/{id}?autoplay=1&rel=0` → fetch `/api/duration/?id=` → `setTimeout` (duration+5s) เรียกเพลงถัดไปผ่าน flow คิวเดิม (`skipSong` + render). ปุ่มข้าม/คิว/ค้นหาใช้ของเดิม. โหมดปกติ (ไม่มี param) ไม่เปลี่ยนแม้แต่บรรทัดเดียวใน flow เดิม.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: PASS.

- [ ] **Step 5: Refactor only after green**

Rerun test. No commit/push.

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

Task 1 + Task 2 Step 1 combined.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL until Tasks 1-2 merged.

- [ ] **Step 3: Implement the minimal code**

Only add tests in `music/tests.py` (no prod code).

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun. No commit/push.
