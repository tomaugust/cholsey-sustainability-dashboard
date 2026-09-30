"""Fetch DESNZ postcode-level domestic electricity/gas consumption,
filtered to OX10 (Cholsey's postcode district) (development-plan.md
Phase 2, P2.6).

Real finding while building this module: P2.1 (2026-09-28) concluded the
most recent postcode-level release findable was from 2020, because the
generic "Postcode level domestic gas and electricity consumption: about
the data" page carries no direct file links (it's a methodology page).
That conclusion was wrong -- postcode-level releases continue under a
year-specific slug each year (`postcode-level-electricity-statistics-YYYY`,
`postcode-level-gas-statistics-YYYY`), confirmed live through 2024, listed
on the "sub-national electricity/gas consumption data" collection pages
rather than linked from the generic methodology page. This module
discovers the current year by scraping the collection page rather than
assuming any specific year stays current.

Suppression note (spec §3, plan risk R4): DESNZ suppresses a postcode's
row if it has <5 meters, or if the top 2 meters make up >90% of
consumption, or if a meter's <100 kWh/yr (excluded entirely) -- so a
missing postcode in this data is not necessarily zero consumption, and a
caller needing every postcode should fall back to the LSOA-level figure
(fetch.desnz_lsoa_energy) with a `flag=parish_estimate`, not treat a
missing row as zero.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from io import StringIO
from typing import Literal

import requests

from cholsey_pipeline.contracts import SOURCE_CONTRACTS, validate_row_count, validate_schema
from cholsey_pipeline.fetch.http import fetch_file, previous_row_count, record_row_count

Fuel = Literal["electricity", "gas"]

COLLECTION_URLS: dict[Fuel, str] = {
    "electricity": "https://www.gov.uk/government/collections/sub-national-electricity-consumption-data",
    "gas": "https://www.gov.uk/government/collections/sub-national-gas-consumption-data",
}
"""Verified live 2026-09-29 (P2.6)."""

YEAR_SLUG_PATTERNS: dict[Fuel, re.Pattern[str]] = {
    "electricity": re.compile(
        r"/government/statistics/postcode-level-electricity-statistics-(\d{4})"
    ),
    "gas": re.compile(r"/government/statistics/postcode-level-gas-statistics-(\d{4})"),
}
"""Only matches the modern, non-"experimental" yearly slug (2022 onward,
verified live) -- earlier years used a differently-worded
"...-experimental" slug that this module doesn't need."""

FILENAME_PATTERNS: dict[Fuel, re.Pattern[str]] = {
    "electricity": re.compile(r"Postcode_level_all_meters_electricity_\d{4}\.csv$"),
    "gas": re.compile(r"Postcode_level_gas_\d{4}\.csv$"),
}

ASSET_LINK_PATTERN = re.compile(
    r'href="(https://assets\.publishing\.service\.gov\.uk/media/[^"]+\.csv)"'
)


class DesnzDiscoveryError(RuntimeError):
    """Raised when a GOV.UK page doesn't contain what was expected --
    never guessed, so a page layout/URL change surfaces loudly."""


def find_latest_year(collection_page_html: str, fuel: Fuel) -> int:
    """Find the most recent year with a postcode-level statistics page
    listed on the collection page's HTML. Pure function -- tested against
    a committed fixture, not fetched live (development-plan.md §5.1)."""
    years = {int(m.group(1)) for m in YEAR_SLUG_PATTERNS[fuel].finditer(collection_page_html)}
    if not years:
        raise DesnzDiscoveryError(
            f"No postcode-level-{fuel}-statistics-YYYY page found on the collection page"
        )
    return max(years)


def discover_download_url(landing_page_html: str, filename_pattern: re.Pattern[str]) -> str:
    """Find the current `.csv` asset URL on a GOV.UK statistics landing
    page's HTML, matching `filename_pattern`. Pure function, same pattern
    as fetch.desnz_lsoa_energy.discover_download_url."""
    for match in ASSET_LINK_PATTERN.finditer(landing_page_html):
        url = match.group(1)
        if filename_pattern.search(url):
            return url
    raise DesnzDiscoveryError(
        f"No .csv link matching {filename_pattern.pattern!r} found on the landing page"
    )


def fetch_latest_year(fuel: Fuel) -> int:
    """Live: fetch the collection page and find the latest year."""
    response = requests.get(COLLECTION_URLS[fuel], timeout=30)
    response.raise_for_status()
    return find_latest_year(response.text, fuel)


def fetch_current_download_url(fuel: Fuel, year: int) -> str:
    """Live: fetch a specific year's landing page and discover its
    current download link."""
    landing_url = (
        f"https://www.gov.uk/government/statistics/postcode-level-{fuel}-statistics-{year}"
    )
    response = requests.get(landing_url, timeout=30)
    response.raise_for_status()
    return discover_download_url(response.text, FILENAME_PATTERNS[fuel])


@dataclass(frozen=True)
class PostcodeEnergyRecord:
    """One postcode's (or postcode district's "All postcodes" rollup)
    domestic consumption for one year and fuel."""

    fuel: Fuel
    year: int
    outcode: str
    postcode: str
    """The literal postcode, or "All postcodes" for the outcode-level
    rollup row DESNZ includes for each outcode."""
    is_outcode_total: bool
    number_of_meters: int
    total_consumption_kwh: float
    mean_consumption_kwh: float
    median_consumption_kwh: float


def parse_postcode_csv(
    csv_text: str, year: int, fuel: Fuel, outcodes: set[str] | None = None
) -> list[PostcodeEnergyRecord]:
    """Parse a postcode-level CSV (as raw text, exactly as downloaded --
    real columns verified live 2026-09-29: Outcode, Postcode, Num_meters,
    Total_cons_kwh, Mean_cons_kwh, Median_cons_kwh), optionally filtered to
    `outcodes` (e.g. {"OX10"}).

    Pure function -- tested against a real trimmed fixture.
    """
    reader = csv.DictReader(StringIO(csv_text))
    records = []
    for row in reader:
        outcode = row["Outcode"]
        if outcodes is not None and outcode not in outcodes:
            continue
        postcode = row["Postcode"]
        records.append(
            PostcodeEnergyRecord(
                fuel=fuel,
                year=year,
                outcode=outcode,
                postcode=postcode,
                is_outcode_total=(postcode == "All postcodes"),
                number_of_meters=int(row["Num_meters"]),
                total_consumption_kwh=float(row["Total_cons_kwh"]),
                mean_consumption_kwh=float(row["Mean_cons_kwh"]),
                median_consumption_kwh=float(row["Median_cons_kwh"]),
            )
        )
    return records


def fetch_postcode_energy(
    fuel: Fuel, outcodes: set[str], *, year: int | None = None
) -> list[PostcodeEnergyRecord]:
    """Full live fetch: find the latest year (unless `year` is given),
    discover that year's download URL, fetch it (via
    fetch.http.fetch_file), and parse rows for the requested outcodes.
    Validates the result against `contracts.SOURCE_CONTRACTS` before
    returning (development-plan.md P2.10).

    The manifest `source_id` is `desnz_postcode_energy/<fuel>` -- nested
    under the registry id (`config/sources.yaml`'s `desnz_postcode_energy`
    entry) with a separate manifest history per fuel.
    """
    manifest_source_id = f"desnz_postcode_energy/{fuel}"
    resolved_year = year if year is not None else fetch_latest_year(fuel)
    # A row-count baseline is only valid for the SAME outcodes/year --
    # fetching one outcode then several is a different query, not a real
    # change in the data (cycle-2 review finding).
    query_signature = f"outcodes={sorted(outcodes)}:year={resolved_year}"
    download_url = fetch_current_download_url(fuel, resolved_year)
    previous_count = previous_row_count(manifest_source_id, query_signature)
    result = fetch_file(
        manifest_source_id,
        download_url,
        dest_filename=f"postcode_{fuel}_{resolved_year}.csv",
    )
    if result.file_path is None:
        raise RuntimeError(f"fetch_file returned no file_path for {manifest_source_id}")
    csv_text = result.file_path.read_text(encoding="utf-8")
    records = parse_postcode_csv(csv_text, resolved_year, fuel, outcodes)
    contract = SOURCE_CONTRACTS["desnz_postcode_energy"]
    validate_schema(records, contract)
    validate_row_count(contract, len(records), previous_count)
    record_row_count(manifest_source_id, len(records), query_signature)
    return records
