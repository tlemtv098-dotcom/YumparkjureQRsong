# Dark/Light Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้างโหมดทีมดาก/ขาวทั้งสองหน้า player และ request เริ่มขาว มีปุ่มสลับจำใน localStorage

**Estimated tasks:** 2 | **Estimated time:** ~40 min | **Touches:** Frontend (player, request) / Tests

## Current Problem / Current Solution

- ทั้งสองหน้าใช้ `bg-gradient-to-br from-slate-50 via-white to-amber-50` โทนขาวอย่างเดียว ไม่มีโทนดาก
- ไม่มีปุ่มสลับและไม่มีการจำค่า

## Proposed Approach

- **Tailwind darkMode:** ใช้ `class` strategy (`tailwind.config = {darkMode: 'class'}`) เพิ่ม toggle ปุ่ม `🌙/☀️` ข้าง header ทั้งสองหน้า คลิกแล้ว `document.documentElement.classList.toggle('dark')` + `localStorage.setItem('theme','dark'|'light')` + `matchMedia` ไม่ใช้
- **CSS:** เพิ่ม `dark:` variant สำหรับ `bg`, `text`, `border` หลักๆ: `dark:bg-slate-900 dark:text-slate-100` สำหรับ body, `dark:bg-slate-800` สำหรับ card, `dark:border-slate-700`
- **Default:** อ่าน `localStorage.getItem('theme')` ถ้า `dark` ให้เพิ่ม `dark` class ตั้งแต่ `DOMContentLoaded` ก่อน render

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| เข้าเว็บครั้งแรก | ขาว | ขาว |
| กดปุ่มสลับ | ไม่มี | สลับดาก/ขาว จำไว้ |
| เปิดใหม่ | ขาว | จำค่าดาก/ขาวที่เลือก |

## Assumptions & Risks

- **Assumed:** ใช้ Tailwind CDN `darkMode: 'class'` ได้ ไม่ต้อง build ใหม่
- **Risk:** เพิ่ม `dark:` ทุก card อาจตกหล่นบางจุด ต้องเทสทั้งสองหน้า

## Impact

- รองรับโทนดาก/ขาวทั้งสองหน้า

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development

1. **[Player dark/light]** - Lane A | Can run together: Task 2 | Must wait for: none | TDD slice: test player has theme toggle -> add toggle + dark: -> `manage.py test`
2. **[Request dark/light]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: test request has theme toggle -> add toggle + dark: -> `manage.py test`

---

### Task 1: Player dark/light

**Files:**

- Modify: `music/templates/music/player.html` (head tailwind config, header button, body dark: classes, JS toggle)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 2
- Must wait for: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_player_has_theme_toggle():
  res = client.get('/')
  assert 'theme' in res.content.decode().lower() and 'dark' in res.content.decode()
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

In `<head>` add `tailwind.config.darkMode='class'`, in `<header>` add `<button onclick="toggleTheme()" id="theme-toggle">🌙</button>`, in JS add `function toggleTheme(){ document.documentElement.classList.toggle('dark'); localStorage.setItem('theme', document.documentElement.classList.contains('dark')?'dark':'light'); updateThemeIcon(); }` and on load read `localStorage.getItem('theme')`.

Add `dark:` classes to body and cards.

- [ ] **Step 4: PASS**

---

### Task 2: Request dark/light

**Files:**

- Modify: `music/templates/music/request.html`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: Task 1
- Must wait for: none

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_request_has_theme_toggle():
  res = client.get('/request/')
  assert 'theme' in res.content.decode().lower()
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

Same as Task 1 but for request.html.

- [ ] **Step 4: PASS**

