# Account Playlist + Header Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เพลย์ลิสต์ผูกบัญชี (DB per user) ข้ามเครื่องได้ + แก้ header โลโก้/ชื่อร้านซ้อนทับบนมือถือ (ย้ายปุ่มลงล่าง)

**Estimated tasks:** 4 | **Estimated time:** ~60 min | **Touches:** DB / API / Frontend

## Current Problem / Current Solution

- เพลย์ลิสต์เก็บ `localStorage ym_playlists_v1` → เปลี่ยนเครื่อง/ล้างแคชหาย ไม่ผูกบัญชี (user ถาม อยากจำกับบัญชี)
- Header `flex items-center gap-2` โลโก้ `w-14 h-14` + `h1 text-lg sm:text-2xl md:text-3xl` + ปุ่ม `เปลี่ยนทีม/เพลย์ลิสต์/ออก` ชิดขวา `ml-auto` → จอแคบ (<360px) ชื่อร้านยาว `ร้านยำปากเจ่อKPP` ไม่มีช่อง → ซ้อนทับ/logo ไม่กึ่งกลาง

## Proposed Approach

- **Playlist DB:** `Playlist` model `user FK + name unique_together + songs JSON (list of {id,title,channel,thumb,video_id,duration}) + created_at` → migration → API `GET /api/playlists/`, `POST /api/playlists/`, `PUT /api/playlists/<id>/`, `DELETE`, `POST /api/playlists/<id>/load/` (clear+add) → frontend `playlist.js` สลับจาก localStorage เป็น fetch (fallback localStorage ถ้า 401) → `player.html` ใช้ API
- **Header fix:** เปลี่ยน `<header>` เป็น `flex flex-wrap` + โลโก้ `flex-shrink-0` + ชื่อ `truncate` + ปุ่มรวมใน `div w-full sm:w-auto sm:ml-auto flex flex-wrap gap-2 justify-end` ย้ายลงล่างบนมือถือ, เพิ่ม `space` ระหว่าง `เจ่อ` และ `KPP`, ลด `text-lg` → `text-base sm:text-xl md:text-2xl` บนมือถือ, โลโก้ `aspect-square`

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| สร้างเพลย์ลิสต์แล้วเปลี่ยนเครื่อง | หาย | ยังอยู่ (login เดิม) |
| Header 320px | ชื่อทับปุ่ม | ปุ่มลงบรรทัดใหม่ ไม่ทับ |

## Assumptions & Risks

- **Assumed:** ใช้ `request.user` ที่ login แล้ว (player บังคับ login), `GET /api/playlists/` ต้อง auth
- **Assumed:** ย้าย localStorage → DB ครั้งแรก: ถ้า user มี local playlists ให้ sync ขึ้น server ครั้งแรก (POST ทีละอัน) แล้วลบ local
- **Risk:** migration เพิ่มตาราง → ต้อง `migrate` บน Render (auto)
- **Risk:** Header flex-wrap อาจดันสูงขึ้น 1 บรรทัดบนมือถือ → รับได้

## Impact

- แตะ `models.py` + `migrations` + `views.py` + `urls.py` + `playlist.js` + `player.html` + `tests.py`

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Playlist model + API]** - Lane A | Can run together: Task 3 | Must wait for: none | TDD slice: GET /api/playlists/ 401 anon, 200 auth -> add model+API -> `manage.py test`
2. **[Frontend switch to API]** - Lane A | Can run together: none | Must wait for: Task 1 | TDD slice: create via API -> update playlist.js -> `manage.py test` + manual
3. **[Header/logo fix]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: header wraps -> edit player.html -> `manage.py check`
4. **[Migrate localStorage + tests]** - Sequential | Can run together: none | Must wait for: Task 1,2 | TDD slice: old local syncs -> add migration test -> `manage.py test`

---

### Task 1: Playlist model + API

**Files:**

- Modify: `music/models.py` (add Playlist), `music/views.py` (add 4 API views), `music/urls.py`
- Create: `music/migrations/0005_playlist.py`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 3`
- Must wait for: `none`
- Race risk: `music/models.py` + `views.py` (single lane)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_playlists_require_login(self): self.client.get('/api/playlists/') -> 302 or 401
def test_create_playlist(self): login staff POST /api/playlists/ name="My" -> 201 + DB exists
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL 404.

- [ ] **Step 3: Implement the minimal code**

`models.py`: `class Playlist(models.Model): user=FK(User), name, songs=JSONField(default=list), created_at, unique_together`

`views.py`: `@login_required def playlist_list`, `playlist_create`, `playlist_update`, `playlist_delete` + `playlist_load` (clear+add) — JSON, check owner

`urls.py`: 4 paths `api/playlists/...`

`migrate` -> `makemigrations` + `migrate`

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test` + `check`.

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 2: Frontend switch to API

**Files:**

- Modify: `music/static/music/playlist.js` (fetch API, fallback), `music/templates/music/player.html` (use API)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1`
- Race risk: `playlist.js` shared

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` (manual verify).

- [ ] **Step 1: Write the failing test**

Manual: login, create playlist via UI -> appears after reload on same account, not on other account.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

LocalStorage only -> not cross-device.

- [ ] **Step 3: Implement the minimal code**

`playlist.js`: `getAll()` → `fetch('/api/playlists/')` (if 401 fallback local), `save()` → `POST`, `delete()` → `DELETE`, etc., keep `window.PlaylistManager` API same.

`player.html`: `renderPlaylistPanel` uses async fetch, `loadPlaylist` calls `/api/playlists/<id>/load/`.

- [ ] **Step 4: Run the test and confirm it passes**

Manual + `manage.py test` green.

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 3: Header/logo fix

**Files:**

- Modify: `music/templates/music/player.html` (header)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 1`
- Must wait for: `none`
- Race risk: `player.html` shared with Task 2 — Task 2 waits

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` (visual).

- [ ] **Step 1: Write the failing test**

Visual: header at 320px should not overlap (manual) or `player.html` contains `flex-wrap`.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Check `player.html` has `flex items-center gap-2` without wrap.

- [ ] **Step 3: Implement the minimal code**

Header: `<header class="flex flex-wrap items-center gap-2 sm:gap-3 mb-4">` + logo `flex-shrink-0 aspect-square` + title `flex-1 min-w-0 truncate` + `h1` add space `ร้านยำปากเจ่อ KPP` + `text-base sm:text-xl md:text-2xl` + buttons wrapper `<div class="w-full sm:w-auto sm:ml-auto flex flex-wrap gap-2 justify-end sm:justify-start mt-2 sm:mt-0">` with 3 buttons + user/logout.

- [ ] **Step 4: Run the test and confirm it passes**

`manage.py check` + visual at 320px.

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 4: Migrate localStorage + tests

**Files:**

- Modify: `music/tests.py`, `music/static/music/playlist.js` (sync once)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1,2`
- Race risk: `tests.py` shared

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

`test_migrate_local_to_account`: old local playlists sync to DB after login.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test`. Expected: FAIL.

- [ ] **Step 3: Implement the minimal code**

`playlist.js`: on load if `localStorage ym_playlists_v1` exists and user authenticated, POST each to `/api/playlists/` then clear local. Add `GET /api/playlists/` merge.

`tests.py`: add test.

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test` 90+ → all PASS + `check`.

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.
