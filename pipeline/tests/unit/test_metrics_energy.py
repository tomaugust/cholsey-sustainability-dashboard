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

from cholsey_pipeline.fetch.desnz_lsoa_energy import AreaEnergyRecord, LsoaEnergyRecord
from cholsey_pipeline.metrics.energy import (
    CHOLSEY_PARISH_CODE,
    compute_area_energy_row,
    compute_comparator_energy_row,
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


REAL_ENGLAND_ELECTRICITY_2024 = AreaEnergyRecord(
    fuel="electricity",
    year=2024,
    area_code="E92000001",
    area_name="England",
    number_of_domestic_meters_thousands=25082.767,
    total_domestic_consumption_gwh=84098.54191439805,
)
REAL_SOUTH_OXFORDSHIRE_GAS_2024 = AreaEnergyRecord(
    fuel="gas",
    year=2024,
    area_code="E07000179",
    area_name="South Oxfordshire",
    number_of_domestic_meters_thousands=54.423,
    total_domestic_consumption_gwh=677.0182702912758,
)


class TestComputeAreaEnergyRow:
    def test_real_england_electricity_values(self) -> None:
        row = compute_area_energy_row(REAL_ENGLAND_ELECTRICITY_2024, area_role="national")
        assert row.area_code == "E92000001"
        assert row.area_name == "England"
        assert row.area_role == "national"
        assert row.metric_id == "electricity"
        assert row.year == 2024
        assert row.unit == "kWh/meter/year"
        assert row.value == pytest.approx(3352.8414913074807, rel=1e-9)
        assert row.total_mwh == pytest.approx(84098541.91439806, rel=1e-9)

    def test_real_south_oxfordshire_gas_values(self) -> None:
        row = compute_area_energy_row(REAL_SOUTH_OXFORDSHIRE_GAS_2024, area_role="district")
        assert row.area_code == "E07000179"
        assert row.area_name == "South Oxfordshire"
        assert row.area_role == "district"
        assert row.metric_id == "gas"
        assert row.value == pytest.approx(12439.929263202612, rel=1e-9)
        assert row.total_mwh == pytest.approx(677018.2702912758, rel=1e-9)

    def test_method_is_direct_not_estimated(self) -> None:
        """DESNZ publishes district/national totals directly -- no
        apportionment or flagging needed, unlike the subject row."""
        row = compute_area_energy_row(REAL_ENGLAND_ELECTRICITY_2024, area_role="national")
        assert row.method == "direct"
        assert row.flag == "none"
        assert row.flag_note == ""


# Real Aldworth (single-LSOA comparator, no NSUL address weight) and
# Brightwell-cum-Sotwell (5-LSOA comparator) AREA weights, exactly as
# committed in data/processed/geography/weights.csv (regenerated
# 2026-09-30 by `scripts/build_weights_csv.py` with its new all-parishes
# bbox-based LSOA search, P3.4). Moulsford is tested separately below --
# it's the one comparator that DOES have a real NSUL address weight
# (P1.5/ADR-0004, via its shared LSOA with Cholsey), so it goes through
# `compute_subject_energy_row` (address-weighted), not this area-weighted
# path.
REAL_ALDWORTH_WEIGHT = {"E01016257": 0.408198}
REAL_ALDWORTH_ELECTRICITY_2024 = [
    LsoaEnergyRecord(
        fuel="electricity",
        year=2024,
        lsoa_code="E01016257",
        lsoa_name="West Berkshire 003B",
        la_code="E06000037",
        la_name="West Berkshire",
        number_of_meters=553,
        total_consumption_kwh=3518076.350245903,
    )
]

REAL_BRIGHTWELL_WEIGHTS = {
    "E01028607": 0.44334,
    "E01028608": 0.93595,
    "E01028674": 0.021342,
    "E01028675": 0.003552,
    "E01028677": 0.001131,
}
REAL_BRIGHTWELL_ELECTRICITY_2024 = [
    LsoaEnergyRecord(
        fuel="electricity",
        year=2024,
        lsoa_code="E01028607",
        lsoa_name="South Oxfordshire 006C",
        la_code="E07000179",
        la_name="South Oxfordshire",
        number_of_meters=833,
        total_consumption_kwh=3371033.36770492,
    ),
    LsoaEnergyRecord(
        fuel="electricity",
        year=2024,
        lsoa_code="E01028608",
        lsoa_name="South Oxfordshire 012A",
        la_code="E07000179",
        la_name="South Oxfordshire",
        number_of_meters=755,
        total_consumption_kwh=3079034.058076504,
    ),
    LsoaEnergyRecord(
        fuel="electricity",
        year=2024,
        lsoa_code="E01028674",
        lsoa_name="South Oxfordshire 012C",
        la_code="E07000179",
        la_name="South Oxfordshire",
        number_of_meters=537,
        total_consumption_kwh=1929451.54132787,
    ),
    LsoaEnergyRecord(
        fuel="electricity",
        year=2024,
        lsoa_code="E01028675",
        lsoa_name="South Oxfordshire 012D",
        la_code="E07000179",
        la_name="South Oxfordshire",
        number_of_meters=520,
        total_consumption_kwh=1745381.297289617,
    ),
    LsoaEnergyRecord(
        fuel="electricity",
        year=2024,
        lsoa_code="E01028677",
        lsoa_name="South Oxfordshire 012F",
        la_code="E07000179",
        la_name="South Oxfordshire",
        number_of_meters=921,
        total_consumption_kwh=2720756.061371579,
    ),
]

REAL_MOULSFORD_ADDRESS_WEIGHT = {"E01035752": 0.416766}


class TestComputeComparatorEnergyRow:
    def test_real_aldworth_single_lsoa_value(self) -> None:
        """With a single contributing LSOA, the weighted mean equals that
        LSOA's own mean regardless of the weight's magnitude (it cancels
        in Sigma/Sigma) -- confirms the area-weighted path is wired
        correctly, not just that area weights below 1.0 change the
        result."""
        row = compute_comparator_energy_row(
            REAL_ALDWORTH_ELECTRICITY_2024,
            REAL_ALDWORTH_WEIGHT,
            parish_code="E04001147",
            parish_name="Aldworth",
        )
        assert row.area_code == "E04001147"
        assert row.area_name == "Aldworth"
        assert row.area_role == "comparator"
        assert row.value == pytest.approx(3518076.350245903 / 553, rel=1e-9)

    def test_real_brightwell_multi_lsoa_weighted_sum(self) -> None:
        row = compute_comparator_energy_row(
            REAL_BRIGHTWELL_ELECTRICITY_2024,
            REAL_BRIGHTWELL_WEIGHTS,
            parish_code="E04012473",
            parish_name="Brightwell-cum-Sotwell",
        )
        assert row.value == pytest.approx(4060.1817, abs=0.01)
        assert row.total_mwh == pytest.approx(4426.79, abs=0.01)

    def test_method_is_area_weighted(self) -> None:
        row = compute_comparator_energy_row(
            REAL_ALDWORTH_ELECTRICITY_2024,
            REAL_ALDWORTH_WEIGHT,
            parish_code="E04001147",
            parish_name="Aldworth",
        )
        assert row.method == "area_weighted"

    def test_always_flagged_parish_estimate(self) -> None:
        """Unlike the subject row (only flagged when a contributing LSOA
        is partial), a comparator row is always flagged -- area weights
        assume uniform address density across the LSOA, a real
        assumption even for a wholly-contained LSOA."""
        row = compute_comparator_energy_row(
            REAL_ALDWORTH_ELECTRICITY_2024,
            REAL_ALDWORTH_WEIGHT,
            parish_code="E04001147",
            parish_name="Aldworth",
        )
        assert row.flag == "parish_estimate"
        assert row.flag_note != ""


class TestMoulsfordUsesAddressWeightedNotAreaWeighted:
    """Moulsford is the one comparator with a real NSUL address-count
    weight (P1.5/ADR-0004: 0.416766, via its shared LSOA E01035752 with
    Cholsey) -- it should go through `compute_subject_energy_row`
    (address_weighted), not `compute_comparator_energy_row`
    (area_weighted), even though it's a comparator, not the subject."""

    def test_moulsford_address_weighted_row(self) -> None:
        moulsford_record = [
            LsoaEnergyRecord(
                fuel="electricity",
                year=2024,
                lsoa_code="E01035752",
                lsoa_name="South Oxfordshire 015I",
                la_code="E07000179",
                la_name="South Oxfordshire",
                number_of_meters=638,
                total_consumption_kwh=2743265.932655738,
            )
        ]
        row = compute_subject_energy_row(
            moulsford_record,
            REAL_MOULSFORD_ADDRESS_WEIGHT,
            parish_code="E04008148",
            parish_name="Moulsford",
            area_role="comparator",
        )
        assert row.area_code == "E04008148"
        assert row.area_role == "comparator"
        assert row.method == "address_weighted"
        # Single contributing LSOA -- the weight cancels in Sigma/Sigma,
        # same real value as Cholsey's own share of this LSOA's mean.
        assert row.value == pytest.approx(2743265.932655738 / 638, rel=1e-9)
