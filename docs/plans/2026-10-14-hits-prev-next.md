# Hits Prev/Next Buttons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add ◀ ▶ buttons to the request-page hits panel so visitors browse older/newer song batches without leaving the page.

**Estimated tasks:** 1 | **Estimated time:** ~30 min | **Touches:** Frontend (single template JS)

## Current Problem / Current Solution

`music/templates/music/request.html` shows max 6 hit songs with only a refresh button (`fetchHits()`, L270-285). Refresh replaces the batch; there is no way back. Server `/api/hits/` already accepts `?exclude=` (music/views.py:425) to skip seen IDs, but request-page `fetchHits()` never sends it.

## Proposed Approach

Add ◀ ▶ buttons beside refresh in the hits panel header. ▶ pushes current batch onto a capped history stack (max 5) then calls `fetchHits(fresh=true)` which appends `exclude=<shown ids>`; ◀ pops history and re-renders from memory with no network call. ◀ disabled when history empty. Reuse `filterBlockedSongs`, `renderHitList`, `.slice(0, 6)`.

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| Visitor likes none of the 6 hits | Must hit refresh, old batch lost forever | ▶ loads 6 fresh songs, ◀ returns to previous batch |
| Rapid ▶ presses | n/a | In-flight guard: only latest response renders (AbortController already exists for search; same pattern) |

## Assumptions & Risks

- **Assumed:** `/api/hits/?exclude=` returns non-overlapping batches (verified in views.py:576-595).
- **Assumed:** 5-batch memory cap keeps DOM/state light on phones.
- **Risk:** Pool exhaustion (all songs seen) → server may return repeats; acceptable, matches refresh behavior today.
- **Risk:** `requestHit(idx)` indexes into `hitSongs` — history restore must replace `hitSongs` wholesale so indices stay valid.

## Impact

- One template file changed, no API/DB/auth changes.
- No new dependencies; existing Tailwind button classes reused.

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **Hits prev/next buttons + batch history** - Lane A | Can run together: none (single task) | Must wait for: none | TDD slice: template-missing-elements test FAIL -> add buttons + history JS -> test PASS + full suite green

---

### Task 1: Hits prev/next buttons + batch history

**Files:**

- Modify: `music/templates/music/request.html` (hits header ~L175-184, JS ~L240-285)
- Test: `music/tests_request_hits_nav.py` (create)

**Parallelization:**

- Can run with: none
- Must wait for: none
- Race risk: none (single file, single task)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code. This task must follow RED -> GREEN -> REFACTOR. JS behavior is verified via rendered-template string assertions (same pattern as `music/tests_request_compact.py`, `tests_player_search_controls.py`).

- [ ] **Step 1: Write the failing test**

Create `music/tests_request_compact.py`-style file `music/tests_request_hits_nav.py`:

```python
from django.test import TestCase

class RequestHitsNavTests(TestCase):
    def page(self):
        r = self.client.get("/request/")
        self.assertEqual(r.status_code, 200)
        return r.content.decode()

    def test_prev_next_buttons_exist(self):
        html = self.page()
        self.assertIn('id="hits-prev"', html)
        self.assertIn('id="hits-next"', html)

    def test_history_stack_and_exclude_wiring(self):
        html = self.page()
        self.assertIn("hitHistory", html)
        self.assertIn("exclude=", html)

    def test_prev_disabled_when_empty(self):
        html = self.page()
        self.assertIn("hits-prev", html)
        # disabled state managed in JS; assert the updater exists
        self.assertIn("updateHitsNav", html)
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run: `venv\Scripts\python.exe manage.py test music.tests_request_hits_nav -v2`

Expected result: FAIL on missing `hits-prev` (behavior missing, not import error).

- [ ] **Step 3: Implement the minimal code**

In hits panel header beside `#refresh-hits`, add `◀` (`#hits-prev`, starts disabled) and `▶` (`#hits-next`) with existing amber button classes. JS:
- `let hitHistory = [];` (max 5, `push` current `hitSongs` before replace, `shift()` overflow).
- `fetchHits(fresh)`: when `fresh===true`, build `exclude=` from all IDs in history + current batch; on success push old batch then replace `hitSongs` + `renderHitList()` + `updateHitsNav()`.
- `hitsPrev()`: pop history into `hitSongs`, `renderHitList()`, `updateHitsNav()`; no fetch.
- `updateHitsNav()`: toggle `disabled` + opacity on `#hits-prev` by `hitHistory.length`.
- Keep `.slice(0, 6)`, `filterBlockedSongs`, `requestHit(idx)` indexing intact.

- [ ] **Step 4: Run the test and confirm it passes**

Run: `venv\Scripts\python.exe manage.py test music.tests_request_hits_nav -v2` → PASS. Then `venv\Scripts\python.exe manage.py test music -v0` → full suite green.

- [ ] **Step 5: Refactor only after green**

Nothing expected beyond matching existing code style. Re-run targeted test.
