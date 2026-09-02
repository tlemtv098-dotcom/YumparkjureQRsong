# PWA Performance SEO Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development

**Goal:** ตรวจ PWA manifest/icons sw.js cache v2 start_url, เปลี่ยน polling เป็น WebSocket ภายหลัง, เพิ่ม label/alt

**Estimated tasks:** 3 | **Estimated time:** ~60 min | **Touches:** PWA / Frontend

## Current Problem

- PWA มี manifest/sw.js v2 แต่ต้องตรวจ icons/start_url/display
- polling 3วิ หนักเมื่อลูกค้า 20คน
- searchInput ไม่มี label, thumbnail ไม่มี alt

## Proposed Approach

- **PWA:** ตรวจ `music/static/music/manifest.json` ให้มี `name, short_name, icons 192/512, start_url: "/", display: "standalone", theme_color, background_color, scope: "/"`, ตรวจ `sw.js` cache v2 มี SHELL `["/", "/request/", "/static/music/img/logo.jpg", "/static/music/manifest.json"]` และ `start_url` ถูกต้อง, เพิ่ม `icons` ถ้าขาด
- **Performance:** ตอนนี้ polling 3วิ พอได้สำหรับร้านเล็ก อนาคตถ้า 20+ คนให้เปลี่ยนเป็น Django Channels WebSocket `/ws/queue/` ส่ง queue แบบ real-time ไม่ต้อง polling
- **SEO/Accessibility:** เพิ่ม `<label for="searchInput">` หรือ `aria-label` ให้ `searchInput`/`manual-search`, เพิ่ม `alt="ปกเพลง {{title}}"` ให้ `img` thumbnail

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| PWA install | อาจขาด icons | ครบ 192/512 |
| polling 20 คน | 20*3req/3s = 20 req/3s | WebSocket 1 connection |
| searchInput | ไม่มี label | มี label/aria-label |
| thumbnail | alt="" | alt="ปกเพลง ..." |

## Assumptions & Risks

- **Assumed:** ไม่ทำ WebSocket ทันที แค่เตรียม docs ไว้ทำภายหลัง
- **Risk:** เพิ่ม label/alt อาจต้องแก้ test

## Impact

- PWA พร้อม install
- ประหยัด polling อนาคต
- Accessibility ดีขึ้น

---

## Task Overview

1. **[PWA manifest/icons]** - Lane A | Can run together: Task 3 | Must wait for: none | TDD slice: test manifest has icons -> add icons -> `manage.py test`
2. **[Performance docs]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: docs only -> create WebSocket plan doc -> `manage.py check`
3. **[SEO label/alt]** - Lane C | Can run together: Task 1 | Must wait for: none | TDD slice: test label/alt exists -> add label/alt -> `manage.py test`

---

### Task 1: PWA manifest/icons

**Files:**

- Modify: `music/static/music/manifest.json`, `music/static/music/sw.js`
- Test: `music/tests.py`

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_manifest_has_icons():
  import json, pathlib
  m=json.loads(pathlib.Path('music/static/music/manifest.json').read_text())
  assert 'icons' in m and len(m['icons'])>=2
  assert m['start_url']=='/'
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

In `manifest.json` ensure `{"name":"ร้านยำปากเจ่อ","short_name":"ยำปากเจ่อ","icons":[{"src":"/static/music/img/logo.jpg","sizes":"192x192","type":"image/jpeg"},{"src":"/static/music/img/logo.jpg","sizes":"512x512","type":"image/jpeg"}],"start_url":"/","display":"standalone","theme_color":"#f59e0b","background_color":"#ffffff","scope":"/"}`. In `sw.js` ensure `CACHE_NAME="yum-juke-v2"` and `SHELL` includes `"/","/request/","/static/music/img/logo.jpg","/static/music/manifest.json"`.

- [ ] **Step 4: PASS**

---

### Task 2: Performance docs

**Files:**

- Create: `docs/superpowers/plans/websocket-future.md`
- Test: `python manage.py check`

- [ ] **Step 0: Docs only**

- [ ] **Step 1: Create doc**

Describe WebSocket future: Django Channels, `consumers.py`, `routing.py`, `ws/queue/`.

- [ ] **Step 2: Verify**

`manage.py check` PASS.

---

### Task 3: SEO label/alt

**Files:**

- Modify: `music/templates/music/player.html`, `music/templates/music/request.html`
- Test: `music/tests.py`

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_search_has_label():
  res=client.get('/request/')
  assert 'aria-label' in res.content.decode() or '<label' in res.content.decode()
def test_thumbnail_has_alt():
  res=client.get('/')
  assert 'alt="ปกเพลง' in res.content.decode()
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

In `request.html` add `<label for="searchInput" class="sr-only">ค้นหาเพลง</label>` before input, add `aria-label="ค้นหาเพลง"` to input, add `alt="ปกเพลง {{title}}"` to img thumbnail (use `alt="{{ song.title }}"`).

In `player.html` add `aria-label="ค้นหาเพลง"` to `manual-search`, add `alt` to queue img.

- [ ] **Step 4: PASS**

