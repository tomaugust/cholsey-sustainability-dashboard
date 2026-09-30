# Project Status

**Last updated:** 2026-09-30 by agent (Tom has submitted a formal MCS data request for Cholsey parish-specific installation data; given the parish's exact live postcode list to aid it). See [worklog](worklog/2026-09-30-j-p2.7-p3.5-mcs-q011.md).
**Current phase:** Phase 3: Geographic join & metric table (`active`) — Phase 0, 1 and 2 are `done`
**Current focus:** Phase 3 branch `phase-3-metric-table` has P3.1, P2.7 and P3.4 **done**; P3.5 has subject+district rows (district-rate-applied-to-parish estimate); P3.2/P3.3 still subject-row-only.
- **MCS parish-level data request pending** (2026-09-30, Tom's side, no ADR/Q-NNN needed — just a status to watch): after Q-011 was actioned with South Oxfordshire-level MCS data, Tom asked how to describe Cholsey precisely for a formal MCS data request; he was given the parish's ONS/GSS code (E04012474) and the exact list of 123 live postcodes ONS's Postcode Directory currently assigns to Cholsey (live-queried, since OX10 alone is shared with Wallingford and others) and has now submitted the request. **Outcome unknown — check for a reply before doing more P3.5 comparator/national work**; if MCS returns real parish-level figures, `metrics/mcs.py`'s subject row should move from `method=address_weighted`/`flag=parish_estimate` to `method=direct`/`flag=none`, superseding the current district-rate estimate.
- **Q-011 answered and actioned** (prior firing): Tom manually pulled the real MCS Data Dashboard export for South Oxfordshire (heat pump + solar PV — no bulk API exists, confirmed by P2.7's earlier investigation). Filed and parsed: `fetch/reference_data/mcs_installations/` (real CSVs + `_provenance.json`), `fetch/mcs_installations.py`, `metrics/mcs.py` (`compute_subject_uptake_row`/`compute_district_uptake_row`). Real 2026 values: heat pump 2.73% of households (South Oxfordshire), ~48.6 estimated installs for Cholsey; solar PV 10.08%, ~179.6 estimated. ADR-0007 moved Proposed → Accepted.
- Earlier still: **P3.4 comparator rows** (real LSOA area weights for all 9 parishes, `fetch_boundary`'s new `bbox` param) and **Q-007 actioned** (Cholsey's `area_km2` now the live ONS figure, 15.91 km²) — see the prior worklog entry for detail.

241 pipeline tests passing. P3.2/P3.3 still need comparator rows (now much easier — real area weights already committed) and district/national. Next: check for MCS's reply first; otherwise P3.5's comparator/national rows (more manual pulls, or fix the browser-automation/proxy issue) or P3.2/P3.3's comparator rows. Q-005 remains open.

> How to maintain this file: see [development-plan.md §4](development-plan.md#4-agent-working-protocol--documentation-strategy). It holds the **present** only. Overwrite it; don't append history. Update it at the end of every session.
> Task states: `todo` · `in-progress` (branch) · `review` (PR) · `blocked` (reason) · `done` · `deferred` (reason)

---

## Next steps (ordered, and the first one is actionable by a cold-start agent)

0. **Continue Phase 3 on `phase-3-metric-table`** (P3.1, P2.7 and P3.4 done; P3.5 subject+district done; P3.2/P3.3 subject-row-only). Reasonable next steps, any order:
   - **P3.5's parish-level MCS request is pending Tom's side** (2026-09-30): Tom has submitted a formal data request to MCS for Cholsey parish-specific installation data (not just South Oxfordshire) — he was given the parish's ONS/GSS code (E04012474) and the exact list of 123 live postcodes ONS's own Postcode Directory currently assigns to Cholsey (live-queried via `Online_ONS_Postcode_Directory_Live`'s `PARNCP26CD` field — OX10 alone isn't precise enough, it's shared with Wallingford and others). **Check for Tom's reply before doing more manual-LA-pull work on P3.5's comparator/national rows** — if MCS returns real parish-level data, it supersedes the district-rate-applied-to-parish estimate entirely and changes `metrics/mcs.py`'s subject-row method from `address_weighted`/`parish_estimate` to `direct`/`none`. No fixed timeline; a future firing should just check STATUS.md/chat for an update before assuming this is still needed.
   - **Alternatively, continue P3.5's comparator/national rows** while waiting: MCS's dashboard only gives one Local Authority's figures per manual export session — each comparator (or a national/England aggregate) needs its own manual dashboard pull the same way Tom did for South Oxfordshire, or a working browser-automation path (this session's Playwright attempt against the real dashboard hit a TLS error from this environment's outbound proxy, not the dashboard itself — worth another attempt with proxy config fixed).
   - **P3.6** (stretch, EPC) needs an API key not yet registered — not currently actionable.
   - **Finish P3.2's comparator rows**: `data/processed/geography/weights.csv` now has real LSOA area weights for all 9 parishes, but metric 1 needs *ward* weights, not LSOA — still needs (a) each of the 8 comparator parishes' containing ward (extend `compute_parish_ward_weights` from P1.5, now easier since `fetch_boundary`'s new `bbox` param can find every comparator's ward(s) in one live call, the same pattern `scripts/build_weights_csv.py` now uses for LSOAs); (b)/(c) district/national canopy still need a ward→LAD lookup and an England-wide ward aggregate respectively.
   - **Finish P3.3's comparator rows**: reuse `metrics/greenspace.py`'s `compute_subject_greenspace_row` and `ACCESSIBLE_FUNCTION_TYPES` — each comparator needs its own clipped OS Open Greenspace sites (already fetched together in one bbox by `fetch_greenspace_sites`, just needs clipping per-comparator) and its own population denominator (comparators already have `population_mid2021_estimate` rows in `population_denominators.csv`). District/national need the comparators' own areas summed or a South Oxfordshire/England-wide OS Open Greenspace clip — bigger live fetch, not yet attempted.
   - Once enough subject/comparator rows exist, **P3.7** (benchmarks: district/national rows for every metric) and **P3.8** (validation/reconciliation suite) become reachable.
1. **Housekeeping, not urgent:** the raw MCS zip files Tom committed to `main` (`data/MCS_*.zip`) are still sitting there — the phase branch has the properly organized/parsed version (`fetch/reference_data/mcs_installations/`); once the phase-end PR merges, delete the redundant zips from `main` as a small follow-up.
2. **Backlog, not yet scheduled:** comparator-level household/dwelling counts (repeat P1.6's method for the 8 comparators) and comparator ward weights (needed for P3.2) — the comparator LSOA-area-weight gap is closed.

## Blockers

- None currently — P2.7's MCS blocker was resolved 2026-09-30 (Q-011 answered and actioned, see ADR-0007).

## Open questions for the project lead

**How to answer one:** fill in the **Tom's answer** cell for that row (edit this file directly, or just reply in chat if a session is live — see development-plan.md §4.7). Leave **Status** as `open` — an agent sets it to `answered` → `actioned` itself; that's not something you need to manage. **The one exception:** if the row itself asks *you* to go and do something outside the repo (a GitHub setting, a real-world confirmation), the agent has no way to verify you've done it, so it'll set status to `awaiting confirmation` and needs you to say so before it can mark it `actioned`.

**Status values** — read this before deciding what to work on:
- `open` — no answer yet. Nothing for an agent to act on beyond, optionally, proceeding on its own stated working assumption.
- **`answered` — Tom has written an answer below and it has not been acted on yet. This is first-priority work, ahead of the normal task queue, at the start of the very next session (routine-fired or not) that sees it.**
- `awaiting confirmation` — an agent acted on the answer as far as it could, but the row asked Tom to do or confirm something outside the repo (see above); waiting on him to say it's done.
- `actioned` — fully resolved. Kept here briefly for visibility, then moved into *Answered / closed questions* below on the next doc audit.

| ID | Raised | Question | Tom's answer | Status | Blocks |
| --- | --- | --- | --- | --- | --- |
| Q-005 | 2026-09-27 | Who in the parish council reviews content (Phase 6) and signs off launch (Phase 7)? | | open | P6.5, Phase 7 exit (not yet reached) |
| Q-007 | 2026-09-28 | P1.2 verification: live ONS BFC parish polygon area for Cholsey is **~15.91 km²** vs spec §2's **16.52 km²** — a real ~3.7% difference. Which is authoritative for `config/geography.yaml`'s `area_km2`? (Working assumption: kept the spec's 16.52 km² unchanged for now; `test_boundaries.py` separately pins the live ~15.9 km² figure so neither drifts unnoticed.) | Use the ONS BFC as the authority | actioned | Phase 3 area-based % calculations |
| Q-011 | 2026-09-30 | P2.7 investigation (ADR-0007, plan risk R1): the MCS Data Dashboard has no self-service bulk/postcode download — only a chargeable, GDPR-limited data-request process. None of the pre-identified fallbacks cleanly matches spec §3's parish-level, "current" requirement for solar PV/heat pump uptake: DESNZ's national solar PV series is discontinued (2021); DESNZ's BUS heat-pump geographic breakdowns are one-off local-authority-level "ad hoc" releases (far coarser than parish, and not a refreshable series); Ofgem's FIT installation reports are PV-only, closed since 2019, and their download links weren't verified (JS-loaded, not investigated further). Which of ADR-0007's four options (accept LA-level BUS figures flagged as an estimate; pursue a paid/manual MCS data request; invest more time in Ofgem FIT specifically; or defer metrics 5/6 entirely) should P2.7 build against? | I have manually retrieved the data form the MCS data dashboard. I have made two commits to the main branch of these data, as zip files, to the data folder look at hte files added to each commit to tell the heat pump data from the solar data. You will need to unzip the data and file it away in to a folder appropriatly. You will need to investigate the data | actioned | P2.7, P3.5 |

## Answered / closed questions

<details>
<summary>Q-006, Q-008, Q-009 (all <code>actioned</code>, 2026-09-28)</summary>

| ID | Question | Tom's answer | Actioned as |
| --- | --- | --- | --- |
| Q-006 | GitHub Pages source, and where phase-end PRs should target. | "Updated pages to run from actions. I also believe that at the end of each phase, the PR should be made to 'main'." | **PR target changed to `main`**: development-plan.md §4.5, CLAUDE.md updated — phase-end PRs now base off `main`, not the designated branch (the designated branch is still where the session develops day-to-day and where phase branches fork from). **Pages source claim**: Tom was right all along — see Q-010 below for the full correction. |
| Q-008 | Ward vintage assumption for the canopy join. | "Consider the UKCEH's landcover map dataset, which may be more frequently updated." | **Fully actioned 2026-09-29 (P2.3, ADR-0006)**: evaluated UKCEH LCM for real — it classifies land into dominant habitat classes (not a canopy %), so it would undercount Cholsey's scattered/garden trees; kept Forest Research as metric 1's source, logged UKCEH as a documented stretch item. Also found and resolved the real vintage question: Forest Research's Cholsey record uses ward E05009737 (Dec 2018 edition), not E05011701 — verified geometrically near-identical (99.4% vs 100.0% parish-in-ward) so no correction needed, but the assumption is now verified, not just assumed. |
| Q-009 | Comparator selection — all 8, the original 4, or a curated subset? | "Use all 8." | `config/geography.yaml`'s 8 comparator entries had their `pending_confirmation` flag removed. ADR-0003 → Accepted. Tests updated to assert the flag is gone rather than present. |

</details>

<details>
<summary>Q-010 (<code>actioned</code>, 2026-09-29 — a false alarm, corrected)</summary>

| ID | Question | Tom's answer | Actioned as |
| --- | --- | --- | --- |
| Q-010 | An earlier session claimed the live Pages URL still served the legacy "Deploy from a branch" README even after `deploy.yml` ran successfully on the Phase 1 merge, and asked Tom to re-check Settings → Pages → Source. | "I check and pages is definitely set to GitHub actions, could something else be causing this issue?" | **Tom was right; this was a false alarm caused by a flawed check, not a real misconfiguration.** The earlier session judged the page "looks like a rendered README" using an AI-based page read (WebFetch) rather than inspecting the actual HTML — that read was wrong. Re-checked properly this time: fetched the raw HTML (`curl`) and compared it byte-for-byte against `web/src/pages/index.astro`'s source — an exact match (same `<title>`, heading, and dev-plan link, no GitHub markdown chrome anywhere). The `Last-Modified` response header (04:28 UTC, 2026-09-29) also matches recent activity on `main`, confirming it's the fresh Actions-based build, not stale content. The site is correctly being served via GitHub Actions and just looks minimal because it genuinely is still the Phase 0 placeholder skeleton — expected until Phase 4 wires in real content, not a bug. No code or settings change needed. |

</details>

<details>
<summary>Q-001 through Q-004 (all <code>actioned</code>, 2026-09-27)</summary>

| ID | Question | Tom's answer | Actioned as |
| --- | --- | --- | --- |
| Q-001 | Accept the proposed stack in ADR-0002? | Accept the stack, but change if there's good reason after experimentation. | ADR-0002 → Accepted, with that exact caveat written into its Status line. |
| Q-002 | Five headline tiles (§6) vs six core metrics (§3): how to reconcile? | Combine gas and electric. | One "Home energy" tile/page combining `electricity` + `gas`, giving exactly five tiles; they stay as two `metric_id`s in the data model. development-plan.md §3 Phase 3/4/6. |
| Q-003 | National benchmark: England or GB? | England. | England is the default; GB/UK only as a per-dataset fallback, labelled in provenance. |
| Q-004 | Default GitHub Pages URL, or a custom domain? | Default URL. | No custom domain planned for launch; target URL recorded under *Key links*. |

</details>

---

## Phase overview

| Phase | Name | State | Notes |
| --- | --- | --- | --- |
| 0 | Foundations & agent workflow | **done** (2026-09-28) | See *Completed phases* below |
| 1 | Boundaries & geographic scope | **done** (2026-09-29) | See *Completed phases* below |
| 2 | Data ingestion | **done** (2026-09-30) | See *Completed phases* below |
| 3 | Geographic join & metric table | **active** | See *Current phase tasks* below |
| 4 | Front-end skeleton | not-started | Can run in parallel with Phases 2–3 after Phase 0 |
| 5 | Data wiring & charts | not-started | |
| 6 | Narrative & opportunities content | not-started | |
| 7 | Polish, accessibility & launch | not-started | |
| 8 | Automated refresh & handover | not-started | |

## Current phase tasks — Phase 3: Geographic join & metric table

Goal, full detail and tests of success: [development-plan.md §3 Phase 3](development-plan.md#phase-3--geographic-join--metric-table). Working on `phase-3-metric-table` (forked from `main`).

| ID | Task | State | Notes |
| --- | --- | --- | --- |
| P3.1 | `metrics.csv` schema (pandera) | done | 2026-09-30. `validate/metrics_schema.py`: `METRICS_CSV_SCHEMA` (structural — enums, no-null provenance, flag/flag_note consistency, (area_code, metric_id, year) uniqueness) plus `validate_registry_references` (metric_id/area_code/source_id must be real config keys). 27 new tests (191 total), built against a real Cholsey electricity row. |
| P3.2 | Metric 1: tree canopy cover % | in-progress (`phase-3-metric-table`) | 2026-09-30. `metrics/canopy.py`'s `compute_subject_canopy_row` done — Cholsey's real row (10.4%, ward E05009737, `method=area_weighted`, always `flag=parish_estimate`; real finding: Cholsey's ward ~66 km² vs parish ~15.9 km², not coterminous, so never `method=direct`). Comparators (need each one's containing ward) and district/national (need a ward→LAD lookup and an England-wide ward aggregate) not yet built. 6 new tests (197 total). |
| P3.3 | Metric 2: accessible green space | in-progress (`phase-3-metric-table`) | 2026-09-30. ADR-0008 decides which OS Open Greenspace function types count as "accessible" (includes parks, playing fields, play space, sports facilities, tennis courts, bowling greens; excludes golf courses, allotments, religious grounds, cemeteries). `metrics/greenspace.py`'s `compute_subject_greenspace_row` done — Cholsey's real row (89,089.84 m² accessible, 20.23 m²/resident, 0.56% of parish area, `method=clip`, always `flag=partial_coverage`). Comparator/district/national rows not yet built. 10 new tests (207 total). |
| P3.4 | Metrics 3–4: domestic electricity and gas | **done** (`phase-3-metric-table`) | 2026-09-30. All 9 areas built and tested: subject (Cholsey, `compute_subject_energy_row`, `method=address_weighted`, real 2024 electricity 3,682.27 kWh/meter, gas 11,000.81 kWh/meter); 8 comparators (`compute_comparator_energy_row` for 7 of them using real LSOA area weights, `method=area_weighted`, always `flag=parish_estimate`; Moulsford via the address-weighted path with a real NSUL weight); district/national (`compute_area_energy_row`, South Oxfordshire/England direct from DESNZ's regional/LA release, `method=direct`, `flag=none`; England electricity 3,352.84 kWh/meter, South Oxfordshire gas 12,439.93 kWh/meter). Real bug found+fixed along the way: gas's regional/LA sheet has a different column layout than electricity's, never verified live before this phase — fixed in `fetch/desnz_lsoa_energy.py` with per-fuel header/column lookups. `geography/boundaries.py`'s new `bbox` param on `fetch_boundary` and the regenerated `weights.csv` (real LSOA area weights for all 9 parishes) built to support this, reusable by P3.2/P3.3. Postcode-level cross-check scoped out (P2.6's fetcher is OX10-outcode-wide, not parish-specific). 21 new tests this phase (228 total). |
| P3.5 | Metrics 5–6: solar PV and heat pump uptake | in-progress (`phase-3-metric-table`) | 2026-09-30. Subject + district rows done via `metrics/mcs.py` (real South Oxfordshire MCS data, Tom's manual retrieval, Q-011/ADR-0007): heat pump 2.73% of households (~48.6 estimated for Cholsey), solar PV 10.08% (~179.6 estimated). `method=address_weighted`/`flag=parish_estimate` for the subject row (district rate applied uniformly to the parish); `method=direct`/`flag=none` for the district row (South Oxfordshire IS the district). No installed-kWp figure available from this source. Comparator/national rows not yet built — need further manual MCS dashboard pulls. |
| P3.6 | *Stretch:* Metric 7, EPC band profile | todo | Needs P2.9's API key (not registered yet) |
| P3.7 | Benchmarks: district and national rows | todo | England is the default national level (Q-003) |
| P3.8 | Validation and reconciliation suite | todo | Ranges, YoY limits, completeness matrix, district/national reconciliation vs published figures |
| P3.9 | `export.py`: site JSON + `data/processed/README.md` | todo | |

## Completed phases

<details>
<summary><strong>Phase 2 — Data ingestion</strong> (done 2026-09-30)</summary>

Goal, full detail and tests of success: [development-plan.md §3 Phase 2](development-plan.md#phase-2--data-ingestion). Merged into `main` as [PR #2](https://github.com/tomaugust/cholsey-sustainability-dashboard/pull/2), after 2 Opus review cycles.

| ID | Task | Notes |
| --- | --- | --- |
| P2.1 | Source registry (`parser`, `download_url`/`download_urls`/`discovery_rule`) | Real, verified download URLs found for `desnz_lsoa_energy` and `os_open_greenspace`. `registry.py::load_sources` enforces the new schema. |
| P2.2 | Fetch framework (`fetch/http.py`) | Retries with backoff, sha256/manifest, real skip-via-304 conditional requests. Hardened in PR review: case-insensitive header lookups, URL-matched conditional headers, no manifest entry written for "unchanged" (idempotence), 4xx not retried, `extra_headers` support. |
| P2.3 | Fetcher: Forest Research UK Ward Canopy Cover | `fetch/forest_research_canopy.py`. UKCEH LCM evaluated and logged as a non-equivalent stretch item; real ward-vintage mismatch found and verified immaterial. ADR-0006, Q-008 fully resolved. Routed through `fetch_file` for provenance (PR review). |
| P2.4 | Fetcher: OS Open Greenspace | `fetch/os_open_greenspace.py`. Clips the GB-wide GeoPackage to a buffered bbox on ingest, read directly out of the zip. |
| P2.5 | Fetcher: DESNZ LSOA domestic electricity and gas, plus district/national totals | `fetch/desnz_lsoa_energy.py`. Real finding: district/national totals come from a separate GOV.UK publication than the LSOA one — new `desnz_regional_la_energy` source registered. Header-row validated before positional parsing (PR review). |
| P2.6 | Fetcher: DESNZ postcode-level electricity and gas | `fetch/desnz_postcode_energy.py`. Real finding: yearly postcode-level releases exist through 2024, contradicting P2.1's earlier "only found a 2020 release" conclusion. Filters to OX10; falls back to LSOA data with `flag=parish_estimate` for suppressed postcodes. |
| P2.7 | Fetcher: MCS installation data | **done** (2026-09-30, on `phase-3-metric-table` — Phase 2 itself stayed merged/closed at the time; this task's resolution landed during Phase 3 once Q-011 was answered). `fetch/mcs_installations.py` loads Tom's manually-retrieved MCS Data Dashboard reference data (no bulk API exists, confirmed — see ADR-0007, now Accepted). Originally blocked pending Q-011 (see history below); Tom answered by retrieving the data himself. |
| P2.8 | Fetcher: ONS population and dwellings | `fetch/ons_population_dwellings.py`. Real finding: a mid-2022 parish population vintage now exists (Cholsey: 4,423) alongside mid-2021 (4,404). Fetches Census 2021 OA-level population/household counts live from nomis. Parish-code column matched by pattern, not hardcoded to one vintage (PR review). |
| P2.9 | *Stretch:* EPC register fetcher | `fetch/dluhc_epc_register.py`. Feature-flagged (`EpcApiKeyMissing` raised loudly if no key). Real finding: the old `epc.opendatacommunities.org` API has moved to `get-energy-performance-data.communities.gov.uk`. Pagination bounded and routed through `fetch_file` for provenance (PR review, cycle 2). No API key registered yet. |
| P2.10 | Source contracts (schema + previous-run diff) | `cholsey_pipeline/contracts.py`: `SchemaContract`/`validate_schema`/`validate_row_count`, wired into every record-based fetcher's own function (not just tests, per PR review cycle 2). Row-count baselines are query-scoped (`query_signature`) and survive a failed run's manifest entry correctly. `numeric_fields` check added for suppressed-value detection. `os_open_greenspace` excluded (GeoDataFrame, different shape). |

Exit criteria (development-plan.md): fetchers for the five buildable core sources merged and live-verified once ✓. Contract tests in CI ✓ (P2.10). The MCS data-access ADR is recorded ✓ (ADR-0007, P2.7 blocked pending Q-011 — the plan's own anticipated outcome for that source). EPC explicitly deferred (feature-flagged, no key) ✓.

Two Opus review cycles (plan §4.5) found and fixed 12 real bugs across the two cycles (fresh-clone `FileNotFoundError` on "unchanged" fetches, contract validation never actually wired into any fetcher, postcode/fuel key-uniqueness collisions, positional-column drift risk, manifest source_id/registry mismatches, a hardcoded parish-vintage column name, non-retryable 4xx being retried, a retry-bypassable row-count guard, a query-blind row-count baseline, case-sensitive header lookups, an unbounded EPC pagination loop, and a broken idempotence guarantee introduced by cycle 1's own fix) plus several non-blocking "altitude and cleanup" findings, logged in *Backlog* below. See worklogs: [2026-09-30-b](worklog/2026-09-30-b-p2.10-phase2-pr.md), [2026-09-30-c](worklog/2026-09-30-c-phase2-pr-review-and-merge.md).

</details>

<details>
<summary><strong>Phase 1 — Boundaries &amp; geographic scope</strong> (done 2026-09-29)</summary>

Goal, full detail and tests of success: [development-plan.md §3 Phase 1](development-plan.md#phase-1--boundaries--geographic-scope). Merged into `main` as [PR #1](https://github.com/tomaugust/cholsey-sustainability-dashboard/pull/1) (also carried Phase 0, since it was the first PR ever to reach `main`), after 2 Opus review cycles.

| ID | Task | Notes |
| --- | --- | --- |
| P1.1 | Fetch ONS parish/LSOA/ward boundaries | `geography/boundaries.py`, 4 real ONS FeatureServer layers verified live |
| P1.2 | Verify spec's area codes against real ONS data | Parish/LSOA/ward codes all confirmed correct. One real discrepancy found (area, Q-007) and one open assumption (ward vintage, Q-008) |
| P1.3 | Comparator selection — confirm/replace the `PENDING-*` placeholders | `geography/comparators.py`. Found 8 real touching parishes vs spec's 5 candidates, 2 of which were wrong. ADR-0003 **Accepted**, Q-009 confirmed ("use all 8") |
| P1.4 | Complete LSOA→parish overlap (ONSUD, polygon intersection) | `geography/lsoa_overlap.py`. Found a THIRD LSOA (E01035752) overlapping Cholsey the spec didn't mention |
| P1.5 | Apportionment weights (`data/processed/geography/weights.csv`) | `geography/weights.py`. Real address-count weight from NSUL vs. area weight genuinely diverge for the split LSOA (0.583 vs 0.457) — see ADR-0004 |
| P1.6 | Parish population/dwelling denominators (2021 Census) | `geography/denominators.py`. Three independently-sourced Cholsey population figures (spec 4,498; ONS mid-2021 4,404; own Census-Day sum 4,390) all differ slightly — see ADR-0005 |
| P1.7 | Finalise `config/geography.yaml` + simplified GeoJSON for the site | No remaining `PENDING-*`/`pending_confirmation` placeholders. `data/processed/geography/parishes.geojson` (9 features, EPSG:4326) for the Phase 5 map/locator |

Exit criteria (development-plan.md): all automated tests in CI ✓ (62 pipeline tests passing). ADR-0003 accepted by the project lead ✓ (Q-009). Code discrepancies logged as open questions (Q-007; Q-010, since resolved as a false alarm) rather than silently resolved ✓.

Two Opus review cycles (plan §4.5) found and fixed 2 blocking issues (silent pagination truncation risk in `fetch_boundary`; missing provenance/bad timestamp in `weights.csv`) plus several medium findings; cycle 2 confirmed clean. Non-blocking follow-ups logged in *Backlog* below. See worklogs: [2026-09-28o](worklog/2026-09-28-o-p1.5-apportionment-weights.md), [2026-09-29a](worklog/2026-09-29-a-p1.6-p1.7-phase1-pr.md), [2026-09-29b](worklog/2026-09-29-b-pr1-review-cycle-1.md), [2026-09-29c](worklog/2026-09-29-c-pr1-merged-cutover.md).

</details>

<details>
<summary><strong>Phase 0 — Foundations &amp; agent workflow</strong> (done 2026-09-28)</summary>

All 7 tasks (P0.1-P0.7) done; P0.8 (optional SessionStart hook) deferred, not required by the phase's exit criteria. See the worklogs for detail: [2026-09-27](worklog/2026-09-27-planning-and-docs-setup.md), [2026-09-27b](worklog/2026-09-27-b-decisions-confirmed.md), [2026-09-27c](worklog/2026-09-27-c-routine-push-fix.md), [2026-09-28a](worklog/2026-09-28-a-p0.3-pipeline-skeleton.md), [2026-09-28b](worklog/2026-09-28-b-p0.4-config-files.md), [2026-09-28c](worklog/2026-09-28-c-p0.5-p0.6-web-and-makefile.md), [2026-09-28d](worklog/2026-09-28-d-p0.7-ci-and-pages.md).

Exit criteria (development-plan.md): P0.1-P0.7 merged ✓. ADR-0002 accepted ✓ (Q-001). Pages URL recorded ✓ — see *Key links* below.

**Correction (checked after the P0.7 push, via `actions_list` and a live fetch):** the earlier note here claiming Pages "needs a manual step before it's live" was wrong. **GitHub Pages is already enabled and already publicly live** at the URL below — but via the legacy "Deploy from a branch" source, auto-deploying on every push to `claude/new-session-7bcxu1` (not `main`, and not via our new `deploy.yml`). Right now it's serving a **rendered `README.md`**, not the Astro build — confirmed by fetching the live URL. `deploy.yml` (Actions-based) won't fire until there's a push to `main`, and even then it needs Settings → Pages → Source switched from "Deploy from a branch" to **"GitHub Actions"** to take over — that switch is a repo-admin action, logged as **Q-006** below for Tom to make (and to say when/whether he wants this branch merged to `main`).

| ID | Task |
| --- | --- |
| P0.1 | Agent documentation scaffolding |
| P0.2 | Confirm ADR-0002 (stack & layout) |
| P0.3 | `pipeline/` Python project skeleton |
| P0.4 | `config/` YAML files + loader + tests |
| P0.5 | `web/` Astro skeleton |
| P0.6 | `Makefile` |
| P0.7 | CI + GitHub Pages deploy workflows |
| P0.8 | SessionStart hook for cloud agents — **deferred**, optional, not needed for Phase 0 exit |

</details>

## Backlog / unscheduled

_(Discovered work that doesn't belong to a phase yet.)_

- **Comparator-level apportionment** (no ID yet — assign one when scheduled): P1.4 (OA→parish/LSOA membership), P1.5 (address-count + area weights) and P1.6's household/dwelling count were all scoped to Cholsey (and Moulsford, only because they share an LSOA) — see ADR-0004 and ADR-0005. The 8 comparator parishes have no equivalent LSOA/ward apportionment or household count yet (population is covered for all 9, via P1.6's direct ONS mid-2021 release). Needed before Phase 3 can benchmark LSOA-sourced metrics (electricity, gas) for comparators, not just Cholsey.
- **From the Phase 1 PR #1 Opus review (non-blocking, fixed findings noted in the PR/worklog instead):**
  - Parish GSS codes are joined across three different boundary/lookup editions without an explicit compatibility check (the OA→parish lookup uses 2024-vintage `PARNCP24CD`, the boundary layers and `geography.yaml` use 2023, the mid-2021 population release uses the 2022 parish edition). Parish codes are stable identifiers that rarely change, so this hasn't caused a real mismatch yet, but nothing would catch it if one ever did — a silent join failure, not an error. Worth a small cross-check (e.g. assert the code sets overlap as expected) before Phase 3 relies on these joins more heavily.
  - Boundary fetch manifests record a sha256/byte count of the merged response (fixed, this PR) but not the raw GeoJSON itself — so the hash proves *whether* a later refetch differs, not *what* changed. Saving the raw response under `data/interim/` (small enough per layer) would close that gap; not done here to avoid growing this PR further.
  - `config/geography.yaml`'s `population_mid2021_estimate` values were copied by hand from `data/processed/geography/population_denominators.csv`'s output (produced by `scripts/build_population_denominators_csv.py`) — there's no automated check that they stay in sync if the CSV is regenerated. Low risk while the source data is static, but worth a contract test in Phase 2/3 once `pandera` schemas are in play (P3.1).
  - Some OA→parish/OA→LSOA reference data is loaded independently in a few places (`test_denominators.py`'s own copy, plus the reference-data JSON used by the two build scripts) rather than from one shared loader — a fix to the underlying data wouldn't necessarily be caught by the test that has its own copy. Minor DRY cleanup, not urgent.
  - `web/astro.config.mjs` doesn't yet set Astro's `site`/`base` for the GitHub Pages subpath (`/cholsey-sustainability-dashboard/`) — fine while the site is just a placeholder skeleton, but needs doing before Phase 4 adds real internal links/assets that would otherwise 404 under that path. Also worth checking `deploy.yml` only deploys after a successful CI run, not unconditionally.
- **Housekeeping**: the merged phase branch `claude/new-session-7bcxu1-phase-1-remainder`, and the retired designated branch `claude/new-session-7bcxu1`, are still on GitHub (not deleted) — `git push origin --delete` returned a 403 (the git credential available to this session can push/merge but not delete a remote branch), and no GitHub MCP tool for branch deletion was available either. Harmless (both are fully merged into `main`), but someone with full repo access could delete them via the GitHub UI/CLI when convenient. **Same limitation hit again for Phase 2's `phase-2-data-ingestion`** (deleted locally, still on GitHub) — same 403, same fix (delete via the UI/CLI when convenient).
- **From the Phase 1 PR #1 Opus review, cycle 2 (non-blocking — cycle 2 confirmed both cycle-1 blocking findings are properly fixed, found no new blockers, recommended merge as-is):**
  - `fetch_boundary`'s pagination loop (fixed in cycle 1) can still stop one page early if a service caps a page below `page_size` **and** omits `exceededTransferLimit` — every current caller filters to a handful of codes, so this hasn't bitten anything yet, but the loop should really stop only on a genuinely empty page. Cheap follow-up.
  - `fetch_boundary`'s `if codes:` treats `codes=[]` the same as `codes=None` (fetches the whole layer) — should probably reject an empty list explicitly rather than silently fetching everything.
  - Pagination has no `orderByFields` and no dedup/stall guard — theoretical risk against the ONS Geoportal specifically, but worth hardening before this function is reused against a less well-behaved service.
  - The manifest's sha256 is computed over the merged/re-serialised GeoJSON, not the exact bytes ONS sent, and `request_url` only records the last page's URL — weaker provenance than it looks, though not wrong.
  - `data/processed/geography/parishes.geojson` itself carries no provenance metadata (source/vintage/retrieved_at) in a form the Phase 5 map can surface — needs adding before that page ships, not before this merge.
  - `compute_lsoa_area_weights`/`compute_parish_ward_weights` do an unindexed nested-loop intersection — fine at today's scale (9 parishes, 3 LSOAs, 1 ward), would need a spatial index if this ever runs against many more areas.
  - CI's `uv sync` doesn't pass `--locked`, so a stale `uv.lock` wouldn't be caught by CI. One-line fix.
  - **New, worth remembering for P2.3**: the ward-level canopy weight (1.0, Cholsey wholly inside its ward) is correct, but when Phase 2 (P2.3) actually applies the ward's canopy % to Cholsey, that figure must be flagged as a ward-level estimate applied to the parish (CLAUDE.md's "flag estimates" rule) — not implicitly presented as parish-specific.
- **From the Phase 2 PR #2 Opus review (2 cycles; all correctness findings fixed in the PR itself — see its commits and resolved review threads for detail; these are the "altitude and cleanup" findings explicitly left as follow-up rather than widening the PR further):**
  - `fetch.desnz_lsoa_energy` and `fetch.desnz_postcode_energy` each define their own near-identical `discover_download_url`/`ASSET_LINK_PATTERN`/`DesnzDiscoveryError` — copied, not shared, so a caller catching one `DesnzDiscoveryError` type would miss the other module's. A shared helper (parameterised by file extension) would remove the duplication.
  - Every record-based `fetch_*` function (desnz_lsoa_energy ×2, desnz_postcode_energy, ons_parish_population, dluhc_epc_register, forest_research_canopy) repeats the same `previous_row_count → fetch_file → file_path-is-None check → validate_schema → validate_row_count → record_row_count` sequence by hand. A shared `fetch_and_validate(source_id, url, contract, parse, query_signature)` wrapper would remove the repetition and give one place to fix a future row-count bug, rather than six. The `file_path is None` checks are also dead code (`fetch_file` always sets it on a normal return) and could be dropped once such a helper exists.
  - `contracts.SchemaContract`'s `numeric_fields` check (added in the PR) validates that a field is a real `int`/`float`, but doesn't validate other dtypes (strings that should match a pattern, enums, etc.) — P2.10's "columns, dtypes, key uniqueness" wording could be read as wanting a more general per-field type declaration than the numeric-only check implemented.

## Key links

- Spec: [technical-specification.md](technical-specification.md)
- Plan: [development-plan.md](development-plan.md)
- Decisions: [decisions/README.md](decisions/README.md)
- Pages URL (Q-004, default URL, no custom domain): `https://tomaugust.github.io/cholsey-sustainability-dashboard/` — live via the GitHub Actions Pages source, correctly serving the Astro build (currently the Phase 0 placeholder skeleton, real content lands in Phase 4). Confirmed 2026-09-29 by inspecting the raw HTML directly — see Q-010.
