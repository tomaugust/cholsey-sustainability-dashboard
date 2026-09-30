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
    EPC_DOMESTIC_SEARCH_URL,
    EpcApiKeyMissing,
    fetch_domestic_certificates,
    has_more_pages,
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


class TestHasMorePages:
    def test_more_pages_remain(self) -> None:
        payload = {"pagination": {"totalResults": 10000, "currentPage": 1, "pageSize": 5000}}
        assert has_more_pages(payload) is True

    def test_last_page(self) -> None:
        payload = {"pagination": {"totalResults": 6000, "currentPage": 2, "pageSize": 5000}}
        assert has_more_pages(payload) is False

    def test_missing_pagination_object_means_no_more_pages(self) -> None:
        assert has_more_pages({}) is False

    def test_malformed_pagination_means_no_more_pages(self) -> None:
        assert has_more_pages({"pagination": {"totalResults": "not a number"}}) is False


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


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class TestFetchDomesticCertificatesPagination:
    def test_follows_pagination_until_exhausted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Regression test for the fixed bug: a result set spanning more
        than one page must not be silently truncated to page 1."""
        pages = [
            {
                "data": [
                    {
                        "certificateNumber": "A",
                        "postcode": "OX10 9AA",
                        "council": "c",
                        "currentEnergyEfficiencyBand": "D",
                        "registrationDate": "2022-01-01",
                    }
                ],
                "pagination": {"totalResults": 2, "currentPage": 1, "pageSize": 1},
            },
            {
                "data": [
                    {
                        "certificateNumber": "B",
                        "postcode": "OX10 9AA",
                        "council": "c",
                        "currentEnergyEfficiencyBand": "C",
                        "registrationDate": "2023-01-01",
                    }
                ],
                "pagination": {"totalResults": 2, "currentPage": 2, "pageSize": 1},
            },
        ]
        calls: list[dict] = []

        def fake_get(url: str, *, params: dict, headers: dict, timeout: int) -> _FakeResponse:
            calls.append({"url": url, "params": dict(params)})
            return _FakeResponse(pages[params["current_page"] - 1])

        monkeypatch.setattr("cholsey_pipeline.fetch.dluhc_epc_register.requests.get", fake_get)

        records = fetch_domestic_certificates("OX10 9AA", "fake-key", page_size=1)

        assert [r.certificate_number for r in records] == ["A", "B"]
        assert len(calls) == 2
        assert calls[0]["url"] == EPC_DOMESTIC_SEARCH_URL
        assert calls[1]["params"]["current_page"] == 2
