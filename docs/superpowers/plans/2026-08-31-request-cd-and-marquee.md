# Request CD and Marquee Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** หน้า request โชว์เพลงที่เล่นเพลงเดียวด้วยโปรไฟล์แผ่น CD หมุนและชื่อเพลงเลื่อน

**Estimated tasks:** 2 | **Estimated time:** ~30 min | **Touches:** Frontend (request)

## Current Problem / Current Solution

- หน้า request มี `now-playing-card` โชว์ "เพลงถัดไปในคิว" แบบ static ไม่มี CD หมุน ไม่มีข้อความเลื่อน, มี `result-panel` และ `queue` ซ้ำ

## Proposed Approach

- **CD หมุน:** ใน `request.html` `now-playing-card` เปลี่ยนเป็น layout `flex` มี `<img id="now-playing-thumb" class="w-16 h-16 rounded-full animate-spin" style="animation-duration: 3s">` หมุนเมื่อมีเพลงเล่น หยุดเมื่อไม่มี
- **Marquee:** ชื่อเพลง `<p id="now-playing-title" class="whitespace-nowrap animate-marquee">` ใช้ CSS `@keyframes marquee {0%{transform:translateX(100%)} 100%{transform:translateX(-100%)}}` เลื่อนเมื่อยาว
- **ลบคิว:** เอา `queue` ตารางออก โชว์แค่เพลงที่เล่น

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| มีเพลงเล่น | โชว์คิวตาราง | โชว์ CD หมุน + ชื่อเลื่อน |
| ไม่มีเพลง | โชว์ "ไม่มีเพลงในคิว" | โชว์ CD หยุด + "รอเพลง" |

## Assumptions & Risks

- **Assumed:** ใช้ CSS spin 3s พอ ไม่ต้อง JS ควบคุม rotation
- **Risk:** Marquee ยาวเกินอาจบัง ต้อง `overflow-hidden`

## Impact

- สวยงามเหมือนเล่นอยู่

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development

1. **[CD spin]** - Lane A | Can run together: Task 2 | Must wait for: none | TDD slice: test CD exists -> add CD -> `manage.py test`
2. **[Marquee]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: test marquee exists -> add marquee -> `manage.py test`

---

### Task 1: CD spin

**Files:**

- Modify: `music/templates/music/request.html` (`now-playing-card`)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 2
- Must wait for: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_request_has_cd():
  res = client.get('/request/')
  assert 'now-playing-thumb' in res.content.decode() and 'animate-spin' in res.content.decode()
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

In `now-playing-card` add `<img id="now-playing-thumb" src="" class="w-16 h-16 rounded-full object-cover animate-spin" style="animation-play-state: paused">` and JS toggling `animationPlayState = 'running'` when song plays.

- [ ] **Step 4: PASS**

---

### Task 2: Marquee

**Files:**

- Modify: `music/templates/music/request.html` (CSS + title)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 1
- Must wait for: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_request_has_marquee():
  res = client.get('/request/')
  assert 'animate-marquee' in res.content.decode()
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

Add `<style>@keyframes marquee{0%{transform:translateX(100%)}100%{transform:translateX(-100%)}} .animate-marquee{animation: marquee 8s linear infinite;}</style>` and `id="now-playing-title"` add `animate-marquee whitespace-nowrap overflow-hidden`.

- [ ] **Step 4: PASS**

