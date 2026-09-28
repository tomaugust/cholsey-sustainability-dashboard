# Project Status

**Last updated:** 2026-09-28 by agent (scheduled routine run). See [worklog](worklog/2026-09-28-d-p0.7-ci-and-pages.md).
**Current phase:** Phase 1: Boundaries & geographic scope (`active`) — Phase 0 is `done`
**Current focus:** Start Phase 1 (P1.1: fetch ONS parish/LSOA/ward boundaries). Note the comparator parishes in `config/geography.yaml` are unconfirmed placeholders that P1.3 must resolve — see below.

> How to maintain this file: see [development-plan.md §4](development-plan.md#4-agent-working-protocol--documentation-strategy). It holds the **present** only. Overwrite it; don't append history. Update it at the end of every session.
> Task states: `todo` · `in-progress` (branch) · `review` (PR) · `blocked` (reason) · `done` · `deferred` (reason)

---

## Next steps (ordered, and the first one is actionable by a cold-start agent)

1. **P1.1**: fetch the ONS parish boundaries (Parishes Dec 2023 BFC for area/clip, BGC for display), LSOA 2021 boundaries, and ward boundaries of the vintage used by the canopy dataset (confirm that vintage as part of this task). This is real geo work — add `geopandas`/`pyogrio` fetch code under `pipeline/src/cholsey_pipeline/geography/`, with offline test fixtures (a trimmed extract), per development-plan.md §5.3.
2. **P1.2**: verify the codes already in `config/geography.yaml` (parish E04012474, ward E05011701, LSOAs E01035751/E01028619, MSOA E02005972, district E07000179) against the real ONS boundary data fetched in P1.1. Record any discrepancy as a new Q-NNN — do not silently "fix" a mismatch.
3. **P1.3**: comparator selection — compute which parishes' polygons actually touch Cholsey, compare against the five `PENDING-*` placeholders already in `config/geography.yaml` (Wallingford, Moulsford, South Stoke, Brightwell-cum-Sotwell, Aston Tirrold & Aston Upthorpe), and replace each placeholder with its real GSS code (or drop/swap a candidate that doesn't actually touch). Record the final list as an ADR for the project lead to confirm.
4. **P1.4-P1.7**: LSOA→parish overlap, apportionment weights (`data/processed/geography/weights.csv`), parish population/dwelling denominators, and finalising `config/geography.yaml` — see development-plan.md §3 Phase 1 for full detail and the automated tests each work package needs (polygon area, weight-sum-to-1, UPRN reconciliation, etc.).
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

Q-005 and Q-006 remain open. Neither blocks Phase 0–5 code work; Q-006 only affects what the public URL currently shows.

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
| P1.1 | Fetch ONS parish/LSOA/ward boundaries | todo | See Next steps #1 |
| P1.2 | Verify spec's area codes against real ONS data | todo | |
| P1.3 | Comparator selection — confirm/replace the `PENDING-*` placeholders | todo | Needs an ADR + project-lead confirmation |
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
