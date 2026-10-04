"""Offline tests for cholsey_pipeline.map_assets (P9.2), using synthetic tiles."""

import numpy as np
import pytest
from PIL import Image

from cholsey_pipeline.map_assets import (
    Bbox,
    bbox_from_lonlat,
    crop_imagery,
    decode_terrarium,
    decode_uint16,
    encode_uint16,
    lat_to_v,
    lon_to_u,
    mosaic,
    sample_grid,
    soften,
    tile_range,
    u_to_lon,
    v_to_lat,
)


def test_mercator_round_trip():
    assert u_to_lon(lon_to_u(-1.2)) == pytest.approx(-1.2)
    assert v_to_lat(lat_to_v(51.55)) == pytest.approx(51.55)


def test_bbox_margin_grows_the_box():
    pts = [(-1.2, 51.5), (-1.1, 51.6)]
    plain = bbox_from_lonlat(pts)
    grown = bbox_from_lonlat(pts, margin_m=500)
    assert grown.u0 < plain.u0 and grown.u1 > plain.u1
    assert grown.v0 < plain.v0 and grown.v1 > plain.v1
    with pytest.raises(ValueError):
        bbox_from_lonlat([])


def test_tile_range_covers_bbox():
    bbox = bbox_from_lonlat([(-1.2, 51.5), (-1.1, 51.6)])
    tx0, tx1, ty0, ty1 = tile_range(bbox, 13)
    n = 2**13
    assert tx0 <= bbox.u0 * n < tx0 + 1 and tx1 <= bbox.u1 * n < tx1 + 1
    assert ty0 <= bbox.v0 * n < ty0 + 1 and ty1 <= bbox.v1 * n < ty1 + 1


def _terrarium_tile(metres: float) -> Image.Image:
    v = metres + 32768
    r, g = int(v // 256), int(v % 256)
    b = int((v - int(v)) * 256)
    return Image.new("RGB", (256, 256), (r, g, b))


def test_mosaic_and_decode_terrarium():
    tiles = {(10, 20): _terrarium_tile(100.0), (11, 20): _terrarium_tile(150.5)}
    img = mosaic(tiles, (10, 11, 20, 20))
    assert img.size == (512, 256)
    h = decode_terrarium(img)
    assert h[0, 0] == pytest.approx(100.0, abs=0.01)
    assert h[0, 300] == pytest.approx(150.5, abs=0.01)


def test_mosaic_refuses_a_hole():
    with pytest.raises(ValueError, match="missing tile"):
        mosaic({(10, 20): _terrarium_tile(1.0)}, (10, 11, 20, 20))


def test_sample_grid_reproduces_a_ramp():
    # Heights equal to the x pixel index: a bilinear sample must follow the ramp.
    heights = np.tile(np.arange(512, dtype=float), (256, 1))
    z, rng = 13, (4000, 4001, 2700, 2700)
    n = 2**z
    bbox = Bbox(
        (4000 * 256 + 100.5) / (n * 256),
        (4000 * 256 + 300.5) / (n * 256),
        (2700 * 256 + 50.5) / (n * 256),
        (2700 * 256 + 150.5) / (n * 256),
    )
    grid = sample_grid(heights, rng, z, bbox, cols=5, rows=3)
    assert grid.shape == (3, 5)
    assert grid[0, 0] == pytest.approx(100.0, abs=0.01)
    assert grid[0, -1] == pytest.approx(300.0, abs=0.01)


def test_uint16_round_trip_within_quantisation():
    grid = np.array([[40.0, 60.5, 90.25], [100.0, 150.0, 210.75]])
    data, lo, hi = encode_uint16(grid)
    back = decode_uint16(data, lo, hi, 2, 3)
    assert lo == 40.0 and hi == 210.75
    assert np.allclose(back, grid, atol=(hi - lo) / 65535)


def test_flat_grid_does_not_divide_by_zero():
    data, lo, hi = encode_uint16(np.full((2, 2), 50.0))
    assert lo == hi == 50.0
    assert decode_uint16(data, lo, hi, 2, 2).tolist() == [[50.0, 50.0], [50.0, 50.0]]


def test_crop_imagery_size_follows_aspect():
    img = Image.new("RGB", (512, 512), (10, 120, 10))
    bbox = Bbox(0.25, 0.75, 0.25, 0.5)  # tall:wide = 0.5
    out = crop_imagery(img, (0, 1, 0, 1), 1, bbox, width=200)
    assert out.size == (200, 100)


def test_soften_lightens_and_keeps_size():
    img = Image.new("RGB", (4, 4), (0, 100, 0))
    out = soften(img)
    px = np.asarray(out)[0, 0]
    assert out.size == (4, 4)
    assert px[0] > 0 and px.min() > 0  # washed toward white
