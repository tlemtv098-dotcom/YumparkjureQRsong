# AI Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development

**Goal:** เพิ่ม AI ช่วยเว็บร้านยำ: แนะนำเพลงตามอารมณ์, กรองเพลงหยาบ, จัดคิวอัตโนมัติ, แชทบอท

**Estimated tasks:** 4 | **Estimated time:** ~120 min | **Touches:** Backend / Frontend

## Current Problem

- เว็บมีคิวเพลง+ค้นหาแล้ว แต่ไม่มี AI ช่วยแนะนำ/กรอง/จัดคิว

## Proposed Approach

- **AI Recommend:** ใช้ OpenAI/DeepSeek API (มี DEEPSEEK_API_KEY ใน .env) ให้ลูกค้าพิมพ์อารมณ์ "เศร้า/สนุก" แล้ว AI แนะนำ 5 เพลงจาก hits
- **AI Filter:** ใช้ AI ตรวจ title ที่หยาบ/การเมือง แล้ว block อัตโนมัติ (แทน keyword)
- **AI Queue:** จัดคิวให้หลากหลาย ไม่ให้เพลงซ้ำศิลปินติดกัน
- **AI Chat:** เพิ่มกล่องแชท "ถาม AI หาเพลง" ที่หน้า request

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| ลูกค้าพิมพ์ "อยากฟังเพลงเศร้า" | ต้องค้นหาเอง | AI แนะนำ 5 เพลงเศร้า |
| เพลงหยาบ | ต้อง manual block | AI กรองอัตโนมัติ |

## Assumptions & Risks

- **Assumed:** มี DEEPSEEK_API_KEY ใช้ได้
- **Risk:** AI อาจแนะนำเพลงไม่มีใน YouTube ต้อง fallback

## Impact

- ลูกค้าได้เพลงตรงใจขึ้น

---

## Task Overview

1. **[AI Recommend API]** - Lane A | Can run together: Task 2 | Must wait for: none | TDD slice: test /api/ai/recommend returns 5 songs -> add endpoint -> `manage.py test`
2. **[AI Filter]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: test filter blocks rude song -> add filter -> `manage.py test`
3. **[AI Chat UI]** - Lane C | Can run together: Task 1,2 | Must wait for: Task 1 | TDD slice: test request has AI chat box -> add UI -> `manage.py test`
4. **[AI Queue diversify]** - Lane D | Can run together: Task 1 | Must wait for: none | TDD slice: test queue not same artist consecutive -> add logic -> `manage.py test`

---

### Task 1: AI Recommend API

**Files:**

- Modify: `music/views.py` (add ai_recommend)
- Modify: `music/urls.py`
- Test: `music/tests.py`

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_ai_recommend():
  res = client.post('/api/ai/recommend/', data=json.dumps({"mood":"เศร้า"}), content_type='application/json')
  assert res.status_code == 200
  assert len(res.json()['songs']) == 5
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

Add `def ai_recommend(request):` call DeepSeek API with prompt "แนะนำเพลง ...", parse 5 titles, search YouTube for each, return.

- [ ] **Step 4: PASS**

---

### Task 2: AI Filter

**Files:**

- Modify: `music/views.py` (`_is_blocked` add AI check)
- Test: `music/tests.py`

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_ai_filter_blocks_rude():
  assert _is_ai_blocked("เพลงหยาบ ...") == True
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

Add `def _is_ai_blocked(title):` call DeepSeek with prompt "เพลงนี้หยาบไหม", if yes return True.

- [ ] **Step 4: PASS**

---

### Task 3: AI Chat UI

**Files:**

- Modify: `music/templates/music/request.html`
- Test: `music/tests.py`

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_request_has_ai_chat():
  res = client.get('/request/')
  assert 'AI' in res.content.decode()
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

Add `<div id="ai-chat"><input id="ai-input" placeholder="ถาม AI หาเพลง..."><button onclick="askAI()">ถาม</button><div id="ai-results"></div></div>` + JS `async function askAI(){ fetch('/api/ai/recommend/', ...) }`.

- [ ] **Step 4: PASS**

---

### Task 4: AI Queue diversify

**Files:**

- Modify: `music/views.py` (`get_queue` order)
- Test: `music/tests.py`

- [ ] **Step 0: Load TDD**

- [ ] **Step 1: Write failing test**

```python
def test_queue_diverse():
  # add 5 songs same artist, ensure queue order not same artist consecutive after AI diversify
  pass
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement**

In `get_queue` shuffle or sort to avoid same artist consecutive.

- [ ] **Step 4: PASS**

