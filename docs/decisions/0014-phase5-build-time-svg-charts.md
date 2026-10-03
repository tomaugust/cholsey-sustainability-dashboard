# 0014. Phase 5 charts are build-time SVG with a long-form data table; three-points rule relaxed where no comparator data exists

- **Status:** Accepted. Decision 5 (relaxed three-points test) was confirmed by Tom (Q-014, 2026-10-03); the rest is technical and reversible.
- **Date:** 2026-10-03
- **Deciders:** Claude Code agent (Phase 5 session)
- **Related:** P5.2–P5.8; development-plan.md Phase 5 tests of success; ADR-0007 (MCS gap), ADR-0013

## Context

Phase 5 needs trend and bar charts with provenance on interaction, keyboard access and accessible fallbacks, on a static zero-cost site with no JavaScript framework.

## Decision

1. **Charts are inline SVG rendered at build time** by Astro components (`TrendChart`, `BarChart`, `Sparkline`), with geometry in `src/lib/chart.ts`. No charting dependency. Cholsey is drawn thick and green, comparators thin grey, district and England dashed with different dash patterns (not colour alone); a legend is always shown.
2. **Provenance on interaction.** Every mark carries `data-value` and `data-prov-id`, which points at a `<Provenance>` element (with `data-field` source/geography/year) in the chart's own data table. A small script copies it into the chart's live region on hover, focus or click. Marks are focusable.
3. **Fallbacks.** Each chart has a text summary and a `<details>` data table listing every plotted value with its provenance.
4. **Provenance gate** (Playwright): every `[data-value]` on every page must resolve to a provenance element with non-empty source, geography and year.
5. **Three-points rule** is tested as: every chart includes Cholsey and a district/national reference, and a comparator wherever the data has one. For metrics with no comparator rows (MCS solar PV and heat pump, ADR-0007) the page must show an explicit "no comparator data" notice. The plan's literal wording ("at least one comparator") cannot hold there.
6. **No hard-coded numbers.** `@data` is a Vite alias (`SITE_DATA_DIR` overrides it); a Vitest test builds the site against a fixture with one changed value and checks it appears.

## Consequences

- Zero client-side chart code beyond ~20 lines; deterministic output.
- Cholsey's solar PV/heat-pump rows are the district rate applied to the parish (flagged as estimates), so the indicator reads "similar to South Oxfordshire" by construction; narrative sentences mark such values as estimates.
- If MCS parish data arrives, the notice disappears automatically.
