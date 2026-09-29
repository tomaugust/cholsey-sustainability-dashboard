# 2026-09-28 — PR workflow changed: one Opus-reviewed PR per phase

- **Phase / tasks:** infrastructure/documentation (second revision of today's PR + review workflow — see the two earlier worklog entries this same day)
- **Branch / PR:** `claude/new-session-7bcxu1` / not opened (documentation-only, direct commit per the workflow's own carve-out)
- **Agent / person:** Claude Code agent, direct interactive session with Tom (not a routine firing)

## Goal
Tom changed his mind after the Sonnet-cost conversation earlier today: he wants Opus back for the review, but only one PR per phase (not per work package) — presumably to keep the Opus cost down to one review per phase rather than one per work package, while getting the stronger, independent-model review back.

## Done
- Rewrote **development-plan.md §4.5** for real, not just a find-replace this time — per-phase PRs are a genuinely different shape of workflow from per-work-package ones, not just a bigger version of the same thing:
  - One branch per **phase** (`<designated-branch>/phase-<N>-<slug>`), not per work package. All of a phase's work-package commits land on it, pushed as they happen.
  - **Docs go to a different branch than code, deliberately, for the first time**: `STATUS.md`/worklog updates still happen every session as before, but go straight to the designated branch (not the phase branch), so Tom's visibility into progress doesn't disappear for the days a phase might take. Code commits alone live on the phase branch until the phase-end PR.
  - The PR opens only once every work package in the phase is done (or as many as can be, same "don't let a blocked one hold up the rest" rule as always).
  - Review: `model: "opus"` (back from Sonnet), `high` effort (bumped from `medium` — explicitly reasoned: a phase-sized diff is bigger, and reviewing it well less often is exactly the point of moving to per-phase in the first place).
  - Same auto-merge-once-clean rule as before, but merging now also marks the whole phase `done` in `STATUS.md`.
- **Transition handling for the in-flight Phase 1**: P1.1-P1.4 already merged directly to the designated branch before either version of this workflow existed today. Rather than retroactively unwind that, Phase 1's phase branch and PR cover only P1.5 onward — stated explicitly in §4.5, `CLAUDE.md`, and `STATUS.md`'s Next steps, with the exact branch name (`claude/new-session-7bcxu1/phase-1-remainder`) spelled out so the next session doesn't have to reconstruct this reasoning.
- Updated `CLAUDE.md`'s non-negotiable rule and PR-workflow summary bullet to match.
- Updated `STATUS.md`'s Next steps item 0 with the concrete first action: create/checkout the phase-1-remainder branch before starting P1.5.
- The routine's trigger prompt update is **not** part of this commit — same as the Sonnet change earlier, that's a live routine configuration, handled separately via `update_trigger` in the same chat turn as this commit.

## Decisions
- No ADR — same category as the two earlier process changes today (agent workflow, governed directly by development-plan.md §4).
- The "docs go to the designated branch, code goes to the phase branch" split is the one genuinely new piece of design here (not just reverting the model/effort). Worth being explicit about why: with per-work-package PRs, each small PR carried its own docs update, so nothing was ever stale for long. With one PR per phase — potentially spanning many 2-hourly routine firings over a day or more — leaving `STATUS.md` only on an unmerged phase branch would mean Tom (or a fresh cold-start session) reading the designated branch mid-phase sees stale status. Splitting docs and code between branches avoids that without needing anything more complex (like a bot posting status comments, or Tom having to check out the phase branch himself to see progress).

## Verification
Documentation-only change — no code to test. Re-read all three changed files after editing to confirm the docs/code branch split is stated consistently and the transition note (P1.1-P1.4 predating this) appears wherever the phase-1-remainder branch is mentioned, so it can't be read as covering the whole phase by mistake.

Still untested end-to-end — P1.5 (via the new `phase-1-remainder` branch) will be the first real run of this exact shape of the workflow, having gone through two revisions today before anything was actually exercised.

## Not done / carried over
- Update the routine's trigger prompt (`trig_01UeEpu3FYupU2DqgxXzSvpu`) to match — separate `update_trigger` call, same chat turn as this commit, not a follow-up task.
- P1.5 itself, now via `claude/new-session-7bcxu1/phase-1-remainder` — next.

## Handoff notes
- If you're the session that creates `claude/new-session-7bcxu1/phase-1-remainder`: branch it from the current tip of the designated branch (which already has P1.1-P1.4 on it), not from some earlier point — the phase branch should contain everything the designated branch has, plus P1.5-P1.7 on top, so the eventual PR's diff is clean (just the new work) rather than showing spurious changes.
- Remember the docs/code branch split when you're mid-phase: `STATUS.md` and worklog commits go to the designated branch (checkout it, commit, push, switch back to the phase branch), not to the phase branch itself.
