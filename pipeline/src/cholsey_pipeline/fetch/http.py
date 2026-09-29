"""Generic HTTP fetch framework (development-plan.md Phase 2, P2.2).

One function, `fetch_file`, that every Phase 2 fetcher (P2.3-P2.9) builds
on: downloads a URL with retries, records sha256/byte size/retrieved_at,
skips the download if the upstream file is unchanged (by ETag or
Last-Modified, falling back to a sha256 comparison against the last
manifest if neither header is present), and writes a manifest entry to
`data/manifest/<source_id>/<date>.json` (development-plan.md §2.2's target
layout).

Design note, matching geography/boundaries.py's pattern (Phase 1): network
I/O is isolated behind an injectable `http_get` callable, so tests can
exercise retry/skip/manifest logic entirely offline (development-plan.md
§5.1) without a real fetcher or a mocked `requests` module -- just pass a
fake `http_get`.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import requests

from cholsey_pipeline.registry import REPO_ROOT

RAW_DIR = REPO_ROOT / "data" / "raw"
MANIFEST_DIR = REPO_ROOT / "data" / "manifest"


class FetchError(RuntimeError):
    """Raised when a download fails after exhausting retries."""


@dataclass(frozen=True)
class HttpResponse:
    """The subset of a `requests.Response` this module actually needs --
    letting tests build one directly instead of constructing a real
    `requests.Response` or mocking the `requests` library."""

    status_code: int
    content: bytes
    headers: dict[str, str]

    def raise_for_status(self) -> None:
        if 400 <= self.status_code:
            raise requests.HTTPError(f"HTTP {self.status_code}")


HttpGet = Callable[..., HttpResponse]


def _default_http_get(url: str, *, timeout: int, headers: dict[str, str]) -> HttpResponse:
    response = requests.get(url, timeout=timeout, headers=headers)
    return HttpResponse(
        status_code=response.status_code,
        content=response.content,
        headers=dict(response.headers),
    )


@dataclass(frozen=True)
class FetchResult:
    """What happened when fetching one source, and everything needed to
    write a provenance-complete manifest entry for it."""

    source_id: str
    url: str
    status: str
    """"downloaded" (new content saved), "unchanged" (skipped, matches the
    last fetch) or "error" (raised as FetchError instead, this value is
    only reachable in principle)."""
    file_path: Path | None
    sha256: str
    byte_size: int
    retrieved_at: str
    etag: str | None
    last_modified: str | None
    attempts: int


def _latest_manifest(source_id: str) -> dict[str, Any] | None:
    source_manifest_dir = MANIFEST_DIR / source_id
    if not source_manifest_dir.is_dir():
        return None
    manifest_files = sorted(source_manifest_dir.glob("*.json"))
    if not manifest_files:
        return None
    return json.loads(manifest_files[-1].read_text(encoding="utf-8"))


def fetch_file(
    source_id: str,
    url: str,
    *,
    dest_filename: str | None = None,
    timeout: int = 30,
    max_retries: int = 3,
    retry_backoff_seconds: float = 1.0,
    http_get: HttpGet = _default_http_get,
    write_manifest: bool = True,
    sleep: Callable[[float], None] = time.sleep,
) -> FetchResult:
    """Fetch `url`, skip re-downloading if unchanged, and record a manifest
    entry. Retries transient failures (connection errors, HTTP 5xx) up to
    `max_retries` times with exponential backoff, then raises FetchError.

    Skip-if-unchanged: if the most recent manifest entry for this
    `source_id` has an `etag`/`last_modified`, this sends them as
    `If-None-Match`/`If-Modified-Since` -- a server that supports
    conditional requests replies 304 Not Modified with no body, so the
    file is genuinely not re-downloaded (not just re-fetched and compared
    after the fact). A server that ignores the conditional headers (or one
    fetched for the first time) falls back to downloading and comparing by
    sha256; only in that fallback case is the download itself not skipped,
    though the manifest still correctly records "unchanged".

    `http_get` defaults to a thin wrapper around `requests.get` -- inject a
    fake for offline tests (development-plan.md §5.1). It must return an
    HttpResponse (status_code, content, headers).
    """
    previous = _latest_manifest(source_id)
    request_headers: dict[str, str] = {}
    if previous:
        if previous.get("etag"):
            request_headers["If-None-Match"] = previous["etag"]
        if previous.get("last_modified"):
            request_headers["If-Modified-Since"] = previous["last_modified"]

    attempts = 0
    last_error: Exception | None = None
    response: HttpResponse | None = None

    while attempts < max_retries:
        attempts += 1
        try:
            response = http_get(url, timeout=timeout, headers=request_headers)
            if response.status_code >= 500:
                raise requests.HTTPError(f"HTTP {response.status_code}")
            if response.status_code != 304:
                response.raise_for_status()
            break
        except (requests.RequestException, OSError) as exc:
            last_error = exc
            response = None
            if attempts < max_retries:
                sleep(retry_backoff_seconds * (2 ** (attempts - 1)))

    if response is None:
        raise FetchError(
            f"'{source_id}': failed to fetch {url} after {attempts} attempt(s): {last_error}"
        )

    retrieved_at = datetime.now(UTC).isoformat()

    if response.status_code == 304:
        # The server confirmed nothing changed -- no body was transferred.
        assert previous is not None  # a 304 only makes sense if we sent conditional headers
        result = FetchResult(
            source_id=source_id,
            url=url,
            status="unchanged",
            file_path=Path(previous["file_path"]) if previous.get("file_path") else None,
            sha256=previous["sha256"],
            byte_size=previous["byte_size"],
            retrieved_at=retrieved_at,
            etag=previous.get("etag"),
            last_modified=previous.get("last_modified"),
            attempts=attempts,
        )
        if write_manifest:
            _write_manifest(result)
        return result

    etag = response.headers.get("ETag")
    last_modified = response.headers.get("Last-Modified")
    sha256 = hashlib.sha256(response.content).hexdigest()
    byte_size = len(response.content)

    # Fallback for servers that ignore conditional headers (or download
    # errors were the reason for the freshly-added etag lines above): if
    # the content is byte-identical to last time, it's still "unchanged"
    # even though a fresh copy was transferred.
    unchanged = bool(previous and previous.get("sha256") == sha256)

    if unchanged:
        file_path = Path(previous["file_path"]) if previous.get("file_path") else None
        result = FetchResult(
            source_id=source_id,
            url=url,
            status="unchanged",
            file_path=file_path,
            sha256=sha256,
            byte_size=byte_size,
            retrieved_at=retrieved_at,
            etag=etag,
            last_modified=last_modified,
            attempts=attempts,
        )
    else:
        dest_dir = RAW_DIR / source_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        filename = dest_filename or url.rsplit("/", 1)[-1] or "download"
        file_path = dest_dir / filename
        file_path.write_bytes(response.content)
        result = FetchResult(
            source_id=source_id,
            url=url,
            status="downloaded",
            file_path=file_path,
            sha256=sha256,
            byte_size=byte_size,
            retrieved_at=retrieved_at,
            etag=etag,
            last_modified=last_modified,
            attempts=attempts,
        )

    if write_manifest:
        _write_manifest(result)

    return result


def _write_manifest(result: FetchResult) -> None:
    source_dir = MANIFEST_DIR / result.source_id
    source_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = source_dir / f"{date.today().isoformat()}.json"
    manifest = {
        "source_id": result.source_id,
        "url": result.url,
        "status": result.status,
        "file_path": str(result.file_path) if result.file_path else None,
        "sha256": result.sha256,
        "byte_size": result.byte_size,
        "retrieved_at": result.retrieved_at,
        "etag": result.etag,
        "last_modified": result.last_modified,
        "attempts": result.attempts,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
