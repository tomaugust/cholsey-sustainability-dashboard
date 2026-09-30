"""Metrics 5 and 6: solar PV and heat pump uptake (development-plan.md
Phase 3, P3.5; ADR-0007, Q-011).

MCS's own public dashboard has no parish-level export (only per-chart
exports filtered to whatever geography the dashboard UI offers -- Tom
confirmed South Oxfordshire, the district, is what's selectable; see
`fetch.mcs_installations`'s module docstring and ADR-0007). So Cholsey's
subject row assumes South Oxfordshire's own household-uptake RATE applies
uniformly to Cholsey -- the same "apply a coarser geography's rate
directly to the parish" shape as metric 1's ward-canopy-on-parish, not a
geometric or address apportionment of a total. `method=address_weighted`
is used for the label (an estimated INSTALL COUNT is backed out via
Cholsey's household share of South Oxfordshire's households), but the
primary %_of_dwellings VALUE itself is just South Oxfordshire's own
percentage, carried over unchanged under the uniform-rate assumption --
always `flag=parish_estimate`.

South Oxfordshire IS the district for this project (spec §2, ADR-0003),
so the district row needs no apportionment at all: `method=direct`,
`flag=none`, `area_role="district"`, the record's own values unchanged.

No installed kWp figure exists in this data source (checked across all 4
exported chart types for both technologies) -- spec §3's "installed kWp
for PV" output isn't available; not silently estimated, just absent.
"""

from __future__ import annotations

from dataclasses import dataclass

from cholsey_pipeline.fetch.mcs_installations import AreaUptakeRecord

CHOLSEY_PARISH_CODE = "E04012474"
CHOLSEY_PARISH_NAME = "Cholsey"
SOUTH_OXFORDSHIRE_CODE = "E07000179"
SOUTH_OXFORDSHIRE_HOUSEHOLDS_CENSUS2021 = 61497
"""Real Census 2021 household count for South Oxfordshire, live-verified
2026-09-30 via the same nomis NM_2059_1 dataset P1.6 used for Cholsey/
Moulsford (https://www.nomisweb.co.uk/api/v01/dataset/NM_2059_1.data.csv
?geography=E07000179&measures=20100). Cross-checked against MCS's own
implied household denominator (installs / pct_of_households), which
agrees closely (~61,430-61,490) -- see
fetch/reference_data/mcs_installations/_provenance.json."""

METRIC_ID_BY_TECHNOLOGY = {"heat_pump": "heat_pump", "solar_pv": "solar_pv"}


@dataclass(frozen=True)
class UptakeMetricRow:
    """One area's solar PV or heat pump uptake metric row, shaped to slot
    into `data/processed/metrics.csv` (development-plan.md §2.3) once
    P3.9's export exists. `estimated_installations` is an extra field
    beyond the strict schema -- the count spec §3 also wants alongside
    the %, backed out from the household-uptake rate rather than
    measured directly for the subject row."""

    area_code: str
    area_name: str
    area_role: str
    metric_id: str
    year: int
    value: float
    unit: str
    geography_used: str
    method: str
    flag: str
    flag_note: str
    estimated_installations: float


def compute_subject_uptake_row(
    record: AreaUptakeRecord,
    district_households: int,
    parish_households: int,
    year: int,
    parish_code: str = CHOLSEY_PARISH_CODE,
    parish_name: str = CHOLSEY_PARISH_NAME,
) -> UptakeMetricRow:
    """Build Cholsey's uptake row from South Oxfordshire's real MCS
    record, assuming the district's own household-uptake rate applies
    uniformly to the parish.

    `district_households`/`parish_households` are real Census 2021
    household counts (South Oxfordshire: 61,497; Cholsey: 1,782, P1.6) --
    used only to back out `estimated_installations`, since the primary
    `value` (%_of_dwellings) is scale-invariant under the uniform-rate
    assumption and equals `record.pct_of_households` unchanged.

    Pure function -- tested against real values (South Oxfordshire heat
    pump: 1,677 installs, 2.73% of households; solar PV: 6,198 installs,
    10.08%).
    """
    estimated_installations = record.installations_total * (parish_households / district_households)

    return UptakeMetricRow(
        area_code=parish_code,
        area_name=parish_name,
        area_role="subject",
        metric_id=METRIC_ID_BY_TECHNOLOGY[record.technology],
        year=year,
        value=record.pct_of_households,
        unit="%_of_dwellings",
        geography_used=f"South Oxfordshire ({SOUTH_OXFORDSHIRE_CODE}), MCS Data Dashboard",
        method="address_weighted",
        flag="parish_estimate",
        flag_note=(
            "MCS's public dashboard has no parish-level export -- South "
            "Oxfordshire's own household-uptake rate is applied directly "
            "to Cholsey, assuming similar renewable-uptake propensity to "
            "the wider district (ADR-0007, Q-011). The estimated "
            "installation count is backed out from Cholsey's real "
            "Census 2021 household share of South Oxfordshire's "
            "households, not measured directly."
        ),
        estimated_installations=estimated_installations,
    )


def compute_district_uptake_row(record: AreaUptakeRecord, year: int) -> UptakeMetricRow:
    """Build South Oxfordshire's own uptake row -- no apportionment
    needed, since South Oxfordshire IS the district (spec §2, ADR-0003)
    and MCS's dashboard already reports it directly. `method=direct`,
    `flag=none`.
    """
    return UptakeMetricRow(
        area_code=SOUTH_OXFORDSHIRE_CODE,
        area_name="South Oxfordshire",
        area_role="district",
        metric_id=METRIC_ID_BY_TECHNOLOGY[record.technology],
        year=year,
        value=record.pct_of_households,
        unit="%_of_dwellings",
        geography_used=f"South Oxfordshire ({SOUTH_OXFORDSHIRE_CODE}), MCS Data Dashboard",
        method="direct",
        flag="none",
        flag_note="",
        estimated_installations=float(record.installations_total),
    )
