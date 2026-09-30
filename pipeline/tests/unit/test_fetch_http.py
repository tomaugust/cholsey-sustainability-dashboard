"""Tests for cholsey_pipeline.fetch.http.

Entirely offline (development-plan.md §5.1): `http_get` is replaced with a
fake callable that returns HttpResponse objects directly, so no real
network call or `requests` mocking is needed anywhere in this file.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cholsey_pipeline.fetch import http as fetch_http
from cholsey_pipeline.fetch.http import FetchError, HttpResponse, fetch_file


@pytest.fixture(autouse=True)
def _isolate_data_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test gets its own data/raw and data/manifest under tmp_path,
    so tests can't interfere with each other or the real repo's data/."""
    monkeypatch.setattr(fetch_http, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(fetch_http, "MANIFEST_DIR", tmp_path / "manifest")


def _no_sleep(_seconds: float) -> None:
    return None


class _FakeHttpGet:
    """A queue of canned responses/exceptions, one per call, with the
    headers each call was made with recorded for assertions."""

    def __init__(self, responses: list[HttpResponse | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    def __call__(self, url: str, *, timeout: int, headers: dict[str, str]) -> HttpResponse:
        self.calls.append({"url": url, "timeout": timeout, "headers": dict(headers)})
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class TestFetchFileHappyPath:
    def test_downloads_and_writes_file_and_manifest(self, tmp_path: Path) -> None:
        fake = _FakeHttpGet(
            [HttpResponse(status_code=200, content=b"hello world", headers={"ETag": '"abc"'})]
        )
        result = fetch_file("my_source", "https://example.invalid/data.csv", http_get=fake)

        assert result.status == "downloaded"
        assert result.byte_size == 11
        assert result.etag == '"abc"'
        assert result.attempts == 1
        assert result.file_path is not None
        assert result.file_path.read_bytes() == b"hello world"

        manifest_files = list((fetch_http.MANIFEST_DIR / "my_source").glob("*.json"))
        assert len(manifest_files) == 1
        manifest = json.loads(manifest_files[0].read_text())
        assert manifest["status"] == "downloaded"
        assert manifest["sha256"] == result.sha256
        assert manifest["etag"] == '"abc"'

    def test_dest_filename_used_when_given(self, tmp_path: Path) -> None:
        fake = _FakeHttpGet([HttpResponse(status_code=200, content=b"x", headers={})])
        result = fetch_file(
            "my_source",
            "https://example.invalid/weird?query=1",
            dest_filename="clean_name.csv",
            http_get=fake,
        )
        assert result.file_path is not None
        assert result.file_path.name == "clean_name.csv"


class TestFetchFileRetries:
    def test_retries_transient_error_then_succeeds(self) -> None:
        fake = _FakeHttpGet(
            [
                ConnectionError("boom"),
                HttpResponse(status_code=200, content=b"ok", headers={}),
            ]
        )
        result = fetch_file(
            "flaky_source", "https://example.invalid/x", http_get=fake, sleep=_no_sleep
        )
        assert result.status == "downloaded"
        assert result.attempts == 2

    def test_5xx_is_retried(self) -> None:
        fake = _FakeHttpGet(
            [
                HttpResponse(status_code=503, content=b"", headers={}),
                HttpResponse(status_code=200, content=b"ok", headers={}),
            ]
        )
        result = fetch_file(
            "flaky_5xx", "https://example.invalid/x", http_get=fake, sleep=_no_sleep
        )
        assert result.status == "downloaded"
        assert result.attempts == 2

    def test_raises_after_exhausting_retries(self) -> None:
        fake = _FakeHttpGet([ConnectionError("a"), ConnectionError("b"), ConnectionError("c")])
        with pytest.raises(FetchError, match="failed to fetch"):
            fetch_file(
                "always_down",
                "https://example.invalid/x",
                http_get=fake,
                max_retries=3,
                sleep=_no_sleep,
            )

    def test_backoff_is_exponential(self) -> None:
        fake = _FakeHttpGet(
            [
                ConnectionError("a"),
                ConnectionError("b"),
                HttpResponse(status_code=200, content=b"ok", headers={}),
            ]
        )
        sleeps: list[float] = []
        fetch_file(
            "backoff_source",
            "https://example.invalid/x",
            http_get=fake,
            retry_backoff_seconds=1.0,
            sleep=sleeps.append,
        )
        assert sleeps == [1.0, 2.0]


class TestFetchFileSkipIfUnchanged:
    def test_304_response_skips_download_entirely(self) -> None:
        first = _FakeHttpGet(
            [HttpResponse(status_code=200, content=b"v1", headers={"ETag": '"v1-etag"'})]
        )
        first_result = fetch_file("versioned_source", "https://example.invalid/x", http_get=first)
        assert first_result.status == "downloaded"

        second = _FakeHttpGet([HttpResponse(status_code=304, content=b"", headers={})])
        second_result = fetch_file("versioned_source", "https://example.invalid/x", http_get=second)

        assert second_result.status == "unchanged"
        assert second_result.sha256 == first_result.sha256
        assert second_result.byte_size == first_result.byte_size
        # The conditional header must actually have been sent.
        assert second.calls[0]["headers"]["If-None-Match"] == '"v1-etag"'

    def test_identical_content_detected_as_unchanged_without_conditional_headers(self) -> None:
        """A server with no ETag/Last-Modified support still gets a correct
        manifest via the sha256 fallback, even though the body was
        re-transferred."""
        first = _FakeHttpGet([HttpResponse(status_code=200, content=b"same bytes", headers={})])
        first_result = fetch_file("no_etag_source", "https://example.invalid/x", http_get=first)
        assert first_result.status == "downloaded"

        second = _FakeHttpGet([HttpResponse(status_code=200, content=b"same bytes", headers={})])
        second_result = fetch_file("no_etag_source", "https://example.invalid/x", http_get=second)
        assert second_result.status == "unchanged"
        assert second_result.sha256 == first_result.sha256

    def test_fetching_twice_writes_no_new_raw_file(self) -> None:
        """development-plan.md P2.2's idempotence test: running fetch twice
        against unchanged content produces no new raw file. Manifest
        entries are timestamped (not just dated), so a same-day re-run adds
        a second entry rather than overwriting the first -- each run's
        provenance (retrieved_at, attempts) is real history, not something
        a later same-day run should erase."""
        first = _FakeHttpGet(
            [HttpResponse(status_code=200, content=b"stable", headers={"ETag": '"e1"'})]
        )
        fetch_file("idempotent_source", "https://example.invalid/x", http_get=first)
        raw_files_after_first = list((fetch_http.RAW_DIR / "idempotent_source").glob("*"))
        assert len(raw_files_after_first) == 1

        second = _FakeHttpGet([HttpResponse(status_code=304, content=b"", headers={})])
        fetch_file("idempotent_source", "https://example.invalid/x", http_get=second)

        manifest_files = list((fetch_http.MANIFEST_DIR / "idempotent_source").glob("*.json"))
        raw_files_after_second = list((fetch_http.RAW_DIR / "idempotent_source").glob("*"))
        assert len(manifest_files) == 2  # each run recorded, not overwritten
        assert len(raw_files_after_second) == 1  # no new raw file written

    def test_changed_content_is_downloaded_again(self) -> None:
        first = _FakeHttpGet([HttpResponse(status_code=200, content=b"v1", headers={})])
        fetch_file("changing_source", "https://example.invalid/x", http_get=first)

        second = _FakeHttpGet([HttpResponse(status_code=200, content=b"v2", headers={})])
        second_result = fetch_file("changing_source", "https://example.invalid/x", http_get=second)
        assert second_result.status == "downloaded"
        assert second_result.file_path is not None
        assert second_result.file_path.read_bytes() == b"v2"

    def test_missing_local_file_forces_real_download_not_unchanged(self) -> None:
        """A committed manifest with no matching local file (a fresh clone
        or CI runner -- data/raw/ is gitignored) must not be trusted as
        "unchanged": no conditional headers are sent, and a real download
        happens even though the manifest's sha256 would otherwise match."""
        first = _FakeHttpGet(
            [HttpResponse(status_code=200, content=b"content", headers={"ETag": '"e1"'})]
        )
        first_result = fetch_file("clone_source", "https://example.invalid/x", http_get=first)
        assert first_result.file_path is not None
        first_result.file_path.unlink()  # simulate a fresh clone: manifest exists, file doesn't

        second = _FakeHttpGet([HttpResponse(status_code=200, content=b"content", headers={})])
        second_result = fetch_file("clone_source", "https://example.invalid/x", http_get=second)

        assert second_result.status == "downloaded"
        assert second_result.file_path is not None
        assert second_result.file_path.read_bytes() == b"content"
        # No conditional headers should have been sent -- there was nothing
        # to confirm "unchanged" against.
        assert "If-None-Match" not in second.calls[0]["headers"]

    def test_url_change_does_not_reuse_stale_conditional_headers(self) -> None:
        """A source whose discovered download URL changes (a new
        hash-named annual release) must not send the previous release's
        ETag/Last-Modified to the new URL -- a server keying its 304 check
        off If-Modified-Since alone could otherwise wrongly confirm
        "unchanged" for a genuinely new file."""
        first = _FakeHttpGet(
            [HttpResponse(status_code=200, content=b"2023 data", headers={"ETag": '"2023-etag"'})]
        )
        fetch_file("annual_source", "https://example.invalid/2023.xlsx", http_get=first)

        second = _FakeHttpGet(
            [HttpResponse(status_code=200, content=b"2024 data", headers={"ETag": '"2024-etag"'})]
        )
        second_result = fetch_file(
            "annual_source", "https://example.invalid/2024.xlsx", http_get=second
        )
        assert "If-None-Match" not in second.calls[0]["headers"]
        assert second_result.status == "downloaded"
        assert second_result.file_path is not None
        assert second_result.file_path.read_bytes() == b"2024 data"


class TestFetchFileNonRetryableErrors:
    def test_404_is_not_retried(self) -> None:
        fake = _FakeHttpGet([HttpResponse(status_code=404, content=b"", headers={})])
        with pytest.raises(FetchError, match="404"):
            fetch_file(
                "missing_source", "https://example.invalid/x", http_get=fake, sleep=_no_sleep
            )
        assert len(fake.calls) == 1  # not retried

    def test_403_is_not_retried(self) -> None:
        fake = _FakeHttpGet([HttpResponse(status_code=403, content=b"", headers={})])
        with pytest.raises(FetchError, match="403"):
            fetch_file(
                "forbidden_source", "https://example.invalid/x", http_get=fake, sleep=_no_sleep
            )
        assert len(fake.calls) == 1

    def test_429_is_retried(self) -> None:
        fake = _FakeHttpGet(
            [
                HttpResponse(status_code=429, content=b"", headers={}),
                HttpResponse(status_code=200, content=b"ok", headers={}),
            ]
        )
        result = fetch_file(
            "rate_limited_source", "https://example.invalid/x", http_get=fake, sleep=_no_sleep
        )
        assert result.status == "downloaded"
        assert len(fake.calls) == 2


class TestRowCountTracking:
    def test_previous_row_count_is_none_when_no_manifest(self) -> None:
        assert fetch_http.previous_row_count("never_fetched_source") is None

    def test_record_and_read_back_row_count(self) -> None:
        fake = _FakeHttpGet([HttpResponse(status_code=200, content=b"data", headers={})])
        fetch_file("counted_source", "https://example.invalid/x", http_get=fake)
        assert fetch_http.previous_row_count("counted_source") is None  # not recorded yet

        fetch_http.record_row_count("counted_source", 42)
        assert fetch_http.previous_row_count("counted_source") == 42

    def test_record_row_count_without_manifest_raises(self) -> None:
        with pytest.raises(FetchError, match="No manifest"):
            fetch_http.record_row_count("nonexistent_source", 1)
