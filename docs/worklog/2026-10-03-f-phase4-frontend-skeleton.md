# 2026-10-03 — Phase 4 front-end skeleton (P4.1–P4.8)

- **Phase / tasks:** Phase 4, P4.1–P4.8
- **Branch / PR:** `phase-4-frontend-skeleton` → `main` (PR to be opened)
- **Agent / person:** Claude Code agent, live session with Tom

## Goal

Build the structurally complete site (all four page types) against the real data.

## Done

- **P4.1/P4.2** — [ADR-0013](../decisions/0013-phase4-real-data-and-metric-config.md): no placeholder generator; real `web/src/data/*.json` used. Added `export.build_metric_config_json`, `registry.load_tile_groups`, `scripts/build_metric_config.py` and `web/src/data/metric_config.json`. Contract tests (`pipeline/tests/contract/test_site_data_contract.py`) validate the committed JSON against `METRICS_CSV_SCHEMA`, registry references, and registry staleness.
- **P4.3** layout (skip link, landmarks, nav, footer with OGL/source attributions from `sources.json`), Astro `site`/`base` set, `href()` helper.
- **P4.4** home page: five tiles with Cholsey value, year label, estimate flag, district and England values, sparkline and indicator slots.
- **P4.5** `/metrics/<tile>/` pages (home energy carries electricity + gas side by side) with trend and comparator tables as chart slots, "What this means" and "Opportunities" slots.
- **P4.6** `/compare/`: table of Cholsey, one comparator (select, progressive enhancement), district, England.
- **P4.7** `/methodology/` from `sources.json`; **P4.8** `<Provenance>` on every number.
- Vitest (14 tests), Playwright smoke tests (11) wired into CI's web job; screenshots at 360/1280 px in `docs/screenshots/phase-4/`.

## Verification

`make test` and `make lint` clean (pipeline 314 passed); Playwright 11 passed locally against `astro preview`; no horizontal overflow at 360 px.

## Not done / carried over

- Comparison indicator, sparklines, charts and narrative text are slots (Phase 5/6). Solar PV and heat pump show "Not available" for England (accepted MCS gap, ADR-0007).
- PR review, merge and Pages check pending.
