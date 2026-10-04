# 0017. Phase 7 approach: automated gates in CI, noindex until launch, charts sized for 360 px

- **Status:** Accepted (technical and reversible)
- **Date:** 2026-10-04
- **Deciders:** Claude Code agent (Phase 7 session)
- **Related:** P7.1-P7.8; ADR-0014, ADR-0016; docs/launch-checklist.md

## Context

Phase 7 asks for a launch-ready accessible site, with several human-only checks (screen reader, real phones, reviewer approval, launch sign-off), and ADR-0016 says the URL stays unshared until content is approved.

## Decision

1. **Automated gates run in CI:** axe-core (Playwright, all pages, details expanded, serious/critical must be zero), 360 px no-scroll and 44 px tap-target checks, footer and metadata checks, a gzip page-weight budget, and Lighthouse CI (`@lhci/cli`, mobile default, filesystem output) at 95/95/90 on home and one metric page.
2. **Not launched means not indexed.** `LAUNCHED = false` in `web/src/lib/site.ts` adds `noindex, nofollow` to every page. (A `robots.txt` cannot work on a project-site sub-path, so the meta tag is the mechanism.) Lighthouse SEO therefore scores low until the switch is flipped; it is not asserted.
3. **Charts are drawn in a 420-unit-wide viewBox** so SVG text stays about 10 px or more at 360 px and no wider than 36 rem on desktop. Individual chart marks are small touch targets; their information is also reachable through the 44 px "data table" disclosure and the tables' own provenance panels. Nav links, disclosures, selects and opportunity links meet 44 px.
4. **Hand-rolled sitemap** (`sitemap.xml.ts`): the Astro 4-compatible integration path was not worth a dependency.
5. **Methodology page** combines reviewable narrative (`content/methodology.md`, draft, no digits) with a table generated from the data (methods, flags, geography per metric).
6. **Human checks live in `docs/launch-checklist.md`.** They are not done by an agent and Phase 7 is not complete until they are.

## Consequences

- CI gains two slower jobs (Lighthouse, longer Playwright).
- Flipping `LAUNCHED` and the checklist are the only things between the current site and launch.
