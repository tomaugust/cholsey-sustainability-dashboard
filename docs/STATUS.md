# Project Status

**Last updated:** 2026-09-28 by agent (scheduled routine run). See [worklog](worklog/2026-09-28-c-p0.5-p0.6-web-and-makefile.md).
**Current phase:** Phase 0: Foundations & agent workflow (`active`)
**Current focus:** P0.3-P0.6 done. Next: P0.7 (CI + Pages deploy) — the last Phase 0 task. Note the comparator parishes in `config/geography.yaml` are unconfirmed placeholders pending Phase 1 — see below.

> How to maintain this file: see [development-plan.md §4](development-plan.md#4-agent-working-protocol--documentation-strategy). It holds the **present** only. Overwrite it; don't append history. Update it at the end of every session.
> Task states: `todo` · `in-progress` (branch) · `review` (PR) · `blocked` (reason) · `done` · `deferred` (reason)

---

## Next steps (ordered, and the first one is actionable by a cold-start agent)

1. **P0.7** (last Phase 0 task): CI workflow `.github/workflows/ci.yml` running `make test` and `make lint` on every PR (the Makefile from P0.6 already does the real work — this just wires it into Actions), plus a GitHub Pages deploy workflow `.github/workflows/deploy.yml` that runs `make site` and publishes `web/dist/` on push to the default branch, to the default `github.io` URL (Q-004; no custom domain). Then update `CLAUDE.md`'s *Commands* section — it currently says "still to do", but `make setup/test/lint` already work for real (verified in the P0.5/P0.6 worklog entry); only `refresh`/`site` need the caveat that `refresh` is a stub. Also confirm GitHub Pages is enabled on the repo (Settings → Pages → Source: GitHub Actions) since Actions can't turn that setting on itself.
2. **This closes Phase 0.** Once P0.7 is merged and a real deploy is confirmed live, mark Phase 0 `done` in the Phase overview table below and move Phase 1 (Boundaries & geographic scope) to `active` as the new current phase — see development-plan.md §3 Phase 1 for its task list (P1.1-P1.7), and copy that table into "Current phase tasks" below.
3. **Not blocking Phase 0, but flag for Phase 1:** `config/geography.yaml`'s five comparator parishes are unconfirmed `PENDING-*` placeholders (no real GSS code) — Phase 1 (P1.1-P1.3) must replace them with real, ONS-confirmed codes (or drop/replace candidates) before Phase 3 can join any comparator data. `config/sources.yaml`'s MCS licence field is also marked "TBD" pending the P2.7 access investigation.

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
| P0.5 | `web/` Astro skeleton | done | 2026-09-28, TypeScript strict, 1 page, 1 vitest test, eslint+prettier clean, `astro check && astro build` clean |
| P0.6 | `Makefile` | done | 2026-09-28, `setup`/`test`/`lint` genuinely work from repo root (verified); `refresh`/`site` are stubs/placeholders per plan |
| P0.7 | CI + GitHub Pages deploy workflows | todo | Last Phase 0 task |
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
