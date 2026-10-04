"""Pure helpers for baking the 3D map assets (Phase 9, P9.2, ADR-0018).

The site never fetches map tiles in a visitor's browser: a one-off script
(`scripts/bake_map_assets.py`) fetches terrain and imagery tiles, and these
functions turn them into small static files in `web/src/data/map/`. Network
and file I/O live in the script; everything here is deterministic and tested
offline against synthetic tiles.

Coordinates: tiles are Web Mercator "slippy map" tiles. `u`/`v` are
normalised Mercator coordinates in [0, 1] (v grows southwards), matching the
`web-map-render` prototype.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from PIL import Image

TILE = 256


def lon_to_u(lon: float) -> float:
    return (lon + 180.0) / 360.0


def lat_to_v(lat: float) -> float:
    s = math.sin(math.radians(lat))
    return 0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)


def u_to_lon(u: float) -> float:
    return u * 360.0 - 180.0


def v_to_lat(v: float) -> float:
    return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * v))))


@dataclass(frozen=True)
class Bbox:
    """Bounding box in normalised Mercator coordinates."""

    u0: float
    u1: float
    v0: float
    v1: float

    @property
    def aspect(self) -> float:
        """Height over width, in Mercator units (equal to the ground ratio)."""
        return (self.v1 - self.v0) / (self.u1 - self.u0)


def bbox_from_lonlat(points: list[tuple[float, float]], margin_m: float = 0.0) -> Bbox:
    """Bounding box of (lon, lat) points, grown by `margin_m` metres."""
    if not points:
        raise ValueError("no points")
    us = [lon_to_u(lon) for lon, _ in points]
    vs = [lat_to_v(lat) for _, lat in points]
    lat0 = sum(lat for _, lat in points) / len(points)
    metres_per_unit = 40_075_016.686 * math.cos(math.radians(lat0))
    m = margin_m / metres_per_unit
    return Bbox(min(us) - m, max(us) + m, min(vs) - m, max(vs) + m)


def tile_range(bbox: Bbox, z: int) -> tuple[int, int, int, int]:
    """Inclusive tile index ranges (tx0, tx1, ty0, ty1) covering `bbox` at zoom `z`."""
    n = 2**z
    return (
        math.floor(bbox.u0 * n),
        math.floor(bbox.u1 * n),
        math.floor(bbox.v0 * n),
        math.floor(bbox.v1 * n),
    )


def mosaic(
    tiles: dict[tuple[int, int], Image.Image], rng: tuple[int, int, int, int]
) -> Image.Image:
    """Stitch tiles keyed by (tx, ty) into one RGB image. Missing tiles raise,
    because a hole in the terrain or imagery must never be baked silently."""
    tx0, tx1, ty0, ty1 = rng
    out = Image.new("RGB", ((tx1 - tx0 + 1) * TILE, (ty1 - ty0 + 1) * TILE))
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            if (tx, ty) not in tiles:
                raise ValueError(f"missing tile {tx},{ty}")
            out.paste(tiles[(tx, ty)].convert("RGB"), ((tx - tx0) * TILE, (ty - ty0) * TILE))
    return out


def decode_terrarium(img: Image.Image) -> np.ndarray:
    """Terrarium RGB to metres: R*256 + G + B/256 - 32768."""
    a = np.asarray(img.convert("RGB"), dtype=np.float64)
    return a[..., 0] * 256.0 + a[..., 1] + a[..., 2] / 256.0 - 32768.0


def sample_grid(
    heights: np.ndarray, rng: tuple[int, int, int, int], z: int, bbox: Bbox, cols: int, rows: int
) -> np.ndarray:
    """Bilinear-resample a stitched height array onto a regular rows x cols grid
    covering `bbox` (row 0 = north edge)."""
    tx0, _, ty0, _ = rng
    n = 2**z
    h, w = heights.shape
    us = bbox.u0 + (bbox.u1 - bbox.u0) * np.linspace(0, 1, cols)
    vs = bbox.v0 + (bbox.v1 - bbox.v0) * np.linspace(0, 1, rows)
    x = np.clip((us * n - tx0) * TILE - 0.5, 0, w - 1.001)
    y = np.clip((vs * n - ty0) * TILE - 0.5, 0, h - 1.001)
    xi, yi = x.astype(int), y.astype(int)
    fx, fy = (x - xi)[None, :], (y - yi)[:, None]
    a = heights[np.ix_(yi, xi)]
    b = heights[np.ix_(yi, xi + 1)]
    c = heights[np.ix_(yi + 1, xi)]
    d = heights[np.ix_(yi + 1, xi + 1)]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def encode_uint8(grid: np.ndarray) -> tuple[bytes, float, float]:
    """Heights to uint8 scaled between the grid min and max (about 0.6 m steps
    across this area, ample for a vertically exaggerated visual terrain, and
    far smaller than 16-bit once compressed). Returns (bytes, min_m, max_m);
    decode with min + v/255*(max-min)."""
    lo, hi = float(grid.min()), float(grid.max())
    span = hi - lo or 1.0
    q = np.rint((grid - lo) / span * 255).astype("u1")
    return q.tobytes(), lo, hi


def decode_uint8(data: bytes, lo: float, hi: float, rows: int, cols: int) -> np.ndarray:
    q = np.frombuffer(data, dtype="u1").reshape(rows, cols).astype(np.float64)
    return lo + q / 255.0 * (hi - lo)


def crop_imagery(
    img: Image.Image, rng: tuple[int, int, int, int], z: int, bbox: Bbox, width: int
) -> Image.Image:
    """Crop a stitched imagery mosaic to `bbox`, resized to `width` px wide
    at the bbox's own aspect ratio."""
    tx0, _, ty0, _ = rng
    n = 2**z
    box = (
        (bbox.u0 * n - tx0) * TILE,
        (bbox.v0 * n - ty0) * TILE,
        (bbox.u1 * n - tx0) * TILE,
        (bbox.v1 * n - ty0) * TILE,
    )
    height = max(1, round(width * bbox.aspect))
    return img.resize((width, height), Image.LANCZOS, box=box)


def soften(img: Image.Image, wash: float = 0.3, desaturate: float = 0.25) -> Image.Image:
    """Lighten and slightly desaturate imagery so data layers read clearly and
    the look stays clean and light (design direction, Phase 9)."""
    a = np.asarray(img.convert("RGB"), dtype=np.float64)
    grey = a.mean(axis=2, keepdims=True)
    a = a * (1 - desaturate) + grey * desaturate
    a = a * (1 - wash) + 255.0 * wash
    return Image.fromarray(np.clip(a, 0, 255).astype("uint8"))
