"""Assemble `data/processed/metrics.csv` and `data/processed/README.md`
from already-computed metric rows (development-plan.md Phase 3, P3.9).

See ADR-0010 for the full design rationale. In short: none of the
`metrics/*.py` modules' row dataclasses (`CanopyMetricRow`,
`GreenspaceMetricRow`, `EnergyMetricRow`, `UptakeMetricRow`) carry the six
provenance columns `validate.metrics_schema.METRICS_CSV_SCHEMA` requires
(`source_id`, `source_name`, `source_publisher`, `source_url`,
`retrieved_at`, `raw_sha256`) -- those functions are deliberately pure,
with no config/manifest I/O of their own. Instead, `build_metrics_row`
takes an already-computed row plus the provenance of the specific live
fetch that produced it (known to whichever script orchestrates
"fetch -> compute -> assemble", right after that fetch returns, not
re-discovered from a manifest file afterwards) and the already-loaded
`sources.yaml` registry, and returns one flat dict with exactly the
columns `METRICS_CSV_SCHEMA` expects (it's `strict=True`, so a row's
module-specific extra fields -- `accessible_area_m2`, `total_mwh`,
`estimated_installations`, `pct_of_parish_area` -- are deliberately left
out here, not column errors).

**Not yet built**: the actual top-level script that re-runs every live
fetch for every area/metric and calls `build_metrics_row` for each real
result -- see ADR-0010's *Consequences* and STATUS.md for why that's a
separate, larger task.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

import pandas as pd

from cholsey_pipeline.validate.metrics_schema import METRICS_CSV_SCHEMA


class MetricRow(Protocol):
    """The fields every `metrics/*.py` row dataclass shares -- enough for
    `build_metrics_row` to read generically, whichever of the four
    concrete types (or a future one) it's given. Checked structurally
    (`Protocol`), not by inheritance, since the existing dataclasses
    don't share a base class and shouldn't need to change to gain one."""

    area_code: str
    area_name: str
    area_role: str
    metric_id: str
    year: int
    value: float
    unit: str
    geography_used: str
    method: str
    flag: str
    flag_note: str


class ExportError(ValueError):
    """Raised when a row can't be exported -- an unknown `source_id`, or
    a provenance value that's empty/None (CLAUDE.md: a value without
    provenance is a bug, so this fails loudly rather than writing a null
    into metrics.csv for pandera to catch later)."""


def build_metrics_row(
    row: MetricRow,
    *,
    source_id: str,
    retrieved_at: str,
    raw_sha256: str,
    sources: dict[str, dict],
) -> dict[str, Any]:
    """Turn one already-computed metric row into a flat dict with exactly
    `METRICS_CSV_SCHEMA`'s columns. `source_id` must be a real key in the
    already-loaded `sources` registry (`registry.load_sources`'s return
    value) -- `source_name`/`source_publisher`/`source_url` are looked up
    from there (`source_url` uses the source's own `url` field: the
    dataset's public page, not its machine query endpoint, so a reader
    following the link lands somewhere meaningful). `retrieved_at` and
    `raw_sha256` are the specific live fetch's own values (a
    `fetch.http.FetchResult`'s `retrieved_at`/`sha256`, or the equivalent
    fields from a manifest `geography.boundaries.fetch_boundary`-style
    multi-page fetcher just wrote) -- see ADR-0010 for why these aren't
    re-derived here from a manifest lookup.

    Pure function, no I/O -- tested against fixtures, no network or real
    config files needed (development-plan.md §5.1).
    """
    if source_id not in sources:
        raise ExportError(f"Unknown source_id '{source_id}' -- not in sources.yaml")
    source = sources[source_id]
    if not retrieved_at:
        raise ExportError(f"retrieved_at is empty for source_id '{source_id}'")
    if not raw_sha256:
        raise ExportError(f"raw_sha256 is empty for source_id '{source_id}'")

    return {
        "area_code": row.area_code,
        "area_name": row.area_name,
        "area_role": row.area_role,
        "metric_id": row.metric_id,
        "year": row.year,
        "value": row.value,
        "unit": row.unit,
        "source_id": source_id,
        "source_name": source["name"],
        "source_publisher": source["publisher"],
        "source_url": source["url"],
        "retrieved_at": retrieved_at,
        "raw_sha256": raw_sha256,
        "geography_used": row.geography_used,
        "method": row.method,
        "flag": row.flag,
        "flag_note": row.flag_note,
    }


def rows_to_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Assemble a batch of `build_metrics_row` dicts into the final
    `metrics.csv` DataFrame, validated against `METRICS_CSV_SCHEMA`.
    Raises whatever `pandera` raises (a `SchemaError`) on the first
    structural problem -- duplicate (area_code, metric_id, year), a bad
    enum, a missing provenance value that slipped past
    `build_metrics_row`'s own checks, etc.

    Column order matches `METRICS_CSV_SCHEMA`'s declaration order (not
    whatever order `rows` happens to carry), so the written CSV has a
    stable, predictable column order run to run.
    """
    df = pd.DataFrame(rows, columns=list(METRICS_CSV_SCHEMA.columns.keys()))
    return METRICS_CSV_SCHEMA.validate(df)


def write_metrics_csv(df: pd.DataFrame, path: Path) -> None:
    """Write the validated metrics table to `path` (normally
    `data/processed/metrics.csv`), UTF-8, no index column -- it's not a
    meaningful key, (area_code, metric_id, year) already is."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def write_readme(df: pd.DataFrame, path: Path) -> None:
    """Write a human-readable summary (development-plan.md P3.9: "latest
    value per metric per area") to `path` (normally
    `data/processed/README.md`) -- one markdown table per metric_id,
    latest year's row per area, for the project lead's plausibility
    review (development-plan.md Phase 3's "Manual" test of success).

    Regenerated wholesale each run, not hand-edited (CLAUDE.md: never
    hand-edit generated data) -- a comment at the top says so.
    """
    lines = [
        "# Processed metrics summary",
        "",
        "**Generated by `export.py` -- do not hand-edit.** Regenerate with "
        "`make refresh` (or re-run the export step directly); this file is "
        "overwritten every run.",
        "",
    ]
    for metric_id in sorted(df["metric_id"].unique()):
        metric_df = df[df["metric_id"] == metric_id]
        latest_year = metric_df.groupby("area_code")["year"].transform("max")
        latest = metric_df[metric_df["year"] == latest_year].sort_values("area_role")

        lines.append(f"## {metric_id}")
        lines.append("")
        lines.append("| Area | Role | Year | Value | Unit | Flag |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for _, r in latest.iterrows():
            lines.append(
                f"| {r['area_name']} | {r['area_role']} | {r['year']} | "
                f"{r['value']:g} | {r['unit']} | {r['flag']} |"
            )
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_metrics_json(df: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    """`metrics.csv`'s rows grouped by `metric_id` (development-plan.md
    §2.3: "`export.py` writes `web/src/data/metrics.json`, which is the
    same rows grouped by metric"). Every row keeps every column -- the
    front end "never computes provenance, it only displays it," so each
    row stays fully self-describing rather than trimmed down.

    Converts pandas/numpy scalar types (`numpy.int64`, `numpy.float64`)
    to plain Python `int`/`float`/`str` via `.item()`/`str()` as it goes,
    since `json.dumps` doesn't know how to serialise numpy types -- a
    real, easy-to-miss gotcha with `DataFrame.to_dict`.
    """
    result: dict[str, list[dict[str, Any]]] = {}
    for metric_id, group in df.groupby("metric_id"):
        rows = []
        for _, row in group.iterrows():
            rows.append({col: _to_json_safe(row[col]) for col in df.columns})
        result[str(metric_id)] = rows
    return result


def _to_json_safe(value: Any) -> Any:
    """Convert one pandas/numpy scalar to a plain, `json.dumps`-safe
    Python value."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def build_sources_json(df: pd.DataFrame, sources: dict[str, dict]) -> dict[str, dict]:
    """The subset of the loaded `sources.yaml` registry actually cited by
    at least one row in `df` -- not every registered source (several,
    like the stretch EPC source or the declined UKCEH alternative,
    aren't backing any real row yet), so the methodology page
    (development-plan.md P4.7, generated from this file) only describes
    datasets actually powering the dashboard."""
    used_ids = set(df["source_id"].unique())
    return {source_id: sources[source_id] for source_id in used_ids if source_id in sources}


def build_areas_json(geography: dict[str, dict]) -> dict[str, dict]:
    """The full `geography.yaml` area registry, unfiltered -- every area
    (subject/comparator/district/national) is relevant regardless of
    which metrics currently have data for it (development-plan.md §2.3:
    "`areas.json`")."""
    return geography


def write_json(data: Any, path: Path) -> None:
    """Write `data` as indented, UTF-8 JSON to `path` (normally one of
    `web/src/data/{metrics,sources,areas}.json`), creating parent
    directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
