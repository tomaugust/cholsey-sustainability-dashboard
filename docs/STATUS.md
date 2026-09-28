# Project Status

**Last updated:** 2026-09-28 by agent (direct session with Tom — PR + Opus-review workflow added). See [worklog](worklog/2026-09-28-i-pr-review-workflow.md).
**Current phase:** Phase 1: Boundaries & geographic scope (`active`) — Phase 0 is `done`
**Current focus:** **Process change, effective now: `P<phase>.<n>` work goes through a PR with an Opus review before merge — see plan §4.5, CLAUDE.md.** Next project task is still P1.5 (apportionment weights), but done via the new PR workflow. Q-009 (comparator set) still awaiting Tom.

> How to maintain this file: see [development-plan.md §4](development-plan.md#4-agent-working-protocol--documentation-strategy). It holds the **present** only. Overwrite it; don't append history. Update it at the end of every session.
> Task states: `todo` · `in-progress` (branch) · `review` (PR) · `blocked` (reason) · `done` · `deferred` (reason)

---

## Next steps (ordered, and the first one is actionable by a cold-start agent)

0. **Before P1.5 (or any `P<phase>.<n>` task) from here on: use the new PR workflow, not a direct push to the designated branch.** Branch → work → push → PR into the designated branch → wait for real CI → spawn an Opus review (`code-review` skill via an `Agent` call with `model: "opus"`, `medium` effort, `--comment`) → fix blocking findings (max 2 review cycles) → merge it yourself once clean. Full detail: development-plan.md §4.5, `CLAUDE.md`. This does not apply to documentation-only commits (like this one).
1. **P1.5**: apportionment weights (`data/processed/geography/weights.csv`) — the real address-count weight from ONSUD (UPRN-level), for each (parish, LSOA) pair now confirmed by P1.4 (`E01035751`, `E01028619` wholly in Cholsey; `E01035752` split ~60/40 with Moulsford — but P1.5 must compute the real UPRN-based figure, not just carry over P1.4's coarser `oa_count_share`). Also compute the (parish, ward) area weight for the canopy dataset. `pipeline/src/cholsey_pipeline/geography/lsoa_overlap.py`'s OA-level lookups from P1.4 narrow down which LSOAs/OAs to pull UPRNs for, so this doesn't need the full ~40M-row national ONSUD file — check whether the ONS Geoportal exposes a queryable UPRN-level table the way the OA lookups turned out to (P1.1/P1.4's worklog entries show the pattern: search the Geoportal API first, don't assume a bulk-download-only file is the only option). development-plan.md §3 Phase 1 has the exact test requirements (weights sum to 1.0 ± 0.001, etc.).
2. **P1.6-P1.7**: parish population/dwelling denominators (2021 Census) for Cholsey **and each of the 8 candidate comparators** (`config/geography.yaml`), and finalising the file once Q-009 lands + simplified GeoJSON for the site.
3. **Not blocking Phase 1, but noted:** `config/sources.yaml`'s MCS licence field is marked "TBD" pending the P2.7 access investigation (Phase 2) — not this phase's problem, just don't be surprised by it.

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
| Q-009 | 2026-09-28 | **P1.3 comparator selection — see [ADR-0003](decisions/0003-comparator-parish-selection.md).** Computed against real ONS data: **8 parishes** genuinely touch Cholsey, not the spec's 5 named candidates. Two real errors found in the spec's list: (1) "South Stoke" is ambiguous — two different parishes share that name, only one touches Cholsey (now correctly selected); (2) "Aston Tirrold & Aston Upthorpe" is two separate parishes and only Aston Tirrold touches — Aston Upthorpe doesn't. Three more real neighbours weren't in the spec's list at all: Aldworth, Crowmarsh, South Moreton. **Which final comparator set do you want** — all 8 (the ADR's recommendation, most defensible but more than the spec's UX sections assumed), the original 4 confirmed-correct ones only, or a curated subset? `config/geography.yaml` currently has all 8, each flagged `pending_confirmation: true`. | | open | Phase 3 (comparator joins), Phase 5 (comparison charts) — not yet reached, so nothing is stalled today |

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
| P1.3 | Comparator selection — confirm/replace the `PENDING-*` placeholders | done | 2026-09-28. `geography/comparators.py`, 6 new tests (39 total). Found 8 real touching parishes vs spec's 5 candidates, 2 of which were wrong. ADR-0003 (Proposed) + Q-009 awaiting Tom's confirmation. |
| P1.4 | Complete LSOA→parish overlap (ONSUD, polygon intersection) | done | 2026-09-28. `geography/lsoa_overlap.py`, 5 new tests (44 total). Found a THIRD LSOA (E01035752) overlapping Cholsey the spec didn't mention — not a discrepancy needing a Q, exactly what this task was for. |
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
