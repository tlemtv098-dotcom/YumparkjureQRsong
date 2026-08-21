# ปรับปรุง UI หน้า player + request (Jukebox UI Redesign) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ตกแต่งหน้า `player.html` และ `request.html` ใหม่ (UI เท่านั้น) ด้วยธีมดาร์ก-ชมพู/ม่วงแบบพรีเมียม พร้อมวางรูปปก 2 รูป (1.png, 2.jpg) เป็นแบนเนอร์/hero บนทั้งสองหน้า

**Estimated tasks:** 4 | **Estimated time:** ~60 min | **Touches:** Frontend (2 templates) / Tests / Static assets

## Current Problem / Current Solution

ปัจจุบันทั้งสองหน้าใช้ Tailwind CDN แบบพื้นฐาน: `player.html` มีพื้น slate-900 เรียบ ๆ วิดีโอ + การ์ด QR/คิวธรรมดา ส่วน `request.html` พื้นม่วงเข้มเรียบ ๆ ฟอร์มค้นหาธรรมดา ไม่มีภาพโปรโมตแบรนด์เลย และตอนไม่มีเพลงเล่นจอจะว่าง/ดำ

## Proposed Approach

เปลี่ยนเป็นธีมดาร์กพรีเมียม (gradient พื้น + การ์ดกระจก + ฟอนต์ไทย "Prompt" จาก Google Fonts):

- **หน้า player:** แถวแบนเนอร์ 2 รูปด้านบนสุด + วิดีโอใหญ่ + แถบ "กำลังเล่น" สไตล์ glass + คอลัมน์ขวา (QR + คิว) + **Idle splash** — ตอนไม่มีเพลงเล่น จะแสดง 2 รูปเต็มจอพร้อมข้อความ "สแกน QR เพื่อขอเพลง" แทนจอดำ
- **หน้า request:** Hero แบนเนอร์ 2 รูปบนสุด + ข้อความแบรนด์ + ฟอร์มค้นหา/การ์ดผลลัพธ์สไตล์ glass
- ฟังก์ชัน JS ทั้งหมด (เล่น/ค้นหา/คิว/QR) คงเดิม — เปลี่ยนเฉพาะ HTML/CSS และ toggle idle splash
- รูปอ้างอิงผ่าน `{% static %}` พร้อม `onerror` fallback (รูปหาย → ซ่อน ไม่พัง)

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| เปิดหน้า `/` บนจอทีวี | พื้นเรียบ ๆ วิดีโอ + การ์ด QR/คิว ธรรมดา | แบนเนอร์ 2 รูปบนสุด + วิดีโอ + การ์ด glass สวยขึ้น |
| ไม่มีเพลงเล่น (idle) | จอว่าง แสดงข้อความ "รอเพลงจากลูกค้า..." เล็ก ๆ | Idle splash เต็มจอ: 2 รูปใหญ่ + QR + ข้อความ "สแกน QR เพื่อขอเพลง" |
| เปิดหน้า `/request/` บนมือถือ | พื้นม่วงเรียบ ฟอร์มค้นหาธรรมดา | Hero 2 รูปบนสุด + ฟอร์ม/การ์ด glass |
| รูป 1.png / 2.jpg หาย | - (ไม่มีรูปเดิม) | fallback ซ่อนรูป หน้าใช้งานปกติ |

## Assumptions & Risks

- **Assumed:** ผู้ใช้จะคัดลอกไฟล์ `1.png` และ `2.jpg` ไปไว้ที่ `music/static/music/img/` ตาม Task 4 (รูปไม่อยู่ในเครื่องตาม path ที่สแกนหาแล้ว)
- **Assumed:** ใช้ฟอนต์ Google Fonts "Prompt" (Thai) — ต้องมีอินเทอร์เน็ต เหมือน Tailwind CDN ที่ใช้อยู่แล้ว
- **Risk:** ถ้า `1.png`/`2.jpg` ความละเอียดต่ำหรืออัตราส่วนแปลก → แบนเนอร์/hero อาจดูไม่เป๊ะ → บรรเทาด้วย `object-cover` + fallback
- **Risk:** เปลี่ยนโครงสร้าง HTML แล้ว JS เดิมอ้าง id เดิม → ถ้าเปลี่ยน id/ชื่อฟังก์ชัน พังได้ → **ห้ามเปลี่ยน id เดิมทั้งหมด** (`player`, `now-playing-title`, `queue-list`, `queue-count`, `userName`, `searchInput`, `loading`, `results`)

## Impact

- เขียนใหม่ 2 templates: `music/templates/music/player.html`, `music/templates/music/request.html` (UI เท่านั้น)
- เพิ่มไฟล์เทส `music/tests.py` (render tests — ตรวจโครงสร้าง/static URL)
- สร้างโฟลเดอร์ static `music/static/music/img/` (สำหรับวางรูป 1.png, 2.jpg)
- **ไม่แตะ:** models, views, urls, settings, migrations, DB

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[เขียน failing render tests]** - Lane A | Can run together: Task 4 | Must wait for: none | TDD slice: เขียนเทสที่คาดเดาโครงสร้างใหม่ (ยัง fail เพราะ template เก่า) -> ยังไม่แก้ production -> run เทสให้เห็น RED
2. **[ปรับ player.html]** - Lane B | Can run together: Task 3, Task 4 | Must wait for: Task 1 (เทสต้องอยู่ก่อน) | TDD slice: เทส PlayerPageTests RED -> เขียน template ใหม่ -> เทส GREEN
3. **[ปรับ request.html]** - Lane C | Can run together: Task 2, Task 4 | Must wait for: Task 1 (เทสต้องอยู่ก่อน) | TDD slice: เทส RequestPageTests RED -> เขียน template ใหม่ -> เทส GREEN
4. **[เตรียม static folder]** - Lane D | Can run together: Task 1, 2, 3 | Must wait for: none | TDD slice: docs/config-only (สร้างโฟลเดอร์ให้ผู้ใช้วางรูป) -> ตรวจว่ามีโฟลเดอร์

---

### Task 1: เขียน failing render tests (RED)

**Files:**

- Modify: `music/tests.py`

**Parallelization:**

- Can run with: `Task 4`
- Must wait for: `none`
- Race risk: `none` (เป็นงานเดียวที่เขียน tests.py)

- [ ] **Step 0: Load the TDD discipline**

  ใช้ `superpowers:test-driven-development` ก่อนแก้ production code. งานนี้เป็นขั้นเขียนเทสล้วน (RED) — ยังไม่แตะ template.

- [ ] **Step 1: เขียน failing test** — แทนที่เนื้อหา `music/tests.py` ทั้งหมดด้วย:

```python
from django.test import TestCase

PLAYER_IMG_1 = '/static/music/img/1.png'
PLAYER_IMG_2 = '/static/music/img/2.jpg'


class PlayerPageTests(TestCase):
    def test_player_page_renders(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_player_has_banner_images(self):
        response = self.client.get('/')
        self.assertContains(response, PLAYER_IMG_1)
        self.assertContains(response, PLAYER_IMG_2)

    def test_player_has_idle_splash(self):
        response = self.client.get('/')
        self.assertContains(response, 'id="idle-splash"')

    def test_player_has_core_elements(self):
        response = self.client.get('/')
        for token in ['id="player"', 'id="queue-list"', 'id="queue-count"',
                      'id="now-playing-title"', 'src="/qr.png"']:
            self.assertContains(response, token)


class RequestPageTests(TestCase):
    def test_request_page_renders(self):
        response = self.client.get('/request/')
        self.assertEqual(response.status_code, 200)

    def test_request_has_hero_images(self):
        response = self.client.get('/request/')
        self.assertContains(response, PLAYER_IMG_1)
        self.assertContains(response, PLAYER_IMG_2)

    def test_request_has_form_elements(self):
        response = self.client.get('/request/')
        for token in ['id="userName"', 'id="searchInput"', 'id="results"', 'id="loading"']:
            self.assertContains(response, token)
```

- [ ] **Step 2: run เทสและยืนยันว่า fail ด้วยเหตุผลที่ถูกต้อง**

  รันจากโฟลเดอร์โปรเจค: `python manage.py test music`
  คาดว่า FAIL เพราะ template ปัจจุบันยังไม่มี static banner / idle-splash (ไม่ใช่ syntax/setup error)

- [ ] **Step 3-5:** งานนี้เป็นแค่เขียนเทส (RED) — จบที่ RED ได้ ไม่ต้อง GREEN

  **ห้ามแตะ template ในงานนี้** เดี๋ยว Task 2/3 จะทำ GREEN.

---

### Task 2: ปรับปรุง player.html (GREEN)

**Files:**

- Modify: `music/templates/music/player.html` (เขียนใหม่ทั้งหมด — UI เท่านั้น)
- Test: `music/tests.py` (PlayerPageTests — เขียนโดย Task 1 แล้ว)

**Parallelization:**

- Can run with: `Task 3`, `Task 4`
- Must wait for: `Task 1` (ต้องมีเทสก่อน)
- Race risk: `none` — งานนี้แตะเฉพาะ player.html (Task 3 แตะ request.html, Task 4 แตะ static folder)

- [ ] **Step 0: Load the TDD discipline** — ใช้ `superpowers:test-driven-development` ก่อนแก้ production code.

- [ ] **Step 1:** เทส RED มีอยู่แล้วจาก Task 1 (PlayerPageTests fail) — run ยืนยันก่อนแก้: `python manage.py test music.tests.PlayerPageTests`

- [ ] **Step 2:** Implement — เขียน `player.html` ใหม่ตามสเปกนี้:

  **โครงสร้าง head:**
  - `{% load static %}` บรรทัดแรกหลัง `<!DOCTYPE html>`
  - `<html lang="th">`, title เดิม
  - Google Fonts: `<link rel="preconnect" href="https://fonts.googleapis.com">`, `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>`, `<link href="https://fonts.googleapis.com/css2?family=Prompt:wght@400;600;700;900&display=swap" rel="stylesheet">`
  - Tailwind CDN + inline config ตั้งฟอนต์: `<script>tailwind.config={theme:{extend:{fontFamily:{sans:['Prompt','sans-serif']}}}}</script>`

  **body:** ฟอนต์ sans พื้น gradient `bg-gradient-to-br from-slate-950 via-slate-900 to-pink-950 text-white`

  **โครงสร้างหลัก (grid เดิม 3 คอลัมน์ รักษาไว้):**
  1. **แถวแบนเนอร์ 2 รูป (ทั้งหน้า, เหนือ grid):** `<div class="grid grid-cols-2 gap-3 md:gap-4 mb-4">` มี `<img src="{% static 'music/img/1.png' %}" ...>` และ `{% static 'music/img/2.jpg' %}` — class: `w-full h-24 md:h-32 object-cover rounded-2xl ring-2 ring-pink-500/40 shadow-lg` + `onerror="this.style.display='none'"`
  2. **หัวข้อแบรนด์:** h1 เดิม (🌶️ ร้านยำปากเจ่อ - ระบบคิวเพลง) ปรับเป็น gradient text `bg-gradient-to-r from-pink-400 to-rose-400 bg-clip-text text-transparent`
  3. **วิดีโอ (col-span-2):** คอนเทนเนอร์เดิม `aspect-video` + `id="player"` ปรับการ์ด: `bg-black rounded-2xl overflow-hidden shadow-2xl ring-1 ring-white/10 border border-slate-700`
  4. **แถบ "กำลังเล่น":** glass style `bg-white/5 backdrop-blur border border-white/10 rounded-xl` — label pink, `#now-playing-title`, ปุ่ม "ข้ามเพลง" gradient `bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500`
  5. **คอลัมน์ขวา:** การ์ด QR (glass เดียวกับแถบกำลังเล่น) + การ์ดคิว (`#queue-count`, `#queue-list` เดิม — รูป thumbnail ในคิวใช้ class เดิม) — ปรับพื้นการ์ดเป็น `bg-white/5 backdrop-blur border border-white/10`
  6. **Idle splash (ใหม่):** `<div id="idle-splash" class="hidden absolute inset-0 z-20 flex flex-col items-center justify-center gap-4 bg-gradient-to-br from-slate-950/95 to-pink-950/95">` วาง**ใน/ทับคอนเทนเนอร์วิดีโอ** (คอนเทนเนอร์วิดีโอต้อง `relative`):
     - 2 รูป: `{% static 'music/img/1.png' %}`, `{% static 'music/img/2.jpg' %}` — `w-40 h-40 md:w-56 md:h-56 object-cover rounded-2xl ring-2 ring-pink-500/60 shadow-2xl` + onerror fallback
     - ข้อความ "🎵 สแกน QR เพื่อขอเพลง" ตัวใหญ่ (text-2xl md:text-4xl font-black)
     - QR เล็ก: `<img src="/qr.png" class="w-28 h-28 md:w-36 md:h-36 rounded-xl bg-white p-1">`
     - ข้อความรอง "รอเพลงจากลูกค้า..."

  **JS (SCRIPT เดิมทั้งหมด คงเดิม) + เพิ่ม idle toggle:**
  - ใน `playNext()`: ถ้าไม่มีเพลง (`queue.length === 0`) → `document.getElementById('idle-splash').classList.remove('hidden')` และถ้ามีเพลง → `.classList.add('hidden')`
  - ตอนโหลดครั้งแรก splash โชว์อยู่แล้ว (HTML เริ่มด้วย `hidden` **ห้าม** — เริ่มโดยไม่ใส่ `hidden` จะแสดง idle ทันที) → **เริ่มต้น HTML ไม่มี class `hidden`** และ JS ซ่อนทันทีที่มีเพลง

- [ ] **Step 3:** run เทส: `python manage.py test music.tests.PlayerPageTests` → ต้อง PASS

- [ ] **Step 4:** run เทสทั้งหมด: `python manage.py test music` → ยังต้องมี FAIL เฉพาะ RequestPageTests (ยังไม่ได้ทำ Task 3) — ถ้า PlayerPageTests PASS ครบ = งานนี้ผ่าน

- [ ] **Step 5 (Refactor):** เช็คว่า id/ฟังก์ชัน JS เดิมครบ ไม่มี class ว่าง/โค้ดตายที่ตัวเองสร้าง

---

### Task 3: ปรับปรุง request.html (GREEN)

**Files:**

- Modify: `music/templates/music/request.html` (เขียนใหม่ทั้งหมด — UI เท่านั้น)
- Test: `music/tests.py` (RequestPageTests — เขียนโดย Task 1 แล้ว)

**Parallelization:**

- Can run with: `Task 2`, `Task 4`
- Must wait for: `Task 1`
- Race risk: `none` — แตะเฉพาะ request.html

- [ ] **Step 0: Load the TDD discipline** — ใช้ `superpowers:test-driven-development` ก่อนแก้ production code.

- [ ] **Step 1:** run `python manage.py test music.tests.RequestPageTests` → ยืนยัน RED (ยังไม่มี hero/static banner ใน template เดิม)

- [ ] **Step 2: Implement** — เขียน `request.html` ใหม่ตามสเปกนี้:

  **head:** เหมือน Task 2 (`{% load static %}`, Google Fonts Prompt, Tailwind CDN + config ฟอนต์)

  **body:** `bg-gradient-to-b from-purple-950 via-purple-900 to-pink-950 text-slate-100` + `font-sans`

  **โครงสร้าง (max-w-md เดิม):**
  1. **Hero 2 รูป:** `<div class="grid grid-cols-2 gap-3 pt-2">` รูป `{% static 'music/img/1.png' %}` / `{% static 'music/img/2.jpg' %}` — `w-full h-36 md:h-44 object-cover rounded-2xl ring-2 ring-pink-500/40 shadow-lg` + onerror fallback
  2. **ข้อความแบรนด์:** h1 "🌶️ ร้านยำปากเจ่อ" gradient text (pink-400 → rose-400) + subtitle เดิม
  3. **ฟอร์ม:** input `#userName` + แถวค้นหา (`#searchInput` + ปุ่ม) — ปรับเป็น glass `bg-white/10 border-white/10 focus:border-pink-400 placeholder-slate-300` ปุ่ม gradient `bg-gradient-to-r from-pink-600 to-rose-600`
  4. **ผลลัพธ์:** `#loading` เดิม, `#results` — การ์ดผลลัพธ์ปรับ glass `bg-white/5 border-white/10 backdrop-blur`
  5. **JS เดิมทั้งหมด คงเดิม** (searchMusic, requestSong — ไม่แตะ)

- [ ] **Step 3:** run `python manage.py test music.tests.RequestPageTests` → ต้อง PASS

- [ ] **Step 4:** run `python manage.py test music` → ทุกเทส PASS (ต่อจาก Task 2)

- [ ] **Step 5 (Refactor):** เช็ค id/ฟังก์ชัน JS เดิมครบ ไม่มีโค้ดตาย

---

### Task 4: เตรียม static folder สำหรับวางรูป

**Files:**

- Create: `music/static/music/img/` (โฟลเดอร์)

**Parallelization:**

- Can run with: `Task 1`, `Task 2`, `Task 3`
- Must wait for: `none`
- Race risk: `none` — โฟลเดอร์ใหม่ ไม่ชนกับไฟล์อื่น

- [ ] **Step 1:** สร้างโฟลเดอร์ (Windows PowerShell):

  ```powershell
  New-Item -ItemType Directory -Path "music\static\music\img" -Force
  ```

- [ ] **Step 2:** ตรวจ: `Test-Path -LiteralPath "music\static\music\img"` → ต้อง `True`

- [ ] **Step 3:** **แจ้งผู้ใช้**ให้คัดลอกไฟล์ `1.png` และ `2.jpg` เข้าโฟลเดอร์นี้ (คน implement ห้ามสร้างไฟล์รูปเอง — ไฟล์มาจากผู้ใช้) — ถ้ารูปยังไม่มา fallback onerror จะซ่อนรูป หน้าเว็บยังใช้งานได้

- [ ] **Step 4 (config-only note):** งานนี้เป็น docs/config-only (สร้างโฟลเดอร์รับไฟล์) ไม่ต้องเขียน behavior test — เทสโครงสร้าง HTML ที่อ้าง static path อยู่ใน Task 1 แล้ว

---

## Final Gate

- [ ] `python manage.py test music` — ทุกเทส PASS (ทั้ง PlayerPageTests และ RequestPageTests)
- [ ] เช็ค `music/static/music/img/` มีรูป 1.png, 2.jpg (หรือแจ้งผู้ใช้ว่าให้วางรูปก่อนดูผลเต็ม)
- [ ] Manual check (optional): `python manage.py runserver 0.0.0.0:8000` → เปิด `/` (ตรวจ idle splash) และ `/request/` (ตรวจ hero)
- [ ] ห้าม commit/push (โปรเจคไม่ใช่ git repo)
