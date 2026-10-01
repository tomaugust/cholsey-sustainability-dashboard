"""Fetch Forest Research's UK Ward Canopy Cover for a set of wards.

development-plan.md Phase 2, P2.3. See config/sources.yaml's
`forest_research_canopy` entry and ADR-0006 for the full investigation:
this dataset is citizen-science i-Tree Canopy data collected ward-by-ward
between 2018 and 2022 (each ward carries its own `survyear`), not a single
"2020" survey as originally assumed. Cholsey ward's own record uses
wardcode E05009737 (the December 2018 ward edition) rather than the
current E05011701 -- verified geometrically close enough to the current
ward boundary not to need correcting (see ADR-0006), but callers must pass
the *dataset's own* ward code, not assume it matches the current ONS one.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode

import requests

from cholsey_pipeline.contracts import SOURCE_CONTRACTS, validate_row_count, validate_schema
from cholsey_pipeline.fetch.http import (
    MANIFEST_DIR,
    fetch_file,
    previous_row_count,
    record_row_count,
)

QUERY_URL = (
    "https://services2.arcgis.com/mHXjwgl3OARRqqD4/arcgis/rest/services/"
    "UK_Ward_Canopy_Cover/FeatureServer/0/query"
)
"""Verified live 2026-09-29 (P2.3) -- see the module docstring and ADR-0006
for how this was found (the ArcGIS Hub item API, not a guess)."""


class CanopyFetchError(RuntimeError):
    """Raised when the Forest Research canopy service returns an error body
    or an unexpected response shape."""


@dataclass(frozen=True)
class WardCanopyRecord:
    """One ward's i-Tree Canopy assessment."""

    ward_code: str
    ward_name: str
    designated: str
    """"Urban" or "Rural" (wards over 1,000 Ha are classed Rural)."""
    survey_year: int
    percent_canopy_cover: float
    standard_error: float
    number_of_points: int
    country: str = ""
    """Only populated by `fetch_ward_canopy_for_country` (P3.2's national
    row) -- `fetch_ward_canopy`'s named-ward queries don't request this
    field, so it stays `""` for every subject/comparator/district call
    site."""
    ward_area_m2: float | None = None
    """The dataset's OWN ward area (`warea`), in m2 -- only populated by
    `fetch_ward_canopy_for_country`. Verified live against Cholsey's own
    ward (E05009737): 66,557,077.88 m2, matching the ~66 km2 figure
    already used elsewhere in this codebase (metrics/canopy.py's module
    docstring), so this is a real, usable area field straight from Forest
    Research's own dataset -- no need to separately join national wards
    against current ONS ward boundaries for P3.2's national row."""


def parse_canopy_response(payload: dict[str, Any]) -> list[WardCanopyRecord]:
    """Parse an ArcGIS REST JSON response into WardCanopyRecords.

    Pure function, no network -- exercised by fixture-based unit tests
    (development-plan.md §5.1).
    """
    if "error" in payload:
        raise CanopyFetchError(
            f"UK Ward Canopy Cover service returned an error: {payload['error']}"
        )
    features = payload.get("features")
    if not features:
        raise CanopyFetchError("UK Ward Canopy Cover response had no features")

    records = []
    for feature in features:
        attrs = feature["attributes"]
        records.append(
            WardCanopyRecord(
                ward_code=attrs["wardcode"],
                ward_name=attrs["wardname"],
                designated=attrs["designated"],
                survey_year=attrs["survyear"],
                percent_canopy_cover=attrs["percancov"],
                standard_error=attrs["standerr"],
                number_of_points=attrs["numpts"],
                country=attrs.get("country", ""),
                ward_area_m2=attrs.get("warea"),
            )
        )
    return records


def fetch_ward_canopy(ward_codes: list[str]) -> list[WardCanopyRecord]:
    """Fetch canopy records for the given Forest Research `wardcode`
    values live from the service, via `fetch.http.fetch_file` so the
    request gets the same provenance (manifest, sha256, retrieved_at) as
    every other Phase 2 source -- CLAUDE.md's "provenance on every value"
    rule -- rather than calling `requests` directly and recording nothing.
    Also validates the result against `contracts.SOURCE_CONTRACTS`.

    Note these are the dataset's OWN ward codes (see the module docstring
    -- Cholsey's is E05009737, an old/retired edition, not the current
    E05011701), not necessarily current ONS ward codes. Look them up by
    name first if unsure (`wardname LIKE '%...%'`) rather than assuming.
    """
    quoted = ",".join(f"'{c}'" for c in ward_codes)
    params = {
        "where": f"wardcode IN ({quoted})",
        "outFields": "wardcode,wardname,designated,survyear,percancov,standerr,numpts",
        "returnGeometry": "false",
        "f": "json",
    }
    full_url = f"{QUERY_URL}?{urlencode(params)}"
    manifest_source_id = "forest_research_canopy"
    # The previous row count is only a valid baseline for the SAME set of
    # ward codes -- fetching 1 ward and then 9 wards is not a "900%
    # change," it's a different query (cycle-2 review finding).
    query_signature = ",".join(sorted(ward_codes))
    previous_count = previous_row_count(manifest_source_id, query_signature)
    result = fetch_file(manifest_source_id, full_url, dest_filename="ward_canopy_response.json")
    if result.file_path is None:
        raise RuntimeError(f"fetch_file returned no file_path for {manifest_source_id}")
    payload = json.loads(result.file_path.read_text(encoding="utf-8"))
    records = parse_canopy_response(payload)
    contract = SOURCE_CONTRACTS["forest_research_canopy"]
    validate_schema(records, contract)
    validate_row_count(contract, len(records), previous_count)
    record_row_count(manifest_source_id, len(records), query_signature)
    return records


def fetch_ward_canopy_for_country(
    country: str,
    *,
    page_size: int = 1000,
    timeout: int = 60,
) -> list[WardCanopyRecord]:
    """Fetch every ward canopy record for a whole country (e.g.
    `"England"`), live, for P3.2's national row. Confirmed live
    2026-10-01: the service's own `maxRecordCount` is 1000 and England
    alone has 6,135 ward records (status always `"Completed"`), so this
    pages via `resultOffset`/`resultRecordCount` the same way
    `geography.boundaries.fetch_boundary` does for national-scale layers
    -- a single unpaginated request would silently return only the first
    1,000 wards with no indication anything was missing.

    Also requests the dataset's own `warea`/`country` fields (not
    requested by `fetch_ward_canopy`'s named-ward queries) -- `warea` is
    a real, usable ward area in m2 straight from Forest Research's own
    dataset (verified live against Cholsey's own ward: 66,557,077.88 m2,
    matching the ~66 km2 figure already used elsewhere), so there's no
    need to separately join thousands of national wards against current
    ONS ward boundaries just to area-weight them -- `metrics.canopy
    .compute_national_canopy_row` uses `ward_area_m2` directly.

    Bypasses `fetch_file` and writes its own merged manifest entry
    directly (same reasoning as `fetch_boundary`: several pages need
    merging into one provenance record, not one manifest entry per page),
    but still goes through the same `contracts` schema/row-count checks
    as `fetch_ward_canopy`.
    """
    manifest_source_id = "forest_research_canopy"
    query_signature = f"country={country}"
    previous_count = previous_row_count(manifest_source_id, query_signature)

    all_features: list[dict[str, Any]] = []
    offset = 0
    last_url = ""
    while True:
        params = {
            "where": f"country='{country}'",
            "outFields": (
                "wardcode,wardname,designated,survyear,percancov,standerr,numpts,warea,country"
            ),
            "returnGeometry": "false",
            "f": "json",
            "resultRecordCount": page_size,
            "resultOffset": offset,
        }
        last_url = f"{QUERY_URL}?{urlencode(params)}"
        response = requests.get(last_url, timeout=timeout)
        response.raise_for_status()
        page = response.json()
        if "error" in page:
            raise CanopyFetchError(
                f"UK Ward Canopy Cover service returned an error: {page['error']}"
            )
        page_features = page.get("features") or []
        all_features.extend(page_features)
        if len(page_features) < page_size:
            break
        offset += len(page_features)

    merged_payload = {"features": all_features}
    records = parse_canopy_response(merged_payload)
    # A separate, slightly relaxed contract from the per-ward
    # `forest_research_canopy` one above: a real, documented upstream
    # finding (verified live 2026-10-01) is that 26 of England's 6,135
    # ward records have a null standard_error/number_of_points but a
    # real percent_canopy_cover/ward_area_m2 -- see contracts.py's
    # `forest_research_canopy_national` entry for the full rationale.
    contract = SOURCE_CONTRACTS["forest_research_canopy_national"]
    validate_schema(records, contract)
    validate_row_count(contract, len(records), previous_count)

    merged_bytes = json.dumps(merged_payload, sort_keys=True).encode("utf-8")
    retrieved_at = datetime.now(UTC).isoformat()
    manifest_dir = MANIFEST_DIR / manifest_source_id
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"{retrieved_at.replace(':', '-')}.json"
    manifest_path.write_text(
        json.dumps(
            {
                "source_id": manifest_source_id,
                "query_url": QUERY_URL,
                "request_url": last_url,
                "where_clause": f"country='{country}'",
                "query_signature": query_signature,
                "feature_count": len(all_features),
                "row_count": len(records),
                "response_sha256": hashlib.sha256(merged_bytes).hexdigest(),
                "response_bytes": len(merged_bytes),
                "retrieved_at": retrieved_at,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return records
