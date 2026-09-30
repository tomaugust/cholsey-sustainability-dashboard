"""Fetch ONS population and household/dwelling denominators
(development-plan.md Phase 2, P2.8).

P1.6/ADR-0005 already computed these once, by hand: a mid-2021 parish
population figure (baked into a reference JSON) and a Census Day OA-level
population/household sum for Cholsey/Moulsford (also baked into a
reference JSON, pulled from nomis once and never re-fetched). This module
turns both into genuinely re-fetchable live sources, per ADR-0005's own
note that this remained P2.8's job.

Two independent sources:

1. **Direct parish-level mid-year population** (ONS ad-hoc release,
   "Parish population estimates for mid-YYYY, based on best-fitting of
   output areas to parishes"). Covers Cholsey and all 8 comparators
   directly, no OA lookup needed. Real finding (2026-09-30): a mid-2022
   vintage now exists in addition to the mid-2021 one P1.6 used (Cholsey:
   4,423 for mid-2022 vs 4,404 for mid-2021) -- confirmed live by
   searching ons.gov.uk, not assumed. Each vintage gets a new numeric
   ad-hoc ID and isn't linked from the previous vintage's page, so this
   discovers the current one by scraping ONS's own site search for the
   newest "...formidYYYYbasedonbestfittingofoutputareastoparishes" result,
   the same "search, don't guess" pattern as P2.5's GOV.UK site-search
   discovery for `desnz_regional_la_energy`.
2. **Census 2021 OA-level population/household counts via the nomis API**
   (NM_2021_1 / NM_2059_1 -- the same two datasets P1.6's reference JSON
   was a one-off snapshot of), aggregated to parish via
   `geography.denominators.sum_by_parish` (the existing P1.4/P1.6 OA-
   >parish best-fit join, reused rather than duplicated). Scoped to
   Cholsey/Moulsford's existing OA set only, same as P1.6/ADR-0005 --
   comparator-level OA lookups remain the separate backlog item
   ("comparator-level apportionment", STATUS.md), not P2.8's to build.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from io import StringIO
from typing import Literal

import requests
from openpyxl import load_workbook

from cholsey_pipeline.fetch.http import fetch_file

ONS_SEARCH_URL = "https://www.ons.gov.uk/search"
"""Verified live 2026-09-30 (P2.8): a plain GET with a `q` query param
returns a server-rendered results page (no separate JSON API found)."""

PARISH_POP_LANDING_PATTERN = re.compile(
    r'href="(/peoplepopulationandcommunity/populationandmigration/populationestimates/'
    r"adhocs/\d+parishpopulationestimatesformid(\d{4})basedonbestfittingofoutputareastoparishes)\""
)

ASSET_LINK_PATTERN = re.compile(r'href="(/file\?uri=[^"]+\.xlsx)"')

PARISH_SHEET_NAME = "Parish Populations"


class OnsDiscoveryError(RuntimeError):
    """Raised when an ons.gov.uk page doesn't contain what was expected --
    never guessed, so a page layout/URL change surfaces loudly."""


def find_latest_parish_population_landing_path(search_page_html: str) -> tuple[int, str]:
    """Find the newest "parish population estimates for mid-YYYY" ad-hoc
    release's landing page path in ONS site-search results HTML. Pure
    function -- tested against a committed fixture, not fetched live
    (development-plan.md §5.1)."""
    matches = PARISH_POP_LANDING_PATTERN.findall(search_page_html)
    if not matches:
        raise OnsDiscoveryError(
            "No 'parish population estimates for mid-YYYY...' ad-hoc release "
            "found in the ONS search results"
        )
    path, year = max(matches, key=lambda m: int(m[1]))
    return int(year), path


def discover_parish_population_download_url(landing_page_html: str) -> str:
    """Find the current `.xlsx` asset link on a parish-population ad-hoc
    release's landing page HTML. Pure function, same pattern as
    fetch.desnz_lsoa_energy.discover_download_url."""
    match = ASSET_LINK_PATTERN.search(landing_page_html)
    if not match:
        raise OnsDiscoveryError("No .xlsx download link found on the landing page")
    return f"https://www.ons.gov.uk{match.group(1)}"


def fetch_current_parish_population_url() -> tuple[int, str]:
    """Live: search ons.gov.uk for the current vintage, then scrape its
    landing page for the current download link."""
    search_response = requests.get(
        ONS_SEARCH_URL,
        params={"q": "parish population estimates best-fitting output areas to parishes"},
        timeout=30,
    )
    search_response.raise_for_status()
    year, landing_path = find_latest_parish_population_landing_path(search_response.text)
    landing_response = requests.get(f"https://www.ons.gov.uk{landing_path}", timeout=30)
    landing_response.raise_for_status()
    return year, discover_parish_population_download_url(landing_response.text)


@dataclass(frozen=True)
class ParishPopulationRecord:
    """One parish's total mid-year population estimate. This ad-hoc
    release is parish-level only -- district/national comparator totals
    are a separate ONS release, same "not actually the same publication"
    pattern P2.5 found for DESNZ's LSOA vs regional/LA energy data."""

    vintage_year: int
    parish_code: str
    parish_name: str
    total_population: int


def parse_parish_population_sheet(
    rows: list[tuple[object, ...]], vintage_year: int, parish_codes: set[str] | None = None
) -> list[ParishPopulationRecord]:
    """Parse the "Parish Populations" sheet's rows (as `(PAR*CD, PAR*NM,
    Total, ...age band columns not needed here)` tuples -- real columns
    verified live 2026-09-30), optionally filtered to `parish_codes`.

    Pure function -- tested against a real trimmed fixture.
    """
    header, *data_rows = rows
    code_idx = header.index("PAR22CD")
    name_idx = header.index("PAR22NM")
    total_idx = header.index("Total")
    records = []
    for row in data_rows:
        code = row[code_idx]
        if parish_codes is not None and code not in parish_codes:
            continue
        records.append(
            ParishPopulationRecord(
                vintage_year=vintage_year,
                parish_code=code,
                parish_name=row[name_idx],
                total_population=row[total_idx],
            )
        )
    return records


def read_parish_population(
    xlsx_path, vintage_year: int, parish_codes: set[str] | None = None
) -> list[ParishPopulationRecord]:
    """Live: read a downloaded parish-population workbook."""
    workbook = load_workbook(xlsx_path, data_only=True, read_only=True)
    worksheet = workbook[PARISH_SHEET_NAME]
    rows = [row for row in worksheet.iter_rows(values_only=True)]
    return parse_parish_population_sheet(rows, vintage_year, parish_codes)


def fetch_parish_population(
    parish_codes: set[str] | None = None,
) -> list[ParishPopulationRecord]:
    """Full live fetch: discover the current vintage's download URL, fetch
    it (via fetch.http.fetch_file), and parse rows for the requested
    parishes."""
    year, download_url = fetch_current_parish_population_url()
    result = fetch_file(
        "ons_parish_population",
        download_url,
        dest_filename=f"parish_population_mid{year}.xlsx",
    )
    if result.file_path is None:
        raise RuntimeError("fetch_file returned no file_path for ons_parish_population")
    return read_parish_population(result.file_path, year, parish_codes)


# --- Census 2021 OA-level counts via nomis (population, households) ---

NOMIS_URL_TEMPLATE = "https://www.nomisweb.co.uk/api/v01/dataset/{dataset_id}.data.csv"

NomisMetric = Literal["population", "households"]

NOMIS_DATASETS: dict[NomisMetric, dict[str, str]] = {
    "population": {
        "dataset_id": "NM_2021_1",
        "category_code_field": "C2021_RESTYPE_3_CODE",
        "total_category_code": "0",
    },
    "households": {
        "dataset_id": "NM_2059_1",
        "category_code_field": "C2021_HH_1_CODE",
        "total_category_code": "0",
    },
}
"""Real dataset IDs and category codes verified live 2026-09-30 against
the nomis API -- the same two datasets P1.6's reference JSON snapshot was
pulled from by hand (see its `_provenance` block)."""


def parse_nomis_oa_csv(csv_text: str, metric: NomisMetric) -> dict[str, int]:
    """Parse a nomis dataset CSV response into `{OA21CD: count}`, keeping
    only the "total" category row per geography (population rows also
    include "lives in a household"/"lives in a communal establishment"
    breakdown rows that must not be summed in as well).

    Pure function -- tested against a real trimmed fixture.
    """
    spec = NOMIS_DATASETS[metric]
    reader = csv.DictReader(StringIO(csv_text))
    counts: dict[str, int] = {}
    for row in reader:
        if row[spec["category_code_field"]] != spec["total_category_code"]:
            continue
        counts[row["GEOGRAPHY_CODE"]] = int(row["OBS_VALUE"])
    return counts


def fetch_oa_counts(metric: NomisMetric, oa_codes: list[str]) -> dict[str, int]:
    """Live: query the nomis API for `metric` (population or households)
    for the given OA21CD codes."""
    spec = NOMIS_DATASETS[metric]
    url = NOMIS_URL_TEMPLATE.format(dataset_id=spec["dataset_id"])
    response = requests.get(
        url, params={"geography": ",".join(oa_codes), "measures": "20100"}, timeout=30
    )
    response.raise_for_status()
    return parse_nomis_oa_csv(response.text, metric)
