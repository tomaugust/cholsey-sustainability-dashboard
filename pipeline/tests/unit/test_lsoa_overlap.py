"""Tests for cholsey_pipeline.geography.lsoa_overlap.

Uses committed, real fixtures (a trimmed extract of the ONS OA->parish
best-fit and OA->LSOA exact-fit lookups, filtered to the 15 OAs relevant
to Cholsey and Moulsford) -- no network, per development-plan.md §5.1.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cholsey_pipeline.geography.lsoa_overlap import find_overlapping_lsoas

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "lsoa_overlap"
CHOLSEY = "E04012474"


def _load(name: str) -> list[dict]:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))["features"]


class TestFindOverlappingLsoas:
    def test_finds_three_lsoas_not_the_spec_assumed_two(self) -> None:
        """spec §2 (and config/geography.yaml before this task) only lists
        E01035751 and E01028619. Real ONS OA-level data shows a THIRD
        LSOA, E01035752 ("South Oxfordshire 015I"), also has OAs that
        best-fit Cholsey -- exactly the gap P1.4 exists to close."""
        oa_parish = _load("oa_to_parish_sample.json")
        oa_lsoa = _load("oa_to_lsoa_sample.json")
        overlaps = find_overlapping_lsoas(oa_parish, oa_lsoa, CHOLSEY)
        codes = {o.lsoa_code for o in overlaps}
        assert codes == {"E01035751", "E01028619", "E01035752"}

    def test_two_original_lsoas_are_wholly_within_cholsey_by_oa_count(self) -> None:
        oa_parish = _load("oa_to_parish_sample.json")
        oa_lsoa = _load("oa_to_lsoa_sample.json")
        overlaps = {o.lsoa_code: o for o in find_overlapping_lsoas(oa_parish, oa_lsoa, CHOLSEY)}
        assert overlaps["E01035751"].oa_count_share == 1.0
        assert overlaps["E01035751"].oas_total == 4
        assert overlaps["E01028619"].oa_count_share == 1.0
        assert overlaps["E01028619"].oas_total == 6

    def test_third_lsoa_is_only_partially_within_cholsey(self) -> None:
        """E01035752 splits 3 OAs to Cholsey and 2 to Moulsford (a real
        P1.3 comparator) -- confirmed against live ONS data while
        building this module."""
        oa_parish = _load("oa_to_parish_sample.json")
        oa_lsoa = _load("oa_to_lsoa_sample.json")
        overlaps = {o.lsoa_code: o for o in find_overlapping_lsoas(oa_parish, oa_lsoa, CHOLSEY)}
        third = overlaps["E01035752"]
        assert third.lsoa_name == "South Oxfordshire 015I"
        assert third.oas_in_subject == 3
        assert third.oas_total == 5
        assert third.oa_count_share == 0.6

    def test_results_sorted_by_descending_share(self) -> None:
        oa_parish = _load("oa_to_parish_sample.json")
        oa_lsoa = _load("oa_to_lsoa_sample.json")
        overlaps = find_overlapping_lsoas(oa_parish, oa_lsoa, CHOLSEY)
        shares = [o.oa_count_share for o in overlaps]
        assert shares == sorted(shares, reverse=True)

    def test_missing_lsoa_membership_row_raises(self) -> None:
        oa_parish = _load("oa_to_parish_sample.json")
        # Deliberately drop the OA->LSOA rows to trigger the guard.
        with_gap: list[dict] = []
        with pytest.raises(ValueError, match="no entry"):
            find_overlapping_lsoas(oa_parish, with_gap, CHOLSEY)
