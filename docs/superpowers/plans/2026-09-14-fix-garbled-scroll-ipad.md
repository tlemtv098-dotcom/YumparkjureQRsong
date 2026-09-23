# Fix garbled now-playing, scroll autoplay, iPad player load

## Problem
- Player now-playing shows literal `????????????????...` + `กำลังเล่น` (placeholder text visible during load).
- Thai UI strings end with `!` everywhere; user wants all removed.
- Scrolling on phone resumes paused song (global touchstart/click → ensurePlaying).
- iPad player page fails to load.

## Approach (recommended)
4 surgical edits, no refactor:
1. `now-loading` placeholder `????...` → Thai `กำลังโหลด...`, keep show/hide logic.
2. Strip trailing `!` from Thai UI strings in player.html + request.html; update exact-string test asserts.
3. Remove global touchstart/click → ensurePlaying tap-resume; keep explicit overlay/buttons/queue paths.
4. iPad boot hardening on player: YT iframe_api stays async non-blocking, verify module/SW guards, visible fallback.

Trade-off: minimal + test-safe. Risk: iPad root cause not 100% without device console.

## Assumptions
- `????` is placeholder text, not file-encoding corruption (file reads UTF-8 Thai fine elsewhere).
- Tests may assert exact toast strings with `!`; update tests alongside.
- `isIOS`/overlay/button play paths remain for first-unlock audio.

## Impact
- Files: player.html, request.html, tests.py only.
- No DB/migration/API contract change.

## Task overview (parallel-first)
| Task | Scope | Can run together | Must wait for | TDD slice |
|---|---|---|---|---|
| T1 player text | player.html Q1+Q2 | T2 | — | grep `????`=0, `กำลังโหลด` present, template tests pass |
| T2 request text + tests | request.html, tests.py | T1 | — | grep `!` in Thai strings gone, targeted tests pass |
| T3 player behavior | player.html Q3+Q4 | — | T1 (same-file race) | grep no global ensurePlaying on touch/click, targeted tests pass |
| T4 verify | full suite + browser | — | T1–T3 | 151 tests OK, live snapshot |

## T1 — player.html text (Q1C + Q2A-player)
- Files: `music/templates/music/player.html` only.
- Changes:
  - Line ~369: `????????????????...` → `กำลังโหลด...` inside `#now-loading`.
  - Strip trailing `!` from Thai UI strings in player.html (toasts/labels), keep code/HTML intact.
- Verify: `Select-String '????' player.html` = 0; `กำลังโหลด` present; `manage.py test music.tests.PlayerPageTests` pass.
- Race: owns player.html until done; T3 waits.

## T2 — request.html text + tests (Q2A-request)
- Files: `music/templates/music/request.html`, `music/tests.py`.
- Changes:
  - Strip trailing `!` from Thai strings (e.g. `กำลังเล่นเพลงของคุณ!` → no `!`).
  - Update tests.py asserts matching old exact strings (search `!` asserts first).
- Verify: grep Thai `!` gone in request.html; targeted RequestPageTests pass.
- Race: only lane touching tests.py.

## T3 — player behavior (Q3A + Q4A)
- Files: `music/templates/music/player.html` only. Must wait T1.
- Changes:
  - Remove `document touchstart/click → ensurePlaying()` global resume (keep touchend flag + overlay/button/queue explicit paths).
  - iPad boot: confirm YT `iframe_api` script async non-blocking, `playlist.js` module + SW guards intact, page renders without YT.
- Verify: grep no `ensurePlaying()` inside touchstart/click listeners; targeted player tests pass.
- Race: after T1.

## T4 — verify all
- Must wait T1–T3. No file writes.
- Run full `manage.py test` (expect 151 OK), browser snapshot request page + player where possible.
- Report residual gaps. No commit/push in tasks.
