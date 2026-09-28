# 0003. Comparator parish selection

- **Status:** Proposed. Awaiting confirmation by the project lead (Q-009 in STATUS.md). This is a scope/comparator decision — CLAUDE.md and development-plan.md §4.4 say an agent does not decide this unilaterally, only propose it.
- **Date:** 2026-09-28
- **Deciders:** Phase 1 (P1.3) computation (proposal), project lead (confirmation)
- **Related:** P1.3; spec §2; Q-009 in STATUS.md; `pipeline/src/cholsey_pipeline/geography/comparators.py`

## Context

Spec §2 names five "likely candidates" for comparator parishes, explicitly caveated with "confirm against the ONS Parish boundary layer": Wallingford (town), Moulsford, South Stoke, Brightwell-cum-Sotwell, and "Aston Tirrold & Aston Upthorpe". Development-plan.md P1.3 says to compute which parishes' polygons actually **touch** Cholsey's, using real ONS boundary data, and compare against that candidate list — not to assume the candidates are correct.

P1.1 built a real fetcher against the ONS parish boundary FeatureServer (`geography/boundaries.py`). This ADR is the result of actually running that computation.

## Method

1. Queried the live ONS parish layer (`Parishes and Non Civil Parished Areas (December 2023) Boundaries EW BFC`) for every parish within a 5km-buffered bounding box of Cholsey's own polygon (46 candidates).
2. Fetched full geometries for those candidates plus Cholsey (British National Grid, EPSG:27700).
3. Computed which candidates' polygons intersect Cholsey's polygon buffered by 5m (to tolerate small gaps BFC clipping can leave at shared boundaries). Cross-checked the result is identical at buffer sizes 0m, 1m, 5m and 20m — stable, not a precision artefact.
4. Implemented as `find_touching_parishes()` in `pipeline/src/cholsey_pipeline/geography/comparators.py`, tested against a committed fixture (`pipeline/tests/fixtures/comparators/parishes_near_cholsey_sample.geojson`) in `pipeline/tests/unit/test_comparators.py`.

## Result: two real findings against the spec's candidate list

**Eight parishes genuinely touch Cholsey**, not five:

| Parish | GSS code | In spec §2's candidate list? |
| --- | --- | --- |
| Wallingford | E04012496 | Yes |
| Moulsford | E04008148 | Yes |
| South Stoke | E04008163 | Yes |
| Brightwell-cum-Sotwell | E04012473 | Yes |
| Aston Tirrold | E04008102 | Partially (see below) |
| **Aldworth** | E04001147 | **No — not in spec's list** |
| **Crowmarsh** | E04008118 | **No — not in spec's list** |
| **South Moreton** | E04012494 | **No — not in spec's list** |

**Finding 1 — "Aston Tirrold & Aston Upthorpe" is not one parish, it's two, and only one of them touches Cholsey.** The spec lists them as a single hyphenated candidate. They are in fact separate civil parishes with separate GSS codes (Aston Tirrold `E04008102`, Aston Upthorpe `E04008103`). Only Aston Tirrold's polygon touches Cholsey's; Aston Upthorpe does not (it borders Aston Tirrold, not Cholsey). Confirmed by a dedicated test (`test_aston_upthorpe_does_not_touch_despite_the_spec_pairing`).

**Finding 2 — Three real neighbours are missing from the spec's candidate list entirely**: Aldworth, Crowmarsh and South Moreton. All three genuinely share a boundary with Cholsey per the live ONS data.

(This is the second real "don't trust the spec's assumptions, verify against live data" finding from Phase 1 — the first was the two different parishes both named "South Stoke", P1.1's worklog entry. The spec's candidate list appears to have been compiled by looking at a map rather than checking parish boundary data, which is exactly the gap P1.3 exists to close.)

## Options considered

1. **Use the spec's original 4 confirmed candidates only** (Wallingford, Moulsford, South Stoke, Brightwell-cum-Sotwell), dropping the Aston Tirrold/Upthorpe pairing since it doesn't cleanly match either real parish. Closest to the spec's original intent and headline-tile-count assumptions; ignores 4 real neighbours (Aston Tirrold plus the 3 newly found).
2. **Use all 8 real touching parishes.** Matches P1.3's literal instruction ("compute parishes whose polygons touch Cholsey") most faithfully, gives more comparator data points for the comparison page (spec §6), but is a bigger set than the spec's UX sections seem to have been written assuming (e.g. bar charts "comparing Cholsey to each named comparator parish" — 8 bars is more than 5 but still very workable).
3. **A curated subset of the 8** — for example the 4 spec-original ones plus Aston Tirrold (5 total, closest to spec's original count while being geometrically correct), dropping Aldworth/Crowmarsh/South Moreton. Splits the difference but is itself a judgement call about which real neighbours "count" less than others, with no principled reason to exclude 3 of 8 genuine neighbours.

## Decision (proposed)

**Recommend Option 2: all 8 real touching parishes** — Wallingford, Moulsford, South Stoke, Brightwell-cum-Sotwell, Aston Tirrold, Aldworth, Crowmarsh, South Moreton. This is the literal, defensible answer to "which parishes touch Cholsey", requires no further judgement calls about which genuine neighbours to drop, and the UX impact (a bar chart with 8 bars instead of 5, spec §6) is real but minor. `config/geography.yaml` has been updated with these 8 real GSS codes, each still flagged `pending_confirmation: true` pending this ADR's acceptance.

**This is a recommendation, not a decision** — Tom may prefer Option 1 or 3 for UX/simplicity reasons the spec's original 5-candidate framing suggests. See Q-009 in `STATUS.md`.

## Consequences

- If Option 2 is confirmed: `config/geography.yaml`'s 8 comparator entries lose their `pending_confirmation` flag, and Phase 3 (P3.7 benchmarks) and Phase 5 (charts) proceed against 8 comparators rather than 5.
- If Option 1 or 3 is chosen instead: whoever actions Q-009 removes the non-selected entries from `config/geography.yaml` and notes the reason (spec-alignment / UX simplicity) in this ADR's Consequences, superseding this recommendation without a whole new ADR number (a straightforward "the recommendation in this ADR was not accepted, N parishes were used instead, see Q-009" edit, since the method and findings above don't change).
- Either way, the underlying computation (`comparators.py`, tested) is reusable for Phase 1's other geography work and needs no rework.
