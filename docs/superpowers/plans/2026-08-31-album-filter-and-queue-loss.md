# Album Filter and Queue Loss Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** กรองเพลงอัลบั้ม/ชั่วโมงออกจากหน้า request และแก้บั๊กบล็อกเพลงลิขสิทธิ์แล้วคิวหายหมดบน player

**Estimated tasks:** 3 | **Estimated time:** ~45 min | **Touches:** Frontend (request, player) / Backend (views) / Tests

## Current Problem / Current Solution

- หน้า request (`/request/`) โชว์เพลงอัลบั้ม Longplay/รวมเพลง/ชั่วโมง (เช่น "รวมเพลงเพราะๆ 60 Minutes Longplay") ผู้ใช้ไม่อยากเห็นเพราะยาว 1 ชม. แต่ตอนนี้ไม่มีการกรอง
- หน้า player เมื่อเจอ YouTube Error 153 (`onPlayerError` [2,5,100,101,150,153]) ทำ `blockedVideoIds.add + fetch /api/block + skipSong -> removePlayedSong -> fetch /api/played/<id>/` แต่หลัง CSRF + owner protect (`_is_owner` require X-Player-Token) ถ้า header ไม่ถูกส่งหรือ 403 จะทำให้ `removePlayedSong` ไม่ลบสำเร็จ แต่ `currentSong = null` แล้ว `fetchQueue` โหลดคิวใหม่แล้วคิวดูเหมือนหายหมด (0) ผู้ใช้เห็น "รีเว็บ" + "คิวหายหมด"
- ไม่มี test ครอบคลุมการกรองอัลบั้มและการไม่ล้างคิวทั้งหมดเมื่อบล็อก

## Proposed Approach

- **Album filter (keyword):** เพิ่ม `isAlbumLike(title)` เช็ค `title.toLowerCase()` มีคำว่า `longplay|รวมเพลง|ชั่วโมง|อัลบั้ม|60 minutes|playlist|ยาวๆ|ต่อเนื่อง` ให้ `filterBlockedSongs` และ `fetchHits`/`searchSong` ใน `request.html` (และ `player.html` สำหรับ hits) กรองออกก่อน `renderHitList`/`manualSearch` ไม่ต้องเรียก API เพิ่ม เร็ว
- **Queue loss fix:** ใน `player.html` `onPlayerError` สำหรับ 153 ให้ `fetch /api/block` แบบ fire-and-forget เหมือนเดิม แต่ `skipSong` -> `removePlayedSong` ต้องส่ง `X-CSRFToken` + `X-Player-Token` ให้ถูกต้อง (ใช้ `getCSRFToken()` + `getPlayerToken()` จาก Task 1) และ handle 403 โดย fallback ลบออกจาก `queue` local แล้ว `renderQueue` ไม่รอ server, ไม่ทำ `location.reload`, ไม่เรียก `clearQueue`
- **Backend:** `music/views.py` `search_youtube`/`hits` เพิ่มกรอง keyword เดียวกันฝั่ง server เพื่อไม่ส่งอัลบั้มมาตั้งแต่ต้น (defense in depth), แต่ไม่บังคับ duration check

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| ค้นหา "เพลง" ใน request | เห็น "รวมเพลง 60 Minutes Longplay" | ไม่เห็น ถูกกรองออก |
| Player เจอ 153 เพลงเดียวในคิว 5 เพลง | คิวหายหมด 0 | หายแค่เพลงที่ 153 เหลือ 4 |
| POST /api/played without token | 403 แล้ว queue ไม่ลบ | ส่ง token ถูกต้อง ลบแค่ตัวเดียว |

## Assumptions & Risks

- **Assumed:** กรองด้วย keyword พอ ไม่ต้องเช็ค duration จาก YouTube API (ประหยัด quota)
- **Assumed:** `X-Player-Token` ถูกส่งจาก `player.html` meta `player-token` แล้ว, ถ้าไม่ส่งจะ 403
- **Risk:** กรอง keyword อาจกรองเพลงปกติที่มีคำว่า "รวมเพลง" ผิด แต่ยอมรับได้ตามที่เลือก A
- **Risk:** ถ้า `removePlayedSong` 403 จะ fallback local remove อาจทำให้ DB กับ UI ไม่ตรง ต้อง fetchQueue ซ้ำหลัง local remove

## Impact

- หน้า request ไม่รกด้วยอัลบั้มชั่วโมง
- บล็อกเพลงลิขสิทธิ์ไม่ทำให้คิวหายหมด ระบบเสถียร

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code.

1. **[Album keyword filter frontend]** - Lane A | Can run together: Task 3 | Must wait for: none | TDD slice: test page not contain Longplay when filtered -> add isAlbumLike -> `manage.py test`
2. **[Backend album filter]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: test /api/hits not return Longplay -> add filter in views -> `manage.py test`
3. **[Fix queue loss on 153 block]** - Lane C | Can run together: none | Must wait for: Task 1 | TDD slice: test block one song queue remains 4 -> fix removePlayedSong headers + fallback -> `manage.py test`

---

### Task 1: Album keyword filter frontend

**Files:**

- Modify: `music/templates/music/request.html` (filterBlockedSongs, fetchHits, searchSong, renderHitList)
- Modify: `music/templates/music/player.html` (hitSongs filter)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 2
- Must wait for: none
- Race risk: none

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_request_filters_album_keyword():
  res = client.get('/request/')
  # JS should contain isAlbumLike or Longplay filter
  assert 'Longplay' in res.content.decode() or 'isAlbumLike' in res.content.decode()
```

- [ ] **Step 2: Run FAIL**

`manage.py test` FAIL.

- [ ] **Step 3: Implement**

Add `function isAlbumLike(title){ return /longplay|รวมเพลง|ชั่วโมง|อัลบั้ม|60 minutes|playlist|ยาวๆ|ต่อเนื่อง/i.test(title); }` and in `filterBlockedSongs` return `!blockedVideoIds.has(song.id) && !isAlbumLike(song.title)` and in `fetchHits` after `hitSongs = data.results.filter(...)` also filter `!isAlbumLike`.

- [ ] **Step 4: PASS**

---

### Task 2: Backend album filter

**Files:**

- Modify: `music/views.py` (`search_youtube`, `hits`, `youtube_api_search` helper)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 1
- Must wait for: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_hits_api_filters_album():
  # mock youtube_api_search returns Longplay title, ensure /api/hits filters it
  pass
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

Add helper `def _is_album_title(title): return bool(re.search(...))` and in `search_youtube` after building `raw`/`api_results`, filter `if _is_album_title(r['title']): continue` and in `hits` fallback static filter same.

- [ ] **Step 4: PASS**

---

### Task 3: Fix queue loss on 153 block

**Files:**

- Modify: `music/templates/music/player.html` (`onPlayerError`, `removePlayedSong`, `skipSong`)
- Modify: `music/views.py` (`mark_played` ensure 403 handling)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: none
- Must wait for: Task 1 (needs CSRF token helper)
- Race risk: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_block_one_song_queue_remains():
  # create 5 songs, simulate block one via /api/block + /api/played with token, ensure 4 remain
  pass
```

- [ ] **Step 2: FAIL** (currently queue becomes 0 due to 403 or remove logic)

- [ ] **Step 3: Implement**

In `player.html` `onPlayerError` already does `blockedVideoIds.add + fetch block + skipSong`, ensure `removePlayedSong` sends `X-CSRFToken` + `X-Player-Token` and on 403 fallback: `queue = queue.filter(s=>s.id!==songId); renderQueue();` without reload. Ensure `skipSong` not call `clearQueue`.

- [ ] **Step 4: PASS**

