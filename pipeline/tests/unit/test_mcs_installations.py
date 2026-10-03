"""Tests for cholsey_pipeline.fetch.mcs_installations (P2.7, ADR-0007).

Exercises the real, committed reference-data CSVs
(`fetch/reference_data/mcs_installations/south_oxfordshire/`) -- no
network, since this source has no live fetch (see that module's
docstring and `_provenance.json`).
"""

from __future__ import annotations

import pytest

from cholsey_pipeline.fetch.mcs_installations import (
    load_area_uptake,
    load_yearly_timeline,
    parse_area_uptake_csv,
    parse_yearly_timeline_csv,
)


class TestParseAreaUptakeCsv:
    def test_real_heat_pump_values(self) -> None:
        csv_text = (
            "Local Authority,MCS Certified Installations Total,"
            "% of Households with Installations,\n"
            "South Oxfordshire,1677,2.73%,\n"
        )
        record = parse_area_uptake_csv(csv_text, "heat_pump")
        assert record.technology == "heat_pump"
        assert record.area_name == "South Oxfordshire"
        assert record.installations_total == 1677
        assert record.pct_of_households == 2.73

    def test_wrong_row_count_raises(self) -> None:
        csv_text = (
            "Local Authority,MCS Certified Installations Total,"
            "% of Households with Installations,\n"
        )
        try:
            parse_area_uptake_csv(csv_text, "heat_pump")
            raise AssertionError("expected ValueError")
        except ValueError as e:
            assert "expected exactly 1" in str(e)


class TestParseYearlyTimelineCsv:
    def test_real_values_and_row_count(self) -> None:
        csv_text = (
            "Year,MCS Certified Installations Total,Percentage Change,\n2009,0,,\n2010,17,,\n"
        )
        records = parse_yearly_timeline_csv(csv_text, "heat_pump")
        assert len(records) == 2
        assert records[0].year == 2009
        assert records[0].installations_total == 0
        assert records[1].year == 2010
        assert records[1].installations_total == 17


class TestLoadRealCommittedData:
    def test_heat_pump_uptake_real_values(self) -> None:
        record = load_area_uptake("heat_pump")
        assert record.area_name == "South Oxfordshire"
        assert record.installations_total == 1677
        assert record.pct_of_households == 2.73

    def test_solar_pv_uptake_real_values(self) -> None:
        record = load_area_uptake("solar_pv")
        assert record.area_name == "South Oxfordshire"
        assert record.installations_total == 6198
        assert record.pct_of_households == 10.08

    def test_heat_pump_yearly_timeline_sums_to_cumulative_total(self) -> None:
        """The dashboard's cumulative total (installation_uptake.csv)
        should equal the sum of every year's installs
        (yearly_installation_timeline.csv) -- a real internal-consistency
        check on the committed data, not just that parsing doesn't
        crash."""
        timeline = load_yearly_timeline("heat_pump")
        uptake = load_area_uptake("heat_pump")
        assert sum(r.installations_total for r in timeline) == uptake.installations_total

    def test_solar_pv_yearly_timeline_approximately_matches_cumulative_total(self) -> None:
        """Real finding: solar PV's two chart exports (timeline and
        uptake) were captured 5 seconds apart during Tom's manual
        dashboard session and disagree by 4 installs (6,202 vs 6,198,
        ~0.06%) -- the MCS dashboard is "near-real-time" per its own
        documentation, so a new install can land between two chart
        exports in the same session. Heat pump's exports matched exactly
        (fewer installs per minute for that technology), so this isn't a
        parsing bug -- a small tolerance here reflects that real-world
        data, not a looser correctness bar."""
        timeline = load_yearly_timeline("solar_pv")
        uptake = load_area_uptake("solar_pv")
        assert sum(r.installations_total for r in timeline) == pytest.approx(
            uptake.installations_total, abs=10
        )
