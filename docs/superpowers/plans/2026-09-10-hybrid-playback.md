# Hybrid Playback (embed-first + audio fallback) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ทุกเพลงเล่นได้ — embed ก่อน พังแล้วตัดไปเสียงสำรองอัตโนมัติ (Q153=A)

**Estimated tasks:** 3 | **Estimated time:** ~60 min | **Touches:** Frontend / API

## Current Problem / Current Solution

- เพลงที่เจ้าของปิดฝัง (153) ข้ามทิ้งอย่างเดียว — อยากให้มีเสียงออกแทน
- มี `/api/audio/` + audio mode อยู่แล้ว แต่ Render `yt-dlp 503` + auto-switch ถูกถอด (กันดูดคิว)

## Proposed Approach

- **Fallback chain ต่อเพลง:** `embed error (153/150/101) → ลอง /api/audio/ 1 ครั้ง → ได้เสียงเล่นต่อเลย (ไม่ข้าม) → ไม่ได้ค่อยข้าม+บล็อก` — ทำใน `onError` เดิม ไม่แตะ path ปกติ
- **Audio provider แบบเสียบได้:** `views.py` เพิ่ม `AUDIO_PROVIDER` chain: `1) yt-dlp ตรง (เผื่อ IP หายบล็อก) 2) cache 3) external worker URL (env AUDIO_WORKER_URL, ยังไม่มี = ข้าม)` — โครงพร้อมรับ worker ร้านทีหลังโดยไม่แก้โค้ดอีก
- **Allowlists เรียนรู้เอง:** เพลงที่เคยเล่นจบ (`song_done` ตรงเพลง) จำ `GoodVideo` (memory+DB?) — hits/search เรียงเพลงดีขึ้นก่อน ลดโอกาสเจอ 153 ตั้งแต่ต้น (เบา: ใช้ BlockedVideo กลับด้าน + hit-order bias)

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| เจอเพลงปิดฝัง | ข้ามทันที เงียบ | ลองเสียงสำรองก่อน ได้ยินแล้วค่อยไปต่อ |
| worker ร้านมา | ใช้ไม่ได้ | ตั้ง env เดียวจบ |

## Assumptions & Risks

- **Assumed:** `/api/audio/` อาจ 503 บ่อย — chain รับมือด้วยข้ามตามเดิม
- **Risk:** audio element + queue state ซ้อนกับ YT player — ต้อง stop ฝั่งหนึ่งก่อนเสมอ

## Impact

- แตะ `player.html` (onError chain + audio handoff), `views.py` (provider chain), `tests.py`

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Provider chain]** - Lane A | Can run together: none | Must wait for: none | TDD slice: worker env used when set -> add chain -> `manage.py test`
2. **[onError audio fallback]** - Lane A | Can run together: none | Must wait for: Task 1 | TDD slice: 153 tries audio before skip -> update player.html -> manual
3. **[Good-video bias]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: proven ids first -> add bias -> `manage.py test`

---

### Task 1: Provider chain

**Files:**

- Modify: `music/views.py` (audio_stream), `music/tests.py`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 3`
- Must wait for: `none`
- Race risk: `views.py` shared with Task 3 — coordinate areas (audio fn vs hits fn)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

`AUDIO_WORKER_URL` set + yt-dlp fails → uses worker URL response.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test -v2`. Expected: FAIL.

- [ ] **Step 3: Implement the minimal code**

`audio_stream`: `worker = os.environ.get('AUDIO_WORKER_URL','')` → try yt-dlp chain → except → if worker: GET `{worker}/audio?id=` timeout 10 → cache → return; else 503 as today.

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test` + `check`.

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 2: onError audio fallback

**Files:**

- Modify: `music/templates/music/player.html` (onError)
- Test: manual + marker test

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1`
- Race risk: `player.html`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` (manual verify).

- [ ] **Step 1: Write the failing test**

Marker `AUDIO_FALLBACK` in HTML.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test`. Expected: FAIL.

- [ ] **Step 3: Implement the minimal code**

onError 153/150/101: if not tried audio for this song → `stopVideo` + hide player + `playNextAudioFor(currentSong)` (reuse audio logic with explicit song, set flag) → on audio fail → original skip path. Guard flag per song id.

- [ ] **Step 4: Run the test and confirm it passes**

`check` + desktop manual (block a test id → hear audio or skip).

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 3: Good-video bias

**Files:**

- Modify: `music/views.py` (hits ordering), `music/tests.py`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 1`
- Must wait for: `none`
- Race risk: `views.py` (different function than Task 1)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

`song_done` (mark_played) records id; hits puts recorded-good ids first.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test`. Expected: FAIL.

- [ ] **Step 3: Implement the minimal code**

`GoodVideo` via existing `BlockedVideo` inverse? Simplest: new tiny model `GoodVideo(video_id, plays)` + `mark_played` increments + `hits` sorts known-good first (stable, rest keep order). Migration included.

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test` + `check` + migrate.

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.
