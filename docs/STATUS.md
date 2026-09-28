# Project Status

**Last updated:** 2026-09-28 by agent (scheduled routine run). See [worklog](worklog/2026-09-28-e-p1.1-p1.2-boundaries.md).
**Current phase:** Phase 1: Boundaries & geographic scope (`active`) — Phase 0 is `done`
**Current focus:** P1.1 and P1.2 done. Next: P1.3 (comparator selection by real polygon adjacency — do not match by name; the live ONS data has two different parishes both named "South Stoke"). Comparator parishes in `config/geography.yaml` are still unconfirmed placeholders until P1.3 lands.

> How to maintain this file: see [development-plan.md §4](development-plan.md#4-agent-working-protocol--documentation-strategy). It holds the **present** only. Overwrite it; don't append history. Update it at the end of every session.
> Task states: `todo` · `in-progress` (branch) · `review` (PR) · `blocked` (reason) · `done` · `deferred` (reason)

---

## Next steps (ordered, and the first one is actionable by a cold-start agent)

1. **P1.3**: comparator selection. `pipeline/src/cholsey_pipeline/geography/boundaries.py::fetch_boundary("parish_bfc")` can now pull real parish polygons live. Fetch Cholsey's polygon plus a reasonable surrounding set (e.g. all parishes in South Oxfordshire district, or a bounding-box query around Cholsey), compute which ones actually **touch** Cholsey's polygon (`geopandas`' `.touches()`/`.intersects()` on shared boundary, not just proximity), and compare against the five `PENDING-*` placeholders in `config/geography.yaml` (Wallingford, Moulsford, South Stoke, Brightwell-cum-Sotwell, Aston Tirrold & Aston Upthorpe). **Do not select "South Stoke" by name alone** — there are two different parishes with that name in the live data (E04008163 and E04009876); use adjacency to pick the right one, or coordinates/district to disambiguate. Replace each placeholder with its real GSS code (or drop/swap a candidate that doesn't actually touch). Record the final list as an ADR (Proposed) for the project lead to confirm — this is exactly the kind of comparator/scope decision CLAUDE.md says not to decide unilaterally.
2. **P1.4**: complete the LSOA→parish overlap using ONSUD (UPRN→LSOA/parish) and polygon intersection — don't assume the two LSOAs already in `config/geography.yaml` are the complete picture; derive membership properly.
3. **P1.5**: apportionment weights (`data/processed/geography/weights.csv`) — address-count weights from ONSUD plus an area-weight cross-check, per development-plan.md §3 Phase 1's exact test requirements (weights sum to 1.0 ± 0.001, etc.).
4. **P1.6-P1.7**: parish population/dwelling denominators (2021 Census) and finalising `config/geography.yaml` (replacing the `PENDING-*` entries for real once P1.3 lands) + simplified GeoJSON for the site.
5. **Not blocking Phase 1, but noted:** `config/sources.yaml`'s MCS licence field is marked "TBD" pending the P2.7 access investigation (Phase 2) — not this phase's problem, just don't be surprised by it.

## Blockers

None.

## Open questions for the project lead

| ID | Raised | Question | Resolution | Blocks |
| --- | --- | --- | --- | --- |
| Q-001 | 2026-09-27 | Accept the proposed stack in ADR-0002? | **Resolved 2026-09-27: accepted.** Agents may deviate with good reason found through experimentation, but must record it as a superseding ADR first. | — |
| Q-002 | 2026-09-27 | Five headline tiles (§6) vs six core metrics (§3): how to reconcile? | **Resolved 2026-09-27: combine electricity and gas into one "Home energy" tile/page.** Gives exactly five tiles. They stay as two `metric_id`s in the data model. See development-plan.md §3 Phase 3/4/6. | — |
| Q-003 | 2026-09-27 | National benchmark: England or GB? | **Resolved 2026-09-27: England by default**, falling back to GB/UK per dataset only where no England figure exists, labelled in provenance. | — |
| Q-004 | 2026-09-27 | Default GitHub Pages URL, or a custom domain? | **Resolved 2026-09-27: default Pages URL.** No custom domain planned for launch. | — |
| Q-005 | 2026-09-27 | Who in the parish council reviews content (Phase 6) and signs off launch (Phase 7)? | **TBD** — project lead to confirm before P6.5 / Phase 7 exit. | P6.5, Phase 7 exit (not yet reached) |
| Q-006 | 2026-09-28 | GitHub Pages is already live at the target URL, but on the legacy "Deploy from a branch" source deploying from `claude/new-session-7bcxu1` (currently serving a rendered README, not the site) rather than our new Actions-based `deploy.yml`. Switch Settings → Pages → Source to "GitHub Actions" now (repo-admin action, no agent can do it), and/or merge this branch to `main`? Until one of those happens, the public URL keeps serving the README on every push to this branch. | **No assumption made — awaiting Tom.** Not harmful (public content is just the README, no secrets), but worth a deliberate decision rather than agents merging their own branch to `main` unasked. | Nothing blocked; the public URL just won't show the real site until resolved |
| Q-007 | 2026-09-28 | P1.2 verification (per CLAUDE.md/plan: "record any discrepancy, do not silently fix"): the live ONS BFC parish polygon area for Cholsey is **~15.91 km²**, but spec §2 states **16.52 km²** — a real ~3.7% difference, not a rounding artefact. All GSS codes checked (parish, ward, both LSOAs) matched the spec exactly; only this area figure differs. Which is authoritative — should `config/geography.yaml`'s `area_km2` field (and anything derived from it, e.g. green-space % of parish area) use the live ONS BFC polygon figure, or does 16.52 km² come from an ONS "Standard Area Measurements" publication (a different, official ONS methodology that can legitimately differ from raw polygon geometry) that should be fetched and used instead? | **Assumption for now: geography.yaml keeps the spec's 16.52 km² figure unchanged**, and `test_boundaries.py` separately pins the live ONS BFC figure (~15.9 km²) so neither number drifts unnoticed. Nothing depends on resolving this yet (P1.5's area-weighting uses relative area shares, not the absolute figure) — but Phase 3's canopy/greenspace % calculations will, so resolve before Phase 3. | Phase 3 area-based % calculations (not yet reached) |
| Q-008 | 2026-09-28 | P1.1: the Forest Research canopy dataset (spec §4) is ward-level, described only as "2020 imagery" — it doesn't name a specific ONS ward boundary edition. "Wards (December 2020) Boundaries UK BFC" was used as a working assumption (the closest-dated ONS ward vintage), and Cholsey ward E05011701 was confirmed present in it — but this hasn't been checked against Forest Research's own dataset documentation/metadata, which may state the exact boundary vintage it was built on. | **Assumption: December 2020 wards**, recorded in `pipeline/.../geography/boundaries.py`'s `LAYERS["ward_bfc"]` and `config/sources.yaml`. Low risk either way — ward boundaries rarely change year to year, so an off-by-one-vintage mismatch is unlikely to matter much, but worth a five-minute check when the canopy fetcher itself is built (Phase 2, P2.3). | P2.3 (not yet reached) |

Q-005 through Q-008 remain open. None blocks the Phase 1 work immediately ahead (P1.3-P1.7); Q-006 only affects the public URL's content, Q-007/Q-008 matter before Phase 3's area calculations and P2.3 respectively.

---

## Phase overview

| Phase | Name | State | Notes |
| --- | --- | --- | --- |
| 0 | Foundations & agent workflow | **done** (2026-09-28) | See *Completed phases* below |
| 1 | Boundaries & geographic scope | **active** | |
| 2 | Data ingestion | not-started | Can run in parallel with Phase 4 after Phase 0 |
| 3 | Geographic join & metric table | not-started | |
| 4 | Front-end skeleton | not-started | Can run in parallel with Phases 2–3 after Phase 0 |
| 5 | Data wiring & charts | not-started | |
| 6 | Narrative & opportunities content | not-started | |
| 7 | Polish, accessibility & launch | not-started | |
| 8 | Automated refresh & handover | not-started | |

## Current phase tasks — Phase 1: Boundaries & geographic scope

Goal, full detail and tests of success: [development-plan.md §3 Phase 1](development-plan.md#phase-1--boundaries--geographic-scope).

| ID | Task | State | Notes |
| --- | --- | --- | --- |
| P1.1 | Fetch ONS parish/LSOA/ward boundaries | done | 2026-09-28. `geography/boundaries.py`, 4 real ONS FeatureServer layers verified live, 10 new tests (32 total passing) |
| P1.2 | Verify spec's area codes against real ONS data | done | 2026-09-28. Parish/LSOA/ward codes all confirmed correct. One real discrepancy found (area, Q-007) and one open assumption (ward vintage, Q-008) |
| P1.3 | Comparator selection — confirm/replace the `PENDING-*` placeholders | todo | See Next steps #1. Real fetcher is ready to use. |
| P1.4 | Complete LSOA→parish overlap (ONSUD, polygon intersection) | todo | |
| P1.5 | Apportionment weights (`data/processed/geography/weights.csv`) | todo | |
| P1.6 | Parish population/dwelling denominators (2021 Census) | todo | |
| P1.7 | Finalise `config/geography.yaml` + simplified GeoJSON for the site | todo | |

## Completed phases

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

- None.

## Key links

- Spec: [technical-specification.md](technical-specification.md)
- Plan: [development-plan.md](development-plan.md)
- Decisions: [decisions/README.md](decisions/README.md)
- Pages URL (Q-004, default URL, no custom domain): `https://tomaugust.github.io/cholsey-sustainability-dashboard/` — **already live**, but currently serving a rendered README (legacy branch-deploy source, deploying from this feature branch) rather than the Astro build. See *Completed phases → Phase 0* above and **Q-006** below.
