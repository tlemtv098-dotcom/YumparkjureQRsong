# Queue Status Auto-Hide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the "เพิ่มเพลงเข้าคิวแล้ว! คิวของคุณ: ลำดับที่ X" status panel on the request page disappear automatically a few seconds after showing the queue position.

**Estimated tasks:** 1 | **Estimated time:** ~15 min | **Touches:** Frontend (template JS)

## Current Problem / Current Solution

`music/templates/music/request.html` shows a sticky result panel (`#result-panel`) after a customer requests a song. The panel displays the queue position and stays visible forever (comments on lines 44 and 249 explicitly say "ค้างไว้ ไม่หายเอง"). `updateMyStatus()` polls `/api/queue/` every 3 seconds indefinitely via a global `setInterval`, keeping the panel updated until the song plays. The panel never disappears on its own.

## Proposed Approach

- `showResult(songId)` shows the panel and starts the polling interval.
- `updateMyStatus()` continues to fetch the queue and display the position, but only while the panel is visible.
- A timer (3.5 seconds) hides the panel, stops the polling interval, and clears `mySongId`.
- Remove the global `setInterval(updateMyStatus, 3000)` so polling only runs while the panel is shown.
- Update the two comments that say "ค้างไว้ ไม่หายเอง" to reflect the new auto-hide behavior.

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| Customer requests a song | Panel shows "เพิ่มเพลงเข้าคิวแล้ว! คิวของคุณ: ลำดับที่ X" and stays forever, polling every 3s | Panel shows the same message for ~3.5s, then hides itself and stops polling |
| Customer requests another song while panel visible | Panel updates to new position | Timer resets; panel shows new position then hides again |
| Song plays while panel visible | Panel switches to "กำลังเล่นเพลงของคุณ!" / "เพลงของคุณเล่นแล้ว" | Panel may briefly show these states but hides after ~3.5s regardless; the "played" notification no longer persists |

## Assumptions & Risks

- **Assumed:** 3.5 seconds is enough for the customer to read the queue position (user chose "3-4 วิ แล้วหาย").
- **Assumed:** The "เพลงของคุณเล่นแล้ว" persistent notification is no longer needed — it only existed because the panel stayed forever. This is a direct consequence of the user's chosen behavior.
- **Risk:** If the queue fetch is slow, the position may appear late and the panel could hide before the customer reads it. Mitigation: the 3.5s timer starts at `showResult`, and the initial "เพิ่มเพลงเข้าคิวแล้ว!" text shows immediately, so the panel is never empty.
- **Risk:** JS behavior in a Django template is not covered by the Django test suite; verification is manual browser testing plus a template-render smoke test.

## Impact

- `music/templates/music/request.html` — only file changed.
- No backend/API changes; `/api/queue/` behavior unchanged.
- Fewer wasted `/api/queue/` requests (polling stops when panel hides).
- The "เพลงของคุณเล่นแล้ว" persistent message is removed as a side effect.

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **Auto-hide queue status panel** - Lane A | Can run together: none | Must wait for: none | TDD slice: template-render smoke test (RED: assert panel markup exists) -> JS auto-hide logic -> manual browser verification

---

### Task 1: Auto-hide queue status panel

**Files:**

- Modify: `music/templates/music/request.html` (lines 44-45 comment, lines 249-277 JS functions, line 277 global interval)
- Test: `music/tests.py` (add a template-render smoke test)

**Parallelization:**

- Can run with: `none`
- Must wait for: `none`
- Race risk: `none` (single file, single worker)

- [ ] **Step 0: Load the TDD discipline**

This task is frontend JS inside a Django template. The auto-hide DOM behavior is not unit-testable with Django's test framework, so the RED step is a template-render smoke test that pins the panel markup and the JS hooks; the actual auto-hide behavior is verified manually in a browser (documented exception to the failing-behavior-test rule, with the smallest meaningful verification command below).

- [ ] **Step 1: Write the failing test**

Add to `music/tests.py`:

```python
from django.test import TestCase
from django.urls import reverse

class RequestPageTemplateTest(TestCase):
    def test_request_page_has_result_panel(self):
        response = self.client.get(reverse('request'))
        self.assertContains(response, 'id="result-panel"')
        self.assertContains(response, 'showResult')
        self.assertContains(response, 'updateMyStatus')
```

Check `music/urls.py` for the URL name of `request_view` first; if the name differs, use the actual name (e.g. `'request'`).

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

```powershell
venv\Scripts\python.exe manage.py test music.tests.RequestPageTemplateTest
```

Expected result: FAIL because the test does not exist yet (or passes trivially if the template already contains these strings — in that case the smoke test is a regression pin, and the real verification is the manual browser check in Step 4).

- [ ] **Step 3: Implement the minimal code**

In `music/templates/music/request.html`:

1. Update the comment on line 44 to remove "ค้างไว้ ไม่หายเอง" (e.g. "แสดงสถานะคิว แล้วหายเองอัตโนมัติ").
2. Replace the `showResult` / `updateMyStatus` block (lines 249-277) so that:
   - `showResult(songId)` sets `mySongId`, shows the panel with "✅ เพิ่มเพลงเข้าคิวแล้ว!", calls `updateMyStatus()`, starts `myStatusTimer = setInterval(updateMyStatus, 3000)`, and starts `hideTimer = setTimeout(hideResultPanel, 3500)`.
   - `hideResultPanel()` hides the panel (`classList.add('hidden')`), clears both timers, and resets `mySongId = null`.
   - `updateMyStatus()` keeps the existing queue-position logic (idx === -1 / idx === 0 / else branches) but no longer needs the `mySongId = null` reset on idx === -1 (the hide timer handles cleanup).
   - Remove the global `setInterval(updateMyStatus, 3000)` at line 277.
   - Add `let myStatusTimer = null; let hideTimer = null;` to the variable declarations near line 80.
3. If the user requests another song while the panel is visible, `showResult` must clear the previous `hideTimer`/`myStatusTimer` before starting new ones (prevents the old timer from hiding the new message early).

- [ ] **Step 4: Run the test and confirm it passes**

```powershell
venv\Scripts\python.exe manage.py test music.tests.RequestPageTemplateTest
```

Expected result: PASS.

Then verify the auto-hide behavior manually in a browser:

1. Start the server: `venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000`
2. Open `http://localhost:8000/request/`.
3. Search for a song and click "ขอเพลง".
4. Confirm the panel shows "เพิ่มเพลงเข้าคิวแล้ว! คิวของคุณ: ลำดับที่ X".
5. Confirm the panel disappears on its own after ~3.5 seconds.
6. Confirm no console errors and that `/api/queue/` polling stops after the panel hides (check Network tab).

- [ ] **Step 5: Refactor only after green**

Keep the change minimal. Do not touch `fetchNowPlaying` (its own 3s interval is a separate feature and must stay). Rerun the smoke test after any refactor.