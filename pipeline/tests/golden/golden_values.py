"""Hand-worked golden values for Cholsey's latest year, per core metric
(development-plan.md Phase 3, P3.10 -- "Tests of success": "for
Cholsey's latest year, a hand-computed value per metric ... equals the
pipeline value").

Each value below is independently re-derived from the real RAW source
data (the same raw files `cholsey_pipeline.fetch.*` downloads), using
plain arithmetic worked out in this module's own docstrings -- not by
calling `cholsey_pipeline.metrics.*`'s compute functions, so a bug
introduced into those functions (a flipped weight, the wrong
denominator, an off-by-one LSOA) would show up as a mismatch here
instead of being silently "confirmed" by re-running the same buggy code.
`test_golden_values.py` asserts each one against the real, committed
`data/processed/metrics.csv`.

**Known limitations** (PR review, 2026-10-03): these are snapshots of a
one-off manual re-derivation against whatever `data/raw/*` happened to be
on disk at the time (`data/raw/` itself isn't committed, so CI does not
and cannot re-derive these numbers from raw bytes -- it only checks that
`metrics.csv`'s committed value still matches the number recorded here).
Each check also only covers Cholsey's SUBJECT row for its LATEST year --
it would not have caught the real 2010-2014 LSOA-code-mismatch bug this
same review found (see ADR-0011's addendum and `build_metrics_csv.py`'s
`_build_energy_rows_for_fuel`), since that only affects earlier years.
And three of the six metrics (canopy, heat_pump, solar_pv) involve no
arithmetic at all -- they only confirm a raw field is passed through
unchanged, which would not have caught the MCS `method` mislabeling bug
this review also found (see `metrics/mcs.py`): the %-value itself was
unaffected by that bug, only its method label was wrong, and a value-only
golden check can't see a label-only bug.

## Canopy (10.4%)

Forest Research's `UK_Ward_Canopy_Cover` raw response
(`data/raw/forest_research_canopy/ward_canopy_response.json`) has, for
Cholsey's own ward (E05009737, the Dec 2018 edition -- ADR-0006):
`{"wardcode": "E05009737", "percancov": 10.4, "survyear": 2021, ...}`.
Only one ward contributes (there's nothing else to blend), so the parish
value is this raw field, unchanged, regardless of the exact weight --
`compute_subject_canopy_row`'s own docstring confirms this. (The real
weight for this specific Dec 2018 ward edition is 99.4%, not 100% --
`weights.csv`'s own 1.0 figure is computed against the CURRENT, Dec 2020
ward boundary; ADR-0006 investigated and recorded the real 99.4% match
against the actual, older edition Forest Research uses. This doesn't
change the value here, only the flag_note's wording -- see the PR review
correction, 2026-10-03.) No arithmetic beyond "read the field" -- the
golden check here is that nothing downstream silently substitutes a
different ward, year, or field.

## Greenspace (19.550428610354274 m2/resident)

Independently re-derived 2026-10-03 via `geography.boundaries
.fetch_boundary("parish_bfc", codes=["E04012474"])` (Cholsey's real BFC
polygon, area 15,910,109.476062458 m2 -- matches Q-007's live-verified
~15.91 km2) and `fetch.os_open_greenspace.fetch_greenspace_sites`
(reusing the already-cached raw `opgrsp_gb.zip`, no live GB-wide
re-download), then `geopandas.clip` against the parish polygon, filtering
to every site whose `function` is one of metric 2's accessible types
(ADR-0008: Public Park Or Garden, Playing Field, Play Space, Other Sports
Facility, Amenity - Residential Or Business, Tennis Court, Bowling
Green), and merging them with `.union_all().area` before summing -- this
is the same fetch-layer call `_build_greenspace_rows` makes, but the
clip/filter/merge here is written out independently in this module
rather than calling `metrics.greenspace.compute_subject_greenspace_row`.

**Correction (2026-10-03, phase-end PR review)**: the first version of
this golden check used a plain `.geometry.area.sum()` instead of
`.union_all().area` before summing, which double-counts real overlapping
site polygons (e.g. a Play Space drawn inside a Playing Field) -- giving
89,089.84 m2 instead of the real, merged 86,100.09 m2. Because this
golden check independently reran the SAME buggy aggregation the pipeline
itself used at the time, it matched the (also wrong) committed
`metrics.csv` value and didn't catch the bug -- a real limitation of a
golden check that re-derives a value using the same aggregation method
being tested, rather than an independently-reasoned one. Both this
module and `metrics/greenspace.py`/`scripts/build_metrics_csv.py` now use
`.union_all()`.

Real result: accessible area = 86,100.0876 m2 (merged). Population
denominator = 4,404 (the mid-2021 parish estimate, `config/geography
.yaml`'s `population_mid2021_estimate` for E04012474).

    86100.0876 / 4404 = 19.550428610354274 m2/resident

## Electricity (3682.271410334187 kWh/meter/year)

DESNZ's real 2024 LSOA-level electricity sheet
(`data/raw/desnz_lsoa_energy/electricity/lsoa_electricity.xlsx`, sheet
"2024") gives, for Cholsey's three contributing LSOAs:

| LSOA | meters | total consumption (kWh) | P1.5 address weight |
| --- | --- | --- | --- |
| E01028619 | 788 | 2,945,410.456923497 | 1.0 (wholly inside) |
| E01035751 | 784 | 2,613,339.550978142 | 1.0 (wholly inside) |
| E01035752 | 638 | 2,743,265.932655738 | 0.583234 (shared with Moulsford) |

`metrics.energy`'s own documented method is Sigma/Sigma (weighted sum of
consumption over weighted sum of meters, not an average of averages):

    weighted_meters = 788*1.0 + 784*1.0 + 638*0.583234 = 1944.103292
    weighted_consumption = 2945410.456923497*1.0 + 2613339.550978142*1.0
                          + 2743265.932655738*0.583234
                        = 7158715.970868176
    mean = 7158715.970868176 / 1944.103292 = 3682.271410334187

## Gas (11000.805698360531 kWh/meter/year)

Same three LSOAs, same weights, from the real 2024 LSOA-level gas sheet
(`data/raw/desnz_lsoa_energy/gas/lsoa_gas.xlsx`, sheet "2024"):

| LSOA | meters | total consumption (kWh) |
| --- | --- | --- |
| E01028619 | 711 | 8,218,199.714451234 |
| E01035751 | 735 | 7,307,477.390840255 |
| E01035752 | 510 | 6,264,501.60481628 |

    weighted_meters = 711 + 735 + 510*0.583234 = 1743.4493400000001
    weighted_consumption = 8218199.714451234 + 7307477.390840255
                          + 6264501.60481628*0.583234
                        = 19179347.43427491
    mean = 19179347.43427491 / 1743.4493400000001 = 11000.805698360531

## Heat pump uptake (2.73 %_of_dwellings)

MCS's own committed export
(`fetch/reference_data/mcs_installations/south_oxfordshire/heat_pump
/installation_uptake.csv`): "South Oxfordshire,1677,2.73%". Per ADR-0007,
Cholsey's subject row applies South Oxfordshire's own rate unchanged (no
arithmetic -- the uniform-rate assumption makes the %-of-dwellings value
itself scale-invariant). Golden check: the committed CSV's own percentage
is what ends up in `metrics.csv`, unchanged by any later step.

## Solar PV uptake (10.08 %_of_dwellings)

Same pattern, `.../solar_pv/installation_uptake.csv`:
"South Oxfordshire,6198,10.08%".
"""

from __future__ import annotations

GOLDEN_VALUES: dict[str, float] = {
    "canopy": 10.4,
    "greenspace": 19.550428610354274,
    "electricity": 3682.271410334187,
    "gas": 11000.805698360531,
    "heat_pump": 2.73,
    "solar_pv": 10.08,
}
"""Cholsey's (area_code E04012474, area_role "subject") golden value per
metric_id, hand-worked above. `test_golden_values.py` compares each one
against the real, latest-year row in `data/processed/metrics.csv`."""
