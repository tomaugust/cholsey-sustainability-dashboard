"""Tests for cholsey_pipeline.fetch.epc_register.

P2.9 is a stretch, feature-flagged source (development-plan.md): it needs a
registered bearer API key this project doesn't have yet. Unlike every other
Phase 2 fetcher's fixtures, `domestic_search_response_sample.json`'s field
NAMES are verbatim from the live API technical documentation (verified
2026-09-30), but its VALUES are illustrative placeholders, not a real
downloaded response -- getting real values requires the key this module is
designed to work without. See the module docstring and the P2.9 worklog
entry.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cholsey_pipeline.fetch.dluhc_epc_register import (
    EpcApiKeyMissing,
    fetch_domestic_certificates,
    parse_domestic_search_response,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "dluhc_epc_register"


class TestParseDomesticSearchResponse:
    def test_parses_records(self) -> None:
        payload = json.loads((FIXTURES_DIR / "domestic_search_response_sample.json").read_text())
        records = parse_domestic_search_response(payload)
        assert len(records) == 2
        assert records[0].postcode == "OX10 9AA"
        assert records[0].current_energy_efficiency_band == "D"
        assert records[1].uprn is None

    def test_empty_data_returns_empty_list(self) -> None:
        assert parse_domestic_search_response({"data": []}) == []

    def test_missing_data_key_returns_empty_list(self) -> None:
        assert parse_domestic_search_response({}) == []


class TestFetchDomesticCertificatesFeatureFlag:
    def test_missing_api_key_raises(self) -> None:
        """The feature-flag behaviour itself: no key means a loud failure,
        not a silent empty result the pipeline could mistake for "no
        certificates in this postcode"."""
        with pytest.raises(EpcApiKeyMissing):
            fetch_domestic_certificates("OX10 9AA", None)

    def test_empty_string_api_key_also_raises(self) -> None:
        with pytest.raises(EpcApiKeyMissing):
            fetch_domestic_certificates("OX10 9AA", "")
