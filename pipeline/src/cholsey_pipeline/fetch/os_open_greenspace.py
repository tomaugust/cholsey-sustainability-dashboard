"""Fetch OS Open Greenspace sites, clipped to a buffered bounding box
around Cholsey and its comparators (development-plan.md Phase 2, P2.4).

The live download is a single GB-wide GeoPackage (~144MB uncompressed,
~57MB zipped) -- P2.4 explicitly says to clip on ingest so the interim
extract stays small, rather than loading or committing the whole thing.
GDAL/pyogrio can filter by bounding box while reading, and can read
straight out of the zip (`zip://<path>!Data/opgrsp_gb.gpkg`) without a
separate extraction step, so the full file never needs to land unzipped on
disk.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from cholsey_pipeline.fetch.http import fetch_file

SOURCE_ID = "os_open_greenspace"
DOWNLOAD_URL = (
    "https://api.os.uk/downloads/v1/products/OpenGreenspace/downloads"
    "?area=GB&format=GeoPackage&redirect"
)
"""Verified live 2026-09-29 (P2.1/P2.4) by actually downloading it -- see
config/sources.yaml's os_open_greenspace entry."""

LAYER_NAME = "greenspace_site"
DEFAULT_BUFFER_M = 500.0
"""How far beyond the tightest bounding box of the subject+comparator
parishes to clip -- generous enough that a greenspace site straddling a
parish boundary isn't cut off, small enough to keep the extract tiny
relative to the GB-wide source."""


def compute_bbox(
    areas: gpd.GeoDataFrame, buffer_m: float = DEFAULT_BUFFER_M
) -> tuple[float, float, float, float]:
    """Compute a buffered bounding box (minx, miny, maxx, maxy) around
    `areas`' combined extent. Pure function -- `areas` must already be in a
    metres-based CRS (BNG, EPSG:27700)."""
    minx, miny, maxx, maxy = areas.total_bounds
    return (minx - buffer_m, miny - buffer_m, maxx + buffer_m, maxy + buffer_m)


def read_greenspace_sites(
    gpkg_path: str | Path, bbox: tuple[float, float, float, float]
) -> gpd.GeoDataFrame:
    """Read the `greenspace_site` layer from a GeoPackage (or a
    `zip://...!...gpkg` URI), filtered to `bbox`. Thin wrapper around
    geopandas/pyogrio's bbox-filtered read -- what the offline tests
    exercise against a small committed fixture, same pattern as
    geography.boundaries' fetch/parse split (development-plan.md §5.1)."""
    return gpd.read_file(str(gpkg_path), layer=LAYER_NAME, bbox=bbox)


def fetch_greenspace_sites(
    areas: gpd.GeoDataFrame,
    *,
    buffer_m: float = DEFAULT_BUFFER_M,
    timeout: int = 120,
) -> gpd.GeoDataFrame:
    """Download OS Open Greenspace (via fetch.http.fetch_file, so it's
    retried/deduplicated/manifested like every other Phase 2 source) and
    return just the sites within a buffered bbox around `areas`.

    `areas` should be the subject parish + comparators (e.g. from
    `data/processed/geography/parishes.geojson`, reprojected to
    EPSG:27700).
    """
    result = fetch_file(
        SOURCE_ID,
        DOWNLOAD_URL,
        dest_filename="opgrsp_gb.zip",
        timeout=timeout,
    )
    if result.file_path is None:
        raise RuntimeError(
            f"'{SOURCE_ID}': fetch_file returned status={result.status!r} with no file_path "
            "-- expected a downloaded or previously-downloaded zip on disk"
        )
    bbox = compute_bbox(areas, buffer_m)
    gpkg_uri = f"zip://{result.file_path}!Data/opgrsp_gb.gpkg"
    return read_greenspace_sites(gpkg_uri, bbox)
