"""Contract tests (development-plan.md Phase 4): the JSON the web site
consumes must validate against the pipeline schema and not drift from
its sources (ADR-0013). Reads the committed `web/src/data/*.json`."""

from __future__ import annotations

import json

import pandas as pd

from cholsey_pipeline.export import build_metric_config_json
from cholsey_pipeline.registry import (
    REPO_ROOT,
    load_geography,
    load_metrics,
    load_sources,
    load_tile_groups,
)
from cholsey_pipeline.validate.metrics_schema import (
    METRICS_CSV_SCHEMA,
    validate_registry_references,
)

DATA = REPO_ROOT / "web" / "src" / "data"


def _load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def test_metrics_json_validates_against_pipeline_schema():
    grouped = _load("metrics.json")
    rows = [row for rows in grouped.values() for row in rows]
    df = pd.DataFrame(rows, columns=list(METRICS_CSV_SCHEMA.columns.keys()))
    METRICS_CSV_SCHEMA.validate(df)
    for metric_id, metric_rows in grouped.items():
        assert {r["metric_id"] for r in metric_rows} == {metric_id}


def test_metrics_json_references_resolve_in_registries():
    grouped = _load("metrics.json")
    df = pd.DataFrame([r for rows in grouped.values() for r in rows])
    validate_registry_references(df, load_metrics(), load_geography(), load_sources())


def test_sources_json_covers_every_cited_source():
    cited = {r["source_id"] for rows in _load("metrics.json").values() for r in rows}
    assert cited <= set(_load("sources.json"))


def test_areas_json_matches_geography_config():
    assert _load("areas.json") == load_geography()


def test_metric_config_json_is_not_stale():
    expected = build_metric_config_json(load_metrics(), load_tile_groups())
    assert _load("metric_config.json") == expected, (
        "web/src/data/metric_config.json is stale: run "
        "`cd pipeline && uv run python scripts/build_metric_config.py`"
    )


def test_every_tile_metric_has_data():
    grouped = _load("metrics.json")
    for tile in _load("metric_config.json")["tiles"]:
        for metric_id in tile["metrics"]:
            assert grouped.get(metric_id), f"no rows for {metric_id}"
