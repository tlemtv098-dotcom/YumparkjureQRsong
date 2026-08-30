# Universal Platform Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ทำให้เว็บเล่นได้เหมือนกันทุกแพลตฟอร์ม (iOS Safari, Chrome iOS iPhone 13, iPad Safari/Chrome, Android Chrome, Desktop Chrome/Safari/Firefox, LINE/Facebook in-app WebView) โดยกรอง Error 153 ตั้งแต่ต้นทางและรวม tap-gate เดียวกันทุกที่

**Estimated tasks:** 5 | **Estimated time:** ~90 min | **Touches:** API / Frontend / Tests / Docs

## Current Problem / Current Solution

- Player ใช้ YouTube IFrame API host youtube.com + playsinline แล้ว Safari ผ่าน แต่ Chrome iOS iPhone 13 ยังเจอ Error 153 (video cannot be embedded) บ่อยเพราะ search/hits ยังคืนวิดีโอที่ embed ไม่ได้ให้ UI ผู้ใช้กดแล้วพังตรงหน้า player
- `search_youtube()` มี `_is_embeddable` check แต่ fallback `return filtered if filtered else raw[:5]` ยังปล่อย raw ที่อาจบล็อกกลับไป  และ fallback static hits ไม่ได้ตรวจซ้ำ
- Autoplay แยก `isMobile` branch ทำให้ Desktop autoplay ได้แต่ Mobile ต้อง tap ไม่สม่ำเสมอ LINE WebView บล็อกเข้มกว่าเดิมทำให้ branch แตกและเทสยาก
- `onError` ทำ soft-skip memory-only แล้วแต่ยังโชว์วิดีโอที่เล่นไม่ได้ตั้งแต่แรก ผู้ใช้รู้สึกพังก่อน skip
- ไม่มี checklist ยืนยัน 5 อุปกรณ์ ทำให้แก้บน Desktop แล้วคิดว่าเสร็จแต่ iPhone 13 Chrome ยังพัง

## Proposed Approach

- **Pre-filter เงียบตั้งแต่ API:** บังคับ `youtube_api_search(videoEmbeddable=true, videoSyndicated=true)` + ตรวจ `yt_dlp _is_embeddable` ทุกตัวก่อนส่ง `hits/search` กลับ ถ้า None (network) ให้เก็บไว้ แต่ถ้า False ให้ทิ้งและ cache ผลลัพธ์ ไม่ fallback raw แบบไม่กรอง
- **Uniform tap-gate ทุกแพลตฟอร์ม:** ลบ `isMobile` branching ใน `fetchQueue/playNext` ให้ทุก browser โชว์ `#queue-overlay` แตะเพื่อเปิดเสียง ครั้งแรกก่อนเล่นเสมอ ลด autoplay บั๊กบน LINE WebView/iOS
- **WebView detection + external open hint:** ตรวจ UA `Line/|FBAN|FBAV|Messenger` แล้วโชว์ปุ่ม เปิดในเบราว์เซอร์ภายนอกบน player + request หน้า พร้อม guard serviceWorker ไม่ลงทะเบียนใน WebView ที่ไม่รองรับ
- **คง soft-skip เดิม:** `blockedVideoIds` memory-only + toast + skipSong ทันที ไม่ย้อนกลับไป POST /api/block
- **Verify ด้วย checklist 5 อุปกรณ์:** เพิ่ม test และคู่มือ verify ใน plan

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| ค้นหาเพลง VEVO บน iPhone 13 Chrome | โชว์ใน results กดแล้ว Error 153 → toast → skip | ไม่โชว์ตั้งแต่ results กรองออกก่อนส่ง UI |
| เปิดเว็บครั้งแรก Desktop | autoplay muted เล่นเอง | โชว์ overlay แตะเพื่อเปิดเสียง เหมือน Mobile ทุกที่ |
| เปิดใน LINE in-app | อาจ autoplay ล้มเหลว + Error 5/153 ไม่มีคำแนะนำ | เจอ banner แนะนำ เปิดใน Safari/Chrome + tap-gate ทำงาน |
| hits แนะนำ fallback static | ส่ง 8 ตัวแบบสุ่มไม่กรองซ้ำ | กรอง `_is_blocked` + `_is_embeddable` cache 60วิก่อนส่ง |
| Network ล้มเหลวตอนตรวจ embed | return raw ทั้งหมดรวมตัวบล็อก | ถ้า `_is_embeddable is None` เก็บไว้ให้ player soft-skip จัดการ ไม่ auto-block DB |

## Assumptions & Risks

- **Assumed:** Render รัน `yt_dlp` ได้ quota YouTube API มีจริง (env YOUTUBE_API_KEY/key) ถ้าไม่มีจะ fallback API → yt-dlp เสมอ
- **Assumed:** `videoEmbeddable=true` กรองได้ ~80% ที่เหลือต้องพึ่ง yt-dlp check
- **Assumed:** ผู้ใช้ยอมแลก Desktop ต้อง tap ครั้งแรกเพื่อความสม่ำเสมอทุกแพลตฟอร์ม
- **Risk:** `yt_dlp _is_embeddable` ช้า 1-2 วิ/ตัว + ตรวจ 5 ตัว = search ช้าลง ต้องมี cache และ limit 8 → 5
- **Risk:** LINE WebView ตรวจ UA ไม่แม่น 100% ต้อง fallback เป็น tap-gate เดิมถ้าตรวจพลาด
- **Risk:** Uniform tap-gate อาจทำให้เจ้าของร้านบ่นต้อง tap ทุกครั้งหลัง refresh ต้องมี wakeLock รักษาหน้าจอ

## Impact

- ลด Error 153 ที่ผู้ใช้เห็นบน iPhone 13 Chrome / iPad / LINE ลง ~80% โดยไม่ refactor เป็น `<audio>`
- UX สม่ำเสมอทุก browser ลด code branch isMobile ครึ่งหนึ่ง เทสง่ายขึ้น
- Search/hits ช้าลงเล็กน้อยแต่ cache ช่วย ครั้งต่อไปเร็ว
- ไม่เปลี่ยน DB schema ไม่เปลี่ยน API contract เดิม blockVideo ยังอยู่แต่ไม่ถูกเรียกจาก player onError

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Server pre-filter hardening]** - Lane A | Can run together: Task 2 | Must wait for: none | TDD slice: failing test `search_youtube` returns no blocked ids even when raw contains blocked -> filter + cache -> `python manage.py test`
2. **[Player uniform tap-gate + WebView detection]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: failing test player contains uniform overlay logic no isMobile autoplay branch -> add UA detection + overlay -> `python manage.py test`
3. **[Request page empty-state + external open hint]** - Lane C | Can run together: Task 2 | Must wait for: Task 1 | TDD slice: failing test request shows no results message when filtered empty -> add hint + external browser button -> `python manage.py test`
4. **[Regression tests for universal support]** - Lane D | Can run together: none | Must wait for: Task 1, Task 2, Task 3 | TDD slice: failing 5-device checklist tests -> add tests -> `python manage.py test`
5. **[Verification checklist doc]** - Docs only | Can run together: none | Must wait for: Task 4 | TDD slice: docs only -> verify checklist rendered -> manual verify

---

### Task 1: Server pre-filter hardening

**Files:**

- Modify: `music/views.py:27-56, 114-256`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 2`
- Must wait for: `none`
- Race risk: `none` (only views.py)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code. This task must follow RED -> GREEN -> REFACTOR unless it is explicitly docs/config-only; if it is docs/config-only, say why and include the smallest verification command instead.

- [ ] **Step 1: Write the failing test**

```python
def test_search_youtube_filters_blocked_even_when_raw_has_blocked():
    # mock youtube_api_search returns [] so yt-dlp path taken, mock _is_embeddable True
    # ensure BLOCKED_VIDEO_IDS never appear in results
    pass

def test_hits_filtered_and_cached():
    res = client.get('/api/hits/')
    assert all(id not in BLOCKED_VIDEO_IDS for id in results)
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `python manage.py test music.tests -v2` Expected FAIL because current `search_youtube` fallback returns `raw[:5]` even if blocked, and hits static fallback not filtered via is_embeddable.

- [ ] **Step 3: Implement the minimal code**

- In `search_youtube`: remove `return filtered if filtered else raw[:5]` leak. Change to `return filtered[:5] if filtered else []` then let caller fallback handle empty correctly, but ensure empty does not return blocked raw. Keep `None` case as keep.
- In `search_song` and `hits`: ensure fallback static list is filtered via `_is_blocked` and also via `_is_embeddable` quickly or at least `_is_blocked`, and cache hits correctly.
- Keep `youtube_api_search` already uses `videoEmbeddable=true` + `videoSyndicated=true`, verify not removed.
- Ensure `_is_embeddable` returns None not False on network error remains.

- [ ] **Step 4: Run the test and confirm it passes**

Run `python manage.py test music.tests -v2` PASS.

- [ ] **Step 5: Refactor only after green**

Clean up duplicate fallback lists into helper `_fallback_hits()` if needed, rerun test.

---

### Task 2: Player uniform tap-gate + WebView detection

**Files:**

- Modify: `music/templates/music/player.html:142-383`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 1`
- Must wait for: `none`
- Race risk: `none` (only player.html)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_player_has_uniform_tap_gate_and_webview_detection():
    res = client.get('/')
    assert 'queue-overlay' in res.content.decode()
    assert 'isLineWebView' in res.content.decode() or 'Line/' in res.content.decode()
    assert 'Open in external browser' in res.content.decode() or 'เปิดในเบราว์เซอร์' in res.content.decode()
    # ensure no isMobile autoplay branch plays without tap
    assert res.content.decode().count('isMobile && !userInteracted') == 0  # should be removed or unified
```

- [ ] **Step 2: Run the test and confirm it fails**

`python manage.py test music.tests.PlayerPageTests.test_player_has_uniform_tap_gate -v2` FAIL.

- [ ] **Step 3: Implement the minimal code**

- Add JS `const isLineWebView = /Line\/|FBAN|FBAV|Messenger/i.test(navigator.userAgent)` + banner `#webview-banner` with button `window.open(location.href, '_blank')` and instruction.
- Remove `if (isMobile && !userInteracted)` branches in `fetchQueue` and `playNext` replace with unified `if (!userInteracted)` show overlay. Keep `isMobile` const for legacy but not used for autoplay branching, or keep isMobile for wakeLock only.
- Ensure `onReady` still `fetchQueue(); fetchHits();` but not auto `playNext` without userInteracted.
- Guard serviceWorker registration: `if ('serviceWorker' in navigator && !isLineWebView)`.
- Keep host youtube.com + playsinline.

- [ ] **Step 4: Run the test and confirm it passes**

`python manage.py test` PASS.

- [ ] **Step 5: Refactor only after green**

Remove dead isMobile branching code, rerun test.

---

### Task 3: Request page empty-state + external open hint

**Files:**

- Modify: `music/templates/music/request.html`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 2`
- Must wait for: `Task 1` (needs filtered empty case real)
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_request_shows_empty_filtered_message():
    res = client.get('/request/')
    assert 'ไม่พบเพลงที่ค้นหา' in res.content.decode() or 'ลองคำค้นอื่น' in res.content.decode()
```

- [ ] **Step 2: Run the test and confirm it fails**

`python manage.py test music.tests.RequestPageTests -v2` FAIL if message not present for filtered empty.

- [ ] **Step 3: Implement the minimal code**

- In `request.html` JS `manualSearch` when `manualSearchResults.length===0` after filter, show distinct message `ไม่พบเพลงที่เล่นได้ ลองคำค้นอื่น` not generic.
- Add same WebView banner as player, and guard PWA manifest/serviceWorker similarly.

- [ ] **Step 4: Run the test and confirm it passes**

`python manage.py test` PASS.

- [ ] **Step 5: Refactor only after green**

Rerun.

---

### Task 4: Regression tests for universal support

**Files:**

- Modify: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1, Task 2, Task 3`
- Race risk: `none` (test file only after others)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

Add 3 new tests:
- `test_api_hits_never_returns_blocked_ids`
- `test_api_search_never_returns_blocked_ids`
- `test_player_no_autoplay_without_tap_gate`

- [ ] **Step 2: Run the test and confirm it fails**

`python manage.py test music.tests -v2` FAIL initially then after Tasks 1-3 should PASS, this task just locks regression.

- [ ] **Step 3: Implement the minimal code**

Only add tests, no prod code. Ensure they pass with previous tasks.

- [ ] **Step 4: Run the test and confirm it passes**

`python manage.py test` PASS no warnings.

- [ ] **Step 5: Refactor only after green**

Clean test helpers.

---

### Task 5: Verification checklist doc

**Files:**

- Create: `docs/superpowers/checklists/universal-platform-checklist.md` (or update existing)
- Modify: `README.md` if needed to link checklist

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 4`
- Race risk: `none`
- Docs only: no TDD, verification is file exists + manual 5-device run.

- [ ] **Step 0: Load the TDD discipline**

Docs only — skip RED.

- [ ] **Step 1: Write checklist**

Include 5 rows: iPhone Safari, iPhone Chrome (iPhone 13), iPad Safari/Chrome, Android Chrome, Desktop Chrome + LINE WebView. Columns: open / search / add to queue / tap gate / play / skip on 153.

- [ ] **Step 2: Verify**

`Test-Path docs/superpowers/checklists/universal-platform-checklist.md` and `python manage.py test` still PASS.

