# Term Project Submission Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Django jukebox visibly complete and demo-ready for the 15 Oct 2026 term-project submission by fixing the four defects that break graded criteria, then producing the three missing written deliverables.

**Estimated tasks:** 9 | **Estimated time:** ~200 min | **Touches:** Templates / Views / URLs / Forms / Management command / Docs

## Current Problem / Current Solution

All eight minimum criteria are already implemented and deployed at `https://yumpakjure.onrender.com/`. Verified live:

```
200  /accounts/register/     <- registration page exists and is deployed
200  /accounts/login/
302  /dashboard/             <- exists, redirects to login (correct)
302  /management/users/      302  /management/genres/      302  /management/tags/
200  /qr.png                 <- QR code already works
```

Git is fully pushed: `HEAD` == `origin/master` == `691eb5f`, ahead/behind `0 / 0`.

The work is invisible or broken for four concrete reasons:

1. **No navigation exists.** `music/templates/base.html` contains only `{% block content %}` — no navbar. `git grep` proves no template anywhere links to `accounts/register`, `accounts/login`, `dashboard`, or `management/*`. An evaluator opening the site sees only the jukebox and cannot discover any term-project feature. This directly fails the criterion "ส่วนติดต่อผู้ใช้มีรูปแบบสม่ำเสมอ อ่านง่าย และใช้งานได้จริง".
2. **Messages are never displayed.** `django.contrib.messages` is correctly configured in `settings.py`, and `music/views_auth.py` calls `messages.success()` / `messages.error()` throughout — but `git grep messages music/templates/` returns nothing. Registration success, permission denial, and every CRUD confirmation are silently dropped.
3. **Uploaded media 404s in production.** `yum_jukebox/urls.py` registers the media route only inside `if settings.DEBUG:`. Live `/media/` returns 404, so the "อัปโหลดรูปภาพหรือไฟล์" criterion demos a broken image. Render's filesystem is also ephemeral.
4. **All four dashboard charts are dead.** `music/views_auth.py:362` puts a raw `QuerySet` into the context, and `music/templates/dashboard.html:163` renders it with `{{ top_genres|safe }}`. That emits `<QuerySet [{...}]>` into JavaScript, which is a syntax error, which kills the whole `<script>` block — so the genre bar, daily line, top-songs bar, and status doughnut never render. The Dashboard/chart bonus scores zero.

Two further demo blockers:

- `music/views_auth.py:144` creates users with `User.objects.make_random_password()` and never displays the result, so an admin-created account cannot be logged into. There is only one account in the database (`admin`), so the "กำหนดสิทธิ์ผู้ใช้" demonstration cannot be performed.
- `music_genre` and `music_tag` contain 0 rows, so the charts would be empty even after the JSON fix.

Finally, three required written deliverables do not exist at all: PDF report, presentation file, and short usage manual. The repository also carries 20 throwaway one-off patch scripts plus 74 planning/session documents, all committed to `master`.

## Proposed Approach

Fix the four defects at their source rather than working around them, seed the minimum data needed to demonstrate roles and charts, delete the repository clutter, then generate the three documents from the finished code.

Decisions already approved by the user:

- Navigation goes in `base.html` (covers all nine templates that extend it) **and** auth entry points are added to `player.html` and `request.html` (the two pages customers actually see first).
- Admin user creation gains real password fields instead of a hidden random password, and demo `staff` / `customer` accounts are seeded.
- Media is served by a small guarded Django view registered unconditionally — no paid Render disk, no S3 account.
- The repository is cleaned to real code plus `README.md`, `Dockerfile`, `requirements.txt`.
- Documents are generated as real `.docx` / `.pptx` / `.pdf` via libraries installed into the existing `venv`.
- iOS Error 153 and the YouTube audio worker are explicitly **out of scope** for this round.

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| Evaluator opens the site | Sees only the jukebox; no way to reach any feature | Header shows เข้าสู่ระบบ / สมัครสมาชิก; after login, links to โปรไฟล์, แดชบอร์ด, จัดการผู้ใช้, แนวเพลง, แท็ก |
| Visitor registers | Redirects to player with no confirmation | Redirects to player with a visible "สมัครสมาชิกสำเร็จ" banner |
| Customer clicks a management URL | Silently bounced to player, no reason shown | Bounced to player with "คุณไม่มีสิทธิ์เข้าถึงหน้านี้" |
| Admin creates a user | Random password generated and discarded | Admin types the password; account is immediately usable |
| Demonstrating role assignment | Only `admin` exists | `admin` / `staff` / `customer` all exist with known passwords |
| Admin uploads an avatar | File saves but image is a broken 404 | Image renders immediately |
| Admin opens the dashboard | Blank page, charts absent, console syntax error | Four charts render with real data |
| Teacher opens the GitHub repo | 20 patch scripts and 74 agent documents at the top level | Only application code, `README.md`, `Dockerfile`, `requirements.txt` |

## Assumptions & Risks

- **Assumed:** Render is configured to auto-deploy `master` on push. Every route check above returned expected codes, which implies the deployment is current.
- **Assumed:** `music/tests.py` (1896 lines) is the only existing test module; new tests go in new `music/tests_*.py` files so parallel workers never collide on one file.
- **Risk:** Serving media through Django in production is weaker than object storage. Acceptable for a graded class project, but uploaded files still vanish on redeploy because Render's filesystem is ephemeral. This must be stated in the report and manual rather than hidden.
- **Risk:** Removing 74 committed documents and 20 scripts is a large deletion. Everything is recoverable from git history, but `git log --oneline -- <path>` must be checked per file before removal so nothing still referenced by the build is deleted.
- **Risk:** The student must be able to explain the code during defense. Generated documents must describe only behaviour that actually exists in this repository, and each section must be walked through with the student before submission.
- **Risk:** `pip install python-docx python-pptx reportlab` needs network access. If it fails, fall back to Markdown drafts the student converts by hand.
- **Risk:** PowerShell 5.1 reads and writes files as ANSI unless `-Encoding UTF8` is passed explicitly. This is the root cause of earlier accidental truncation of `yum_jukebox/settings.py` and `music/views.py`. See the editing constraint below.

### Repo-wide editing constraint

Windows PowerShell 5.1 is the shell. `Get-Content` / `Set-Content` / `Out-File` **without** `-Encoding UTF8` mangle Thai text. `?` characters seen in console output are a display artifact, not file corruption — a file is clean only when verified at byte level.

Before and after editing any file containing Thai text:

```powershell
# read
[System.IO.File]::ReadAllText("path", [System.Text.Encoding]::UTF8)
# write
[System.Text.File]::WriteAllText("path", $text, (New-Object System.Text.UTF8Encoding $false))
```

Never pipe file content through `Set-Content` to rewrite a whole file. Prefer targeted `python` scripts that open with `encoding="utf-8"` and assert the byte length did not collapse.

## Impact

- All eight minimum criteria become reachable and demonstrable; the navigation and messages fixes close the "ใช้งานได้จริง" gap.
- File upload becomes visibly correct in production, satisfying a required criterion.
- Dashboard charts render, converting a zero-scoring bonus into a demonstrable one.
- Role-based access control becomes demonstrable with three known accounts.
- The repository reads as a finished submission rather than an agent scratchpad.
- The three written deliverables exist in the exact formats the assignment requires.

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that race on the same files, migrations, generated artifacts, or shared state.

1. **Navbar and message banner in base.html** - Lane A | Can run together: 2, 3, 4, 7, 8 | Must wait for: none | TDD slice: assert `/accounts/register/` response contains a link to `user_list` and a messages container -> add markup -> re-run
2. **Auth entry points on player and request pages** - Lane A | Can run together: 1, 3, 4, 7, 8 | Must wait for: none | TDD slice: assert anonymous `/` contains an href to `register` -> add markup -> re-run
3. **Serve uploaded media in production** - Lane B | Can run together: 1, 2, 4, 7, 8 | Must wait for: none | TDD slice: request `/media/x.txt` with the file present, expect 200 but get 404 -> add guarded view -> re-run
4. **Fix dashboard chart data injection** - Lane C | Can run together: 1, 2, 3, 7, 8 | Must wait for: none | TDD slice: assert rendered chart JSON parses and `<QuerySet` is absent -> serialise in view + template -> re-run
5. **Admin-set password on user creation** - Lane C | Can run together: 1, 2, 3, 7, 8 | Must wait for: 4 | TDD slice: POST create form, assert new user can log in -> add password fields -> re-run
6. **Guard profile view against a missing Profile** - Lane C | Can run together: 7, 8 | Must wait for: 5 | TDD slice: user without Profile GETs `/accounts/profile/`, expect 200 but get 500 -> `get_or_create` -> re-run
7. **Seed demo accounts and content** - Lane D | Can run together: 1, 2, 3, 4, 8 | Must wait for: none | TDD slice: run command, assert 3 roles and non-empty genres exist -> implement command -> re-run
8. **Remove throwaway scripts and agent documents** - Lane E | Can run together: 1, 2, 3, 4, 7 | Must wait for: none | Docs/config only: `git status` shows only intended deletions, app boots, tests pass
9. **Generate report, slides, and manual** - Lane F | Can run together: none | Must wait for: 1, 2, 3, 4, 5, 6, 7, 8 | Docs only: generated files open and contain the real URLs and test counts

**Conflict map.** Lane C is strictly serial (Tasks 4 -> 5 -> 6) because all three edit `music/views_auth.py`. Every other lane touches a disjoint file set, so Lanes A, B, D, E run concurrently. No task creates a migration.

---

## Task 1: Navbar and message banner in base.html

**Files:**

- Modify: `music/templates/base.html:69-70` (insert nav + messages above `{% block content %}`)
- Test: `music/tests_nav.py` (create)

**Parallelization:**

- Can run with: Task 2, 3, 4, 7, 8
- Must wait for: none
- Race risk: none — `base.html` is touched by no other task

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code. This task must follow RED -> GREEN -> REFACTOR.

- [ ] **Step 1: Write the failing test**

Create `music/tests_nav.py`:

```python
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from music.models import Profile


class BaseNavTests(TestCase):
    def _make_user(self, username, role):
        user = User.objects.create_user(username=username, password="testpass123")
        Profile.objects.update_or_create(user=user, defaults={"role": role})
        return user

    def test_anonymous_register_page_has_link_to_login(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("login"))

    def test_customer_nav_shows_no_management_links(self):
        self._make_user("cust_nav", "customer")
        self.client.login(username="cust_nav", password="testpass123")
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("genre_list"))
        self.assertNotContains(response, reverse("user_list"))

    def test_staff_nav_shows_genre_and_tag_links(self):
        self._make_user("staff_nav", "staff")
        self.client.login(username="staff_nav", password="testpass123")
        response = self.client.get(reverse("profile"))
        self.assertContains(response, reverse("genre_list"))
        self.assertContains(response, reverse("tag_list"))
        self.assertNotContains(response, reverse("user_list"))

    def test_admin_nav_shows_user_management(self):
        self._make_user("admin_nav", "admin")
        self.client.login(username="admin_nav", password="testpass123")
        response = self.client.get(reverse("profile"))
        self.assertContains(response, reverse("user_list"))

    def test_messages_container_is_rendered(self):
        response = self.client.get(reverse("register"))
        self.assertContains(response, "messages")
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run: `venv\Scripts\python.exe manage.py test music.tests_nav -v2`

Expected: `test_customer_nav_shows_no_management_links` and the staff/admin nav tests FAIL because the navbar does not exist. `test_messages_container_is_rendered` FAILS because no messages markup exists. `test_anonymous_register_page_has_link_to_login` may pass — if it does, that is fine; the other four carry the RED state.

- [ ] **Step 3: Implement the minimal code**

In `music/templates/base.html`, immediately before `{% block content %}`, insert a messages loop and a responsive Tailwind nav. Rules:

- Always show: brand link to `{% url 'player' %}`, link to `{% url 'login' %}` when anonymous, `{% url 'profile' %}` when authenticated.
- Show `{% url 'dashboard' %}`, `{% url 'genre_list' %}`, `{% url 'tag_list' %}` only when the user's `Profile.role` is `admin` or `staff`.
- Show `{% url 'user_list' %}` only when `Profile.role == 'admin'`.
- Reuse the existing amber/slate Tailwind classes already present in the file. Do not add a second Tailwind CDN script.
- The messages loop must render `message.tags` as the CSS class and `message` as the body, inside a container whose markup contains the literal word `messages` as an id or class so the test can assert on it.
- Guard every role check so a missing `Profile` does not raise. Use `{% if user.profile.role == 'admin' %}` style checks, which Django resolves safely, and prefer a single `{% with role=user.profile.role %}` wrapper.

Edit the file with a UTF-8-safe script, not `Set-Content`.

- [ ] **Step 4: Run the test and confirm it passes**

Run: `venv\Scripts\python.exe manage.py test music.tests_nav -v2`

Expected: PASS, 5 tests.

- [ ] **Step 5: Refactor only after green**

Extract repeated link markup into an `{% include %}` only if the file becomes hard to read. Keep it inline otherwise — a single nav does not justify a new template. Re-run the targeted test.

---

## Task 2: Auth entry points on player and request pages

**Files:**

- Modify: `music/templates/music/player.html:281` (extend the existing `{% if user.is_authenticated %}` line)
- Modify: `music/templates/music/request.html:62-69` (add an auth control to the header row)
- Test: `music/tests_nav_customer.py` (create)

**Parallelization:**

- Can run with: Task 1, 3, 4, 7, 8
- Must wait for: none
- Race risk: none — `player.html` and `request.html` are touched by no other task in this plan

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code.

- [ ] **Step 1: Write the failing test**

`player.html` already renders a `เข้า` link at line 281 for anonymous visitors, so the RED state must target what is genuinely missing: a link to registration, and management links once logged in.

Create `music/tests_nav_customer.py`:

```python
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from music.models import Profile


class CustomerPageAuthEntryTests(TestCase):
    def test_player_anonymous_has_register_link(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("register"))

    def test_player_authenticated_has_management_links(self):
        user = User.objects.create_user(username="staff_p", password="testpass123")
        Profile.objects.update_or_create(user=user, defaults={"role": "staff"})
        self.client.login(username="staff_p", password="testpass123")
        response = self.client.get("/")
        self.assertContains(response, reverse("genre_list"))

    def test_request_page_anonymous_has_login_and_register(self):
        response = self.client.get(reverse("request_view"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("login"))
        self.assertContains(response, reverse("register"))
```

If `/` requires login, obtain an authenticated client for the first test instead of asserting 200 anonymously — check the actual status before finalising the assertion.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run: `venv\Scripts\python.exe manage.py test music.tests_nav_customer -v2`

Expected: FAIL because `player.html` has no `{% url 'register' %}` and `request.html` has no auth controls at all.

- [ ] **Step 3: Implement the minimal code**

`player.html` line 281 — inside the existing `{% else %}` branch, add a `สมัครสมาชิก` link to `{% url 'register' %}` beside the existing `เข้า` link. Inside the authenticated branch, append compact links to `{% url 'dashboard' %}` and, for `admin`/`staff`, `{% url 'genre_list' %}`. Keep the markup on the existing single line and match the existing `text-xs` sizing so the header does not reflow.

`request.html` — add a control to the header row at lines 62-69, after the theme toggle. For anonymous visitors render `เข้าสู่ระบบ` (`{% url 'login' %}`) and `สมัครสมาชิก` (`{% url 'register' %}`). For authenticated users render the username and a POST logout form matching the pattern already used in `player.html:281`. Do not disturb the existing logo, title, or theme-toggle markup, and do not change any JavaScript.

- [ ] **Step 4: Run the test and confirm it passes**

Run: `venv\Scripts\python.exe manage.py test music.tests_nav_customer -v2`

Expected: PASS, 3 tests.

- [ ] **Step 5: Refactor only after green**

If both headers now duplicate the same auth markup, that is acceptable duplication — do not extract a shared partial, because `player.html` and `request.html` have different layouts and no other page needs it. Re-run the targeted test plus `music.tests_nav`.

---

## Task 3: Serve uploaded media in production

**Files:**

- Modify: `yum_jukebox/urls.py:3-15`
- Test: `music/tests_media.py` (create)

**Parallelization:**

- Can run with: Task 1, 2, 4, 7, 8
- Must wait for: none
- Race risk: none — `yum_jukebox/urls.py` is touched by no other task

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code.

- [ ] **Step 1: Write the failing test**

Create `music/tests_media.py`:

```python
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(MEDIA_ROOT=Path(tempfile.gettempdir()) / "mysong_media_test")
class MediaServingTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_root = Path(tempfile.gettempdir()) / "mysong_media_test"
        cls.media_root.mkdir(parents=True, exist_ok=True)
        (cls.media_root / "probe.txt").write_text("ok", encoding="utf-8")

    def test_media_file_is_served(self):
        response = self.client.get("/media/probe.txt")
        self.assertEqual(response.status_code, 200)

    def test_missing_media_file_returns_404(self):
        response = self.client.get("/media/does-not-exist.txt")
        self.assertEqual(response.status_code, 404)

    def test_path_traversal_is_blocked(self):
        response = self.client.get("/media/../../yum_jukebox/settings.py", status=404)
        self.assertIn(response.status_code, (400, 404))
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run: `venv\Scripts\python.exe manage.py test music.tests_media -v2`

Expected: `test_media_file_is_served` FAILS with 404, because `yum_jukebox/urls.py` registers the media route only under `if settings.DEBUG:` and the test environment does not serve it through `static()`.

- [ ] **Step 3: Implement the minimal code**

In `yum_jukebox/urls.py`, replace the `if settings.DEBUG: urlpatterns += static(...)` block with an always-registered guarded route:

```python
import os

from django.http import Http404
from django.views.static import serve


def _media_view(request, path):
    root = os.path.abspath(settings.MEDIA_ROOT)
    full = os.path.abspath(os.path.join(root, path))
    if os.path.commonpath([root, full]) != root:
        raise Http404("media path outside MEDIA_ROOT")
    return serve(request, path, document_root=root)
```

Register it with `re_path(r"^media/(?P<path>.*)$", _media_view)` and keep `path("", include("music.urls"))` last so it does not shadow application URLs. Remove the now-unused `static` import and the `settings.DEBUG` media block; keep `staticfiles_urlpatterns` behaviour untouched. `os.path.commonpath` raises `ValueError` on mismatched drives — catch it and return 404 rather than a 500.

- [ ] **Step 4: Run the test and confirm it passes**

Run: `venv\Scripts\python.exe manage.py test music.tests_media -v2`

Expected: PASS, 3 tests, including the traversal guard.

- [ ] **Step 5: Refactor only after green**

Confirm the traversal guard cannot be bypassed with an absolute path or a `..` chain before considering the task done. Re-run `music.tests_media` and then `music.healthz`-covering tests to prove the URL reorder broke nothing.

---

## Task 4: Fix dashboard chart data injection

**Files:**

- Modify: `music/views_auth.py:328-366` (`dashboard_view` context) and `music/views_auth.py:370-403` (`dashboard_stats_api`)
- Modify: `music/templates/dashboard.html:163`, `:204`, `:239`, `:268`
- Test: `music/tests_dashboard.py` (create)

**Parallelization:**

- Can run with: Task 1, 2, 3, 7, 8
- Must wait for: none
- Race risk: `music/views_auth.py` is also edited by Tasks 5 and 6 — those must not start until this task finishes

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code.

- [ ] **Step 1: Write the failing test**

Create `music/tests_dashboard.py`:

```python
import json
import re

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from music.models import Genre, Profile, SongQueue


class DashboardChartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dash_admin", password="testpass123")
        Profile.objects.update_or_create(user=self.user, defaults={"role": "admin"})
        self.client.login(username="dash_admin", password="testpass123")
        genre = Genre.objects.create(name="Pop")
        SongQueue.objects.create(
            title="Test Song", video_id="abcdefghijk", genre=genre, is_played=True
        )

    def _extract(self, html, const_name):
        match = re.search(rf"const {const_name} = (.*?);", html, re.S)
        self.assertIsNotNone(match, f"{const_name} not found in page")
        return match.group(1)

    def test_dashboard_never_renders_a_raw_queryset(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<QuerySet")

    def test_genre_chart_data_is_valid_json(self):
        html = self.client.get(reverse("dashboard")).content.decode()
        payload = self._extract(html, "genreData")
        self.assertIsInstance(json.loads(payload), list)

    def test_all_chart_payloads_are_valid_json(self):
        html = self.client.get(reverse("dashboard")).content.decode()
        for name in ("genreData", "dailyStats", "topSongsData", "statusData"):
            with self.subTest(chart=name):
                self.assertIsInstance(json.loads(self._extract(html, name)), list)

    def test_stats_api_returns_lists(self):
        response = self.client.get(reverse("dashboard_stats_api"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        for key in ("daily_stats", "top_songs", "status_stats", "genres"):
            with self.subTest(key=key):
                self.assertIsInstance(payload[key], list)

    def test_stats_api_rejects_non_numeric_period(self):
        response = self.client.get(reverse("dashboard_stats_api"), {"period": "abc"})
        self.assertEqual(response.status_code, 200)
```

If the chart constants in `dashboard.html` are not named exactly `genreData` / `dailyStats` / `topSongsData` / `statusData`, read the file and correct the test names before running — the test must match reality, not the other way round.

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run: `venv\Scripts\python.exe manage.py test music.tests_dashboard -v2`

Expected: `test_dashboard_never_renders_a_raw_queryset` FAILS on `<QuerySet`; `test_genre_chart_data_is_valid_json` FAILS because `json.loads` receives `<QuerySet ...>`; `test_stats_api_returns_lists` FAILS because `genres` is absent from the API payload; `test_stats_api_rejects_non_numeric_period` FAILS with a 500 from `int("abc")`.

- [ ] **Step 3: Implement the minimal code**

In `dashboard_view`, serialise every chart input in the view with `json.dumps(..., ensure_ascii=False)` and pass the resulting strings under new `*_json` context keys. Convert `top_genres` from a QuerySet to a list of `{"name": ..., "song_count": ...}` dicts before serialising. Keep the existing plain context keys only if a template still reads them.

In `dashboard_stats_api`, add the missing `genres` list so the endpoint matches the page, and wrap the `int(request.GET.get("period", 7))` parse so a non-numeric value falls back to 7 instead of raising.

In `dashboard.html`, replace each `{{ x|safe }}` injection with the matching `*_json` string. Because `json.dumps` already produces valid JavaScript, `|safe` remains correct and `json_script` is unnecessary. Do not restructure the Chart.js code.

- [ ] **Step 4: Run the test and confirm it passes**

Run: `venv\Scripts\python.exe manage.py test music.tests_dashboard -v2`

Expected: PASS, 5 tests.

- [ ] **Step 5: Refactor only after green**

If `dashboard_view` and `dashboard_stats_api` now duplicate the same four aggregation blocks, extract one private helper that returns the chart payload dict and have both call it. This is justified duplication removal because both are in the same file. Re-run `music.tests_dashboard`.

---

## Task 5: Admin-set password on user creation

**Files:**

- Modify: `music/forms.py:125-158` (`UserForm`)
- Modify: `music/views_auth.py:136-158` (`user_create_view`)
- Modify: `music/templates/admin/user_form.html:60-74`
- Test: `music/tests_user_create.py` (create)

**Parallelization:**

- Can run with: Task 1, 2, 3, 7, 8
- Must wait for: Task 4 (shares `music/views_auth.py`)
- Race risk: `music/views_auth.py` — strictly sequential after Task 4

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code.

- [ ] **Step 1: Write the failing test**

Create `music/tests_user_create.py`:

```python
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from music.models import Profile


class UserCreatePasswordTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="root_admin", password="testpass123")
        Profile.objects.update_or_create(user=self.admin, defaults={"role": "admin"})
        self.client.login(username="root_admin", password="testpass123")

    def _payload(self, username, password):
        return {
            "username": username,
            "first_name": "Test",
            "last_name": "User",
            "email": f"{username}@example.com",
            "is_active": "on",
            "role": "staff",
            "password1": password,
            "password2": password,
        }

    def test_created_user_can_log_in_with_chosen_password(self):
        response = self.client.post(reverse("user_create"), self._payload("newstaff", "ChosenPass123"))
        self.assertEqual(response.status_code, 302)
        created = User.objects.get(username="newstaff")
        self.assertTrue(created.check_password("ChosenPass123"))
        self.assertEqual(created.profile.role, "staff")

    def test_mismatched_password_is_rejected(self):
        payload = self._payload("badstaff", "ChosenPass123")
        payload["password2"] = "DifferentPass123"
        response = self.client.post(reverse("user_create"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="badstaff").exists())

    def test_short_password_is_rejected(self):
        response = self.client.post(reverse("user_create"), self._payload("weakstaff", "123"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="weakstaff").exists())

    def test_create_form_renders_password_fields(self):
        response = self.client.get(reverse("user_create"))
        self.assertContains(response, "password1")
        self.assertContains(response, "password2")
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run: `venv\Scripts\python.exe manage.py test music.tests_user_create -v2`

Expected: FAIL. `newstaff` is created with `make_random_password()` so `check_password("ChosenPass123")` is false, the mismatch and short-password cases are silently accepted because the fields are ignored, and the form does not render password inputs.

- [ ] **Step 3: Implement the minimal code**

Add a `UserCreateForm` in `music/forms.py` that extends `UserCreationForm` for the same user fields plus `is_active`, and keep the existing `UserForm` untouched for the edit view. Do not add password fields to `UserForm`, because the edit form must not silently reset an existing user's password.

In `user_create_view`, use `UserCreateForm` on POST and replace the `make_random_password()` call with `user.set_password(user_form.cleaned_data["password1"])`. Keep the `ProfileRoleForm` handling and the redirect unchanged.

In `user_form.html`, render the two password fields only when `user_obj` is absent, reusing the existing grid and error-markup style. Delete the stale `{% if user_obj %}` hint at lines 70-74 that tells the user to use Django Admin for password resets, and replace it with a pointer to the change-password page.

- [ ] **Step 4: Run the test and confirm it passes**

Run: `venv\Scripts\python.exe manage.py test music.tests_user_create -v2`

Expected: PASS, 4 tests.

- [ ] **Step 5: Refactor only after green**

Confirm the edit view still works unchanged by re-running the whole `music` suite before finishing. Re-run `music.tests_user_create`.

---

## Task 6: Guard profile view against a missing Profile

**Files:**

- Modify: `music/views_auth.py:65-77` (`profile_view`)
- Test: `music/tests_profile_guard.py` (create)

**Parallelization:**

- Can run with: Task 7, 8
- Must wait for: Task 5 (shares `music/views_auth.py`)
- Race risk: `music/views_auth.py` — sequential within Lane C

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code.

- [ ] **Step 1: Write the failing test**

Create `music/tests_profile_guard.py`:

```python
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from music.models import Profile


class ProfileGuardTests(TestCase):
    def test_user_without_profile_row_gets_profile_page(self):
        legacy = User.objects.create_user(username="legacy", password="testpass123")
        Profile.objects.filter(user=legacy).delete()
        self.client.login(username="legacy", password="testpass123")
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Profile.objects.filter(user=legacy).exists())

    def test_existing_profile_is_not_duplicated(self):
        user = User.objects.create_user(username="hasprofile", password="testpass123")
        Profile.objects.update_or_create(user=user, defaults={"role": "staff", "phone": "0812345678"})
        self.client.login(username="hasprofile", password="testpass123")
        self.client.get(reverse("profile"))
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
        self.assertEqual(Profile.objects.get(user=user).phone, "0812345678")
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run: `venv\Scripts\python.exe manage.py test music.tests_profile_guard -v2`

Expected: `test_user_without_profile_row_gets_profile_page` FAILS with `RelatedObjectDoesNotExist` (a 500) because line 68 does `request.user.profile` unguarded. This is a real production risk: users created before migration `0008` have no `Profile` row.

- [ ] **Step 3: Implement the minimal code**

Replace line 68 with `profile, _ = Profile.objects.get_or_create(user=request.user)`. Leave the rest of the view unchanged. Do not add a signal, a data migration, or a try/except — `get_or_create` is the whole fix.

- [ ] **Step 4: Run the test and confirm it passes**

Run: `venv\Scripts\python.exe manage.py test music.tests_profile_guard -v2`

Expected: PASS, 2 tests.

- [ ] **Step 5: Refactor only after green**

Nothing to refactor. Re-run the targeted test and `music.tests_user_create` to confirm Lane C is still green.

---

## Task 7: Seed demo accounts and content

**Files:**

- Create: `music/management/__init__.py`
- Create: `music/management/commands/__init__.py`
- Create: `music/management/commands/seed_demo_data.py`
- Test: `music/tests_seed.py` (create)

**Parallelization:**

- Can run with: Task 1, 2, 3, 4, 8
- Must wait for: none
- Race risk: none — creates new files only, touches no existing application file

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development` before editing production code.

- [ ] **Step 1: Write the failing test**

Create `music/tests_seed.py`:

```python
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from music.models import Genre, Playlist, Profile, SongQueue, Tag


class SeedDemoDataTests(TestCase):
    def setUp(self):
        call_command("seed_demo_data", verbosity=0)

    def test_creates_three_roles(self):
        for username, role in (("admin", "admin"), ("staff", "staff"), ("customer", "customer")):
            with self.subTest(username=username):
                self.assertTrue(User.objects.filter(username=username).exists())
                self.assertEqual(Profile.objects.get(user__username=username).role, role)

    def test_demo_accounts_can_authenticate(self):
        for username in ("admin", "staff", "customer"):
            with self.subTest(username=username):
                self.assertTrue(User.objects.get(username=username).check_password(self.PASSWORD))

    def test_creates_genres_and_tags(self):
        self.assertGreaterEqual(Genre.objects.count(), 5)
        self.assertGreaterEqual(Tag.objects.count(), 5)

    def test_creates_songs_for_charts(self):
        self.assertGreaterEqual(SongQueue.objects.count(), 10)
        self.assertGreaterEqual(SongQueue.objects.filter(is_played=True).count(), 1)

    def test_creates_a_playlist(self):
        self.assertGreaterEqual(Playlist.objects.count(), 1)

    def test_command_is_idempotent(self):
        call_command("seed_demo_data", verbosity=0)
        self.assertEqual(User.objects.filter(username="staff").count(), 1)
        self.assertEqual(Genre.objects.count(), Genre.objects.distinct().count())

    PASSWORD = "12345678"
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run: `venv\Scripts\python.exe manage.py test music.tests_seed -v2`

Expected: FAIL with `Unknown command: seed_demo_data`.

- [ ] **Step 3: Implement the minimal code**

Write `seed_demo_data` as an idempotent command using `get_or_create` throughout. It must create:

- Accounts `admin`, `staff`, `customer` with password `12345678` and matching `Profile` roles. Use `set_password` rather than `create_user(password=...)` only where an existing account needs its password reset to the same documented value.
- At least 5 `Genre` rows and 5 `Tag` rows with Thai names.
- At least 10 `SongQueue` rows using real 11-character YouTube video IDs, with a mix of `is_played` true and false, at least one carrying a `thumbnail` URL, and genres/tags attached so the genre chart has data.
- At least 1 `Playlist` owned by `customer` with songs attached through `PlaylistSong`.

Accept an optional `--reset-passwords` flag that is off by default. Print a summary table of created credentials at the end. Do not reference any other application module beyond `music.models`.

- [ ] **Step 4: Run the test and confirm it passes**

Run: `venv\Scripts\python.exe manage.py test music.tests_seed -v2`

Expected: PASS, 6 tests, including the idempotency check.

- [ ] **Step 5: Refactor only after green**

Run the command against the local database and confirm the dashboard now has data:

```
venv\Scripts\python.exe manage.py seed_demo_data
venv\Scripts\python.exe manage.py test music -v0
```

---

## Task 8: Remove throwaway scripts and agent documents

**Files:**

- Delete: 20 root-level patch scripts (`add_dashboard_api.py`, `add_dashboard_url.py`, `add_form_validation.py`, `add_playlist_validation.py`, `add_paginator_import.py`, `add_playlist_pagination.py`, `add_playlistsong.py`, `add_profile_avatar.py`, `add_queue_pagination.py`, `add_sq_validation.py`, `add_user_validation.py`, `check_pagination.py`, `find_sq_end.py`, `find_static.py`, `find_thumb.py`, `fix_add_song.py`, `fix_reorder.py`, `fix_songqueue_ref.py`, `update_artwork_upload.py`, `update_views_artwork.py`, plus `update_dashboard_view.py`)
- Delete: `.superpowers/` (4 files), `docs/superpowers/` (74 files)
- Keep: `README.md`, `Dockerfile`, `requirements.txt`, `docs/plans/`

**Parallelization:**

- Can run with: Task 1, 2, 3, 4, 7
- Must wait for: none
- Race risk: none — deletes only files no other task touches. Must not delete `docs/plans/`, which holds this plan.

- [ ] **Step 0: Load the TDD discipline**

This task is **docs/config-only** — it removes files and changes no runtime behaviour, so a failing behaviour test is not appropriate. Verification is the commands below.

- [ ] **Step 1: Confirm nothing depends on the files being removed**

```
git grep -n "add_dashboard_api\|add_playlistsong\|fix_reorder\|update_views_artwork\|check_pagination" -- .
```

Expected: no matches outside the scripts themselves. Then confirm each script is unreferenced:

```
foreach ($f in @("add_dashboard_api.py","add_dashboard_url.py","update_dashboard_view.py","add_playlistsong.py","fix_add_song.py","fix_reorder.py","fix_songqueue_ref.py","add_form_validation.py","add_playlist_validation.py","add_paginator_import.py","add_playlist_pagination.py","add_queue_pagination.py","add_profile_avatar.py","add_sq_validation.py","add_user_validation.py","check_pagination.py","find_sq_end.py","find_static.py","find_thumb.py","update_artwork_upload.py","update_views_artwork.py")) {
  $hits = git grep -l --fixed-strings $f -- . ':!*.py' 2>$null
  "$f -> " + ($(if ($hits) { $hits -join ',' } else { 'no external reference' }))
}
```

- [ ] **Step 2: Remove the files from git and disk**

```
git rm --cached add_dashboard_api.py add_dashboard_url.py update_dashboard_view.py add_playlistsong.py fix_add_song.py fix_reorder.py fix_songqueue_ref.py add_form_validation.py add_playlist_validation.py add_paginator_import.py add_playlist_pagination.py add_queue_pagination.py add_profile_avatar.py add_sq_validation.py add_user_validation.py check_pagination.py find_sq_end.py find_static.py find_thumb.py update_artwork_upload.py update_views_artwork.py
git rm -r --cached .superpowers docs/superpowers
Remove-Item -Recurse -Force .superpowers, docs/superpowers -ErrorAction SilentlyContinue
```

Confirm `docs/plans/` survives. If these paths must stay on disk for reference, use `git rm --cached` only and add them to `.gitignore` instead — but the user approved full removal, so delete.

- [ ] **Step 3: Verify the app still boots and the suite is green**

```
venv\Scripts\python.exe manage.py check
venv\Scripts\python.exe manage.py test music -v0
```

Expected: no `check` errors and the same pass count as before this task, with no new failures.

- [ ] **Step 4: Verify the working tree contains only intended changes**

```
git status --short
```

Expected: only `D` entries for the removed paths. If anything else appears, restore it before continuing.

---

## Task 9: Generate report, slides, and manual

**Files:**

- Create: `deliverables/รายงานโครงงาน.pdf`
- Create: `deliverables/รายงานโครงงาน.docx`
- Create: `deliverables/ไฟล์นำเสนอ.pptx`
- Create: `deliverables/คู่มือการใช้งาน.docx`
- Create: `deliverables/build_documents.py` (the generator, so the documents are reproducible)

**Parallelization:**

- Can run with: none
- Must wait for: Tasks 1, 2, 3, 4, 5, 6, 7, 8 — the documents must describe the finished system, including the real post-fix test count
- Race risk: generated binary artifacts. Run alone.

- [ ] **Step 0: Load the TDD discipline**

This task is **docs-only** — it produces documents, not runtime behaviour, so a failing behaviour test is not appropriate. Verification is opening the generated files and checking their content.

- [ ] **Step 1: Install the libraries into the existing venv**

```
venv\Scripts\python.exe -m pip install python-docx python-pptx reportlab
venv\Scripts\python.exe -c "import docx, pptx, reportlab; print('doc libs ok')"
```

Expected: `doc libs ok`. If the install fails, stop and report the blocker — the fallback is Markdown drafts the student converts by hand.

- [ ] **Step 2: Collect the real facts to embed**

Do not invent numbers. Capture:

```
venv\Scripts\python.exe manage.py test music -v0 2>&1 | Select-String "Ran |OK|FAILED"
git log --oneline | Measure-Object -Line
venv\Scripts\python.exe -c "from music.models import *; print([m.__name__ for m in [Profile,Genre,Tag,Playlist,SongQueue,PlaylistSong,BlockedVideo,GoodVideo,ClientLog]])"
```

Also record: live URL `https://yumpakjure.onrender.com/`, repository `https://github.com/tlemtv098-dotcom/YumparkjureQRsong` (226 commits at plan time), QR endpoint `/qr.png`, and the demo credentials `admin` / `staff` / `customer` all with password `12345678`.

- [ ] **Step 3: Write the generator script**

Create `deliverables/build_documents.py`. It must produce:

**Report (PDF + DOCX)** with these chapters, matching the assignment wording exactly:

1. บทนำ — problem statement, scope, why a jukebox
2. การวิเคราะห์และออกแบบระบบ — roles, use cases, ER diagram as a generated image or an ASCII-art schema block, data flow
3. การพัฒนาระบบ — models and their fields, auth and role control, CRUD, search, upload, pagination, model relationships, form validation, REST API, dashboard
4. ผลการพัฒนาและภาพหน้าจอ — embed real screenshots captured from the live site
5. การทดสอบ — the automated test suite result, the manual test checklist
6. สรุปผล — what was achieved, known limitations
7. ภาคผนวก — live URL, QR code image, GitHub URL, test accounts, short usage manual

Every technical claim must be traceable to a file in this repository. Name real modules, real model fields, and real view functions.

**Presentation (PPTX)** with 12-15 slides: title, problem, roles, architecture, ER diagram, key models, auth and permissions, CRUD demo flow, search, upload, pagination, dashboard, testing, limitations, appendix with URL and accounts.

**Manual (DOCX)**: how to register, log in, request a song, use the player, and how an admin manages users, genres, and tags. Include the credential table and a troubleshooting section covering the ephemeral-media caveat and the YouTube API key requirement.

- [ ] **Step 4: Capture screenshots from the live site**

Use the browser tool to capture, at minimum, the register page, the logged-in dashboard with charts rendering, the user management list, and the genre CRUD page. Save PNGs into `deliverables/screenshots/` and embed them in the report. This step also serves as the manual verification that Tasks 1-4 actually work in production.

- [ ] **Step 5: Generate and verify the files**

```
venv\Scripts\python.exe deliverables\build_documents.py
```

Then verify each file: open the PDF and confirm page count and that Thai text renders (not boxes), open the PPTX and confirm slide count, open both DOCX files and confirm the credential table is present. Confirm no placeholder text such as `TODO` or `Lorem` remains.

- [ ] **Step 6: Walk the student through the content**

Report the chapter-by-chapter outline and answer what the teacher is most likely to ask, so the student can defend the work as the assignment requires. Flag explicitly that the student must be able to explain every section.

---

## Final Verification

Run after all tasks complete:

```
venv\Scripts\python.exe manage.py check
venv\Scripts\python.exe manage.py test music -v0
git status --short
```

Then confirm against the live site with an authenticated session: register a new account, log in, verify the navbar links appear, open the dashboard and confirm all four charts render, upload an avatar and confirm the image displays, and open `/management/users/create/` and confirm the password fields are present and the new account can log in.

## Out of Scope for This Plan

- iOS/Safari Error 153 and the YouTube audio worker (explicitly deferred by the user)
- Render Persistent Disk or S3/Cloudinary media storage
- The queue-blank-on-first-load and custom-named auto-queue feature
- Square logo and `autoPlayedIds` persistence, both dropped by an earlier revert
- Any new database migration
