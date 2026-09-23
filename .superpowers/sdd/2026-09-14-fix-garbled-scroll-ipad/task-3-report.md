# T3 Report — player behavior (Q3A + Q4A)

## Changes (`music/templates/music/player.html` only)

1. **Cut global tap-resume** (old lines 670–675, now ~670–676):
   - Removed `document.addEventListener('touchstart', ... ensurePlaying() ...)` and
     `document.addEventListener('click', ... ensurePlaying() ...)` global listeners.
   - Replaced with a comment block explaining why they must NOT be re-added
     (scrolling/tapping anywhere must not resume a paused song).
   - Kept: `ensurePlaying()` function definition itself (line ~647, now unused by
     globals but retained for explicit paths per plan), the flag-only
     `document touchend` listener (`userInteracted = true; soundEnabled = true;`,
     no `ensurePlaying()` call), the wake-lock `click` re-acquire listener
     (line ~566, no `ensurePlaying()`), the dropdown-dismiss `click` listener
     (line ~1707, no `ensurePlaying()`), the `handleOverlayTap` sound-overlay
     handler, explicit play buttons, and queue-driven `playNext` paths.
2. **iPad boot hardening**: no edit needed — verified as-is:
   - YT `iframe_api` script (line ~457) left untouched, non-blocking position at
     end of body as before (plan: keep non-blocking as-is).
   - `playlist.js` loaded via `type="module"` (line ~39) — deferred by default,
     does not block first render.
   - SW registration guarded (`'serviceWorker' in navigator && !isLineWebView`,
     on `window load`, `.catch(()=>{})`) + LINE WebView unregister path
     (lines ~2140–2152) — does not block render.
   - `window.onerror` → `clog('js_error', ...)` surface already present
     (line ~480); compat guard for old browsers present (line ~25).
   - Tailwind CDN untouched. No refactor.

## Test output

- Grep: `ensurePlaying()` calls = 0 (only `function ensurePlaying()` definition
  remains); no `ensurePlaying` inside any `touchstart`/`click` listener. Pass.
- `.\venv\Scripts\python.exe manage.py test music.tests.PlayerPageTests music.tests.SingleSoundOverlayTests music.tests.UniversalPlayerRegressionTests`
  → **Ran 17 tests, OK** (19.3s). Pre-existing RuntimeWarning about DB access
  during app init (unrelated, pre-existing).

## Concerns

- **iOS first-tap audio unlock path preserved**: sound-overlay tap
  (`handleOverlayTap`, sets `userInteracted`/`soundEnabled`, unmutes + plays),
  explicit play buttons, queue-driven `playNext`, and the flag-only `touchend`
  gesture listener all intact. `ensurePlaying()` function kept for explicit use.
  Risk: since `ensurePlaying()` now has zero callers, a future reader may delete
  it or re-add global listeners — the comment block guards against this.
- **iPad root cause not 100% confirmable** without a device console (per plan
  trade-off); boot verified statically only — `window.onerror` beacon
  (`clog('js_error')`) is the diagnostic path if iPad still fails.
- Same-file race with T1 respected: T1's text edits were already in place;
  this edit touched only lines ~670–676, no overlap with T1 regions.
