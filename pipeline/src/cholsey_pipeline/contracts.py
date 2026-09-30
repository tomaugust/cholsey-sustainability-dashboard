"""Per-source schema contracts and previous-run diffing (development-plan.md
Phase 2, P2.10).

Every Phase 2 fetcher that returns tabular data does so as a list of a
frozen dataclass (one per source -- `LsoaEnergyRecord`,
`PostcodeEnergyRecord`, `WardCanopyRecord`, ...). This module declares, per
source, the fields a batch of such records must have and which field(s)
form a uniqueness key, and validates a fetched batch against that contract
-- so a government file silently renaming or dropping a column, or a key
field going null, fails loudly (spec §5) instead of corrupting the
dataset downstream. It also diffs a run's row count against the previous
run's manifest entry within a declared tolerance, so a silent 50%+ drop
(a common symptom of a broken filter or a changed upstream schema) is a
hard stop, not a quietly-smaller dataset.

Scope note: `os_open_greenspace` returns a `geopandas.GeoDataFrame`, not a
list of dataclasses (it's a different shape -- geometry plus a handful of
OS attribute columns), so it isn't covered by `validate_schema` below.
Every other Phase 2 fetcher (P2.3, P2.5, P2.6, P2.8, P2.9) is.

What this module does NOT catch: `expected_fields` checks the record
dataclass's own fields, which are fixed in code -- it only catches an
internal regression (a field renamed in the dataclass without updating
its contract), not an upstream government file quietly renaming or
reordering a column. The DESNZ parsers, which read columns by fixed
position, guard against *that* directly: `fetch.desnz_lsoa_energy`'s
`_check_header` validates the real header row's text before any row is
read by position, so an upstream column change fails loudly at the
column it affects, rather than silently shifting values into the wrong
field while this module's checks still pass.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


class ContractViolation(RuntimeError):
    """Raised when a batch of records (or a run's row count) violates its
    declared contract. Always names the source id and the offending
    field/reason, so a CI failure or refresh log is immediately
    actionable."""


@dataclass(frozen=True)
class SchemaContract:
    """The expected shape of one source's fetched records.

    `expected_fields` -- every field name the record dataclass must have
    (a missing one means a column was dropped or renamed upstream).
    `key_fields` -- the field(s) that together must be non-null and
    unique across the batch (e.g. `("lsoa_code", "year")`).
    `numeric_fields` -- fields that must hold a real `int`/`float` on
    every record, not `None` or a suppression marker like DESNZ's `".."`/
    `"c"` that slipped through parsing as a string -- a value like that
    would otherwise flow into metrics as a non-number.
    `row_count_tolerance_pct` -- how much a run's row count may change
    from the previous run before `validate_row_count` treats it as a
    hard stop.
    """

    source_id: str
    expected_fields: tuple[str, ...]
    key_fields: tuple[str, ...]
    numeric_fields: tuple[str, ...] = ()
    row_count_tolerance_pct: float = 30.0


def validate_schema(records: Sequence[Any], contract: SchemaContract) -> None:
    """Validate a batch of records against `contract`.

    Checks, in order: every `expected_fields` entry is a real field on the
    record type (a dropped or renamed column fails here); every
    `key_fields` entry is non-null on every record; the tuple of
    `key_fields` values is unique across the batch (no duplicate key);
    every `numeric_fields` entry is a real `int`/`float` (not `None`, not
    a stray suppression-marker string) on every record.

    An empty `records` batch is not itself a contract violation here --
    `validate_row_count` is what catches "this run returned far fewer
    rows than last time," including zero.
    """
    if not records:
        return

    actual_fields = {f.name for f in dataclasses.fields(records[0])}
    missing = [f for f in contract.expected_fields if f not in actual_fields]
    if missing:
        raise ContractViolation(
            f"{contract.source_id}: expected field(s) {missing} not found on "
            f"{type(records[0]).__name__} -- a column was likely dropped or renamed upstream"
        )

    seen_keys: set[tuple[Any, ...]] = set()
    for record in records:
        key = tuple(getattr(record, field) for field in contract.key_fields)
        for field, value in zip(contract.key_fields, key, strict=True):
            if value is None:
                raise ContractViolation(
                    f"{contract.source_id}: key field '{field}' is null on a record "
                    f"(key fields must never be null)"
                )
        if key in seen_keys:
            raise ContractViolation(
                f"{contract.source_id}: duplicate key {key} for key fields "
                f"{contract.key_fields} -- expected each key to be unique"
            )
        seen_keys.add(key)

        for field in contract.numeric_fields:
            value = getattr(record, field)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ContractViolation(
                    f"{contract.source_id}: numeric field '{field}' has non-numeric "
                    f"value {value!r} ({type(value).__name__}) -- a suppressed/missing "
                    "upstream value likely slipped through as a string"
                )


def validate_row_count(
    contract: SchemaContract, current_count: int, previous_count: int | None
) -> None:
    """Compare a run's row count against the previous run's. `previous_count
    of None` means there is no previous run to compare against (e.g. the
    first-ever fetch), so nothing is checked. A change (in either
    direction) exceeding `contract.row_count_tolerance_pct` is a hard
    stop -- a shrink usually means a broken filter or upstream schema
    change; a large jump can mean a filter stopped applying at all.
    """
    if previous_count is None or previous_count == 0:
        return
    change_pct = abs(current_count - previous_count) / previous_count * 100
    if change_pct > contract.row_count_tolerance_pct:
        raise ContractViolation(
            f"{contract.source_id}: row count changed by {change_pct:.1f}% "
            f"(from {previous_count} to {current_count}), exceeding the "
            f"{contract.row_count_tolerance_pct}% tolerance"
        )


# --- Declared contracts for every Phase 2 record-based source ---

SOURCE_CONTRACTS: dict[str, SchemaContract] = {
    "forest_research_canopy": SchemaContract(
        source_id="forest_research_canopy",
        expected_fields=(
            "ward_code",
            "ward_name",
            "designated",
            "survey_year",
            "percent_canopy_cover",
            "standard_error",
            "number_of_points",
        ),
        key_fields=("ward_code", "survey_year"),
        numeric_fields=("percent_canopy_cover", "standard_error", "number_of_points"),
    ),
    "desnz_lsoa_energy": SchemaContract(
        source_id="desnz_lsoa_energy",
        expected_fields=(
            "fuel",
            "year",
            "lsoa_code",
            "lsoa_name",
            "la_code",
            "la_name",
            "number_of_meters",
            "total_consumption_kwh",
        ),
        # `fuel` is in the key because `fetch_lsoa_energy` is called once
        # per fuel but a caller could still validate an electricity+gas
        # batch together; without it, the same (lsoa_code, year) from both
        # fuels would collide as a false duplicate-key violation.
        key_fields=("fuel", "lsoa_code", "year"),
        numeric_fields=("number_of_meters", "total_consumption_kwh"),
    ),
    "desnz_regional_la_energy": SchemaContract(
        source_id="desnz_regional_la_energy",
        expected_fields=(
            "fuel",
            "year",
            "area_code",
            "area_name",
            "number_of_domestic_meters_thousands",
            "total_domestic_consumption_gwh",
        ),
        key_fields=("fuel", "area_code", "year"),
        numeric_fields=(
            "number_of_domestic_meters_thousands",
            "total_domestic_consumption_gwh",
        ),
    ),
    "desnz_postcode_energy": SchemaContract(
        source_id="desnz_postcode_energy",
        expected_fields=(
            "fuel",
            "year",
            "outcode",
            "postcode",
            "is_outcode_total",
            "number_of_meters",
            "total_consumption_kwh",
            "mean_consumption_kwh",
            "median_consumption_kwh",
        ),
        # `outcode` must be in the key, not just `postcode`: every outcode
        # contributes its own "All postcodes" rollup row, so `postcode`
        # alone collides across outcodes (e.g. two "All postcodes" rows
        # when fetching more than one outcode) -- a real bug this
        # contract itself would previously false-fail on.
        key_fields=("fuel", "outcode", "postcode", "year"),
        numeric_fields=(
            "number_of_meters",
            "total_consumption_kwh",
            "mean_consumption_kwh",
            "median_consumption_kwh",
        ),
        # Postcode-level suppression (spec §3, plan risk R4) means the set
        # of reported postcodes can shift more between years than a typical
        # LSOA/LA release -- a wider tolerance avoids false-failing on that
        # expected behaviour while still catching a genuinely broken fetch.
        row_count_tolerance_pct=50.0,
    ),
    "ons_parish_population": SchemaContract(
        source_id="ons_parish_population",
        expected_fields=("vintage_year", "parish_code", "parish_name", "total_population"),
        key_fields=("parish_code", "vintage_year"),
        numeric_fields=("total_population",),
    ),
    "dluhc_epc_register": SchemaContract(
        source_id="dluhc_epc_register",
        expected_fields=(
            "certificate_number",
            "postcode",
            "council",
            "current_energy_efficiency_band",
            "registration_date",
            "uprn",
        ),
        key_fields=("certificate_number",),
    ),
}
