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
REAL_ACCESSIBLE_AREA_M2 = 89_089.8403
"""Sum of the real fixture's Playing Field + Play Space + Tennis Court
site areas (the ADR-0008 accessible types present in Cholsey's own real
data) -- verified 2026-09-30 against the live service."""


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
REAL_MOULSFORD_ACCESSIBLE_AREA_M2 = 38_443.83965000155
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
