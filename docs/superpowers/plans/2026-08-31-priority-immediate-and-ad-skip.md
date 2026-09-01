# Priority Immediate Play and Ad Skip Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** กด เล่น (ข้ามคิว) แล้วหยุดเพลงปัจจุบันเล่นเพลงใหม่ทันที และพยายามข้ามโฆษณาเมื่อมีปุ่ม Skip

**Estimated tasks:** 2 | **Estimated time:** ~40 min | **Touches:** Frontend (player)

## Current Problem / Current Solution

- กด `เล่น (ข้ามคิว)` / `เล่นทันที (ข้ามคิว)` เรียก `/api/add-front/` แล้ว `fetchQueue` รอเพลงปัจจุบันจบถึงเล่นเพลงใหม่ ผู้ใช้รู้สึกว่าไม่ข้ามคิวทันที
- เพลงที่มีโฆษณา YouTube ไม่มี logic พยายามข้าม ต้องรอโฆษณาจบ

## Proposed Approach

- **Priority immediate:** ใน `player.html` `playPriority` หลัง `fetch /api/add-front` สำเร็จ ให้ `skipSong()` เพลงปัจจุบัน (removePlayedSong) แล้ว `fetchQueue` + `playNext(true)` ทันที เพื่อตัดเพลงปัจจุบันเล่นเพลงใหม่เลย
- **Ad skip:** ใน `player.html` เพิ่ม `onPlayerStateChange` ตรวจโฆษณา: `if (player.getVideoData().isAd)` หรือ `player.getPlayerState() === YT.PlayerState.BUFFERING && document.querySelector('.ytp-ad-skip-button')` ให้ `setInterval` ทุก 500ms เช็คปุ่ม `.ytp-ad-skip-button` ถ้าเจอให้ `click()` อัตโนมัติ

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| กดข้ามคิวตอนเพลงเล่นอยู่ | รอจบ | ตัดแล้วเล่นใหม่ทันที |
| เพลงมีโฆษณา 5 วิข้ามได้ | รอ 5 วิ | กดข้ามให้เอง |

## Assumptions & Risks

- **Assumed:** YouTube ไม่อนุญาตข้ามโฆษณาที่ห้ามข้ามได้ แค่ข้ามเมื่อมีปุ่ม
- **Risk:** ตัดเพลงปัจจุบันอาจทำให้เพลงหายจากคิว ต้อง `removePlayedSong` แค่ตัวปัจจุบัน

## Impact

- ข้ามคิวทันทีตามที่ขอ
- โฆษณาข้ามเร็วขึ้นเมื่อมีปุ่ม

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development

1. **[Priority immediate]** - Lane A | Can run together: Task 2 | Must wait for: none | TDD slice: test playPriority calls skipSong -> add immediate play -> `manage.py test`
2. **[Ad skip]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: test ad skip interval exists -> add interval -> `manage.py test`

---

### Task 1: Priority immediate

**Files:**

- Modify: `music/templates/music/player.html` (`playPriority`)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 2
- Must wait for: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_priority_plays_immediately():
  res = client.get('/')
  assert 'skipSong' in res.content.decode() and 'playPriority' in res.content.decode()
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

In `playPriority` after `showToast` and `fetchQueue`, add `if (currentSong) skipSong();` then `setTimeout(()=>playNext(true), 300)` to play new front song immediately.

- [ ] **Step 4: PASS**

---

### Task 2: Ad skip

**Files:**

- Modify: `music/templates/music/player.html` (add ad skip interval)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 1
- Must wait for: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_ad_skip_present():
  res = client.get('/')
  assert 'ytp-ad-skip-button' in res.content.decode()
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

Add `setInterval(()=>{ const btn=document.querySelector('.ytp-ad-skip-button'); if(btn) btn.click(); }, 500);` after player init, and also check `player.getVideoData().isAd`.

- [ ] **Step 4: PASS**

