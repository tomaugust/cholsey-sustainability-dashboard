"""Tests for cholsey_pipeline.metrics.energy (P3.4, metrics 3-4).

Uses real values, live-verified 2026-09-30 against the actual DESNZ 2024
LSOA electricity/gas releases for Cholsey's 3 real contributing LSOAs
(`fetch_lsoa_energy('electricity'/'gas', years=[2024],
lsoa_codes={'E01028619','E01035751','E01035752'})`) and the real address-
count weights already committed in P1.5's `weights.csv`
(E01028619=1.0, E01035751=1.0, E01035752=0.583234) -- not synthetic data.
"""

from __future__ import annotations

import pytest

from cholsey_pipeline.fetch.desnz_lsoa_energy import LsoaEnergyRecord
from cholsey_pipeline.metrics.energy import (
    CHOLSEY_PARISH_CODE,
    compute_subject_energy_row,
)

REAL_LSOA_WEIGHTS = {
    "E01028619": 1.0,
    "E01035751": 1.0,
    "E01035752": 0.583234,
}

REAL_ELECTRICITY_2024 = [
    LsoaEnergyRecord(
        fuel="electricity",
        year=2024,
        lsoa_code="E01028619",
        lsoa_name="South Oxfordshire 015B",
        la_code="E07000179",
        la_name="South Oxfordshire",
        number_of_meters=788,
        total_consumption_kwh=2945410.456923497,
    ),
    LsoaEnergyRecord(
        fuel="electricity",
        year=2024,
        lsoa_code="E01035751",
        lsoa_name="South Oxfordshire 015H",
        la_code="E07000179",
        la_name="South Oxfordshire",
        number_of_meters=784,
        total_consumption_kwh=2613339.550978142,
    ),
    LsoaEnergyRecord(
        fuel="electricity",
        year=2024,
        lsoa_code="E01035752",
        lsoa_name="South Oxfordshire 015I",
        la_code="E07000179",
        la_name="South Oxfordshire",
        number_of_meters=638,
        total_consumption_kwh=2743265.932655738,
    ),
]

REAL_GAS_2024 = [
    LsoaEnergyRecord(
        fuel="gas",
        year=2024,
        lsoa_code="E01028619",
        lsoa_name="South Oxfordshire 015B",
        la_code="E07000179",
        la_name="South Oxfordshire",
        number_of_meters=711,
        total_consumption_kwh=8218199.714451234,
    ),
    LsoaEnergyRecord(
        fuel="gas",
        year=2024,
        lsoa_code="E01035751",
        lsoa_name="South Oxfordshire 015H",
        la_code="E07000179",
        la_name="South Oxfordshire",
        number_of_meters=735,
        total_consumption_kwh=7307477.390840255,
    ),
    LsoaEnergyRecord(
        fuel="gas",
        year=2024,
        lsoa_code="E01035752",
        lsoa_name="South Oxfordshire 015I",
        la_code="E07000179",
        la_name="South Oxfordshire",
        number_of_meters=510,
        total_consumption_kwh=6264501.60481628,
    ),
]


class TestComputeSubjectEnergyRow:
    def test_real_electricity_values(self) -> None:
        row = compute_subject_energy_row(REAL_ELECTRICITY_2024, REAL_LSOA_WEIGHTS)
        assert row.area_code == CHOLSEY_PARISH_CODE
        assert row.area_name == "Cholsey"
        assert row.area_role == "subject"
        assert row.metric_id == "electricity"
        assert row.year == 2024
        assert row.unit == "kWh/meter/year"
        assert row.value == pytest.approx(3682.271410334187, rel=1e-9)
        assert row.total_mwh == pytest.approx(7158.715970868176, rel=1e-9)

    def test_real_gas_values(self) -> None:
        row = compute_subject_energy_row(REAL_GAS_2024, REAL_LSOA_WEIGHTS)
        assert row.metric_id == "gas"
        assert row.value == pytest.approx(11000.805698360531, rel=1e-9)
        assert row.total_mwh == pytest.approx(19179.347434274907, rel=1e-9)

    def test_flagged_parish_estimate_when_any_lsoa_partial(self) -> None:
        """One of Cholsey's 3 LSOAs (E01035752) is split with Moulsford
        (weight 0.583234 < 1.0), so the row must be flagged."""
        row = compute_subject_energy_row(REAL_ELECTRICITY_2024, REAL_LSOA_WEIGHTS)
        assert row.flag == "parish_estimate"
        assert row.flag_note != ""

    def test_not_flagged_when_all_lsoas_wholly_in_parish(self) -> None:
        """Unlike metric 1 (always flagged), an LSOA wholly inside the
        parish contributes real, unapportioned meters/consumption -- no
        estimate needed if every contributing LSOA has weight 1.0."""
        wholly_contained = [r for r in REAL_ELECTRICITY_2024 if r.lsoa_code != "E01035752"]
        weights = {"E01028619": 1.0, "E01035751": 1.0}
        row = compute_subject_energy_row(wholly_contained, weights)
        assert row.flag == "none"
        assert row.flag_note == ""

    def test_method_is_address_weighted(self) -> None:
        row = compute_subject_energy_row(REAL_ELECTRICITY_2024, REAL_LSOA_WEIGHTS)
        assert row.method == "address_weighted"

    def test_geography_used_names_all_three_real_lsoas(self) -> None:
        row = compute_subject_energy_row(REAL_ELECTRICITY_2024, REAL_LSOA_WEIGHTS)
        assert "E01028619" in row.geography_used
        assert "E01035751" in row.geography_used
        assert "E01035752" in row.geography_used

    def test_raises_on_empty_records(self) -> None:
        with pytest.raises(ValueError, match="at least one record"):
            compute_subject_energy_row([], REAL_LSOA_WEIGHTS)

    def test_raises_on_mixed_fuel(self) -> None:
        mixed = [REAL_ELECTRICITY_2024[0], REAL_GAS_2024[1]]
        with pytest.raises(ValueError, match="same fuel and year"):
            compute_subject_energy_row(mixed, REAL_LSOA_WEIGHTS)

    def test_raises_on_missing_weight(self) -> None:
        with pytest.raises(ValueError, match="E01035752"):
            compute_subject_energy_row(REAL_ELECTRICITY_2024, {"E01028619": 1.0, "E01035751": 1.0})
