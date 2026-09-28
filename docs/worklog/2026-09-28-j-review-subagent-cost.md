# 2026-09-28 — PR review subagent switched from Opus to Sonnet (cost)

- **Phase / tasks:** infrastructure/documentation (follow-up to the PR + review workflow added earlier today)
- **Branch / PR:** `claude/new-session-7bcxu1` / not opened (documentation-only, direct commit per that workflow's own carve-out)
- **Agent / person:** Claude Code agent, direct interactive session with Tom (not a routine firing)

## Goal
Tom asked to change the PR-review subagent from Opus to Sonnet, citing cost — this workflow runs unattended every ~2 hours, and an Opus subagent on every work-package PR adds up.

## Done
- Updated every reference in `development-plan.md` §4.5, `CLAUDE.md`, and `STATUS.md`'s Next steps from `model: "opus"` to `model: "sonnet"`.
- Added an explicit caveat everywhere the review step is described: this is now a **same-model self-review** (the working session and the reviewing subagent are both Sonnet), not an independent check from a stronger model. A clean verdict is a useful check, not a guarantee — flagged so a future session doesn't over-trust it just because a review "passed."
- Updated the routine's own trigger prompt is NOT part of this commit — see Not done below, this needs a separate `update_trigger` call outside the git workflow.

## Decisions
- No ADR — this is the same category of change as setting the workflow up in the first place (agent process, governed directly by development-plan.md §4), and it's a straightforward parameter change (which model reviews), not a new design.
- Kept the workflow's other mechanics (per-work-package granularity, auto-merge on green + clean, 2-cycle cap) unchanged — Tom's ask was specifically about the model, not the shape of the process.

## Verification
Documentation-only change — no code to test. Grepped all three files afterward for "Opus"/"opus" to confirm no stale references were left (only the historical worklog entries from earlier today, which correctly describe what was true when they were written, are left untouched — worklog entries are append-only history, not edited retrospectively, per §4.6).

## Not done / carried over
- The routine's own trigger prompt (`trig_01UeEpu3FYupU2DqgxXzSvpu`) needs updating separately via `update_trigger` — it currently still says `model: "opus"` in its step 3, since that's a live routine configuration outside the git repo, not a file this commit touches. Do this in the same chat turn as this commit, not as a follow-up task for a future session to remember.

## Handoff notes
- If cost is still a concern later, the next lever (not applied here, just noting it exists) would be lowering the review's effort level from `medium` to `low`, or reviewing only a subset of work packages (e.g. skip review for a trivial config-only change) rather than dropping the review step entirely.
