"""Data-quality rules for `data/processed/metrics.csv` (development-plan.md
§5.2, Phase 3, P3.8).

Three checks, each reading its thresholds from `config/metrics.yaml`
(§5.2: "tightening a rule is a config change with a visible diff, not a
code change") rather than hardcoding them:

1. `validate_ranges` -- every row's `value` must fall inside its metric's
   `valid_range`.
2. `validate_yoy_change` -- year-on-year change for the same (area_code,
   metric_id) must not exceed `max_yoy_change_pct`, unless a matching
   entry in `config/dq_exceptions.yaml` excuses it.
3. `check_completeness` -- every metric expected for an area (one row for
   its latest year) must exist, unless a matching `dq_exceptions.yaml`
   entry documents why it genuinely doesn't (e.g. Aldworth's real Forest
   Research canopy gap, ADR-0006/P3.2).

Reconciliation against a publisher's own aggregate (development-plan.md's
fourth §5.2 check, `reconcile_with`) is NOT built here -- see this
module's own docstring note below, and ADR-0012, for why.

All three take an already-loaded `metrics.csv` DataFrame (as
`export.rows_to_dataframe` produces) and the already-loaded
`metrics.yaml`/`dq_exceptions.yaml` registries, so they're pure functions
over data already in memory -- no file I/O of their own, easy to test
against small fixtures (development-plan.md §5.1) as well as the real
assembled table.

**Reconciliation note**: development-plan.md §3 Phase 3's own test of
success wants "district-level values computed by our pipeline match the
publisher's own district figure within 0.5%." For electricity/gas this is
automatically true by construction -- `compute_area_energy_row`
(`method=direct`) takes DESNZ's own district/national release value
directly, so there's no second, independently-computed figure to
reconcile it against. For canopy/greenspace, the real reconciliation
already happened as a one-off manual cross-check during each metric's
original district-row build (documented in their worklogs: canopy's
21-ward area sum matched the real LAD boundary area to 0.003%;
greenspace's district clip was cross-checked against its own boundary
fetch) -- not yet turned into an automated, re-runnable check here. MCS
has no committed district/national figures yet to reconcile at all
(P3.5, blocked on Tom's data request). Building a general
`reconcile_with`-driven check is left for a future P3.8 session once
there's a second real case to generalise from, rather than writing a
single-purpose check for energy alone that would just always pass by
construction.

**Q-012/ADR-0012**: development-plan.md §3's reconciliation bullet also
has a second sentence -- "summed apportioned meter counts across ALL
parishes in the district match the district total within 1%" -- that is
genuinely unsatisfiable as written, since this project only builds
apportioned rows for 9 of South Oxfordshire's 60+ constituent parishes
(ADR-0003's deliberate scope). Tom answered Q-012 (2026-10-03, option b):
drop that line as out of scope, relying on the three checks this module
already builds plus P3.10's golden-value tests for the apportionment
math itself. See ADR-0012 for the full resolution -- this is a settled
decision, not an open gap.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from cholsey_pipeline.registry import CONFIG_DIR, RegistryError

DQ_EXCEPTIONS_PATH = CONFIG_DIR / "dq_exceptions.yaml"


@dataclass(frozen=True)
class DqException:
    """One allow-list entry (development-plan.md §5.2). `year` is `None`
    for a completeness exception (excuses a missing row entirely) and set
    for a year-on-year exception (excuses one specific breach)."""

    metric_id: str
    area_code: str
    reason: str
    added_by: str
    date: str
    year: int | None = None


def load_dq_exceptions(path: Path = DQ_EXCEPTIONS_PATH) -> list[DqException]:
    """Load `config/dq_exceptions.yaml`. Returns an empty list if the file
    has no entries; raises `RegistryError` if an entry is missing a
    required field (development-plan.md §5.2: "each with reason, added_by
    and date")."""
    if not path.exists():
        raise RegistryError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    entries = data.get("exceptions", []) or []

    required_fields = ("metric_id", "area_code", "reason", "added_by", "date")
    exceptions = []
    for entry in entries:
        missing = [f for f in required_fields if f not in entry]
        if missing:
            raise RegistryError(f"dq_exceptions.yaml entry missing required field(s) {missing}")
        exceptions.append(
            DqException(
                metric_id=entry["metric_id"],
                area_code=entry["area_code"],
                reason=entry["reason"],
                added_by=entry["added_by"],
                date=str(entry["date"]),
                year=entry.get("year"),
            )
        )
    return exceptions


def validate_ranges(df: pd.DataFrame, metrics: dict[str, dict]) -> list[str]:
    """Check every row's `value` is within its `metric_id`'s
    `valid_range` (`config/metrics.yaml`). Returns a list of violation
    messages (empty if clean) -- a list, not a raise, so a caller can
    decide whether one bad row should fail a whole CI run or just be
    reported (development-plan.md doesn't say every rule is a hard CI
    stop, unlike P3.1's structural schema).

    Rows for a `metric_id` with no `valid_range` declared are skipped,
    not treated as a violation -- `valid_range` is documented as
    optional.
    """
    violations = []
    for _, row in df.iterrows():
        metric = metrics.get(row["metric_id"])
        if metric is None or "valid_range" not in metric:
            continue
        low, high = metric["valid_range"]
        if not (low <= row["value"] <= high):
            violations.append(
                f"{row['area_code']}/{row['metric_id']}/{row['year']}: value "
                f"{row['value']} outside valid_range [{low}, {high}]"
            )
    return violations


def validate_yoy_change(
    df: pd.DataFrame, metrics: dict[str, dict], exceptions: list[DqException] | None = None
) -> list[str]:
    """Check year-on-year change, per (area_code, metric_id), against
    `max_yoy_change_pct`. Compares each year to the immediately preceding
    year PRESENT in the data for that area/metric (not necessarily
    `year - 1` -- a gap year is simply not compared across, not treated
    as 0% or 100% change). A breach is excused if `exceptions` has a
    matching `DqException` with that exact `(metric_id, area_code, year)`
    (development-plan.md §5.2: "allow-list entry with a reason").

    Rows for a `metric_id` with no `max_yoy_change_pct` declared are
    skipped.
    """
    exceptions = exceptions or []
    excused = {(e.metric_id, e.area_code, e.year) for e in exceptions if e.year is not None}

    violations = []
    for (area_code, metric_id), group in df.groupby(["area_code", "metric_id"]):
        metric = metrics.get(metric_id)
        if metric is None or "max_yoy_change_pct" not in metric:
            continue
        max_pct = metric["max_yoy_change_pct"]
        ordered = group.sort_values("year")
        prev_value = None
        prev_year = None
        for _, row in ordered.iterrows():
            if prev_value is not None and prev_value != 0:
                change_pct = abs(row["value"] - prev_value) / abs(prev_value) * 100
                if change_pct > max_pct and (metric_id, area_code, row["year"]) not in excused:
                    violations.append(
                        f"{area_code}/{metric_id}: {change_pct:.1f}% change from "
                        f"{prev_year} ({prev_value}) to {row['year']} ({row['value']}), "
                        f"exceeding {max_pct}% (no allow-list entry)"
                    )
            prev_value = row["value"]
            prev_year = row["year"]
    return violations


def build_completeness_matrix(
    df: pd.DataFrame, metric_ids: list[str], area_codes: list[str]
) -> pd.DataFrame:
    """A (area_code x metric_id) boolean matrix: does this area have at
    least one row for this metric, at any year, in `df`? Printed in test
    output per development-plan.md §3 Phase 3's own wording ("a
    completeness matrix is printed in the test output")."""
    present = df.groupby(["area_code", "metric_id"]).size() > 0
    matrix = pd.DataFrame(index=area_codes, columns=metric_ids, dtype=bool)
    for area_code in area_codes:
        for metric_id in metric_ids:
            matrix.loc[area_code, metric_id] = bool(present.get((area_code, metric_id), False))
    return matrix


def check_completeness(
    df: pd.DataFrame,
    metric_ids: list[str],
    area_codes: list[str],
    exceptions: list[DqException] | None = None,
) -> list[str]:
    """Every (area_code, metric_id) pair must have at least one row,
    unless a matching completeness `DqException` (`year is None`)
    documents why it genuinely doesn't (development-plan.md §3 Phase 3:
    "every area has a latest-year value, or ... explaining its
    absence" -- here, "explaining its absence" is the committed
    `dq_exceptions.yaml` entry, since `METRICS_CSV_SCHEMA`'s `flag` enum
    has no "unavailable" value to attach to a nonexistent row).
    """
    excused = {(e.metric_id, e.area_code) for e in exceptions or [] if e.year is None}
    matrix = build_completeness_matrix(df, metric_ids, area_codes)

    gaps = []
    for area_code in area_codes:
        for metric_id in metric_ids:
            if not matrix.loc[area_code, metric_id] and (metric_id, area_code) not in excused:
                gaps.append(f"{area_code}/{metric_id}: no row and no dq_exceptions.yaml entry")
    return gaps
