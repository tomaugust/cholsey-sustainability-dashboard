# 2026-09-28 — STATUS.md authority clarified; post-Phase-1 cutover plan documented

- **Phase / tasks:** infrastructure (PR workflow, §4.5) — answering a direct question from Tom, not a queued project task
- **Branch / PR:** `claude/new-session-7bcxu1` / not opened (documentation-only)
- **Agent / person:** Claude Code agent

## Goal
Tom asked: now that phase branches PR back into `main`, once Phase 1's PR merges, is `main`'s `STATUS.md` the authority, or the working phase/designated branch's? This exposed a real gap — the workflow never said which copy governs while both branches exist, or what happens to the designated branch once `main` starts receiving merges.

## Done
- Added a "Which `STATUS.md` is authoritative, while both branches exist" subsection to `development-plan.md` §4.5: while `main` has not yet received Phase 1's PR, the designated branch's `STATUS.md` is authoritative (it's the only one that's current — `main` still holds the pre-project skeleton). After each phase-end merge, `main`'s copy is current for that phase but the designated branch keeps moving during the next phase's work, so it goes back to being ahead until the next merge — this lag is by design, not a bug, for every phase **except** Phase 1.
- Added a "Planned cutover, right after Phase 1's PR merges into `main`" subsection: Phase 1 is a one-time special case. Because it's the *first* PR ever to reach `main`, immediately after it merges the designated-branch/`main` split is retired entirely — `main` becomes the sole ongoing branch for both docs and future phase branches (simplified names from then on: `phase-<N>-<slug>`, no `claude/new-session-*` prefix). From Phase 2 onward there is only ever one branch's `STATUS.md` to consult between merges: `main`'s, kept current by documentation-only commits straight to `main` during each phase (mirroring how the designated branch worked during Phase 0/1), with phase branches forking from `main` and merging back into it.
- Amended §4.5 step 8 (the merge step) with a call-out: if this is Phase 1's merge, do the cutover in the same session, before opening Phase 2's branch — update `development-plan.md`/`CLAUDE.md` to say `main` instead of "the designated branch" throughout, and stop treating `claude/new-session-7bcxu1` as special.
- Amended the "Transition note (Phase 1)" paragraph to reference the cutover.
- Added a bullet to `CLAUDE.md`'s Documentation duties: **"The designated branch is temporary."** — summarises the lag/authority rule and the cutover, and instructs a future session picking up work post-cutover to treat `main` as "the designated branch" and flag it if the docs weren't updated as part of that cutover (a safety net in case a session does the merge but skips the cutover step).
- Added a pointer to this in `STATUS.md`'s Current focus line, spelling out which copy is authoritative right now and where the cutover is documented.

## Decisions
- No new ADR — this is a workflow/process clarification governed directly by plan §4, same category as the day's earlier PR-workflow revisions, not a project-level decision needing Tom's sign-off.
- Judgement call: made the cutover a hard, mandatory step tied specifically to Phase 1's merge (not "eventually," not left to a future session's discretion) so it can't be silently skipped — the "If this was Phase 1's merge" callout in step 8 and the CLAUDE.md safety-net bullet are the two enforcement points.

## Verification
Read-through only; no code or config changed, so no tests run. Confirmed by re-reading the edited sections of `development-plan.md` and `CLAUDE.md` after writing them.

## Not done / carried over
- The actual cutover doesn't happen yet — it's a documented plan, executed only once Phase 1's PR actually merges into `main` (still pending P1.5-P1.7).
- P1.5 (apportionment weights) is still the next real project task, on `claude/new-session-7bcxu1-phase-1-remainder`.

## Handoff notes
- If you're the session that merges Phase 1's PR: don't skip the cutover. It's in §4.5 step 8 and CLAUDE.md's "designated branch is temporary" bullet — do it in the same session as the merge, not as a follow-up.
- If you're a session starting *after* the cutover has already happened and you find `CLAUDE.md`/the plan still talking about "the designated branch": that means a previous session merged Phase 1 without completing the cutover step. Finish it before doing anything else — treat it like an answered-but-unactioned Q-NNN in urgency.
