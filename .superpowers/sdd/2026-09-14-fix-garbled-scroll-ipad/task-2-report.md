# T2 Report — request.html Thai `!` strip + tests

## Goal
Strip trailing `!` from user-visible Thai strings in `request.html`; update only matching exact-string test asserts.

## Changes (`music/templates/music/request.html`, 4 lines)
- Line 363: `showToast("ส่งคำขอเพลงแล้ว!", "success")` → `showToast("ส่งคำขอเพลงแล้ว", "success")`
- Line 402: `text.innerHTML = "เพลงของคุณเล่นแล้ว ขอบคุณที่ใช้บริการ!"` → `...ที่ใช้บริการ"` (no `!`)
- Line 405: `text.innerHTML = "กำลังเล่นเพลงของคุณ!"` → `"กำลังเล่นเพลงของคุณ"`
- Line 407: `text.innerHTML = "เพิ่มเพลงเข้าคิวแล้ว!<br>..."` → `"เพิ่มเพลงเข้าคิวแล้ว<br>..."`

## tests.py
- No edits. Verified zero lines in `music/tests.py` contain Thai + `!` co-occurrence, so no assert matched the 4 old exact strings. All other `!` occurrences are passwords (`Testpass123!`) or code operators (`!userInteracted`, `!currentSong`, etc.) — left untouched per scope.

## Verification
- Grep (Python, UTF-8, lines containing both `!` and Thai U+0E00–U+0E7F): only lines 18 and 472 remain.
  - Line 18: `!`s are code operators (`!window.fetch||!window.URLSearchParams||!window.Promise`); Thai compat-guard text ends with `ใช้งาน`, no `!` — correctly untouched.
  - Line 472: `!` is code operator (`!confirm(...)`); Thai string ends with `?` (`ลบเพลงนี้ออกจากคิว?`) — correctly untouched (only `!` in scope).
  - No Thai visible string ends with `!`. PASS.
- `.\venv\Scripts\python.exe manage.py test music.tests.RequestPageTests` from `D:\mysong`: **Ran 15 tests, OK** (0.233s, no issues silenced).

## Concerns
- None blocking. Note: T1 owns `player.html` Thai-`!` strings in parallel — no overlap with this lane (different files, and `tests.py` untouched here so no merge race from this side).
