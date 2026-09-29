#!/usr/bin/env python3
"""Build data/processed/geography/population_denominators.csv (P1.6).

Combines:
  - geography/reference_data/parish_population_mid2021.json -- ONS's own
    direct parish-level mid-2021 population estimate, covering Cholsey and
    all 8 comparators (no OA apportionment needed, ONS already publishes
    it at parish level).
  - geography/reference_data/oa_census_counts_cholsey_area.json -- real
    Census Day (21 March 2021) OA-level population and household counts
    for Cholsey/Moulsford's 15 relevant OAs, aggregated to parish via
    geography.denominators.sum_by_parish (the same OA->parish best-fit
    join P1.4/P1.5 use). Comparator-level household/dwelling figures are
    NOT computed here -- see ADR-0005 and STATUS.md's backlog item.

Run manually to regenerate the CSV (one-off Phase 1 geography build, same
pattern as build_weights_csv.py -- not wired into `make refresh`):

    cd pipeline && uv run python scripts/build_population_denominators_csv.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from cholsey_pipeline.geography.denominators import sum_by_parish
from cholsey_pipeline.registry import REPO_ROOT

REFERENCE_DIR = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "cholsey_pipeline"
    / "geography"
    / "reference_data"
)
OA_LOOKUPS = json.loads(
    (REFERENCE_DIR / "oa_lookups_cholsey_area.json").read_text(encoding="utf-8")
)
OA_CENSUS_COUNTS = json.loads(
    (REFERENCE_DIR / "oa_census_counts_cholsey_area.json").read_text(encoding="utf-8")
)
MID2021 = json.loads((REFERENCE_DIR / "parish_population_mid2021.json").read_text(encoding="utf-8"))

OUTPUT_PATH = REPO_ROOT / "data" / "processed" / "geography" / "population_denominators.csv"

CHOLSEY = "E04012474"
MOULSFORD = "E04008148"

FIELDNAMES = [
    "parish_code",
    "parish_name",
    "metric",
    "value",
    "source_id",
    "source_url",
    "vintage",
    "retrieved_at",
    "method",
    "flag",
]


def _oa_to_parish() -> dict[str, str]:
    return {
        row["attributes"]["OA21CD"]: row["attributes"]["PARNCP24CD"]
        for row in OA_LOOKUPS["oa_to_parish"]["features"]
    }


def build_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    # --- Direct ONS mid-2021 parish population, all 9 areas ---
    prov = MID2021["_provenance"]
    for code, entry in MID2021["populations"].items():
        rows.append(
            {
                "parish_code": code,
                "parish_name": entry["name"],
                "metric": "population_mid2021_estimate",
                "value": entry["total"],
                "source_id": prov["source_id"],
                "source_url": prov["url"],
                "vintage": prov["vintage"],
                "retrieved_at": prov["retrieved_at"],
                "method": prov["method"],
                # The provenance-level flag is specifically about Cholsey's
                # own figure (4,404) diverging from spec's 4,498 and this
                # project's own 4,390 -- it doesn't apply to the other 8
                # areas' rows.
                "flag": prov["flag"] if code == CHOLSEY else "",
            }
        )

    # --- Census Day OA-best-fit population and households, Cholsey/Moulsford only ---
    oa_to_parish = _oa_to_parish()
    parish_names = {CHOLSEY: "Cholsey", MOULSFORD: "Moulsford"}

    pop_prov = OA_CENSUS_COUNTS["population"]["_provenance"]
    pop_totals = sum_by_parish(OA_CENSUS_COUNTS["population"]["counts"], oa_to_parish)
    for code, total in pop_totals.items():
        rows.append(
            {
                "parish_code": code,
                "parish_name": parish_names.get(code, code),
                "metric": "population_census_day_oa_bestfit",
                "value": total,
                "source_id": pop_prov["source_id"],
                "source_url": pop_prov["url"],
                "vintage": pop_prov["vintage"],
                "retrieved_at": pop_prov["retrieved_at"],
                "method": pop_prov["method"],
                "flag": "",
            }
        )

    hh_prov = OA_CENSUS_COUNTS["households"]["_provenance"]
    hh_totals = sum_by_parish(OA_CENSUS_COUNTS["households"]["counts"], oa_to_parish)
    # This flag is a scope caveat about the metric as a whole (household
    # counts only exist for Cholsey/Moulsford, not the other 8 comparators),
    # not something specific to one area's row -- so it belongs on every
    # households row this script writes, not just one of the two.
    comparator_scope_flag = (
        "Comparator-level household/dwelling counts not yet computed "
        "(would need each comparator's own OA->parish lookup) -- see "
        "ADR-0005 and STATUS.md backlog."
    )
    for code, total in hh_totals.items():
        rows.append(
            {
                "parish_code": code,
                "parish_name": parish_names.get(code, code),
                "metric": "households_census_day_oa_bestfit",
                "value": total,
                "source_id": hh_prov["source_id"],
                "source_url": hh_prov["url"],
                "vintage": hh_prov["vintage"],
                "retrieved_at": hh_prov["retrieved_at"],
                "method": hh_prov["method"],
                "flag": comparator_scope_flag,
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
