"""Fetch DESNZ sub-national domestic electricity/gas consumption
(development-plan.md Phase 2, P2.5): LSOA-level figures for every
available year, plus district and national totals.

Real finding while building this module: the LSOA-level release
("Lower and middle super output areas <fuel> consumption") and the
district/national-level release ("Regional and local authority <fuel>
consumption statistics") are two DIFFERENT GOV.UK statistics
publications, not one release as P2.5's summary wording suggested --
related, in the same "sub-national electricity consumption data"
collection, but published and updated separately, each with its own
landing page and its own current-year `.xlsx` asset link. This module
treats them as the two sibling sources they actually are.

Both releases' asset URLs are hash-named
(assets.publishing.service.gov.uk/media/<hash>/...) and change on every
annual update, so this module discovers the current link by scraping the
landing page each run rather than hardcoding a snapshot (see
config/sources.yaml's discovery_rule note and P1's boundaries.py /
lsoa_overlap.py worklog entries for the same "search, don't guess"
pattern).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

import requests
from openpyxl import load_workbook

from cholsey_pipeline.fetch.http import fetch_file

Fuel = Literal["electricity", "gas"]

LSOA_LANDING_URLS: dict[Fuel, str] = {
    "electricity": (
        "https://www.gov.uk/government/statistics/"
        "lower-and-middle-super-output-areas-electricity-consumption"
    ),
    "gas": (
        "https://www.gov.uk/government/statistics/"
        "lower-and-middle-super-output-areas-gas-consumption"
    ),
}
REGIONAL_LA_LANDING_URLS: dict[Fuel, str] = {
    "electricity": (
        "https://www.gov.uk/government/statistics/"
        "regional-and-local-authority-electricity-consumption-statistics"
    ),
    "gas": (
        "https://www.gov.uk/government/statistics/"
        "regional-and-local-authority-gas-consumption-statistics"
    ),
}
"""Verified live 2026-09-29 (P2.5). Discovered via the GOV.UK site search
API (api/search.json), not guessed -- see the P2.5 worklog entry."""

LSOA_FILENAME_PATTERNS: dict[Fuel, re.Pattern[str]] = {
    "electricity": re.compile(r"LSOA_domestic_elec_\d{4}-\d{4}\.xlsx$"),
    "gas": re.compile(r"LSOA_domestic_gas_\d{4}-\d{4}\.xlsx$"),
}
REGIONAL_LA_FILENAME_PATTERNS: dict[Fuel, re.Pattern[str]] = {
    "electricity": re.compile(r"Subnational_electricity_consumption_statistics_\d{4}-\d{4}\.xlsx$"),
    "gas": re.compile(r"Subnational_gas_consumption_statistics_\d{4}-\d{4}\.xlsx$"),
}

ASSET_LINK_PATTERN = re.compile(
    r'href="(https://assets\.publishing\.service\.gov\.uk/media/[^"]+\.xlsx)"'
)

LSOA_HEADER_ROW = 5
"""1-indexed row the column headers are on, in every LSOA-level sheet --
verified live 2026-09-29 against the real 2023 electricity sheet."""
REGIONAL_LA_HEADER_ROW = 5
"""Same, for the regional/local-authority sheets."""


class DesnzDiscoveryError(RuntimeError):
    """Raised when a GOV.UK landing page doesn't contain a matching .xlsx
    link -- never guessed, so a page layout change surfaces loudly."""


class DesnzParseError(RuntimeError):
    """Raised when a workbook's sheet doesn't have the expected columns."""


def discover_download_url(landing_page_html: str, filename_pattern: re.Pattern[str]) -> str:
    """Find the current `.xlsx` asset URL on a GOV.UK statistics landing
    page's HTML, matching `filename_pattern`. Pure function -- tested
    against a committed fixture HTML snippet, not fetched live
    (development-plan.md §5.1)."""
    for match in ASSET_LINK_PATTERN.finditer(landing_page_html):
        url = match.group(1)
        if filename_pattern.search(url):
            return url
    raise DesnzDiscoveryError(
        f"No .xlsx link matching {filename_pattern.pattern!r} found on the landing page"
    )


def fetch_current_download_url(landing_url: str, filename_pattern: re.Pattern[str]) -> str:
    """Live version of discover_download_url: fetches the landing page
    then discovers the link. The network call itself isn't covered by
    tests, same as geography.boundaries.fetch_boundary."""
    response = requests.get(landing_url, timeout=30)
    response.raise_for_status()
    return discover_download_url(response.text, filename_pattern)


@dataclass(frozen=True)
class LsoaEnergyRecord:
    """One LSOA's domestic consumption for one year."""

    year: int
    lsoa_code: str
    lsoa_name: str
    la_code: str
    la_name: str
    number_of_meters: float
    total_consumption_kwh: float


@dataclass(frozen=True)
class AreaEnergyRecord:
    """One region/country/local-authority's domestic consumption for one
    year, from the regional/LA-level release."""

    year: int
    area_code: str
    area_name: str
    number_of_domestic_meters_thousands: float
    total_domestic_consumption_gwh: float


def _iter_data_rows(rows: list[tuple[Any, ...]], header_row: int) -> list[tuple[Any, ...]]:
    """Rows are 0-indexed in `rows`; `header_row` is 1-indexed (matching
    Excel's own row numbering, as used in this module's *_HEADER_ROW
    constants) -- data starts immediately after it."""
    return rows[header_row:]


def parse_lsoa_sheet(
    rows: list[tuple[Any, ...]], year: int, lsoa_codes: set[str] | None = None
) -> list[LsoaEnergyRecord]:
    """Parse one year's LSOA-level sheet (as a list of row tuples, exactly
    as `worksheet.iter_rows(values_only=True)` yields them) into
    LsoaEnergyRecords, optionally filtered to `lsoa_codes`.

    Column order verified live 2026-09-29 against the real 2023
    electricity sheet: la_code, la_name, msoa_code, msoa_name, lsoa_code,
    lsoa_name, num_meters, total_kwh, mean_kwh, median_kwh.
    """
    data_rows = _iter_data_rows(rows, LSOA_HEADER_ROW)
    records = []
    for row in data_rows:
        if len(row) < 8 or row[4] is None:
            continue
        lsoa_code = row[4]
        if lsoa_codes is not None and lsoa_code not in lsoa_codes:
            continue
        records.append(
            LsoaEnergyRecord(
                year=year,
                lsoa_code=lsoa_code,
                lsoa_name=row[5],
                la_code=row[0],
                la_name=row[1],
                number_of_meters=row[6],
                total_consumption_kwh=row[7],
            )
        )
    return records


def parse_regional_la_sheet(
    rows: list[tuple[Any, ...]], year: int, area_codes: set[str] | None = None
) -> list[AreaEnergyRecord]:
    """Parse one year's regional/local-authority sheet into
    AreaEnergyRecords, optionally filtered to `area_codes` (GSS codes,
    e.g. a local authority district code or a country code like
    E92000001 for England).

    Column order verified live 2026-09-29 against the real 2023
    electricity sheet: code, country_or_region, local_authority,
    <meter counts...>, <consumption...> -- this function reads column 0
    (code), 1/2 (name -- region name if this is a country/region summary
    row, else the local authority name), 5 (all-domestic meters,
    thousands) and 10 (all-domestic consumption, GWh).
    """
    data_rows = _iter_data_rows(rows, REGIONAL_LA_HEADER_ROW)
    records = []
    for row in data_rows:
        if len(row) < 11 or row[0] is None:
            continue
        area_code = row[0]
        if area_codes is not None and area_code not in area_codes:
            continue
        area_name = row[2] if row[2] and row[2] != "All local authorities" else row[1]
        records.append(
            AreaEnergyRecord(
                year=year,
                area_code=area_code,
                area_name=area_name,
                number_of_domestic_meters_thousands=row[5],
                total_domestic_consumption_gwh=row[10],
            )
        )
    return records


def read_lsoa_energy(
    xlsx_path: str,
    years: list[int],
    lsoa_codes: set[str] | None = None,
) -> list[LsoaEnergyRecord]:
    """Read and parse multiple years' sheets from a downloaded LSOA-level
    workbook. Each sheet is named after its year (e.g. "2023")."""
    workbook = load_workbook(xlsx_path, read_only=True, data_only=True)
    all_records = []
    for year in years:
        sheet_name = str(year)
        if sheet_name not in workbook.sheetnames:
            raise DesnzParseError(f"No sheet named {sheet_name!r} in {xlsx_path}")
        rows = list(workbook[sheet_name].iter_rows(values_only=True))
        all_records.extend(parse_lsoa_sheet(rows, year, lsoa_codes))
    return all_records


def read_regional_la_energy(
    xlsx_path: str,
    years: list[int],
    area_codes: set[str] | None = None,
) -> list[AreaEnergyRecord]:
    """Read and parse multiple years' sheets from a downloaded regional/
    local-authority workbook."""
    workbook = load_workbook(xlsx_path, read_only=True, data_only=True)
    all_records = []
    for year in years:
        sheet_name = str(year)
        if sheet_name not in workbook.sheetnames:
            raise DesnzParseError(f"No sheet named {sheet_name!r} in {xlsx_path}")
        rows = list(workbook[sheet_name].iter_rows(values_only=True))
        all_records.extend(parse_regional_la_sheet(rows, year, area_codes))
    return all_records


def fetch_lsoa_energy(
    fuel: Fuel,
    years: list[int],
    lsoa_codes: set[str] | None = None,
) -> list[LsoaEnergyRecord]:
    """Full live fetch: discover the current LSOA-level download URL,
    fetch it (via fetch.http.fetch_file), and parse the requested years."""
    download_url = fetch_current_download_url(LSOA_LANDING_URLS[fuel], LSOA_FILENAME_PATTERNS[fuel])
    result = fetch_file(f"desnz_lsoa_{fuel}", download_url, dest_filename=f"lsoa_{fuel}.xlsx")
    if result.file_path is None:
        raise RuntimeError(f"fetch_file returned no file_path for desnz_lsoa_{fuel}")
    return read_lsoa_energy(str(result.file_path), years, lsoa_codes)


def fetch_regional_la_energy(
    fuel: Fuel,
    years: list[int],
    area_codes: set[str] | None = None,
) -> list[AreaEnergyRecord]:
    """Full live fetch: discover the current regional/LA-level download
    URL, fetch it, and parse the requested years."""
    download_url = fetch_current_download_url(
        REGIONAL_LA_LANDING_URLS[fuel], REGIONAL_LA_FILENAME_PATTERNS[fuel]
    )
    result = fetch_file(
        f"desnz_regional_la_{fuel}", download_url, dest_filename=f"regional_la_{fuel}.xlsx"
    )
    if result.file_path is None:
        raise RuntimeError(f"fetch_file returned no file_path for desnz_regional_la_{fuel}")
    return read_regional_la_energy(str(result.file_path), years, area_codes)
