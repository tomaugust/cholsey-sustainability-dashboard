#!/usr/bin/env python3
"""Build data/processed/metrics.csv and data/processed/README.md (P3.9).

**Scope, this first pass (2026-10-01)**: metrics 3 and 4 only (domestic
electricity and gas, `metrics/energy.py`) -- the two core metrics whose
real apportionment data (`data/processed/geography/weights.csv`, P1.5)
and live sources (`fetch.desnz_lsoa_energy`) are already committed,
structured, and don't need any further ad hoc live research (unlike
metric 1's per-comparator Forest Research ward-name matching, or metric
2's England-wide clip) -- see ADR-0010's "Consequences" and the
2026-10-01 P3.9 worklog for why the full 4-metric integration wasn't
attempted in one sitting. Extending this script to canopy/greenspace/MCS
is the next step; each metric's own `compute_*_row` functions and real
area/ward/LSOA mappings already exist from Phase 3's per-metric work, so
this script's fetch -> compute -> `export.build_metrics_row` pattern
should carry over directly, not be redesigned.

Run live (not wired into `make refresh`, which is a Phase 2/3 stub per
the Makefile):

    cd pipeline && uv run python scripts/build_metrics_csv.py

This is generated output -- never hand-edit `data/processed/metrics.csv`
or `data/processed/README.md` directly (CLAUDE.md's non-negotiable rule).
Re-run this script instead.
"""

from __future__ import annotations

import csv

from cholsey_pipeline.export import (
    build_metrics_row,
    rows_to_dataframe,
    write_metrics_csv,
    write_readme,
)
from cholsey_pipeline.fetch.desnz_lsoa_energy import (
    Fuel,
    LsoaEnergyRecord,
    fetch_lsoa_energy,
    fetch_regional_la_energy,
)
from cholsey_pipeline.fetch.http import latest_manifest
from cholsey_pipeline.metrics.energy import (
    compute_area_energy_row,
    compute_comparator_energy_row,
    compute_subject_energy_row,
)
from cholsey_pipeline.registry import REPO_ROOT, load_geography, load_sources

YEAR = 2024
"""The latest year DESNZ has published (verified live 2026-09-30, P3.4)."""

SOUTH_OXFORDSHIRE_CODE = "E07000179"
ENGLAND_CODE = "E92000001"

WEIGHTS_CSV = REPO_ROOT / "data" / "processed" / "geography" / "weights.csv"
METRICS_CSV_PATH = REPO_ROOT / "data" / "processed" / "metrics.csv"
README_PATH = REPO_ROOT / "data" / "processed" / "README.md"


def _load_lsoa_weights() -> dict[str, dict[str, dict[str, float]]]:
    """Returns {parish_code: {weight_type: {lsoa_code: weight}}}, read
    from the real, committed `weights.csv` (P1.5/P3.4) -- never
    hand-edited, never re-derived here."""
    weights: dict[str, dict[str, dict[str, float]]] = {}
    with WEIGHTS_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["join_geography_type"] != "lsoa":
                continue
            if row["weight_type"] not in ("address_count", "area"):
                continue  # skip area_cross_check rows -- not a primary weight
            parish = weights.setdefault(row["parish_code"], {})
            by_lsoa = parish.setdefault(row["weight_type"], {})
            by_lsoa[row["join_geography_code"]] = float(row["weight"])
    return weights


def _build_energy_rows_for_fuel(
    fuel: Fuel,
    geography: dict[str, dict],
    lsoa_weights: dict[str, dict[str, dict[str, float]]],
    sources: dict[str, dict],
) -> list[dict]:
    rows: list[dict] = []
    subject_comparator_codes = [
        code for code, entry in geography.items() if entry["role"] in ("subject", "comparator")
    ]
    all_lsoa_codes: set[str] = set()
    for code in subject_comparator_codes:
        for by_lsoa in lsoa_weights.get(code, {}).values():
            all_lsoa_codes.update(by_lsoa)

    lsoa_records = fetch_lsoa_energy(fuel, [YEAR], all_lsoa_codes)
    lsoa_provenance = latest_manifest(f"desnz_lsoa_energy/{fuel}")
    records_by_lsoa: dict[str, LsoaEnergyRecord] = {r.lsoa_code: r for r in lsoa_records}

    for area_code in subject_comparator_codes:
        area_weights = lsoa_weights.get(area_code)
        if not area_weights:
            print(f"  skip {geography[area_code]['name']} ({area_code}): no LSOA weights")
            continue
        area_name = geography[area_code]["name"]
        if "address_count" in area_weights:
            weight_map = area_weights["address_count"]
            area_records = [records_by_lsoa[code] for code in weight_map if code in records_by_lsoa]
            role = "subject" if geography[area_code]["role"] == "subject" else "comparator"
            row = compute_subject_energy_row(
                area_records,
                weight_map,
                parish_code=area_code,
                parish_name=area_name,
                area_role=role,
            )
        else:
            weight_map = area_weights["area"]
            area_records = [records_by_lsoa[code] for code in weight_map if code in records_by_lsoa]
            row = compute_comparator_energy_row(area_records, weight_map, area_code, area_name)
        rows.append(
            build_metrics_row(
                row,
                source_id="desnz_lsoa_energy",
                retrieved_at=lsoa_provenance["retrieved_at"],
                raw_sha256=lsoa_provenance["sha256"],
                sources=sources,
            )
        )
        print(f"  {area_name} ({area_code}) {fuel}: {row.value:.2f} {row.unit}")

    area_records = fetch_regional_la_energy(fuel, [YEAR], {SOUTH_OXFORDSHIRE_CODE, ENGLAND_CODE})
    area_provenance = latest_manifest(f"desnz_regional_la_energy/{fuel}")
    for record in area_records:
        role = "district" if record.area_code == SOUTH_OXFORDSHIRE_CODE else "national"
        row = compute_area_energy_row(record, area_role=role)
        rows.append(
            build_metrics_row(
                row,
                source_id="desnz_regional_la_energy",
                retrieved_at=area_provenance["retrieved_at"],
                raw_sha256=area_provenance["sha256"],
                sources=sources,
            )
        )
        print(f"  {record.area_name} ({record.area_code}) {fuel}: {row.value:.2f} {row.unit}")

    return rows


def main() -> None:
    geography = load_geography()
    sources = load_sources()
    lsoa_weights = _load_lsoa_weights()

    all_rows: list[dict] = []
    for fuel in ("electricity", "gas"):
        print(f"Fetching {fuel}...")
        all_rows.extend(_build_energy_rows_for_fuel(fuel, geography, lsoa_weights, sources))

    df = rows_to_dataframe(all_rows)
    write_metrics_csv(df, METRICS_CSV_PATH)
    write_readme(df, README_PATH)
    print(f"\nWrote {len(df)} rows to {METRICS_CSV_PATH}")
    print(f"Wrote {README_PATH}")


if __name__ == "__main__":
    main()
