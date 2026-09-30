"""Tests for cholsey_pipeline.fetch.os_open_greenspace.

Uses a committed, real fixture (10 real OS Open Greenspace sites near
Cholsey, one per distinct `function` value, trimmed from a live bbox-
filtered read while building this module, P2.4) -- no network, per
development-plan.md §5.1. fetch_greenspace_sites() itself (the live
download + zip-URI read) is a thin wrapper around fetch_file and
read_greenspace_sites, same pattern as every other Phase 1/2 fetcher.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Polygon

from cholsey_pipeline.fetch.os_open_greenspace import compute_bbox, read_greenspace_sites

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "os_open_greenspace"
    / "cholsey_area_sample.gpkg"
)


class TestReadGreenspaceSites:
    def test_reads_all_fixture_sites_within_a_generous_bbox(self) -> None:
        gdf = read_greenspace_sites(FIXTURE_PATH, bbox=(0, 0, 700_000, 1_300_000))
        assert len(gdf) == 10
        assert "function" in gdf.columns

    def test_real_function_types_present(self) -> None:
        """Real values from the live OS Open Greenspace service, verified
        while building this module (P2.4) -- not synthetic."""
        gdf = read_greenspace_sites(FIXTURE_PATH, bbox=(0, 0, 700_000, 1_300_000))
        functions = set(gdf["function"])
        assert "Play Space" in functions
        assert "Playing Field" in functions
        assert "Public Park Or Garden" in functions
        assert "Allotments Or Community Growing Spaces" in functions

    def test_bbox_filters_out_sites(self) -> None:
        """A bbox not covering the fixture's real extent should return
        fewer (here, zero) features -- confirms the filter is real, not a
        no-op."""
        gdf = read_greenspace_sites(FIXTURE_PATH, bbox=(0, 0, 1, 1))
        assert len(gdf) == 0


class TestComputeBbox:
    def test_buffers_the_total_bounds(self) -> None:
        square = Polygon([(100, 100), (200, 100), (200, 200), (100, 200)])
        areas = gpd.GeoDataFrame({"geometry": [square]}, crs="EPSG:27700")
        bbox = compute_bbox(areas, buffer_m=10)
        assert bbox == pytest.approx((90, 90, 210, 210))

    def test_default_buffer_is_500m(self) -> None:
        square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
        areas = gpd.GeoDataFrame({"geometry": [square]}, crs="EPSG:27700")
        bbox = compute_bbox(areas)
        assert bbox == pytest.approx((-500, -500, 600, 600))

    def test_multiple_areas_use_combined_extent(self) -> None:
        a = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        b = Polygon([(1000, 1000), (1010, 1000), (1010, 1010), (1000, 1010)])
        areas = gpd.GeoDataFrame({"geometry": [a, b]}, crs="EPSG:27700")
        bbox = compute_bbox(areas, buffer_m=0)
        assert bbox == pytest.approx((0, 0, 1010, 1010))
