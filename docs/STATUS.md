# Project Status

**Last updated:** 2026-09-28 by agent (direct session with Tom — answer/action-tracking protocol added). See [worklog](worklog/2026-09-28-f-answer-tracking-protocol.md).
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

**How to answer one:** fill in the **Tom's answer** cell for that row (edit this file directly, or just reply in chat if a session is live — see development-plan.md §4.7). Leave **Status** as `open` — an agent sets it to `answered` → `actioned` itself; that's not something you need to manage. **The one exception:** if the row itself asks *you* to go and do something outside the repo (a GitHub setting, a real-world confirmation), the agent has no way to verify you've done it, so it'll set status to `awaiting confirmation` and needs you to say so before it can mark it `actioned`.

**Status values** — read this before deciding what to work on:
- `open` — no answer yet. Nothing for an agent to act on beyond, optionally, proceeding on its own stated working assumption.
- **`answered` — Tom has written an answer below and it has not been acted on yet. This is first-priority work, ahead of the normal task queue, at the start of the very next session (routine-fired or not) that sees it.**
- `awaiting confirmation` — an agent acted on the answer as far as it could, but the row asked Tom to do or confirm something outside the repo (see above); waiting on him to say it's done.
- `actioned` — fully resolved. Kept here briefly for visibility, then moved into *Answered / closed questions* below on the next doc audit.

| ID | Raised | Question | Tom's answer | Status | Blocks |
| --- | --- | --- | --- | --- | --- |
| Q-005 | 2026-09-27 | Who in the parish council reviews content (Phase 6) and signs off launch (Phase 7)? | | open | P6.5, Phase 7 exit (not yet reached) |
| Q-006 | 2026-09-28 | GitHub Pages is already live at the target URL, but on the legacy "Deploy from a branch" source deploying from `claude/new-session-7bcxu1` (currently serving a rendered README, not the site) rather than our new Actions-based `deploy.yml`. Switch Settings → Pages → Source to "GitHub Actions" now (repo-admin action, no agent can do it), and/or merge this branch to `main`? | | open | Nothing blocked; the public URL just won't show the real site until resolved |
| Q-007 | 2026-09-28 | P1.2 verification: live ONS BFC parish polygon area for Cholsey is **~15.91 km²** vs spec §2's **16.52 km²** — a real ~3.7% difference. Which is authoritative for `config/geography.yaml`'s `area_km2`? (Working assumption: kept the spec's 16.52 km² unchanged for now; `test_boundaries.py` separately pins the live ~15.9 km² figure so neither drifts unnoticed.) | | open | Phase 3 area-based % calculations (not yet reached) |
| Q-008 | 2026-09-28 | Forest Research canopy dataset (spec §4) is ward-level, "2020 imagery" only — no named ONS ward edition. Used "Wards (December 2020) Boundaries UK BFC" as a working assumption (Cholsey ward E05011701 confirmed present in it) — worth a check against Forest Research's own metadata. | | open | P2.3 (not yet reached) |

## Answered / closed questions

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
