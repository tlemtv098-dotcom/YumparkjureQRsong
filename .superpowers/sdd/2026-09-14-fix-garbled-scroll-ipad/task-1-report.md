# T1 report — player.html text (Q1 + Q2-player)

## Changes (file: `music/templates/music/player.html` only)

1. **Line 369** — `#now-loading` placeholder `????????????????...` → `กำลังโหลด...`.
   Classes (`hidden text-xs text-slate-400 font-bold`) and show/hide JS untouched.
2. **Line 1779** — `showToast("เพิ่มเพลงหน้าคิวแล้ว!", "success")` → `showToast("เพิ่มเพลงหน้าคิวแล้ว", "success")` (trailing `!` removed).

No other Thai string in player.html ends with `!`: full UTF-8 scan found exactly one
`[ก-๛]!` occurrence (line 1779) and zero `!`-before-closing-quote Thai literals;
no HTML text node ends with `!`. Code operators (`!`, `!==`), URLs, CSS
(`!bg-*` Tailwind important modifiers, `!important`), English strings, and
`aria-label`s left untouched.

## Verification

- `Select-String -Pattern '\?\?\?\?' player.html` → Count 0 (was 1, line 369, before edit).
- UTF-8 scan: no literal `????` runs; `กำลังโหลด...` present inside `#now-loading` span; no Thai `!` remains.
- `.\venv\Scripts\python.exe manage.py test music.tests.PlayerPageTests` from `D:\mysong` → **OK, 14 tests, ~16 s**. No exact-string assert failures, so no test updates needed (tests.py untouched, owned by T2).

## Concerns

- None blocking. Note for T3: it owns player.html next (global touchstart/click → ensurePlaying + iPad boot hardening) — this lane is done with the file.
