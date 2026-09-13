# Embeddability Filter (oEmbed) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** กรองคลิปปิดฝังออกตั้งแต่ API ด้วย oEmbed check + cache ก่อนเข้าคิว (แก้ 153 + ข้ามรัวคิวหมด)

**Estimated tasks:** 2 | **Estimated time:** ~30 min | **Touches:** API / Tests

## Current Problem / Current Solution

- iPad เจอ `153 + ข้ามรัวคิวหมด` — pool `hits ?player=1` มี Longplay/TikTok spam ปนที่ปิดฝัง (`embedding disabled`) → `onError 153 → skipSong` วนจนคิวหมดทุกเครื่อง (desktop รอดเพราะสุ่มโดนเพลงดี)
- `oEmbed` เช็คแล้วแม่น: 18 static `200` ฝังได้หมด, คลิปปิดฝังคืน `401/404`

## Proposed Approach

- `views.py`: helper `_is_embed_ok(video_id)` → `cache embed_ok:{id} 24h` → `oEmbed .../oembed?url=watch?v={id}&format=json timeout 3s` → `200 True`, `401/404 False`, exception `None` (allow ไม่บล็อกมั่ว)
- ใช้ใน `youtube_api_search` (skip `False`) + `hits` merged/dedup + `search_song` live results — fallback static ไม่ต้องเช็ค (verified แล้ว)
- ไม่แตะ player.html (breaker/skip เดิมรับมือที่เหลือ)

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| hits pool | ปนคลิปปิดฝัง → 153 รัว | มีแต่คลิปฝังได้ → เล่นได้ |
| quota/perf | — | cache 24h, miss ครั้งแรกช้า ~1-2s |

## Assumptions & Risks

- **Assumed:** oEmbed `401/404` = ฝังไม่ได้จริง (verified 18/18)
- **Risk:** oEmbed ช้าทำ hits ช้า → timeout 3s + cache 24h รับมือ

## Impact

- แตะ `views.py` + `tests.py` เท่านั้น

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[oEmbed helper + search filter]** - Lane A | Can run together: none | Must wait for: none | TDD slice: 401 filtered -> add helper -> `manage.py test`
2. **[Hits filter + tests]** - Lane A | Can run together: none | Must wait for: Task 1 | TDD slice: spam compilation out -> extend filter -> `manage.py test`

---

### Task 1: oEmbed helper + search filter

**Files:**

- Modify: `music/views.py` (`_is_embed_ok` + use in `youtube_api_search`), `music/tests.py`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `views.py`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

Mock `urllib.request.urlopen` for oEmbed: 401 → filtered; 200 → kept; exception → kept.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL.

- [ ] **Step 3: Implement the minimal code**

`_is_embed_ok`: cache check → oEmbed GET timeout 3 → True/False/None. In `youtube_api_search` loop: `if _is_embed_ok(video_id) is False: continue`.

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test` + `check`.

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 2: Hits filter + tests

**Files:**

- Modify: `music/views.py` (hits merged/dedup/pad loops), `music/tests.py`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1`
- Race risk: `views.py`

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

`hits` with mocked live Longplay-spam (oEmbed 401) → not in results; static fallback still present.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test`. Expected: FAIL.

- [ ] **Step 3: Implement the minimal code**

Add `and _is_embed_ok(r['id']) is not False` to hits `filtered_cached`, `results`, `dedup`, pad loops. Static `_fallback_static` untouched.

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v1` all PASS + `check`.

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.
