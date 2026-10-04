# 0016. Defer content approval (P6.5) to the Phase 7 launch gate

- **Status:** Accepted (decided by Tom, Q-015, 2026-10-04)
- **Date:** 2026-10-04
- **Deciders:** Tom (project lead)
- **Related:** P6.5, P7.8; development-plan.md Phase 6 exit criteria; ADR-0015; Q-005, Q-015

## Context

Phase 6's exit criterion is "all core metrics have approved content", and P6.5 is a human review by the parish council reviewer ("S"). The site is deployed on a public GitHub Pages URL, but that URL has not been shared with anyone, so it is very unlikely to be found.

## Decision

Tom's call: build as complete a site as possible, with unapproved elements marked as draft, before sharing it with anyone. Therefore:

1. Phase 6 is merged and marked done with all content `status: draft`. The on-page "Draft wording" notices stay until approval.
2. Approval moves to Phase 7 as **P7.8**. The URL is not shared until every `content/` file is `status: approved` with `reviewed_by` (role only) and `reviewed_on`.
3. How S reviews (reading `docs/content-review-pack.md` and replying, or editing `content/*.md` on GitHub) is decided at that point.
4. Later phases that add reader-facing wording follow the same rule: mark it draft and include it in the review pack.

## Consequences

- Changes S asks for arrive at the end. The review pack and the editable Markdown model keep that cheap.
- The Phase 6 exit criterion is knowingly relaxed; the launch gate carries it instead.
