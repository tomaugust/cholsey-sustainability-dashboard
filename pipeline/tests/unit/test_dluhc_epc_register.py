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
from urllib.parse import parse_qs, urlparse

import pytest

from cholsey_pipeline.fetch import http as fetch_http
from cholsey_pipeline.fetch.dluhc_epc_register import (
    EPC_DOMESTIC_SEARCH_URL,
    EpcApiKeyMissing,
    EpcPaginationError,
    fetch_domestic_certificates,
    has_more_pages,
    parse_domestic_search_response,
)
from cholsey_pipeline.fetch.http import HttpResponse

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "dluhc_epc_register"


@pytest.fixture(autouse=True)
def _isolate_data_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """fetch_domestic_certificates now routes through fetch.http.fetch_file
    for provenance, so it needs its own isolated data/raw and
    data/manifest, same as test_fetch_http.py."""
    monkeypatch.setattr(fetch_http, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(fetch_http, "MANIFEST_DIR", tmp_path / "manifest")


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


def _cert(number: str, band: str, date: str) -> dict:
    return {
        "certificateNumber": number,
        "postcode": "OX10 9AA",
        "council": "c",
        "currentEnergyEfficiencyBand": band,
        "registrationDate": date,
    }


def _current_page_of(url: str) -> int:
    return int(parse_qs(urlparse(url).query)["current_page"][0])


class _FakeHttpGetByPage:
    """Serves canned page payloads keyed by the `current_page` query
    param, and records the auth header sent with each call."""

    def __init__(self, pages: dict[int, dict]) -> None:
        self._pages = pages
        self.calls: list[dict] = []

    def __call__(self, url: str, *, timeout: int, headers: dict[str, str]) -> HttpResponse:
        page = _current_page_of(url)
        self.calls.append({"url": url, "headers": dict(headers), "page": page})
        return HttpResponse(
            status_code=200, content=json.dumps(self._pages[page]).encode(), headers={}
        )


class TestFetchDomesticCertificatesPagination:
    def test_follows_pagination_until_exhausted(self) -> None:
        """Regression test for the fixed bug: a result set spanning more
        than one page must not be silently truncated to page 1."""
        fake = _FakeHttpGetByPage(
            {
                1: {
                    "data": [_cert("A", "D", "2022-01-01")],
                    "pagination": {"totalResults": 2, "currentPage": 1, "pageSize": 1},
                },
                2: {
                    "data": [_cert("B", "C", "2023-01-01")],
                    "pagination": {"totalResults": 2, "currentPage": 2, "pageSize": 1},
                },
            }
        )

        records = fetch_domestic_certificates("OX10 9AA", "fake-key", page_size=1, http_get=fake)

        assert [r.certificate_number for r in records] == ["A", "B"]
        assert len(fake.calls) == 2
        assert fake.calls[0]["url"].startswith(EPC_DOMESTIC_SEARCH_URL)
        assert fake.calls[0]["headers"]["Authorization"] == "Bearer fake-key"
        assert fake.calls[1]["page"] == 2

    def test_single_page_result_makes_one_call(self) -> None:
        fake = _FakeHttpGetByPage(
            {
                1: {
                    "data": [_cert("A", "D", "2022-01-01")],
                    "pagination": {"totalResults": 1, "currentPage": 1, "pageSize": 5000},
                }
            }
        )
        records = fetch_domestic_certificates("OX10 9AA", "fake-key", http_get=fake)
        assert len(records) == 1
        assert len(fake.calls) == 1

    def test_pagination_loop_is_bounded(self) -> None:
        """Regression test for the fixed infinite-loop bug: if the API
        ignores `current_page` and keeps claiming more pages exist beyond
        what totalResults/pageSize can account for, the loop must raise
        rather than continue forever."""

        class _StuckHttpGet:
            def __init__(self) -> None:
                self.call_count = 0

            def __call__(self, url: str, *, timeout: int, headers: dict[str, str]) -> HttpResponse:
                self.call_count += 1
                # Always claims more pages remain, regardless of current_page.
                payload = {
                    "data": [_cert(f"X{self.call_count}", "D", "2022-01-01")],
                    "pagination": {"totalResults": 2, "currentPage": 1, "pageSize": 1},
                }
                return HttpResponse(
                    status_code=200, content=json.dumps(payload).encode(), headers={}
                )

        stuck = _StuckHttpGet()
        with pytest.raises(EpcPaginationError):
            fetch_domestic_certificates("OX10 9AA", "fake-key", page_size=1, http_get=stuck)
        assert stuck.call_count < 10  # bounded, not thousands of calls
