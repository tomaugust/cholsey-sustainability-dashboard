"""Tests for cholsey_pipeline.geography.boundaries.

These exercise parse_boundary_response and load_fixture against committed,
trimmed-but-real GeoJSON fixtures under tests/fixtures/boundaries/ -- no
network access, per development-plan.md §5.1 ("CI never depends on
government websites being up"). fetch_boundary() itself (the live network
call) is not covered here; it was verified manually against the live ONS
service while building this module (see the P1.1 worklog entry) and is a
thin wrapper around parse_boundary_response plus a requests.get call.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cholsey_pipeline.geography.boundaries import (
    LAYERS,
    BoundaryFetchError,
    load_fixture,
    parse_boundary_response,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "boundaries"


class TestParishFixture:
    def test_cholsey_present_with_correct_code(self) -> None:
        gdf = load_fixture(FIXTURES_DIR / "parish_bfc_sample.geojson", "parish_bfc")
        cholsey = gdf[gdf["PARNCP23CD"] == "E04012474"]
        assert len(cholsey) == 1
        assert cholsey.iloc[0]["PARNCP23NM"] == "Cholsey"

    def test_cholsey_area_within_tolerance_of_spec_figure(self) -> None:
        """spec §2 states 16.52 km². The live ONS BFC polygon area is ~15.91
        km² -- a real ~3.7% discrepancy, logged as Q-007 in docs/STATUS.md
        rather than silently reconciled (CLAUDE.md: raise scope/spec
        questions, don't decide them). This test pins the *actual* ONS
        figure so a future change is caught, not the spec's figure."""
        gdf = load_fixture(FIXTURES_DIR / "parish_bfc_sample.geojson", "parish_bfc")
        cholsey = gdf[gdf["PARNCP23CD"] == "E04012474"].iloc[0]
        area_km2 = cholsey.geometry.area / 1_000_000
        assert 15.5 < area_km2 < 16.3, (
            f"Cholsey BFC area is {area_km2:.2f} km² -- if this moved outside the "
            "expected ~15.9 km² range, either the geometry precision used when "
            "the fixture was trimmed changed, or ONS republished the boundary; "
            "re-check against Q-007 either way."
        )

    def test_two_south_stokes_exist_by_name(self) -> None:
        """Real finding from building this fixture: querying the ONS parish
        layer by name for 'South Stoke' returns TWO different parishes with
        different GSS codes (E04008163 and E04009876) -- there is more than
        one place called South Stoke in England. This is exactly why
        development-plan.md P1.3 says to select comparators by polygon
        adjacency, never by name matching, and this test guards against a
        future fixture regeneration silently losing that finding."""
        gdf = load_fixture(FIXTURES_DIR / "parish_bfc_sample.geojson", "parish_bfc")
        south_stokes = gdf[gdf["PARNCP23NM"] == "South Stoke"]
        assert len(south_stokes) == 2
        assert set(south_stokes["PARNCP23CD"]) == {"E04008163", "E04009876"}


class TestLsoaFixture:
    def test_both_cholsey_lsoas_present_with_correct_names(self) -> None:
        gdf = load_fixture(FIXTURES_DIR / "lsoa_bfc_sample.geojson", "lsoa_bfc")
        by_code = gdf.set_index("LSOA21CD")["LSOA21NM"].to_dict()
        assert by_code["E01035751"] == "South Oxfordshire 015H"
        assert by_code["E01028619"] == "South Oxfordshire 015B"


class TestWardFixture:
    def test_cholsey_ward_present_with_correct_code(self) -> None:
        gdf = load_fixture(FIXTURES_DIR / "ward_bfc_sample.geojson", "ward_bfc")
        assert len(gdf) == 1
        assert gdf.iloc[0]["WD20CD"] == "E05011701"
        assert gdf.iloc[0]["WD20NM"] == "Cholsey"


class TestParseBoundaryResponseErrors:
    def test_arcgis_error_body_raises(self) -> None:
        layer = LAYERS["parish_bfc"]
        with pytest.raises(BoundaryFetchError, match="error"):
            parse_boundary_response({"error": {"code": 400, "message": "Invalid URL"}}, layer)

    def test_no_features_raises(self) -> None:
        layer = LAYERS["parish_bfc"]
        with pytest.raises(BoundaryFetchError, match="no features"):
            parse_boundary_response({"type": "FeatureCollection", "features": []}, layer)

    def test_missing_expected_field_raises(self) -> None:
        layer = LAYERS["parish_bfc"]
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"SOME_OTHER_FIELD": "x"},
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                }
            ],
        }
        with pytest.raises(BoundaryFetchError, match="not found"):
            parse_boundary_response(geojson, layer)


class TestLayerRegistry:
    def test_all_layers_have_distinct_query_urls(self) -> None:
        urls = [layer.query_url for layer in LAYERS.values()]
        assert len(urls) == len(set(urls))

    def test_all_layers_point_at_the_ons_arcgis_org(self) -> None:
        for key, layer in LAYERS.items():
            assert "services1.arcgis.com/ESMARspQHYMw9BZ9/" in layer.query_url, (
                f"layer '{key}' does not point at the ONS Geoportal's ArcGIS org -- "
                "did this get hand-edited to a guessed URL? See the module "
                "docstring for how to look one up properly."
            )
