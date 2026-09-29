#!/usr/bin/env python3
"""Build data/processed/geography/parishes.geojson (P1.7).

Fetches the generalised (BGC, display-quality) parish boundary for Cholsey
and all 8 confirmed comparators, lightly simplifies it further, reprojects
to WGS84 (EPSG:4326, what web maps expect), and writes a single
FeatureCollection with the properties the Phase 5 map/locator will need:
area_code, name, role (matching config/geography.yaml's schema).

Run manually to regenerate (one-off Phase 1 geography build, same pattern
as build_weights_csv.py / build_population_denominators_csv.py):

    cd pipeline && uv run python scripts/build_parish_geojson.py
"""

from __future__ import annotations

import json

import yaml

from cholsey_pipeline.geography.boundaries import fetch_boundary
from cholsey_pipeline.registry import CONFIG_DIR, REPO_ROOT

OUTPUT_PATH = REPO_ROOT / "data" / "processed" / "geography" / "parishes.geojson"

# A light simplification tolerance in metres -- the BGC layer is already
# ONS's own generalised-for-display edition (38-94 vertices per parish
# here), so this is a small further reduction for a lightweight web map,
# not the kind of aggressive simplification that would distort shape.
SIMPLIFY_TOLERANCE_M = 5.0


def main() -> None:
    geography = yaml.safe_load((CONFIG_DIR / "geography.yaml").read_text(encoding="utf-8"))
    subject_and_comparators = {
        code: entry
        for code, entry in geography["areas"].items()
        if entry["role"] in ("subject", "comparator")
    }
    codes = list(subject_and_comparators)

    gdf = fetch_boundary("parish_bgc", codes=codes)
    returned_codes = set(gdf["PARNCP23CD"])
    missing = set(codes) - returned_codes
    if missing:
        raise RuntimeError(
            f"ONS parish_bgc layer did not return {len(missing)} of the {len(codes)} "
            f"configured subject/comparator parishes: {sorted(missing)} -- refusing to "
            "write a silently incomplete parishes.geojson."
        )

    # Each parish is simplified independently, so two neighbouring parishes'
    # shared edge can end up with a small gap or overlap after simplification
    # -- acceptable for a display-only locator map at this tolerance (5m,
    # imperceptible at web map zoom), but NOT suitable for area/adjacency
    # calculations, which use the unsimplified BFC layer via
    # geography.boundaries/comparators/weights instead.
    gdf["geometry"] = gdf.geometry.simplify(SIMPLIFY_TOLERANCE_M, preserve_topology=True)
    gdf = gdf.to_crs("EPSG:4326")

    features = []
    for _, row in gdf.iterrows():
        code = row["PARNCP23CD"]
        entry = subject_and_comparators[code]
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "area_code": code,
                    "name": entry["name"],
                    "role": entry["role"],
                },
                "geometry": json.loads(json.dumps(row.geometry.__geo_interface__)),
            }
        )

    feature_collection = {
        "type": "FeatureCollection",
        "properties": {
            "source": "ons_boundaries_parish_bgc (see config/sources.yaml)",
            "vintage": "December 2023",
            "simplify_tolerance_m": SIMPLIFY_TOLERANCE_M,
            "crs": "EPSG:4326",
        },
        "features": features,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(feature_collection), encoding="utf-8")
    print(f"Wrote {len(features)} features to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
