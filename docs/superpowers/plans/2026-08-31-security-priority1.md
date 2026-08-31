# Security Priority 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** แก้ 🔴 Priority 1 ให้เว็บพร้อมใช้งานจริง: CSRF, ป้องกัน /api/clear & /api/played ให้เฉพาะเจ้าของร้าน, XSS escape, รวม Sound Overlay เหลือตัวเดียว

**Estimated tasks:** 5 | **Estimated time:** ~90 min | **Touches:** Frontend / Backend / Tests

## Current Problem / Current Solution

- ทุก POST (`/api/add/`, `/api/clear/`, `/api/add-front/`, `/api/my-songs/.../delete/`, `/api/block/`) ใช้ `@csrf_exempt` ใครก็ยิงได้ ไม่มี `<meta name="csrf-token">` ส่ง `X-CSRFToken`
- `/api/clear/` ล้างคิวได้โดยใครก็ได้ ไม่มี auth ลูกค้าแกล้งล้างได้
- `/api/played/<id>/` ทำให้เพลงจบได้โดยใครก็ได้
- `innerHTML` ใส่ `song.title/channel/requested_by` ตรงๆ เสี่ยง XSS
- มี `sound-overlay` + `queue-overlay` ซ้อนกัน ทำให้ Safari/Chrome จัดการ gesture สับสน
- Frontend `blockedVideoIds` กรอง UX แต่ไม่มี Backend validation ซ้ำ

## Proposed Approach

- **CSRF:** เพิ่ม `<meta name="csrf-token" content="{{ csrf_token }}">` ใน `player.html` + `request.html` (ใช้ `{% csrf_token %}`), เพิ่ม `function getCSRFToken()` อ่าน meta, ทุก `fetch POST` ส่ง `X-CSRFToken: getCSRFToken()` + `credentials: 'same-origin'`, เอา `@csrf_exempt` ออกจาก `add_to_queue/add_to_queue_front/remove_my_song/block_video/clear_queue` เหลือ `mark_played/clear_queue` ที่จะล็อกสิทธิ์เพิ่ม, ตั้ง `CSRF_TRUSTED_ORIGINS` ใน `settings.py` ให้ตรง `https://yumpakjure.onrender.com` + `ALLOWED_HOSTS`
- **/api/clear & /api/played owner only:** เพิ่ม decorator `require_owner` เช็ค `request.user.is_staff` หรือ `X-Player-Token == settings.PLAYER_TOKEN` (ตั้ง ENV `PLAYER_TOKEN` ง่ายๆ) ถ้าไม่ผ่าน 403, `request` หน้าไม่ต้อง auth
- **XSS:** เพิ่ม `escapeHtml()` และใช้ก่อน `innerHTML` ทุก `renderQueue/manualSearch/renderHitList` ครอบ `title/channel/requested_by`
- **Overlay single:** ลบ `queue-overlay` ออก เหลือ `sound-overlay` ตัวเดียว, รวม JS `showSoundOverlay/hideSoundOverlay/enableSoundFromUserGesture` ให้ fetchQueue/playNext ใช้ตัวเดียว
- **Backend validation:** `add_to_queue` ตรวจ `video_id` `title` `channel` ซ้ำ, `_is_blocked` + `dedup` + `rate_limit` ยังอยู่, ไม่เชื่อ `client_id` อย่างเดียว

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| POST /api/add/ จาก curl ไม่มี token | 200 สำเร็จ (exempt) | 403 CSRF fail ถ้าไม่ส่ง X-CSRFToken |
| ลูกค้าเรียก /api/clear/ | ล้างได้ | 403 ต้องเป็นเจ้าของร้าน |
| ชื่อเพลง `<script>alert(1)</script>` | รัน script | แสดงเป็น text ธรรมดา |
| เปิดเว็บ iPhone มี 2 overlay | sound + queue ซ้อน | เหลือ sound ตัวเดียว |

## Assumptions & Risks

- **Assumed:** Render ใช้ HTTPS, `CSRF_COOKIE_SECURE=True` ได้, `CSRF_TRUSTED_ORIGINS` มี `https://yumpakjure.onrender.com`
- **Assumed:** เจ้าของร้านเปิด `player.html` บนเครื่องเดียว ไม่ต้องทำ login เต็มระบบ ใช้ `PLAYER_TOKEN` ง่ายๆ พอ
- **Risk:** เปลี่ยน CSRF แล้วลืมส่ง header จะ 403 ทุก POST ต้องอัปเดต JS ทุกจุด
- **Risk:** รวม overlay เหลือตัวเดียว ถ้า logic เดิมพึ่ง queue-overlay อาจทำให้ flow แตะเปิดเสียงพัง ต้องเทส Safari/Chrome

## Impact

- ปิดช่อง CSRF ที่ critical ที่สุด
- กันลูกค้าล้างคิว/จบเพลงมั่ว
- กัน XSS จากชื่อเพลง
- โค้ด Player สะอาดขึ้น ลดบั๊ก Safari

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes.

1. **[CSRF meta + JS header]** - Lane A | Can run together: Task 3 | Must wait for: none | TDD slice: test page contains meta csrf-token + JS sends X-CSRFToken -> add meta + getCSRFToken -> `manage.py test`
2. **[Protect /api/clear & /api/played owner only]** - Lane B | Can run together: Task 3 | Must wait for: Task 1 | TDD slice: test clear without token 403, with token 200 -> add decorator -> `manage.py test`
3. **[XSS escapeHtml]** - Lane C | Can run together: Task 1, Task 2 | Must wait for: none | TDD slice: test render with <script> not executed -> add escapeHtml -> `manage.py test`
4. **[Single sound-overlay]** - Lane D | Can run together: none | Must wait for: Task 1, Task 3 | TDD slice: test only sound-overlay exists, queue-overlay gone -> remove queue-overlay -> `manage.py test`
5. **[Settings CSRF_TRUSTED_ORIGINS]** - Docs/config | Can run together: Task 1 | Must wait for: none | TDD slice: docs only -> verify settings -> `manage.py check`

---

### Task 1: CSRF meta + JS header

**Files:**

- Modify: `music/templates/music/player.html:1-15` add meta
- Modify: `music/templates/music/request.html:1-15` add meta
- Modify: `music/templates/music/player.html` JS getCSRFToken + all fetch POST
- Modify: `music/templates/music/request.html` JS getCSRFToken + all fetch POST
- Modify: `music/views.py` remove @csrf_exempt from add_to_queue etc
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 3
- Must wait for: none
- Race risk: none

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_player_has_csrf_meta():
  res = client.get('/')
  assert 'csrf-token' in res.content.decode()
  assert 'getCSRFToken' in res.content.decode()
def test_add_requires_csrf():
  res = client.post('/api/add/', data=json.dumps({...}), content_type='application/json')
  assert res.status_code == 403  # without token
```

- [ ] **Step 2: Run the test and confirm it fails**

`venv\Scripts\python.exe manage.py test music.tests -v2` FAIL.

- [ ] **Step 3: Implement the minimal code**

Add `<meta name="csrf-token" content="{{ csrf_token }}">` in `<head>`, add `function getCSRFToken(){return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')||''}` and add header `"X-CSRFToken": getCSRFToken()` + `credentials: 'same-origin'` to every `fetch(..., {method: 'POST'})`. Remove `@csrf_exempt` from views that should be protected, keep `ensure_csrf_cookie` on player_view.

- [ ] **Step 4: Run the test and confirm it passes**

`manage.py test` PASS.

- [ ] **Step 5: Refactor only after green**

---

### Task 2: Protect /api/clear & /api/played owner only

**Files:**

- Modify: `music/views.py: clear_queue, mark_played`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 3
- Must wait for: Task 1 (needs CSRF header to test 403 correctly)
- Race risk: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_clear_requires_owner():
  res = client.post('/api/clear/')
  assert res.status_code == 403
  res = client.post('/api/clear/', headers={'X-Player-Token': settings.PLAYER_TOKEN})
  assert res.status_code == 200
```

- [ ] **Step 2: Run FAIL**

- [ ] **Step 3: Implement**

Add `PLAYER_TOKEN = os.environ.get('PLAYER_TOKEN','dev')` in settings, add decorator `def require_owner(view): if request.headers.get('X-Player-Token') != settings.PLAYER_TOKEN and not request.user.is_staff: return HttpResponseForbidden()`, apply to `clear_queue` and `mark_played`.

- [ ] **Step 4: PASS**

---

### Task 3: XSS escapeHtml

**Files:**

- Modify: `music/templates/music/player.html` `music/templates/music/request.html` (renderQueue etc)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 1, Task 2
- Must wait for: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_render_escapes_xss():
  # check JS contains escapeHtml
  res = client.get('/')
  assert 'escapeHtml' in res.content.decode()
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

Ensure `escapeHtml` exists and is used before `innerHTML +=` for title/channel/requested_by in `renderQueue`, `manualSearch`, `renderHitList`, `requestHit`.

- [ ] **Step 4: PASS**

---

### Task 4: Single sound-overlay

**Files:**

- Modify: `music/templates/music/player.html`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: none
- Must wait for: Task 1, Task 3

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_only_sound_overlay_exists():
  res = client.get('/')
  assert 'id="sound-overlay"' in res.content.decode()
  assert 'id="queue-overlay"' not in res.content.decode()
```

- [ ] **Step 2: FAIL** (currently has both)

- [ ] **Step 3: Implement**

Remove `<div id="queue-overlay">` HTML and JS references `queueOverlay` → replace with `soundOverlay` (`sound-overlay`). Update `fetchQueue`/`playNext`/`enableSoundFromUserGesture` to use `soundOverlay` only.

- [ ] **Step 4: PASS**

---

### Task 5: Settings CSRF_TRUSTED_ORIGINS

**Files:**

- Modify: `yum_jukebox/settings.py`
- Test: `python manage.py check`

**Parallelization:**

- Can run with: Task 1
- Must wait for: none

- [ ] **Step 0: Docs only**

- [ ] **Step 1: Verify**

Check `settings.py` contains `CSRF_TRUSTED_ORIGINS = ['https://yumpakjure.onrender.com']` and `ALLOWED_HOSTS` includes it, `CSRF_COOKIE_SECURE = True`.

- [ ] **Step 2: Run `python manage.py check` PASS**

