# Local Playlist Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** หน้า player สร้าง/จัดการ/เปิด เพลย์ลิสต์ส่วนตัวใน localStorage (Q114=A)

**Estimated tasks:** 4 | **Estimated time:** ~45 min | **Touches:** Frontend only (player.html + static JS)

## Current Problem / Current Solution

- ผู้ใช้อยาก "ทำอัลบั้มเอง แบบทำริสเพลง แล้วพอจะเปิดก็เปิดริสเพลงที่ทำไว้" — ไม่มีฟีเจอร์นี้ตอนนี้
- มีคิว (`queue`) แล้วแต่หายตอน reload — ต้องการ persistence + named playlists + switch ระหว่างหลายลิสต์

## Proposed Approach

- เพิ่ม `playlistManager` module ใน `player.html` (หรือแยกไฟล์ `static/music/playlist.js` โหลดก่อน player) ใช้ `localStorage` key `ym_playlists_v1` = `{ "name": [{id,title,channel,thumb,duration},...], ... }`
- UI: sidebar/panel ด้านขวา (mobile: bottom sheet) — ปุ่ม "เพลย์ลิสต์" เปิด panel → แสดงลิสต์ + สร้างใหม่ + เลือกโหลด + ลบ + rename
- คิวปัจจุบัน → "บันทึกเป็นเพลย์ลิสต์" (prompt ชื่อ) → push เข้า storage
- โหลดเพลย์ลิสต์ → replace queue + render + auto-play ตัวแรก (ถ้า owner) / enqueue (ถ้า guest)
- Export/Import JSON (optional bonus) — ไม่บังคับใน MVP

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| Reload หน้า | คิวหาย | คิวคงอยู่ (last playlist auto-load) |
| หลาย mood | ทำซ้ำทุกครั้ง | สลับเพลย์ลิสต์ได้ทันที |
| Guest | ไม่มีอะไร | เปิดดู/เล่นได้ (ไม่ save) |

## Assumptions & Risks

- **Assumed:** localStorage ~5MB พอสำหรับหลายร้อยเพลง (แต่ละ entry ~200B)
- **Assumed:** Owner/Guest แยกสิทธิ์ save — guest เห็น/เล่นได้ แต่มองไม่เห็นปุ่ม save/delete
- **Risk:** Safari private mode block localStorage — fallback in-memory (warn toast)
- **Risk:** player.html ใหญ่แล้ว — แยก `playlist.js` โหลดแยกดีกว่า inline

## Impact

- แตะ `player.html` (inject panel + load script) + สร้าง `static/music/playlist.js` + CSS นิดหน่อย

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Playlist core module]** - Lane A | Can run together: Task 2 | Must wait for: none | TDD slice: localStorage CRUD -> write module -> manual verify
2. **[UI panel in player.html]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: panel renders -> inject HTML/JS -> manual verify
3. **[Wire queue <-> playlist]** - Sequential | Can run together: none | Must wait for: Task 1,2 | TDD slice: save queue -> load playlist -> manual verify
4. **[Owner/Guest gating + polish]** - Sequential | Can run together: none | Must wait for: Task 3 | TDD slice: guest no save btn -> owner full -> manual verify

---

### Task 1: Playlist core module

**Files:**

- Create: `music/static/music/playlist.js` (ESM, export `PlaylistManager` class)
- Modify: `music/templates/music/player.html` (add `<script type="module" src="{% static 'music/playlist.js' %}"></script>` before player script)

**Parallelization:**

- Can run with: `Task 2`
- Must wait for: `none`
- Race risk: `player.html` script tag (Task 2 also touches) — coordinate: Task 1 adds import, Task 2 adds panel HTML

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` (manual verify acceptable for localStorage UI).

- [ ] **Step 1: Write the failing test**

Manual: open console, `PlaylistManager.getAll()` → `[]`, `save('test', [{id:'abc'}])` → `getAll()` has 'test'.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

File not exist → error.

- [ ] **Step 3: Implement the minimal code**

`static/music/playlist.js`:
```js
const STORAGE_KEY = 'ym_playlists_v1';
export class PlaylistManager {
  static getAll() { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
  static save(name, songs) { const all = this.getAll(); all[name] = songs; localStorage.setItem(STORAGE_KEY, JSON.stringify(all)); }
  static load(name) { return this.getAll()[name] || []; }
  static delete(name) { const all = this.getAll(); delete all[name]; localStorage.setItem(STORAGE_KEY, JSON.stringify(all)); }
  static rename(oldName, newName) { const all = this.getAll(); if (all[oldName]) { all[newName] = all[oldName]; delete all[oldName]; localStorage.setItem(STORAGE_KEY, JSON.stringify(all)); } }
  static exportJSON() { return JSON.stringify(this.getAll(), null, 2); }
  static importJSON(json) { try { const data = JSON.parse(json); if (data && typeof data === 'object') { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); return true; } } catch { return false; } }
}
```
Add script tag in player.html head.

- [ ] **Step 4: Run the test and confirm it passes**

Reload player, console test passes.

- [ ] **Step 5: Refactor only after green**

Add try/catch for private mode, toast helper. No commit/push.

---

### Task 2: UI panel in player.html

**Files:**

- Modify: `music/templates/music/player.html` (add panel HTML + CSS + wire buttons to PlaylistManager)

**Parallelization:**

- Can run with: `Task 1`
- Must wait for: `none`
- Race risk: `player.html` (Task 1 adds script tag) — Task 1 adds import first, Task 2 adds panel after

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` (manual verify).

- [ ] **Step 1: Write the failing test**

Manual: open player, click "เพลย์ลิสต์" button → panel opens with empty state.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

No panel HTML → nothing happens.

- [ ] **Step 3: Implement the minimal code**

Panel HTML (right sidebar desktop, bottom sheet mobile):
- Header: "เพลย์ลิสต์ของฉัน" + close btn
- List: each playlist → name, count, [โหลด] [แก้ชื่อ] [ลบ]
- Footer: input ชื่อใหม่ + [สร้าง] + [บันทึกคิวปัจจุบัน] (owner only) + [Export] [Import]
- CSS: fixed right-0 top-0 h-full w-72 bg-white dark:bg-gray-900 shadow-lg z-50 transform transition-transform (mobile: bottom-0 left-0 right-0 h-auto max-h-96)
- JS: `document.getElementById('playlist-btn').onclick = () => panel.classList.remove('hidden')` etc, call PlaylistManager methods, re-render list

- [ ] **Step 4: Run the test and confirm it passes**

Reload, panel works, CRUD works.

- [ ] **Step 5: Refactor only after green**

Polish animations, empty state illustration. No commit/push.

---

### Task 3: Wire queue <-> playlist

**Files:**

- Modify: `music/templates/music/player.html` (wire save/load buttons to actual queue data)

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1, 2`
- Race risk: `player.html` shared — run last among player.html edits

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` (manual verify).

- [ ] **Step 1: Write the failing test**

Manual: add 3 songs to queue, click "บันทึกคิวปัจจุบัน" → name "My Mix" → appears in panel → reload → click "โหลด" → queue has 3 songs.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Buttons not wired.

- [ ] **Step 3: Implement the minimal code**

- Save: `const songs = currentQueue.map(s => ({id:s.id, title:s.title, channel:s.channel, thumb:s.thumb, duration:s.duration})); PlaylistManager.save(name, songs); renderPanel(); toast('Saved');`
- Load: `const songs = PlaylistManager.load(name); if (isOwner) { replaceQueue(songs); playIndex(0); } else { enqueueSongs(songs); } renderQueue(); toast('Loaded');`
- Auto-load last playlist on init (optional): `const last = localStorage.getItem('ym_last_playlist'); if (last) load(last);`

- [ ] **Step 4: Run the test and confirm it passes**

Full cycle works.

- [ ] **Step 5: Refactor only after green**

Dedup on load, preserve order. No commit/push.

---

### Task 4: Owner/Guest gating + polish

**Files:**

- Modify: `music/templates/music/player.html` (conditional render save/delete/rename buttons)

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 3`
- Race risk: `player.html` shared — run last

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` (manual verify).

- [ ] **Step 1: Write the failing test**

Manual: open as guest (no `isOwner` flag) → panel shows load only, no save/delete/rename/create.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Buttons visible to all.

- [ ] **Step 3: Implement the minimal code**

Template: `{% if is_owner %}` wrap save/delete/rename/create buttons + "บันทึกคิวปัจจุบัน". Guest sees list + load + export/import only.
JS: check `window.IS_OWNER` (set in template) before enabling mutating actions.

- [ ] **Step 4: Run the test and confirm it passes**

Owner full, guest read-only.

- [ ] **Step 5: Refactor only after green**

Toast i18n, keyboard shortcuts (optional). No commit/push.