# Playlist Edit + Search Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เพิ่มให้แก้ไขเพลย์ลิสต์ได้ (inline rename มีแล้ว เพิ่มดู/ลบเพลงในเพลย์ลิสต์) และแก้ค้นหาให้คำค้นแล้วเจอเพลงแม้ API ตาย (fallback ยืดหยุ่น + แนะนำ 3 เพลง)

**Estimated tasks:** 3 | **Estimated time:** ~45 min | **Touches:** API (views.py) / Frontend (player.html, playlist.js) / Tests

## Current Problem / Current Solution

- **Playlist:** Backend `playlist_detail PUT` และ `playlist.js rename/delete/addSong` มีแล้ว Frontend `player.html` มี inline rename (2033,2148,2157) และ delete แต่แผงเพลย์ลิสต์โชว์แค่ชื่อ+จำนวนเพลง ไม่มีวิธีดูรายเพลงหรือลบเพลงออกจากเพลย์ลิสต์ ต้องลบทั้งเพลย์ลิสต์แล้วสร้างใหม่
- **Search:** `search_youtube` คืน `[]` เมื่อ API ตาย, `search_song` fallback 39 เพลงกรองด้วย `q_lower in title/channel` แบบ substring ตรงๆ ถ้าคำค้นไม่ตรงเป๊ะ (เช่น พิมพ์หลายคำ ชื่อเว้นวรรคต่าง) จะคืน `[]` ว่าง ทำให้ผู้ใช้เห็น "ไม่เจอเพลง" ทั้งที่เพลงอยู่ใน fallback

## Proposed Approach

- **Playlist edit:** เพิ่มปุ่มขยาย ▶ ดูรายเพลงในแต่ละเพลย์ลิสต์ แสดง thumbnail+title+channel และปุ่ม X ลบเพลงทีละเพลง กด X → `PUT /api/playlists/<id>/` ส่ง `songs` ใหม่แบบไม่มีเพลงนั้น แล้ว re-render panel ใช้ `PlaylistManager.getAll()` + `window.PlaylistManager` + `getCSRFToken()` เดิม ไม่เพิ่ม endpoint ใหม่
- **Search fix:** แก้ `search_song` fallback ให้แยกคำค้นเป็น token (`query.lower().split()`) ตรวจว่า token ใดตรง `title` หรือ `channel` ก็ถือว่าเจอ ถ้ายังไม่เจอและ `had_substring_match` เดิมเป็น false ให้คืน `fallback[:3]` ที่กรอง blocked/ai/non_music แล้วเป็นคำแนะนำแทนว่าง เก็บ logic `had_substring_match` เดิมไว้สำหรับกรณีกรองแล้วว่าง

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| ดูเพลงในเพลย์ลิสต์ | เห็นแค่ชื่อ+จำนวนเพลง ต้องโหลดทั้งลิสต์ถึงรู้ | กด ▶ ขยายดูรายเพลง thumbnail+ชื่อ+ช่อง |
| ลบเพลงออกจากเพลย์ลิสต์ | ทำไม่ได้ ต้องลบทั้งเพลย์ลิสต์ | กด X ข้างเพลง → PUT songs ใหม่ ไม่ต้องลบเพลย์ลิสต์ |
| ค้นหา "เพลงรัก bodyslam" ตกคำ | `q_lower in title` ไม่ตรงเป๊ะ → `[]` ว่าง | แยก token `['เพลงรัก','bodyslam']` เจอถ้ามีคำใดคำหนึ่ง → เจอเพลง |
| ค้นหาคำไม่มีใน 39 เพลงเลย | คืน `[]` ว่าง | คืน 3 เพลงแนะนำ (fallback[:3] กรองแล้ว) ให้เลือกต่อ |

## Assumptions & Risks

- **Assumed:** ล็อกดีไซน์ Q1 B, Q2 B, Q3 A, Q4 A, Q5 A (rename inline มีแล้ว, ลบทีละเพลงด้วย X, token แยกด้วย space)
- **Assumed:** ไม่ต้องทำ reorder ลากสลับเพลงในรอบนี้
- **Assumed:** API `YOUTUBE_API_KEYS` ยังตาย จึงพึ่ง fallback 39 เพลงเป็นหลัก
- **Risk:** token split แบบ space ไม่ครอบคลุมคำไทยไม่มี space — ยอมรับข้อจำกัดนี้ ถ้าไม่เจอยังมี 3 แนะนำ
- **Risk:** ลบเพลงต้อง PUT ทั้ง array อาจ race ถ้าเปิดหลายแท็บ — ยอมรับ เพราะ playlist เป็นของ user เดียว

## Impact

- แก้ไขเพลย์ลิสต์ได้จริงโดยไม่ต้องลบสร้างใหม่
- ค้นหาเจอเพลงบ่อยขึ้น ลด "ไม่เจอเพลง" ว่างเปล่า

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **Search fallback token + recommend 3** - Lane A | Can run together: Task 2, Task 3 | Must wait for: none | TDD slice: failing test `test_search_token_fallback` -> edit `music/views.py:379-388` -> verify `manage.py test`
2. **Playlist inline rename already exists verify** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: test `test_playlist_inline_rename_exists` -> no code if pass -> verify
3. **Playlist expand + remove song X** - Lane B | Can run together: Task 1 | Must wait for: Task 2 (same file player.html) | TDD slice: failing test `test_playlist_remove_song_ui` -> edit `player.html:2024-2042` + `playlist.js` helper -> verify

---

### Task 1: Search fallback token + recommend 3

**Files:**

- Modify: `music/views.py:378-391` (fallback filter)
- Test: `music/tests.py` (add `SearchFallbackTests.test_token_and_recommend`)

**Parallelization:**

- Can run with: `Task 2`, `Task 3`
- Must wait for: `none`
- Race risk: `none` (views.py only)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code.

- [ ] **Step 1: Write the failing test**

```python
def test_token_and_recommend(self):
    # token: query with 2 words should match if any token in title/channel
    res = self.client.get('/api/search/?q=เพลงรัก bodyslam')
    self.assertEqual(res.status_code, 200)
    data = res.json()
    # should find at least one (bodyslam present)
    self.assertGreater(len(data['results']), 0)
    # no token match should return 3 recommendations not empty
    res2 = self.client.get('/api/search/?q=zzzznotfound123')
    self.assertEqual(res2.status_code, 200)
    self.assertEqual(len(res2.json()['results']), 3)
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `& ".\venv\Scripts\python.exe" manage.py test music.tests.SearchFallbackTests.test_token_and_recommend -v 2`. Expected FAIL: first assert 0 results or second asserts 0 !=3.

- [ ] **Step 3: Implement the minimal code**

In `views.py:378-388` replace substring check:
```python
q_lower = query.lower()
tokens = [t for t in q_lower.split() if t]
def matches(s):
    hay = (s['title'] + ' ' + s['channel']).lower()
    return any(tok in hay for tok in tokens) if tokens else False
results = [s for s in fallback if matches(s)]
```
Keep `had_substring_match` logic but rename to `had_match`. After blocked/ai filters, if `not results and not had_match`: return `fallback[:3]` filtered (not empty) as recommendations. Keep existing `if not results and had_match: fallback[:3]` branch.

- [ ] **Step 4: Run the test and confirm it passes**

Targeted + `manage.py test -v 1` (158 tests expected).

- [ ] **Step 5: Refactor only after green**

Extract `matches` helper, keep surgical change.

---

### Task 2: Playlist inline rename already exists verify

**Files:**

- Modify: `none` (verify only, if missing add)
- Test: `music/tests.py` (add `PlaylistUITests.test_inline_rename_exists`)

**Parallelization:**

- Can run with: `Task 1`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` (docs/config exception if no code change).

- [ ] **Step 1: Write the failing test**

```python
def test_inline_rename_exists(self):
    self.client.force_login(User.objects.create_user(username='u', password='p', is_staff=True))
    html = self.client.get('/').content.decode()
    self.assertIn('startInlineRename', html)
    self.assertIn('finishInlineRename', html)
    self.assertIn('playlist-rename-input', html)
```

- [ ] **Step 2: Run the test and confirm it passes**

Expected PASS (already exists at 2033,2148,2157). If FAIL, implement missing inline rename per Q3 A.

- [ ] **Step 3: Implement the minimal code**

No change if test passes. Otherwise add inline rename markup as in plan.

- [ ] **Step 4: Run the test and confirm it passes**

Targeted + full suite.

- [ ] **Step 5: Refactor only after green**

None.

---

### Task 3: Playlist expand + remove song X

**Files:**

- Modify: `music/templates/music/player.html:2024-2042` (renderPlaylistPanel)
- Modify: `music/static/music/playlist.js` (optional helper for PUT songs)
- Test: `music/tests.py` (add `test_playlist_remove_song_ui` + `test_playlist_put_remove`)

**Parallelization:**

- Can run with: `Task 1`
- Must wait for: `Task 2` (same file player.html)
- Race risk: `player.html` - sequential with Task 2

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_playlist_remove_song_ui(self):
    html = self.client.get('/').content.decode()
    self.assertIn('playlist', html.lower())
    # new: expand + remove button
    self.assertIn('removeSongFromPlaylist', html)
    self.assertIn('togglePlaylistSongs', html)

def test_playlist_put_remove(self):
    user = User.objects.create_user(username='pluser', password='p')
    self.client.force_login(user)
    # create playlist with 2 songs
    res = self.client.post('/api/playlists/create/', data=json.dumps({'name':'MyMix','songs':[{'id':'a1','title':'T1','channel':'C1','video_id':'a1'},{'id':'b2','title':'T2','channel':'C2','video_id':'b2'}]}), content_type='application/json')
    self.assertEqual(res.status_code, 201)
    pid = res.json()['id']
    # remove one via PUT
    put = self.client.put(f'/api/playlists/{pid}/', data=json.dumps({'songs':[{'id':'b2','title':'T2','channel':'C2','video_id':'b2'}]}), content_type='application/json')
    self.assertEqual(put.status_code, 200)
    self.assertEqual(len(put.json()['songs']), 1)
```

- [ ] **Step 2: Run the test and confirm it fails**

Targeted: `test_playlist_remove_song_ui` FAIL missing tokens, `test_playlist_put_remove` should already PASS (backend already handles). Confirm.

- [ ] **Step 3: Implement the minimal code**

In `player.html` `renderPlaylistPanel`:
- Add expand button `▶` per playlist row that toggles `<div id="playlist-songs-{safeName}">` containing songs list.
- Each song row: thumbnail, title, channel, X button `onclick="removeSongFromPlaylist('name','video_id')"`
- Implement `togglePlaylistSongs(name)` to show/hide div.
- Implement `removeSongFromPlaylist(name, videoId)`:
  ```js
  const all = await pm.getAll(); // map
  const songs = all[name] || [];
  const filtered = songs.filter(s => (s.id||s.video_id) !== videoId);
  const plId = pm._idMap[name] || (await fetch('/api/playlists/').then(r=>r.json()).then(d=>d.playlists.find(p=>p.name===name)?.id));
  await fetch(`/api/playlists/${plId}/`, {method:'PUT', headers:{'Content-Type':'application/json','X-CSRFToken':getCSRFToken()}, credentials:'same-origin', body: JSON.stringify({songs: filtered})});
  await renderPlaylistPanel();
  ```
- Keep inline rename/delete untouched.

- [ ] **Step 4: Run the test and confirm it passes**

Targeted + `manage.py test -v 1` (160 tests).

- [ ] **Step 5: Refactor only after green**

Extract helper, keep XSS escape via `escapeHtml`.

---

## Verification

- `& ".\venv\Scripts\python.exe" manage.py test -v 1` -> 160 tests OK (skipped 1)
- Manual: search `?q=เพลงรัก bodyslam` returns results, `?q=zzzz` returns 3 recommendations
- Manual: player playlist panel → expand ▶ → see songs → X ลบเพลง → reload → playlist persists
