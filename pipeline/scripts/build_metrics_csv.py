#!/usr/bin/env python3
"""Build data/processed/metrics.csv, data/processed/README.md, and the
site's web/src/data/{metrics,sources,areas}.json (P3.9, development-plan.md
§2.3: "export.py writes web/src/data/metrics.json ... plus sources.json
and areas.json").

**Scope so far**: metrics 1, 2, 3 and 4 (tree canopy cover, accessible
greenspace, domestic electricity and gas) -- all four fully covered
(subject, every comparator with real data, district, national). MCS
(metrics 5/6) is still outstanding -- blocked on Tom's pending
parish-level data request (see STATUS.md), not a methodology gap like
the others were. See ADR-0010's "Consequences" and the P3.9 worklogs for
why the full integration wasn't attempted in one sitting. Each metric's
own `compute_*_row` functions and real area/ward/LSOA mappings already
exist from Phase 3's per-metric work, so this script's
fetch -> compute -> `export.build_metrics_row` pattern carries over
directly to the rest, not redesigned each time.

Greenspace's national row is the single slowest step here (re-fetches
England's ~150,000 OS Open Greenspace sites, ~550s, then a
simplify/within/clip pass, ~260s) -- see `_build_greenspace_national_row`
and `metrics/greenspace.py`'s module docstring for why a direct clip
against England's full-precision boundary doesn't finish in a reasonable
time. Budget ~10-15 minutes for a full run of this script.

Canopy's per-area Forest Research ward mapping
(`_DOMINANT_WARD_FOREST_RESEARCH_OVERRIDE` below) is small and
hand-maintained rather than re-derived by a live name-lookup every run,
because the mapping itself is the result of ADR-0006's real
vintage-mismatch investigation (2026-09-29) and the P3.2 comparator-rows
work (commit 4a6aaec, 2026-09-30) -- re-deriving it live each run would
re-run the same ambiguous-name-matching research for no benefit, when the
real, already-verified answer is just two overrides (see the constant's
own docstring). The *weights* and *which ward is dominant* still come
from the live, regenerable `weights.csv`, not hardcoded -- only the
"which Forest Research vintage code does this current ward's name
correspond to" fact is hand-maintained, since that's a one-off historical
lookup, not a value that changes on refresh.

Canopy's **district** row takes the opposite approach: every current
ward and its Forest Research match is re-derived LIVE each run (a live
ward-to-LAD lookup, `WARD_TO_LAD_QUERY_URL`, cross-matched against
Forest Research's own real ward names), not hand-maintained, since
there's no ambiguity to resolve once South Oxfordshire's real ward list
is known -- unlike the 2-entry subject/comparator override, which exists
specifically because that ambiguity (which vintage code is "Cholsey")
needed a one-off human-verified decision.

Run live (not wired into `make refresh`, which is a Phase 2/3 stub per
the Makefile):

    cd pipeline && uv run python scripts/build_metrics_csv.py

This is generated output -- never hand-edit `data/processed/metrics.csv`,
`data/processed/README.md`, or `web/src/data/{metrics,sources,areas}.json`
directly (CLAUDE.md's non-negotiable rule). Re-run this script instead.
"""

from __future__ import annotations

import csv
import time

import geopandas as gpd
import pandas as pd
import requests

from cholsey_pipeline.export import (
    build_areas_json,
    build_metrics_json,
    build_metrics_row,
    build_sources_json,
    rows_to_dataframe,
    write_json,
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
from cholsey_pipeline.fetch.http import fetch_file, latest_manifest
from cholsey_pipeline.fetch.os_open_greenspace import SOURCE_ID as GREENSPACE_SOURCE_ID
from cholsey_pipeline.fetch.os_open_greenspace import fetch_greenspace_sites
from cholsey_pipeline.geography.boundaries import fetch_boundary
from cholsey_pipeline.metrics.canopy import (
    compute_district_canopy_row,
    compute_national_canopy_row,
    compute_subject_canopy_row,
)
from cholsey_pipeline.metrics.energy import (
    compute_area_energy_row,
    compute_comparator_energy_row,
    compute_subject_energy_row,
)
from cholsey_pipeline.metrics.greenspace import (
    ACCESSIBLE_FUNCTION_TYPES,
    compute_national_greenspace_row,
    compute_subject_greenspace_row,
)
from cholsey_pipeline.registry import REPO_ROOT, load_geography, load_sources

ENERGY_YEARS = list(range(2010, 2025))
"""Every year DESNZ's LSOA-level electricity/gas releases actually cover
(verified live 2026-10-02 by reading the real downloaded workbooks' own
sheet names: both fuels' LSOA-level sheets run 2010-2024; the
regional/LA-level sheets go back further, to 2005, but 2010 is used
throughout for an apples-to-apples trend across subject/comparator/
district/national rows, since LSOA-level is the limiting factor). This
is the real, full trend development-plan.md's Phase 3 "Key outcomes"
wants ("all available years"), not just the latest year -- a real gap
against that goal in every earlier P3.9 firing this phase, which only
ever fetched `[2024]`."""

REGIONAL_LA_YEARS = list(range(2012, 2025))
"""DESNZ's regional/LA-level workbooks (district/national rows only --
the LSOA-level sheets above aren't affected) can't be trusted for
2010-2011 for TWO independent, genuine upstream reasons, both verified
live 2026-10-02 by reading the real downloaded workbooks directly (not
guessed):

1. **Electricity** changed column layout between its real 2011 and 2012
   sheets: 2005-2011 use a "Mean consumption: Domestic/Non-Domestic"
   layout with no Standard/E7 split, while 2012 onward use the "Domestic
   Standard/Domestic E7" layout `parse_regional_la_sheet`'s
   `_REGIONAL_LA_EXPECTED_HEADER` is written for -- a genuine second
   upstream layout break, on top of the already-known electricity-vs-gas
   split from P3.4.

2. **Both fuels** (gas confirmed directly; electricity shares the same
   sheet template so almost certainly affected too) identify
   country/region/LA rows by an old pre-GSS code scheme in 2010-2011
   (e.g. South Oxfordshire is `38UD`, England's row has a blank code),
   switching to current GSS codes (`E07000179`, `E92000001`) only from
   2012 onward. `parse_regional_la_sheet` filters by GSS `area_codes`, so
   for 2010-2011 this silently matches zero rows -- no exception, just
   fewer years than requested (this is exactly how the initial "gas
   returns only 13 of 15 years" finding surfaced: no parse error, because
   gas's *column* layout genuinely is stable back to 2010 -- only the
   *area-code* scheme isn't).

Rather than silently misread the older layout, join on the old code
scheme, or widen this integration script into a parser fix, this just
narrows BOTH fuels' district/national year range to 2012-2024, where
`parse_regional_la_sheet` already handles column layout and GSS codes
correctly. The real pre-2012 district/national figures (both fuels) are
a documented, carried-over gap (see STATUS.md), not silently dropped
without explanation. LSOA-level rows are unaffected (DESNZ's LSOA
sheets have always used GSS-equivalent LSOA codes), so subject/
comparator rows keep the full `ENERGY_YEARS` range."""

NATIONAL_CANOPY_YEAR = 2020
"""The modal real Forest Research survey year across England's wards
(2,135 of 5,867 non-placeholder records), used as the representative
label for the national canopy row -- see ADR-0009."""

SOUTH_OXFORDSHIRE_CODE = "E07000179"
ENGLAND_CODE = "E92000001"

WEIGHTS_CSV = REPO_ROOT / "data" / "processed" / "geography" / "weights.csv"
METRICS_CSV_PATH = REPO_ROOT / "data" / "processed" / "metrics.csv"
README_PATH = REPO_ROOT / "data" / "processed" / "README.md"
SITE_DATA_DIR = REPO_ROOT / "web" / "src" / "data"
METRICS_JSON_PATH = SITE_DATA_DIR / "metrics.json"
SOURCES_JSON_PATH = SITE_DATA_DIR / "sources.json"
AREAS_JSON_PATH = SITE_DATA_DIR / "areas.json"

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

WARD_TO_LAD_QUERY_URL = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "WD20_LAD20_UK_LU_v2_3784d8d58a134af091cf9601bd36acdf/FeatureServer/0/query"
)
"""ONS "Ward to Local Authority District (December 2020) Lookup in the
United Kingdom V2" -- found live via the ArcGIS Hub item search API
(`hub.arcgis.com/api/search/v1/collections/dataset/items?q=...`), not
guessed, re-discovered 2026-10-02 (an earlier firing used this same
service without recording its URL anywhere reusable). Gives every
current (Dec 2020) ward's own containing LAD, used here to find South
Oxfordshire's real 21 wards for the canopy district row."""

SOUTH_OXFORDSHIRE_FR_WARD_CODE_RANGE = range(733, 754)
"""Forest Research's own ward codes for all 21 of South Oxfordshire's
wards happen to be contiguous -- E05009733 through E05009753 -- verified
live 2026-10-02 (every code in this range really is a South Oxfordshire
ward, by cross-matching each one's real `wardname` against the real
current ward list from `WARD_TO_LAD_QUERY_URL`, not assumed from the
range alone)."""

GREENSPACE_YEAR = 2021
"""OS Open Greenspace is a continuously-refreshed snapshot, not
year-stamped data -- 2021 matches the Census/mid-2021 population vintage
each row's denominator uses (same convention the original P3.3 rows
used)."""

NOMIS_URL = "https://www.nomisweb.co.uk/api/v01/dataset/NM_2021_1.data.csv"
"""Census 2021 usual-resident population by local authority/country,
same dataset P1.6/ADR-0005 already uses at OA level -- queried here
directly at LAD/country level for South Oxfordshire's and England's real
denominators (verified live 2026-09-30/2026-10-01, re-fetched here rather
than hardcoded)."""


def _fetch_census_2021_population(area_code: str) -> int:
    """Live Census 2021 usual-resident population for one LAD/country
    area code, via the nomis API (`NOMIS_URL`), filtered to the "Total:
    all usual residents" row."""
    result = fetch_file(
        "ons_census_2021_population_la",
        f"{NOMIS_URL}?geography={area_code}&measures=20100",
        dest_filename=f"population_{area_code}.csv",
    )
    if result.file_path is None:
        raise RuntimeError("fetch_file returned no file_path for census population")
    text = result.file_path.read_text(encoding="utf-8")
    reader = csv.DictReader(text.splitlines())
    for row in reader:
        if row["C2021_RESTYPE_3_CODE"] == "0":
            return int(row["OBS_VALUE"])
    raise ValueError(f"No 'Total: All usual residents' row found for {area_code}")


def _build_greenspace_rows(geography: dict[str, dict], sources: dict[str, dict]) -> list[dict]:
    rows: list[dict] = []
    subject_comparator_codes = [
        code for code, entry in geography.items() if entry["role"] in ("subject", "comparator")
    ]

    parishes_gdf = fetch_boundary("parish_bfc", codes=subject_comparator_codes)
    parish_areas = dict(zip(parishes_gdf["PARNCP23CD"], parishes_gdf.geometry.area, strict=True))
    parish_sites = fetch_greenspace_sites(parishes_gdf)
    greenspace_provenance = latest_manifest(GREENSPACE_SOURCE_ID)

    for area_code in subject_comparator_codes:
        area_name = geography[area_code]["name"]
        population = geography[area_code]["population_mid2021_estimate"]
        area_geom = parishes_gdf.loc[parishes_gdf["PARNCP23CD"] == area_code, "geometry"].iloc[0]
        clipped = gpd.clip(parish_sites, area_geom)
        role = "subject" if geography[area_code]["role"] == "subject" else "comparator"
        row = compute_subject_greenspace_row(
            clipped,
            parish_areas[area_code],
            population,
            GREENSPACE_YEAR,
            parish_code=area_code,
            parish_name=area_name,
            area_role=role,
        )
        rows.append(
            build_metrics_row(
                row,
                source_id=GREENSPACE_SOURCE_ID,
                retrieved_at=greenspace_provenance["retrieved_at"],
                raw_sha256=_manifest_hash(greenspace_provenance),
                sources=sources,
            )
        )
        print(f"  {area_name} ({area_code}) greenspace: {row.value:.2f} {row.unit}")

    district_row = _build_greenspace_district_row(sources)
    rows.append(district_row)
    print(f"  South Oxfordshire ({SOUTH_OXFORDSHIRE_CODE}) greenspace: district row added")

    national_row = _build_greenspace_national_row(sources)
    rows.append(national_row)
    print(f"  England ({ENGLAND_CODE}) greenspace: national row added")

    return rows


def _build_greenspace_district_row(sources: dict[str, dict]) -> dict:
    lad_gdf = fetch_boundary("lad_bfc", codes=[SOUTH_OXFORDSHIRE_CODE])
    lad_area_m2 = float(lad_gdf.geometry.area.iloc[0])
    lad_sites = fetch_greenspace_sites(lad_gdf, buffer_m=0.0)
    greenspace_provenance = latest_manifest(GREENSPACE_SOURCE_ID)
    clipped = gpd.clip(lad_sites, lad_gdf.geometry.iloc[0])
    population = _fetch_census_2021_population(SOUTH_OXFORDSHIRE_CODE)

    row = compute_subject_greenspace_row(
        clipped,
        lad_area_m2,
        population,
        GREENSPACE_YEAR,
        parish_code=SOUTH_OXFORDSHIRE_CODE,
        parish_name="South Oxfordshire",
        area_role="district",
        boundary_label="district boundary",
        population_label="the real Census 2021 total (not a mid-2021 estimate)",
    )
    return build_metrics_row(
        row,
        source_id=GREENSPACE_SOURCE_ID,
        retrieved_at=greenspace_provenance["retrieved_at"],
        raw_sha256=_manifest_hash(greenspace_provenance),
        sources=sources,
    )


def _build_greenspace_national_row(sources: dict[str, dict]) -> dict:
    """England's real area-weighted greenspace figure. Unlike the
    parish/district clips, England's real site set (~150,000 sites) and
    real BFC boundary (20MB WKB) are too large/complex to clip directly
    in a reasonable time -- simplify the boundary first, then split into
    a fast `.within()` pass (sites fully inside, no clip needed) and an
    exact `gpd.clip()` only for the much smaller boundary-straddling
    candidate set (the same pattern the original P3.3 national-row firing
    established and documented in `metrics/greenspace.py`'s module
    docstring)."""
    t0 = time.time()
    country_gdf = fetch_boundary("country_bfc", codes=[ENGLAND_CODE])
    country_geom = country_gdf.geometry.iloc[0]
    england_area_m2 = float(country_geom.area)

    england_sites = fetch_greenspace_sites(country_gdf, buffer_m=0.0, timeout=900)
    greenspace_provenance = latest_manifest(GREENSPACE_SOURCE_ID)
    print(f"    fetched {len(england_sites)} England sites in {time.time() - t0:.0f}s")

    simplified = country_geom.simplify(50.0, preserve_topology=True)
    within_mask = england_sites.geometry.within(simplified)
    fully_within = england_sites[within_mask]
    boundary_candidates = england_sites[~within_mask]
    clipped_boundary = (
        gpd.clip(boundary_candidates, country_gdf)
        if len(boundary_candidates) > 0
        else boundary_candidates.iloc[0:0]
    )
    accessible_all = gpd.GeoDataFrame(
        pd.concat(
            [fully_within[["function", "geometry"]], clipped_boundary[["function", "geometry"]]],
            ignore_index=True,
        ),
        crs=england_sites.crs,
    )
    accessible = accessible_all[accessible_all["function"].isin(ACCESSIBLE_FUNCTION_TYPES)]
    accessible_area_m2 = float(accessible.geometry.area.sum())
    print(f"    accessible area m2: {accessible_area_m2}, total time {time.time() - t0:.0f}s")

    population = _fetch_census_2021_population(ENGLAND_CODE)
    row = compute_national_greenspace_row(
        accessible_area_m2,
        england_area_m2,
        population,
        GREENSPACE_YEAR,
    )
    return build_metrics_row(
        row,
        source_id=GREENSPACE_SOURCE_ID,
        retrieved_at=greenspace_provenance["retrieved_at"],
        raw_sha256=_manifest_hash(greenspace_provenance),
        sources=sources,
    )


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

    district_row = _build_canopy_district_row(sources)
    rows.append(district_row)
    print(f"  South Oxfordshire ({SOUTH_OXFORDSHIRE_CODE}) canopy: district row added")

    return rows


def _fetch_current_wards_for_lad(lad_code: str) -> dict[str, str]:
    """Returns {current_ward_code: current_ward_name} for every current
    (Dec 2020) ward in `lad_code`, via the live ONS ward-to-LAD lookup
    (`WARD_TO_LAD_QUERY_URL`)."""
    params = {
        "where": f"LAD20CD='{lad_code}'",
        "outFields": "WD20CD,WD20NM",
        "returnGeometry": "false",
        "f": "json",
    }
    response = requests.get(WARD_TO_LAD_QUERY_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    return {f["attributes"]["WD20CD"]: f["attributes"]["WD20NM"] for f in payload["features"]}


def _build_canopy_district_row(sources: dict[str, dict]) -> dict:
    """South Oxfordshire's real area-weighted canopy average across all
    21 of its own current wards (ADR-0006/P3.2's established method):
    find the district's real current wards live, fetch Forest Research's
    real records for its own (contiguous, live-verified)
    `SOUTH_OXFORDSHIRE_FR_WARD_CODE_RANGE`, match the two by real ward
    NAME (not assumed from any code pattern), then area-weight using each
    matched current ward's own real area."""
    current_wards = _fetch_current_wards_for_lad(SOUTH_OXFORDSHIRE_CODE)
    current_code_by_name = {name: code for code, name in current_wards.items()}

    fr_ward_codes = [f"E05009{n}" for n in SOUTH_OXFORDSHIRE_FR_WARD_CODE_RANGE]
    ward_records = fetch_ward_canopy(fr_ward_codes)
    ward_provenance = latest_manifest("forest_research_canopy")

    unmatched = [r.ward_name for r in ward_records if r.ward_name not in current_code_by_name]
    if unmatched:
        raise ValueError(
            f"Forest Research ward(s) {unmatched} did not match any current South "
            f"Oxfordshire ward by name -- real investigation needed (ADR-0006), not "
            f"a silent drop"
        )

    current_ward_codes = [current_code_by_name[r.ward_name] for r in ward_records]
    boundary_gdf = fetch_boundary("ward_bfc", codes=current_ward_codes)
    area_by_current_code = dict(
        zip(boundary_gdf["WD20CD"], boundary_gdf.geometry.area, strict=True)
    )

    ward_areas = {
        r.ward_code: area_by_current_code[current_code_by_name[r.ward_name]] for r in ward_records
    }

    district_row = compute_district_canopy_row(
        ward_records,
        ward_areas,
        district_code=SOUTH_OXFORDSHIRE_CODE,
        district_name="South Oxfordshire",
    )
    return build_metrics_row(
        district_row,
        source_id="forest_research_canopy",
        retrieved_at=ward_provenance["retrieved_at"],
        raw_sha256=_manifest_hash(ward_provenance),
        sources=sources,
    )


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

    lsoa_records = fetch_lsoa_energy(fuel, ENERGY_YEARS, all_lsoa_codes)
    lsoa_provenance = latest_manifest(f"desnz_lsoa_energy/{fuel}")
    records_by_year_lsoa: dict[int, dict[str, LsoaEnergyRecord]] = {}
    for r in lsoa_records:
        records_by_year_lsoa.setdefault(r.year, {})[r.lsoa_code] = r

    for area_code in subject_comparator_codes:
        area_weights = lsoa_weights.get(area_code)
        if not area_weights:
            print(f"  skip {geography[area_code]['name']} ({area_code}): no LSOA weights")
            continue
        area_name = geography[area_code]["name"]
        years_built = []
        for year, records_by_lsoa in sorted(records_by_year_lsoa.items()):
            if "address_count" in area_weights:
                weight_map = area_weights["address_count"]
                area_records = [
                    records_by_lsoa[code] for code in weight_map if code in records_by_lsoa
                ]
                if not area_records:
                    continue
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
                area_records = [
                    records_by_lsoa[code] for code in weight_map if code in records_by_lsoa
                ]
                if not area_records:
                    continue
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
            years_built.append(year)
        latest_row_value = rows[-1]["value"] if years_built else None
        print(
            f"  {area_name} ({area_code}) {fuel}: {len(years_built)} years "
            f"({min(years_built, default='-')}-{max(years_built, default='-')}), "
            f"latest {latest_row_value}"
        )

    area_records = fetch_regional_la_energy(
        fuel, REGIONAL_LA_YEARS, {SOUTH_OXFORDSHIRE_CODE, ENGLAND_CODE}
    )
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
    district_national_years = sorted({r.year for r in area_records})
    print(
        f"  South Oxfordshire/England {fuel}: {len(district_national_years)} years "
        f"({min(district_national_years, default='-')}-{max(district_national_years, default='-')})"
    )

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
    print("Fetching greenspace (this includes an England-wide fetch, budget ~10-15 minutes)...")
    all_rows.extend(_build_greenspace_rows(geography, sources))

    df = rows_to_dataframe(all_rows)
    write_metrics_csv(df, METRICS_CSV_PATH)
    write_readme(df, README_PATH)
    write_json(build_metrics_json(df), METRICS_JSON_PATH)
    write_json(build_sources_json(df, sources), SOURCES_JSON_PATH)
    write_json(build_areas_json(geography), AREAS_JSON_PATH)
    print(f"\nWrote {len(df)} rows to {METRICS_CSV_PATH}")
    print(f"Wrote {README_PATH}")
    print(f"Wrote {METRICS_JSON_PATH}, {SOURCES_JSON_PATH}, {AREAS_JSON_PATH}")


if __name__ == "__main__":
    main()
