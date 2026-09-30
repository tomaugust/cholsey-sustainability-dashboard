"""Tests for cholsey_pipeline.metrics.mcs (P3.5, metrics 5-6).

Uses real committed MCS reference data (South Oxfordshire, retrieved by
Tom 2026-09-30) and real Census 2021 household counts (South Oxfordshire
61,497 live-verified via nomis; Cholsey 1,782, already committed in
P1.6's population_denominators.csv) -- not synthetic data.
"""

from __future__ import annotations

import pytest

from cholsey_pipeline.fetch.mcs_installations import AreaUptakeRecord
from cholsey_pipeline.metrics.mcs import (
    CHOLSEY_PARISH_CODE,
    SOUTH_OXFORDSHIRE_CODE,
    SOUTH_OXFORDSHIRE_HOUSEHOLDS_CENSUS2021,
    compute_district_uptake_row,
    compute_subject_uptake_row,
)

CHOLSEY_HOUSEHOLDS_CENSUS2021 = 1782

REAL_HEAT_PUMP_UPTAKE = AreaUptakeRecord(
    technology="heat_pump",
    area_name="South Oxfordshire",
    installations_total=1677,
    pct_of_households=2.73,
)
REAL_SOLAR_PV_UPTAKE = AreaUptakeRecord(
    technology="solar_pv",
    area_name="South Oxfordshire",
    installations_total=6198,
    pct_of_households=10.08,
)


class TestComputeSubjectUptakeRow:
    def test_real_heat_pump_values(self) -> None:
        row = compute_subject_uptake_row(
            REAL_HEAT_PUMP_UPTAKE,
            SOUTH_OXFORDSHIRE_HOUSEHOLDS_CENSUS2021,
            CHOLSEY_HOUSEHOLDS_CENSUS2021,
            year=2026,
        )
        assert row.area_code == CHOLSEY_PARISH_CODE
        assert row.area_name == "Cholsey"
        assert row.area_role == "subject"
        assert row.metric_id == "heat_pump"
        assert row.unit == "%_of_dwellings"
        assert row.value == 2.73
        assert row.estimated_installations == pytest.approx(48.594468022830384, rel=1e-9)

    def test_real_solar_pv_values(self) -> None:
        row = compute_subject_uptake_row(
            REAL_SOLAR_PV_UPTAKE,
            SOUTH_OXFORDSHIRE_HOUSEHOLDS_CENSUS2021,
            CHOLSEY_HOUSEHOLDS_CENSUS2021,
            year=2026,
        )
        assert row.metric_id == "solar_pv"
        assert row.value == 10.08
        assert row.estimated_installations == pytest.approx(179.59959022391337, rel=1e-9)

    def test_always_flagged_parish_estimate(self) -> None:
        """The district's rate is applied uniformly to the parish -- an
        estimate, never a direct parish-level measurement (CLAUDE.md's
        "flag estimates" rule)."""
        row = compute_subject_uptake_row(
            REAL_HEAT_PUMP_UPTAKE,
            SOUTH_OXFORDSHIRE_HOUSEHOLDS_CENSUS2021,
            CHOLSEY_HOUSEHOLDS_CENSUS2021,
            year=2026,
        )
        assert row.flag == "parish_estimate"
        assert row.flag_note != ""

    def test_value_equals_district_pct_unchanged(self) -> None:
        """Scale-invariant under the uniform-rate assumption -- the value
        is South Oxfordshire's own percentage, not reweighted."""
        row = compute_subject_uptake_row(
            REAL_SOLAR_PV_UPTAKE,
            SOUTH_OXFORDSHIRE_HOUSEHOLDS_CENSUS2021,
            CHOLSEY_HOUSEHOLDS_CENSUS2021,
            year=2026,
        )
        assert row.value == REAL_SOLAR_PV_UPTAKE.pct_of_households


class TestComputeDistrictUptakeRow:
    def test_real_heat_pump_values(self) -> None:
        row = compute_district_uptake_row(REAL_HEAT_PUMP_UPTAKE, year=2026)
        assert row.area_code == SOUTH_OXFORDSHIRE_CODE
        assert row.area_name == "South Oxfordshire"
        assert row.area_role == "district"
        assert row.value == 2.73
        assert row.estimated_installations == 1677.0

    def test_method_is_direct_not_estimated(self) -> None:
        """South Oxfordshire IS the district -- no apportionment, unlike
        the subject row."""
        row = compute_district_uptake_row(REAL_SOLAR_PV_UPTAKE, year=2026)
        assert row.method == "direct"
        assert row.flag == "none"
        assert row.flag_note == ""
