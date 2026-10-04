# 0015. Phase 6 content model: Markdown front-matter in `content/`, loaded at build time, drafts labelled

- **Status:** Accepted (technical and reversible; the publish-before-approval question is Q-015)
- **Date:** 2026-10-03
- **Deciders:** Claude Code agent (Phase 6 session)
- **Related:** P6.1-P6.5; development-plan.md Phase 6; ADR-0013, ADR-0014

## Context

Phase 6 needs plain-English explainers and local actions that non-developers can edit, are checked automatically, and are reviewed by the parish council reviewer ("S", Q-005) before they count as approved.

## Decision

1. **One Markdown file per metric** in `content/metrics/<metric_id>.md` (plus `glossary.md`, `about.md`), all data in YAML front-matter as P6.1 specifies. `web/src/lib/content.ts` reads and validates them at build time (`js-yaml`, JSON schema so dates stay strings). Invalid content throws, so the build fails.
2. **Checks:** every core metric has a file; 2-4 opportunities, each with title, description, provider, an `https` URL and a `YYYY-MM-DD` `last_checked`; `status: approved` requires `reviewed_by` (a role, never a personal name, per Q-005) and `reviewed_on`.
3. **No digits in any editable prose** ("What this means", opportunity titles and descriptions, glossary, about). Every number on the site must come from the data with provenance, so editable prose may not carry figures. The validator enforces this.
4. **Readability** (Flesch reading ease, 60 or more) is computed over reader-facing text and printed as a warning only.
5. **Drafts are labelled.** Anything not `status: approved` shows a "Draft wording: awaiting review" notice.
6. **Opportunity links** are real, currently reachable pages found by search and checked on 2026-10-03, preferring GOV.UK and local bodies. Grant amounts and eligibility thresholds are deliberately not quoted, so the copy does not go stale. A `lychee` job in CI and a weekly scheduled workflow check external links (403/429 accepted, since some publishers block automated requests).
7. **Review pack:** `npm run content:export` writes `docs/content-review-pack.md` for the reviewer.

## Consequences

- A non-developer can edit copy through a GitHub web edit; bad edits fail CI with a clear message.
- The phase exit criterion (approved content) needs a human review step; see Q-015.
