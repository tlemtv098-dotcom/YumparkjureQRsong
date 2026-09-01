# Music Clip Filter and Loudness Normalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เอาแต่คลิปเพลงปกติ (กรอง Longplay แล้ว เก็บทุกแบบที่เป็นเพลง) และทำให้ทุกเพลงดังเท่ากันด้วย volume คงที่

**Estimated tasks:** 2 | **Estimated time:** ~30 min | **Touches:** API / Frontend

## Current Problem / Current Solution

- หน้า request ตอนนี้กรอง Longplay/รวมเพลงแล้ว แต่ `youtube_api_search` ยังไม่จำกัด `videoCategoryId=10` (Music) ทำให้บางครั้งได้คลิปที่ไม่ใช่เพลง (vlog, podcast)
- User เลือก "เอาทุกแบบที่เป็นเพลง" (B) = เก็บ MV/Lyric/Live/Shorts ขอแค่ไม่ใช่ Longplay ซึ่งกรอง Longplay แล้วพอ แต่ควรเพิ่ม `videoCategoryId=10` เพื่อเอาแต่หมวดเพลง
- เพลงแต่ละคลิปดังไม่เท่ากัน (mastering ต่าง) ตอนนี้ `player.setVolume(getSavedVolume())` ตั้งคงที่ 80 ทุกเพลงแล้ว แต่ยังไม่มีการย้ำว่า `playNext` ต้องตั้ง volume ทุกครั้งที่เล่นเพลงใหม่

## Proposed Approach

- **Clip filter:** ใน `music/views.py` `youtube_api_search` เพิ่ม `videoCategoryId: '10'` ใน params เพื่อเอาเฉพาะหมวด Music, คง keyword Longplay filter ไว้
- **Loudness:** ใน `music/templates/music/player.html` ย้ำว่า `playNext` และ `safePlayWithSound/safePlayMuted` ต้อง `player.setVolume(getSavedVolume())` ทุกครั้งก่อน `playVideo` เพื่อให้ดังเท่ากัน 80 ตลอด ไม่ต้องใช้ Web Audio API

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| ค้นหา "เพลง" | ได้คลิป vlog บ้าง | ได้แต่หมวด Music |
| เล่นเพลง A ดัง 100 เพลง B ดัง 60 | ดังไม่เท่ากัน | ตั้ง volume 80 ทุกเพลง ดังใกล้เคียงกัน |

## Assumptions & Risks

- **Assumed:** YouTube API `videoCategoryId=10` กรองได้เฉพาะเพลง ไม่ทำให้ผลลัพธ์หายหมด
- **Risk:** กรองหมวดเพลงแล้วผลลัพธ์น้อยลง แต่ยอมรับได้ตามที่เลือก B

## Impact

- หน้า request ได้แต่คลิปเพลงจริง
- ทุกเพลงดังใกล้เคียงกัน

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development

1. **[Music category filter]** - Lane A | Can run together: Task 2 | Must wait for: none | TDD slice: test /api/search returns only music category -> add videoCategoryId -> `manage.py test`
2. **[Loudness constant]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: test player setVolume called on playNext -> ensure setVolume -> `manage.py test`

---

### Task 1: Music category filter

**Files:**

- Modify: `music/views.py:69-86` (`youtube_api_search` params)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 2
- Must wait for: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_search_uses_music_category():
  # mock urllib.request.urlopen, check params contains videoCategoryId=10
  pass
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

Add `'videoCategoryId': '10'` to params dict in `youtube_api_search`.

- [ ] **Step 4: PASS**

---

### Task 2: Loudness constant

**Files:**

- Modify: `music/templates/music/player.html` (`playNext`, `safePlayMuted`, `safePlayWithSound`)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 1
- Must wait for: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_player_sets_volume_on_play():
  res = client.get('/')
  assert 'setVolume(getSavedVolume())' in res.content.decode()
```

- [ ] **Step 2: FAIL** (if not present)

- [ ] **Step 3: Implement**

Ensure `playNext` calls `player.setVolume(getSavedVolume())` before `playVideo`, and `safePlayMuted`/`safePlayWithSound` already do.

- [ ] **Step 4: PASS**

