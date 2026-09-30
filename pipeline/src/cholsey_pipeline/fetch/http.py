"""Generic HTTP fetch framework (development-plan.md Phase 2, P2.2).

One function, `fetch_file`, that every Phase 2 fetcher (P2.3-P2.9) builds
on: downloads a URL with retries, records sha256/byte size/retrieved_at,
skips the download if the upstream file is unchanged (by ETag or
Last-Modified, falling back to a sha256 comparison against the last
manifest if neither header is present), and writes a manifest entry to
`data/manifest/<source_id>/<timestamp>.json` (development-plan.md §2.2's
target layout).

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
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from cholsey_pipeline.registry import REPO_ROOT

RAW_DIR = REPO_ROOT / "data" / "raw"
MANIFEST_DIR = REPO_ROOT / "data" / "manifest"


class FetchError(RuntimeError):
    """Raised when a download fails after exhausting retries, or
    immediately on a non-retryable client error (4xx other than 429)."""


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


def _latest_manifest_path(source_id: str) -> Path | None:
    source_manifest_dir = MANIFEST_DIR / source_id
    if not source_manifest_dir.is_dir():
        return None
    manifest_files = sorted(source_manifest_dir.glob("*.json"))
    if not manifest_files:
        return None
    return manifest_files[-1]


def _latest_manifest(source_id: str) -> dict[str, Any] | None:
    manifest_path = _latest_manifest_path(source_id)
    if manifest_path is None:
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def previous_row_count(source_id: str) -> int | None:
    """The previous run's parsed row count, for
    `contracts.validate_row_count` -- `None` if there's no previous
    manifest, or it predates row-count tracking (or this run's own
    manifest, if called after `fetch_file` but before `record_row_count`).
    Must be called before `fetch_file` overwrites "latest" for this
    `source_id`, or the caller will be comparing a run against itself.
    """
    manifest = _latest_manifest(source_id)
    if manifest is None:
        return None
    return manifest.get("row_count")


def record_row_count(source_id: str, row_count: int) -> None:
    """Record `row_count` (the number of parsed records this run
    produced) on the most recent manifest entry for `source_id`. Parsing
    happens after `fetch_file` writes its manifest entry (the row count
    isn't known until then), so this updates that same entry in place
    rather than writing a new one."""
    manifest_path = _latest_manifest_path(source_id)
    if manifest_path is None:
        raise FetchError(f"No manifest found for '{source_id}' to record a row count against")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["row_count"] = row_count
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


_NON_RETRYABLE_STATUS_CODES = range(400, 500)
_RETRYABLE_CLIENT_STATUS_CODES = {429}


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
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> FetchResult:
    """Fetch `url`, skip re-downloading if unchanged, and record a manifest
    entry. Retries transient failures (connection errors, HTTP 5xx, and
    429) up to `max_retries` times with exponential backoff. Any other 4xx
    (a stale discovered URL returning 404, an auth failure, ...) is not
    retried -- it's a `FetchError` immediately, since retrying it can only
    waste time before failing anyway.

    Skip-if-unchanged: if the most recent manifest entry for this
    `source_id` was fetched from the *same URL* and has an
    `etag`/`last_modified`, this sends them as
    `If-None-Match`/`If-Modified-Since` -- a server that supports
    conditional requests replies 304 Not Modified with no body, so the
    file is genuinely not re-downloaded (not just re-fetched and compared
    after the fact). A source whose discovered download URL changes (a
    new hash-named annual release, say) is never sent the previous
    release's conditional headers, since a server that keys 304 checks off
    `If-Modified-Since` alone could otherwise wrongly confirm "unchanged"
    for a genuinely new file at the new URL.

    A server that ignores the conditional headers (or one fetched for the
    first time) falls back to downloading and comparing by sha256; only in
    that fallback case is the download itself not skipped, though the
    manifest still correctly records "unchanged". Either way, "unchanged"
    is only trusted if the previous manifest's file still exists on disk
    -- `data/raw/` is gitignored, so a fresh clone or CI runner has a
    committed manifest but no local file, and the previous run's *content*
    (freshly downloaded either way) is written out instead of skipped.

    `http_get` defaults to a thin wrapper around `requests.get` -- inject a
    fake for offline tests (development-plan.md §5.1). It must return an
    HttpResponse (status_code, content, headers).
    """
    previous = _latest_manifest(source_id)
    previous_for_url = previous if previous and previous.get("url") == url else None
    previous_file_exists = bool(
        previous_for_url
        and previous_for_url.get("file_path")
        and (RAW_DIR / previous_for_url["file_path"]).exists()
    )

    request_headers: dict[str, str] = {}
    if previous_for_url and previous_file_exists:
        if previous_for_url.get("etag"):
            request_headers["If-None-Match"] = previous_for_url["etag"]
        if previous_for_url.get("last_modified"):
            request_headers["If-Modified-Since"] = previous_for_url["last_modified"]
    # If previous_for_url exists but the file doesn't (fresh clone/CI), no
    # conditional headers are sent at all -- "unchanged" is meaningless
    # without a local file to serve, so there's no point asking for a 304.

    total_attempts = 0

    def _request(headers: dict[str, str]) -> HttpResponse:
        nonlocal total_attempts
        attempts = 0
        last_error: Exception | None = None
        while attempts < max_retries:
            attempts += 1
            total_attempts += 1
            try:
                response = http_get(url, timeout=timeout, headers=headers)
                if (
                    response.status_code >= 500
                    or response.status_code in _RETRYABLE_CLIENT_STATUS_CODES
                ):
                    raise requests.HTTPError(f"HTTP {response.status_code}")
                if response.status_code in _NON_RETRYABLE_STATUS_CODES:
                    raise FetchError(
                        f"'{source_id}': {url} returned HTTP {response.status_code} "
                        "(not retried -- not a transient failure)"
                    )
                if response.status_code != 304:
                    response.raise_for_status()
                return response
            except (requests.RequestException, OSError) as exc:
                last_error = exc
                if attempts < max_retries:
                    sleep(retry_backoff_seconds * (2 ** (attempts - 1)))
        raise FetchError(
            f"'{source_id}': failed to fetch {url} after {attempts} attempt(s): {last_error}"
        )

    response = _request(request_headers)

    retrieved_at = now().isoformat()

    if response.status_code == 304:
        # The server confirmed nothing changed, and we still have the file
        # from last time -- no body was transferred, nothing to re-save.
        # (A 304 can only happen here if conditional headers were sent,
        # which only happens when previous_file_exists is already True.)
        assert previous_for_url is not None
        result = FetchResult(
            source_id=source_id,
            url=url,
            status="unchanged",
            file_path=RAW_DIR / previous_for_url["file_path"],
            sha256=previous_for_url["sha256"],
            byte_size=previous_for_url["byte_size"],
            retrieved_at=retrieved_at,
            etag=previous_for_url.get("etag"),
            last_modified=previous_for_url.get("last_modified"),
            attempts=total_attempts,
        )
        if write_manifest:
            _write_manifest(result)
        return result

    etag = response.headers.get("ETag")
    last_modified = response.headers.get("Last-Modified")
    sha256 = hashlib.sha256(response.content).hexdigest()
    byte_size = len(response.content)

    # Fallback for servers that ignore conditional headers: if the content
    # is byte-identical to last time AND we still have that file locally,
    # it's still "unchanged" even though a fresh copy was transferred. If
    # we don't have the file locally, save the freshly-fetched bytes
    # rather than discarding them.
    unchanged = bool(
        previous_for_url and previous_for_url.get("sha256") == sha256 and previous_file_exists
    )

    if unchanged:
        assert previous_for_url is not None
        result = FetchResult(
            source_id=source_id,
            url=url,
            status="unchanged",
            file_path=RAW_DIR / previous_for_url["file_path"],
            sha256=sha256,
            byte_size=byte_size,
            retrieved_at=retrieved_at,
            etag=etag,
            last_modified=last_modified,
            attempts=total_attempts,
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
            attempts=total_attempts,
        )

    if write_manifest:
        _write_manifest(result)

    return result


def _write_manifest(result: FetchResult) -> None:
    source_dir = MANIFEST_DIR / result.source_id
    source_dir.mkdir(parents=True, exist_ok=True)
    # Timestamped (not just dated) so two fetches of the same source on
    # the same UTC day don't overwrite each other's manifest entry.
    timestamp = result.retrieved_at.replace(":", "-").replace("+00:00", "Z")
    manifest_path = source_dir / f"{timestamp}.json"
    file_path = result.file_path
    stored_path = str(file_path.relative_to(RAW_DIR)) if file_path else None
    manifest = {
        "source_id": result.source_id,
        "url": result.url,
        "status": result.status,
        "file_path": stored_path,
        "sha256": result.sha256,
        "byte_size": result.byte_size,
        "retrieved_at": result.retrieved_at,
        "etag": result.etag,
        "last_modified": result.last_modified,
        "attempts": result.attempts,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
