# iOS 153 Black Screen Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** iPhone/iPad กดเล่นแล้ว 153 ดำ → แก้ให้เล่นได้ (hits 8 ขึ้นแล้วแต่เล่นไม่ได้)

**Estimated tasks:** 3 | **Estimated time:** ~45 min | **Touches:** Player JS / Test

## Current Problem / Current Solution

- `testuser1000` login iPhone/iPad เห็น `hits 8` แต่กด `เล่น/เริ่มเล่นเพลง` → ดำ + `Error 153` (Q125) — ก่อนหน้า `fetchHits` ค้างเพราะ `SyntaxError` แก้แล้ว (`b654380`) ตอนนี้โหลดได้แต่เล่นไม่ได้
- `player.html` ใช้ `host: youtube-nocookie.com` + `playerVars` เต็ม 10 ตัว + `playsinline:1` + `overlay tap` + `onError 153` soft-skip (ลบ toast แล้ว) แต่ iOS ยัง 153 ทุกเพลงที่ hits สุ่ม (fallback 8 เพลง)
- `isLineWebView` error หายแล้วหลังแก้ `function function`

## Proposed Approach

- **Host สลับตาม UA:** iOS → `https://www.youtube.com` (ไม่ใช่ nocookie) + `widget_referrer` กลับมาแบบมี `origin` ชัดเจน, อื่นๆ คง `nocookie` — ทดลองแล้ว 153 บน iPad เกี่ยวกับ nocookie + ITP
- **Auto fallback 153 → noapi:** `onError 153` ครั้งแรกไม่แค่ `skip` แต่ `loadVideoById` ล้มเหลว → ลอง `playNextNoApi()` (iframe ธรรมดา `youtube-nocookie/embed/<id>?autoplay=1`) ทันที ถ้ายัง 153 อีก 2 ครั้งค่อย breaker — ทำให้ iOS ยังดูได้แม้ JS API บล็อก
- **Hits กรอง embeddable เข้ม:** `hits` fallback 8 เพลง เช็ค `_is_blocked` แล้ว แต่ไม่เช็ค `playable_in_embed` บน iOS — เพิ่ม `cache` แยก `hits:ios` ที่เช็ค `_is_embeddable` แบบเบา (HEAD oEmbed) หรือ fallback เฉพาะที่แน่ใจว่า iOS เล่นได้ (ks7p6DA0dKk, L1k0wkQ6uww ที่เทสแล้ว)

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| iPad กดเล่น | ดำ 153 | ลอง nocookie→youtube สลับ + fallback noapi → เล่นได้ |
| hits | สุ่ม 8 ตัวเดิม | กรอง iOS-safe 8 ตัว |

## Assumptions & Risks

- **Assumed:** 153 บน iOS มาจาก `nocookie` + `videoEmbeddable` ไม่ตรงกับ iOS (desktop ผ่าน)
- **Risk:** สลับ host อาจทำให้ desktop 153 แทน → แยก UA
- **Risk:** noapi iframe ไม่มี `onStateChange` → ต้องใช้ `duration API` timer ต่อคิวเอง (มีแล้ว)

## Impact

- แตะ `player.html` (host, playerVars, onError, fetchHits), `views.py` (hits cache key)

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Host switch UA]** - Lane A | Can run together: none | Must wait for: none | TDD slice: iOS UA -> youtube.com -> `manage.py test`
2. **[153 fallback noapi]** - Lane A | Can run together: none | Must wait for: Task 1 | TDD slice: 153 first -> noapi -> `manage.py test`
3. **[iOS-safe hits]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: hits ios cache -> `manage.py test`

---

### Task 1: Host switch UA

**Files:**

- Modify: `music/templates/music/player.html` (player host)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 3`
- Must wait for: `none`
- Race risk: `player.html`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

`GET /` as iPhone UA should contain `youtube.com` not `nocookie` (or both)

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test -v2`. Expected: FAIL

- [ ] **Step 3: Implement the minimal code**

`player.html`: `const isIOS = ...; const ytHost = isIOS ? 'https://www.youtube.com' : 'https://www.youtube-nocookie.com';` + `host: ytHost` + `widget_referrer: isIOS ? window.location.origin : undefined` (ถ้าต้อง), keep `origin/enablejsapi`

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test` PASS

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 2: 153 fallback noapi

**Files:**

- Modify: `music/templates/music/player.html` (onError)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1`
- Race risk: `player.html`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

`onError 153` should contain `playNextNoApi`

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test`. Expected: FAIL

- [ ] **Step 3: Implement the minimal code**

`onError`: if `event.data===153` and `!window._triedNoApi` → `window._triedNoApi=true; try{ playNextNoApi(); }catch(e){ skipSong(); }` else `skipSong()`, keep breaker

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test` PASS

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 3: iOS-safe hits

**Files:**

- Modify: `music/views.py` (hits)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 1`
- Must wait for: `none`
- Race risk: `views.py`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

`GET /api/hits/` with iPhone UA should not contain blocked 153 ids, and cache key includes ios

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test`. Expected: FAIL

- [ ] **Step 3: Implement the minimal code**

`hits`: `is_ios = 'iPhone|iPad' in request.META.get('HTTP_USER_AGENT','')` → `cache_key = f"hits:{genre}:v3:{'ios' if is_ios else 'other'}"` + filter `_is_blocked` + if ios, prefer fallback ids that are known embeddable (ks7p6DA0dKk, L1k0wkQ6uww, etc.) and skip `_is_embeddable` check heavy, just use static 8

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test` PASS

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.
