# Add to Playlist Button Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ปุ่ม เพิ่มลงเพลย์ลิสต์ ข้าง เล่น/ข้ามคิว ใน hits/search (Q130=A) + ยืนยันเล่นได้หลังแก้ 153

**Estimated tasks:** 2 | **Estimated time:** ~30 min | **Touches:** Frontend / API

## Current Problem / Current Solution

- hits/search มี `เล่น` + `เล่น (ข้ามคิว)` แต่ไม่มี `เพิ่มลงเพลย์ลิสต์` → ต้อง save ทั้งคิวเท่านั้น
- iOS hits 8 ขึ้นแต่เล่นดำ 153 — แก้ `a7150db` (iOS noapi) แล้ว ต้องยืนยันว่า `add-to-playlist` ไม่ทำให้ JS พังซ้ำ

## Proposed Approach

- hits/search: เพิ่มปุ่ม `เพิ่มลงเพลย์ลิสต์` (สี `slate-100`/`slate-700`) ข้าง `เล่น` → คลิก → dropdown เลือกเพลย์ลิสต์ที่มี (fetch `/api/playlists/`) + ช่อง `สร้างใหม่` → `POST /api/playlists/<id>/` เพิ่มเพลง `{id,title,channel,thumb,video_id}` เข้า `songs` → toast `เพิ่มลง <name> แล้ว`
- คง `playlist.js` API เดิม, เพิ่ม `addSongToPlaylist(playlistId, song)` helper
- ไม่แตะ `playNext`/`noapi` logic

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| เจอเพลงถูกใจ | กดเล่นทันทีเท่านั้น | กดเพิ่มลงเพลย์ลิสต์เก็บไว้ก่อน |
| เลือกเพลย์ลิสต์ | ไม่มี | dropdown + สร้างใหม่ |

## Assumptions & Risks

- **Assumed:** `playlist.js` async API พร้อมแล้ว (3033700), `song` มี `id/title/channel/thumbnail`
- **Risk:** dropdown บนมือถือบังปุ่ม → ใช้ `absolute` + `max-h-40 overflow-y`

## Impact

- แตะ `player.html` (hits/search render + dropdown + add logic) + `playlist.js` (addSong helper) + `tests.py`

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Add song helper]** - Lane A | Can run together: none | Must wait for: none | TDD slice: POST add song -> add helper -> `manage.py test`
2. **[Hits/search button + dropdown]** - Lane A | Can run together: none | Must wait for: Task 1 | TDD slice: button renders -> add UI -> `manage.py test` + manual

---

### Task 1: Add song helper

**Files:**

- Modify: `music/static/music/playlist.js` (add `addSongToPlaylist`), `music/views.py` (add `playlist_add_song` API if needed or reuse detail PUT)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `playlist.js` + `views.py`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

`POST /api/playlists/<id>/add-song/` with song -> 200 + playlist songs length +1

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test -v2`. Expected: FAIL 404.

- [ ] **Step 3: Implement the minimal code**

`views.py`: `def playlist_add_song(request, pk): @login_required POST {song} -> playlist.songs.append(song) -> save -> return`

`playlist.js`: `static async addSongToPlaylist(id, song){ return fetch(...).then }`

If `playlist_detail` PUT already handles full songs array, reuse: `addSong` = get + append + PUT.

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test`.

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 2: Hits/search button + dropdown

**Files:**

- Modify: `music/templates/music/player.html` (hits/search render + dropdown logic)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1`
- Race risk: `player.html`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` (manual).

- [ ] **Step 1: Write the failing test**

Manual: hits card has 3rd button `เพิ่มลงเพลย์ลิสต์` + click shows dropdown.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Check `player.html` no such button.

- [ ] **Step 3: Implement the minimal code**

`player.html`: `hitPlay`/`manualPlay` row add `<button onclick="openAddToPlaylist(${idx}, 'hit')">เพิ่มลงเพลย์ลิสต์</button>` + `<div id="add-dropdown-${idx}" class="hidden absolute ...">` with list from `await PlaylistManager.getAll()` + `onSelect` calls `addSongToPlaylist` + toast.

Keep `playNext` untouched.

- [ ] **Step 4: Run the test and confirm it passes**

`manage.py check` + manual click dropdown -> song added -> reload playlist sees it.

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.
