# Player Page Fixes & Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix YouTube embed errors (Error 153), skip button race condition, and redesign player page idle/queue states per user requirements.

**Estimated tasks:** 4 | **Estimated time:** ~60 min | **Touches:** Frontend (player.html) / Tests

## Current Problem / Current Solution

- **YouTube embed errors:** Test videos (jNQXAC9IVRw, dQw4w9WgXcQ) return Error 153 "Video player configuration error" — embedding disabled by video owner. Current `onError: () => skipSong()` exists but needs verification.
- **Skip button race:** `skipSong()` → `removePlayedSong()` → `fetchQueue()` timing causes "press skip but next song doesn't play" intermittently.
- **Idle screen (no songs):** Currently shows logo.jpg + QR + text in dark gradient. User wants banner with 2 images (1.png, 2.jpg) full width + branding text + QR.
- **Queue exists state:** Video area shows black background. User wants white background + centered overlay text "ยำปากเจ่อกำแพงเพชรอร่อยถูกดีอันดับ1" before video loads.
- **Logo:** Header logo small; idle uses logo.jpg. User wants header logo bigger with shadow/border; idle uses 1.png, 2.jpg.

## Proposed Approach

1. **Error handling:** Enhance `onError` to distinguish Error 153 (embed disabled) from transient errors. On Error 153, skip immediately. On other errors, retry once then skip.
2. **Skip race fix:** Ensure `removePlayedSong()` calls `fetchQueue()` in `finally` block after API completes. Add `finishingSongIds` guard (already present) to prevent double-processing.
3. **Idle screen redesign:** Replace current idle-splash with banner grid (2 images full width) + branding text + QR, matching template-redesign.md light theme.
4. **Queue background:** Add conditional CSS class on video container: white background + centered overlay text when `queue.length > 0 && !currentSong`. Remove overlay when video starts playing.
5. **Logo updates:** Header logo larger with ring/shadow; idle-splash uses 1.png and 2.jpg via `{% static %}` with onerror fallback.

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| No songs (idle) | Dark gradient, logo.jpg + QR + small text | Light theme banner: 1.png + 2.jpg full width, large branding text, QR |
| Queue exists, no current song | Black video area, "รอเพลงจากลูกค้า..." | White video area, centered overlay "ยำปากเจ่อกำแพงเพชรอร่อยถูกดีอันดับ1" |
| Video starts playing | Overlay hidden via `idle-splash.hidden` | Overlay hidden, video plays normally |
| YouTube Error 153 (embed disabled) | skipSong() called, may loop if next also fails | Detect Error 153, skip immediately, log warning |
| Skip button pressed | Race: fetchQueue may run before /api/played completes | finishingSongIds guard + fetchQueue in finally ensures next song loads |

## Assumptions & Risks

- **Assumed:** Static files `1.png` and `2.jpg` exist at `music/static/music/img/` (per template-redesign.md Task 4). If missing, onerror fallback hides them.
- **Assumed:** YouTube Error 153 is the only embed-disabled error code; other codes (2, 5, 100, 101, 150) may be transient.
- **Risk:** If all videos in queue have embedding disabled, player will skip through entire queue rapidly. Mitigation: add max-skip limit or user notification.
- **Risk:** Template changes must preserve all existing IDs and JS handlers for test contract (12 tests in music/tests.py).

## Impact

- `music/templates/music/player.html` — visual rewrite + JS error handling + conditional rendering
- `music/tests.py` — may need updates for new idle-splash structure (banner images, text content)
- Server restart required after template changes (Django caches templates per process)

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Enhance YouTube error handling]** - Lane A | Can run together: Task 2 | Must wait for: none | TDD slice: Write test for onError behavior -> implement error code detection -> verify skip on Error 153
2. **[Fix skip button race condition]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: Write test for skip->next flow -> ensure fetchQueue in finally -> verify no stuck state
3. **[Redesign idle screen & queue background]** - Lane C | Can run together: Task 1, Task 2 | Must wait for: none | TDD slice: Existing PlayerPageTests as regression -> rewrite idle-splash + add queue overlay -> tests GREEN
4. **[Update logo & verify full suite]** - Sequential | Can run together: none | Must wait for: Task 1, Task 2, Task 3 | TDD slice: Run full test suite -> restart server -> HTTP verify both pages

---

### Task 1: Enhance YouTube error handling (Error 153)

**Files:**
- Modify: `music/templates/music/player.html` (JS section: onError handler)
- Test: `music/tests.py` (PlayerPageTests — regression)

**Parallelization:**
- Can run with: `Task 2`
- Must wait for: `none`
- Race risk: `none` (only touches onError handler in player.html)

- [ ] **Step 0: Load the TDD discipline**
  Use `superpowers:test-driven-development` before editing production code.

- [ ] **Step 1: Write the failing test**
  Add a test to verify `onError` handler exists and handles error codes. Since we can't easily unit-test YouTube iframe events, verify the JS code contains the enhanced handler via template render test:
  ```python
  def test_player_has_enhanced_onerror_handler(self):
      response = self.client.get('/')
      self.assertContains(response, 'onError')
      self.assertContains(response, '153')  # Error 153 handling
  ```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**
  `python manage.py test music.tests.PlayerPageTests.test_player_has_enhanced_onerror_handler` → FAIL (handler not yet enhanced)

- [ ] **Step 3: Implement the minimal code**
  In `player.html`, replace the `onError: () => skipSong()` with enhanced handler:
  ```js
  'onError': (event) => {
      // Error 153 = embedding disabled by video owner
      // Other codes (2, 5, 100, 101, 150) may be transient
      if (event.data === 153) {
          console.warn('Video embedding disabled (Error 153), skipping:', currentSong?.title);
          skipSong();
      } else {
          console.warn('YouTube player error:', event.data, 'retrying once...');
          // Retry once by reloading the same video
          if (currentSong && !window._retryCount) {
              window._retryCount = 1;
              player.loadVideoById(currentSong.video_id);
          } else {
              window._retryCount = 0;
              skipSong();
          }
      }
  }
  ```

- [ ] **Step 4: Run the test and confirm it passes**
  `python manage.py test music.tests.PlayerPageTests.test_player_has_enhanced_onerror_handler` → PASS

- [ ] **Step 5: Refactor only after green**
  Verify full test suite: `python manage.py test music` → 12/12 OK

---

### Task 2: Fix skip button race condition

**Files:**
- Modify: `music/templates/music/player.html` (JS: removePlayedSong function)
- Test: `music/tests.py` (PlayerPageTests — regression)

**Parallelization:**
- Can run with: `Task 1`
- Must wait for: `none`
- Race risk: `none` (only touches removePlayedSong in player.html)

- [ ] **Step 0: Load the TDD discipline**
  Use `superpowers:test-driven-development` before editing production code.

- [ ] **Step 1: Write the failing test**
  Add test verifying `removePlayedSong` calls `fetchQueue` in finally block:
  ```python
  def test_player_removeplayed_calls_fetchqueue_in_finally(self):
      response = self.client.get('/')
      self.assertContains(response, 'finishingSongIds')
      self.assertContains(response, 'finally')
      self.assertContains(response, 'fetchQueue()')
  ```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**
  `python manage.py test music.tests.PlayerPageTests.test_player_removeplayed_calls_fetchqueue_in_finally` → FAIL (finally block may not have fetchQueue)

- [ ] **Step 3: Implement the minimal code**
  In `player.html`, ensure `removePlayedSong` has `fetchQueue()` in `finally` block (already present in current code at line 220). Verify the structure:
  ```js
  function removePlayedSong(songId) {
      if (!songId || finishingSongIds.has(songId)) return;
      finishingSongIds.add(songId);
      if (currentSong && currentSong.id === songId) currentSong = null;
      fetch(`/api/played/${songId}/`)
          .then(() => fetchQueue())
          .catch(err => console.error('Unable to finish song:', err))
          .finally(() => {
              finishingSongIds.delete(songId);
              if (!currentSong && isPlayerReady) fetchQueue();
          });
  }
  ```
  The current code already has this pattern. Verify it's correct and add test assertion.

- [ ] **Step 4: Run the test and confirm it passes**
  `python manage.py test music.tests.PlayerPageTests.test_player_removeplayed_calls_fetchqueue_in_finally` → PASS

- [ ] **Step 5: Refactor only after green**
  Verify full test suite: `python manage.py test music` → 12/12 OK

---

### Task 3: Redesign idle screen & queue background overlay

**Files:**
- Modify: `music/templates/music/player.html` (HTML: idle-splash, video container; JS: playNext, renderQueue)
- Test: `music/tests.py` (PlayerPageTests — regression contract)

**Parallelization:**
- Can run with: `Task 1`, `Task 2`
- Must wait for: `none`
- Race risk: `none` (only touches player.html, different sections)

- [ ] **Step 0: Load the TDD discipline**
  Use `superpowers:test-driven-development` before editing production code.

- [ ] **Step 1: Run existing tests and confirm baseline**
  `python manage.py test music.tests.PlayerPageTests` → 7/7 PASS (current baseline)

- [ ] **Step 2: Implement the minimal code**
  Rewrite the video container section (lines 40-49) and idle-splash (lines 44-48) per design:

  **Video container with conditional queue overlay:**
  ```html
  <div class="aspect-video bg-black rounded-2xl overflow-hidden shadow-xl relative border border-slate-200" id="video-container">
      <div id="player" class="w-full h-full"></div>

      <!-- Queue overlay: shows when queue exists but no current song -->
      <div id="queue-overlay" class="absolute inset-0 z-10 hidden flex-col items-center justify-center bg-white p-4">
          <p class="text-2xl md:text-4xl font-extrabold text-amber-700 text-center">
              ยำปากเจ่อกำแพงเพชรอร่อยถูกดีอันดับ1
          </p>
      </div>

      <!-- Idle splash: shows when no queue AND no current song -->
      <div id="idle-splash" class="absolute inset-0 z-20 flex flex-col items-center justify-center gap-3 md:gap-4 bg-gradient-to-br from-white/95 to-amber-50/95 p-4 text-center">
          <div class="grid grid-cols-2 gap-3 w-full max-w-2xl mx-auto">
              <img src="{% static 'music/img/1.png' %}" alt="ร้านยำปากเจ่อ" class="w-full h-48 object-cover rounded-2xl ring-2 ring-amber-400/60 shadow-xl" onerror="this.style.display='none'">
              <img src="{% static 'music/img/2.jpg' %}" alt="ร้านยำปากเจ่อ" class="w-full h-48 object-cover rounded-2xl ring-2 ring-amber-400/60 shadow-xl" onerror="this.style.display='none'">
          </div>
          <img src="/qr.png" class="w-28 h-28 md:w-36 md:h-36 rounded-xl bg-white p-1 shadow-lg border border-slate-200" alt="QR Code">
          <p class="text-xl md:text-3xl font-extrabold text-amber-600">สแกน QR เพื่อขอเพลง</p>
          <p class="text-xs md:text-sm text-slate-500">รอเพลงจากลูกค้า...</p>
      </div>
  </div>
  ```

  **Update `playNext()` to manage overlays:**
  ```js
  function playNext() {
      const next = queue.find(song => !finishingSongIds.has(song.id));
      const videoContainer = document.getElementById('video-container');
      const queueOverlay = document.getElementById('queue-overlay');
      const idleSplash = document.getElementById('idle-splash');

      if (next) {
          if (currentSong && currentSong.id === next.id) return;
          currentSong = next;
          lastPlayedVideoId = next.video_id;
          document.getElementById('now-playing-title').innerText = currentSong.title;
          idleSplash.classList.add('hidden');
          queueOverlay.classList.add('hidden');
          videoContainer.classList.remove('bg-white');
          videoContainer.classList.add('bg-black');
          player.loadVideoById(currentSong.video_id);
          player.mute();
          player.playVideo();
          player.unMute();
      } else {
          currentSong = null;
          lastPlayedVideoId = null;
          document.getElementById('now-playing-title').innerText = "รอเพลงจากลูกค้า...";
          idleSplash.classList.remove('hidden');
          if (queue.length > 0) {
              queueOverlay.classList.remove('hidden');
              videoContainer.classList.remove('bg-black');
              videoContainer.classList.add('bg-white');
          } else {
              queueOverlay.classList.add('hidden');
              videoContainer.classList.remove('bg-white');
              videoContainer.classList.add('bg-black');
          }
      }
  }
  ```

  **Update `fetchQueue()` to show/hide queue overlay on poll:**
  ```js
  function fetchQueue(onDone) {
      fetch('/api/queue/')
          .then(res => res.json())
          .then(data => {
              queue = data.queue;
              document.getElementById('queue-count').innerText = queue.length;
              renderQueue();

              const videoContainer = document.getElementById('video-container');
              const queueOverlay = document.getElementById('queue-overlay');
              const idleSplash = document.getElementById('idle-splash');

              if (isPlayerReady && !currentSong && queue.length > 0) {
                  playNext();
              } else if (!currentSong) {
                  // No current song, update overlays based on queue
                  if (queue.length > 0) {
                      idleSplash.classList.add('hidden');
                      queueOverlay.classList.remove('hidden');
                      videoContainer.classList.remove('bg-black');
                      videoContainer.classList.add('bg-white');
                  } else {
                      idleSplash.classList.remove('hidden');
                      queueOverlay.classList.add('hidden');
                      videoContainer.classList.remove('bg-white');
                      videoContainer.classList.add('bg-black');
                  }
              }
              if (onDone) onDone();
          })
          .catch(err => console.error(err));
  }
  ```

  **Update header logo (line 29):**
  ```html
  <img src="{% static 'music/img/logo.jpg' %}" alt="ร้านยำปากเจ่อ" class="w-14 h-14 sm:w-16 sm:h-16 md:w-20 md:h-20 object-cover rounded-xl ring-4 ring-amber-400/60 shadow-xl" onerror="this.style.display='none'">
  ```

- [ ] **Step 3: Run the test and confirm it passes**
  `python manage.py test music.tests.PlayerPageTests` → 7/7 PASS

- [ ] **Step 4: Run full test suite**
  `python manage.py test music` → 12/12 PASS

- [ ] **Step 5: Refactor only after green**
  Verify no dead code, all IDs preserved.

---

### Task 4: Update logo, restart server, verify both pages

**Files:**
- None (ops verification only)

**Parallelization:**
- Can run with: `none`
- Must wait for: `Task 1`, `Task 2`, `Task 3`
- Race risk: `none`

- [ ] **Step 1: Clean restart procedure**
  ```powershell
  Get-Process python* | Stop-Process -Force
  Start-Sleep -Seconds 3
  Get-NetTCPConnection -LocalPort 8000 -State Listen  # must be EMPTY
  Start-Process -FilePath "C:\Users\TITLE\OneDrive\เอกสาร\mysong\venv\Scripts\python.exe" -ArgumentList "manage.py","runserver","0.0.0.0:8000","--noreload" -WorkingDirectory "C:\Users\TITLE\OneDrive\เอกสาร\mysong" -WindowStyle Hidden -RedirectStandardOutput "C:\Users\TITLE\AppData\Local\Temp\opencode\server_final.log" -RedirectStandardError "C:\Users\TITLE\AppData\Local\Temp\opencode\server_final_err.log"
  Start-Sleep -Seconds 6
  ```

- [ ] **Step 2: Verify listening + content**
  - `Get-NetTCPConnection -LocalPort 8000 -State Listen` → one PID listening
  - `Invoke-WebRequest http://127.0.0.1:8000/` → HTTP 200 AND body contains: `Kanit`, `amber`, `logo.jpg`, `id="queue-overlay"`, `id="idle-splash"`, `1.png`, `2.jpg`, `ยำปากเจ่อกำแพงเพชรอร่อยถูกดีอันดับ1`, `wakeLock`
  - `Invoke-WebRequest http://127.0.0.1:8000/request/` → HTTP 200 AND body contains: `Kanit`, `amber`, `logo.jpg`, `id="noSleepBtn"`, `nosleep.js`
  - Full suite: `python manage.py test music` → `Ran 12 tests ... OK`

- [ ] **Step 3: Manual verification (optional but recommended)**
  - Open `/` in browser: verify idle screen shows 2-image banner + QR + text
  - Add song via `/request/`: verify queue overlay appears (white bg + text) then video plays
  - Test skip button: verify next song loads without stuck state
  - Test Error 153: add video with embedding disabled → verify auto-skip to next

- [ ] **Step 4: Report**
  Report: what changed (player.html error handling, skip race fix, idle redesign, queue overlay, logo), verification results (HTTP 200 both pages, new tokens present, 12/12 GREEN), and residual risk (Error 153 handling untested with real restricted videos; static images 1.png/2.jpg must be placed by user).

---

## Final Gate

- [ ] `python manage.py test music` — ทุกเทส PASS (ทั้ง PlayerPageTests และ RequestPageTests)
- [ ] `music/static/music/img/` มีรูป 1.png, 2.jpg (หรือแจ้งผู้ใช้ว่าให้วางรูปก่อนดูผลเต็ม)
- [ ] Manual check: `python manage.py runserver 0.0.0.0:8000` → เปิด `/` (ตรวจ idle banner, queue overlay) และ `/request/` (ตรวจ hero)
- [ ] ห้าม commit/push (โปรเจคไม่ใช่ git repo)