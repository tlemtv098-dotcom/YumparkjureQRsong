# Remove Tabs + Stable Random (Album Only Player) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เอาแท็บ ทั้งหมด/ป๊อป/ร็อก/ลูกทุ่ง/TikTok ออกจาก request + ทำสุ่มใหม่ player เสถียร สุ่มกว้าง (hits+ค้นหายอดนิยม+อัลบั้ม 1 ชม. เฉพาะ player) + ข้าม 153/ซ้ำ ไม่สุ่มซ้ำเซสชัน

**Estimated tasks:** 3 | **Estimated time:** ~45 min | **Touches:** Frontend / API

## Current Problem / Current Solution

- request มีแท็บ `ทั้งหมด/ป๊อป/ร็อก/ลูกทุ่ง/TikTok` ผู้ใช้อยากเอาออก
- player `autoRandom` สุ่มจาก `hitSongs 15` อย่างเดียว + `isAlbumLike` เพิ่งปลดทุกจุด → อัลบั้ม 1 ชม. โผล่ทั้ง request/player แต่ผู้ใช้อยากได้แค่ `player` ส่วน `request` ยังกรองเหมือนเดิม + สุ่มไม่เสถียร (153 ค้าง, สุ่มซ้ำ)

## Proposed Approach

- **request:** ลบ `genre tabs` HTML + JS `genre` handling + `fetchHits(genre)` แต่คง `hits` แบบ `ทั้งหมด` อย่างเดียว (ไม่ส่ง `?genre=`)
- **player:** `hits` แยก `is_player` flag → ถ้า `player` ส่ง `?player=1` ให้ `_is_album_title` ไม่กรอง (รวมอัลบั้ม 1 ชม.) + `search_youtube` สุ่ม 3-4 query กว้าง (`เพลงไทยฮิต`, `เพลงลูกทุ่ง 1 ชั่วโมง`, `รวมเพลงยาว`) + `cache` แยก `player`/`request` → `autoRandom` ปรับ: `candidates = hitSongs.filter(...autoPlayedIds...)` + `skip 153` → `blockedVideoIds.add + autoPlayedIds.add` + ข้ามทันที + จำไม่สุ่มซ้ำจนครบแล้วค่อย `clear`

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| request | มีแท็บ 5 ปุ่ม | ไม่มีแท็บ โชว์ hits 8 เดียว |
| player hits | 15 ไม่มีอัลบั้ม | 15 มีอัลบั้ม 1 ชม. ปนได้ |
| autoRandom | สุ่ม 15 เดิม ซ้ำได้ | สุ่มกว้าง ไม่ซ้ำเซสชัน ข้าม 153 ทันที |

## Assumptions & Risks

- **Assumed:** Q132=A สุ่มกว้าง, Q133=A ข้าม+จำ, อัลบั้มเฉพาะ player
- **Risk:** hits player มีอัลบั้มยาว 60 นาที → iOS noapi ต้องใช้ `duration` ยาว อาจค้างนาน → ใช้ `duration API` อยู่แล้ว

## Impact

- แตะ `request.html` (tabs), `player.html` (hits+autoRandom), `views.py` (hits/request filter)

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Remove tabs request]** - Lane A | Can run together: none | Must wait for: none | TDD slice: GET /request/ no genre tabs -> remove HTML/JS -> `manage.py test`
2. **[Player hits album only]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: player hits allows album -> add ?player=1 flag -> `manage.py test`
3. **[Stable random wide]** - Lane B | Can run together: none | Must wait for: Task 2 | TDD slice: autoRandom wide + no repeat -> update player.html -> `manage.py test`

---

### Task 1: Remove tabs request

**Files:**

- Modify: `music/templates/music/request.html` (remove tabs HTML + JS genre)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `request.html`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

`GET /request/` should not contain `ทั้งหมด` + `ป๊อป` tabs (check `genre-tab`)

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test -v2`. Expected: FAIL (tabs exist)

- [ ] **Step 3: Implement the minimal code**

Remove `<div class="flex gap-2">` tabs + `genre` JS `fetchHits(genre)` + `data-genre` handlers, keep `hits` as `ทั้งหมด` single call `fetch('/api/hits/')`

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test` PASS

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 2: Player hits album only

**Files:**

- Modify: `music/views.py` (hits), `music/templates/music/player.html` (fetchHits ?player=1)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 1`
- Must wait for: `none`
- Race risk: `views.py` + `player.html` (different lanes okay)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

`GET /api/hits/?player=1` allows album title (mock Longplay), `GET /api/hits/` blocks album

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test`. Expected: FAIL

- [ ] **Step 3: Implement the minimal code**

`views.py hits`: `is_player = request.GET.get('player')=='1'` → if `is_player` skip `_is_album_title` filter, else keep filter. Cache key `hits:{genre}:v3:{'player' if is_player else 'request'}:{'ios'...}`

`player.html`: `fetch('/api/hits/?player=1')`

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test` PASS

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 3: Stable random wide

**Files:**

- Modify: `music/templates/music/player.html` (autoRandom + hits wide queries + skip)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 2`
- Race risk: `player.html`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

Manual: `autoRandom` candidates not repeat until all 15 used, and 153 blocked not re-picked

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Check `autoPlayedIds` logic

- [ ] **Step 3: Implement the minimal code**

`player.html`: `hits` wide queries add `เพลงลูกทุ่ง 1 ชั่วโมง` + `รวมเพลง 1 ชั่วโมง` when `?player=1`, `autoRandom` already has `autoPlayedIds` + `blockedVideoIds` filter, ensure `onError 153` adds to both sets and `skipSong` then `playRandomHit` next tick, `playRandomHit` shuffles `picked` 3-4 queries

- [ ] **Step 4: Run the test and confirm it passes**

`manage.py check` + manual

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.
