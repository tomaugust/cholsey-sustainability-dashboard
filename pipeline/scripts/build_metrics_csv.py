#!/usr/bin/env python3
"""Build data/processed/metrics.csv and data/processed/README.md (P3.9).

**Scope so far**: metrics 1, 3 and 4 (tree canopy cover, domestic
electricity and gas). Greenspace (metric 2) and MCS (metrics 5/6) are
still outstanding -- see ADR-0010's "Consequences" and the P3.9 worklogs
for why the full integration wasn't attempted in one sitting. Each
metric's own `compute_*_row` functions and real area/ward/LSOA mappings
already exist from Phase 3's per-metric work, so this script's
fetch -> compute -> `export.build_metrics_row` pattern carries over
directly to the rest, not redesigned each time.

Canopy's per-area Forest Research ward mapping (`_DOMINANT_WARD_OVERRIDE`
below) is small and hand-maintained rather than re-derived by a live
name-lookup every run, because the mapping itself is the result of
ADR-0006's real vintage-mismatch investigation (2026-09-29) and the P3.2
comparator-rows work (commit 4a6aaec, 2026-09-30) -- re-deriving it live
each run would re-run the same ambiguous-name-matching research for no
benefit, when the real, already-verified answer is just two overrides
(see the constant's own docstring). The *weights* and *which ward is
dominant* still come from the live, regenerable `weights.csv`, not
hardcoded -- only the "which Forest Research vintage code does this
current ward's name correspond to" fact is hand-maintained, since that's
a one-off historical lookup, not a value that changes on refresh.

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
from cholsey_pipeline.fetch.forest_research_canopy import (
    fetch_ward_canopy,
    fetch_ward_canopy_for_country,
)
from cholsey_pipeline.fetch.http import latest_manifest
from cholsey_pipeline.metrics.canopy import (
    compute_national_canopy_row,
    compute_subject_canopy_row,
)
from cholsey_pipeline.metrics.energy import (
    compute_area_energy_row,
    compute_comparator_energy_row,
    compute_subject_energy_row,
)
from cholsey_pipeline.registry import REPO_ROOT, load_geography, load_sources

YEAR = 2024
"""The latest year DESNZ has published (verified live 2026-09-30, P3.4)."""

NATIONAL_CANOPY_YEAR = 2020
"""The modal real Forest Research survey year across England's wards
(2,135 of 5,867 non-placeholder records), used as the representative
label for the national canopy row -- see ADR-0009."""

SOUTH_OXFORDSHIRE_CODE = "E07000179"
ENGLAND_CODE = "E92000001"

WEIGHTS_CSV = REPO_ROOT / "data" / "processed" / "geography" / "weights.csv"
METRICS_CSV_PATH = REPO_ROOT / "data" / "processed" / "metrics.csv"
README_PATH = REPO_ROOT / "data" / "processed" / "README.md"

_DOMINANT_WARD_FOREST_RESEARCH_OVERRIDE = {
    "E05011701": "E05009737",  # current "Cholsey" ward -> FR's Dec 2018 "Cholsey" (ADR-0006)
    "E05011710": "E05009750",  # current "Wallingford" ward -> FR's own "Wallingford" (P3.2)
}
"""Maps a *current* (Dec 2020) ONS ward code to Forest Research's own
(possibly older-vintage) ward code for the same real ward, for the two
cases in this project's area set where they differ (ADR-0006's explicit
lesson: never assume a current ward code matches Forest Research's own
dataset). Every other area's dominant ward code already equals its
Forest Research code directly (verified live, P3.2 comparator rows)."""

_NO_FOREST_RESEARCH_RECORD = {"E05012133"}
"""Current ward codes with NO Forest Research canopy record at all --
a real, documented data gap (P3.2, 2026-09-30), not silently
interpolated. E05012133 is Basildon (West Berkshire), Aldworth's
containing ward."""


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


def _manifest_hash(manifest: dict) -> str:
    """Different fetchers write different key names for a manifest's
    content hash: `fetch_file`-based fetchers (e.g. `fetch_ward_canopy`)
    use `sha256`, while multi-page fetchers that write their own manifest
    directly (e.g. `fetch_ward_canopy_for_country`,
    `geography.boundaries.fetch_boundary`) use `response_sha256` -- see
    ADR-0010. Normalize here rather than changing either format."""
    return manifest.get("sha256") or manifest["response_sha256"]


def _load_dominant_ward_weights() -> dict[str, tuple[str, str, float]]:
    """Returns {parish_code: (current_ward_code, current_ward_name,
    weight)} -- the single ward contributing most of each parish's real
    area (from `weights.csv`'s `join_geography_type=ward` rows, P1.5/
    P3.2), live-regenerable, never hand-edited. A parish split across
    multiple wards (only South Stoke, 99.84%/0.16%) just gets its
    dominant ward -- the same sliver-dropping the committed test fixtures
    already use for this exact case."""
    best: dict[str, tuple[str, str, float]] = {}
    with WEIGHTS_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["join_geography_type"] != "ward":
                continue
            weight = float(row["weight"])
            existing = best.get(row["parish_code"])
            if existing is None or weight > existing[2]:
                best[row["parish_code"]] = (
                    row["join_geography_code"],
                    row["join_geography_name"],
                    weight,
                )
    return best


def _build_canopy_rows(geography: dict[str, dict], sources: dict[str, dict]) -> list[dict]:
    rows: list[dict] = []
    dominant_wards = _load_dominant_ward_weights()
    subject_comparator_codes = [
        code for code, entry in geography.items() if entry["role"] in ("subject", "comparator")
    ]

    fr_ward_code_for_area: dict[str, str] = {}
    for area_code in subject_comparator_codes:
        current_ward_code, _name, _weight = dominant_wards[area_code]
        if current_ward_code in _NO_FOREST_RESEARCH_RECORD:
            print(
                f"  skip {geography[area_code]['name']} ({area_code}): no Forest Research "
                f"record for its ward (real data gap, see ADR-0006/P3.2)"
            )
            continue
        fr_ward_code_for_area[area_code] = _DOMINANT_WARD_FOREST_RESEARCH_OVERRIDE.get(
            current_ward_code, current_ward_code
        )

    ward_records = fetch_ward_canopy(sorted(set(fr_ward_code_for_area.values())))
    ward_provenance = latest_manifest("forest_research_canopy")
    records_by_ward = {r.ward_code: r for r in ward_records}

    for area_code, fr_ward_code in fr_ward_code_for_area.items():
        area_name = geography[area_code]["name"]
        _current_code, _current_name, weight = dominant_wards[area_code]
        role = "subject" if geography[area_code]["role"] == "subject" else "comparator"
        row = compute_subject_canopy_row(
            records_by_ward[fr_ward_code],
            weight,
            parish_code=area_code,
            parish_name=area_name,
            area_role=role,
        )
        rows.append(
            build_metrics_row(
                row,
                source_id="forest_research_canopy",
                retrieved_at=ward_provenance["retrieved_at"],
                raw_sha256=_manifest_hash(ward_provenance),
                sources=sources,
            )
        )
        print(f"  {area_name} ({area_code}) canopy: {row.value:.2f}{row.unit}")

    national_records = fetch_ward_canopy_for_country("England")
    national_provenance = latest_manifest("forest_research_canopy")
    national_row = compute_national_canopy_row(national_records, year=NATIONAL_CANOPY_YEAR)
    rows.append(
        build_metrics_row(
            national_row,
            source_id="forest_research_canopy",
            retrieved_at=national_provenance["retrieved_at"],
            raw_sha256=_manifest_hash(national_provenance),
            sources=sources,
        )
    )
    print(f"  England ({ENGLAND_CODE}) canopy: {national_row.value:.2f}{national_row.unit}")

    print(
        "  (district row not yet built -- needs a live ward-to-LAD lookup "
        "re-derivation, see STATUS.md)"
    )

    return rows


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
                raw_sha256=_manifest_hash(lsoa_provenance),
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
                raw_sha256=_manifest_hash(area_provenance),
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
    print("Fetching canopy...")
    all_rows.extend(_build_canopy_rows(geography, sources))
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
