"""Fetch ONS boundary layers from the ONS Open Geography Portal (Esri
ArcGIS REST services) and parse them into GeoDataFrames.

Covers development-plan.md Phase 1, P1.1: parish, LSOA and ward boundaries.
Each layer's dataset was looked up and verified live against the ONS
Geoportal's search API and its own FeatureServer before being hard-coded
here — see the P1.1 worklog entry for how, and CLAUDE.md's traceability
rule for why this matters: a wrong or guessed service URL would silently
poison every downstream area/apportionment calculation.

Design note: fetching (network) and parsing (pure function over a GeoJSON
dict) are kept separate so tests can exercise parsing against committed
fixtures without depending on the ONS service being reachable in CI
(development-plan.md §5.1).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import geopandas as gpd
import requests

from cholsey_pipeline.registry import REPO_ROOT

MANIFEST_DIR = REPO_ROOT / "data" / "manifest" / "boundaries"


@dataclass(frozen=True)
class BoundaryLayer:
    """One ONS boundary FeatureServer layer this pipeline knows how to fetch."""

    key: str
    """Short id used in the manifest path and error messages, e.g. 'parish_bfc'."""
    title: str
    """The dataset's title exactly as ONS Geoportal lists it (for provenance)."""
    query_url: str
    """The FeatureServer layer's /query endpoint (verified live — see module docstring)."""
    code_field: str
    """The GSS-code field name in this layer's schema, e.g. 'PARNCP23CD'."""
    name_field: str
    """The name field, e.g. 'PARNCP23NM'."""
    vintage: str
    """Human-readable vintage/edition, for provenance."""


# Verified 2026-09-28 against https://geoportal.statistics.gov.uk/api/search/v1
# (see the P1.1 worklog entry). Do not guess a URL for a new layer the way this
# one was originally almost gotten wrong — look it up via the same search API
# first (its `?q=<title words>` search over
# https://geoportal.statistics.gov.uk/api/search/v1/collections/dataset/items),
# then read the item's `properties.url` field for the real FeatureServer URL.
LAYERS: dict[str, BoundaryLayer] = {
    "parish_bfc": BoundaryLayer(
        key="parish_bfc",
        title="Parishes and Non Civil Parished Areas (December 2023) Boundaries EW BFC",
        query_url=(
            "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
            "Parishes_and_Non_Civil_Parished_Areas_December_2023_Boundaries_EW_BFC/"
            "FeatureServer/0/query"
        ),
        code_field="PARNCP23CD",
        name_field="PARNCP23NM",
        vintage="December 2023",
    ),
    "parish_bgc": BoundaryLayer(
        key="parish_bgc",
        title="Parishes and Non Civil Parished Areas (December 2023) Boundaries EW BGC",
        query_url=(
            "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
            "Parishes_and_Non_Civil_Parished_Areas_December_2023_Boundaries_EW_BGC/"
            "FeatureServer/0/query"
        ),
        code_field="PARNCP23CD",
        name_field="PARNCP23NM",
        vintage="December 2023",
    ),
    "lsoa_bfc": BoundaryLayer(
        key="lsoa_bfc",
        title="Lower layer Super Output Areas (December 2021) Boundaries EW BFC (V10)",
        query_url=(
            "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
            "Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BFC_V10/"
            "FeatureServer/0/query"
        ),
        code_field="LSOA21CD",
        name_field="LSOA21NM",
        vintage="December 2021",
    ),
    "ward_bfc": BoundaryLayer(
        key="ward_bfc",
        title="Wards (December 2020) Boundaries UK BFC",
        query_url=(
            "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
            "Wards_December_2020_UK_BFC_2022/FeatureServer/0/query"
        ),
        code_field="WD20CD",
        name_field="WD20NM",
        vintage="December 2020",
    ),
}
"""ward_bfc's vintage (December 2020) is a WORKING ASSUMPTION, not yet confirmed
against Forest Research's own canopy-cover dataset documentation (spec §4 says
the canopy dataset uses "2020 imagery" but doesn't name a specific ONS ward
edition) -- see docs/STATUS.md Q-008 / the P1.1 worklog entry. Do not silently
change this without updating that note."""


class BoundaryFetchError(RuntimeError):
    """Raised when an ONS FeatureServer query fails or returns an error body."""


def parse_boundary_response(geojson: dict[str, Any], layer: BoundaryLayer) -> gpd.GeoDataFrame:
    """Parse an ArcGIS REST GeoJSON response into a GeoDataFrame.

    Pure function, no network — this is what the fixture-based unit tests
    exercise. Raises BoundaryFetchError if the response is an ArcGIS error
    body (which is still valid JSON, so it must be checked explicitly) or
    has no features.
    """
    if "error" in geojson:
        raise BoundaryFetchError(
            f"{layer.title}: ONS service returned an error: {geojson['error']}"
        )
    features = geojson.get("features")
    if not features:
        raise BoundaryFetchError(f"{layer.title}: response had no features")

    gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:27700")
    missing = {layer.code_field, layer.name_field} - set(gdf.columns)
    if missing:
        raise BoundaryFetchError(
            f"{layer.title}: expected field(s) {missing} not found in response "
            f"(got {list(gdf.columns)}) -- the layer's schema may have changed"
        )
    return gdf


def fetch_boundary(
    layer_key: str,
    codes: list[str] | None = None,
    *,
    code_field_override: str | None = None,
    timeout: int = 30,
    write_manifest: bool = True,
) -> gpd.GeoDataFrame:
    """Fetch a boundary layer (optionally filtered to specific GSS codes) live
    from the ONS Geoportal, parse it, and record a manifest entry.

    `codes=None` fetches every feature in the layer -- only do this for
    layers small enough to be reasonable (parish/LSOA/ward are fine; a
    finer geography might not be). Writes data/manifest/boundaries/
    <layer_key>/<UTC-ISO-timestamp>.json with the query URL, code list,
    feature count and retrieval time, per the project's traceability
    requirement (spec §4, development-plan.md §2.3).
    """
    if layer_key not in LAYERS:
        raise BoundaryFetchError(
            f"Unknown boundary layer '{layer_key}'. Known layers: {sorted(LAYERS)}"
        )
    layer = LAYERS[layer_key]
    code_field = code_field_override or layer.code_field

    if codes:
        quoted = ",".join(f"'{c}'" for c in codes)
        where = f"{code_field} IN ({quoted})"
    else:
        where = "1=1"

    params = {
        "where": where,
        "outFields": f"{layer.code_field},{layer.name_field}",
        "returnGeometry": "true",
        "f": "geojson",
        # Request British National Grid (metres) explicitly. Without this,
        # ArcGIS defaults f=geojson output to WGS84 (EPSG:4326, degrees) --
        # geopandas would then compute a bogus near-zero "area" in degrees²
        # if that were mislabelled as EPSG:27700, as happened once while
        # building this module (caught by test_boundaries.py). All areas
        # and distances downstream assume metres, so fetch in BNG directly
        # rather than reprojecting after the fact.
        "outSR": "27700",
    }
    response = requests.get(layer.query_url, params=params, timeout=timeout)
    response.raise_for_status()
    geojson = response.json()
    gdf = parse_boundary_response(geojson, layer)

    if write_manifest:
        _write_manifest(layer, where, gdf, response.url)

    return gdf


def _write_manifest(
    layer: BoundaryLayer, where: str, gdf: gpd.GeoDataFrame, request_url: str
) -> None:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    retrieved_at = datetime.now(UTC).isoformat()
    manifest_path = MANIFEST_DIR / layer.key / f"{retrieved_at.replace(':', '-')}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "layer_key": layer.key,
        "dataset_title": layer.title,
        "vintage": layer.vintage,
        "query_url": layer.query_url,
        "request_url": request_url,
        "where_clause": where,
        "feature_count": len(gdf),
        "retrieved_at": retrieved_at,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def load_fixture(fixture_path: Path, layer_key: str) -> gpd.GeoDataFrame:
    """Load a committed test fixture (a trimmed real GeoJSON response) as a
    GeoDataFrame, the same way fetch_boundary would parse a live response."""
    layer = LAYERS[layer_key]
    geojson = json.loads(fixture_path.read_text(encoding="utf-8"))
    return parse_boundary_response(geojson, layer)
