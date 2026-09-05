# README Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** README ตรงระบบปัจจุบันทั้งไฟล์ (Q45=A)

**Estimated tasks:** 1 | **Estimated time:** ~20 min | **Touches:** Docs

## Current Problem / Current Solution

- `README.md` ตกยุค: บอก 42 tests (จริง 68), ขาด multi-key rotation, search retry/abort, fallback 15, unblock endpoint, AI recommend, dark mode, CD spin, queue move, auto-random, ad skip, Media Session, device matrix, Render URL, PLAYER_TOKEN env

## Proposed Approach

- เขียน `README.md` ใหม่ทั้งไฟล์ภาษาไทย โครงเดิม (ฟีเจอร์/Stack/โครงสร้าง/ติดตั้ง/Routing/Model/ทดสอบ) + อัปเดตตัวเลขและฟีเจอร์ใหม่ทั้งหมด + ตาราง env (`YOUTUBE_API_KEY`, `YOUTUBE_API_KEY_2`, `PLAYER_TOKEN`, `PUBLIC_URL`) + สถานะภาพรวม (test 68 OK, Live Render)
- Docs-only ไม่แตะโค้ด

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| อ่าน README | 42 tests, ไม่มี rotation/dark/AI | 68 tests + ภาพรวมปัจจุบันครบ |

## Assumptions & Risks

- **Assumed:** ข้อมูลจากโค้ดปัจจุบัน + git log (Q45)
- **Risk:** ไม่มี — docs-only

## Impact

- เอกสารตรงระบบจริง

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Rewrite README]** - Lane A | Can run together: none | Must wait for: none | TDD slice: docs-only exception -> rewrite file -> verify README + `manage.py test`

---

### Task 1: Rewrite README

**Files:**

- Modify: `README.md`
- Test: `music/tests.py` (run only, no change)

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none`

- [ ] **Step 0: Load the TDD discipline**

Docs-only exception: no failing behavior test appropriate (no prod code change). Verification = README contains current sections + `manage.py test` still green.

- [ ] **Step 1: Rewrite the file**

Rewrite `README.md` (TH): ภาพรวมระบบ + ฟีเจอร์ปัจจุบันทั้งหมด (player/request/queue/QR/PWA/153 soft-skip+guard/block-clear endpoint/multi-key rotation/search abort+retry/fallback 15/dark mode/CD spin/queue move/auto-random/ad skip/Media Session/AI recommend/device matrix) + Stack + โครงสร้าง + env table + Routing (รวม `/api/ai/recommend/`, `/api/queue/move/`, `/api/block/clear/`) + Model (SongQueue + BlockedVideo) + วิธีรัน + test 68 + Render URL + ข้อจำกัด (iOS tap, quota 100/ครั้ง, cold start).

- [ ] **Step 2: Verify**

`README.md` มีครบทุกหัวข้อ + `venv\Scripts\python.exe manage.py test music.tests -v2` PASS. No commit/push.
