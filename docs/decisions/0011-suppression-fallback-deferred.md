# 0011. `flag=suppression_fallback` is defined but not yet exercised — defer building it until a real suppressed row is hit

- **Status:** Accepted (technical/methodology decision confirming an existing scope boundary, not a new spec/scope/stack decision — P3.4's energy metric already scoped this out when it was built; this ADR just records that decision formally, since Phase 3's exit criteria expects "method ADRs exist for... suppression fallback" and none existed).
- **Date:** 2026-10-02
- **Deciders:** Phase 3 exit-criteria review (this firing)
- **Related:** P2.6 (`fetch/desnz_postcode_energy.py`); P3.4 (`metrics/energy.py`); `validate/metrics_schema.py`'s `FLAGS` set; development-plan.md spec §3, plan risk R4

## Context

`validate/metrics_schema.py` defines four valid `flag` values: `none`, `parish_estimate`, `suppression_fallback`, `partial_coverage`. Three are real, exercised flags in `metrics.csv` today (`parish_estimate` for energy/MCS rows with sub-1.0 apportionment weights, `partial_coverage` for the national canopy row, ADR-0009). `suppression_fallback` has never been set on any row, by any metric, in any firing so far.

The flag exists because of a real DESNZ data-quality behaviour, already documented in `fetch/desnz_postcode_energy.py`'s own module docstring: DESNZ suppresses a postcode's row if it has fewer than 5 meters, if its top 2 meters make up over 90% of consumption, or if a meter's annual consumption is under 100 kWh (excluded entirely). So a missing postcode in DESNZ's postcode-level release is not necessarily zero consumption — a genuine gap this project anticipated (spec §3, plan risk R4) by building `fetch_desnz_postcode_energy` in P2.6 specifically to allow a postcode-level cross-check against the LSOA-level figures metric 3/4 actually use.

That cross-check was never built. `metrics/energy.py`'s own docstring (written during P3.4) says why: `fetch.desnz_postcode_energy` only fetches whole OX10-outcode totals, which cover Wallingford and other neighbouring postcodes as well as Cholsey — not directly comparable to a single parish's figure without a postcode-to-parish mapping, which doesn't exist. P3.4 explicitly scoped this out as "at most an order-of-magnitude plausibility check, not a real cross-check," and moved on.

Separately, and more fundamentally: the metrics this project actually builds (metrics 3/4, electricity and gas) are computed from **LSOA-level** DESNZ data (`fetch.desnz_lsoa_energy`), not postcode-level data. DESNZ's LSOA-level releases have their own suppression rule (small-number rounding, not full-row exclusion) and — critically — Cholsey's three contributing LSOAs (E01028619, E01035751, E01035752) have never actually hit a suppressed/missing row in any live fetch this project has run (verified across every firing's real `build_metrics_csv.py` output to date). So `suppression_fallback` is currently a flag for a scenario that is real in principle (an LSOA could be suppressed) but has not yet occurred in practice for any area this project tracks.

## Decision

**Defer building the postcode-level suppression-fallback cross-check.** `fetch.desnz_postcode_energy` (P2.6) stays built and documented — it's real, tested, working code, kept for the day it's needed — but no caller in `metrics/energy.py` or `scripts/build_metrics_csv.py` invokes it, and `flag=suppression_fallback` stays unexercised, because:

1. No LSOA this project actually uses (subject, 8 comparators, or any future addition) has ever come back suppressed/missing from a live DESNZ LSOA-level fetch — there's nothing to fall back *from* yet.
2. The postcode-level data that exists (`desnz_postcode_energy`) can't cleanly answer "is LSOA X suppressed" without a postcode-to-parish/LSOA mapping this project doesn't have and hasn't needed for anything else — building that mapping purely to support a fallback path with no current trigger would be speculative work (CLAUDE.md: don't build for hypothetical requirements).
3. If an LSOA genuinely does come back missing/suppressed in a future live fetch, `cholsey_pipeline.fetch.desnz_lsoa_energy.read_lsoa_energy`/`fetch_lsoa_energy` would surface that as a real, visible gap (fewer rows than expected LSOAs) rather than silently mis-reporting a zero — this project's existing validate/row-count checks already catch that class of problem; they just haven't needed to, yet.

**When this should be revisited:** the first time a live `fetch_lsoa_energy` call returns fewer records than Cholsey's (or a comparator's) known contributing LSOA count. At that point, build the actual fallback: use `desnz_postcode_energy`'s OX10 figure as an order-of-magnitude sanity check (not a precise substitute, per the existing `metrics/energy.py` docstring's own caveat), set `method` to reflect the degraded precision, and set `flag=suppression_fallback` with a `flag_note` explaining which LSOA was missing and why. Until then, this ADR documents the gap as understood and deliberately deferred, not overlooked.

## Consequences

- Phase 3's exit criteria ("method ADRs exist for... suppression fallback") is satisfied by this ADR's existence, not by new code — the method *is* "not currently applicable; see ADR-0011 for the trigger condition."
- `validate/metrics_schema.py`'s `FLAGS` set keeps `suppression_fallback` as a valid value (no schema change) — it's a real, defined flag for a real, anticipated (if not-yet-occurred) scenario, not dead code to remove.
- No change to any existing module. `fetch/desnz_postcode_energy.py`, `metrics/energy.py`, and `scripts/build_metrics_csv.py` are unchanged by this ADR.
- A future session hitting a real suppressed LSOA should update this ADR's Status (Accepted → Superseded, pointing at whatever new ADR documents the actual fallback built) rather than silently adding ad hoc handling.
