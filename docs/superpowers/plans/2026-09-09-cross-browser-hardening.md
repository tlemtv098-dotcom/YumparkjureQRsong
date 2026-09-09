# Cross-Browser Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** player/request ใช้งานได้ทุกเบราว์เซอร์/ทุกเครื่อง (เก่า-ใหม่, WebView) ไม่พังทั้งหน้า

**Estimated tasks:** 3 | **Estimated time:** ~45 min | **Touches:** Frontend / Tests

## Current Problem / Current Solution

- `player.html` ใช้ `?.` (4 จุด) + `request.html` (1 จุด) — เบราว์เซอร์เก่า (iOS 12-, Android เก่า) parse ไม่ผ่าน → สคริปต์ทั้งก้อนตาย หน้าใช้งานไม่ได้เลย
- `playlist.js` ใช้ `async/fetch` หนัก (34 จุด) ไม่มี fallback
- `LINE WebView` มีแค่ banner, ไม่มีปุ่มเปิดเบราว์เซอร์จริงจัง; autoplay policy ต่างกันแต่ละที่

## Proposed Approach

- แทน `?.`/`??` ทั้งหมดใน 2 templates ด้วยเช็คธรรมดา (`&&` guard) — behavior เดิม
- เติม feature guard ตอนบูต: ถ้าไม่มี `fetch`/`URLSearchParams`/`Promise` → โชว์ข้อความไทยเตือนอัปเดตเบราว์เซอร์แทนที่จะเงียบ
- `playlist.js`: try/catch รอบ fetch + fallback localStorage (มีบางส่วนแล้ว) + guard `localStorage` เต็มรูปแบบ
- `LINE WebView`: ปุ่ม `เปิดใน Chrome/Safari` ใช้ intent/link ชัดเจน (`intent://` บน Android, ปุ่ม copy-link บน iOS)

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| เบราว์เซอร์เก่า | หน้าขาว/ปุ่มกดไม่ติด | ใช้งานหลักได้ + เตือนอัปเดต |
| LINE | banner อย่างเดียว | ปุ่มเปิดข้างนอกชัด |

## Assumptions & Risks

- **Assumed:** ไม่ต้องรองรับต่ำกว่า ES2017 จริงจัง แค่ไม่พังทั้งหน้า + ข้อความบอก
- **Risk:** แตะไฟล์ใหญ่ ระวัง Thai garble — verify ไม่มี `�` ทุกครั้ง

## Impact

- แตะ `player.html`, `request.html`, `playlist.js`, `tests.py`

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Replace ?. / ??]** - Lane A | Can run together: none | Must wait for: none | TDD slice: grep zero `?.` in templates -> replace -> `manage.py test`
2. **[Boot guards + playlist fallback]** - Lane A | Can run together: none | Must wait for: Task 1 | TDD slice: old-browser message renders -> add guards -> `manage.py check`
3. **[WebView external open]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: intent link present -> add button -> `manage.py test`

---

### Task 1: Replace ?. / ??

**Files:**

- Modify: `music/templates/music/player.html`, `music/templates/music/request.html`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 3`
- Must wait for: `none`
- Race risk: templates (one worker, sequential)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

Grep-based test: `?.` count in both templates == 0 (allow `?` in ternaries/URLs — match `?.` specifically excluding `?.`... careful: regex `\?\.`).

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test -v2`. Expected: FAIL (4+1 found).

- [ ] **Step 3: Implement the minimal code**

Replace each `a?.b` → `(a&&a.b)`, `a?.[k]` similarly, `??` → ternary. Verify behavior identical. Check no `�`.

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test` + `check`.

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 2: Boot guards + playlist fallback

**Files:**

- Modify: `music/templates/music/player.html`, `music/templates/music/request.html`, `music/static/music/playlist.js`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1`
- Race risk: same files

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` (manual for old browser).

- [ ] **Step 1: Write the failing test**

`GET /` contains `COMPAT_GUARD` marker; `GET /request/` same.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test`. Expected: FAIL.

- [ ] **Step 3: Implement the minimal code**

Head inline script (ES5 only): `if(!window.fetch||!window.URLSearchParams||!window.Promise){document.write thai warning}` — placed before main scripts. playlist.js: wrap localStorage access already try/catch — verify + add quota fallback (memory).

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test` + `check`.

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 3: WebView external open

**Files:**

- Modify: `music/templates/music/player.html`, `music/templates/music/request.html`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 1`
- Must wait for: `none`
- Race risk: templates (different lines than Task 1 — coordinate)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

`GET /request/` contains `intent://` link; player banner has external button marker.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test`. Expected: FAIL.

- [ ] **Step 3: Implement the minimal code**

WebView banner: Android → `<a href="intent://HOST/path#Intent;scheme=https;package=com.android.chrome;end">เปิดใน Chrome</a>`; iOS → copy-link button + text. Build host/path from location at runtime (no hardcode).

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test` + `check`.

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.
