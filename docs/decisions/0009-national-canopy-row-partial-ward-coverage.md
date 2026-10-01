# 0009. How to compute and present P3.2's England national canopy row, given Forest Research's dataset doesn't cover all of England

- **Status:** Accepted (technical/methodology decision within P3.2's existing scope — development-plan.md P3.2 says "District and national from the same dataset," without anticipating this gap; this ADR documents how that's actually done, not a new spec/scope/stack decision).
- **Date:** 2026-10-01
- **Deciders:** Phase 3 (P3.2) implementation
- **Related:** P3.2; ADR-0006 (ward vintage); `pipeline/src/cholsey_pipeline/fetch/forest_research_canopy.py`; `pipeline/src/cholsey_pipeline/metrics/canopy.py`

## Context

P3.2's district row (South Oxfordshire, built 2026-10-01) area-weighted all 21 of the district's own current wards and got a total ward area matching the district's real boundary area to within 0.003% — in that one LAD, Forest Research's dataset has complete ward coverage.

The national row doesn't have that property. Fetching every English ward record from Forest Research's `UK_Ward_Canopy_Cover` service (`country='England'`, live, paginated: 6,135 records) and summing each record's own `warea` field (verified real and usable — Cholsey's own ward record's `warea`, 66,557,077.88 m², matches the ~66 km² figure already used elsewhere in this codebase) gives a **total covered ward area of 71,286,265,097.85 m² (~71,286 km²) — only 54.6% of England's real BFC boundary area (130,462,331,610.03 m², verified live via the `country_bfc` layer added for P3.3's national greenspace row)**.

By ward *count* the gap looks much smaller: 6,135 Forest Research records vs. 6,862 current English wards (Dec 2023 boundaries, verified live) — 89.4% covered. The much larger area-based gap (54.6%) means the missing ~727 wards are disproportionately large, i.e. disproportionately rural — consistent with this already being a documented, real finding at smaller scale: Aldworth's own containing ward (Basildon, West Berkshire) has **no** Forest Research record at all (P3.2's module docstring, found while building the comparator rows), and that's exactly the kind of rural, less-populated ward this citizen-science dataset appears to systematically under-cover.

A second, smaller real finding from the same live fetch: Forest Research's wards were surveyed across multiple real years (2018: 137, 2019: 1,246, 2020: 2,135, 2021: 1,204, 2022: 1,115, 2023: 30), not one single "2020" survey as the project's earlier risk register (development-plan.md R2) assumed before P2.3 investigated — already corrected there for Cholsey's own ward, but a national aggregate now has to blend all of these real vintages into one figure. A third: 268 of the 6,135 records (4.4%) carry a placeholder `survyear` of `0` and nulls for `standard_error`/`number_of_points`, but still have real, non-null `percent_canopy_cover` and `warea` values — a data-quality gap in the dataset's own metadata, not in the measurement actually needed for the area-weighted average.

## Decision

**Compute the England row as the real area-weighted average across every one of the 6,135 ward records Forest Research's dataset actually has for England** (not restricted to a "clean" subset) — this is the same dataset, same methodology, and same honest approach as the subject/comparator/district rows: use what the source really contains, and flag what it doesn't cover, rather than silently padding the gap with an assumption about the missing wards' canopy cover (CLAUDE.md: never silently interpolate).

- Include all 6,135 records, including the 268 with a `survyear` of `0` — their `percent_canopy_cover`/`warea` are real, non-null measurements; excluding them would only *increase* the coverage gap for no accuracy gain (the aggregate moves by 0.05 percentage points either way: 14.36% excluding them vs 14.41% including them).
- Report `year` as 2020, the modal real survey year (2,135 of the 5,867 non-placeholder records) — a representative label, not a claim that every included ward was surveyed in 2020.
- `method=area_weighted` (matching the district row), **`flag=partial_coverage`** (not `flag=none`, unlike the district row) — the district's 21 wards fully tile South Oxfordshire; England's 6,135 available wards do not tile England, so this is a real, material coverage gap that must be visible wherever the figure is shown, not just in code comments.
- `flag_note` states the real coverage gap in both terms that matter (54.6% of England's area; 89.4% of its current wards) and the likely direction of bias (missing wards are disproportionately large/rural, so this figure likely skews toward more urban canopy rates than true full-England coverage would show), plus the multi-year blend (2018–2023, modal 2020) and the 268-record metadata gap.

**Not done**, and not needed to make this row usable: joining the included wards against current ONS ward boundaries to compute a "true" area-weighted figure some other way — Forest Research's own `warea` field is itself a verified real area (cross-checked against Cholsey's ward), so there's no missing input here, only missing *rows* (uncovered wards), which no join against current boundaries could supply canopy data for anyway.

## Consequences

- `pipeline/src/cholsey_pipeline/fetch/forest_research_canopy.py` gained `fetch_ward_canopy_for_country` (paginated England-wide fetch, its own manifest, and a new `forest_research_canopy_national` contract in `contracts.py` that doesn't require `standard_error`/`number_of_points` to be non-null, since 26 real records lack them but still have valid `percent_canopy_cover`/`ward_area_m2`).
- `WardCanopyRecord` gained two new optional fields (`country`, `ward_area_m2`), defaulting to `""`/`None` so every existing subject/comparator/district call site (which doesn't request these fields from the service) is unaffected.
- `metrics/canopy.py` gained `compute_national_canopy_row`, which area-weights directly off each record's own `ward_area_m2` (no separate boundary join needed) and always sets `flag=partial_coverage`.
- Real figure (live-verified 2026-10-01): England's area-weighted average canopy cover across its 6,135 available Forest Research ward records is **14.41%** (year label 2020) — this is the dashboard's England reference line for metric 1, clearly flagged as covering 54.6% of England's area rather than all of it.
- A future session revisiting this (e.g. if Forest Research ever publishes the missing wards, or if UKCEH's Land Cover Map — evaluated and declined for metric 1 generally in ADR-0006 — is reconsidered specifically as a *gap-fill* for the uncovered wards rather than a full replacement) should update this ADR rather than silently changing the figure's meaning.
