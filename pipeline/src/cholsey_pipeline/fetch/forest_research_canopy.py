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

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from cholsey_pipeline.contracts import SOURCE_CONTRACTS, validate_row_count, validate_schema
from cholsey_pipeline.fetch.http import fetch_file, previous_row_count, record_row_count

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
    previous_count = previous_row_count(manifest_source_id)
    result = fetch_file(manifest_source_id, full_url, dest_filename="ward_canopy_response.json")
    if result.file_path is None:
        raise RuntimeError(f"fetch_file returned no file_path for {manifest_source_id}")
    payload = json.loads(result.file_path.read_text(encoding="utf-8"))
    records = parse_canopy_response(payload)
    contract = SOURCE_CONTRACTS["forest_research_canopy"]
    validate_schema(records, contract)
    validate_row_count(contract, len(records), previous_count)
    record_row_count(manifest_source_id, len(records))
    return records
