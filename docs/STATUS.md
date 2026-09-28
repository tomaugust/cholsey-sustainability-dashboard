# Project Status

**Last updated:** 2026-09-28 by agent (scheduled routine run). See [worklog](worklog/2026-09-28-b-p0.4-config-files.md).
**Current phase:** Phase 0: Foundations & agent workflow (`active`)
**Current focus:** P0.3 and P0.4 done. Next: P0.5/P0.6 (web skeleton, Makefile), then P0.7 (CI). Note the comparator parishes in `config/geography.yaml` are unconfirmed placeholders pending Phase 1 — see below.

> How to maintain this file: see [development-plan.md §4](development-plan.md#4-agent-working-protocol--documentation-strategy). It holds the **present** only. Overwrite it; don't append history. Update it at the end of every session.
> Task states: `todo` · `in-progress` (branch) · `review` (PR) · `blocked` (reason) · `done` · `deferred` (reason)

---

## Next steps (ordered, and the first one is actionable by a cold-start agent)

1. **P0.5**: Astro skeleton in `web/` (TypeScript, one placeholder page, `npm run build/test/lint` scripts).
2. **P0.6**: root `Makefile` (`setup`, `test`, `lint`, `refresh`, `site` — `refresh`/`site` can be stubs until Phase 2/4 land real work; `setup`/`test`/`lint` should already work for real against `pipeline/` and, once P0.5 lands, `web/`).
3. **P0.7**: CI (`ci.yml`, running `uv run pytest`/`ruff` in `pipeline/` and `npm test`/lint in `web/`) and Pages deploy (`deploy.yml`) to the default `github.io` URL (Q-004). Then update the *Commands* section of `CLAUDE.md` to match reality (currently says "still to do").
4. **Not blocking Phase 0, but flag for Phase 1:** `config/geography.yaml`'s five comparator parishes are unconfirmed `PENDING-*` placeholders (no real GSS code) — Phase 1 (P1.1-P1.3) must replace them with real, ONS-confirmed codes (or drop/replace candidates) before Phase 3 can join any comparator data. `config/sources.yaml`'s MCS licence field is also marked "TBD" pending the P2.7 access investigation.

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
| P0.4 | `config/` YAML skeletons + loader + tests | done | 2026-09-28, real `sources.yaml`/`geography.yaml`/`metrics.yaml` + 12 integration tests. Comparator parish codes are unconfirmed placeholders — see Next steps. |
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
