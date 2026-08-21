# Template Redesign (Light + Kanit + Gold) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign both Django templates (`player.html`, `request.html`) from the current dark pink/purple neon look to a clean light theme with Kanit font and gold/amber accents, while preserving every functional ID, JS handler, and the 12-test contract.

**Estimated tasks:** 3 | **Estimated time:** ~30 min | **Touches:** Frontend (templates only — no views/urls/models changes)

## Current Problem / Current Solution

Both templates currently use a dark neon style: `player.html` is slate-950→pink-950 gradient with pink/rose accents; `request.html` is purple-950→pink-950 gradient. The user asked (Thai): "ทำการออกเเบบตกเเต่งหน้าเทรมเเพรตไหม่ทั้งหมดไห้ดูเป็นทางการมากกว่านี้" (redesign all template pages to look more formal/professional). Via grill-design the user chose: **B - Light สว่างสะอาด** (clean bright light theme), **C - Kanit** font, **A - ทอง/อำพัน** (gold/amber) accent color.

## Proposed Approach

Rewrite the visual layer of both templates only. Keep every functional element byte-compatible with the existing tests and JS:

- All IDs: `player`, `idle-splash`, `now-playing-title`, `queue-list`, `queue-count`, `userName`, `searchInput`, `results`, `loading`, `noSleepBtn`
- All JS handlers: `clearQueue` + button text `รีคิวเพลง`, `skipSong`, `requestWakeLock`/`wakeLock`, `fetchQueue`, `playNext`, `removePlayedSong`, `renderQueue`, `setInterval(fetchQueue, 3000)`, `searchMusic`, `requestSong(idx)` with `searchResults` array, `toggleNoSleep`, `autoEnableNoSleep`
- Assets: `{% static 'music/img/logo.jpg' %}` (logo), `src="/qr.png"` (QR), NoSleep CDN `https://cdn.jsdelivr.net/npm/nosleep.js@0.12.0/dist/NoSleep.min.js`
- Emoji: 🎵 kept in headings

### SHARED DESIGN CONTRACT (both pages — must match exactly)

- **Font:** Google Fonts Kanit — `<link href="https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">`; `tailwind.config = { theme: { extend: { fontFamily: { sans: ['Kanit', 'sans-serif'] } } } }`
- **Background:** light warm gradient `bg-gradient-to-br from-slate-50 via-white to-amber-50` on body
- **Text:** headings `text-slate-900`, body `text-slate-600`, muted `text-slate-400/500`
- **Accent (gold/amber):** buttons `bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-600 hover:to-yellow-600`, accent text `text-amber-600`, rings `ring-amber-400/50`
- **Cards:** `bg-white shadow-md border border-slate-200 rounded-2xl`
- **Logo frame:** `rounded-xl ring-2 ring-amber-400/50 shadow-md`
- **YouTube video area:** keep dark (`bg-black`) — video itself is dark; idle-splash overlay becomes light-themed (white/amber gradient) but keeps logo.jpg + "🎵 สแกน QR เพื่อขอเพลง" + `/qr.png`

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| Player page look | Dark slate/pink neon gradient | Clean light white/amber gradient, gold accents, Kanit |
| Request page look | Dark purple/pink neon gradient | Clean light white/amber gradient, gold accents, Kanit |
| Functionality | All IDs/JS/buttons working | Identical — visual layer only |
| Tests | 12/12 GREEN | 12/12 GREEN (unchanged contract) |

## Assumptions & Risks

- **Assumed:** The 12 existing tests in `music/tests.py` are the complete functional contract; no test changes needed.
- **Assumed:** No views.py/urls.py/models.py changes required (visual-only).
- **Assumed:** Server must be restarted after template changes (Django caches templates per process — established in prior rounds).
- **Risk:** If a required token (ID, button text, emoji, asset path) is dropped during rewrite, tests fail — mitigated by running the full test suite after each template change.
- **Risk:** Sub-agents cannot write non-.md files directly (permission config). All template content MUST be written to `C:\Users\TITLE\AppData\Local\Temp\opencode\*.md` then copied with `Copy-Item -Force` to the real destination to preserve UTF-8 Thai.

## Impact

- `music/templates/music/player.html` — full visual rewrite (light/gold/Kanit)
- `music/templates/music/request.html` — full visual rewrite (light/gold/Kanit)
- `music/tests.py` — unchanged
- Server restart + HTTP verification after both templates land

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **Redesign player.html (light/gold/Kanit)** - Lane A | Can run together: Task 2 | Must wait for: none | TDD slice: existing PlayerPageTests (7 tests) as regression contract -> rewrite visual layer keeping all IDs/JS -> `manage.py test music` GREEN
2. **Redesign request.html (light/gold/Kanit)** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: existing RequestPageTests (4 tests) as regression contract -> rewrite visual layer keeping all IDs/JS -> `manage.py test music` GREEN
3. **Restart server + verify both pages** - Sequential | Can run together: none | Must wait for: Task 1, Task 2 | TDD slice: n/a (ops verification) -> clean restart procedure -> fetch `/` and `/request/` and assert new tokens (Kanit, amber, logo.jpg, all IDs) + full test suite GREEN

---

### Task 1: Redesign player.html (light/gold/Kanit)

**Files:**

- Modify: `music/templates/music/player.html` (full rewrite of visual layer)
- Test: `music/tests.py` (unchanged — regression contract)

**Parallelization:**

- Can run with: `Task 2` (different file, no race)
- Must wait for: `none`
- Race risk: `none` (only touches player.html)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code. This task is a visual rewrite guarded by the existing test contract: the 7 `PlayerPageTests` must stay GREEN. Run `& "C:\Users\TITLE\OneDrive\เอกสาร\mysong\venv\Scripts\python.exe" manage.py test music` first to confirm the current baseline is 12/12 GREEN.

- [ ] **Step 1: Write the failing test**

No new test needed — the existing `PlayerPageTests` are the contract. They assert: page renders 200, contains `LOGO='/static/music/img/logo.jpg'`, does NOT contain `2.png`/`2.jpg`, contains `id="idle-splash"`, contains `id="player"`, `id="queue-list"`, `id="queue-count"`, `id="now-playing-title"`, `src="/qr.png"`, contains `clearQueue` + `รีคิวเพลง`, contains `wakeLock`.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Baseline check: run the full suite — expected 12/12 OK before any change (this confirms the contract is intact and the test command works).

- [ ] **Step 3: Implement the minimal code**

Rewrite `music/templates/music/player.html` visual layer per the SHARED DESIGN CONTRACT. Write the full new template to `C:\Users\TITLE\AppData\Local\Temp\opencode\player_light.md` then `Copy-Item -LiteralPath "C:\Users\TITLE\AppData\Local\Temp\opencode\player_light.md" -Destination "C:\Users\TITLE\OneDrive\เอกสาร\mysong\music\templates\music\player.html" -Force`.

MUST KEEP (verbatim behavior):
- `{% load static %}` + `{% static 'music/img/logo.jpg' %}` in header AND idle-splash
- `id="player"` div + YT iframe API script + `onYouTubeIframeAPIReady` with `autoplay:1, playsinline:1, origin: window.location.origin`
- `id="idle-splash"` overlay containing logo.jpg + text `🎵 สแกน QR เพื่อขอเพลง` + `src="/qr.png"`
- `id="now-playing-title"` + ข้ามเพลง button calling `skipSong()`
- QR card with `src="/qr.png"`
- Queue card: `id="queue-count"`, `id="queue-list"`, รีคิวเพลง button calling `clearQueue()`
- Full JS: `requestWakeLock()`/`wakeLock` + visibilitychange re-request, `fetchQueue`, `playNext`, `skipSong`, `clearQueue` (confirm + POST /api/clear/), `removePlayedSong`, `renderQueue`, `setInterval(fetchQueue, 3000)`
- Title text `🎵 ร้านยำปากเจ่อ - ระบบคิวเพลง` + subtitle `ระบบคิวเพลงอัตโนมัติสำหรับลูกค้า`

- [ ] **Step 4: Run the test and confirm it passes**

Run `& "C:\Users\TITLE\OneDrive\เอกสาร\mysong\venv\Scripts\python.exe" manage.py test music`. Expected: `Ran 12 tests ... OK`.

- [ ] **Step 5: Refactor only after green**

No refactor needed beyond the rewrite. Re-run the suite once more if any cleanup happened.

---

### Task 2: Redesign request.html (light/gold/Kanit)

**Files:**

- Modify: `music/templates/music/request.html` (full rewrite of visual layer)
- Test: `music/tests.py` (unchanged — regression contract)

**Parallelization:**

- Can run with: `Task 1` (different file, no race)
- Must wait for: `none`
- Race risk: `none` (only touches request.html)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code. This task is a visual rewrite guarded by the existing test contract: the 4 `RequestPageTests` must stay GREEN.

- [ ] **Step 1: Write the failing test**

No new test needed — existing `RequestPageTests` are the contract: page renders 200, contains `LOGO`, does NOT contain `2.png`/`2.jpg`, contains `id="userName"`, `id="searchInput"`, `id="results"`, `id="loading"`.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Baseline check: run the full suite — expected 12/12 OK before any change.

- [ ] **Step 3: Implement the minimal code**

Rewrite `music/templates/music/request.html` visual layer per the SHARED DESIGN CONTRACT. Write the full new template to `C:\Users\TITLE\AppData\Local\Temp\opencode\request_light.md` then `Copy-Item -LiteralPath "C:\Users\TITLE\AppData\Local\Temp\opencode\request_light.md" -Destination "C:\Users\TITLE\OneDrive\เอกสาร\mysong\music\templates\music\request.html" -Force`.

MUST KEEP (verbatim behavior):
- `{% load static %}` + `{% static 'music/img/logo.jpg' %}` in header
- Title `🎵 ร้านยำปากเจ่อ`
- `id="userName"` input, `id="searchInput"` input, ค้นหา button calling `searchMusic()`, `id="loading"` div, `id="results"` div
- JS: `let searchResults = []`, `searchMusic()` (fetch `/api/search/?q=...`, render results with `onclick="requestSong(${idx})"`), `requestSong(idx)` (looks up `searchResults[idx]`, POST `/api/add/` with `requested_by` from userName, `.catch()` error handling)
- `id="noSleepBtn"` floating button + NoSleep CDN `https://cdn.jsdelivr.net/npm/nosleep.js@0.12.0/dist/NoSleep.min.js` + `toggleNoSleep()` + `autoEnableNoSleep()` (first touchstart/click)
- Body needs bottom padding (`pb-24` or similar) so the floating NoSleep button never covers content

- [ ] **Step 4: Run the test and confirm it passes**

Run `& "C:\Users\TITLE\OneDrive\เอกสาร\mysong\venv\Scripts\python.exe" manage.py test music`. Expected: `Ran 12 tests ... OK`.

- [ ] **Step 5: Refactor only after green**

No refactor needed beyond the rewrite. Re-run the suite once more if any cleanup happened.

---

### Task 3: Restart server + verify both pages

**Files:**

- None (ops verification only)

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1`, `Task 2` (both templates must be in place)
- Race risk: `none`

- [ ] **Step 1: Clean restart procedure**

```
Get-Process python* | Stop-Process -Force
Start-Sleep -Seconds 3
# verify: Get-NetTCPConnection -LocalPort 8000 -State Listen -> must be EMPTY ("PORT FREE")
Start-Process -FilePath "C:\Users\TITLE\OneDrive\เอกสาร\mysong\venv\Scripts\python.exe" -ArgumentList "manage.py","runserver","0.0.0.0:8000","--noreload" -WorkingDirectory "C:\Users\TITLE\OneDrive\เอกสาร\mysong" -WindowStyle Hidden -RedirectStandardOutput "C:\Users\TITLE\AppData\Local\Temp\opencode\server_final.log" -RedirectStandardError "C:\Users\TITLE\AppData\Local\Temp\opencode\server_final_err.log"
Start-Sleep -Seconds 6
```

- [ ] **Step 2: Verify listening + content**

- `Get-NetTCPConnection -LocalPort 8000 -State Listen` → one PID listening
- `Invoke-WebRequest http://127.0.0.1:8000/` → HTTP 200 AND body contains: `Kanit`, `amber`, `logo.jpg`, `id="queue-list"`, `รีคิวเพลง`, `wakeLock`
- `Invoke-WebRequest http://127.0.0.1:8000/request/` → HTTP 200 AND body contains: `Kanit`, `amber`, `logo.jpg`, `id="noSleepBtn"`, `nosleep.js`
- Full suite: `& "C:\Users\TITLE\OneDrive\เอกสาร\mysong\venv\Scripts\python.exe" manage.py test music` → `Ran 12 tests ... OK`

- [ ] **Step 3: Report**

Report: what changed (both templates restyled), verification results (HTTP 200 both pages, new tokens present, 12/12 GREEN), and residual risk (visual polish is subjective — user should eyeball both pages on the TV/phone).