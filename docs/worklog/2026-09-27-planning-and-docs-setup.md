# 2026-09-27 — Planning and documentation setup

- **Phase / tasks:** P0.1
- **Branch / PR:** `claude/new-session-7bcxu1` / not opened
- **Agent / person:** Claude Code agent, at Tom's request

## Goal
Bring the technical specification into the repo. Produce a detailed, phased development plan with outcomes and tests of success. Set up the documentation system that future agents will use.

## Done
- Copied the spec from Tom's Claude Doc "Cholsey Parish Sustainability Dashboard — Technical Specification" (revision 14) into `docs/technical-specification.md`. The only change is the embedded pipeline diagram, which the export dropped and which was redrawn as Mermaid. A provenance note was added at the top.
- Wrote `docs/development-plan.md`: guiding principles, target architecture and canonical data model, nine phases (0–8) with work packages, key outcomes, automated and manual tests of success, and exit criteria. Also the agent working protocol and documentation strategy (§4), testing strategy, risks, and a glossary.
- P0.1: created `CLAUDE.md`, `README.md`, `docs/STATUS.md`, `docs/decisions/` (index, template, ADR-0001, ADR-0002), `docs/worklog/` (template and this entry), and `.github/pull_request_template.md`.

## Decisions
- ADR-0001: record decisions and maintain agent documentation (Accepted).
- ADR-0002: tech stack and repository layout (Proposed; Q-001).
- Added a Phase 0 (foundations) that the spec doesn't have. Folded the spec's monthly refresh automation (§5, §7) into Phase 8, alongside handover.
- Chose a canonical CSV with per-row provenance columns as the data model (plan §2.3).

## Verification
Documentation-only session, so there is no code to test. Checked that the spec copy matches the source doc's content section by section (sections 1–8, all tables and links present).

## Not done / carried over
- P0.2–P0.8: see STATUS.md Next steps.
- Open questions Q-001 to Q-005 are raised with Tom.

## Handoff notes
- The spec has an internal inconsistency about the number of headline tiles and sources (five) versus metrics (six core plus a stretch). It is logged as Q-002. Don't build tiles until it's answered, or build six as the interim assumption.
- MCS data access (risk R1 in the plan) is the biggest data uncertainty. Investigate it early in Phase 2 (P2.7), before relying on it.
- Spec area codes (parish E04012474, etc.) have not been verified against ONS data yet. That is P1.2.
