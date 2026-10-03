"""Tests for cholsey_pipeline.metrics.greenspace (P3.3, metric 2).

Uses a real committed fixture (`cholsey_clipped_real.gpkg`): the actual 11
OS Open Greenspace sites intersecting Cholsey's real parish boundary, from
a live `fetch_greenspace_sites` + `geopandas.clip` run against the real
service, 2026-09-30 -- not synthetic geometry. Real parish area
(15,896,375.505 m2, `geom.area` in EPSG:27700, same method P1.5's
weights.py uses) and real mid-2021 population (4,404, from
`data/processed/geography/population_denominators.csv`) verified from
already-committed project data.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pytest

from cholsey_pipeline.metrics.greenspace import (
    ACCESSIBLE_FUNCTION_TYPES,
    CHOLSEY_PARISH_CODE,
    compute_national_greenspace_row,
    compute_subject_greenspace_row,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "os_open_greenspace"
    / "cholsey_clipped_real.gpkg"
)

REAL_PARISH_AREA_M2 = 15_896_375.505129188
REAL_POPULATION_MID2021 = 4404
REAL_ACCESSIBLE_AREA_M2 = 86_100.0876
"""Merged (union) area of the real fixture's Playing Field + Play Space +
Tennis Court sites (the ADR-0008 accessible types present in Cholsey's
own real data) -- verified 2026-09-30 against the live service. Uses
`.union_all().area`, not a plain sum of each polygon's own area: some of
these real site polygons genuinely overlap (e.g. a Play Space drawn
inside a Playing Field), so a plain sum double-counts the overlap --
89,089.84 vs the real, merged 86,100.09 (PR review finding, 2026-10-03)."""


def _load_clipped_sites() -> gpd.GeoDataFrame:
    return gpd.read_file(FIXTURE_PATH, layer="clipped_sites")


class TestAccessibleFunctionTypes:
    def test_excludes_types_present_in_cholseys_own_real_data(self) -> None:
        """Allotments and Religious Grounds are both real function types
        present in Cholsey's clipped fixture -- confirms the exclusion
        list has a real, immediate effect here, not just hypothetically
        for other parishes (ADR-0008)."""
        assert "Allotments Or Community Growing Spaces" not in ACCESSIBLE_FUNCTION_TYPES
        assert "Religious Grounds" not in ACCESSIBLE_FUNCTION_TYPES

    def test_includes_playing_field_and_play_space_and_tennis_court(self) -> None:
        assert "Playing Field" in ACCESSIBLE_FUNCTION_TYPES
        assert "Play Space" in ACCESSIBLE_FUNCTION_TYPES
        assert "Tennis Court" in ACCESSIBLE_FUNCTION_TYPES

    def test_excludes_golf_course_and_cemetery(self) -> None:
        assert "Golf Course" not in ACCESSIBLE_FUNCTION_TYPES
        assert "Cemetery" not in ACCESSIBLE_FUNCTION_TYPES


class TestComputeSubjectGreenspaceRow:
    def test_real_cholsey_values(self) -> None:
        sites = _load_clipped_sites()
        row = compute_subject_greenspace_row(
            sites,
            parish_area_m2=REAL_PARISH_AREA_M2,
            population=REAL_POPULATION_MID2021,
            year=2021,
        )
        assert row.area_code == CHOLSEY_PARISH_CODE
        assert row.area_name == "Cholsey"
        assert row.area_role == "subject"
        assert row.metric_id == "greenspace"
        assert row.year == 2021
        assert row.unit == "m2_per_resident"
        assert row.accessible_area_m2 == pytest.approx(REAL_ACCESSIBLE_AREA_M2, abs=0.01)

    def test_value_is_accessible_area_divided_by_population(self) -> None:
        sites = _load_clipped_sites()
        row = compute_subject_greenspace_row(
            sites,
            parish_area_m2=REAL_PARISH_AREA_M2,
            population=REAL_POPULATION_MID2021,
            year=2021,
        )
        expected = REAL_ACCESSIBLE_AREA_M2 / REAL_POPULATION_MID2021
        assert row.value == pytest.approx(expected, rel=1e-6)

    def test_pct_of_parish_area_is_accessible_over_parish_area(self) -> None:
        sites = _load_clipped_sites()
        row = compute_subject_greenspace_row(
            sites,
            parish_area_m2=REAL_PARISH_AREA_M2,
            population=REAL_POPULATION_MID2021,
            year=2021,
        )
        expected = REAL_ACCESSIBLE_AREA_M2 / REAL_PARISH_AREA_M2 * 100
        assert row.pct_of_parish_area == pytest.approx(expected, rel=1e-6)

    def test_excluded_sites_do_not_inflate_the_total(self) -> None:
        """The fixture has 11 sites (Allotments/Religious Grounds
        included), but only the 3 accessible-type sites should count --
        confirms the filter is real, not a no-op that sums everything."""
        sites = _load_clipped_sites()
        assert len(sites) == 11
        total_all_sites_area = float(sites.geometry.area.sum())
        row = compute_subject_greenspace_row(
            sites,
            parish_area_m2=REAL_PARISH_AREA_M2,
            population=REAL_POPULATION_MID2021,
            year=2021,
        )
        assert row.accessible_area_m2 < total_all_sites_area

    def test_always_flagged_partial_coverage(self) -> None:
        """OS Open Greenspace excludes CRoW open-access/common land, so
        this metric always undercounts true accessible green space --
        must always be flagged (CLAUDE.md's "flag estimates" rule)."""
        sites = _load_clipped_sites()
        row = compute_subject_greenspace_row(
            sites,
            parish_area_m2=REAL_PARISH_AREA_M2,
            population=REAL_POPULATION_MID2021,
            year=2021,
        )
        assert row.flag == "partial_coverage"
        assert row.flag_note != ""

    def test_method_is_clip_not_area_weighted(self) -> None:
        """Unlike metric 1 (a ward rate applied to a parish it doesn't
        equal), this is a direct geometric clip of real polygons against
        the parish's own boundary."""
        sites = _load_clipped_sites()
        row = compute_subject_greenspace_row(
            sites,
            parish_area_m2=REAL_PARISH_AREA_M2,
            population=REAL_POPULATION_MID2021,
            year=2021,
        )
        assert row.method == "clip"

    def test_geography_used_names_parish_boundary(self) -> None:
        sites = _load_clipped_sites()
        row = compute_subject_greenspace_row(
            sites,
            parish_area_m2=REAL_PARISH_AREA_M2,
            population=REAL_POPULATION_MID2021,
            year=2021,
        )
        assert "parish boundary" in row.geography_used


# Real Moulsford and Aldworth clipped fixtures (P3.3 comparator rows,
# 2026-09-30) -- the actual OS Open Greenspace sites intersecting each
# parish's real boundary, from the same live fetch_greenspace_sites run
# already used for Cholsey and the other 6 comparators.
MOULSFORD_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "os_open_greenspace"
    / "moulsford_clipped_real.gpkg"
)
ALDWORTH_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "os_open_greenspace"
    / "aldworth_clipped_real.gpkg"
)
REAL_MOULSFORD_PARISH_AREA_M2 = 7_242_627.606993225
REAL_MOULSFORD_POPULATION_MID2021 = 592
REAL_MOULSFORD_ACCESSIBLE_AREA_M2 = 37_901.07465000108
"""Merged (union) area -- see REAL_ACCESSIBLE_AREA_M2's docstring above
for why a plain sum (38,443.84) double-counts real overlapping sites."""
REAL_ALDWORTH_PARISH_AREA_M2 = 9_040_097.480831392
REAL_ALDWORTH_POPULATION_MID2021 = 283
REAL_ALDWORTH_ACCESSIBLE_AREA_M2 = 18_381.16615000026


class TestComputeComparatorGreenspaceRow:
    def test_real_moulsford_values(self) -> None:
        sites = gpd.read_file(MOULSFORD_FIXTURE_PATH, layer="clipped_sites")
        row = compute_subject_greenspace_row(
            sites,
            parish_area_m2=REAL_MOULSFORD_PARISH_AREA_M2,
            population=REAL_MOULSFORD_POPULATION_MID2021,
            year=2021,
            parish_code="E04008148",
            parish_name="Moulsford",
            area_role="comparator",
        )
        assert row.area_code == "E04008148"
        assert row.area_role == "comparator"
        assert row.accessible_area_m2 == pytest.approx(REAL_MOULSFORD_ACCESSIBLE_AREA_M2, abs=0.01)
        assert row.value == pytest.approx(
            REAL_MOULSFORD_ACCESSIBLE_AREA_M2 / REAL_MOULSFORD_POPULATION_MID2021, rel=1e-9
        )

    def test_real_aldworth_values(self) -> None:
        sites = gpd.read_file(ALDWORTH_FIXTURE_PATH, layer="clipped_sites")
        row = compute_subject_greenspace_row(
            sites,
            parish_area_m2=REAL_ALDWORTH_PARISH_AREA_M2,
            population=REAL_ALDWORTH_POPULATION_MID2021,
            year=2021,
            parish_code="E04001147",
            parish_name="Aldworth",
            area_role="comparator",
        )
        assert row.area_code == "E04001147"
        assert row.value == pytest.approx(
            REAL_ALDWORTH_ACCESSIBLE_AREA_M2 / REAL_ALDWORTH_POPULATION_MID2021, rel=1e-9
        )

    def test_comparator_rows_stay_flagged_partial_coverage(self) -> None:
        sites = gpd.read_file(MOULSFORD_FIXTURE_PATH, layer="clipped_sites")
        row = compute_subject_greenspace_row(
            sites,
            parish_area_m2=REAL_MOULSFORD_PARISH_AREA_M2,
            population=REAL_MOULSFORD_POPULATION_MID2021,
            year=2021,
            parish_code="E04008148",
            parish_name="Moulsford",
            area_role="comparator",
        )
        assert row.flag == "partial_coverage"


# Real South Oxfordshire district data (P3.7, 2026-10-01): the actual OS
# Open Greenspace sites clipped to South Oxfordshire's real district
# boundary (lad_bfc, E07000179), live-verified -- 640 real clipped sites,
# 6,747,817.44 m2 accessible area. Population is the real Census 2021
# total (149,085, nomis NM_2021_1), not a mid-2021 estimate -- a real,
# documented vintage difference from the parish rows' denominator.
SOUTH_OXFORDSHIRE_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "os_open_greenspace"
    / "south_oxfordshire_clipped_real.gpkg"
)
REAL_SOUTH_OXFORDSHIRE_AREA_M2 = 678_502_434.2500844
REAL_SOUTH_OXFORDSHIRE_POPULATION_CENSUS2021 = 149_085
REAL_SOUTH_OXFORDSHIRE_ACCESSIBLE_AREA_M2 = 6_488_614.587333227
"""Merged (union) area -- see REAL_ACCESSIBLE_AREA_M2's docstring above
for why a plain sum (6,747,817.44) double-counts real overlapping sites."""


class TestComputeDistrictGreenspaceRow:
    def test_real_south_oxfordshire_values(self) -> None:
        sites = gpd.read_file(SOUTH_OXFORDSHIRE_FIXTURE_PATH, layer="clipped_sites")
        row = compute_subject_greenspace_row(
            sites,
            parish_area_m2=REAL_SOUTH_OXFORDSHIRE_AREA_M2,
            population=REAL_SOUTH_OXFORDSHIRE_POPULATION_CENSUS2021,
            year=2021,
            parish_code="E07000179",
            parish_name="South Oxfordshire",
            area_role="district",
            boundary_label="district boundary",
            population_label="the real Census 2021 total (not a mid-2021 estimate)",
        )
        assert row.area_code == "E07000179"
        assert row.area_role == "district"
        assert row.accessible_area_m2 == pytest.approx(
            REAL_SOUTH_OXFORDSHIRE_ACCESSIBLE_AREA_M2, abs=0.01
        )
        assert row.value == pytest.approx(
            REAL_SOUTH_OXFORDSHIRE_ACCESSIBLE_AREA_M2
            / REAL_SOUTH_OXFORDSHIRE_POPULATION_CENSUS2021,
            rel=1e-9,
        )

    def test_boundary_and_population_labels_are_used_in_text(self) -> None:
        sites = gpd.read_file(SOUTH_OXFORDSHIRE_FIXTURE_PATH, layer="clipped_sites")
        row = compute_subject_greenspace_row(
            sites,
            parish_area_m2=REAL_SOUTH_OXFORDSHIRE_AREA_M2,
            population=REAL_SOUTH_OXFORDSHIRE_POPULATION_CENSUS2021,
            year=2021,
            parish_code="E07000179",
            parish_name="South Oxfordshire",
            area_role="district",
            boundary_label="district boundary",
            population_label="the real Census 2021 total (not a mid-2021 estimate)",
        )
        assert "district boundary" in row.geography_used
        assert "district boundary" in row.flag_note
        assert "Census 2021 total" in row.flag_note

    def test_default_labels_still_say_parish(self) -> None:
        """Existing (Cholsey/comparator) call sites don't pass
        boundary_label/population_label -- confirms the defaults keep
        their original wording, not a silent behaviour change."""
        sites = gpd.read_file(SOUTH_OXFORDSHIRE_FIXTURE_PATH, layer="clipped_sites")
        row = compute_subject_greenspace_row(
            sites,
            parish_area_m2=REAL_SOUTH_OXFORDSHIRE_AREA_M2,
            population=REAL_SOUTH_OXFORDSHIRE_POPULATION_CENSUS2021,
            year=2021,
        )
        assert "parish boundary" in row.geography_used
        assert "mid-2021 parish estimate" in row.flag_note


# Real England national data (P3.3, 2026-10-01): the full OS Open
# Greenspace accessible-site set for England (96,914 sites, fetched via a
# bbox-wide fetch_greenspace_sites + simplified-boundary clip -- see the
# module docstring for the simplify/within/clip performance pattern, not
# reproducible here as a committed fixture at this scale). Accessible
# area and England's own real BFC boundary area both verified live
# 2026-10-01; population is the real Census 2021 total for England
# (E92000001, nomis), not an estimate.
REAL_ENGLAND_ACCESSIBLE_AREA_M2 = 1_940_711_368.3078492
REAL_ENGLAND_AREA_M2 = 130_462_331_610.02695
REAL_ENGLAND_POPULATION_CENSUS2021 = 56_490_048


class TestComputeNationalGreenspaceRow:
    def test_real_england_values(self) -> None:
        row = compute_national_greenspace_row(
            REAL_ENGLAND_ACCESSIBLE_AREA_M2,
            REAL_ENGLAND_AREA_M2,
            REAL_ENGLAND_POPULATION_CENSUS2021,
            year=2021,
        )
        assert row.area_code == "E92000001"
        assert row.area_name == "England"
        assert row.area_role == "national"
        assert row.metric_id == "greenspace"
        assert row.unit == "m2_per_resident"
        assert row.accessible_area_m2 == pytest.approx(REAL_ENGLAND_ACCESSIBLE_AREA_M2)
        assert row.value == pytest.approx(
            REAL_ENGLAND_ACCESSIBLE_AREA_M2 / REAL_ENGLAND_POPULATION_CENSUS2021, rel=1e-9
        )
        assert row.pct_of_parish_area == pytest.approx(
            REAL_ENGLAND_ACCESSIBLE_AREA_M2 / REAL_ENGLAND_AREA_M2 * 100, rel=1e-9
        )

    def test_flagged_partial_coverage_like_every_other_role(self) -> None:
        row = compute_national_greenspace_row(
            REAL_ENGLAND_ACCESSIBLE_AREA_M2,
            REAL_ENGLAND_AREA_M2,
            REAL_ENGLAND_POPULATION_CENSUS2021,
            year=2021,
        )
        assert row.flag == "partial_coverage"
        assert "England boundary" in row.geography_used
        assert "England boundary" in row.flag_note
        assert "Census 2021" in row.flag_note

    def test_method_is_clip(self) -> None:
        """The underlying work was a real clip (done in a one-off script,
        see module docstring), so the row should say so just like the
        other roles, not a different method string for the national
        case."""
        row = compute_national_greenspace_row(
            REAL_ENGLAND_ACCESSIBLE_AREA_M2,
            REAL_ENGLAND_AREA_M2,
            REAL_ENGLAND_POPULATION_CENSUS2021,
            year=2021,
        )
        assert row.method == "clip"
