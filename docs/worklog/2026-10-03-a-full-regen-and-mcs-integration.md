# 2026-10-03 — Full metrics.csv regeneration; MCS wired into the export

- **Phase / tasks:** P3.9 (regeneration), P3.5 (MCS integration, new), P3.10 (raised)
- **Branch / PR:** `phase-3-metric-table` (code) / `main` (this doc update) / no PR yet
- **Agent / person:** routine-firing agent (scheduled check-in, trigger `trig_01UeEpu3FYupU2DqgxXzSvpu`)

## Goal

Continue from the prior firing's interrupted work: the ONS Geoportal ArcGIS outage that blocked a full `metrics.csv` regeneration had not yet been confirmed to clear. Retry the full pipeline run, and pick up the next unblocked Phase 3 task.

## Done

- **Confirmed the ONS ArcGIS outage (reported in the prior firing's worklog) had cleared**: `curl`'d the parish boundary FeatureServer's and the ward-to-LAD lookup's own `?f=json` root directly — both returned real service metadata instead of `{"error":{"code":400,"message":"Invalid URL"}}`.
- **Ran the full `build_metrics_csv.py` pipeline successfully end-to-end** (two runs, see below): canopy (10 rows), greenspace (11 rows), electricity/gas (156 rows each — full real multi-year trend, 2010-2024 subject/comparator except Moulsford 2015-2024, 2012-2024 district/national). Confirmed every 2024/latest-year value is byte-identical to the prior (single-year) run — only `retrieved_at` changed and history was added, no regression.
- **Found and closed a real MCS integration gap**: `metrics/mcs.py`'s `compute_subject_uptake_row`/`compute_district_uptake_row` were built and tested back on 2026-09-30 (Q-011/ADR-0007) but `build_metrics_csv.py` never actually called them — the module's own top docstring still claimed MCS was "blocked on Tom's pending parish-level data request," which (per ADR-0007) wasn't true of the subject+district rows at all; only comparator/national rows are genuinely blocked. Added `_build_mcs_rows` and `_load_cholsey_households` (reads Cholsey's real household count from the already-committed `population_denominators.csv` rather than hardcoding); wired into `main()`. No live fetch involved — `fetch.mcs_installations.load_area_uptake` reads the already-committed reference CSVs, so provenance is the committed file's own sha256 plus `_provenance.json`'s documented 2026-09-30 manual-retrieval date.
- **Second full run** (after the MCS code change) produced the final **337-row** `metrics.csv`: the 333 rows above plus 4 new MCS rows (heat_pump/solar_pv × subject/district). Real values: heat pump 2.73% of Cholsey's dwellings (~48.6 estimated installs; South Oxfordshire 1,677 installs, `method=direct`/`flag=none`), solar PV 10.08% (~179.6 estimated; South Oxfordshire 6,198 installs) — matching the values already verified when `metrics/mcs.py` was first built.
- **Verified no regression**: 300 pipeline tests pass unchanged against the new file. The existing completeness check (`test_real_metrics_csv_has_exactly_the_documented_aldworth_gap`) only asserts on `["canopy", "greenspace", "electricity", "gas"]`, so MCS's genuinely-incomplete comparator/national coverage doesn't trip it (by design, not oversight — confirmed by reading the test). The range check (`test_real_metrics_csv_passes_range_checks`) iterates every real row including the new MCS ones, and passed.
- **Reviewed Phase 3's exact "benchmarks" wording (P3.7)** against the final table: "district and national rows for every metric" is not yet satisfied, because MCS only has a district row, not national — logged this precisely rather than marking P3.7 done.
- **Found a new, real gap**: no golden-value tests exist anywhere in the repo (`pipeline/tests/golden/`), despite development-plan.md's Phase 3 "Tests of success" explicitly requiring them. Logged as a new task, **P3.10**, rather than attempted this firing (it needs an independently hand-computed reference value, which deserves its own session rather than being rushed).

## Decisions

- No new ADR this firing — both changes (regenerating from already-ADR'd code, wiring up already-tested MCS logic) are mechanical integration, not new methodology.

## Verification

```
$ cd pipeline && source .venv/bin/activate && python3 -m pytest -q
300 passed

$ ruff check . && ruff format --check .
All checks passed!
```
Live runs: `build_metrics_csv.py` completed successfully twice this firing (once before the MCS change, 333 rows; once after, 337 rows). Both runs' logs are consistent with every previously-verified real value (canopy 10.40% Cholsey / 14.41% England; electricity/gas multi-year ranges; greenspace 20.23 m²/resident Cholsey). MCS values cross-checked against the real numbers already verified when `metrics/mcs.py` was built (2026-09-30 worklog): heat pump 2.73%/1,677 installs, solar PV 10.08%/6,198 installs, both South Oxfordshire.

## Not done / carried over

- **Q-012** (reconciliation test vs. ADR-0003 scope) still needs Tom's answer before P3.8's fourth check can be built.
- **P3.10** (golden-value tests) — newly identified, not started.
- **Phase 3's manual plausibility sign-off** (exit criteria) — not yet requested from Tom; worth doing once P3.10/Q-012 are further along so the review covers a more final table.
- MCS comparator/national rows remain genuinely blocked (each needs its own manual MCS dashboard pull, per ADR-0007) — unchanged from before this firing.
- The raw MCS zip files on `main` (`data/MCS_*.zip`) are still unremoved (housekeeping, logged previously, not urgent).

## Handoff notes

- If you're continuing Phase 3: P3.10 (golden values) is the most concrete, well-scoped next task — development-plan.md names the exact mechanism (hand-computed value per metric for Cholsey's latest year, committed under `pipeline/tests/golden/`, asserted equal to the pipeline's output in a pytest test).
- `_build_mcs_rows` in `build_metrics_csv.py` is a good template if comparator-level MCS data ever arrives (e.g. after more manual Tom pulls) — mirrors `metrics/energy.py`'s subject/comparator/district split pattern already used elsewhere.
- Remember: STATUS.md/worklog commits go directly to `main`; code (including regenerated `metrics.csv`/site JSON, which are generated-but-still-tracked data) goes to the phase branch. This firing's code commits are `b8a92a4` (MCS wiring) and `0ebe9d8` (regenerated data) on `phase-3-metric-table`; merge `main`'s tip into the phase branch again before any future phase-end PR, since this doc commit moves `main` forward independently.
