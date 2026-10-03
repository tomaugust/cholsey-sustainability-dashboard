# Decision Records (ADRs)

Each file records one significant decision: its context, the options considered, the choice made and the consequences. Why we keep them, and when to write one, is set out in [ADR-0001](0001-record-decisions-and-agent-documentation.md) and [development-plan.md §4.4](../development-plan.md#44-decision-records-adrs).

## Rules

- Name files `NNNN-kebab-case-title.md`, numbered sequentially. Add each one to the index below.
- An agent may **accept** its own ADR when the decision is technical, reversible and within the plan. Anything touching scope, stack, comparators or the spec stays **Proposed** until the project lead confirms. Log it as a `Q-NNN` in `STATUS.md`.
- Accepted ADRs are immutable. To change one, write a new ADR that supersedes it, and change only the old one's **Status** line to `Superseded by NNNN`.
- Commit an ADR in the same PR as the code it justifies.

## Index

| # | Title | Status | Date |
| --- | --- | --- | --- |
| [0001](0001-record-decisions-and-agent-documentation.md) | Record decisions and maintain agent documentation | Accepted | 2026-09-27 |
| [0002](0002-tech-stack-and-repo-layout.md) | Tech stack and repository layout | Accepted (deviate only with a superseding ADR) | 2026-09-27 |
| [0003](0003-comparator-parish-selection.md) | Comparator parish selection | Accepted | 2026-09-28 |
| [0004](0004-p1-5-apportionment-weight-methodology.md) | P1.5 apportionment weight methodology (NSUL source, whole-address counts, scope) | Accepted | 2026-09-28 |
| [0005](0005-p1-6-population-and-household-denominator-methodology.md) | P1.6 population/household denominator methodology (mid-year source, scope, the third population figure) | Accepted | 2026-09-29 |
| [0006](0006-canopy-cover-source-and-ward-vintage.md) | Canopy cover source (Forest Research vs UKCEH Land Cover Map) and a ward-vintage correction | Accepted | 2026-09-29 |
| [0007](0007-mcs-installation-data-access-investigation.md) | MCS installation data access investigation | Accepted (Q-011 answered) | 2026-09-30 |
| [0008](0008-accessible-greenspace-function-types.md) | Which OS Open Greenspace function types count as "accessible green space" (metric 2) | Accepted | 2026-09-30 |
| [0009](0009-national-canopy-row-partial-ward-coverage.md) | How to compute and present P3.2's England national canopy row, given Forest Research's dataset doesn't cover all of England | Accepted | 2026-10-01 |
| [0010](0010-export-provenance-assembly.md) | How `export.py` attaches provenance to each metrics.csv row (P3.9) | Accepted | 2026-10-01 |
| [0011](0011-suppression-fallback-deferred.md) | Suppression fallback deferred | Accepted | 2026-10-02 |
| [0012](0012-reconciliation-scope-vs-district-coverage.md) | Reconciliation scope vs district coverage | Accepted | 2026-10-03 |
| [0013](0013-phase4-real-data-and-metric-config.md) | Phase 4 builds against real JSON plus a generated metric registry | Accepted | 2026-10-03 |

## Template

Copy this into a new file:

```markdown
# NNNN. <Title>

- **Status:** Proposed | Accepted | Rejected | Superseded by NNNN
- **Date:** YYYY-MM-DD
- **Deciders:** <agent session / project lead>
- **Related:** <task IDs, spec §, other ADRs>

## Context
What problem or question prompted this? What constraints apply (spec, plan, data)?

## Options considered
1. **Option A**: pros / cons
2. **Option B**: pros / cons

## Decision
What we chose, stated plainly.

## Consequences
What becomes easier or harder. Follow-up tasks (with IDs). How to revisit.
```
