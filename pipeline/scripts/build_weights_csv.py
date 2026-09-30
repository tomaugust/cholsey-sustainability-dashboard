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

from cholsey_pipeline.geography.boundaries import LAYERS, fetch_boundary
from cholsey_pipeline.geography.weights import (
    compute_address_weights,
    compute_lsoa_area_weights,
    compute_parish_ward_weights,
)
from cholsey_pipeline.registry import REPO_ROOT, load_geography

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
BBOX_BUFFER_M = 4000.0
"""How far beyond the subject+comparators' combined extent to search for
overlapping LSOAs/wards (P3.4) -- generous enough that a comparator's real
overlap isn't clipped at the edge, verified live 2026-09-30 to return
every LSOA a real polygon intersection needs (Aston Tirrold, the smallest
and most marginal case checked, has 99.7% of its area in one LSOA found
within this buffer)."""

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
    # ALL subject+comparator parishes (P3.4): Cholsey/Moulsford's rows are
    # the same address-count cross-check P1.5 always computed; the other 7
    # comparators get a REAL area weight here for the first time, filling
    # the "comparator-level LSOA apportionment" backlog item (STATUS.md) --
    # not the address-count weight (that still needs NSUL/UPRN data these
    # comparators don't have yet), but real polygon intersections, not
    # assumed or estimated.
    geography = load_geography()
    all_parish_codes = [
        code for code, entry in geography.items() if entry["role"] in ("subject", "comparator")
    ]
    all_parish_names = {code: geography[code]["name"] for code in all_parish_codes}
    parishes_gdf_all = fetch_boundary("parish_bfc", codes=all_parish_codes)
    minx, miny, maxx, maxy = parishes_gdf_all.total_bounds
    lsoa_bbox = (
        minx - BBOX_BUFFER_M,
        miny - BBOX_BUFFER_M,
        maxx + BBOX_BUFFER_M,
        maxy + BBOX_BUFFER_M,
    )
    lsoas_gdf_all = fetch_boundary("lsoa_bfc", bbox=lsoa_bbox)

    parishes_gdf = parishes_gdf_all[parishes_gdf_all["PARNCP23CD"].isin([CHOLSEY, MOULSFORD])]
    ward_gdf = fetch_boundary("ward_bfc", codes=[CHOLSEY_WARD])
    # retrieved_at is taken *after* the fetches above complete, not before --
    # otherwise the CSV would (and did, before this fix) claim a retrieval
    # time earlier than the manifest entries the fetches themselves wrote.
    now = datetime.now(UTC).isoformat()
    area_source_url = f"{LAYERS['lsoa_bfc'].query_url},{LAYERS['parish_bfc'].query_url}"
    ward_source_url = f"{LAYERS['ward_bfc'].query_url},{LAYERS['parish_bfc'].query_url}"

    for w in compute_lsoa_area_weights(lsoas_gdf_all, parishes_gdf_all):
        is_subject_or_moulsford = w.parish_code in (CHOLSEY, MOULSFORD)
        rows.append(
            {
                "parish_code": w.parish_code,
                "parish_name": all_parish_names.get(w.parish_code, w.parish_code),
                "join_geography_type": "lsoa",
                "join_geography_code": w.lsoa_code,
                "join_geography_name": w.lsoa_name,
                "weight_type": "area_cross_check" if is_subject_or_moulsford else "area",
                "weight": round(w.weight, 6),
                "numerator": "",
                "denominator": "",
                "source_id": "ons_boundaries_lsoa,ons_boundaries_parish_bfc",
                "source_url": area_source_url,
                "vintage": "LSOA Dec 2021 BFC / Parish Dec 2023 BFC",
                "retrieved_at": now,
                "method": (
                    "Polygon intersection area (parish geometry ∩ LSOA geometry) "
                    "/ LSOA polygon area, both in EPSG:27700. "
                    + (
                        "A cross-check on the address_count weight above, not a "
                        "substitute -- they can genuinely differ (see the P1.5 "
                        "worklog entry)."
                        if is_subject_or_moulsford
                        else "This comparator's primary apportionment weight -- no "
                        "NSUL address-count weight exists for it yet (P3.4 "
                        "backlog), so this area weight is used directly, not as "
                        "a cross-check."
                    )
                ),
                "flag": (
                    ""
                    if is_subject_or_moulsford
                    else "Area weight only -- assumes addresses are evenly "
                    "distributed across this LSOA's area, which can differ from "
                    "the real address-count share (see P1.5's own Cholsey/"
                    "Moulsford example: 45.7% by area vs 58.3% by address count "
                    "for the same LSOA)."
                ),
            }
        )

    # --- Parish-in-ward area weights, for the canopy join (Cholsey only --
    # comparator ward-vintage verification is a separate, bigger task per
    # ADR-0006's own lesson, not done here) ---
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
                "source_url": ward_source_url,
                "vintage": "Ward Dec 2020 BFC / Parish Dec 2023 BFC",
                "retrieved_at": now,
                "method": (
                    "Polygon intersection area (parish geometry ∩ ward geometry) "
                    "/ parish polygon area, both in EPSG:27700. Used to combine "
                    "ward-level canopy figures onto the parish (Phase 2, P2.3)."
                ),
                "flag": (
                    "Forest Research's canopy dataset actually uses an older ward "
                    "edition for Cholsey (wardcode E05009737, Dec 2018) than this "
                    "weight's Dec 2020 boundary (E05011701) -- verified geometrically "
                    "near-identical for Cholsey (99.4% vs 100.0% parish-in-ward), so "
                    "not corrected. See ADR-0006 (Q-008, resolved 2026-09-29)."
                ),
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
