# Project Status

**Last updated:** 2026-09-27 by agent (planning session). See [worklog](worklog/2026-09-27-planning-and-docs-setup.md).
**Current phase:** Phase 0: Foundations & agent workflow (`active`)
**Current focus:** Getting ADR-0002 (tech stack & layout) confirmed, then scaffolding the pipeline, web and CI.

> How to maintain this file: see [development-plan.md §4](development-plan.md#4-agent-working-protocol--documentation-strategy). It holds the **present** only. Overwrite it; don't append history. Update it at the end of every session.
> Task states: `todo` · `in-progress` (branch) · `review` (PR) · `blocked` (reason) · `done` · `deferred` (reason)

---

## Next steps (ordered, and the first one is actionable by a cold-start agent)

1. **Q-001**: ask the project lead to confirm or amend [ADR-0002](decisions/0002-tech-stack-and-repo-layout.md) (stack & repo layout). *P0.3–P0.7 can start on the proposed stack. Only P0.2 waits on the answer.*
2. **P0.3**: scaffold `pipeline/` (uv, ruff, pytest, package skeleton, `.gitignore` for `data/raw/`).
3. **P0.4**: `config/` YAML skeletons with loader and validation tests (including the negative test).
4. **P0.5 / P0.6**: Astro skeleton in `web/`, and the `Makefile`.
5. **P0.7**: CI (`ci.yml`) and Pages deploy (`deploy.yml`). Then update the *Commands* section of `CLAUDE.md`.

## Blockers

None.

## Open questions for the project lead

| ID | Raised | Question | Assumption in the meantime | Blocks |
| --- | --- | --- | --- | --- |
| Q-001 | 2026-09-27 | Accept the proposed stack in ADR-0002 (Python/uv/geopandas pipeline, Astro + Observable Plot site, GitHub Pages)? | Proceed on the proposed stack | P0.2 |
| Q-002 | 2026-09-27 | Spec §6 says "five headline tiles", but §3 lists six core metrics (+ EPC stretch), and §8 says "5 sources". One tile per metric (six), or combine electricity and gas into one "home energy" tile? | Six tiles, one per core metric | P4.4 (not yet) |
| Q-003 | 2026-09-27 | National benchmark: prefer England or GB where a dataset offers both? | England where available, else GB, labelled per row | P3.7 (not yet) |
| Q-004 | 2026-09-27 | Default GitHub Pages URL, or a custom domain at launch? | Default Pages URL | P7.7 (not yet) |
| Q-005 | 2026-09-27 | Who in the parish council reviews content (Phase 6) and signs off launch (Phase 7)? | The project lead (Tom) | P6.5, P7 (not yet) |

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
| P0.2 | Confirm ADR-0002 (stack & layout) | blocked | Q-001 |
| P0.3 | `pipeline/` Python project skeleton | todo | |
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
