"""Tests for cholsey_pipeline.fetch.forest_research_canopy.

Uses a committed, real fixture (Cholsey's and Wallingford's actual i-Tree
Canopy records, live-verified while building this module, P2.3) -- no
network, per development-plan.md §5.1. fetch_ward_canopy() itself (the live
network call) is a thin wrapper around parse_canopy_response plus a
requests.get call, same pattern as geography/boundaries.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cholsey_pipeline.fetch.forest_research_canopy import (
    CanopyFetchError,
    parse_canopy_response,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "forest_research_canopy"
    / "cholsey_wallingford_sample.json"
)


def _load() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class TestParseCanopyResponse:
    def test_parses_both_wards(self) -> None:
        records = parse_canopy_response(_load())
        assert {r.ward_code for r in records} == {"E05009737", "E05009750"}

    def test_cholsey_real_values(self) -> None:
        """Real values verified live 2026-09-29 while building this module
        -- Cholsey's own i-Tree Canopy record uses wardcode E05009737 (the
        December 2018 ward edition), NOT the current E05011701 -- see
        ADR-0006. Surveyed 2021, not the "2020" this project previously
        assumed."""
        records = {r.ward_code: r for r in parse_canopy_response(_load())}
        cholsey = records["E05009737"]
        assert cholsey.ward_name == "Cholsey"
        assert cholsey.designated == "Rural"
        assert cholsey.survey_year == 2021
        assert cholsey.percent_canopy_cover == 10.4
        assert cholsey.number_of_points == 500

    def test_error_body_raises(self) -> None:
        with pytest.raises(CanopyFetchError, match="error"):
            parse_canopy_response({"error": {"code": 400, "message": "bad request"}})

    def test_no_features_raises(self) -> None:
        with pytest.raises(CanopyFetchError, match="no features"):
            parse_canopy_response({"features": []})
