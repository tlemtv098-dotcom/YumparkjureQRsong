# iOS Audio Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** iPad ที่บล็อก YouTube ฝังทุกแบบ (Q139=B) เล่นเพลงได้ผ่านสตรีมเสียงตรง + ปุ่มเปิดในแอป YouTube

**Estimated tasks:** 3 | **Estimated time:** ~60 min | **Touches:** API / Frontend

## Current Problem / Current Solution

- `/embed-test/` ดำทั้ง 4 ส่วนบน iPad แต่ `youtube.com` ตรงๆ เล่นได้ → โดนบล็อกเฉพาะ third-party embed (Screen Time/content blocker/DNS) แก้ config ฝั่งเราไม่หาย
- ทางเหลือ code-side: เลี่ยงตัวเล่น YouTube ไปเลย ใช้สตรีมเสียงตรงผ่าน `<audio>` (เน็ตเปิด `googlevideo` อยู่เพราะ watch เล่นได้)

## Proposed Approach

- **Audio mode:** `GET /api/audio/?id=` → `yt-dlp` (ios client) ดึง `audio-only URL` + `cache 6 ชม.` → frontend `Audio()` element เล่นแทน iframe เมื่อ `?audio=1` หรือหลัง embed ล้มเหลว 2 ครั้งติด → `ended` ต่อคิวเอง + `MediaSession` เดิม + โชว์ปก/ชื่อเหมือนเดิม (ไม่มีภาพ)
- **Escape hatch:** ปุ่ม `เปิดในแอป YouTube` ต่อเพลง (`youtube://watch?v=` + fallback `https://youtube.com/watch?v=`) ทั้ง player/request
- ไม่แตะ embed path เดิม (desktop/Android ใช้เหมือนเดิม)

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| iPad บล็อกฝัง | ดำ 153 ทุกเพลง | เสียงเล่นผ่าน audio mode + ต่อคิวได้ |
| อยากดูภาพ | ไม่มีทาง | ปุ่มเปิดในแอป YouTube |

## Assumptions & Risks

- **Assumed:** `googlevideo` เปิดอยู่ (watch เล่นได้) + `yt-dlp` บน Render ดึงลิงก์ได้ (อาจโดน bot-block → มี fallback แจ้งเตือน)
- **Risk:** `yt-dlp` บน Render free อาจ 429/bot → endpoint คืน 503 + toast ชัดเจน, ไม่พัง path เดิม
- **Risk:** URL เสียงหมดอายุ (~6 ชม.) → cache 6 ชม. + ขอใหม่เมื่อ `error`

## Impact

- แตะ `views.py` (`audio` endpoint) + `urls.py` + `player.html` (audio mode + ปุ่ม) + `request.html` (ปุ่มเปิดในแอป)

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Audio API]** - Lane A | Can run together: none | Must wait for: none | TDD slice: GET /api/audio/?id= returns url -> add endpoint -> `manage.py test`
2. **[Audio mode player]** - Lane A | Can run together: none | Must wait for: Task 1 | TDD slice: ?audio=1 plays via Audio -> update player.html -> manual
3. **[Open-in-app button]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: button deep-links -> add to player/request -> `manage.py check`

---

### Task 1: Audio API

**Files:**

- Modify: `music/views.py` (add `audio_stream`), `music/urls.py`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 3`
- Must wait for: `none`
- Race risk: `views.py` shared with nothing else in this plan

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

`GET /api/audio/?id=ks7p6DA0dKk` (mock yt-dlp) -> 200 `{audio_url, duration_sec}`; bad id -> 400; yt-dlp fail -> 503

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL 404.

- [ ] **Step 3: Implement the minimal code**

`views.py`: `def audio_stream(request):` validate 11-char id → `cache.get(f"aud:{id}")` → `YoutubeDL({'format':'bestaudio[ext=m4a]/bestaudio','quiet':True,'socket_timeout':8,'extractor_args':{'youtube':{'player_client':['ios']}}})` extract `url` + `duration` → `cache.set 6h` → JSON. Fail → 503 `ดึงเสียงไม่ได้`.

`urls.py`: `path('api/audio/', views.audio_stream, name='audio_stream')`

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test` + `check`.

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 2: Audio mode player

**Files:**

- Modify: `music/templates/music/player.html` (audio mode)
- Test: manual + `music/tests.py` (marker test)

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1`
- Race risk: `player.html`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` (manual verify for audio).

- [ ] **Step 1: Write the failing test**

`GET /` contains `AUDIO_MODE` marker.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test`. Expected: FAIL.

- [ ] **Step 3: Implement the minimal code**

`player.html`: `const AUDIO_MODE = isIOS || new URLSearchParams(location.search).has('audio') || EMBED_FAILED_TWICE` → `let audioEl = new Audio()` → `playNextAudio()`: fetch `/api/audio/?id=` → `audioEl.src` → `play()` (ใน tap handler ตรง overlay) → `ended` → `removePlayedSong` → next → `MediaSession` เดิม → ซ่อน video เหลือปก+ชื่อ. Auto-switch: นับ embed fail 2 ครั้ง → `location.search += audio=1` + reload หรือสลับ inline.

- [ ] **Step 4: Run the test and confirm it passes**

`manage.py check` + เปิด `?audio=1` บน desktop กดเล่นมีเสียง.

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 3: Open-in-app button

**Files:**

- Modify: `music/templates/music/player.html` (now-playing row), `music/templates/music/request.html` (hit card)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 1`
- Must wait for: `none`
- Race risk: `player.html` shared with Task 2 — Task 2 waits, this edits different lines (button rows)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

`GET /` contains `youtube://` deep link marker; `GET /request/` contains `watch?v=`.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test`. Expected: FAIL.

- [ ] **Step 3: Implement the minimal code**

Player: ปุ่ม `เปิดในแอป` ข้าง `ข้ามเพลง` → `location.href='youtube://watch?v='+currentSong.video_id` + fallback timer `https://youtube.com/watch?v=`. Request: ลิงก์เล็กใต้ปุ่ม `ขอเพลง`.

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test` + `check`.

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.
