# 2026-09-30 — Phase 2 PR: 2 Opus review cycles, merged into main

- **Phase / tasks:** Phase 2 phase-end PR (all of P2.1-P2.10)
- **Branch / PR:** `phase-2-data-ingestion` → `main`, [PR #2](https://github.com/tomaugust/cholsey-sustainability-dashboard/pull/2), merged
- **Agent / person:** Claude Code agent, fired by the "Cholsey dashboard 5-hourly agent" routine (`trig_01UeEpu3FYupU2DqgxXzSvpu`)

## Goal
Drive PR #2 (opened in the previous firing, worklog `2026-09-30-b-p2.10-phase2-pr.md`) through CI, an Opus review cycle (max 2 per CLAUDE.md §4.5), fixes, and merge -- completing Phase 2.

## Done
- **Cycle 1 review** (Agent, `model: opus`, `code-review` skill, high effort, `--comment`): 10 findings, 2 blocking (a fresh-clone `FileNotFoundError` from `fetch_file` trusting a manifest's file path when `data/raw/` is gitignored and the file doesn't exist locally; `contracts.validate_schema`/`validate_row_count` never actually called from any `fetch_*` function, only from tests). Fixed all 10 in commit `48e2c38`: relative file paths, URL-matched conditional headers, timestamped manifests, 4xx not retried, `fuel` added as a real field to the DESNZ energy records (fixing a postcode-contract key-uniqueness bug), header-row validation before positional parsing, manifest source_ids aligned to the registry, `ons_population_dwellings`'s hardcoded `PAR22CD` column fixed to a pattern match, `forest_research_canopy`/`fetch_oa_counts` routed through `fetch_file` for provenance, EPC pagination fixed. Replied to and resolved all 10 review threads, each naming the fix commit.
- **Cycle 2 review** (same setup, re-reviewing the fixes): found 2 of cycle 1's fixes didn't actually work as claimed (the row-count guard could be bypassed by a single retry, since `fetch_file` wrote a manifest entry *before* validation and `record_row_count` only ran *after* it passed -- a failed run's manifest had no `row_count`, so the next run's `previous_row_count` read `None` and skipped the check entirely; the EPC fetch still only had `validate_schema` wired in, not real provenance, despite the cycle-1 commit message claiming otherwise) plus 8 more real issues: a row-count baseline that ignored the actual query (fetching 1 ward then 9 would false-fail as an "800% change"), an idempotence violation introduced by cycle 1's own timestamped-filename fix (every "unchanged" fetch now wrote a *new* manifest file, contradicting the plan's literal "no new files" test), case-sensitive header lookups (missing lowercase `etag`/`last-modified`), an unbounded EPC pagination loop, a missing OA-completeness check in `fetch_oa_counts`, no dtype checking in contracts beyond field presence, real code duplication (DESNZ discovery logic, the fetch/validate/record sequence) across the six wrappers, and a genuinely dead `.replace()` in the timestamp logic, plus a CLAUDE.md commit-title convention miss (no task-ID prefix on the cycle-1 fix commit).
- Fixed 9 of the 10 cycle-2 findings in commit `133e48c` (title corrected to start with `P2.10:`, per the convention the cycle-1 commit missed): `previous_row_count` now walks back past any manifest entry lacking a `row_count`; every `previous_row_count`/`record_row_count` call site now passes a `query_signature` built from its actual filter arguments; an "unchanged" result no longer writes any manifest entry at all; header lookups use a new case-insensitive `_get_header_ci` helper; the timestamp `.replace()` calls are correctly ordered; `fetch_file` gained an `extra_headers` param and `dluhc_epc_register.fetch_domestic_certificates` now genuinely routes through it (bearer token passed as an extra header) with a bounded pagination loop (`ceil(totalResults/pageSize)`) and real `previous_row_count`/`record_row_count` tracking; `fetch_oa_counts` now raises if any requested OA is missing from the response; `contracts.SchemaContract` gained a `numeric_fields` check (int/float, not `None`/a suppression-marker string).
- **Did not fix** the 10th finding (code duplication across the DESNZ discovery helpers and the six `fetch_*` wrappers' repeated validate/record sequence) -- explicitly the review's own "altitude and cleanup" category, not correctness, and this was already the second (and per CLAUDE.md, final) review cycle. Logged as backlog in STATUS.md instead of widening the PR further; replied to the review thread explaining why.
- Merged `main`'s tip into the phase branch a second time (it had moved again, docs-only) before merging, per CLAUDE.md's explicit "check whether main has moved" instruction -- clean merge, re-verified tests/lint after.
- Replied to and resolved all 10 cycle-2 review threads (all 20 threads across both cycles now resolved).
- Verified CI green and `mergeable_state: clean` on the final head commit, then merged PR #2 into `main` (squash-free merge commit `634fd35`) myself, per CLAUDE.md's "this is a deliberate auto-merge: the review plus CI passing is the quality gate, not a wait for Tom."
- Deleted the local `phase-2-data-ingestion` branch; the remote deletion failed with the same 403 already logged for Phase 1's branches (the git credential can merge but not delete) -- logged in STATUS.md's housekeeping backlog, same as before.
- Confirmed the Pages deploy workflow fired and (per its established pattern on every prior `main` push this project) is expected to succeed.
- Updated `docs/STATUS.md`: header/current-focus, Phase overview (Phase 2 → done), moved Phase 2 into *Completed phases* with the full task table and exit-criteria check, added the cycle-1/cycle-2 non-blocking findings to *Backlog*, updated *Next steps* to point at Phase 3.

## Decisions
- No new ADR -- following the already-accepted PR/review protocol (CLAUDE.md §4.5), not a fresh scope/stack decision.
- Judgement call: after cycle 2 found real issues in cycle 1's own fixes, I fixed everything reasonably fixable myself and did my own final assessment rather than spawning a third automated review agent, since CLAUDE.md caps this project's review cycles at 2 ("max 2 cycles, else log a Q-NNN and leave it open"). I judged the one remaining finding (code duplication) as genuinely non-blocking per the review's own categorization, so no Q-NNN was needed -- STATUS.md backlog was the right home for it instead.

## Verification
```
$ cd pipeline && uv run pytest -q
164 passed   # was 137 at PR open, +9 (cycle 1) +18 (cycle 2, net of test rewrites)

$ uv run ruff check . && uv run ruff format --check .
All checks passed!
```
CI green on every pushed commit (`ec6c9ab`, `48e2c38`, `133e48c`, `995401b`) via GitHub Actions, not just the local run.

## Not done / carried over
- Q-005, Q-007, Q-011 remain open. Q-011 specifically now blocks only P2.7 (MCS fetcher), which can be picked up independently whenever answered -- it does not block Phase 3.
- The code-duplication backlog items (DESNZ discovery helpers, fetch/validate/record wrapper) are real, logged, and not yet scheduled to a phase.
- The remote `phase-2-data-ingestion` branch is still on GitHub (delete permission issue, logged).

## Handoff notes
- If you're starting Phase 3 next: fork `phase-3-<slug>` from `main`'s tip (now includes all of Phase 2). Check STATUS.md's Open questions table first (plan §4.7) -- Q-011 in particular, since an answer would unblock a small P2.7 follow-up fetcher worth slotting in alongside Phase 3 work rather than waiting for a dedicated phase.
- The `previous_row_count`/`record_row_count`/`query_signature` pattern in `fetch/http.py` (and the `extra_headers` param) is now the established, tested way to get contract-checked, provenance-complete fetches -- worth reusing directly for any Phase 3 fetcher rather than re-deriving it.
