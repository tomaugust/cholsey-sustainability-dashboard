"""Fetch EPC (Energy Performance Certificate) register data, filtered to
Cholsey's postcodes (development-plan.md Phase 2, P2.9, stretch).

**Feature-flagged**: this source needs a bearer API key from a free
registration this project hasn't completed yet (see `config/sources.yaml`'s
`epc_register` entry) -- development-plan.md P2.9 explicitly says to "build
behind a feature flag, so the pipeline works without it." Every live-fetching
function here requires an explicit `api_key`; passing `None` raises
`EpcApiKeyMissing` loudly rather than the pipeline silently skipping metric 7
(spec §3's optional EPC/insulation stretch metric). Parsing logic is fully
testable offline against a fixture, independent of the key.

API structure confirmed live 2026-09-30 by reading
https://get-energy-performance-data.communities.gov.uk/api-technical-documentation/
(the successor to the older opendatacommunities.org EPC API, which now
redirects here): `search-certificates/domestic` endpoint, `Authorization:
Bearer <token>` header, JSON response, `postcode`/`council`/`date_start`/
`date_end` query filters, pagination via `current_page`/`page_size` (max
5000/page), rate limit 6000 requests/5 minutes/IP. Real record VALUES are
not available without a registered key -- the field names below are
verbatim from the live API documentation, not guessed, but a fully
real-values fixture isn't possible until this project has a key (see
`Not done` in the P2.9 worklog entry).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

EPC_DOMESTIC_SEARCH_URL = (
    "https://api.get-energy-performance-data.communities.gov.uk/api/domestic/search"
)
"""Verified live 2026-09-30 (P2.9) against the current API technical docs."""

MAX_PAGE_SIZE = 5000


class EpcApiKeyMissing(RuntimeError):
    """Raised when a live EPC fetch is attempted without an API key -- the
    feature flag this module implements (development-plan.md P2.9)."""


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
    """Parse the JSON body of a `search-certificates/domestic` response
    into records. Pure function -- tested against a fixture built from the
    live API documentation's own field names (see module docstring for why
    this isn't a real-values fixture like every other Phase 2 fetcher's).
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


def fetch_domestic_certificates(
    postcode: str, api_key: str | None, *, page_size: int = MAX_PAGE_SIZE
) -> list[EpcCertificateRecord]:
    """Live: fetch all domestic EPC certificates for `postcode`.

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
    response = requests.get(
        EPC_DOMESTIC_SEARCH_URL,
        params={"postcode": postcode, "current_page": 1, "page_size": page_size},
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    return parse_domestic_search_response(response.json())
