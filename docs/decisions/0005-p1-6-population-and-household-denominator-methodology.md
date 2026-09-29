# 0005. P1.6 population/household denominator methodology (mid-year source, scope, the third population figure)

- **Status:** Accepted (technical implementation choice within an already-unblocked task, not a spec/scope/stack decision).
- **Date:** 2026-09-29
- **Deciders:** Phase 1 (P1.6) implementation
- **Related:** P1.6; development-plan.md §3 Phase 1; `pipeline/src/cholsey_pipeline/geography/denominators.py`; `pipeline/scripts/build_population_denominators_csv.py`; `data/processed/geography/population_denominators.csv`; Q-007; ADR-0004

## Context

P1.6 asks for "2021 Census population and dwelling/household counts for Cholsey and comparators (parish-level Census tables), plus mid-year estimates where available."

Parish is not a native Census 2021 output geography (nomis's TS001/TS041 topic-summary tables are only queryable down to Output Area, LSOA, MSOA, LA and ward — confirmed by checking every geography type code the `NM_2021_1`/`NM_2059_1` datasets accept). ONS's own standard solution is the same "best-fit of Output Areas to parishes" method P1.4 already uses for the LSOA join — and ONS publishes this pre-computed for population (an ad-hoc release, "Parish population estimates for mid-2021"), but not for households/dwellings.

## Three genuinely different population figures for Cholsey

While building this, three independently-sourced numbers for Cholsey's population turned up, all legitimate, all different:

| Figure | Value | Source / method |
| --- | --- | --- |
| spec §2's figure | **4,498** | Unstated method — presumably also an OA-best-fit calculation, but on a different boundary vintage or slightly different input than either figure below |
| ONS's own mid-2021 estimate | **4,404** | ONS ad-hoc release, OA-best-fit to PAR22 (2022 parish edition), rebased to Census 2021, as at 30 June 2021 |
| This project's own Census Day OA-best-fit sum | **4,390** | Summing Census 2021 TS001 ("Total: All usual residents") across the same 13 OAs P1.4 already confirmed best-fit Cholsey, as at 21 March 2021 |

The two independently-computed real figures (4,404 and 4,390) agree to within 0.3%, both computed via OA best-fit, differing only in mid-year vs. census-day timing — exactly the kind of small gap expected between those two vintages. Spec's 4,498 is a real outlier against both by ~2.4%, similar in nature (though smaller in magnitude) to Q-007's ~3.7% area discrepancy.

## Decision

**1. Use ONS's own mid-2021 parish population estimate (`ons_parish_population_mid2021`) as the primary, comparator-covering population denominator.** It is a direct, national, parish-level release — no per-comparator OA lookup needed — giving real numbers for Cholsey and all 8 confirmed comparators in one query. This satisfies P1.6's "plus mid-year estimates where available" clause directly, and is the most practical choice for cross-parish comparison (spec's own headline figure and this project's from-scratch OA sum are both Cholsey-only).

**2. Also compute and keep the from-scratch Census Day OA-best-fit population (4,390) and household count (1,782) for Cholsey/Moulsford**, reusing P1.4's exact OA set and best-fit assignment — this directly answers P1.6's literal "2021 Census population... (parish-level Census tables)" wording (Census Day, not mid-year) and adds the household/dwelling figure the mid-year release doesn't provide.

**3. Do NOT silently overwrite `config/geography.yaml`'s existing `population_2021_census: 4498` field** (spec's own figure) — same precedent as Q-007's area figure: the spec wins when the plan and spec conflict on values it explicitly states, and CLAUDE.md forbids editing the spec itself. The new, real, computed figures live in `data/processed/geography/population_denominators.csv` with their own provenance rows instead, so all three are visible and traceable rather than one silently replacing another.

**4. Scope household/dwelling counts to Cholsey/Moulsford only**, same as ADR-0004 — no equivalent direct national release exists for households at parish level (checked), so getting a comparator's household count would need repeating P1.4's OA lookup for each of the 8 comparators. Logged as part of the same "comparator-level apportionment" backlog item as ADR-0004's (STATUS.md).

## Consequences

- `data/processed/geography/population_denominators.csv` has 13 rows: 9 `population_mid2021_estimate` (all confirmed areas), 2 `population_census_day_oa_bestfit` and 2 `households_census_day_oa_bestfit` (Cholsey + Moulsford only), each with full provenance.
- The ~2.4% gap between spec's 4,498 and both independently-computed real figures (4,404 mid-year, 4,390 census-day) is not a new open question by itself — like Q-007, it doesn't block anything at this phase (Phase 3's area-based % calculations is where a wrong denominator would actually bite), and the pattern (spec figure kept as-is, real figure recorded alongside with a flag) is already established. If Phase 3 needs to pick one, both Q-007 and this ADR should be read together.
- Comparator household/dwelling denominators remain a backlog item (same one ADR-0004 created), not scheduled to a phase yet.
- P2.8 ("Fetcher: ONS population and dwellings, if not fully covered in P1.6") is now largely superseded for population by this ADR's mid-2021 estimate; household/dwelling counts and any later-vintage refresh (mid-2022+) remain P2.8's to build as a proper re-fetchable Phase 2 fetcher.
