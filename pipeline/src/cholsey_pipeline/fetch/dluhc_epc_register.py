"""Fetch EPC (Energy Performance Certificate) register data, filtered to
Cholsey's postcodes (development-plan.md Phase 2, P2.9, stretch).

**Feature-flagged**: this source needs a bearer API key from a free
registration this project hasn't completed yet (see `config/sources.yaml`'s
`dluhc_epc_register` entry) -- development-plan.md P2.9 explicitly says to
"build behind a feature flag, so the pipeline works without it." Every
live-fetching function here requires an explicit `api_key`; passing `None`
raises `EpcApiKeyMissing` loudly rather than the pipeline silently skipping
metric 7 (spec §3's optional EPC/insulation stretch metric). Parsing logic
is fully testable offline against a fixture, independent of the key.

API structure confirmed live 2026-09-30 by reading
https://get-energy-performance-data.communities.gov.uk/api-technical-documentation/
(the successor to the older opendatacommunities.org EPC API, which now
redirects here). The docs page's own URL slug is
`.../api-technical-documentation/search-certificates/domestic` (a
documentation path, not an API path) -- re-verified directly against that
page's own "Method"/curl example that the real request path is
`GET /api/domestic/search` against `api.get-energy-performance-data.
communities.gov.uk`, i.e. `EPC_DOMESTIC_SEARCH_URL` below, not the docs
slug. `Authorization: Bearer <token>` header, JSON response,
`postcode`/`council`/`date_start`/`date_end` query filters, pagination via
`current_page`/`page_size` (max 5000/page) with a `pagination` object
(`totalResults`, `currentPage`, `pageSize`) in the response, rate limit
6000 requests/5 minutes/IP. Real record VALUES are not available without a
registered key -- the field names below are verbatim from the live API
documentation, not guessed, but a fully real-values fixture isn't possible
until this project has a key (see `Not done` in the P2.9 worklog entry).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from cholsey_pipeline.contracts import SOURCE_CONTRACTS, validate_row_count, validate_schema
from cholsey_pipeline.fetch.http import (
    HttpGet,
    _default_http_get,
    fetch_file,
    previous_row_count,
    record_row_count,
)

EPC_DOMESTIC_SEARCH_URL = (
    "https://api.get-energy-performance-data.communities.gov.uk/api/domestic/search"
)
"""Verified live 2026-09-30 (P2.9) against the current API technical docs."""

MAX_PAGE_SIZE = 5000


class EpcApiKeyMissing(RuntimeError):
    """Raised when a live EPC fetch is attempted without an API key -- the
    feature flag this module implements (development-plan.md P2.9)."""


class EpcPaginationError(RuntimeError):
    """Raised when the API's own pagination metadata doesn't behave as
    documented (e.g. `currentPage` never advances, or more pages are
    claimed than `totalResults`/`pageSize` can account for) -- a hard stop
    rather than looping indefinitely re-fetching the same page."""


@dataclass(frozen=True)
class EpcCertificateRecord:
    """One domestic EPC certificate, the fields this project needs for
    metric 7 (spec §3's optional EPC/insulation stretch)."""

    certificate_number: str
    postcode: str
    council: str
    current_energy_efficiency_band: str
    registration_date: str
    uprn: str | None


def parse_domestic_search_response(payload: dict[str, Any]) -> list[EpcCertificateRecord]:
    """Parse the JSON body of one page of a `/api/domestic/search`
    response into records. Pure function -- tested against a fixture built
    from the live API documentation's own field names (see module
    docstring for why this isn't a real-values fixture like every other
    Phase 2 fetcher's).
    """
    records = []
    for row in payload.get("data", []):
        records.append(
            EpcCertificateRecord(
                certificate_number=row["certificateNumber"],
                postcode=row["postcode"],
                council=row["council"],
                current_energy_efficiency_band=row["currentEnergyEfficiencyBand"],
                registration_date=row["registrationDate"],
                uprn=row.get("uprn"),
            )
        )
    return records


def has_more_pages(payload: dict[str, Any]) -> bool:
    """Whether a `/api/domestic/search` response's `pagination` object
    indicates more results remain beyond this page. Pure function --
    tested against a fixture, same as `parse_domestic_search_response`.
    Treats a missing/malformed `pagination` object as "no more pages"
    rather than looping forever on an unexpected response shape.
    """
    pagination = payload.get("pagination")
    if not isinstance(pagination, dict):
        return False
    total = pagination.get("totalResults")
    current_page = pagination.get("currentPage")
    page_size = pagination.get("pageSize")
    if not all(isinstance(v, int) for v in (total, current_page, page_size)):
        return False
    return current_page * page_size < total


def fetch_domestic_certificates(
    postcode: str,
    api_key: str | None,
    *,
    page_size: int = MAX_PAGE_SIZE,
    http_get: HttpGet = _default_http_get,
) -> list[EpcCertificateRecord]:
    """Live: fetch ALL domestic EPC certificates for `postcode`, following
    pagination until the response's own `pagination` metadata says no
    pages remain -- a result set larger than one `page_size` would
    otherwise be silently truncated to just the first page.

    Each page is fetched via `fetch.http.fetch_file` (with the bearer
    token passed through as an extra header) so it gets the same
    provenance (manifest, sha256, retrieved_at) as every other Phase 2
    source, all under one `dluhc_epc_register/<postcode>` manifest history
    -- `record_row_count` after the loop updates the latest page's entry
    with the combined total across all pages.

    The loop is bounded by `ceil(totalResults / pageSize)` (from the
    first page's own pagination metadata) or a page returning no new
    `data`/an unchanged `currentPage` -- protection against an API that
    ignores `current_page` and would otherwise re-serve page 1 forever
    (untested live, since no key exists yet to exercise it against).

    Raises `EpcApiKeyMissing` if `api_key` is falsy, rather than silently
    returning no data -- callers (and `make refresh`) must treat a missing
    key as "this metric is disabled," not "this metric is zero."
    """
    if not api_key:
        raise EpcApiKeyMissing(
            "EPC register fetch requires an API key (development-plan.md P2.9's "
            "feature flag) -- none was provided. Register at "
            "https://get-energy-performance-data.communities.gov.uk/ and set it "
            "as a GitHub secret before enabling this source."
        )
    manifest_source_id = f"dluhc_epc_register/{postcode}"
    query_signature = f"postcode={postcode}"
    auth_headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    previous_count = previous_row_count(manifest_source_id, query_signature)

    all_records: list[EpcCertificateRecord] = []
    current_page = 1
    max_pages: int | None = None
    while True:
        params = {"postcode": postcode, "current_page": current_page, "page_size": page_size}
        page_url = f"{EPC_DOMESTIC_SEARCH_URL}?{urlencode(params)}"
        result = fetch_file(
            manifest_source_id,
            page_url,
            dest_filename=f"page{current_page}.json",
            extra_headers=auth_headers,
            http_get=http_get,
        )
        if result.file_path is None:
            raise RuntimeError(f"fetch_file returned no file_path for {manifest_source_id}")
        payload = json.loads(result.file_path.read_text(encoding="utf-8"))
        page_records = parse_domestic_search_response(payload)
        if not page_records and current_page > 1:
            # An empty non-first page means nothing more, regardless of
            # what the pagination metadata claims.
            break
        all_records.extend(page_records)

        if max_pages is None:
            pagination = payload.get("pagination")
            total = pagination.get("totalResults") if isinstance(pagination, dict) else None
            if isinstance(total, int) and page_size:
                max_pages = math.ceil(total / page_size) or 1

        if not has_more_pages(payload):
            break
        current_page += 1
        if max_pages is not None and current_page > max_pages:
            raise EpcPaginationError(
                f"EPC pagination for postcode {postcode!r} exceeded the expected "
                f"{max_pages} page(s) based on the first page's totalResults -- "
                "the API's pagination metadata isn't behaving as documented"
            )

    contract = SOURCE_CONTRACTS["dluhc_epc_register"]
    validate_schema(all_records, contract)
    validate_row_count(contract, len(all_records), previous_count)
    record_row_count(manifest_source_id, len(all_records), query_signature)
    return all_records
