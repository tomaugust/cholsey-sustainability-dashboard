# 0004. P1.5 apportionment weight methodology (NSUL source, whole-address counts, scope)

- **Status:** Accepted (technical implementation choice within an already-unblocked task, not a spec/scope/stack decision — CLAUDE.md's rule that those go to the project lead as Proposed doesn't apply here).
- **Date:** 2026-09-28
- **Deciders:** Phase 1 (P1.5) implementation
- **Related:** P1.5; development-plan.md §3 Phase 1; `pipeline/src/cholsey_pipeline/geography/weights.py`; `pipeline/scripts/build_weights_csv.py`; `config/sources.yaml`'s `ons_nsul_uprn_lookup` entry; `data/processed/geography/weights.csv`

## Context

P1.5 asks for, per (parish, LSOA) pair, "an address-count weight: the share of the LSOA's residential UPRNs that fall inside the parish, from ONSUD", plus an area weight as a cross-check, and the equivalent (parish, ward) area weight for the ward-level canopy dataset.

Three implementation questions came up that the plan doesn't answer directly:

1. **ONSUD is a ~40 million row, UK-wide file.** Do we need the whole thing, or is there a smaller equivalent for just our area?
2. **"Residential UPRNs"** — does the dataset we use actually distinguish residential from other property types?
3. **Scope** — P1.5's wording ("for every (parish, LSOA) pair") could mean Cholsey only, or Cholsey plus all 8 comparators. P1.3/P1.4 both scoped their work to Cholsey (and, for P1.4, Cholsey's immediate neighbour Moulsford where a shared LSOA required it) — `config/geography.yaml`'s `lsoas:` section only lists Cholsey's overlapping LSOAs, no comparator ones.

## Decision

**1. Use the ONS National Statistics UPRN Lookup (NSUL, January 2024) instead of the full ONSUD.** NSUL already assigns every UPRN to a 2021 Output Area, and P1.4 already has a verified OA→parish best-fit lookup — so NSUL doesn't introduce a different assignment method, it just gives an address count to weight by, within OAs whose parish membership is already known. NSUL is still only queryable as a bulk CSV-in-zip download (no FeatureServer, unlike the OA lookups), but split by GB region — the South East (SE) region file (~1.6GB uncompressed) covers Cholsey, so only ~1/11th of the national file needed downloading, filtered immediately to the 15 relevant OAs and discarded (not committed — `data/raw/` is gitignored, re-fetchable).

**2. Use whole-address (all use classes) counts, not residential-only.** NSUL carries no property-type/classification field to filter on. A genuine residential/non-residential split requires AddressBase Premium, a paid OS/GeoPlace product — out of scope for a zero-cost project (spec's own framing). This is a real, documented deviation from the plan's literal wording ("residential UPRNs"), not a silent one: flagged in `weights.py`'s module docstring, the `ons_nsul_uprn_lookup` source entry, and `weights.csv`'s `method` column for every address_count row.

**3. Scope P1.5 to Cholsey (and Moulsford, only because they share LSOA `E01035752`)** — the same footprint P1.4 already established. Comparator parishes' own LSOA/ward apportionment is not computed here. This matches the precedent: `config/geography.yaml`'s `lsoas:` section, `comparators.py` and `lsoa_overlap.py` are all Cholsey-scoped, and nothing before Phase 3 (area-based % calculations, "not yet reached") actually consumes a comparator's own LSOA apportionment yet.

## Consequences

- `data/processed/geography/weights.csv` has address_count and area_cross_check rows for Cholsey/Moulsford's shared LSOAs, and an area row for Cholsey's ward, all with full provenance (source, URL, vintage, retrieved_at, method, flag).
- **Real finding worth flagging forward:** the split LSOA `E01035752`'s address-count weight (Cholsey ≈0.583) and area weight (Cholsey ≈0.457) diverge by more than 12 percentage points — the Cholsey-side addresses are measurably denser than the Moulsford-side ones. Phase 2/3 should apportion LSOA-level consumption data (electricity/gas) using the **address-count weight**, not the area weight, since consumption is a per-meter (i.e. per-address) quantity — the area weight is a cross-check only, exactly as the plan specifies, not an interchangeable alternative.
- **New task for whoever picks up comparator-level apportionment** (likely needed before Phase 3's benchmark rows can use LSOA-sourced metrics for comparators, not just Cholsey): repeat P1.4 (OA→parish/LSOA membership) and P1.5 (this ADR's method) for each of the 8 comparators. Logged as backlog item in STATUS.md rather than done speculatively here, per CLAUDE.md's "don't jump ahead of the current phase's exit criteria" and "don't add features beyond what the task requires."
- If AddressBase Premium ever becomes available to the project (e.g. via a council/parish council licence), `weights.py`'s `compute_address_weights` can be re-run with residential-filtered counts without any change to its interface — only the input `oa_uprn_counts` dict would need to come from a different source.
