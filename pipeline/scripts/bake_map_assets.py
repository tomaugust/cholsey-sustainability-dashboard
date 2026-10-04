"""Bake the static 3D-map assets (Phase 9, P9.2, ADR-0018).

Fetches terrain (Mapzen/AWS Terrarium) and imagery (OpenStreetMap) tiles
once, politely and cached under data/raw/map_tiles/, and writes small static
files to web/src/data/map/ (generated: never hand-edit, re-run this script):

  terrain.bin     uint8 heights (see meta.json for scaling)
  imagery.jpg     softened OSM imagery covering the same box
  parishes.json   simplified polygons for Cholsey and the 8 comparators
  greenspace.json real OS Open Greenspace sites inside Cholsey (accessible types)
  meta.json       extents, scaling, sources, attribution, retrieval date, hashes

Run:  cd pipeline && uv run python scripts/bake_map_assets.py
OpenStreetMap's tile policy allows light, cached use only: tiles are cached,
fetched sequentially with a descriptive User-Agent, and the script is not part
of CI or the refresh job.
"""

from __future__ import annotations

import hashlib
import io
import json
import time
from datetime import UTC, datetime

import geopandas as gpd
import requests
from PIL import Image
from shapely.geometry import mapping

from cholsey_pipeline.map_assets import (
    bbox_from_lonlat,
    crop_imagery,
    decode_terrarium,
    encode_uint8,
    mosaic,
    sample_grid,
    soften,
    tile_range,
    u_to_lon,
    v_to_lat,
)
from cholsey_pipeline.metrics.greenspace import ACCESSIBLE_FUNCTION_TYPES
from cholsey_pipeline.registry import REPO_ROOT

OUT = REPO_ROOT / "web" / "src" / "data" / "map"
CACHE = REPO_ROOT / "data" / "raw" / "map_tiles"
PARISHES = REPO_ROOT / "data" / "processed" / "geography" / "parishes.geojson"
GREENSPACE = (
    REPO_ROOT
    / "pipeline"
    / "tests"
    / "fixtures"
    / "os_open_greenspace"
    / "cholsey_clipped_real.gpkg"
)
UA = "cholsey-dashboard-map-bake/0.1 (+https://github.com/tomaugust/cholsey-sustainability-dashboard)"
TERRARIUM = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
OSM = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
ELEV_Z, IMG_Z = 13, 14
MARGIN_M = 600.0
GRID_COLS = 192
IMG_WIDTH = 1024
SIMPLIFY_DEG = 0.00004  # about 4 m
CHOLSEY_CODE = "E04012474"


def fetch_tile(kind: str, url: str, z: int, x: int, y: int) -> Image.Image:
    path = CACHE / kind / str(z) / str(x) / f"{y}.png"
    if not path.exists():
        for attempt in range(4):
            r = requests.get(url.format(z=z, x=x, y=y), headers={"User-Agent": UA}, timeout=30)
            if r.status_code == 200:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(r.content)
                time.sleep(0.3)
                break
            time.sleep(2**attempt)
        else:
            raise RuntimeError(f"could not fetch {kind} tile {z}/{x}/{y}")
    return Image.open(path).convert("RGB")


def fetch_mosaic(kind: str, url: str, z: int, rng: tuple[int, int, int, int]):
    tx0, tx1, ty0, ty1 = rng
    tiles = {
        (x, y): fetch_tile(kind, url, z, x, y)
        for y in range(ty0, ty1 + 1)
        for x in range(tx0, tx1 + 1)
    }
    return mosaic(tiles, rng)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def round_coords(geom, nd=5):
    m = mapping(geom)

    def r(c):
        return (
            [round(c[0], nd), round(c[1], nd)]
            if isinstance(c[0], (int, float))
            else [r(x) for x in c]
        )

    return {"type": m["type"], "coordinates": r(m["coordinates"])}


def main() -> None:
    parishes = gpd.read_file(PARISHES).to_crs(4326)
    pts = [(x, y) for g in parishes.geometry for x, y in g.exterior.coords]
    bbox = bbox_from_lonlat(pts, margin_m=MARGIN_M)

    elev_rng = tile_range(bbox, ELEV_Z)
    img_rng = tile_range(bbox, IMG_Z)
    n_elev = (elev_rng[1] - elev_rng[0] + 1) * (elev_rng[3] - elev_rng[2] + 1)
    n_img = (img_rng[1] - img_rng[0] + 1) * (img_rng[3] - img_rng[2] + 1)
    print(f"fetching {n_elev} elevation and {n_img} imagery tiles (cached after first run)")
    elev = decode_terrarium(fetch_mosaic("terrarium", TERRARIUM, ELEV_Z, elev_rng))
    imagery = fetch_mosaic("osm", OSM, IMG_Z, img_rng)

    rows = round(GRID_COLS * bbox.aspect)
    grid = sample_grid(elev, elev_rng, ELEV_Z, bbox, GRID_COLS, rows)
    terrain_bytes, hmin, hmax = encode_uint8(grid)

    buf = io.BytesIO()
    soften(crop_imagery(imagery, img_rng, IMG_Z, bbox, IMG_WIDTH)).save(
        buf, "JPEG", quality=64, optimize=True, progressive=True
    )
    imagery_bytes = buf.getvalue()

    simple = parishes.copy()
    simple["geometry"] = simple.geometry.simplify(SIMPLIFY_DEG, preserve_topology=True)
    parishes_json = {
        "features": [
            {
                "area_code": r.area_code,
                "name": r["name"],
                "role": r.role,
                "geometry": round_coords(r.geometry),
            }
            for _, r in simple.iterrows()
        ]
    }

    sites = gpd.read_file(GREENSPACE)
    sites = sites[sites["function"].isin(ACCESSIBLE_FUNCTION_TYPES)].to_crs(4326)
    greenspace_json = {
        "area_code": CHOLSEY_CODE,
        "features": [
            {"function": r["function"], "geometry": round_coords(r.geometry.simplify(SIMPLIFY_DEG))}
            for _, r in sites.iterrows()
        ],
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "terrain.bin").write_bytes(terrain_bytes)
    (OUT / "imagery.jpg").write_bytes(imagery_bytes)
    parishes_text = json.dumps(parishes_json, separators=(",", ":")) + "\n"
    greenspace_text = json.dumps(greenspace_json, separators=(",", ":")) + "\n"
    (OUT / "parishes.json").write_text(parishes_text)
    (OUT / "greenspace.json").write_text(greenspace_text)

    meta = {
        "_readme": "Generated by pipeline/scripts/bake_map_assets.py. Do not hand-edit.",
        "baked_at": datetime.now(UTC).strftime("%Y-%m-%d"),
        "bbox_uv": {"u0": bbox.u0, "u1": bbox.u1, "v0": bbox.v0, "v1": bbox.v1},
        "bbox_lonlat": {
            "west": u_to_lon(bbox.u0),
            "east": u_to_lon(bbox.u1),
            "north": v_to_lat(bbox.v0),
            "south": v_to_lat(bbox.v1),
        },
        "terrain": {
            "file": "terrain.bin",
            "cols": GRID_COLS,
            "rows": rows,
            "min_m": hmin,
            "max_m": hmax,
            "encoding": "uint8, row 0 = north; m = min + v/255*(max-min)",
            "sha256": sha(terrain_bytes),
            "tiles": {"source": "terrarium", "zoom": ELEV_Z, "count": n_elev},
        },
        "imagery": {
            "file": "imagery.jpg",
            "width": IMG_WIDTH,
            "treatment": "lightened 30% and desaturated 25% for legibility of data layers",
            "sha256": sha(imagery_bytes),
            "tiles": {"source": "osm", "zoom": IMG_Z, "count": n_img},
        },
        "parishes": {
            "file": "parishes.json",
            "simplified_deg": SIMPLIFY_DEG,
            "sha256": sha(parishes_text.encode()),
        },
        "greenspace": {
            "file": "greenspace.json",
            "functions": sorted(ACCESSIBLE_FUNCTION_TYPES),
            "sha256": sha(greenspace_text.encode()),
        },
        "sources": [
            {
                "name": "OpenStreetMap raster tiles",
                "publisher": "OpenStreetMap contributors",
                "url": "https://www.openstreetmap.org/copyright",
                "licence": "Open Database Licence (ODbL)",
                "attribution": "Map data © OpenStreetMap contributors",
            },
            {
                "name": "Terrain Tiles (Terrarium)",
                "publisher": "Mapzen / AWS Open Data",
                "url": "https://registry.opendata.aws/terrain-tiles/",
                "licence": "Open data; composite of SRTM, USGS NED and others (see publisher)",
                "attribution": "Elevation: Mapzen / AWS Terrain Tiles",
            },
            {
                "name": "Parishes and Non Civil Parished Areas (December 2023) Boundaries EW BFC",
                "publisher": "ONS Open Geography Portal",
                "url": "https://geoportal.statistics.gov.uk/",
                "licence": "Open Government Licence v3.0",
                "attribution": "Boundaries: ONS, OGL v3.0",
            },
            {
                "name": "OS Open Greenspace",
                "publisher": "Ordnance Survey",
                "url": "https://www.ordnancesurvey.co.uk/products/os-open-greenspace",
                "licence": "Open Government Licence v3.0",
                "attribution": "Contains OS data © Crown copyright and database right",
            },
        ],
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    total = sum(p.stat().st_size for p in OUT.iterdir())
    sizes = {"terrain": len(terrain_bytes) // 1024, "imagery": len(imagery_bytes) // 1024}
    print(f"wrote {OUT} ({total // 1024} KB in total; KB per file: {sizes})")


if __name__ == "__main__":
    main()
