# Work Log

One file per agent (or human) working session, named `YYYY-MM-DD-<short-slug>.md`. If there are several sessions on the same day, add a suffix: `2026-10-02-b-desnz-fetcher.md`. Entries are **append-only history**: don't rewrite past entries except to correct facts, and mark any correction as an edit.

The worklog is the **past**. Current state belongs in [`../STATUS.md`](../STATUS.md), and reasons for decisions belong in [`../decisions/`](../decisions/). Link to them rather than duplicating them.

## Template

```markdown
# YYYY-MM-DD — <short title>

- **Phase / tasks:** P<n>.<m>, …
- **Branch / PR:** <branch> / <PR link or "not opened">
- **Agent / person:** <who>

## Goal
What this session set out to do (one or two sentences).

## Done
- P<n>.<m>: what changed, with key files.

## Decisions
- ADR-NNNN <title> (Accepted/Proposed), or "none".
- Minor choices not worth an ADR: one line each.

## Verification
Commands run and **actual results**, for example `make test` → 42 passed, 0 failed. For data work, include key numbers (row counts, years covered, Cholsey latest values). For UI work, link screenshots.

## Not done / carried over
What's incomplete and why. These must also appear in STATUS.md Next steps.

## Handoff notes
Anything the next agent needs that isn't obvious from the code or STATUS: gotchas, surprising upstream data quirks, half-finished experiments.
