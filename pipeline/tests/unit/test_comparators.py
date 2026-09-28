"""Tests for cholsey_pipeline.geography.comparators.

Uses a committed, trimmed-but-real fixture (Cholsey + the 8 parishes
verified to actually touch it, plus two non-touching controls: Aston
Upthorpe and Didcot) -- no network, per development-plan.md §5.1.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pytest

from cholsey_pipeline.geography.comparators import SUBJECT_CODE, find_touching_parishes

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "comparators"
    / "parishes_near_cholsey_sample.geojson"
)


@pytest.fixture
def parishes() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(FIXTURE)
    return gdf.set_crs("EPSG:27700", allow_override=True)


class TestFindTouchingParishes:
    def test_finds_the_eight_real_neighbours(self, parishes: gpd.GeoDataFrame) -> None:
        """Ground truth computed live against the full ONS parish layer
        while building this module (P1.3 worklog entry), stable across
        buffer_m in {0, 1, 5, 20}m -- not a fixture-only artifact."""
        touching = find_touching_parishes(parishes)
        names = set(touching["PARNCP23NM"])
        assert names == {
            "Aldworth",
            "Aston Tirrold",
            "Brightwell-cum-Sotwell",
            "Crowmarsh",
            "Moulsford",
            "South Moreton",
            "South Stoke",
            "Wallingford",
        }

    def test_subject_parish_excluded_from_result(self, parishes: gpd.GeoDataFrame) -> None:
        touching = find_touching_parishes(parishes)
        assert SUBJECT_CODE not in set(touching["PARNCP23CD"])

    def test_aston_upthorpe_does_not_touch_despite_the_spec_pairing(
        self, parishes: gpd.GeoDataFrame
    ) -> None:
        """spec §2 lists "Aston Tirrold & Aston Upthorpe" as one candidate
        comparator, but they are two separate parishes and only Aston
        Tirrold actually touches Cholsey -- see Q-009 / ADR-0003."""
        touching = find_touching_parishes(parishes)
        assert "Aston Upthorpe" not in set(touching["PARNCP23NM"])
        assert "Aston Tirrold" in set(touching["PARNCP23NM"])

    def test_didcot_does_not_touch(self, parishes: gpd.GeoDataFrame) -> None:
        """Sanity control: Didcot is a real nearby town but does not
        border Cholsey directly."""
        touching = find_touching_parishes(parishes)
        assert "Didcot" not in set(touching["PARNCP23NM"])

    def test_result_stable_across_reasonable_buffer_sizes(self, parishes: gpd.GeoDataFrame) -> None:
        names_0 = set(find_touching_parishes(parishes, buffer_m=0)["PARNCP23NM"])
        names_20 = set(find_touching_parishes(parishes, buffer_m=20)["PARNCP23NM"])
        assert names_0 == names_20

    def test_missing_subject_raises(self, parishes: gpd.GeoDataFrame) -> None:
        without_subject = parishes[parishes["PARNCP23CD"] != SUBJECT_CODE]
        with pytest.raises(ValueError, match="not found"):
            find_touching_parishes(without_subject)
