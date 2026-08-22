# Fix Static Files Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix static files (images) not loading on Railway production deployment by configuring Django static files properly, adding missing image placeholders, and fixing QR code URL path.

**Estimated tasks:** 5 | **Estimated time:** ~30 min | **Touches:** Django settings, templates, static files

## Current Problem / Current Solution

**Current problems:**
1. `settings.py` missing `STATIC_ROOT` and `STATICFILES_DIRS` — `collectstatic` won't work on Railway production
2. Template `player.html` references `{% static 'music/img/1.png' %}` and `{% static 'music/img/2.jpg' %}` but these files don't exist in `music/static/music/img/`
3. Template `player.html` uses hardcoded `/qr.png` for QR code — breaks if Railway adds subpath prefix
4. Template `request.html` uses hardcoded `/static/music/img/logo.jpg` instead of `{% static %}` template tag

**Current behavior:** Images show locally (DEBUG=True serves static automatically) but 404 on Railway production.

## Proposed Approach

1. Add `STATIC_ROOT` and `STATICFILES_DIRS` to `settings.py` for production `collectstatic`
2. Create placeholder images for missing `1.png` and `2.jpg` (copy `logo.jpg` as fallback)
3. Fix `player.html` QR code to use `{% url 'qr_code' %}` instead of hardcoded `/qr.png`
4. Fix `request.html` logo to use `{% static 'music/img/logo.jpg' %}` instead of hardcoded path
5. Verify `collectstatic` works and Railway deployment serves static files

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| Deploy to Railway | `collectstatic` fails / no static files served | `collectstatic` runs, static files served at `/static/` |
| Player page idle splash | Missing 1.png, 2.jpg (broken images) | Placeholder images show (logo.jpg copies) |
| QR code on player/request page | Hardcoded `/qr.png` — breaks with subpath | `{% url 'qr_code' %}` — works on any path |
| Request page logo | Hardcoded `/static/music/img/logo.jpg` | `{% static 'music/img/logo.jpg' %}` — works with CDN/storage |

## Assumptions & Risks

- **Assumed:** Railway uses nixpacks builder and runs `collectstatic` automatically or via build command
- **Assumed:** `DEBUG=False` in production (Railway sets this via env var)
- **Risk:** If Railway doesn't run `collectstatic`, need to add build command in `railway.toml`
- **Risk:** Placeholder images are just copies of logo.jpg — user may want actual different images later

## Impact

- Static files (images, CSS, JS) will load correctly on Railway production
- No more broken image icons on player page idle state
- QR code works regardless of deployment URL structure
- Consistent static file handling across all templates

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Configure static files in settings.py]** - Lane A | Can run together: [Task 2, Task 3] | Must wait for: [none] | TDD slice: verify `collectstatic` runs without error -> add STATIC_ROOT/STATICFILES_DIRS -> run `collectstatic` and verify output
2. **[Create placeholder images 1.png and 2.jpg]** - Lane B | Can run together: [Task 1, Task 3] | Must wait for: [none] | TDD slice: verify files missing -> copy logo.jpg as 1.png and 2.jpg -> verify files exist in static/music/img/
3. **[Fix QR code URL in player.html]** - Lane C | Can run together: [Task 1, Task 2] | Must wait for: [none] | TDD slice: verify hardcoded /qr.png -> replace with {% url 'qr_code' %} -> verify template renders correct URL
4. **[Fix logo static tag in request.html]** - Lane D | Can run together: [Task 1, Task 2, Task 3] | Must wait for: [none] | TDD slice: verify hardcoded /static/... -> replace with {% static %} -> verify template renders correct URL
5. **[Verify collectstatic and Railway config]** - Sequential | Can run together: [none] | Must wait for: [Task 1, Task 2] | TDD slice: run collectstatic locally -> verify staticfiles directory populated -> check railway.toml for build command

---