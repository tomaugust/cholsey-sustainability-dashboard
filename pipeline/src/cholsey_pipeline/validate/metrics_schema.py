"""Schema for `data/processed/metrics.csv`, the canonical data model
(development-plan.md Phase 3, P3.1; schema defined in §2.3).

One row per (area_code, metric_id, year). Every non-value column is
provenance and must never be null (§2.3's own rule, enforced here rather
than just documented) -- a value without provenance is a bug (CLAUDE.md).

Two layers of validation, since a pandera column schema can't see outside
the DataFrame it's given:

1. `METRICS_CSV_SCHEMA` -- structural: types, enums (`area_role`, `method`,
   `flag`), ranges, no nulls in provenance columns, `flag_note` required
   exactly when `flag != "none"`, and (area_code, metric_id, year)
   uniqueness. Self-contained, no config files needed.
2. `validate_registry_references` -- referential: every `metric_id` is a
   real key in `config/metrics.yaml`, every `area_code` in
   `config/geography.yaml`, every `source_id` in `config/sources.yaml`
   (P3.1's own "tests of success" wording). Takes the already-loaded
   registries so tests can pass small fixtures instead of the real repo
   config.
"""

from __future__ import annotations

import pandas as pd
from pandera.pandas import Check, Column, DataFrameSchema

AREA_ROLES = {"subject", "comparator", "district", "national"}
METHODS = {"direct", "area_weighted", "address_weighted", "postcode_sum", "clip"}
FLAGS = {"none", "parish_estimate", "suppression_fallback", "partial_coverage"}

PROVENANCE_COLUMNS = (
    "source_id",
    "source_name",
    "source_publisher",
    "source_url",
    "retrieved_at",
    "raw_sha256",
    "geography_used",
    "method",
)
"""Every column §2.3 calls provenance -- "no provenance column may be
null" is a schema-level rule, checked below via `nullable=False` on each."""


def _flag_note_matches_flag(df: pd.DataFrame) -> pd.Series:
    """`flag_note` must be null when `flag == "none"` (nothing to explain)
    and non-empty otherwise (§2.3: "flag_note: Plain English, shown in
    tooltip" -- a non-`none` flag with no explanation is exactly the kind
    of silent gap CLAUDE.md's provenance rule forbids)."""
    has_note = df["flag_note"].notna() & (df["flag_note"].str.strip() != "")
    is_none_flag = df["flag"] == "none"
    return has_note != is_none_flag


METRICS_CSV_SCHEMA = DataFrameSchema(
    {
        "area_code": Column(str, nullable=False),
        "area_name": Column(str, nullable=False),
        "area_role": Column(str, Check.isin(AREA_ROLES), nullable=False),
        "metric_id": Column(str, nullable=False),
        "year": Column(int, Check.in_range(1900, 2100), nullable=False),
        "value": Column(float, nullable=False),
        "unit": Column(str, nullable=False),
        "source_id": Column(str, nullable=False),
        "source_name": Column(str, nullable=False),
        "source_publisher": Column(str, nullable=False),
        "source_url": Column(str, Check.str_startswith("http"), nullable=False),
        "retrieved_at": Column(str, nullable=False),
        "raw_sha256": Column(str, Check.str_length(min_value=64, max_value=64), nullable=False),
        "geography_used": Column(str, nullable=False),
        "method": Column(str, Check.isin(METHODS), nullable=False),
        "flag": Column(str, Check.isin(FLAGS), nullable=False),
        "flag_note": Column(str, nullable=True),
    },
    checks=[
        Check(
            lambda df: ~df.duplicated(subset=["area_code", "metric_id", "year"]),
            error="duplicate (area_code, metric_id, year) -- exactly one row per "
            "area/metric/year is required",
        ),
        Check(
            _flag_note_matches_flag,
            error="flag_note must be present when flag != 'none', and absent when flag == 'none'",
        ),
    ],
    strict=True,
    coerce=True,
)


class RegistryReferenceError(ValueError):
    """Raised when metrics.csv references a metric_id/area_code/source_id
    that doesn't exist in the corresponding config/*.yaml registry."""


def validate_registry_references(
    df: pd.DataFrame,
    metrics: dict[str, dict],
    geography: dict[str, dict],
    sources: dict[str, dict],
) -> None:
    """Check every `metric_id`/`area_code`/`source_id` in `df` is a real
    key in the loaded `metrics.yaml`/`geography.yaml`/`sources.yaml`
    registries (P3.1's own "tests of success"). Raises
    `RegistryReferenceError` naming every unknown value found, not just
    the first, so a single run surfaces the whole problem."""
    problems: list[str] = []

    unknown_metrics = sorted(set(df["metric_id"]) - set(metrics))
    if unknown_metrics:
        problems.append(f"metric_id(s) not in metrics.yaml: {unknown_metrics}")

    unknown_areas = sorted(set(df["area_code"]) - set(geography))
    if unknown_areas:
        problems.append(f"area_code(s) not in geography.yaml: {unknown_areas}")

    unknown_sources = sorted(set(df["source_id"]) - set(sources))
    if unknown_sources:
        problems.append(f"source_id(s) not in sources.yaml: {unknown_sources}")

    if problems:
        raise RegistryReferenceError("; ".join(problems))


def validate_metrics_table(
    df: pd.DataFrame,
    metrics: dict[str, dict],
    geography: dict[str, dict],
    sources: dict[str, dict],
) -> pd.DataFrame:
    """Full P3.1 validation: structural schema, then registry references.
    Returns the (possibly type-coerced) validated DataFrame, matching
    pandera's own `schema.validate()` return convention."""
    validated = METRICS_CSV_SCHEMA.validate(df)
    validate_registry_references(validated, metrics, geography, sources)
    return validated
