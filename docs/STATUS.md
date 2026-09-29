# Project Status

**Last updated:** 2026-09-29 by agent (Tom pushed back on Q-010 — correctly. Re-checked properly and closed it as a false alarm from a flawed earlier check, not a real Pages issue). See [worklog](worklog/2026-09-29-f-q010-false-alarm-corrected.md).
**Current phase:** Phase 2: Data ingestion (`active`) — Phase 0 and Phase 1 are `done`
**Current focus:** Phase 2 branch `phase-2-data-ingestion` has P2.1, P2.2 and P2.3 done. P2.3 fully resolved Q-008 (evaluated UKCEH's Land Cover Map for real — not a canopy-% substitute, kept as a documented stretch item — and found/verified a real ward-code mismatch in Forest Research's Cholsey record, immaterial after checking the actual geometry). `fetch/forest_research_canopy.py` fetches live, tested against real fixture data. Next: P2.4 (OS Open Greenspace, `download_url` already verified) onward. Q-010 is now closed (was a false alarm, see below) — Q-005 and Q-007 remain open.

> How to maintain this file: see [development-plan.md §4](development-plan.md#4-agent-working-protocol--documentation-strategy). It holds the **present** only. Overwrite it; don't append history. Update it at the end of every session.
> Task states: `todo` · `in-progress` (branch) · `review` (PR) · `blocked` (reason) · `done` · `deferred` (reason)

---

## Next steps (ordered, and the first one is actionable by a cold-start agent)

0. **Continue Phase 2 on `phase-2-data-ingestion`** (P2.1, P2.2, P2.3 done and pushed). Next work package: **P2.4**, OS Open Greenspace — `download_url` already verified real in P2.1, ready to fetch with `fetch.http.fetch_file`.
1. After P2.4: **P2.5** (DESNZ LSOA electricity/gas — `download_urls` already verified real), then P2.6-P2.10 (see development-plan.md §3 Phase 2 for exact scope; P2.6 postcode data and P2.7 MCS both need real investigation first, don't guess a URL).
2. **Not blocking Phase 2, but noted:** `config/sources.yaml`'s MCS licence field is marked "TBD" pending the P2.7 access investigation — not an immediate problem, just don't be surprised by it.
3. **Backlog, not yet scheduled:** comparator-level LSOA/ward apportionment and household/dwelling counts (repeat P1.4/P1.5/P1.6's method for the 8 comparators) — logged below, needed before Phase 3 can benchmark LSOA-sourced metrics for comparators, not just Cholsey.
4. ~~Q-010 needs Tom's attention~~ — resolved 2026-09-29: it was a false alarm from a flawed page-read check, not a real Pages misconfiguration. Nothing to do here.

## Blockers

None.

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
| Q-007 | 2026-09-28 | P1.2 verification: live ONS BFC parish polygon area for Cholsey is **~15.91 km²** vs spec §2's **16.52 km²** — a real ~3.7% difference. Which is authoritative for `config/geography.yaml`'s `area_km2`? (Working assumption: kept the spec's 16.52 km² unchanged for now; `test_boundaries.py` separately pins the live ~15.9 km² figure so neither drifts unnoticed.) | | open | Phase 3 area-based % calculations (not yet reached) |

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
| 2 | Data ingestion | **active** | Can run in parallel with Phase 4. See *Current phase tasks* below |
| 3 | Geographic join & metric table | not-started | |
| 4 | Front-end skeleton | not-started | Can run in parallel with Phases 2–3 after Phase 0 |
| 5 | Data wiring & charts | not-started | |
| 6 | Narrative & opportunities content | not-started | |
| 7 | Polish, accessibility & launch | not-started | |
| 8 | Automated refresh & handover | not-started | |

## Current phase tasks — Phase 2: Data ingestion

Goal, full detail and tests of success: [development-plan.md §3 Phase 2](development-plan.md#phase-2--data-ingestion). Working on `phase-2-data-ingestion` (forked from `main`).

| ID | Task | State | Notes |
| --- | --- | --- | --- |
| P2.1 | Source registry (`parser`, `download_url`/`download_urls`/`discovery_rule`) | done | 2026-09-29. Real, verified download URLs found for `desnz_lsoa_energy` (electricity + gas .xlsx) and `os_open_greenspace` (OS Data Hub GeoPackage, confirmed by actually downloading it). `registry.py::load_sources` enforces the new schema, 68 pipeline tests passing. |
| P2.2 | Fetch framework (`fetch/http.py`) | done | 2026-09-29. Retries with backoff, sha256/manifest, real skip-via-304 conditional requests (not just re-fetch-and-compare). 10 new tests, fully offline, 78 total passing. |
| P2.3 | Fetcher: Forest Research UK Ward Canopy Cover | done | 2026-09-29. `fetch/forest_research_canopy.py`, 4 new tests (82 total). UKCEH LCM evaluated and logged as a non-equivalent stretch item; real ward-vintage mismatch found and verified immaterial. ADR-0006, Q-008 fully resolved. |
| P2.4 | Fetcher: OS Open Greenspace | todo | `download_url` already verified (P2.1) |
| P2.5 | Fetcher: DESNZ LSOA domestic electricity and gas | todo | `download_urls` already verified (P2.1) |
| P2.6 | Fetcher: DESNZ postcode-level electricity and gas | todo | P2.1 found only a 2020 release with no direct file link on a plain fetch — needs real investigation |
| P2.7 | Fetcher: MCS installation data | todo | Investigate access first, record an ADR (plan risk R1) |
| P2.8 | Fetcher: ONS population and dwellings | todo | Largely superseded for population by P1.6/ADR-0005; check what's left |
| P2.9 | *Stretch:* EPC register fetcher | todo | Needs API key, feature-flagged |
| P2.10 | Source contracts (schema + previous-run diff) | todo | |

## Completed phases

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
- **Housekeeping**: the merged phase branch `claude/new-session-7bcxu1-phase-1-remainder`, and the retired designated branch `claude/new-session-7bcxu1`, are still on GitHub (not deleted) — `git push origin --delete` returned a 403 (the git credential available to this session can push/merge but not delete a remote branch), and no GitHub MCP tool for branch deletion was available either. Harmless (both are fully merged into `main`), but someone with full repo access could delete them via the GitHub UI/CLI when convenient.
- **From the Phase 1 PR #1 Opus review, cycle 2 (non-blocking — cycle 2 confirmed both cycle-1 blocking findings are properly fixed, found no new blockers, recommended merge as-is):**
  - `fetch_boundary`'s pagination loop (fixed in cycle 1) can still stop one page early if a service caps a page below `page_size` **and** omits `exceededTransferLimit` — every current caller filters to a handful of codes, so this hasn't bitten anything yet, but the loop should really stop only on a genuinely empty page. Cheap follow-up.
  - `fetch_boundary`'s `if codes:` treats `codes=[]` the same as `codes=None` (fetches the whole layer) — should probably reject an empty list explicitly rather than silently fetching everything.
  - Pagination has no `orderByFields` and no dedup/stall guard — theoretical risk against the ONS Geoportal specifically, but worth hardening before this function is reused against a less well-behaved service.
  - The manifest's sha256 is computed over the merged/re-serialised GeoJSON, not the exact bytes ONS sent, and `request_url` only records the last page's URL — weaker provenance than it looks, though not wrong.
  - `data/processed/geography/parishes.geojson` itself carries no provenance metadata (source/vintage/retrieved_at) in a form the Phase 5 map can surface — needs adding before that page ships, not before this merge.
  - `compute_lsoa_area_weights`/`compute_parish_ward_weights` do an unindexed nested-loop intersection — fine at today's scale (9 parishes, 3 LSOAs, 1 ward), would need a spatial index if this ever runs against many more areas.
  - CI's `uv sync` doesn't pass `--locked`, so a stale `uv.lock` wouldn't be caught by CI. One-line fix.
  - **New, worth remembering for P2.3**: the ward-level canopy weight (1.0, Cholsey wholly inside its ward) is correct, but when Phase 2 (P2.3) actually applies the ward's canopy % to Cholsey, that figure must be flagged as a ward-level estimate applied to the parish (CLAUDE.md's "flag estimates" rule) — not implicitly presented as parish-specific.

## Key links

- Spec: [technical-specification.md](technical-specification.md)
- Plan: [development-plan.md](development-plan.md)
- Decisions: [decisions/README.md](decisions/README.md)
- Pages URL (Q-004, default URL, no custom domain): `https://tomaugust.github.io/cholsey-sustainability-dashboard/` — live via the GitHub Actions Pages source, correctly serving the Astro build (currently the Phase 0 placeholder skeleton, real content lands in Phase 4). Confirmed 2026-09-29 by inspecting the raw HTML directly — see Q-010.
