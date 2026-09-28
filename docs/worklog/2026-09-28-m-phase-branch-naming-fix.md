# 2026-09-28 — Phase branch naming scheme was invalid; fixed

- **Phase / tasks:** infrastructure (PR workflow, §4.5) — found while actually creating Phase 1's phase branch
- **Branch / PR:** `claude/new-session-7bcxu1` / not opened (documentation-only)
- **Agent / person:** Claude Code agent, same firing as the Q-006/Q-008/Q-009 actioning entry above

## Goal
Create `claude/new-session-7bcxu1/phase-1-remainder` as instructed by this morning's (today's) plan §4.5, to start P1.5 on it.

## Done
- `git checkout -b claude/new-session-7bcxu1/phase-1-remainder` failed immediately: `fatal: cannot lock ref 'refs/heads/claude/new-session-7bcxu1/phase-1-remainder': 'refs/heads/claude/new-session-7bcxu1' exists; cannot create`. Git branch names are filesystem-like paths under `refs/heads/` — `claude/new-session-7bcxu1` already exists as a leaf ref (a file), so nothing can also treat it as a directory by creating `claude/new-session-7bcxu1/anything`. The `<designated-branch>/phase-<N>-<slug>` naming convention written into §4.5 earlier today was never actually valid the moment both the designated branch and a phase branch need to coexist — which is every single time, since the designated branch never goes away.
- Fixed by using a hyphen instead of a slash: `claude/new-session-7bcxu1-phase-1-remainder`, created and pushed successfully.
- Updated the naming convention in `development-plan.md` §4.5 (step 1) and `CLAUDE.md`'s PR-workflow bullet to use `<designated-branch>-phase-<N>-<slug>`, with the reason spelled out so nobody re-introduces the slash. Fixed the two stray `/phase-1-remainder` mentions left in `STATUS.md` from the same-firing Q-006 actioning commit (pushed just before this branch-creation attempt).

## Decisions
- No ADR — a syntax-level fix to a convention set earlier the same day, not a new design choice.

## Verification
The branch now exists and is pushed: `claude/new-session-7bcxu1-phase-1-remainder` (confirmed via the `git push` output showing `* [new branch]`).

## Not done / carried over
- P1.5 itself starts now, on the correctly-named branch.

## Handoff notes
- This is exactly the kind of thing worth remembering: a convention that looks fine on paper (`<branch>/phase-N-slug`) can be structurally invalid in git the moment the parent name is itself a real branch that has to keep existing. If any other naming scheme gets proposed later (e.g. for something under `main` once that's the base for everything), sanity-check it the same way: would this name ever need to coexist with a branch that is a strict prefix of it?
