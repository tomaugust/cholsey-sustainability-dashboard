"""Load MCS Data Dashboard reference data (development-plan.md Phase 2,
P2.7; ADR-0007, Q-011).

Unlike every other `fetch/*` module, there is no live HTTP call here.
Real investigation (ADR-0007, 2026-09-30) confirmed the public MCS Data
Dashboard has no self-service bulk/postcode download API -- only
per-chart CSV exports filtered to whatever geography the dashboard UI's
user selects. Tom manually selected South Oxfordshire (the district
Cholsey sits in) and downloaded each chart's export; those CSVs are
committed as reference data (`fetch/reference_data/mcs_installations/`,
see that directory's `_provenance.json`), the same "small, hand-verified,
not re-fetchable via a simple API" pattern `geography/reference_data/`
already established for the OA lookups.

This module's job is parsing those committed CSVs into typed records --
tested against real, committed data, no network involved.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Technology = Literal["heat_pump", "solar_pv"]

REFERENCE_DATA_DIR = Path(__file__).resolve().parent / "reference_data" / "mcs_installations"


@dataclass(frozen=True)
class AreaUptakeRecord:
    """One area's cumulative MCS-certified installation total and
    household uptake rate, as of the dashboard's retrieval date."""

    technology: Technology
    area_name: str
    installations_total: int
    pct_of_households: float
    """Parsed from the dashboard's own '%of Households with
    Installations' column (e.g. "2.73%" -> 2.73), not recomputed --
    MCS's own household denominator, not this project's."""


@dataclass(frozen=True)
class YearlyTimelineRecord:
    """One year's MCS-certified installation count for an area/technology."""

    technology: Technology
    year: int
    installations_total: int


def _tech_dir(technology: Technology) -> Path:
    return REFERENCE_DATA_DIR / "south_oxfordshire" / technology


def parse_area_uptake_csv(csv_text: str, technology: Technology) -> AreaUptakeRecord:
    """Parse an `installation_uptake.csv` (one row: Local Authority,
    MCS Certified Installations Total, % of Households with Installations).
    Real column order verified against the committed South Oxfordshire
    files for both technologies, 2026-09-30."""
    reader = csv.DictReader(csv_text.splitlines())
    rows = list(reader)
    if len(rows) != 1:
        raise ValueError(f"expected exactly 1 area row in installation_uptake.csv, got {len(rows)}")
    row = rows[0]
    pct_text = row["% of Households with Installations"].strip().rstrip("%")
    return AreaUptakeRecord(
        technology=technology,
        area_name=row["Local Authority"].strip(),
        installations_total=int(row["MCS Certified Installations Total"]),
        pct_of_households=float(pct_text),
    )


def parse_yearly_timeline_csv(csv_text: str, technology: Technology) -> list[YearlyTimelineRecord]:
    """Parse a `yearly_installation_timeline.csv` (Year, MCS Certified
    Installations Total, Percentage Change) into one record per year."""
    reader = csv.DictReader(csv_text.splitlines())
    return [
        YearlyTimelineRecord(
            technology=technology,
            year=int(row["Year"]),
            installations_total=int(row["MCS Certified Installations Total"]),
        )
        for row in reader
        if row["Year"]
    ]


def load_area_uptake(technology: Technology) -> AreaUptakeRecord:
    """Load South Oxfordshire's committed MCS uptake record for `technology`."""
    path = _tech_dir(technology) / "installation_uptake.csv"
    return parse_area_uptake_csv(path.read_text(encoding="utf-8"), technology)


def load_yearly_timeline(technology: Technology) -> list[YearlyTimelineRecord]:
    """Load South Oxfordshire's committed yearly MCS installation timeline
    for `technology`."""
    path = _tech_dir(technology) / "yearly_installation_timeline.csv"
    return parse_yearly_timeline_csv(path.read_text(encoding="utf-8"), technology)
