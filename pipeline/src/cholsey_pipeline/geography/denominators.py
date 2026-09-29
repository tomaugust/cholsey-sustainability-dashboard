"""Aggregate OA-level counts (population, households) up to parish level.

development-plan.md Phase 1, P1.6: "Parish denominators: 2021 Census
population and dwelling/household counts for Cholsey and comparators
(parish-level Census tables), plus mid-year estimates where available."

Census population/household counts are published at Output Area (2021),
not parish -- parish is not a native census geography. This module reuses
the same OA->parish best-fit lookup P1.4/P1.5 already established for
Cholsey/Moulsford to aggregate any OA-level count (population, households)
up to parish level, exactly the same join direction as
`lsoa_overlap.find_overlapping_lsoas`.
"""

from __future__ import annotations

from collections import defaultdict


def sum_by_parish(
    oa_values: dict[str, int],
    oa_to_parish: dict[str, str],
) -> dict[str, int]:
    """Sum an OA-level count up to each parish it best-fits.

    `oa_values` maps an OA21CD to a count (e.g. census population or
    household count for that OA). `oa_to_parish` maps the same OA21CD to
    the PARNCP code it best-fits (as produced from the ONS OA->parish
    best-fit lookup's `PARNCP24CD` field). Every key in `oa_values` must
    have a matching entry in `oa_to_parish`.

    Returns one total per parish code that has at least one contributing
    OA.
    """
    totals: dict[str, int] = defaultdict(int)
    for oa_code, value in oa_values.items():
        if oa_code not in oa_to_parish:
            raise ValueError(f"OA '{oa_code}' has a value but no entry in oa_to_parish")
        totals[oa_to_parish[oa_code]] += value
    return dict(totals)
