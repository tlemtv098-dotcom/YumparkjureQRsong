# Full Verification Checklist — Queue Edit / Search Duplicate / Auto Bug

> **Goal:** ตรวจโครงสร้างทั้งหมดหลังแก้คิวเลื่อน/ค้นหาซ้ำ/ออโต้สุ่ม — ให้ `manage.py test` + `manage.py check` + หน้าเว็บหลักครบ
> **Plan:** `docs/superpowers/plans/2026-08-31-queue-edit-search-auto.md` (Task 4)
> **Branch:** `master` หลัง merge Task 1,2,3
> **Date:** 2026-08-31

## How to run quick verification

```bat
venv\Scripts\python.exe manage.py test music.tests -v2
venv\Scripts\python.exe manage.py check
```

Expected: `Ran 50 tests in ... OK` + `System check identified no issues (0 silenced).`

---

## 1. `python manage.py test` — 50 OK

| Check | Command | Expected |
|-------|---------|----------|
| Full suite | `venv\Scripts\python.exe manage.py test music.tests -v2` | `Found 50 test(s)` / `Ran 50 tests in ... OK` / `Destroying test database ...` |
| No warnings as errors | same run, no traceback | PASS |

- [ ] `Found 50 test(s). ... Ran 50 tests in ... OK` (0 failures, 0 errors)
- [ ] No `FAIL` / `ERROR` lines in output

**Automated guard (existing tests):** `PlayerPageTests`, `RequestPageTests`, `ClearQueueApiTests`, `MySongsApiTests`, `Universal*RegressionTests`, `SingleSoundOverlayTests`, etc. already assert 50 total. If adding task 1-3 tests, keep total >=50; update this row count accordingly.

---

## 2. `python manage.py check` — OK

| Check | Command | Expected |
|-------|---------|----------|
| Django system check | `venv\Scripts\python.exe manage.py check` | `System check identified no issues (0 silenced).` |

- [ ] `System check identified no issues (0 silenced).`

---

## 3. CSRF meta present

**Why:** กัน POST จาก curl/origin อื่น, ต้องส่ง `X-CSRFToken` + `credentials: same-origin`

| Page | Check |
|------|-------|
| `GET /` (player) | HTML contains `<meta name="csrf-token" content="{{ csrf_token }}">` |
| `GET /request/` | same meta |
| JS | `function getCSRFToken()` exists และทุก `fetch(...,{method:"POST"})` ส่ง `headers:{"X-CSRFToken": getCSRFToken(), ...}` + `credentials:'same-origin'` |

Quick verify:
```bat
venv\Scripts\python.exe manage.py shell -c "from django.test import Client; c=Client(); print('csrf-token' in c.get('/').content.decode()); print('getCSRFToken' in c.get('/').content.decode()); print('csrf-token' in c.get('/request/').content.decode())"
```
or console check: DevTools → Elements → `<meta name="csrf-token">` exists.

- [ ] `player.html` มี `meta[name="csrf-token"]` + `getCSRFToken()`
- [ ] `request.html` มี `meta[name="csrf-token"]` + `getCSRFToken()`
- [ ] ทุก `fetch POST` (`/api/add/`, `/api/clear/`, `/api/played/`, `/api/queue/move/`, `/api/block/`, `/api/my-songs/...`) ส่ง `X-CSRFToken`
- [ ] Negative: `POST /api/clear/` without CSRF cookie → 403 (enforce_csrf_checks=True test)

---

## 4. XSS escape

**Why:** `title/channel/requested_by` มาจาก YouTube/ผู้ใช้ ต้อง escape ก่อน `innerHTML`

| Check | Expected |
|-------|----------|
| `player.html` | `function escapeHtml(str)` exists + `renderQueue`, `manualSearch`, `renderHitList` ใช้ `escapeHtml(song.title)` / `escapeHtml(song.channel)` / `escapeHtml(requested_by)` ก่อน `innerHTML +=` |
| `request.html` | same `escapeHtml` + `renderHitList`, `searchSong`, `fetchMySongs`, `showSuggestions` ใช้ `escapeHtml` |

Quick verify:
```bat
venv\Scripts\python.exe manage.py shell -c "from django.test import Client; c=Client(); h=c.get('/').content.decode(); print(h.count('escapeHtml'))"
```
Should be >= 4 occurrences per template.

- [ ] `escapeHtml` defined in `player.html` และ `request.html`
- [ ] No raw `song.title` / `song.channel` inserted via `innerHTML` without `escapeHtml()`
- [ ] Test payload `<script>alert(1)</script>` renders as `&lt;script&gt;` not executed

---

## 5. Single overlay (sound-overlay only)

**Why:** รวม overlay เหลือตัวเดียว กัน gesture สับสนบน iOS/Chrome/LINE

| Check | Expected |
|-------|----------|
| `GET /` HTML | `id="sound-overlay"` exists (1 instance) |
| `GET /` HTML | `id="queue-overlay"` NOT exists (0 instances) |
| JS | Only `soundOverlay` / `sound-overlay` refs, no `queueOverlay` variable |
| Behaviour | `fetchQueue` / `playNext` / `handleOverlayTap` use `showSoundOverlay()` / `hideSoundOverlay()` uniform |

Tests: `SingleSoundOverlayTests.test_only_sound_overlay_exists` + `UniversalPlayerRegressionTests`

- [ ] `player.html` contains `id="sound-overlay"` exactly once
- [ ] `player.html` does NOT contain `id="queue-overlay"` / `queue-overlay`
- [ ] `handleOverlayTap()` hides overlay + unmutes + calls `playVideo()`
- [ ] Manual: เปิด `GET /` บน iPhone Safari / Chrome / LINE WebView → เห็น overlay เดียว `แตะเพื่อเปิดเสียง` ก่อนเล่นครั้งแรก

---

## 6. Queue move button — `เล่นถัดไป`

**Why:** ย้ายเพลงท้ายคิวขึ้นเล่นถัดไป โดยไม่ต้องลบแล้วขอใหม่

| Check | Expected |
|-------|----------|
| `player.html` `renderQueue` | มี `<button onclick="moveToNext(${song.id})">เล่นถัดไป</button>` สำหรับทุกเพลงที่ไม่ใช่ `currentSong` |
| JS | `function moveToNext(id)` exists → `fetch('/api/queue/move/', {method:'POST', headers:{"Content-Type":"application/json","X-CSRFToken":getCSRFToken(),"X-Player-Token":getPlayerToken()}, credentials:'same-origin', body:JSON.stringify({song_id:id, position:'next'})}).then(()=>fetchQueue())` |
| Backend | `music/views.py` has `def move_queue(request)` + `music/urls.py` has `path('api/queue/move/', views.move_queue)` → reorder queue (move to position 2 / next) |
| Auth | `move_queue` requires `X-CSRFToken` + `X-Player-Token` if protected, or documented open; returns `{status:'success'}` |

Quick verify:
```bat
venv\Scripts\python.exe manage.py shell -c "from django.test import Client; c=Client(); print('เล่นถัดไป' in c.get('/').content.decode()); print('moveToNext' in c.get('/').content.decode()); print('api/queue/move' in c.get('/').content.decode())"
```

- [ ] `GET /` contains `เล่นถัดไป` และ `moveToNext`
- [ ] `GET /` contains `/api/queue/move/`
- [ ] `POST /api/queue/move/` with `{song_id, position:'next'}` reorders queue correctly (create 5 songs → move last → second)
- [ ] After move, `GET /api/queue/` returns new order
- [ ] (Optional) `request.html` `fetchMySongs` also shows move button if spec requires

---

## 7. Search loading — single text `กำลังค้นหาโปรดรอสักครู่`

**Why:** แก้โชว์ซ้ำ 2 ที่ (`#loading` + `results.innerHTML = 'กำลังค้นหา...'`) เหลืออันเดียว

| Check | Expected |
|-------|----------|
| `request.html` | `<p id="loading" class="hidden ...">กำลังค้นหาโปรดรอสักครู่</p>` exists (exact string) |
| `request.html` JS `searchSong()` | Only `document.getElementById("loading").classList.remove("hidden")` for loading, no `document.getElementById("results").innerHTML = '<p>กำลังค้นหา...` |
| Count | `res.content.decode().count('กำลังค้นหา') == 1` and `count('กำลังค้นหาโปรดรอสักครู่') == 1` |

Quick verify:
```bat
venv\Scripts\python.exe manage.py shell -c "from django.test import Client; c=Client(); h=c.get('/request/').content.decode(); print(h.count('กำลังค้นหา')); print('กำลังค้นหาโปรดรอสักครู่' in h); print('results' in h and 'กำลังค้นหา...' in h)"
```
Expected: `1`, `True`, `False` for duplicate results innerHTML (player `manual-loading` is separate panel, OK if it stays `กำลังค้นหา...` or updated — main contract is `request.html` single).

- [ ] `GET /request/` contains `กำลังค้นหาโปรดรอสักครู่` exactly once
- [ ] `GET /request/` does NOT contain duplicate `กำลังค้นหา...` in `results.innerHTML`
- [ ] `searchSong()` removes hidden loading on `finally`, shows results only after fetch done
- [ ] Manual: พิมพ์ค้นหา → เห็น loading เดียว `กำลังค้นหาโปรดรอสักครู่` ไม่ซ้อน

---

## 8. Auto OFF not playing — `autoRandomEnabled` guard

**Why:** ปิด `ออโต้: ปิด` แล้วต้องหยุดสุ่มทันที ไม่เรียก `playRandomHit` อีกแม้ `fetchQueue`/`onReady`/`setTimeout` ค้าง

| Check | Expected |
|-------|----------|
| Initial state | `let autoRandomEnabled = localStorage.getItem('auto_random') === 'on'` (defaults OFF) |
| Guard | `function playRandomHit(){ if (!autoRandomEnabled) return; ... }` at top |
| `fetchQueue` | `if (autoRandomEnabled && isPlayerReady && !currentSong && queue.length===0) playRandomHit()` (guarded) |
| `onYouTubeIframeAPIReady.onReady` | `setTimeout(()=>{ if (autoRandomEnabled) playRandomHit(); }, 800)` (guarded) |
| `toggleAutoRandom()` | When OFF: `clearTimeout(autoRandomTimer); autoRandomTimer=null` + not calling `playRandomHit` |
| Timer var | `let autoRandomTimer = null` exists, `fetchHits` auto play uses `clearTimeout(autoRandomTimer); autoRandomTimer=setTimeout(()=>playRandomHit(),300)` guarded |

Quick verify:
```bat
venv\Scripts\python.exe manage.py shell -c "from django.test import Client; c=Client(); h=c.get('/').content.decode(); print(h.count('if (!autoRandomEnabled')); print('autoRandomTimer' in h); print('clearTimeout(autoRandomTimer)' in h)"
```
Expected: count >=2, True, True

- [ ] `player.html` `playRandomHit` first line is `if (!autoRandomEnabled) return;`
- [ ] `player.html` `toggleAutoRandom` does `clearTimeout(autoRandomTimer)` when turning OFF
- [ ] `fetchQueue` + `onReady` + `fetchHits` all check `autoRandomEnabled` before `playRandomHit`
- [ ] Manual: เปิดเว็บ (defaults OFF) → ปล่อยว่าง → ไม่สุ่มเล่น; กด `ออโต้: เปิด` → ปล่อยว่าง 800ms → สุ่ม 1 เพลง; กด `ออโต้: ปิด` ระหว่าง `setTimeout` ค้าง → ไม่สุ่มต่อ

---

## Sign-off

| Verifier | Command | Result |
|----------|---------|--------|
| `manage.py test` | `venv\Scripts\python.exe manage.py test music.tests -v2` | ☐ PASS (50 OK) / ☐ FAIL |
| `manage.py check` | `venv\Scripts\python.exe manage.py check` | ☐ PASS / ☐ FAIL |
| Browser (player) | `GET /` → overlay, queue move, auto | ☐ PASS / ☐ FAIL |
| Browser (request) | `GET /request/` → search, loading, CSRF, XSS | ☐ PASS / ☐ FAIL |

- Date: ___________
- Tester: ___________
- Notes: ___________
- Result: ☐ PASS (all checked) / ☐ FAIL (note failed row)
