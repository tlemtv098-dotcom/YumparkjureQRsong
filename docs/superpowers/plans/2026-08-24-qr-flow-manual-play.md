# QR Flow & Manual Play Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement QR code flow (scan → request page → auto-play on player) and add manual search/play on player page when queue is empty.

**Estimated tasks:** 5 | **Estimated time:** ~45 min | **Touches:** Frontend (player.html, request.html), API (views.py)

## Current Problem / Current Solution

**Current problems:**
1. QR code works but flow isn't seamless - scan opens request page but player doesn't auto-play new requests immediately
2. Player page has no manual search/play when queue is empty - just shows idle splash
3. Request page has preview but no direct "play now" from request page

**Current behavior:**
- QR scan → request page → user searches → clicks "ขอเพลง" → song added to queue → player polls queue every 3s → plays
- Player page: only plays from queue, no manual control when empty

## Proposed Approach

1. **Request page**: Add "เล่นทันที" (Play Now) button that adds to queue AND triggers immediate play on player page via WebSocket/polling optimization
2. **Player page**: Add search bar + play controls when queue is empty (manual mode)
3. **Optimize polling**: Reduce poll interval when queue changes, or add "force play" trigger
4. **Manual mode**: When queue empty, show search + play controls instead of idle splash

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| User scans QR, requests song | Song added to queue, plays after 3s poll | Song plays immediately on player page |
| Queue empty, venue wants music | Idle splash with QR only | Search bar + manual play controls |
| Venue wants specific song | Must use request page | Search + play directly on player page |

## Assumptions & Risks

- **Assumed:** Polling every 3s is acceptable for "immediate" play (can optimize to 1s when queue changes)
- **Assumed:** YouTube IFrame API allows programmatic playVideo() after loadVideoById()
- **Risk:** Browser autoplay policy may block playVideo() without user interaction
- **Risk:** YouTube embedding disabled (Error 153) still applies to manual play

## Impact

- Seamless QR → request → play flow
- Venue can play music manually when no customers
- Better UX for venue operators

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Add manual search/play to player.html]** - Lane A | Can run together: [Task 2] | Must wait for: [none] | TDD slice: search input renders -> search API call -> playVideo() works
2. **[Add "เล่นทันที" button to request.html]** - Lane B | Can run together: [Task 1] | Must wait for: [none] | TDD slice: button renders -> API call -> triggers immediate play
3. **[Optimize player polling for immediate play]** - Lane A | Can run together: [none] | Must wait for: [Task 1] | TDD slice: poll interval reduces -> playNext() triggers immediately
4. **[Add manual play controls to idle splash]** - Lane A | Can run together: [none] | Must wait for: [Task 1] | TDD slice: idle splash shows search -> play button works
5. **[Test full flow: QR → request → auto-play]** - Sequential | Can run together: [none] | Must wait for: [Task 1, 2, 3] | TDD slice: scan QR → request → player plays immediately

---