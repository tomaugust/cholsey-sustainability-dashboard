# 2026-09-27 — Decisions confirmed, loop scheduling set up

- **Phase / tasks:** P0.2
- **Branch / PR:** `claude/new-session-7bcxu1` / not opened
- **Agent / person:** Claude Code agent, at Tom's request

## Goal
Record the project lead's answers to Q-001 through Q-004, update the plan and status accordingly, and set up a recurring session so the project keeps moving without waiting on a person to kick off every session.

## Done
- P0.2: ADR-0002 accepted, with the caveat that agents may deviate from the stack where hands-on experimentation finds good reason, via a superseding ADR.
- Q-002 resolved: electricity and gas are combined into one "Home energy" tile and detail page, which yields exactly five home-page tiles and reconciles spec §6 ("five tiles") with §3 (six core metrics). They remain two separate `metric_id`s in the data model. Updated development-plan.md §3 (P3.4, P4.4, P4.5) and the risks/open-questions section accordingly.
- Q-003 resolved: England is the default national comparator level; GB/UK only as a per-dataset fallback, labelled.
- Q-004 resolved: default GitHub Pages URL, no custom domain.
- Q-005 (content review / launch sign-off) left as TBD; noted that it doesn't block Phases 0–5 or the Phase 6/7 build work, only final approval steps.
- Updated `docs/STATUS.md`: task states, Next steps, and the open-questions table now shows resolutions.
- Set up a recurring `/loop` (see the scheduling note below) so the project self-progresses roughly every 5 hours, with an instruction to stop the loop rather than guess whenever it hits something only Tom can decide.

## Decisions
- ADR-0002 moved from Proposed to Accepted (with the experimentation caveat).
- No new ADR needed for the tile-combination decision; it's a UI/config detail, not a stack or scope change, so it's recorded in the plan and STATUS directly.

## Verification
Documentation-only session. Re-read `development-plan.md` after edits to confirm the five-tile list (canopy, green space, home energy, solar PV, heat pump) is consistent everywhere it's mentioned.

## Not done / carried over
- P0.3–P0.7 (pipeline, config, web and CI scaffolding) are next; see STATUS.md.

## Handoff notes
- When building `metrics.yaml` (P0.4) and the home page (P4.4), remember: electricity and gas are separate metric IDs but share a `tile_group`/grouping key so the front end renders one tile and one detail page for both.
- The recurring loop's prompt tells future sessions to cancel the loop (not just log a blocker) when they hit something needing Tom's direct input, so it won't keep firing uselessly. If you're a session picked up by that loop and you hit such a blocker, make sure you actually cancel it before ending the turn.
