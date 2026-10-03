# 0013. Phase 4 builds against the real generated JSON, plus a generated metric registry

- **Status:** Accepted (technical, reversible, within the plan's intent)
- **Date:** 2026-10-03
- **Deciders:** Claude Code agent (Phase 4 session)
- **Related:** P4.1, P4.2, P4.5; development-plan.md §3 Phase 4; ADR-0010

## Context

P4.1 asks for placeholder `metrics.json`/`sources.json`/`areas.json` produced by a pipeline fixture generator "so the shapes cannot drift", and Phase 4's tests ask for a contract test that the placeholder JSON validates against the pipeline schema. Phase 3 already shipped the real JSON in exactly that shape, so a placeholder generator would only create a second, fake dataset to keep in sync. Separately, the site needs labels, units, direction and tile grouping, which live only in `config/metrics.yaml`; hard-coding them in TypeScript would let the two drift.

## Decision

1. **No placeholder generator.** The site is built against the real `web/src/data/*.json`. The shape-drift guarantee is kept by a contract test (`pipeline/tests/contract/test_site_data_contract.py`) that validates the committed `metrics.json` against `METRICS_CSV_SCHEMA`, checks registry references, and checks `sources.json`/`areas.json` coverage. It runs in CI's pipeline job.
2. **Generated metric registry.** `export.build_metric_config_json` writes `web/src/data/metric_config.json` (label, unit, direction, similar band, tile list in `metrics.yaml` order, stretch metrics excluded) from `config/metrics.yaml`. It is regenerated offline by `scripts/build_metric_config.py` (and by `build_metrics_csv.py`); a contract test fails if the committed file is stale.
3. **TypeScript types** are hand-written in `web/src/lib/types.ts` and checked against the real JSON by `astro check` (JSON imports are typed) plus Vitest loader tests; the pipeline contract test is the authority on the schema itself.

## Consequences

- P4.1 is satisfied in intent (shapes cannot drift) with less code; the "placeholder" wording of the plan is deliberately not followed.
- Phase 5 needs no data swap-over.
- Any change to `metrics.yaml` requires re-running `build_metric_config.py`; CI catches forgetting.
