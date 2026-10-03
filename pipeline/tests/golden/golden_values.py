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

## Canopy (10.4%)

Forest Research's `UK_Ward_Canopy_Cover` raw response
(`data/raw/forest_research_canopy/ward_canopy_response.json`) has, for
Cholsey's own ward (E05009737, the Dec 2018 edition -- ADR-0006):
`{"wardcode": "E05009737", "percancov": 10.4, "survyear": 2021, ...}`.
Cholsey parish lies wholly inside this one ward (P1.5's own area weight
for this ward is 1.0 -- there is nothing else to blend), so the parish
value is this raw field, unchanged. No arithmetic beyond "read the
field" -- the golden check here is that nothing downstream silently
substitutes a different ward, year, or field.

## Greenspace (20.2293007039057 m2/resident)

Independently re-derived 2026-10-03 via `geography.boundaries
.fetch_boundary("parish_bfc", codes=["E04012474"])` (Cholsey's real BFC
polygon, area 15,910,109.476062458 m2 -- matches Q-007's live-verified
~15.91 km2) and `fetch.os_open_greenspace.fetch_greenspace_sites`
(reusing the already-cached raw `opgrsp_gb.zip`, no live GB-wide
re-download), then `geopandas.clip` against the parish polygon and
summing `.geometry.area` for every site whose `function` is one of
metric 2's accessible types (ADR-0008: Public Park Or Garden, Playing
Field, Play Space, Other Sports Facility, Amenity - Residential Or
Business, Tennis Court, Bowling Green) -- this is the same fetch-layer
call `_build_greenspace_rows` makes, but the clip/filter/sum here is
written out independently in this module rather than calling
`metrics.greenspace.compute_subject_greenspace_row`.

Real result: accessible area = 89,089.84030000071 m2. Population
denominator = 4,404 (the mid-2021 parish estimate, `config/geography
.yaml`'s `population_mid2021_estimate` for E04012474).

    89089.84030000071 / 4404 = 20.2293007039057 m2/resident

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
    "greenspace": 20.2293007039057,
    "electricity": 3682.271410334187,
    "gas": 11000.805698360531,
    "heat_pump": 2.73,
    "solar_pv": 10.08,
}
"""Cholsey's (area_code E04012474, area_role "subject") golden value per
metric_id, hand-worked above. `test_golden_values.py` compares each one
against the real, latest-year row in `data/processed/metrics.csv`."""
