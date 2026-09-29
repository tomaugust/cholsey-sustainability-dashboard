"""Compute apportionment weights that move LSOA- and ward-level datasets
onto parish polygons.

development-plan.md Phase 1, P1.5: "For every (parish, LSOA) pair, compute
an address-count weight: the share of the LSOA's residential UPRNs that
fall inside the parish, from ONSUD. Also compute an area weight as a
cross-check. Do the same for (parish, ward) area weights for canopy."

Two different apportionment DIRECTIONS are needed, because the two source
datasets each aggregate at a different level relative to the parish:

- LSOA-level data (electricity/gas, Phase 2) must be SPLIT across the
  parishes an LSOA overlaps -> the weight is the *LSOA's* share that falls
  in each parish (`compute_address_weights`, `compute_lsoa_area_weights`).
- Ward-level data (canopy, Phase 2) must be COMBINED across the wards a
  parish spans -> the weight is the *parish's* own area that falls in each
  ward (`compute_parish_ward_weights`). Cholsey happens to sit wholly
  inside one ward (verified live while building this module: the "Cholsey"
  ward E05011701 is ~4x the parish's area and fully contains it), so that
  weight is trivially 1.0 for Cholsey today, but the function does the
  general computation in case a future comparator spans more than one ward.

Address-count source note: this project uses the ONS National Statistics
UPRN Lookup (NSUL), not the full ONSUD, because NSUL is a much smaller
per-region download (~1.6GB for South East vs ONSUD's full national
attribute set) and both already assign each UPRN to its 2021 Output Area
via the same "best fit" methodology P1.4 already relies on for OA->parish
-- so using NSUL doesn't introduce a different assignment method, just
counts addresses within OAs already known to best-fit Cholsey or a
neighbour. NSUL has no residential/non-residential flag, so the counts
this module works with are whole-address (all use classes) counts, not
residential-only as the plan's wording literally says -- a residential
split needs AddressBase Premium (a paid product), out of scope. See
ADR-0004 and the P1.5 worklog entry.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import geopandas as gpd


@dataclass(frozen=True)
class AddressWeight:
    """One (LSOA, parish) pair's address-count-based apportionment weight."""

    lsoa_code: str
    lsoa_name: str
    parish_code: str
    uprn_count: int
    """UPRNs in this LSOA whose OA best-fits `parish_code`."""
    lsoa_total_uprns: int
    """UPRNs across every OA of this LSOA, regardless of parish."""

    @property
    def weight(self) -> float:
        if self.lsoa_total_uprns == 0:
            return 0.0
        return self.uprn_count / self.lsoa_total_uprns


def compute_address_weights(
    oa_to_parish_rows: list[dict[str, Any]],
    oa_to_lsoa_rows: list[dict[str, Any]],
    oa_uprn_counts: dict[str, int],
) -> list[AddressWeight]:
    """Compute the address-count weight of every (LSOA, parish) pair that
    appears in `oa_uprn_counts`.

    `oa_to_parish_rows`/`oa_to_lsoa_rows` are ArcGIS-style
    `{"attributes": {...}}` rows, exactly as
    `geography.lsoa_overlap.find_overlapping_lsoas` consumes them.
    `oa_uprn_counts` maps an OA21CD to its UPRN count (from NSUL or
    equivalent). Every OA in `oa_uprn_counts` must have an entry in both
    lookup row lists.

    Returns one AddressWeight per (LSOA, parish) pair with at least one
    UPRN, sorted by LSOA code then descending weight -- for an LSOA split
    between N parishes, its weights sum to 1.0 (up to any OAs missing from
    `oa_uprn_counts`, which callers should avoid by ensuring the OA sets
    passed to `lsoa_overlap.find_overlapping_lsoas` and here match).
    """
    oa_to_lsoa: dict[str, tuple[str, str]] = {}
    for row in oa_to_lsoa_rows:
        attrs = row["attributes"]
        oa_to_lsoa[attrs["OA21CD"]] = (attrs["LSOA21CD"], attrs["LSOA21NM"])

    oa_to_parish: dict[str, str] = {}
    for row in oa_to_parish_rows:
        attrs = row["attributes"]
        oa_to_parish[attrs["OA21CD"]] = attrs["PARNCP24CD"]

    per_pair: dict[tuple[str, str], int] = defaultdict(int)
    lsoa_totals: dict[str, int] = defaultdict(int)
    lsoa_names: dict[str, str] = {}
    for oa_code, count in oa_uprn_counts.items():
        if oa_code not in oa_to_lsoa:
            raise ValueError(f"OA '{oa_code}' has a UPRN count but no entry in oa_to_lsoa_rows")
        if oa_code not in oa_to_parish:
            raise ValueError(f"OA '{oa_code}' has a UPRN count but no entry in oa_to_parish_rows")
        lsoa_code, lsoa_name = oa_to_lsoa[oa_code]
        parish_code = oa_to_parish[oa_code]
        per_pair[(lsoa_code, parish_code)] += count
        lsoa_totals[lsoa_code] += count
        lsoa_names[lsoa_code] = lsoa_name

    results = [
        AddressWeight(
            lsoa_code=lsoa_code,
            lsoa_name=lsoa_names[lsoa_code],
            parish_code=parish_code,
            uprn_count=count,
            lsoa_total_uprns=lsoa_totals[lsoa_code],
        )
        for (lsoa_code, parish_code), count in per_pair.items()
    ]
    return sorted(results, key=lambda r: (r.lsoa_code, -r.weight))


@dataclass(frozen=True)
class LsoaAreaWeight:
    """(LSOA, parish) area-based weight -- a cross-check on AddressWeight,
    not a replacement for it (address density can differ from area share;
    see the P1.5 worklog entry for a real example: Cholsey/Moulsford's
    split LSOA is 45.7% Cholsey by area but 58.3% by address count)."""

    lsoa_code: str
    lsoa_name: str
    parish_code: str
    weight: float
    """Share of the LSOA's polygon area that intersects this parish."""


MIN_AREA_WEIGHT = 0.001
"""Below this share, an "overlap" is treated as a boundary-snapping sliver
rather than a real one, not counted as a genuine parish/LSOA or
parish/ward relationship. Real finding while building P1.5: LSOA and
parish boundaries are separate ONS products, and their shared edges don't
always snap to identical vertices, producing spurious near-zero slivers
(e.g. a real, committed E01035751/Moulsford intersection of weight 5.5e-05
-- ~108 m^2 out of a ~2,000,000 m^2 LSOA -- even though that LSOA is
otherwise wholly within Cholsey). 0.1% is comfortably above the sliver
sizes observed and comfortably below any plausible genuine partial overlap
for this project's geographies."""


def compute_lsoa_area_weights(
    lsoas: gpd.GeoDataFrame,
    parishes: gpd.GeoDataFrame,
    lsoa_code_field: str = "LSOA21CD",
    lsoa_name_field: str = "LSOA21NM",
    parish_code_field: str = "PARNCP23CD",
    min_weight: float = MIN_AREA_WEIGHT,
) -> list[LsoaAreaWeight]:
    """Compute each LSOA's area-based share falling in each parish it
    overlaps. Both GeoDataFrames must be in a metres-based CRS (BNG,
    EPSG:27700 -- what `geography.boundaries.fetch_boundary` returns).
    Overlaps below `min_weight` are dropped as boundary-snapping slivers,
    not genuine partial overlaps (see MIN_AREA_WEIGHT)."""
    results: list[LsoaAreaWeight] = []
    for _, lsoa_row in lsoas.iterrows():
        lsoa_geom = lsoa_row.geometry
        lsoa_area = lsoa_geom.area
        if lsoa_area == 0:
            continue
        for _, parish_row in parishes.iterrows():
            intersection_area = lsoa_geom.intersection(parish_row.geometry).area
            if intersection_area / lsoa_area < min_weight:
                continue
            results.append(
                LsoaAreaWeight(
                    lsoa_code=lsoa_row[lsoa_code_field],
                    lsoa_name=lsoa_row[lsoa_name_field],
                    parish_code=parish_row[parish_code_field],
                    weight=intersection_area / lsoa_area,
                )
            )
    return sorted(results, key=lambda r: (r.lsoa_code, -r.weight))


@dataclass(frozen=True)
class WardAreaWeight:
    """Share of a PARISH's own area that falls inside a given ward --
    used to combine ward-level canopy figures onto the parish, weighted by
    how much of the parish each ward actually covers."""

    parish_code: str
    ward_code: str
    ward_name: str
    weight: float


def compute_parish_ward_weights(
    parishes: gpd.GeoDataFrame,
    wards: gpd.GeoDataFrame,
    parish_code_field: str = "PARNCP23CD",
    ward_code_field: str = "WD20CD",
    ward_name_field: str = "WD20NM",
    min_weight: float = MIN_AREA_WEIGHT,
) -> list[WardAreaWeight]:
    """Compute, for every parish, the share of its own polygon area that
    falls inside each ward it overlaps. Both GeoDataFrames must be in a
    metres-based CRS (BNG, EPSG:27700). Overlaps below `min_weight` are
    dropped as boundary-snapping slivers (see MIN_AREA_WEIGHT)."""
    results: list[WardAreaWeight] = []
    for _, parish_row in parishes.iterrows():
        parish_geom = parish_row.geometry
        parish_area = parish_geom.area
        if parish_area == 0:
            continue
        for _, ward_row in wards.iterrows():
            intersection_area = parish_geom.intersection(ward_row.geometry).area
            if intersection_area / parish_area < min_weight:
                continue
            results.append(
                WardAreaWeight(
                    parish_code=parish_row[parish_code_field],
                    ward_code=ward_row[ward_code_field],
                    ward_name=ward_row[ward_name_field],
                    weight=intersection_area / parish_area,
                )
            )
    return sorted(results, key=lambda r: (r.parish_code, -r.weight))
