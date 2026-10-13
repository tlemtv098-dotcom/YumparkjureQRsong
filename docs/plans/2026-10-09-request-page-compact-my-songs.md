# Request Page Compact + My-Songs Panel Move Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the request page compact (6 song rows per list), move the my-songs panel below search, and label each request with the requester's name.

**Estimated tasks:** 3 | **Estimated time:** ~60 min | **Touches:** Template (request.html) / API (views.py)

## Current Problem / Current Solution

`music/templates/music/request.html` renders three unbounded lists: search `#results` (every match), hits `#hit-list` (up to 15 from `fetchHits`), and `#my-songs-list` at the page bottom with no requester name. The page is long on phones, the my-songs panel sits far from the search action that fills it, and `requestSongData` hardcodes `requested_by: "ลูกค้าในร้าน"` while `my_songs` (`music/views.py:877`) does not even return `requested_by` — so every row would show the same generic name if displayed as-is.

## Proposed Approach

Cap the two long lists at 6 rows each via `slice(0, 6)` at the render sites (search results loop and `fetchHits`), move the existing `เพลงที่ฉันขอ` panel markup to directly below the search panel (single panel, removed from bottom), add a name input persisted in `localStorage` and sent as `requested_by`, return `requested_by` from `my_songs`, and render it in each my-songs row.

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| Customer searches "รัก" with 20 matches | 20 rows, long scroll | 6 rows |
| Hit list refresh | Up to 15 rows | 6 rows |
| After requesting a song | Must scroll to bottom to see "เพลงที่ฉันขอ" | Panel directly below search |
| My-songs rows | Title + channel + delete button | Title + channel + requester name + delete button |
| Anonymous request identity | Always "ลูกค้าในร้าน" | Name typed once, remembered per device |

## Assumptions & Risks

- **Assumed:** 6 is a fixed cap, no "show more" toggle (user asked for exactly 6 rows).
- **Assumed:** One device = one requester; `client_id` in `localStorage` stays the identity key, the name field only labels it.
- **Assumed:** `my_songs` stays anonymous-accessible (customers scan QR without login); adding `requested_by` to its `values()` leaks nothing new since names are user-supplied labels.
- **Risk:** All three tasks touch `music/templates/music/request.html` — strictly sequential, no parallel edits to that file.
- **Risk:** XSS via the name field — must go through existing `escapeHtml()` like title/channel, and server-side `_clean_text` already caps `requested_by` at 100 chars.

## Impact

- Shorter request page on phones; search and hits each max 6 rows.
- Requesters see their songs immediately below the search box with their name on each row.
- No migration, no new endpoints, no auth changes.

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **Cap search results and hits at 6 rows** - Lane A | Can run together: none (shares request.html) | Must wait for: none | TDD slice: assert rendered page has no `.slice(0, 15)` and search loop caps at 6 -> change slices -> re-run
2. **Move my-songs panel below search + name input** - Lane A | Can run together: none | Must wait for: Task 1 (same file) | TDD slice: assert single `#my-songs-list` ordered before `#hit-list`, name input persisted -> move markup + wire localStorage -> re-run
3. **Return and render requested_by** - Lane A | Can run together: none | Must wait for: Task 2 (same file) | TDD slice: assert `my_songs` JSON includes `requested_by` and POST stores a custom name -> extend `values()` + row markup -> re-run

---

### Task 1: Cap search results and hits at 6 rows

**Files:**

- Modify: `music/templates/music/request.html` (search results `forEach` ~L307, `fetchHits` `.slice(0, 15)` ~L272)
- Test: `music/tests_request_compact.py` (create)

**Parallelization:**

- Can run with: none
- Must wait for: none
- Race risk: `request.html` is also edited by Tasks 2 and 3 — this task runs first, alone

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code. This task must follow RED -> GREEN -> REFACTOR.

- [ ] **Step 1: Write the failing test**

Create `music/tests_request_compact.py`:

```python
from django.test import TestCase

class RequestCompactTests(TestCase):
    def page(self):
        response = self.client.get("/request/")
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_hit_list_caps_at_six(self):
        html = self.page()
        self.assertNotIn(".slice(0, 15)", html)
        self.assertIn(".slice(0, 6)", html)

    def test_search_results_cap_at_six(self):
        html = self.page()
        self.assertIn("searchResults.slice(0, 6).forEach", html)
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run: `venv\Scripts\python.exe manage.py test music.tests_request_compact -v2`

Expected: FAIL — page contains `.slice(0, 15)` and the search `forEach` has no slice.

- [ ] **Step 3: Implement the minimal code**

In `fetchHits`: change `.slice(0, 15)` to `.slice(0, 6)`. In `searchSong` success handler: change `searchResults.forEach` to `searchResults.slice(0, 6).forEach`. Nothing else.

- [ ] **Step 4: Run the test and confirm it passes**

Run the same command. Expected: PASS, 2 tests.

- [ ] **Step 5: Refactor only after green**

Nothing expected. Re-run the targeted test.

### Task 2: Move my-songs panel below search + name input

**Files:**

- Modify: `music/templates/music/request.html` (move `เพลงที่ฉันขอ` panel ~L176-179 to below search panel ~L163; add name input; `localStorage` key; send in `requestSongData`)
- Test: `music/tests_request_compact.py` (extend)

**Parallelization:**

- Can run with: none
- Must wait for: Task 1 (same file)
- Race risk: same file as Tasks 1 and 3 — sequential only

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code. This task must follow RED -> GREEN -> REFACTOR.

- [ ] **Step 1: Write the failing test**

Append to `music/tests_request_compact.py`:

```python
    def test_single_my_songs_panel_sits_below_search(self):
        html = self.page()
        self.assertEqual(html.count('id="my-songs-list"'), 1)
        self.assertLess(html.index('id="my-songs-list"'), html.index('id="hit-list"'))

    def test_name_input_is_persisted(self):
        html = self.page()
        self.assertIn('id="requester-name"', html)
        self.assertIn("jukebox_requester_name", html)
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run: `venv\Scripts\python.exe manage.py test music.tests_request_compact -v2`

Expected: FAIL — panel is after `#hit-list`, no `#requester-name` input.

- [ ] **Step 3: Implement the minimal code**

Move the whole `เพลงที่ฉันขอ` div (heading + `#my-songs-list`) to directly after the search panel div, delete the bottom copy. Add `<input id="requester-name">` above the search input; on load read `localStorage["jukebox_requester_name"]`, on change save it; in `requestSongData` send `requested_by: name || "ลูกค้าในร้าน"`. Match existing Tailwind classes; do not restyle anything else.

- [ ] **Step 4: Run the test and confirm it passes**

Run the same command. Expected: PASS, 4 tests.

- [ ] **Step 5: Refactor only after green**

Nothing expected. Re-run the targeted test.

### Task 3: Return and render requested_by

**Files:**

- Modify: `music/views.py:877` (`my_songs` `values()` add `'requested_by'`)
- Modify: `music/templates/music/request.html` (`fetchMySongs` row markup shows name)
- Test: `music/tests_request_compact.py` (extend)

**Parallelization:**

- Can run with: none
- Must wait for: Task 2 (same template file)
- Race risk: same template file — sequential only

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code. This task must follow RED -> GREEN -> REFACTOR.

- [ ] **Step 1: Write the failing test**

Append to `music/tests_request_compact.py`:

```python
    def test_my_songs_api_returns_requester_name(self):
        from music.models import SongQueue
        SongQueue.objects.create(
            title="t", video_id="abcdefghijk", requested_by="มิน",
            client_id=" naming-case-1",
        )
        payload = self.client.get("/api/my-songs/", {"client_id": " naming-case-1"}).json()
        self.assertEqual(payload["songs"][0]["requested_by"], "มิน")

    def test_add_stores_custom_requester_name(self):
        from music.models import SongQueue
        self.client.post(
            "/api/add/", data={"title": "t2", "video_id": "abcdefghij1",
                                "requested_by": "มิน", "client_id": "naming-case-2"},
            content_type="application/json",
        )
        self.assertEqual(
            SongQueue.objects.get(video_id="abcdefghij1").requested_by, "มิน")

    def test_my_songs_rows_render_the_name(self):
        html = self.page()
        self.assertIn("song.requested_by", html)
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run: `venv\Scripts\python.exe manage.py test music.tests_request_compact -v2`

Expected: FAIL — `requested_by` missing from API payload, row markup has no name.

- [ ] **Step 3: Implement the minimal code**

Add `'requested_by'` to the `values()` list in `my_songs`. In `fetchMySongs` row template, render `${escapeHtml(song.requested_by || '')}` as a small line under channel (never raw — XSS). No other view changes; `add_to_queue` already stores the field.

- [ ] **Step 4: Run the test and confirm it passes**

Run the same command. Expected: PASS, 7 tests.

- [ ] **Step 5: Refactor only after green**

Nothing expected. Re-run the targeted test plus the full `music` suite before finishing.

---

## Final Verification

```
venv\Scripts\python.exe manage.py test music.tests_request_compact -v0
venv\Scripts\python.exe manage.py test music -v0
git status --short
```

Then confirm on the live site after deploy: search returns max 6 rows, hits max 6 rows, my-songs panel sits below search, typed name persists across reload and appears on requested rows.

## Out of Scope for This Plan

- A "show more" toggle for the capped lists (user asked for exactly 6 rows).
- Queue panel changes on the player page.
- Any new database migration or endpoint.
- Committing or pushing (done separately after review).
