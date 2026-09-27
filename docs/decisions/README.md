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
| [0002](0002-tech-stack-and-repo-layout.md) | Tech stack and repository layout | Proposed | 2026-09-27 |

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
