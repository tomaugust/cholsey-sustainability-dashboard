# 0010. How `export.py` attaches provenance to each metrics.csv row (P3.9)

- **Status:** Accepted (technical/design decision within P3.9's existing scope -- flagged as needing "a quick design decision (not necessarily an ADR)" by the P3.2 worklog handoff note; writing it up as a short ADR anyway since it fixes the shape of every future metric module's output).
- **Date:** 2026-10-01
- **Deciders:** Phase 3 (P3.9) implementation
- **Related:** P3.9; `METRICS_CSV_SCHEMA` (P3.1, `validate/metrics_schema.py`); every `metrics/*.py` module

## Context

`METRICS_CSV_SCHEMA` requires six non-null provenance columns on every row: `source_id`, `source_name`, `source_publisher`, `source_url`, `retrieved_at`, `raw_sha256`. None of the four metric row dataclasses built so far (`CanopyMetricRow`, `GreenspaceMetricRow`, `EnergyMetricRow`, `UptakeMetricRow`) carry any of these -- flagged as an open gap in the P3.2 worklog (2026-10-01) rather than decided ad hoc while building P3.2/P3.3.

Three of these six columns (`source_name`, `source_publisher`, `source_url`) are properties of the *source*, already sitting in `config/sources.yaml`, looked up by `source_id`. Two more (`retrieved_at`, a fetch-run's hash) are properties of *one specific live fetch*, already recorded in that fetch's manifest entry under `data/manifest/<source_id>/*.json` -- but manifest shapes aren't uniform across fetchers: `fetch.http.fetch_file`'s manifests use a `sha256` key and no `query_signature` unless `record_row_count` added one later; `geography.boundaries.fetch_boundary` and `fetch.forest_research_canopy.fetch_ward_canopy_for_country` (both multi-page, writing their own manifest directly) use `response_sha256` and always set `query_signature`/`where_clause`. Re-deriving "which manifest entry backs this particular row" after the fact, from source_id and query_signature alone, would need to handle both shapes and would be fragile for a source fetched with several different queries in the same session (exactly what happened this session: `forest_research_canopy` now has manifest entries for single-ward queries, a 9-ward comparator query, and a 6,135-ward national query, all under the same source_id).

## Options considered

1. **Add all six provenance fields directly to every row dataclass**, set by each `compute_*_row` function. Rejected: these functions are deliberately pure (no I/O, no config lookups -- development-plan.md §5.1's "pure function, tested against fixtures" pattern used throughout Phase 2/3), and would need `sources.yaml` loaded just to fill in `source_name`/`source_publisher`/`source_url`, which has nothing to do with the actual metric computation. It would also require updating every existing call site and test across four modules (already dozens of tests) for a concern that belongs one layer up.
2. **Have `export.py` re-discover provenance from the manifest after the fact**, matching on `source_id` (+ a best-guess query signature). Rejected: manifest shapes aren't uniform (see above), and "latest manifest for this source_id" would silently pick the wrong fetch's hash/timestamp once a source has been queried more than once with different scopes in the same session -- exactly the kind of silent provenance bug CLAUDE.md's traceability rule exists to prevent.
3. **Have the orchestrating script pass provenance through explicitly at row-assembly time**, right after the fetch that produced the row's underlying data returns (chosen). The script that drives "fetch → compute → assemble" always has the freshest, correct `retrieved_at`/hash in hand at that exact moment (either directly from a `FetchResult`, for sources using `fetch_file`, or by reading the manifest file `fetch_boundary`/`fetch_ward_canopy_for_country` just wrote, which is unambiguous immediately after the call, unlike re-discovering it later). `export.build_metrics_row` takes the already-computed row plus `source_id`/`retrieved_at`/`raw_sha256` as plain arguments, looks up `source_name`/`source_publisher`/`source_url` from the already-loaded `sources.yaml`, and returns one flat dict ready for the final table.

## Decision

**Option 3.** `pipeline/src/cholsey_pipeline/export.py` gains:
- `build_metrics_row(row, *, source_id, retrieved_at, raw_sha256, sources) -> dict` -- a pure function (no I/O) taking any of the four existing `*MetricRow` dataclasses (duck-typed on their shared base fields) plus explicit provenance values and the loaded `sources` registry, returning a dict with every `METRICS_CSV_SCHEMA` column filled in.
- `rows_to_dataframe(rows: list[dict]) -> pd.DataFrame` and `write_metrics_csv`/`write_readme` to turn a batch of such dicts into the final `data/processed/metrics.csv` and `data/processed/README.md`.

None of the four existing metric row dataclasses change. No manifest-matching heuristic is needed. The cost: whatever script eventually orchestrates the full live run (not yet written -- see *Consequences*) must thread `source_id`/`retrieved_at`/`raw_sha256` through itself, immediately after each fetch, rather than recovering them from disk afterwards. This is a small, local cost paid once by one script, versus a correctness risk spread across every future metric.

## Consequences

- `export.py`'s core assembly logic (`build_metrics_row`, `rows_to_dataframe`, `write_metrics_csv`, `write_readme`) is built and tested this session against fixtures -- no network, no dependency on any particular metric module's real data.
- The actual top-level orchestration script -- re-running every live fetch for every area/metric, collecting each one's real `source_id`/`retrieved_at`/`raw_sha256`, calling the right `compute_*_row` function, and calling `build_metrics_row` for every row to produce the real `data/processed/metrics.csv` -- was explicitly scoped out of this session (it's a separate, large integration task: re-running dozens of live fetches across 9 areas × 4+ metrics, several of which take minutes) and built in a later P3.9 firing as `scripts/build_metrics_csv.py`.
- A future metric module (e.g. if P3.6's EPC stretch metric is ever built) follows the same pattern: its `compute_*_row` function stays a pure function with no provenance fields, and whatever script calls it supplies `source_id`/`retrieved_at`/`raw_sha256` to `build_metrics_row` directly.
