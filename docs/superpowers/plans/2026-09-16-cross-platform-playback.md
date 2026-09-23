# Cross-Platform Playback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ทำให้เพลงเล่นได้ทุกเบราว์เซอร์/แพลตฟอร์ม (Android / iOS / iPad / Desktop / LINE WebView) ภายใต้ข้อจำกัด autoplay และ YT embed โดยกำหนด per-platform 3 branch ชัดเจน

**Estimated tasks:** 6 | **Estimated time:** ~90 min | **Touches:** Frontend (player.html) / API (views.py audio_stream) / Tests / PWA

## Current Problem / Current Solution

สภาพปัจจุบัน `player.html` ใช้ YT IFrame API เป็นหลัก มี `isIOS` boolean เดียวเลือก host (`youtube.com` vs `youtube-nocookie.com`) และ audio fallback แบบ `?audio` + `playNextNoApi` จับแค่ error 153 ครั้งเดียว `COMPAT_GUARD` บล็อกเบราว์เซอร์เก่าทิ้ง ไม่มี MediaSession ครบทุกโหมด ไม่มี capability detection ทำให้ Android Chrome, Firefox, Samsung Internet, LINE WebView และ iPad บางเคสยังเล่นไม่เสถียร และล็อกจอแล้ว YT หยุด

## Proposed Approach

Build เดียว แยก 3 runtime branch: Desktop (nocookie + MediaSession), iOS/iPad (youtube.com + overlay + playsinline + audio fallback), Android/Other (nocookie + audio fallback + PWA) ใช้ Hybrid detection (UA เลือก host + capability เลือกฟีเจอร์) ลอง muted autoplay ก่อน ถ้าโดนบล็อกค่อยโชว์ overlay สำรอง แยก error 153/150/101 ให้ fallback ตรงจุด MediaSession ทุกโหมด + สลับ audio ตอน `visibilitychange` และ polyfill แบบ degrade สำหรับเบราว์เซอร์เก่า เก็บ `yt-dlp` local + `AUDIO_WORKER_URL` ไว้เป็นสำรอง audio เท่านั้น (ถูก ToS สุด)

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| Desktop Chrome/Edge | nocookie เล่นได้ แต่ไม่มี muted autoplay attempt | ลอง muted autoplay ทันที ถ้าบล็อกค่อย overlay + MediaSession |
| iOS Safari / iPad | isIOS boolean เดียว host youtube.com error 153 จับครั้งเดียว | Hybrid detect + แยก error 153→สลับ host 150/101→audio + overlay ต้องแตะ |
| Android Chrome | ต้องแตะ overlay เหมือน iOS | nocookie + muted attempt + audio fallback auto |
| LINE WebView | YT embed บล็อกบ่อย ไม่มีทางออก | error 150/101 auto ไป audio_stream |
| ล็อกจอ/background | YT หยุด มี MediaSession แค่ audio mode | MediaSession ทุกโหมด + visibilitychange สลับ audio |
| เบราว์เซอร์เก่า | COMPAT_GUARD บล็อกทิ้ง | polyfill fetch/Promise/URLSearchParams แล้ว degrade เล่นแบบพื้นฐาน |

## Assumptions & Risks

- **Assumed:** ล็อกดีไซน์ 10 ข้อ (Q1 A, Q2 C, Q3 C, Q4 A, Q5 C, Q6 C, Q7 B, Q8 A, Q9 B, Q10 A) เป็น final
- **Assumed:** ยอมให้ desktop เล่นเงียบ 1 วิก่อนมีเสียงหลัง gesture (ตาม Q3 C)
- **Assumed:** `AUDIO_WORKER_URL` ยังตั้งค่าได้บน Render env (ใช้เมื่อ yt-dlp local โดน bot-check)
- **Risk:** YT เปลี่ยน signature/bot-check ทำให้ yt-dlp/worker พังชั่วคราว ต้องอัปเดตไลบรารี
- **Risk:** polyfill เพิ่มขนาดไฟล์ อาจกระทบโหลดช้าเล็กน้อยบน 3G
- **Risk:** MediaSession ทุกโหมดอาจซ้ำซ้อนกับ YT controls ต้องเทสบน iOS จริง

## Impact

- เล่นได้ครอบคลุม Android/iOS/iPad/Desktop/LINE ภายใต้กฎ autoplay
- ลดจอดำ error 153/150/101 ด้วย fallback ตรงจุด
- ล็อกจอมีเสียงต่อได้ (audio fallback)
- เบราว์เซอร์เก่าไม่โดนบล็อกทิ้ง

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **Hybrid platform detection** - Lane A | Can run together: Task 6 | Must wait for: none | TDD slice: test HTML contains capability checks -> add JS -> verify
2. **Muted autoplay + overlay fallback** - Lane A | Can run together: none | Must wait for: Task 1 (same file) | TDD slice: test overlay logic -> implement muted attempt -> verify
3. **YT error mapping & host fallback** - Lane A | Can run together: none | Must wait for: Task 2 (same file) | TDD slice: test error 150/101/153 branches -> implement -> verify
4. **Audio fallback auto+manual & visibility handling** - Lane B | Can run together: Task 1, Task 6 | Must wait for: none (different JS block) | TDD slice: test ?audio + auto switch + visibilitychange -> implement -> verify
5. **MediaSession everywhere** - Lane B | Can run together: Task 4 | Must wait for: Task 4 (same audio block) | TDD slice: test MediaMetadata handlers -> implement -> verify
6. **Old-browser polyfill degrade** - Lane C | Can run together: Task 1 | Must wait for: none | TDD slice: test COMPAT_GUARD replaced -> add polyfills -> verify

---

### Task 1: Hybrid platform detection

**Files:**

- Modify: `music/templates/music/player.html:472-477`
- Test: `music/tests.py` (add `PlayerPageTests.test_hybrid_platform_detection`)

**Parallelization:**

- Can run with: `Task 6` or `none`
- Must wait for: `none`
- Race risk: `same file player.html` - do not run Task 2/3 in parallel with this

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code. This task must follow RED -> GREEN -> REFACTOR.

- [ ] **Step 1: Write the failing test**

```python
def test_hybrid_platform_detection(self):
    response = self.client.get('/')
    html = response.content.decode()
    self.assertIn('isIOS', html)
    self.assertIn('isAndroid', html)
    self.assertIn('capability', html.lower())  # or 'MediaSession' or 'canPlay'
    self.assertIn('maxTouchPoints', html)
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `& ".\venv\Scripts\python.exe" manage.py test music.tests.PlayerPageTests.test_hybrid_platform_detection -v 2`. Expected: FAIL missing capability token.

- [ ] **Step 3: Implement the minimal code**

In `player.html` keep `isIOS`/`isAndroid` UA checks and add capability probes:
```js
const cap = { mediaSession: 'mediaSession' in navigator, autoplayMuted: false, pip: 'pictureInPictureEnabled' in document };
const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
const isAndroid = /Android/i.test(navigator.userAgent);
const host = isIOS ? 'https://www.youtube.com' : 'https://www.youtube-nocookie.com';
```
Preserve `isIOS` host logic (Q4 A) and expose `cap` for later tasks. No other file changes.

- [ ] **Step 4: Run the test and confirm it passes**

Same command. Expected: PASS. Also run `manage.py test -v 1` and ensure no regression (151+ pass).

- [ ] **Step 5: Refactor only after green**

Extract detection into small helper `detectPlatform()` if desired. Rerun targeted test.

---

### Task 2: Muted autoplay + overlay fallback

**Files:**

- Modify: `music/templates/music/player.html:347-356, 611-687, 1139-1150` (sound-overlay + playNext)
- Test: `music/tests.py` (add `test_muted_autoplay_overlay`)

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1` (same file region)
- Race risk: `player.html` - sequential

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_muted_autoplay_overlay(self):
    html = self.client.get('/').content.decode()
    self.assertIn('sound-overlay', html)
    self.assertIn('handleOverlayTap', html)
    # new: muted autoplay attempt before overlay
    self.assertIn('mute', html.lower())
    self.assertIn('autoplay', html.lower())
```

- [ ] **Step 2: Run the test and confirm it fails**

Targeted test. Expected FAIL missing muted autoplay token if not yet added.

- [ ] **Step 3: Implement the minimal code**

In `playNext`/`init`: attempt `player.mute(); player.playVideo()` immediately on `onReady` (desktop). If `play` rejected or YT state not playing within 800ms, show `#sound-overlay`. Keep `handleOverlayTap` as single gesture to `unMute` + `play`. Do not re-add global `touchstart` listener. Respect `userInteracted`/`soundEnabled` flags.

- [ ] **Step 4: Run the test and confirm it passes**

Targeted + full suite `manage.py test`.

- [ ] **Step 5: Refactor only after green**

Clean timeouts, keep overlay CSS `hidden` default.

---

### Task 3: YT error mapping & host fallback

**Files:**

- Modify: `music/templates/music/player.html:850-853, 1093-1125` (onError + playNextNoApi host)
- Test: `music/tests.py` (add `test_yt_error_mapping`)

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 2`
- Race risk: `player.html` - sequential

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_yt_error_mapping(self):
    html = self.client.get('/').content.decode()
    self.assertIn('onError', html)
    self.assertIn('153', html)
    self.assertIn('150', html)
    self.assertIn('101', html)
    self.assertIn('audio', html.lower())
```

- [ ] **Step 2: Run the test and confirm it fails**

Targeted test FAIL missing 150/101.

- [ ] **Step 3: Implement the minimal code**

Expand `onError` handler:
- 153 -> if not yet triedNoApi, switch host `youtube.com` retry once else `playNextAudio`
- 150/101 (owner block) -> immediate `playNextAudio` via `/api/audio/?id=` then `skip` if audio also fails
- others -> toast + skip
Keep `window._triedNoApi` guard, add `window._triedHostSwitch` if needed. Update `playNextNoApi` to use hybrid host const.

- [ ] **Step 4: Run the test and confirm it passes**

Targeted + full suite.

- [ ] **Step 5: Refactor only after green**

De-dupe error handling, keep logs via `clog`.

---

### Task 4: Audio fallback auto+manual & visibility handling

**Files:**

- Modify: `music/templates/music/player.html:477, 1137, 1140-1141` (AUDIO_MODE, playNextAudio, visibilitychange)
- Modify: `music/views.py:1194` (audio_stream no logic change, just ensure cache/worker path covered)
- Test: `music/tests.py` (add `test_audio_fallback_and_visibility`)

**Parallelization:**

- Can run with: `Task 1`, `Task 6`
- Must wait for: `none` (JS block separate from Task1 host block, but if conflict merge with Task 3)
- Race risk: `player.html` vs `views.py` - low, coordinate if touching same lines

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_audio_fallback_and_visibility(self):
    html = self.client.get('/').content.decode()
    self.assertIn('AUDIO_MODE', html)
    self.assertIn('playNextAudio', html)
    self.assertIn('visibilitychange', html.lower())
    self.assertIn('/api/audio/', html)
```

- [ ] **Step 2: Run the test and confirm it fails**

Expect FAIL missing visibilitychange.

- [ ] **Step 3: Implement the minimal code**

Keep `AUDIO_MODE = new URLSearchParams(location.search).has('audio')` manual toggle. Auto path: error 150/101/153 -> `playNextAudio()`. Add `document.addEventListener('visibilitychange', () => { if(document.hidden && currentSong && player && !AUDIO_MODE) { /* keep playing, if YT pauses try audio */ } })`. Ensure `playNext` routes `if(AUDIO_MODE) return playNextAudio()` first. Views `audio_stream` unchanged except verify worker URL env still read.

- [ ] **Step 4: Run the test and confirm it passes**

Targeted + full suite. Manual check: `GET /api/audio/?id=ks7p6DA0dKk` returns 200 or cached.

- [ ] **Step 5: Refactor only after green**

Extract `switchToAudio()` helper.

---

### Task 5: MediaSession everywhere

**Files:**

- Modify: `music/templates/music/player.html:1137` (playNextAudio) + `playNext` YT path (add MediaSession after play)
- Test: `music/tests.py` (add `test_mediasession_everywhere`)

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 4` (same audio block)
- Race risk: `player.html` - sequential

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_mediasession_everywhere(self):
    html = self.client.get('/').content.decode()
    self.assertIn('mediaSession', html)
    self.assertIn('MediaMetadata', html)
    self.assertIn('setActionHandler', html)
    # should appear at least twice (audio + YT path)
    self.assertGreaterEqual(html.count('mediaSession'), 2)
```

- [ ] **Step 2: Run the test and confirm it fails**

FAIL if only one occurrence.

- [ ] **Step 3: Implement the minimal code**

Copy MediaSession setup from `playNextAudio` into YT `playNext` success path after `player.playVideo()`:
```js
if('mediaSession' in navigator){
  navigator.mediaSession.metadata = new MediaMetadata({title: currentSong.title, artist: 'ร้านยำปากเจ่อKPP', artwork: [{src: currentSong.thumbnail, sizes:'512x512', type:'image/jpeg'}]});
  navigator.mediaSession.setActionHandler('nexttrack', ()=>skipSong());
  navigator.mediaSession.setActionHandler('play', ()=>player.playVideo());
  navigator.mediaSession.setActionHandler('pause', ()=>player.pauseVideo());
}
```
Keep existing audio path. No views change.

- [ ] **Step 4: Run the test and confirm it passes**

Targeted + full suite.

- [ ] **Step 5: Refactor only after green**

Extract `updateMediaSession(song)` helper.

---

### Task 6: Old-browser polyfill degrade

**Files:**

- Modify: `music/templates/music/player.html:25` (COMPAT_GUARD)
- Test: `music/tests.py` (add `test_old_browser_polyfill`)

**Parallelization:**

- Can run with: `Task 1`
- Must wait for: `none`
- Race risk: `none` (head section)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` (docs/config exception allowed but still write test).

- [ ] **Step 1: Write the failing test**

```python
def test_old_browser_polyfill(self):
    html = self.client.get('/').content.decode()
    # old guard removed or softened, polyfill present
    self.assertIn('polyfill', html.lower())
    self.assertIn('fetch', html.lower())
    self.assertNotIn('COMPAT_GUARD: กรุณาอัปเดต', html)  # or softened message
```

- [ ] **Step 2: Run the test and confirm it fails**

FAIL missing polyfill.

- [ ] **Step 3: Implement the minimal code**

Replace hard block:
```html
<script>if(!window.fetch||!window.URLSearchParams||!window.Promise){...COMPAT_GUARD...}</script>
```
with polyfill CDN + soft degrade:
```html
<script src="https://polyfill.io/v3/polyfill.min.js?features=fetch,Promise,URLSearchParams"></script>
<script>if(!window.fetch||!window.URLSearchParams||!window.Promise){ /* show warning but still load */ console.warn('old browser'); }</script>
```
Keep Tailwind CDN and `type=module` fallback: add `nomodule` warning. No hard `innerHTML` wipe.

- [ ] **Step 4: Run the test and confirm it passes**

Targeted + full suite. Manual: test with old UA string does not wipe body.

- [ ] **Step 5: Refactor only after green**

Minify polyfill URL, keep CSP compatible.

---

## Verification

- `& ".\venv\Scripts\python.exe" manage.py test -v 1` -> 157+ pass (6 new tests)
- Manual matrix: Desktop Chrome/Edge, Android Chrome, iOS Safari, iPad, LINE WebView, Firefox
- Check: `GET /api/audio/?id=ks7p6DA0dKk` + `GET /api/hits/?player=1` + queue add/play
- PWA: manifest still served, no install prompt regression
