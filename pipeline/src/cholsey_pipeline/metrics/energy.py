"""Metrics 3 and 4: domestic electricity and gas consumption
(development-plan.md Phase 3, P3.4).

LSOA-level meter counts and total consumption (`fetch.desnz_lsoa_energy`)
are apportioned onto the parish using the real address-count weights P1.5
computed (`data/processed/geography/weights.csv`'s `address_count` rows,
NSUL UPRN-in-parish shares) -- `method=address_weighted`, matching the
plan's own wording. The parish's mean kWh/meter is the weighted sum of
consumption divided by the weighted sum of meters (Sigma / Sigma, not an
average of averages), so an LSOA contributing more of the parish's meters
also contributes proportionally more to the mean.

Electricity and gas stay as two separate metric_ids (different units,
different sources, different valid ranges in metrics.yaml) even though
the UI combines them into one "Home energy" tile (Q-002).

Real Cholsey finding (verified live 2026-09-30, 2024 data, the latest
year DESNZ has published): Cholsey spans 3 LSOAs. Two
(E01028619, E01035751) are wholly inside Cholsey (address weight 1.0
each, from P1.5/ADR-0004) -- their meters and consumption belong to
Cholsey outright, no apportionment assumption needed. The third
(E01035752) is split with Moulsford, 58.3% of its addresses in Cholsey --
apportioning that LSOA's meters/consumption by this weight assumes each
address's consumption is close to that LSOA's own mean, an assumption
that doesn't apply to the two wholly-contained LSOAs. So this metric is
only flagged `parish_estimate` when at least one contributing LSOA has a
weight below 1.0 -- not unconditionally, unlike metric 1 (every canopy
row is ward-derived, so always an estimate).

Postcode-level cross-check (spec's own "cross-check against a
postcode-level sum"): `fetch.desnz_postcode_energy` only fetches whole
OX10-outcode totals (P2.6), which cover Wallingford and other
neighbouring postcodes as well as Cholsey -- not directly comparable to a
single parish's figure without a postcode-to-parish mapping, which
doesn't exist yet. Scoped out of this first pass (see the P3.4 worklog
"Not done" section); the OX10 total is at most an order-of-magnitude
plausibility check, not a real cross-check.

District (South Oxfordshire, E07000179) and national (England,
E92000001) rows don't need apportionment at all -- DESNZ's separate
regional/local-authority release (`fetch_regional_la_energy`, P2.5)
already publishes both directly. `compute_area_energy_row` builds these,
`method=direct`, `flag=none`. Real finding while wiring this up
(2026-09-30): the regional/LA gas sheet has a genuinely different column
layout than electricity's (an extra "Notes" column, no Standard/E7
meter split, header one row lower) -- P2.5 only ever verified the
electricity sheet live, so this was a latent bug until P3.4 tried to
fetch gas district/national data for real. Fixed in
`fetch.desnz_lsoa_energy` (per-fuel header row and column lookups), not
worked around here.
"""

from __future__ import annotations

from dataclasses import dataclass

from cholsey_pipeline.fetch.desnz_lsoa_energy import AreaEnergyRecord, Fuel, LsoaEnergyRecord

CHOLSEY_PARISH_CODE = "E04012474"
CHOLSEY_PARISH_NAME = "Cholsey"

UNIT_BY_FUEL: dict[Fuel, str] = {
    "electricity": "kWh/meter/year",
    "gas": "kWh/meter/year",
}


@dataclass(frozen=True)
class EnergyMetricRow:
    """One area's electricity or gas consumption metric row, shaped to
    slot into `data/processed/metrics.csv` (development-plan.md §2.3)
    once P3.9's export step exists. `total_mwh` is an extra field beyond
    the strict schema, kept for the detail page's "total MWh" figure
    (spec §3 metrics 3/4 want both mean kWh/meter and total MWh)."""

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
    total_mwh: float


def compute_subject_energy_row(
    records: list[LsoaEnergyRecord],
    lsoa_weights: dict[str, float],
    parish_code: str = CHOLSEY_PARISH_CODE,
    parish_name: str = CHOLSEY_PARISH_NAME,
) -> EnergyMetricRow:
    """Build the electricity/gas metric row for a parish from its
    contributing LSOAs' real DESNZ records and their real address-count
    weights (P1.5's `weights.csv`, `weight_type=address_count`).

    `records` must all share the same `fuel` and `year` (a single fetch's
    output, already filtered to the parish's contributing LSOA codes --
    e.g. `fetch_lsoa_energy(fuel, [year], lsoa_codes={...})`).
    `lsoa_weights` maps each record's `lsoa_code` to its real address-
    count weight (the share of that LSOA's addresses falling in the
    parish); every record's LSOA must have an entry.

    Pure function -- tested against real values (Cholsey's 3 LSOAs, 2024:
    weighted mean 3,682.27 kWh/meter electricity, 11,000.81 kWh/meter
    gas).
    """
    if not records:
        raise ValueError("compute_subject_energy_row requires at least one record")
    fuel = records[0].fuel
    year = records[0].year
    if any(r.fuel != fuel or r.year != year for r in records):
        raise ValueError("all records must share the same fuel and year")

    weighted_meters = 0.0
    weighted_kwh = 0.0
    geography_parts = []
    any_partial = False
    for r in records:
        if r.lsoa_code not in lsoa_weights:
            raise ValueError(f"LSOA '{r.lsoa_code}' has a record but no entry in lsoa_weights")
        weight = lsoa_weights[r.lsoa_code]
        if weight < 1.0:
            any_partial = True
        weighted_meters += r.number_of_meters * weight
        weighted_kwh += r.total_consumption_kwh * weight
        geography_parts.append(f"{r.lsoa_code} ({weight:.1%})")

    value = weighted_kwh / weighted_meters
    total_mwh = weighted_kwh / 1000

    if any_partial:
        flag = "parish_estimate"
        flag_note = (
            f"Address-weighted sum across {len(records)} LSOAs (P1.5 NSUL "
            "address-count weights). At least one contributing LSOA is "
            "only partly in the parish, so that LSOA's meters/consumption "
            "are apportioned assuming its addresses inside and outside "
            "the parish consume similarly on average -- an estimate for "
            "that portion, not a direct measurement."
        )
    else:
        flag = "none"
        flag_note = ""

    return EnergyMetricRow(
        area_code=parish_code,
        area_name=parish_name,
        area_role="subject",
        metric_id=fuel,
        year=year,
        value=value,
        unit=UNIT_BY_FUEL[fuel],
        geography_used=f"{len(records)} LSOAs (address-weighted): " + ", ".join(geography_parts),
        method="address_weighted",
        flag=flag,
        flag_note=flag_note,
        total_mwh=total_mwh,
    )


def compute_area_energy_row(record: AreaEnergyRecord, area_role: str) -> EnergyMetricRow:
    """Build a district/national electricity or gas metric row directly
    from a DESNZ regional/local-authority release record
    (`fetch.desnz_lsoa_energy.fetch_regional_la_energy`) -- no
    apportionment needed, since DESNZ already publishes local authority
    and country-level totals directly. `method=direct`, `flag=none`.

    `area_role` must be `"district"` or `"comparator"`'s national
    equivalent, `"national"` -- this function doesn't decide which,
    since a caller applying it to South Oxfordshire vs England needs to
    say so explicitly rather than guessing from the area_code.

    Pure function -- tested against real values (South Oxfordshire and
    England, 2024, both fuels, live-verified 2026-09-30).
    """
    total_kwh = record.total_domestic_consumption_gwh * 1_000_000
    total_meters = record.number_of_domestic_meters_thousands * 1_000
    value = total_kwh / total_meters
    total_mwh = record.total_domestic_consumption_gwh * 1_000

    return EnergyMetricRow(
        area_code=record.area_code,
        area_name=record.area_name,
        area_role=area_role,
        metric_id=record.fuel,
        year=record.year,
        value=value,
        unit=UNIT_BY_FUEL[record.fuel],
        geography_used=f"DESNZ regional/local authority release ({record.area_name})",
        method="direct",
        flag="none",
        flag_note="",
        total_mwh=total_mwh,
    )
