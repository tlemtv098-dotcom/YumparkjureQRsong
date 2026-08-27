# Project Completeness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ทำให้โปรเจกต์ Yum Jukebox สมบูรณ์พร้อม production — เติม UX polish, security, performance, admin, PWA และ features ที่ขาด

**Estimated tasks:** 6 | **Estimated time:** ~45 min | **Touches:** API / DB / Frontend / Ops / Security

## Current Problem / Current Solution

ระบบปัจจุบันใช้งานได้ (YouTube IFrame API, queue, search, hits, suggestions) แต่ยังขาด:
- ไม่มี rate limiting / dedup → spam คิวได้
- ไม่มี volume control / toast / loading skeletons → UX ยังดิบ
- ไม่มี health check / Dockerfile / caching → ops ไม่พร้อม
- Admin ยังพื้นฐาน, ไม่มีสถิติ, ไม่มี PWA, ไม่มี genre/playlist features
- BlockedVideoIds กระจาย 3 ที่ไม่ sync, CSRF exempt ทุก endpoint, ไม่มี CSP

## Proposed Approach

เติม 6 lane แบบ parallel-first:
1. **UX/UI Polish** — volume slider, toast, progress, skeleton, empty states (player + request)
2. **Admin & Analytics** — ปรับ admin list_display, สถิติ top songs, export, dashboard endpoint
3. **Performance & Reliability** — cache hits/suggest, dedup queue, retry, timeout tuning
4. **Features** — genre filter tabs, playlist save, share link, lyrics preview
5. **Security & Ops** — rate limit, input sanitize, CSP, healthz, Dockerfile, gunicorn tuning
6. **Mobile/PWA** — manifest.json, service worker (cache static), install prompt

## Side by Side

| Scenario | Before | After |
|---|---|---|
| Spam ขอเพลงรัวๆ | เพิ่มคิวได้ไม่จำกัด, ซ้ำได้ | Rate limit 5 req/10s + dedup video_id ในคิว |
| ปรับเสียง | ต้องใช้ YouTube controls อย่างเดียว | Volume slider + mute toggle บน player |
| เปิด Player ครั้งแรก | ไม่มี feedback ตอนโหลด | Skeleton + toast "กำลังโหลด..." |
| ดูสถิติร้าน | ต้องเข้า DB ตรง | /admin สถิติ + /api/stats top 10 |
| Deploy Railway | ใช้ nixpacks อย่างเดียว | มี Dockerfile + healthz + WhiteNoise ครบ |
| เปิดบนมือถือ | แค่ responsive | PWA installable + offline cache shell |

## Assumptions & Risks

- **Assumed:** yt-dlp ใช้งานได้, ไม่ต้องเปลี่ยน search backend
- **Assumed:** SQLite พอสำหรับร้านเดียว (ไม่ต้อง Postgres)
- **Assumed:** ไม่ต้อง auth จริง (client_id พอ)
- **Risk:** Rate limit แบบ memory จะหายเมื่อ restart (รับได้สำหรับร้านเดียว)
- **Risk:** PWA service worker อาจ cache เก่า ต้อง version bump
- **Risk:** CSP อาจ block YouTube iframe ถ้าตั้งเข้มเกิน

## Impact

- UX ดีขึ้นมาก — รู้สึกเป็นแอปจริง ไม่ใช่ prototype
- ปลอดภัยขึ้น — กัน spam, XSS, CSRF ดีขึ้น
- Deploy เสถียร — health check + Dockerfile
- ดูแลร้านง่าย — admin สวย + สถิติ

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[UX/UI Polish]** - Lane A | Can run together: 2,3,5 | Must wait for: none | TDD slice: visual verify (no unit test — frontend) -> toast+volume+skeleton -> verify in browser
2. **[Admin & Analytics]** - Lane B | Can run together: 1,3,5 | Must wait for: none | TDD slice: test_admin_list_display -> admin.py + /api/stats -> verify /admin + /api/stats
3. **[Performance & Reliability]** - Lane C | Can run together: 1,2,5 | Must wait for: none | TDD slice: test_dedup_queue -> cache + dedup -> verify /api/add duplicate rejected + cache hit
4. **[Features - Genre/Playlist/Share]** - Lane D | Can run together: 5 | Must wait for: 1,3 (reuse search UI) | TDD slice: test_genre_filter -> genre tabs + share link -> verify filter works
5. **[Security & Ops]** - Lane E | Can run together: 1,2,3 | Must wait for: none | TDD slice: test_healthz + test_ratelimit -> healthz + rate limit + CSP -> verify /healthz 200 + 429 on spam
6. **[Mobile/PWA]** - Lane F | Can run together: 1,2,3,5 | Must wait for: none | TDD slice: manual verify (manifest + sw) -> manifest.json + sw.js -> verify Lighthouse PWA

---

### Task 1: UX/UI Polish

**Files:**

- Modify: `music/templates/music/player.html` (add volume slider, toast div, skeleton, progress bar)
- Modify: `music/templates/music/request.html` (add toast, skeleton, empty state polish)

**Parallelization:**

- Can run with: `Task 2`, `Task 3`, `Task 5`
- Must wait for: `none`
- Race risk: `none` (only touches templates, different from backend tasks)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code. This task is frontend-only; use visual verification instead of failing unit test (docs/config-only exception).

- [ ] **Step 1: Visual baseline**

Open http://localhost:8000/ and http://localhost:8000/request/ — note missing toast, volume, skeleton.

- [ ] **Step 2: Implement minimal code**

Add to player.html:
- Volume slider (`<input type="range">` 0-100 → `player.setVolume()`) + mute toggle
- Toast container (`#toast` fixed bottom-center, auto-hide 3s, function `showToast(msg, type)`)
- Skeleton for `#hit-list` and `#manual-results` while loading
- Call `showToast` on add/skip/clear/error

Add to request.html similarly: toast, skeleton for search/hits.

- [ ] **Step 3: Verify**

Run server, open both pages, check volume slider changes volume, toast appears on add, skeleton shows during fetch.

---

### Task 2: Admin & Analytics

**Files:**

- Modify: `music/admin.py`
- Modify: `music/views.py` (add `stats` endpoint)
- Modify: `music/urls.py` (add `api/stats/` route)
- Test: `music/tests.py` (add test_stats)

**Parallelization:**

- Can run with: `Task 1`, `Task 3`, `Task 5`
- Must wait for: `none`
- Race risk: `views.py` shared with Task 3,5 — coordinate via Task tool (different functions)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_stats_returns_top_songs(self):
    SongQueue.objects.create(title="A", video_id="aaa", channel="C")
    SongQueue.objects.create(title="A", video_id="aaa", channel="C")
    res = self.client.get("/api/stats/")
    self.assertEqual(res.status_code, 200)
    self.assertIn("top_songs", res.json())
```

- [ ] **Step 2: Run the test and confirm it fails**

`python manage.py test music.tests.StatsTest`

- [ ] **Step 3: Implement minimal code**

- admin.py: list_display += requested_by, client_id; list_filter += channel, created_at; readonly created_at; ordering -created_at
- views.py: `def stats(request):` aggregate top 5 by video_id count, total queued/played
- urls.py: `path('api/stats/', views.stats)`

- [ ] **Step 4: Run the test and confirm it passes**

- [ ] **Step 5: Refactor only after green**

---

### Task 3: Performance & Reliability

**Files:**

- Modify: `music/views.py` (add cache for hits/suggest, dedup logic in add_to_queue, timeout for yt_dlp)
- Modify: `yum_jukebox/settings.py` (add CACHES = LocMemCache)
- Test: `music/tests.py` (test_dedup, test_cache)

**Parallelization:**

- Can run with: `Task 1`, `Task 2`, `Task 5`
- Must wait for: `none`
- Race risk: `views.py` shared — add functions without overlapping lines

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_dedup_same_video_in_queue(self):
    self.client.post("/api/add/", json.dumps({"title":"A","video_id":"abc123","client_id":"c1"}), content_type="application/json")
    res = self.client.post("/api/add/", json.dumps({"title":"A","video_id":"abc123","client_id":"c1"}), content_type="application/json")
    self.assertEqual(res.status_code, 400)
    self.assertIn("already in queue", res.json()["error"])
```

- [ ] **Step 2: Run `python manage.py test music.tests.DedupTest` — FAIL**

- [ ] **Step 3: Implement**

- settings.py: `CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}`
- views.py: in add_to_queue check `SongQueue.objects.filter(video_id=video_id, is_played=False).exists()` → 400; wrap yt_dlp with cache `cache.get/set` 60s for hits, 30s for suggest; add timeout try/except
- [ ] **Step 4: PASS**

---

### Task 4: Features - Genre/Playlist/Share

**Files:**

- Modify: `music/templates/music/request.html` (genre tabs)
- Modify: `music/templates/music/player.html` (share button)
- Modify: `music/views.py` (genre param for hits)
- Test: `music/tests.py` (genre filter)

**Parallelization:**

- Can run with: `Task 5`
- Must wait for: `Task 1`, `Task 3` (needs search UI + cache)
- Race risk: `request.html` also touched by Task 1 — wait for Task 1

- [ ] **Step 0: TDD**

- [ ] **Step 1: Failing test**

```python
def test_hits_genre_filter(self):
    res = self.client.get("/api/hits/?genre=rock")
    self.assertEqual(res.status_code, 200)
```

- [ ] **Step 3: Implement**

- views.py hits(): if genre=rock/pop/lukthung → different query list
- request.html: tabs `[ทั้งหมด, ป๊อป, ร็อก, ลูกทุ่ง, ฮิต TikTok]` → fetchHits(genre)
- player.html: share button → copy `location.origin + "/request/?q=" + encodeURIComponent(title)` + toast

---

### Task 5: Security & Ops

**Files:**

- Modify: `music/views.py` (rate limit decorator, input sanitize, healthz)
- Modify: `music/urls.py` (healthz route)
- Modify: `yum_jukebox/settings.py` (CSP via middleware or header, SECURE_CONTENT_TYPE_NOSNIFF)
- Create: `Dockerfile`
- Modify: `railway.toml` (healthcheckPath = "/healthz/")
- Test: `music/tests.py` (healthz, ratelimit)

**Parallelization:**

- Can run with: `Task 1`, `Task 2`, `Task 3`
- Must wait for: `none`
- Race risk: `views.py` shared — add at bottom

- [ ] **Step 0: TDD**

- [ ] **Step 1: Failing tests**

```python
def test_healthz(self):
    self.assertEqual(self.client.get("/healthz/").status_code, 200)

def test_ratelimit_add(self):
    for _ in range(6):
        self.client.post("/api/add/", json.dumps({"title":"A","video_id":"x"+str(_),"client_id":"c1"}), content_type="application/json")
    res = self.client.post("/api/add/", json.dumps({"title":"A","video_id":"zzz","client_id":"c1"}), content_type="application/json")
    self.assertEqual(res.status_code, 429)
```

- [ ] **Step 3: Implement**

- views.py: `healthz` → JsonResponse({"status":"ok"}); `rate_limit` simple dict + time window 10s/5 req per IP
- settings.py: add `SECURE_CONTENT_TYPE_NOSNIFF = True` already true, add CSP header middleware
- Dockerfile: `FROM python:3.12-slim` + pip install + migrate + gunicorn
- railway.toml: `healthcheckPath = "/healthz/"`

---

### Task 6: Mobile/PWA

**Files:**

- Create: `music/static/music/manifest.json`
- Create: `music/static/music/sw.js`
- Modify: `music/templates/music/player.html` (link manifest, register sw)
- Modify: `music/templates/music/request.html` (link manifest, register sw)
- Test: manual Lighthouse

**Parallelization:**

- Can run with: `Task 1,2,3,5`
- Must wait for: `none`
- Race risk: `player.html` also touched by Task 1 — coordinate (insert at head)

- [ ] **Step 0: TDD (manual)**

- [ ] **Step 1: Create manifest.json**

```json
{"name":"Yum Jukebox","short_name":"YumJuke","start_url":"/","display":"standalone","background_color":"#fff7ed","icons":[{"src":"/static/music/img/logo.jpg","sizes":"192x192","type":"image/jpeg"}]}
```

- [ ] **Step 2: Create sw.js** — cache static shell (/, /request/, /static/**), network-first for /api/**
- [ ] **Step 3: Register in both templates** `<link rel="manifest" href="{% static 'music/manifest.json' %}">` + `navigator.serviceWorker.register(...)`
- [ ] **Step 4: Verify** — open Chrome DevTools > Application > Manifest + Service Workers
