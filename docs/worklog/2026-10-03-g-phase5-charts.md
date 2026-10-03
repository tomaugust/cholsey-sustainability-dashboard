# 2026-10-03 — Phase 5 data wiring and charts (P5.1–P5.8)

- **Phase / tasks:** Phase 5, P5.1–P5.8
- **Branch / PR:** `phase-5-data-wiring-charts` → `main`
- **Agent / person:** Claude Code agent, live session with Tom

## Done

- **P5.1** already satisfied in Phase 4 (real JSON, ADR-0013).
- **P5.2** home tiles: latest-year label, Cholsey sparkline, better/similar/worse indicator vs district and England (icon + text + % difference, from `direction`/`similar_band_pct`); `lib/compare.ts`.
- **P5.3/P5.4** `TrendChart` (Cholsey emphasised, comparators muted, district/national dashed) and `BarChart` (Cholsey vs comparators with district/national reference lines).
- **P5.5** compare page shows Cholsey's verdict against each column.
- **P5.6** marks are focusable; hover/focus/click shows the source panel; estimate flags shown inline.
- **P5.7** text summaries and expandable data tables with per-row provenance.
- **P5.8** deterministic narrative sentences (`lib/narrative.ts`), flagged values labelled "estimate".
- Tests: Vitest 25 (compare, narrative, charts, fixture build proving no hard-coded numbers); Playwright 26 including the provenance gate, three-points rule, unique ids, latest-year labels, interaction.
- ADR-0014; screenshots in `docs/screenshots/phase-5/`.

## Not done / notes

- Three-points test relaxed to "comparator wherever data has one" with an explicit on-page notice for solar PV/heat pump (ADR-0014).
- Manual three-number trace for the PR: to be recorded in the PR body.
- Cholsey's MCS values equal the district rate by construction, so the indicator is "similar" trivially; flagged as estimate.

## Review cycle 1 (Opus)

- Blocking: ADR-0014 relaxes a test of success but was marked Accepted. Now Proposed, with Q-014 logged.
- Fixed: tied values ranked as "1st of 2" (now "tied with"); single-year charts centred; partial-coverage flag no longer labelled "estimate"; marks given `role="img"`; comparator greys darkened for 3:1 contrast; year mismatches vs the reference noted on the indicator; tiny differences shown as "<1%"; last x tick always labelled; Sparkline uses `SUBJECT_CODE`.
- Not done (backlog): provenance gate scanning untagged digits in captions; per-comparator line styles.
