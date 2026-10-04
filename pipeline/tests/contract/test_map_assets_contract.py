"""Contract tests for the baked 3D map assets (Phase 9, P9.2): the committed
files in web/src/data/map/ are internally consistent and agree with the
site's own area registry."""

from __future__ import annotations

import hashlib
import json

from cholsey_pipeline.registry import REPO_ROOT, load_geography

MAP = REPO_ROOT / "web" / "src" / "data" / "map"


def _json(name: str):
    return json.loads((MAP / name).read_text(encoding="utf-8"))


def test_files_match_their_recorded_hashes():
    meta = _json("meta.json")
    for key in ("terrain", "imagery", "parishes", "greenspace"):
        data = (MAP / meta[key]["file"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == meta[key]["sha256"], key


def test_terrain_size_matches_grid():
    t = _json("meta.json")["terrain"]
    assert (MAP / t["file"]).stat().st_size == t["cols"] * t["rows"] * 2
    assert t["min_m"] < t["max_m"]


def test_parish_polygons_cover_every_subject_and_comparator_in_areas_json():
    expected = {
        code: a["name"]
        for code, a in load_geography().items()
        if a["role"] in ("subject", "comparator")
    }
    got = {f["area_code"]: f["name"] for f in _json("parishes.json")["features"]}
    assert got == expected


def test_greenspace_sites_are_only_accessible_types():
    meta = _json("meta.json")
    allowed = set(meta["greenspace"]["functions"])
    sites = _json("greenspace.json")["features"]
    assert sites and all(s["function"] in allowed for s in sites)
    assert "Allotments Or Community Growing Spaces" not in allowed


def test_every_source_carries_attribution_and_licence():
    for s in _json("meta.json")["sources"]:
        assert s["attribution"] and s["licence"] and s["url"].startswith("https://")
