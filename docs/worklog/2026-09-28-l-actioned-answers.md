# 2026-09-28 — Actioned Q-006, Q-008, Q-009; logged Q-010

- **Phase / tasks:** cross-cutting (question-actioning per plan §4.7, not a single project task) — precedes starting P1.5
- **Branch / PR:** `claude/new-session-7bcxu1` / not opened (documentation-only + config, no code deliverable of its own)
- **Agent / person:** Claude Code agent, fired by the "Cholsey dashboard 2-hourly agent" routine (`trig_01UeEpu3FYupU2DqgxXzSvpu`)

## Goal
Per CLAUDE.md's reading-order rule and plan §4.7, checked `STATUS.md`'s Open questions table before picking up P1.5, and found Tom had answered three questions directly on GitHub since the last firing (Q-006, Q-008, Q-009) — all `open` with the answer cell filled in, which per protocol outranks the task queue. Actioned all three before starting any new code.

## Done
- **Q-009 (comparator set — "Use all 8"):** removed `pending_confirmation: true` from all 8 comparator entries in `config/geography.yaml`. ADR-0003's status moved from Proposed to Accepted, its "Decision (proposed)" section reworded to a plain Decision, Consequences updated. `docs/decisions/README.md` index updated. Updated the pipeline test that used to assert the flag was present (`test_comparator_parishes_are_explicitly_flagged_pending`) to instead assert it's gone (`test_comparator_parishes_have_real_confirmed_codes`) — 44/44 pipeline tests still passing.
- **Q-006 (Pages source + where phase PRs should target):** this answer had two parts.
  - *"the PR should be made to 'main'"* — a real, actionable workflow instruction. Rewrote `development-plan.md` §4.5 (steps 1, 4 and 8, plus the intro and transition note) and `CLAUDE.md`'s two PR-workflow mentions: the phase branch still forks from the designated branch's tip and still carries all in-progress docs/code as before, but the **PR itself now targets `main`**, not the designated branch. Since nothing has ever reached `main` yet, Phase 1's PR (once P1.5-P1.7 are done) will be the first — and because the phase branch forks from the designated branch's current tip, that one PR will carry Phase 0 and P1.1-P1.4 too, not just P1.5 onward. Every phase after that is a clean, phase-only diff into `main`.
  - *"Updated pages to run from actions"* — checked via `actions_list` (10 most recent runs, all still `pages build and deployment` / legacy branch-deploy, most recent at 18:51 UTC, same window as the answer) and a live fetch of the Pages URL (still a rendered README). If the source setting had actually saved as "GitHub Actions", the legacy mechanism should have stopped firing on pushes to the designated branch entirely — it hadn't, as of that check. Rather than assume either "he's right, ignore what I'm seeing" or "he's wrong, override his answer", logged this discrepancy as a fresh **Q-010** and left Q-006 fully actioned only for the part that was.
- **Q-008 (ward-vintage assumption → UKCEH suggestion):** Tom's answer wasn't really a direct answer to the vintage question, more a suggestion to reconsider the whole canopy data source. Recorded it as a concrete forward instruction rather than trying to force it into "resolves the vintage question": `config/sources.yaml`'s `forest_research_canopy` entry and `development-plan.md`'s risk R2 both now say P2.3 (Phase 2, not yet reached) should evaluate UKCEH's Land Cover Map first — it may update more often than Forest Research's one-off 2020 survey, which could give metric 1 a real trend instead of a single point (directly addressing risk R2's own complaint, not just Q-008's narrower vintage question).
- Moved all three (Q-006, Q-008, Q-009) into `STATUS.md`'s *Answered / closed questions*, in their own collapsed section (kept separate from the older Q-001–Q-004 block for a cleaner read). The live Open questions table now shows Q-005, Q-007 (both still genuinely open, untouched) and the new Q-010.
- Updated `STATUS.md`'s header, Next steps, and the P1.3 task row to reflect all of the above.

## Decisions
- No ADR for the PR-target-main change itself — same category as the day's two earlier PR-workflow revisions (agent process, governed directly by plan §4). ADR-0003's status *did* change (Proposed → Accepted), which is the normal outcome of a Q-NNN answer landing, not a new decision being made here.
- Judgement call: when re-checking Q-006's Pages claim turned up a discrepancy, chose to log it as a new question (Q-010) rather than silently trusting the claim, silently overriding it, or leaving Q-006 stuck half-`answered`/half-`actioned` in a confusing state. This keeps the record honest without accusing Tom of being wrong outright — the setting might genuinely not have saved, or GitHub's UI might behave differently than expected; a direct, specific question gets that resolved properly.
- Judgement call: Q-008's answer didn't map cleanly onto "resolve this specific working assumption" — rather than forcing a fit, recorded it as guidance for the future task (P2.3) where it actually applies, in the two places (`sources.yaml`, risk R2) a future session doing that work would actually look.

## Verification
```
$ python3 -c "import yaml; yaml.safe_load(open('config/geography.yaml')); yaml.safe_load(open('config/sources.yaml'))"
config/geography.yaml OK
config/sources.yaml OK

$ uv run pytest -q   # pipeline/
............................................                             [100%]
44 passed in 0.72s
```
The Pages/Actions discrepancy behind Q-010 was checked directly (`actions_list` for the 10 most recent workflow runs, a live `WebFetch` of the Pages URL) at the time of this session, not assumed from either direction.

## Not done / carried over
- P1.5 itself — this session's actual queued task — is next, now that the answered questions are actioned. Per the current plan, that means creating `claude/new-session-7bcxu1/phase-1-remainder` off the designated branch's tip and starting the real UPRN-weight work there.
- Q-005, Q-007, Q-010 remain open.

## Handoff notes
- If you're picking up P1.5 next: the phase branch doesn't exist yet as of this entry — create it fresh off the designated branch's current tip (which now includes this session's changes: geography.yaml/sources.yaml edits, ADR-0003 acceptance, the plan/CLAUDE.md PR-target-main change).
- If Q-010 gets answered and the Pages source really is now "GitHub Actions": no repo change needed, just note it resolved in STATUS.md — the deploy will start working the moment something reaches `main` regardless.
