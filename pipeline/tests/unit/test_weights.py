"""Tests for cholsey_pipeline.geography.weights.

Uses committed, real fixtures: the same OA->parish/OA->LSOA extracts as
test_lsoa_overlap.py, a real UPRN-count-per-OA extract from the ONS
National Statistics UPRN Lookup (NSUL, January 2024), and real parish/LSOA/
ward polygons -- no network, per development-plan.md §5.1.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pytest

from cholsey_pipeline.geography.weights import (
    compute_address_weights,
    compute_lsoa_area_weights,
    compute_parish_ward_weights,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
WEIGHTS_DIR = FIXTURES_DIR / "weights"
LSOA_OVERLAP_DIR = FIXTURES_DIR / "lsoa_overlap"

CHOLSEY = "E04012474"
MOULSFORD = "E04008148"


def _load_features(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["features"]


@pytest.fixture
def oa_to_parish_rows() -> list[dict]:
    return _load_features(LSOA_OVERLAP_DIR / "oa_to_parish_sample.json")


@pytest.fixture
def oa_to_lsoa_rows() -> list[dict]:
    return _load_features(LSOA_OVERLAP_DIR / "oa_to_lsoa_sample.json")


@pytest.fixture
def oa_uprn_counts() -> dict[str, int]:
    return json.loads((WEIGHTS_DIR / "oa_uprn_counts_sample.json").read_text(encoding="utf-8"))[
        "counts"
    ]


@pytest.fixture
def parishes() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(WEIGHTS_DIR / "parishes_sample.geojson")
    return gdf.set_crs("EPSG:27700", allow_override=True)


@pytest.fixture
def lsoas() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(WEIGHTS_DIR / "lsoas_sample.geojson")
    return gdf.set_crs("EPSG:27700", allow_override=True)


@pytest.fixture
def ward() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(WEIGHTS_DIR / "ward_sample.geojson")
    return gdf.set_crs("EPSG:27700", allow_override=True)


class TestComputeAddressWeights:
    def test_wholly_within_lsoas_weight_one_to_cholsey(
        self, oa_to_parish_rows, oa_to_lsoa_rows, oa_uprn_counts
    ) -> None:
        weights = compute_address_weights(oa_to_parish_rows, oa_to_lsoa_rows, oa_uprn_counts)
        by_lsoa_parish = {(w.lsoa_code, w.parish_code): w for w in weights}
        assert by_lsoa_parish[("E01028619", CHOLSEY)].weight == pytest.approx(1.0)
        assert by_lsoa_parish[("E01035751", CHOLSEY)].weight == pytest.approx(1.0)

    def test_split_lsoa_weights_sum_to_one(
        self, oa_to_parish_rows, oa_to_lsoa_rows, oa_uprn_counts
    ) -> None:
        weights = compute_address_weights(oa_to_parish_rows, oa_to_lsoa_rows, oa_uprn_counts)
        split = [w for w in weights if w.lsoa_code == "E01035752"]
        assert {w.parish_code for w in split} == {CHOLSEY, MOULSFORD}
        assert sum(w.weight for w in split) == pytest.approx(1.0, abs=0.001)

    def test_split_lsoa_real_address_counts(
        self, oa_to_parish_rows, oa_to_lsoa_rows, oa_uprn_counts
    ) -> None:
        """Ground truth from the real NSUL extract: Cholsey's 3 OAs in
        E01035752 hold 218+170+99=487 UPRNs; Moulsford's 2 hold
        228+120=348; total 835 -- giving Cholsey a real address-count
        weight of ~0.583, noticeably different from P1.4's coarse
        3-of-5-OAs proxy of 0.6 and from the area-based weight (~0.457,
        see TestComputeLsoaAreaWeights) -- see the P1.5 worklog entry."""
        weights = compute_address_weights(oa_to_parish_rows, oa_to_lsoa_rows, oa_uprn_counts)
        by_parish = {w.parish_code: w for w in weights if w.lsoa_code == "E01035752"}
        assert by_parish[CHOLSEY].uprn_count == 487
        assert by_parish[MOULSFORD].uprn_count == 348
        assert by_parish[CHOLSEY].lsoa_total_uprns == 835
        assert by_parish[CHOLSEY].weight == pytest.approx(487 / 835, abs=1e-6)

    def test_unknown_oa_in_lsoa_lookup_raises(self, oa_to_parish_rows, oa_to_lsoa_rows) -> None:
        with pytest.raises(ValueError, match="oa_to_lsoa_rows"):
            compute_address_weights(oa_to_parish_rows, oa_to_lsoa_rows, {"E00000000": 10})

    def test_unknown_oa_in_parish_lookup_raises(self, oa_to_lsoa_rows) -> None:
        # A valid OA->LSOA row but no matching OA->parish row.
        with pytest.raises(ValueError, match="oa_to_parish_rows"):
            compute_address_weights([], oa_to_lsoa_rows, {"E00145772": 100})


class TestComputeLsoaAreaWeights:
    def test_wholly_within_lsoas_are_near_one(self, lsoas, parishes) -> None:
        weights = compute_lsoa_area_weights(lsoas, parishes)
        by_lsoa_parish = {(w.lsoa_code, w.parish_code): w for w in weights}
        assert by_lsoa_parish[("E01028619", CHOLSEY)].weight == pytest.approx(1.0, abs=0.001)
        assert by_lsoa_parish[("E01035751", CHOLSEY)].weight == pytest.approx(1.0, abs=0.01)

    def test_split_lsoa_area_share_differs_from_address_share(self, lsoas, parishes) -> None:
        """Real finding while building P1.5: the split LSOA's area is
        divided roughly evenly (~46/54) but its addresses are more
        concentrated on the Cholsey side (~58/42) -- area and address
        weights are genuinely different quantities, which is exactly why
        the plan asks for the area weight as a cross-check, not a
        substitute."""
        weights = compute_lsoa_area_weights(lsoas, parishes)
        by_parish = {w.parish_code: w for w in weights if w.lsoa_code == "E01035752"}
        assert by_parish[CHOLSEY].weight == pytest.approx(0.457, abs=0.01)
        assert by_parish[MOULSFORD].weight == pytest.approx(0.542, abs=0.01)
        total = by_parish[CHOLSEY].weight + by_parish[MOULSFORD].weight
        assert total == pytest.approx(1.0, abs=0.01)

    def test_boundary_snapping_sliver_is_dropped(self, lsoas, parishes) -> None:
        """Real finding from the Phase 1 PR review: E01035751 is wholly
        within Cholsey, but the live parish/LSOA polygons (separate ONS
        products that don't share vertices) produce a spurious ~108 m^2
        Moulsford sliver (weight ~5.5e-05) at their shared edge. That's
        noise, not a genuine partial overlap, and MIN_AREA_WEIGHT should
        filter it out rather than it silently ending up in weights.csv."""
        weights = compute_lsoa_area_weights(lsoas, parishes)
        codes_for_e01035751 = {w.parish_code for w in weights if w.lsoa_code == "E01035751"}
        assert codes_for_e01035751 == {CHOLSEY}

    def test_min_weight_is_configurable(self, lsoas, parishes) -> None:
        """A caller who wants the raw slivers (e.g. for debugging boundary
        quality) can still get them by passing min_weight=0."""
        weights = compute_lsoa_area_weights(lsoas, parishes, min_weight=0)
        codes_for_e01035751 = {w.parish_code for w in weights if w.lsoa_code == "E01035751"}
        assert MOULSFORD in codes_for_e01035751


class TestComputeParishWardWeights:
    def test_cholsey_wholly_within_its_ward(self, parishes, ward) -> None:
        """Real finding: the "Cholsey" ward (E05011701) is ~4x the area of
        Cholsey parish and fully contains it -- so Cholsey's parish-side
        weight into that one ward is 1.0, and no other ward is needed to
        reconstruct Cholsey's canopy figure from ward-level data."""
        cholsey_only = parishes[parishes["PARNCP23CD"] == CHOLSEY]
        weights = compute_parish_ward_weights(cholsey_only, ward)
        assert len(weights) == 1
        assert weights[0].parish_code == CHOLSEY
        assert weights[0].ward_code == "E05011701"
        assert weights[0].weight == pytest.approx(1.0, abs=0.001)

    def test_weights_per_parish_sum_to_one_across_its_wards(self, parishes, ward) -> None:
        weights = compute_parish_ward_weights(parishes, ward)
        by_parish: dict[str, float] = {}
        for w in weights:
            by_parish[w.parish_code] = by_parish.get(w.parish_code, 0.0) + w.weight
        for code, total in by_parish.items():
            assert total <= 1.0 + 1e-6, f"{code} weight sums to {total} (should be <= 1.0)"
