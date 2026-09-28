#!/usr/bin/env python3
"""Build data/processed/geography/weights.csv (development-plan.md P1.5).

Combines:
  - geography/reference_data/oa_lookups_cholsey_area.json (the live-verified
    OA->parish/OA->LSOA rows and NSUL UPRN counts for Cholsey/Moulsford's 15
    relevant OAs -- see that file's own _readme and ADR-0004)
  - live parish/LSOA/ward boundary polygons, fetched fresh from the ONS
    Geoportal via geography.boundaries.fetch_boundary, for the area-weight
    cross-check.

Run manually to regenerate the CSV (not wired into `make refresh`, which is
a Phase 2/3 stub per the Makefile -- this is Phase 1's one-off geography
build, following the same pattern as P1.1-P1.4's live-verified-then-
committed approach):

    cd pipeline && uv run python scripts/build_weights_csv.py

This is generated output -- never hand-edit data/processed/geography/
weights.csv directly (CLAUDE.md's non-negotiable rule). Re-run this script
instead.
"""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from cholsey_pipeline.geography.boundaries import fetch_boundary
from cholsey_pipeline.geography.weights import (
    compute_address_weights,
    compute_lsoa_area_weights,
    compute_parish_ward_weights,
)
from cholsey_pipeline.registry import REPO_ROOT

REFERENCE_DATA = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "cholsey_pipeline"
    / "geography"
    / "reference_data"
    / "oa_lookups_cholsey_area.json"
)
OUTPUT_PATH = REPO_ROOT / "data" / "processed" / "geography" / "weights.csv"

CHOLSEY = "E04012474"
MOULSFORD = "E04008148"
LSOA_CODES = ["E01035751", "E01028619", "E01035752"]
CHOLSEY_WARD = "E05011701"

PARISH_NAMES = {CHOLSEY: "Cholsey", MOULSFORD: "Moulsford"}

FIELDNAMES = [
    "parish_code",
    "parish_name",
    "join_geography_type",
    "join_geography_code",
    "join_geography_name",
    "weight_type",
    "weight",
    "numerator",
    "denominator",
    "source_id",
    "source_url",
    "vintage",
    "retrieved_at",
    "method",
    "flag",
]


def build_rows() -> list[dict[str, object]]:
    reference = json.loads(REFERENCE_DATA.read_text(encoding="utf-8"))
    oa_to_parish_rows = reference["oa_to_parish"]["features"]
    oa_to_lsoa_rows = reference["oa_to_lsoa"]["features"]
    uprn_provenance = reference["uprn_counts"]["_provenance"]
    uprn_counts = reference["uprn_counts"]["counts"]

    now = datetime.now(UTC).isoformat()
    rows: list[dict[str, object]] = []

    # --- Address-count weights (primary), per (LSOA, parish) ---
    for w in compute_address_weights(oa_to_parish_rows, oa_to_lsoa_rows, uprn_counts):
        rows.append(
            {
                "parish_code": w.parish_code,
                "parish_name": PARISH_NAMES.get(w.parish_code, w.parish_code),
                "join_geography_type": "lsoa",
                "join_geography_code": w.lsoa_code,
                "join_geography_name": w.lsoa_name,
                "weight_type": "address_count",
                "weight": round(w.weight, 6),
                "numerator": w.uprn_count,
                "denominator": w.lsoa_total_uprns,
                "source_id": uprn_provenance["source_id"],
                "source_url": uprn_provenance["url"],
                "vintage": uprn_provenance["title"],
                "retrieved_at": uprn_provenance["retrieved_at"],
                "method": uprn_provenance["method"],
                "flag": "",
            }
        )

    # --- Area-weight cross-check, per (LSOA, parish) -- live-fetched ---
    parishes_gdf = fetch_boundary("parish_bfc", codes=[CHOLSEY, MOULSFORD])
    lsoas_gdf = fetch_boundary("lsoa_bfc", codes=LSOA_CODES)
    ward_gdf = fetch_boundary("ward_bfc", codes=[CHOLSEY_WARD])

    for w in compute_lsoa_area_weights(lsoas_gdf, parishes_gdf):
        rows.append(
            {
                "parish_code": w.parish_code,
                "parish_name": PARISH_NAMES.get(w.parish_code, w.parish_code),
                "join_geography_type": "lsoa",
                "join_geography_code": w.lsoa_code,
                "join_geography_name": w.lsoa_name,
                "weight_type": "area_cross_check",
                "weight": round(w.weight, 6),
                "numerator": "",
                "denominator": "",
                "source_id": "ons_boundaries_lsoa,ons_boundaries_parish_bfc",
                "source_url": "",
                "vintage": "LSOA Dec 2021 BFC / Parish Dec 2023 BFC",
                "retrieved_at": now,
                "method": (
                    "Polygon intersection area (parish geometry ∩ LSOA geometry) "
                    "/ LSOA polygon area, both in EPSG:27700. A cross-check on "
                    "the address_count weight above, not a substitute -- they "
                    "can genuinely differ (see the P1.5 worklog entry)."
                ),
                "flag": "",
            }
        )

    # --- Parish-in-ward area weights, for the canopy join ---
    for w in compute_parish_ward_weights(
        parishes_gdf[parishes_gdf["PARNCP23CD"] == CHOLSEY], ward_gdf
    ):
        rows.append(
            {
                "parish_code": w.parish_code,
                "parish_name": PARISH_NAMES.get(w.parish_code, w.parish_code),
                "join_geography_type": "ward",
                "join_geography_code": w.ward_code,
                "join_geography_name": w.ward_name,
                "weight_type": "area",
                "weight": round(w.weight, 6),
                "numerator": "",
                "denominator": "",
                "source_id": "ons_boundaries_ward,ons_boundaries_parish_bfc",
                "source_url": "",
                "vintage": "Ward Dec 2020 BFC / Parish Dec 2023 BFC",
                "retrieved_at": now,
                "method": (
                    "Polygon intersection area (parish geometry ∩ ward geometry) "
                    "/ parish polygon area, both in EPSG:27700. Used to combine "
                    "ward-level canopy figures onto the parish (Phase 2, P2.3)."
                ),
                "flag": "ward vintage (Dec 2020) is a working assumption, see Q-008",
            }
        )

    return rows


def main() -> None:
    rows = build_rows()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
