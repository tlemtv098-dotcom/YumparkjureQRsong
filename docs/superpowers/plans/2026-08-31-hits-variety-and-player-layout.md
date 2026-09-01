# Hits Variety and Player Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เพลงแนะนำ 10 เพลงสุ่มไม่ซ้ำเมื่อรีเฟรช และหน้า player เห็นชื่อเพลง 2 บรรทัด ย้ายปุ่มลงล่าง ลบปุ่มคัดลอกลิ้ง

**Estimated tasks:** 3 | **Estimated time:** ~45 min | **Touches:** API / Frontend / Tests

## Current Problem / Current Solution

- `hits` ใช้ cache 60 วิ + `random.choice` 1 query จาก 6 ได้ 5-8 เพลง บางครั้งสุ่มได้ชุดเดิมซ้ำ รีเฟรชแล้วเจอเพลงเดิม
- `player.html` Now Playing `truncate` บรรทัดเดียว ปุ่ม `volume/ออโต้/🔗/ข้าม` อยู่บรรทัดเดียวกันเบียด ชื่อยาวๆ ถูกตัด
- ปุ่มคัดลอกลิ้ง `shareCurrentSong` ไม่ได้ใช้แล้ว อยากเอาออก

## Proposed Approach

- **Hits variety:** ใน `music/views.py` `hits` เพิ่ม `max_results` จาก 8 เป็น 10, สุ่ม 2-3 query แทน 1, รวมผลแล้ว `shuffle` + `dict` dedup ด้วย `video_id` + กรอง `_is_album_title` + `_is_blocked` แล้ว `cache` แยกต่อ genre+query combo, `out = results[:10]` ไม่ซ้ำ
- **Player layout:** ใน `music/templates/music/player.html` Now Playing เปลี่ยน `truncate` เป็น `line-clamp-2` หรือ `whitespace-normal break-words` 2 บรรทัด `flex-col` ปุ่มย้ายลงบรรทัดใหม่ `flex flex-wrap gap-2 mt-2` ใต้ title, ลบปุ่ม `shareCurrentSong` (`🔗`) ออกทั้ง HTML + JS `shareCurrentSong` + `navigator.share` ที่เกี่ยวข้อง (เก็บ `navigator.clipboard` อื่นไว้ถ้าไม่มี)
- **Keep:** `blockedVideoIds`, `isAlbumLike`, `auto-random` ไม่แตะ

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| กดรีเฟรชเพลงแนะนำ | ได้ 5 เพลงเดิมซ้ำ | ได้ 10 เพลงสุ่มไม่ซ้ำ |
| ชื่อเพลงยาว "รวมเพลงเพราะๆ 2025..." | ตัด `...` | เห็น 2 บรรทัดเต็ม |
| ปุ่ม ตอนนี้ | อยู่ข้าง title เบียด | อยู่บรรทัดล่างใต้ title สะอาด |
| ปุ่มคัดลอกลิ้ง | มี 🔗 | ไม่มี |

## Assumptions & Risks

- **Assumed:** YouTube API quota พอสำหรับดึง 10 เพลงต่อครั้ง (ยังใช้ cache 60 วิ)
- **Risk:** เพิ่มจาก 5 เป็น 10 เพลงอาจเพิ่มเวลา `search_youtube` เล็กน้อย แต่ cache ช่วย
- **Risk:** ลบปุ่ม share อาจทำให้ test ที่เช็ค 🔗 fail ต้องอัปเดต test

## Impact

- เพลงแนะนำหลากหลายขึ้น
- เห็นชื่อเพลงชัดขึ้น
- ลดปุ่มไม่จำเป็น

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development

1. **[Hits 10 non-duplicate]** - Lane A | Can run together: Task 2 | Must wait for: none | TDD slice: test hits returns 10 unique ids -> increase to 10 + shuffle dedup -> `manage.py test`
2. **[Player layout title 2 lines + buttons below]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: test title has line-clamp-2 and no share button -> change HTML -> `manage.py test`
3. **[Remove share button JS]** - Lane C | Can run together: Task 2 | Must wait for: Task 2 | TDD slice: test no shareCurrentSong -> remove JS -> `manage.py test`

---

### Task 1: Hits 10 non-duplicate

**Files:**

- Modify: `music/views.py` (`hits`, `search_youtube` max_results)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 2
- Must wait for: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_hits_returns_10_unique():
  res = client.get('/api/hits/')
  ids = [r['id'] for r in res.json()['results']]
  assert len(ids) == len(set(ids))
  assert len(ids) >= 8
```

- [ ] **Step 2: FAIL** (currently 5)

- [ ] **Step 3: Implement**

In `hits`: `results = search_youtube(query, 10)` already 10, but `out = results[:8]` -> change to `[:10]`, and before cache, do `seen=set(); dedup=[]; for r in results: if r['id'] not in seen and not _is_album_title(r['title']): dedup.append(r); seen.add(r['id'])` and `random.shuffle(dedup)` then `out = dedup[:10]`.

- [ ] **Step 4: PASS**

---

### Task 2: Player layout title 2 lines + buttons below

**Files:**

- Modify: `music/templates/music/player.html` (Now Playing div)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 1
- Must wait for: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_player_title_two_lines_and_no_share():
  res = client.get('/')
  assert 'line-clamp-2' in res.content.decode() or 'whitespace-normal' in res.content.decode()
  assert 'shareCurrentSong' not in res.content.decode()
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

Change Now Playing HTML from:
```
<div class="flex items-center justify-between">
  <div class="flex-1 min-w-0"><h2 class="truncate">...</h2></div>
  <div class="flex gap-2"><input><button>ออโต้</button><button>🔗</button><button>ข้าม</button></div>
</div>
```
To:
```
<div class="flex flex-col gap-2">
  <h2 class="whitespace-normal break-words line-clamp-2">...</h2>
  <div class="flex flex-wrap items-center gap-2"><input><button>ออโต้</button><button>ข้าม</button></div>
</div>
```
Remove share button HTML.

- [ ] **Step 4: PASS**

---

### Task 3: Remove share button JS

**Files:**

- Modify: `music/templates/music/player.html` (JS shareCurrentSong)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 2
- Must wait for: Task 2

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_no_share_js():
  res = client.get('/')
  assert 'shareCurrentSong' not in res.content.decode()
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

Remove `function shareCurrentSong(){...}` and `navigator.share` block entirely.

- [ ] **Step 4: PASS**

