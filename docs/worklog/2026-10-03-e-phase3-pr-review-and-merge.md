# 2026-10-03 — Phase 3 PR review (2 cycles) and merge

- **Phase / tasks:** Phase 3 (all of P3.1-P3.5, P3.7-P3.10) — merged
- **Branch / PR:** `phase-3-metric-table` → `main`, [PR #3](https://github.com/tomaugust/cholsey-sustainability-dashboard/pull/3) (merged)
- **Agent / person:** Claude Code agent, live session with Tom

## Goal

Open and drive Phase 3's one phase-end PR to green and merged, per development-plan.md §4.5 — exit criteria (Q-012/ADR-0012, P3.10, Tom's plausibility sign-off) were all met earlier this session.

## Done

- Opened PR #3 into `main`. CI green on open.
- **Cycle 1 review** (Opus, `code-review` skill, high effort, `--comment`, plus a manual second pass): 17 inline comments. **3 blocking bugs**:
  1. `_build_energy_rows_for_fuel` silently apportioned over whichever LSOAs matched a given year's sheet, instead of requiring all of an area's weighted LSOAs to be present. DESNZ's pre-2015 LSOA sheets use 2011-vintage LSOA codes that don't match `weights.csv`'s 2021 codes, so Cholsey's 2010-2014 rows were built from 1 of 3 LSOAs (`flag=none`, as if direct), Crowmarsh's from a 0.1% boundary sliver, Moulsford had none at all.
  2. `build_metrics_csv.py`'s `main()` never actually called P3.8's data-quality checks (`validate_ranges`/`validate_yoy_change`/`check_completeness`/`validate_registry_references`) before writing output — only pandera's structural schema ran. Running them surfaced 3 real YoY breaches and 18 real completeness gaps that had been silently shipping.
  3. Greenspace summed each site polygon's own area instead of merging overlaps first (`.area.sum()` vs `.union_all().area`), double-counting real overlapping sites (e.g. a Play Space inside a Playing Field) — inflated every area figure 3.5-4%.
  Plus 9 secondary findings: MCS's subject row mislabelled `method=address_weighted` (the value is a direct unchanged copy); national canopy pagination not checking `exceededTransferLimit`; MCS/national-canopy-year provenance hardcoded instead of read live; national greenspace's fast boundary check not shrunk, risking a slight overcount; and wording/consistency corrections across ADR-0009 through ADR-0012.
- **Fixed all of the above** (commit `b8ec3c6`): required every weighted LSOA present before building a year's row (skip otherwise); wired the four DQ checks into `main()`, failing loudly on a violation; added 21 documented `dq_exceptions.yaml` entries (1 canopy gap, 18 MCS comparator/national gaps, 2 real YoY breaches — a genuine, systemic 2021→2022 electricity drop across all 9 areas, the UK energy-price crisis, verified by checking every area's own real YoY change); fixed greenspace to `.union_all()` at both call sites; relabelled MCS's method; fixed canopy pagination, MCS/canopy-year provenance, and the greenspace boundary buffer; corrected the ADR wording issues (a genuine 268-vs-26 metadata-count confusion resolved by re-fetching the full live dataset and confirming they're two distinct, non-overlapping populations, not a typo).
- Raised **Q-013** (MCS's reuse licence still unconfirmed, now published to the public site JSON) rather than deciding unilaterally — committed directly to `main` (docs-only).
- Replied to and resolved 15 of 17 review threads naming the fix commit; left 2 open (Q-013, and a golden-test-coverage suggestion addressed by fixing the root cause instead of adding the suggested test).
- **Cycle 2 review** (Opus, independent re-verification — recomputed the real numbers rather than just re-reading the diff): confirmed all 3 blocking fixes and 6 of the secondary fixes are genuinely correct (cross-checked the LSOA presence logic, re-ran the DQ checks against the committed CSV with an empty exceptions file to confirm they'd actually fail, independently recomputed the greenspace fixture areas from the `.gpkg` files). Found 4 small leftover issues: a stale "Real result" block in `golden_values.py` still showing the pre-fix arithmetic; a stale `REAL_ENGLAND_ACCESSIBLE_AREA_M2` test constant; ADR-0012 overstating that all 3 YoY breaches came from the LSOA bug (only 1 did); a docstring misplaced between two unrelated constants. Fixed all 4 (commit `e127673`).
- Merged `main`'s tip (which had moved — Q-013's commit) into the phase branch before merging.
- CI green on the final commit (`06cfafb`). Updated the PR description to reflect the final state (317 rows, not 337; CI checkbox ticked; review history summarized) before merging.
- **Merged PR #3** into `main` (merge commit `97badbc`). Verified the Pages deploy workflow ran and succeeded on the merge commit.
- Deleted the redundant raw MCS zip files from `data/` (housekeeping, logged since Phase 2) — the organized, parsed version in `fetch/reference_data/mcs_installations/` has always been the one actually used.
- Updated STATUS.md: Phase 3 moved to *Completed phases*, Phase overview table updated, Next steps point at starting Phase 4.

## Decisions

- No new ADRs this entry — all decision content is corrections to ADR-0009/0010/0011/0012, already described above.

## Verification

```
$ cd pipeline && uv run pytest        # 307 passed (both before and after cycle-2 cleanup)
$ cd pipeline && uv run ruff check . && uv run ruff format --check .   # clean
$ cd web && npm run test / build / lint   # all clean (verified before each push)
```
CI on PR #3's final head commit (06cfafb): both Pipeline and Web jobs green. Pages deploy on the merge commit (97badbc): completed, success.

## Not done / carried over

- **Branch deletion**: `git push origin --delete phase-3-metric-table` returned a 403 (this session's git credential can push/merge but not delete a remote branch), and no GitHub MCP tool for branch deletion is available. Logged in STATUS.md's Backlog for a human with full repo access to clean up — harmless, since the branch is fully merged.
- **Q-013** (MCS licence) and the golden-test-coverage suggestion remain open on the merged PR's thread (GitHub keeps resolved/open thread state after merge) — Q-013 also tracked in STATUS.md's Open Questions table.
- MCS comparator/national rows remain genuinely blocked (ADR-0007) — unaffected by this session, a known accepted gap going into Phase 4.
- Phase 4 (front-end skeleton) not started — next session's first step.

## Handoff notes

- **Start Phase 4 on a new `phase-4-<slug>` branch forked from `main`'s tip.** Worth checking early whether P4.1's "placeholder JSON generator" is still needed, since Phase 3 already produced the real `web/src/data/*.json` in the exact schema P4.1 asks for — may be able to skip straight to building against real data.
- If Tom answers Q-012-style open questions or Q-013 before the next firing, act on that first per plan §4.7 (it already outranks the task queue).
- The 2-cycle Opus review process worked as intended on real, substantive findings this time (unlike some earlier phases where cycle 2 just confirmed cycle 1's fixes) — worth noting that an agent assembling a large integration script (`build_metrics_csv.py`) across many separate firings is exactly the kind of accumulation where a fresh, skeptical re-read catches real bugs the original author's incremental view missed.
