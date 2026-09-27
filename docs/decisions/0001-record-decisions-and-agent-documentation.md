# 0001. Record decisions and maintain agent documentation

- **Status:** Accepted
- **Date:** 2026-09-27
- **Deciders:** Planning session, at the project lead's request
- **Related:** P0.1; development-plan.md §4

## Context

AI coding agents will build this project across many separate sessions. None of them remembers earlier sessions. Without a shared written record, each session would have to reconstruct the project state, and might repeat work, contradict earlier choices or drift from the spec. The project also has to be handed over to non-specialist volunteer maintainers (spec §7), so the reasoning behind choices must survive the people and agents who made them.

## Options considered

1. **Single running notes file.** Simple, but it mixes present state with history and reasons. It grows without bound, and it's hard for a cold-start agent to find "what's next".
2. **GitHub Issues / Projects only.** Good for task tracking, but it lives outside the repo. Cloud agents may not always have API access to it, and it can't be versioned with the code.
3. **Separated in-repo docs, each with one job** (status, worklog, decision records, plan, spec) and a mandatory session protocol.

## Decision

Option 3. Each document holds one kind of information:

- `docs/STATUS.md` holds the **present**: current phase, task states, blockers, open questions and ordered next steps. It is overwritten and kept short.
- `docs/worklog/YYYY-MM-DD-slug.md` holds the **past**, with one append-only entry per session.
- `docs/decisions/NNNN-*.md` holds the **reasons** (ADRs). They are immutable once accepted and superseded, not rewritten.
- `docs/development-plan.md` holds the **future**: phases, outcomes and tests of success. It changes only via an ADR.
- `docs/technical-specification.md` holds the **intent**. Only the project lead edits it.
- `CLAUDE.md` is the entry point: reading order, rules and commands.

Every session must update `STATUS.md` and add a worklog entry before it ends, and must commit the docs together with the code. Tasks carry stable IDs (`P<phase>.<n>`) and questions carry `Q-NNN` IDs, so work can be traced across commits, PRs and sessions.

GitHub Issues may be used as well, for example the automated `data-refresh-failed` issue in Phase 8. The in-repo docs remain the source of truth.

## Consequences

- A cold-start agent can orient itself from 2–3 short files.
- There is a small overhead each session: a few minutes of documentation.
- `STATUS.md` can go stale if a session ends abruptly. The session-start protocol (plan §4.2 step 4) checks it against `git log` and repairs it.
- The protocol is only useful if it is followed. Phase-end doc audits (plan §4.6) catch drift.
