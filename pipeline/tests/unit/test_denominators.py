"""Tests for cholsey_pipeline.geography.denominators.

Uses the same real OA->parish extract as test_lsoa_overlap.py/test_weights.py
(Cholsey's 13 OAs + Moulsford's 2, for the shared LSOA E01035752), with real
Census 2021 OA-level population and household counts from the ONS/nomis
TS001 and TS041 tables -- no network, per development-plan.md §5.1.
"""

from __future__ import annotations

import pytest

from cholsey_pipeline.geography.denominators import sum_by_parish

CHOLSEY = "E04012474"
MOULSFORD = "E04008148"

# Real OA->parish best-fit assignment (P1.4), and real Census 2021 OA
# population (TS001, "Total: All usual residents") and household (TS041)
# counts (P1.6), for exactly the 15 OAs relevant to Cholsey/Moulsford --
# see the P1.6 worklog entry for the live query.
OA_TO_PARISH = {
    "E00145768": CHOLSEY,
    "E00145769": CHOLSEY,
    "E00145770": CHOLSEY,
    "E00145771": CHOLSEY,
    "E00145772": CHOLSEY,
    "E00145775": CHOLSEY,
    "E00145776": CHOLSEY,
    "E00145777": CHOLSEY,
    "E00145778": CHOLSEY,
    "E00185967": CHOLSEY,
    "E00185997": CHOLSEY,
    "E00186000": CHOLSEY,
    "E00186067": CHOLSEY,
    "E00145779": MOULSFORD,
    "E00145780": MOULSFORD,
}

OA_POPULATION = {
    "E00145768": 358,
    "E00145769": 303,
    "E00145770": 279,
    "E00145771": 445,
    "E00145772": 293,
    "E00145775": 421,
    "E00145776": 287,
    "E00145777": 283,
    "E00145778": 295,
    "E00185967": 614,
    "E00185997": 279,
    "E00186000": 279,
    "E00186067": 254,
    "E00145779": 320,
    "E00145780": 270,
}

OA_HOUSEHOLDS = {
    "E00145768": 135,
    "E00145769": 122,
    "E00145770": 131,
    "E00145771": 167,
    "E00145772": 110,
    "E00145775": 177,
    "E00145776": 121,
    "E00145777": 113,
    "E00145778": 133,
    "E00185967": 225,
    "E00185997": 118,
    "E00186000": 135,
    "E00186067": 95,
    "E00145779": 101,
    "E00145780": 103,
}


class TestSumByParish:
    def test_cholsey_census_day_population(self) -> None:
        totals = sum_by_parish(OA_POPULATION, OA_TO_PARISH)
        assert totals[CHOLSEY] == 4390

    def test_moulsford_census_day_population(self) -> None:
        totals = sum_by_parish(OA_POPULATION, OA_TO_PARISH)
        assert totals[MOULSFORD] == 590

    def test_cholsey_census_day_households(self) -> None:
        totals = sum_by_parish(OA_HOUSEHOLDS, OA_TO_PARISH)
        assert totals[CHOLSEY] == 1782

    def test_unknown_oa_raises(self) -> None:
        with pytest.raises(ValueError, match="oa_to_parish"):
            sum_by_parish({"E00000000": 10}, OA_TO_PARISH)
