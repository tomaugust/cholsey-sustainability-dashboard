# Project Status

**Last updated:** 2026-09-28 by agent (scheduled routine run). See [worklog](worklog/2026-09-28-a-p0.3-pipeline-skeleton.md).
**Current phase:** Phase 0: Foundations & agent workflow (`active`)
**Current focus:** P0.3 done. Next: P0.4 (`config/` YAML skeletons + loader tests against real files), then P0.5/P0.6 (web skeleton, Makefile), then P0.7 (CI).

> How to maintain this file: see [development-plan.md §4](development-plan.md#4-agent-working-protocol--documentation-strategy). It holds the **present** only. Overwrite it; don't append history. Update it at the end of every session.
> Task states: `todo` · `in-progress` (branch) · `review` (PR) · `blocked` (reason) · `done` · `deferred` (reason)

---

## Next steps (ordered, and the first one is actionable by a cold-start agent)

1. **P0.4**: `config/` YAML skeletons (`sources.yaml`, `geography.yaml`, `metrics.yaml`) plus a test that loads the *real* files through `pipeline/src/cholsey_pipeline/registry.py`'s `load_metrics`/`load_geography`/`load_sources` (the loader and its unit tests against fixtures already exist from P0.3 — this task is the real config content plus one integration test per loader, including at least one negative case). `metrics.yaml` needs 6 metric IDs (canopy, greenspace, electricity, gas, solar_pv, heat_pump [+ EPC as a flagged stretch]); electricity and gas share a UI grouping key (`tile_group: home_energy`) so the front end renders them as one tile/page (Q-002 resolution).
2. **P0.5 / P0.6**: Astro skeleton in `web/`, and the `Makefile` (`setup`, `test`, `lint`, `refresh`, `site` — `refresh`/`site` can be stubs until Phase 2/4 land real work).
3. **P0.7**: CI (`ci.yml`, running `uv run pytest`/`ruff` in `pipeline/` and `npm test`/lint in `web/` once P0.5 exists) and Pages deploy (`deploy.yml`) to the default `github.io` URL (Q-004). Then update the *Commands* section of `CLAUDE.md` to match reality.

## Blockers

None.

**Resolved infrastructure issue (2026-09-27):** the first automated 5-hourly run's fresh-session-per-fire trigger couldn't push or self-manage (no repo access, no Claude_Code_Remote tools in that session type). The recurring job was rebuilt bound to a persistent session with full access; see [2026-09-27-c-routine-push-fix.md](worklog/2026-09-27-c-routine-push-fix.md). The 2026-09-28 run (this one) confirms the fix worked: it read STATUS.md, did P0.3, and pushed successfully.

## Open questions for the project lead

| ID | Raised | Question | Resolution | Blocks |
| --- | --- | --- | --- | --- |
| Q-001 | 2026-09-27 | Accept the proposed stack in ADR-0002? | **Resolved 2026-09-27: accepted.** Agents may deviate with good reason found through experimentation, but must record it as a superseding ADR first. | — |
| Q-002 | 2026-09-27 | Five headline tiles (§6) vs six core metrics (§3): how to reconcile? | **Resolved 2026-09-27: combine electricity and gas into one "Home energy" tile/page.** Gives exactly five tiles. They stay as two `metric_id`s in the data model. See development-plan.md §3 Phase 3/4/6. | — |
| Q-003 | 2026-09-27 | National benchmark: England or GB? | **Resolved 2026-09-27: England by default**, falling back to GB/UK per dataset only where no England figure exists, labelled in provenance. | — |
| Q-004 | 2026-09-27 | Default GitHub Pages URL, or a custom domain? | **Resolved 2026-09-27: default Pages URL.** No custom domain planned for launch. | — |
| Q-005 | 2026-09-27 | Who in the parish council reviews content (Phase 6) and signs off launch (Phase 7)? | **TBD** — project lead to confirm before P6.5 / Phase 7 exit. | P6.5, Phase 7 exit (not yet reached) |

Only Q-005 remains open, and it doesn't block any Phase 0–5 work.

---

## Phase overview

| Phase | Name | State | Notes |
| --- | --- | --- | --- |
| 0 | Foundations & agent workflow | **active** | P0.1 done |
| 1 | Boundaries & geographic scope | not-started | |
| 2 | Data ingestion | not-started | Can run in parallel with Phase 4 after Phase 0 |
| 3 | Geographic join & metric table | not-started | |
| 4 | Front-end skeleton | not-started | Can run in parallel with Phases 2–3 after Phase 0 |
| 5 | Data wiring & charts | not-started | |
| 6 | Narrative & opportunities content | not-started | |
| 7 | Polish, accessibility & launch | not-started | |
| 8 | Automated refresh & handover | not-started | |

## Current phase tasks — Phase 0

| ID | Task | State | Notes |
| --- | --- | --- | --- |
| P0.1 | Agent documentation scaffolding (CLAUDE.md, STATUS, ADRs, worklog, PR template) | done | 2026-09-27, branch `claude/new-session-7bcxu1` |
| P0.2 | Confirm ADR-0002 (stack & layout) | done | Accepted by project lead 2026-09-27 (Q-001) |
| P0.3 | `pipeline/` Python project skeleton | done | 2026-09-28, `uv`/ruff/pytest set up, `registry.py` loader + 10 unit tests passing |
| P0.4 | `config/` YAML skeletons + loader + tests | todo | |
| P0.5 | `web/` Astro skeleton | todo | |
| P0.6 | `Makefile` | todo | |
| P0.7 | CI + GitHub Pages deploy workflows | todo | |
| P0.8 | SessionStart hook for cloud agents (optional) | todo | |

## Upcoming phase tasks

Full task lists are in [development-plan.md §3](development-plan.md#3-phase-plan). Copy the next phase's table here when it becomes active.

## Backlog / unscheduled

_(Discovered work that doesn't belong to a phase yet.)_

- None.

## Key links

- Spec: [technical-specification.md](technical-specification.md)
- Plan: [development-plan.md](development-plan.md)
- Decisions: [decisions/README.md](decisions/README.md)
- Live site: _not yet deployed_
