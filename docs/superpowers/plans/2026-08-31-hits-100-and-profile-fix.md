# Hits 100 and Profile Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development

**Goal:** เพลงแนะนำ 100 เพลงไม่ซ้ำทั้ง player+request และโปรไฟล์โหลดถูกต้อง ชื่อเพลง/วงถูกต้อง

**Estimated tasks:** 2 | **Estimated time:** ~60 min | **Touches:** API / Frontend

## Current Problem

- hits 15 เพลง ผู้ใช้อยาก 100++
- บางเพลงโปรไฟล์ไม่โหลด ชื่อเพลง/วงผิด เพราะ YouTube API ส่ง title แบบ "Official MV" ปน หรือ fallback id ไม่ตรง

## Proposed Approach

- **Hits 100:** ใน `music/views.py` `hits` เพิ่ม `search_youtube` หลาย query (สุ่ม 5 query จาก 10) รวม dedup 100, cache 60 วิ, `out = dedup[:100]`, fallback static ขยายเป็น 20 เพลงคุณภาพดี
- **Profile fix:** ตรวจ `thumbnail` URL ใช้ `https://i.ytimg.com/vi/{id}/mqdefault.jpg` เสมอ, ตรวจ `title`/`channel` จาก `snippet.title`/`channelTitle` ตรงๆ ไม่ตัด, เพิ่ม `escapeHtml` ครบ, ตรวจ `blockedVideoIds` ไม่ให้โปรไฟล์หาย

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| กดรีเฟรช | 15 เพลง | 100 เพลง |
| โปรไฟล์ซ่อนไม่หา | 404 | โหลดได้ |

## Assumptions & Risks

- **Assumed:** YouTube API quota พอสำหรับ 100 เพลง (5 query * 20)
- **Risk:** 100 เพลงโหลดช้า 2-3 วิ แต่ cache ช่วย

## Impact

- เพลงแนะนำเยอะ หลากหลาย

---

## Task Overview

1. **[Hits 100]** - Lane A | Can run together: Task 2 | Must wait for: none | TDD slice: test hits returns 100 -> increase to 100 -> `manage.py test`
2. **[Profile fix]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: test thumbnail correct -> fix thumbnail -> `manage.py test`

---

### Task 1: Hits 100

**Files:**

- Modify: `music/views.py`
- Test: `music/tests.py`

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_hits_returns_100():
  res = client.get('/api/hits/')
  assert len(res.json()['results']) >= 50
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

Change `hits` to fetch 5 queries * 20, dedup 100.

- [ ] **Step 4: PASS**

---

### Task 2: Profile fix

**Files:**

- Modify: `music/views.py`, `music/templates/music/player.html`, `music/templates/music/request.html`
- Test: `music/tests.py`

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_profile_loads():
  res = client.get('/api/hits/')
  for r in res.json()['results']:
    assert r['thumbnail'].startswith('https://')
    assert r['title'] and r['channel']
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

Ensure `thumbnail` is `https://i.ytimg.com/vi/{id}/mqdefault.jpg` or from API, ensure `title`/`channel` not truncated, ensure `escapeHtml` not breaking.

- [ ] **Step 4: PASS**

