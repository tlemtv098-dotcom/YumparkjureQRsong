# Queue Edit, Search Duplicate, Auto Bug Fix and Full Verification Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ทำคิวเลือก/เลื่อนได้ (ปุ่มเล่นถัดไป), แก้ค้นหาซ้ำเหลืออันเดียวเปลี่ยนข้อความ, แก้ออโต้ปิดแล้วยังสุ่มต่อ, ตรวจโครงสร้างทั้งหมด

**Estimated tasks:** 4 | **Estimated time:** ~60 min | **Touches:** Frontend (player, request) / Backend (views) / Tests

## Current Problem / Current Solution

- คิวหน้า player/request ยังดูได้อย่างเดียว ไม่มีปุ่มเลื่อนท้ายขึ้นไปเล่นเลย ต้องลบแล้วขอใหม่
- หน้า request ตอนค้นหาโชว์ "กำลังค้นหา" 2 ที่: `#loading` + `results.innerHTML = 'กำลังค้นหา...'` ซ้ำ
- ปุ่ม `ออโต้: เปิด/ปิด` บางครั้งปิดแล้วยังสุ่มต่อ เพราะ `playRandomHit` ถูกเรียกจาก `fetchQueue`/`onReady` แม้ `autoRandomEnabled==false` หรือ `setTimeout` ค้าง
- ไม่มี verification รวมว่าโครงสร้างหลังแก้ทั้งหมดยัง OK

## Proposed Approach

- **Queue edit:** เพิ่มปุ่ม `⬆️ เลื่อนขึ้น` + `▶️ เล่นถัดไป` ข้างแต่ละรายการใน `renderQueue` (player.html) และ `my-songs-list` (request.html) กดแล้วเรียก API ใหม่ `/api/queue/move/` หรือใช้ `/api/add-front/` + ลบตัวเดิม เพื่อย้ายท้ายขึ้นบนสุด/เลื่อนขึ้น 1 ตำแหน่ง ไม่ทำ drag
- **Search duplicate:** ลบ `results.innerHTML = 'กำลังค้นหา...'` ใน `searchSong` เหลือแค่ `loading` (`#loading`) และเปลี่ยนข้อความ `#loading` เป็น `กำลังค้นหาโปรดรอสักครู่`
- **Auto bug:** ใน `player.html` `playRandomHit` เพิ่ม guard `if (!autoRandomEnabled) return` ทุกทางเข้า, `fetchQueue` `onReady` `setTimeout` ตรวจ `autoRandomEnabled` ก่อนเรียก `playRandomHit`, `toggleAutoRandom` เมื่อปิดต้อง `clearTimeout` ที่ค้าง
- **Verification:** เพิ่ม `python manage.py test` + `python manage.py check` + `npm run build` (ถ้ามี) + checklist `docs/superpowers/checklists/full-verification.md`

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| คิวมี 5 เพลงอยากให้ท้ายเล่นเลย | ทำไม่ได้ | กด ▶️ เล่นถัดไป → ย้ายขึ้น #2 เล่นต่อจากเพลงปัจจุบัน |
| ค้นหา "เพลง" | เห็น กำลังค้นหา 2 อัน | เห็น กำลังค้นหาโปรดรอสักครู่ อันเดียว |
| กด ออโต้: ปิด | ยังสุ่มต่อ | หยุดสุ่มทันที ไม่เรียก playRandomHit อีก |
| โครงสร้างรวม | ไม่ได้ตรวจ | `manage.py test` 50+ OK, check OK |

## Assumptions & Risks

- **Assumed:** ใช้ปุ่มเลื่อนแทน drag พอ ไม่ต้องทำ drag & drop
- **Assumed:** API ย้ายคิวใช้ `POST /api/queue/move/` ใหม่ หรือ reuse `/api/add-front/` + delete
- **Risk:** เพิ่มปุ่มใน queue ทำให้ `renderQueue` ต้องส่ง `X-CSRFToken` + `X-Player-Token` ด้วย
- **Risk:** แก้ autoRandom guard ถ้าลืมจุดใดจุดหนึ่งจะยังสุ่มต่อ

## Impact

- คิวแก้ไขได้ตามที่ขอ
- ค้นหาไม่ซ้ำ
- ออโต้ปิดแล้วหยุดจริง
- มี verification รวม

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development

1. **[Queue move button]** - Lane A | Can run together: Task 2 | Must wait for: none | TDD slice: test queue has move button -> add button + API -> `manage.py test`
2. **[Search duplicate fix]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: test only one loading text -> fix -> `manage.py test`
3. **[Auto bug fix]** - Lane C | Can run together: Task 1, Task 2 | Must wait for: none | TDD slice: test auto off not call playRandomHit -> add guard -> `manage.py test`
4. **[Full verification]** - Docs | Can run together: none | Must wait for: Task 1,2,3 | TDD slice: docs only -> run `manage.py test && manage.py check` -> `checklists/full-verification.md`

---

### Task 1: Queue move button

**Files:**

- Modify: `music/templates/music/player.html` (`renderQueue`), `music/templates/music/request.html` (`fetchMySongs`)
- Create: `music/views.py` (`move_queue` endpoint)
- Modify: `music/urls.py`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 2
- Must wait for: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_queue_has_move_button():
  res = client.get('/')
  assert 'เล่นถัดไป' in res.content.decode() or 'move' in res.content.decode()
def test_move_api():
  # create 5 songs, POST /api/queue/move/ with from/to, assert order changed
  pass
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

In `views.py` add `def move_queue(request): if POST: data=json.loads, from_id, to_index, reorder by created_at or add position field, return 200`. In `urls.py` add `path('api/queue/move/', views.move_queue)`. In `player.html` `renderQueue` add `<button onclick="moveToNext(${song.id})">เล่นถัดไป</button>` with `function moveToNext(id){ fetch('/api/queue/move/', {method:'POST', headers:{"X-CSRFToken":getCSRFToken(),"X-Player-Token":getPlayerToken(),"Content-Type":"application/json"}, body:JSON.stringify({song_id:id, position:'next'})}).then(()=>fetchQueue())}`. Simple: use `add-front` trick: fetch existing song data then add-front + delete old.

- [ ] **Step 4: PASS**

---

### Task 2: Search duplicate fix

**Files:**

- Modify: `music/templates/music/request.html` (`searchSong`)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 1
- Must wait for: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_search_loading_single_text():
  res = client.get('/request/')
  assert 'กำลังค้นหาโปรดรอสักครู่' in res.content.decode()
  assert res.content.decode().count('กำลังค้นหา') == 1 # or check JS not set results innerHTML to loading
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

In `request.html` `searchSong`: remove `document.getElementById("results").innerHTML = '<p>กำลังค้นหา...</p>'` line, keep only `loading` element, change `<p id="loading">กำลังค้นหา...</p>` to `กำลังค้นหาโปรดรอสักครู่`.

- [ ] **Step 4: PASS**

---

### Task 3: Auto bug fix

**Files:**

- Modify: `music/templates/music/player.html` (`playRandomHit`, `fetchQueue`, `onPlayerReady`, `toggleAutoRandom`)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 1, Task 2
- Must wait for: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_auto_off_not_call_random():
  res = client.get('/')
  # check JS has if (!autoRandomEnabled) return at top of playRandomHit and in fetchQueue
  assert res.content.decode().count('if (!autoRandomEnabled') >= 2
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

In `playRandomHit` first line `if (!autoRandomEnabled) return;` already there but ensure also in `fetchQueue` `if (autoRandomEnabled && isPlayerReady && !currentSong && queue.length===0) playRandomHit()` already has guard, but `onPlayerReady` setTimeout also guard, `toggleAutoRandom` when off should not call playRandomHit, and clear any pending timeout for playRandomHit.

Add `let autoRandomTimer=null` and in `playRandomHit` clear, in `toggleAutoRandom` if off clearTimeout.

- [ ] **Step 4: PASS**

---

### Task 4: Full verification

**Files:**

- Create: `docs/superpowers/checklists/full-verification.md`
- Test: `python manage.py test && python manage.py check`

**Parallelization:**

- Can run with: none
- Must wait for: Task 1,2,3

- [ ] **Step 0: Docs only**

- [ ] **Step 1: Create checklist**

Include `manage.py test 50 OK`, `manage.py check OK`, `CSRF` `XSS` `overlay` `queue move` `search loading` `auto` checks.

- [ ] **Step 2: Verify**

Run `venv\Scripts\python.exe manage.py test music.tests -v2 && venv\Scripts\python.exe manage.py check` PASS.

