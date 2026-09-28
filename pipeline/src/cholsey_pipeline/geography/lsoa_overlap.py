"""Determine which LSOAs genuinely overlap Cholsey parish, and by how much.

development-plan.md Phase 1, P1.4: "Complete the LSOA→parish overlap.
Parish-to-LSOA membership is NOT assumed from the spec's two LSOAs. Derive
it from ONS lookups (ONSUD UPRN→LSOA/parish, and OA→parish best-fit) and
polygon intersection."

This module uses the OA (Output Area, 2021)-level route: OAs nest exactly
inside LSOAs (an LSOA is built from whole 2021 OAs, so OA->LSOA is an exact
fit, not an estimate), and ONS separately publishes an OA->parish
BEST FIT lookup (each OA assigned to whichever parish holds most of its
population -- a coarser approximation than the full UPRN-level ONSUD, but
enough to determine *membership*, which is P1.4's job; P1.5's address-count
weights are the finer-grained follow-up that does need UPRN-level data).

Both source lookups are small, queryable ONS Geoportal FeatureServer tables
(hundreds/thousands of rows for our area, not ONSUD's ~40 million UK-wide
UPRNs) -- see config/sources.yaml's `ons_oa_to_parish` and
`ons_oa_to_lsoa` entries for the verified live URLs.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LsoaOverlap:
    """One LSOA's overlap with the subject parish, in OA-count terms."""

    lsoa_code: str
    lsoa_name: str
    oas_in_subject: int
    """How many of this LSOA's OAs best-fit the subject parish."""
    oas_total: int
    """How many OAs this LSOA has in total (from the OA->LSOA lookup)."""

    @property
    def oa_count_share(self) -> float:
        """Rough share of this LSOA "in" the subject parish, by OA count.

        This is NOT the address-count weight P1.5 will compute (that needs
        UPRN-level data, since OAs vary in how many addresses they hold) --
        it is a coarser, OA-count-based approximation useful for spotting
        which LSOAs are wholly vs partially inside the subject parish.
        """
        if self.oas_total == 0:
            return 0.0
        return self.oas_in_subject / self.oas_total


def find_overlapping_lsoas(
    oa_to_parish_rows: list[dict[str, Any]],
    oa_to_lsoa_rows: list[dict[str, Any]],
    subject_parish_code: str,
) -> list[LsoaOverlap]:
    """Compute which LSOAs overlap the subject parish and by how much.

    `oa_to_parish_rows` and `oa_to_lsoa_rows` are lists of ArcGIS-style
    `{"attributes": {...}}` dicts, exactly as the ONS FeatureServer query
    responses return them (see this module's docstring for the field
    names each table uses) -- both lookups' full rows for at least every
    OA that best-fits `subject_parish_code`, plus every other OA belonging
    to any LSOA that appears among those.

    Returns one LsoaOverlap per LSOA that has at least one OA best-fitting
    the subject parish, sorted by descending oa_count_share (LSOAs mostly
    or wholly inside the parish first).
    """
    oa_to_lsoa: dict[str, tuple[str, str]] = {}
    lsoa_total_oas: dict[str, int] = defaultdict(int)
    lsoa_names: dict[str, str] = {}
    for row in oa_to_lsoa_rows:
        attrs = row["attributes"]
        oa_code = attrs["OA21CD"]
        lsoa_code = attrs["LSOA21CD"]
        lsoa_name = attrs["LSOA21NM"]
        oa_to_lsoa[oa_code] = (lsoa_code, lsoa_name)
        lsoa_total_oas[lsoa_code] += 1
        lsoa_names[lsoa_code] = lsoa_name

    subject_oas_per_lsoa: dict[str, int] = defaultdict(int)
    for row in oa_to_parish_rows:
        attrs = row["attributes"]
        if attrs["PARNCP24CD"] != subject_parish_code:
            continue
        oa_code = attrs["OA21CD"]
        if oa_code not in oa_to_lsoa:
            raise ValueError(
                f"OA '{oa_code}' best-fits the subject parish but has no entry in "
                "oa_to_lsoa_rows -- pass that OA's LSOA membership row too."
            )
        lsoa_code, _ = oa_to_lsoa[oa_code]
        subject_oas_per_lsoa[lsoa_code] += 1

    results = [
        LsoaOverlap(
            lsoa_code=lsoa_code,
            lsoa_name=lsoa_names[lsoa_code],
            oas_in_subject=count,
            oas_total=lsoa_total_oas[lsoa_code],
        )
        for lsoa_code, count in subject_oas_per_lsoa.items()
    ]
    return sorted(results, key=lambda r: r.oa_count_share, reverse=True)
