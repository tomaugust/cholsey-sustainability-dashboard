# 2026-09-28 — PR + Opus code-review workflow added

- **Phase / tasks:** infrastructure/documentation (agent workflow process, not a phase task)
- **Branch / PR:** `claude/new-session-7bcxu1` / not opened (this itself is a documentation-only change, committed directly per the new rule's own carve-out)
- **Agent / person:** Claude Code agent, direct interactive session with Tom (not a routine firing)

## Goal
Tom asked whether project work should go through a PR after each phase, with an Opus agent triggered to review it and Sonnet routines acting on the findings. Design and put in place a concrete, immediately-usable version of that.

## Done
- Discussed granularity and merge-autonomy with Tom directly (two real judgement calls, not mine to make unilaterally): confirmed **per work package** (not per whole phase — matches the plan's existing "one work package per PR" convention, and keeps diffs small enough for a real review) and **auto-merge** once CI is green and the Opus review has no blocking findings (not a wait for Tom to click merge — matches the project's whole "keep moving unattended, only stop for Tom when it's a real decision" design).
- Rewrote **development-plan.md §4.5** with the concrete step-by-step protocol: branch off the designated branch per work package → work, test, lint locally → commit (docs included) → push → open a PR → wait for the *real* GitHub Actions run (not just trust the local run, since this is now the actual merge gate) → spawn an Opus review (`Agent` tool, `model: "opus"`, the `code-review` skill, `medium` effort, `--comment` so findings post as real inline PR comments) → fix blocking findings and re-review, capped at 2 cycles (a third unresolved cycle becomes a logged `Q-NNN` and the PR stays open, not an infinite loop) → merge once clean, done by the agent itself, not Tom.
- Scoped it deliberately: this applies to `P<phase>.<n>` project work, not to documentation-only commits (a `STATUS.md` correction, actioning an answered question, a worklog entry with no code) — those stay as lightweight direct commits, same as they've been throughout Phase 0/1 so far. Making every doc tweak go through a full PR+review cycle would be disproportionate overhead for no real risk.
- Updated **CLAUDE.md**: replaced the now-stale "one phase per PR" rule with the real one, and added a concise one-line version of the PR workflow under Documentation duties, so it's visible on the very first file read every session, not just three files deep in the plan.
- No ADR — same category as the earlier answer/action-tracking protocol change (§4.7): agent workflow process, which development-plan.md §4 already governs directly, not a project architecture or scope decision.

## Decisions
- **Per-work-package granularity, not per-phase** (Tom's confirmed choice, offered as the recommended option): a whole-phase PR (Phase 1 is already 7 work packages, 5 commits so far) would be too large a diff for Opus to review with real precision. Smaller PRs get better reviews.
- **Auto-merge on green + clean review** (Tom's confirmed choice, offered as the recommended option): the quality gate is Opus review + passing tests, not a human click. This is a real trust decision — flagged as such rather than assumed — and Tom chose it explicitly because it matches the project's whole reason for existing (autonomous progress between his check-ins).
- Capped review cycles at 2 before falling back to a logged `Q-NNN` and an open PR: a bound was needed so a genuinely stuck disagreement between the working session and the reviewing session doesn't loop forever burning cost with nothing to show for it.

## Verification
Documentation-only change (this entry, `STATUS.md`, `CLAUDE.md`, `development-plan.md` §4.5) — no code to test. Re-read all three changed files after editing to check the cross-references (`§4.5`, `§4.7`) are consistent and the rule doesn't contradict itself (e.g. that "documentation-only changes stay direct" is stated the same way in both `CLAUDE.md` and the plan).

The protocol itself is **untested by an actual PR cycle yet** — P1.5, the next queued project task, will be the first real run of it. Worth watching closely: does the Opus subagent actually post inline PR comments correctly via `--comment`, does the CI-polling step work as expected, does the auto-merge behave. If something about the mechanics doesn't work as described here, fix the *protocol* (this file's guidance), not just work around it silently in one session.

## Not done / carried over
- P1.5 itself — next, now via the new PR workflow (see `STATUS.md` Next steps item 0).
- No PR template changes were needed — `.github/pull_request_template.md` (from P0.1) already asks for task IDs, verification, and a docs-updated checklist, which fits this workflow without modification.

## Handoff notes
- If you're the first session to actually run this end-to-end (most likely P1.5): read development-plan.md §4.5 closely before starting, not just this summary — it has the exact step order. If any step doesn't work the way it's described (e.g. `actions_list`/`actions_get` polling, the `Agent` tool's `model: "opus"` override, or `--comment` on the `code-review` skill), don't paper over it — fix the instructions here so the next session doesn't hit the same surprise.
- Branch naming convention: `<designated-branch>/p<phase>.<n>-<short-slug>`, e.g. `claude/new-session-7bcxu1/p1.5-apportionment-weights`.
