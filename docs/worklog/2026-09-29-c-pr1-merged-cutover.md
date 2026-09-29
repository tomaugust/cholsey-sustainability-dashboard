# 2026-09-29 — PR #1 merged; designated-branch cutover executed; a real doc-sync gap found and fixed

- **Phase / tasks:** Phase 1 close-out (plan §4.5), cutover (plan §4.5's cutover section)
- **Branch / PR:** `main` (direct, per the cutover — this is the first entry written directly to `main`) / [PR #1](https://github.com/tomaugust/cholsey-sustainability-dashboard/pull/1), merged
- **Agent / person:** Claude Code agent, fired by the "Cholsey dashboard 2-hourly agent" routine (`trig_01UeEpu3FYupU2DqgxXzSvpu`)

## Goal
Merge PR #1 (cycle 2 of the Opus review came back clean, recommending merge as-is), execute the mandatory post-Phase-1 cutover, and confirm everything actually landed correctly.

## Done
- Merged PR #1 into `main` (merge commit `f7550d5`, title `P0-P1: Foundations and boundaries & geographic scope`, regular merge not squash — the individual work-package commit history was worth preserving).
- Attempted to delete the phase branch (`git push origin --delete claude/new-session-7bcxu1-phase-1-remainder`) — got a 403; the git credential this session has can push and merge but not delete a remote branch, and no GitHub MCP tool for branch deletion was available either. Logged as a harmless housekeeping item in `STATUS.md`'s backlog (both branches are fully merged, so nothing is at risk, just untidy).
- Verified `deploy.yml` fired on the merge and completed successfully (build + deploy jobs both green). **Fetched the live Pages URL to check** — it still serves the legacy branch-deploy's rendered README, not the Astro build. This is strong, first-hand confirmation of Q-010's suspicion (logged 2026-09-28): the "Deploy from a branch"/"GitHub Actions" Pages sources are mutually exclusive, so a successful Actions deployment not actually being served means the Settings → Pages → Source switch likely never saved as "GitHub Actions" despite Tom's Q-006 answer. Updated Q-010 with this new evidence rather than closing it or silently assuming either way.
- **Found and fixed a real process gap while executing the cutover.** The plan's cutover text (written earlier this session, before Phase 1's PR existed) assumed "content should already match, since the phase branch carried the latest docs into main" — that assumption was wrong. The phase branch was forked from the designated branch's tip *before* several docs-only commits landed on the designated branch (the cutover plan itself, the P1.5/P1.6/P1.7 STATUS.md updates, and both review-cycle worklog entries) — those commits, by design, only ever went to the designated branch, never to the phase branch. So when PR #1 merged, `main` ended up with a `STATUS.md`/`development-plan.md`/`CLAUDE.md` that was **several commits stale** (still saying "Next: create phase-1-remainder and do P1.5", with no mention of P1.5-P1.7 being done, no ADR-0004/0005, no cutover plan at all).
  - Fixed by merging `origin/claude/new-session-7bcxu1` (the designated branch, at its final state) into `main` directly — a clean merge with no conflicts, since the phase branch and designated branch had been touching different files (code vs. docs) since they diverged. This brought all 5 missing worklog entries and the correct, up-to-date `STATUS.md`/`development-plan.md`/`CLAUDE.md` onto `main`.
  - Added a new step (plan §4.5 step 10) capturing this lesson for every future phase: before merging a phase's PR, check whether `main` has moved since the phase branch was forked, and merge `main`'s tip into the phase branch (or vice versa right after merging) if so.
- **Executed the rest of the cutover**: rewrote development-plan.md §4.5 and CLAUDE.md's two PR-workflow mentions to say `main` throughout instead of "the designated branch" (kept the old wording as clearly-marked historical/transition notes, not deleted outright, so the reasoning behind Phase 1's now-obsolete branch-naming constraint isn't lost). `STATUS.md` now lives solely on `main` from this entry onward.
- Marked Phase 1 `done` in `STATUS.md`'s Phase overview, moved its task table into *Completed phases* (mirroring Phase 0's treatment), and set Phase 2 to "not-started, ready to begin".
- Verified the final state: `git log`/`git diff` confirm `main`'s `STATUS.md`, `development-plan.md`, `CLAUDE.md`, and all 5 previously-missing worklog entries are present and correct; `git push origin main` succeeded and a fresh `git fetch` shows origin matches local.

## Decisions
- No new ADR — the cutover was already decided and documented earlier this session (as a plan revision, itself not requiring an ADR per the established precedent for process/workflow changes); this entry executes that decision and fixes an implementation bug in how it was originally planned (the false assumption that phase branches stay in sync with docs-only commits elsewhere).
- Judgement call: merged the designated branch into `main` (rather than, say, hand-copying the missing worklog files and manually reconciling STATUS.md) because it was clean, safe (no conflicts, verified before pushing) and preserves full history/attribution for those commits, consistent with using a regular merge (not squash) for PR #1 itself.

## Verification
```
$ git log --oneline main | wc -l
23   # LICENSE (pre-existing) + PR #1's merge + all Phase 0/1 commits + the docs-sync merge

$ ls docs/worklog/ | wc -l
# includes 2026-09-28-m, -n, -o and 2026-09-29-a, -b that were missing right after the PR-only merge

$ grep -n "designated branch" CLAUDE.md docs/development-plan.md
# only appears now in explicitly-historical/transition-note context, not as live instruction
```
Live-fetched `https://tomaugust.github.io/cholsey-sustainability-dashboard/` and confirmed by eye it's still the rendered README (heading "Cholsey Parish Sustainability Dashboard" appearing in GitHub's markdown-render style, not an Astro layout).

## Not done / carried over
- Q-005, Q-007, and the now-updated Q-010 remain open.
- Phase 2 (data ingestion) is ready to start, on a `phase-2-<slug>` branch forked from `main`.
- The un-deleted branches (`claude/new-session-7bcxu1`, `claude/new-session-7bcxu1-phase-1-remainder`) — harmless, logged in STATUS.md backlog, deletable by anyone with full repo access whenever convenient.
- All the Opus review's non-blocking findings from both cycles — logged in STATUS.md backlog, not yet scheduled to a phase.

## Handoff notes
- **This is the first worklog entry and STATUS.md update made directly on `main`.** From here on, docs-only commits go straight to `main`, and phase branches fork from `main`'s tip with plain `phase-<N>-<slug>` names — no more designated-branch prefix, no more of the slash-collision risk that caused Phase 1's branch-naming fix.
- If you're starting Phase 2: read development-plan.md §3 Phase 2 and §4.5 (now updated) before branching. The MCS licence "TBD" note (P2.7) and the UKCEH Land Cover Map evaluation (P2.3, per Q-008) are both already flagged in `config/sources.yaml` for whenever those tasks come up.
- The lesson from this entry's docs-sync fix generalizes: **always check `git log main..<any-other-branch-you're-about-to-merge>` (and the reverse) before assuming two branches agree on non-code files**, especially in any workflow that deliberately splits docs and code commits across branches.
