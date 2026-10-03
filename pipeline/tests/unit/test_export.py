"""Tests for cholsey_pipeline.export (P3.9).

Uses real metric rows and real provenance already produced/verified this
phase -- P3.2's real national canopy row (14.41%, England) and its real
`forest_research_canopy` manifest entry (retrieved 2026-10-01, the real
`country='England'` fetch, 6,135 features) -- rather than synthetic
fixtures, per development-plan.md §5.1 where real data is already
available. No network calls: `sources` is a small, real-shaped registry
fixture, not the live `config/sources.yaml` loader, matching how
`test_metrics_schema.py`/`test_registry_real_config.py` split "real
registry shape" from "real file on disk" testing.
"""

from __future__ import annotations

import pandas as pd
import pytest

from cholsey_pipeline.export import (
    ExportError,
    build_areas_json,
    build_metrics_json,
    build_metrics_row,
    build_sources_json,
    rows_to_dataframe,
    write_json,
    write_metrics_csv,
    write_readme,
)
from cholsey_pipeline.fetch.forest_research_canopy import WardCanopyRecord
from cholsey_pipeline.metrics.canopy import compute_national_canopy_row
from cholsey_pipeline.validate.metrics_schema import METRICS_CSV_SCHEMA

REAL_ENGLAND_WARD_RECORDS = [
    WardCanopyRecord(
        ward_code="E05000170",
        ward_name="Acton Central",
        designated="Urban",
        survey_year=0,
        percent_canopy_cover=18.2,
        standard_error=0,
        number_of_points=0,
        country="England",
        ward_area_m2=1_775_371.193,
    ),
    WardCanopyRecord(
        ward_code="E05002319",
        ward_name="Abbey",
        designated="Urban",
        survey_year=2020,
        percent_canopy_cover=11.6,
        standard_error=None,
        number_of_points=None,
        country="England",
        ward_area_m2=3_172_890.99,
    ),
    WardCanopyRecord(
        ward_code="E05009737",
        ward_name="Cholsey",
        designated="Rural",
        survey_year=2021,
        percent_canopy_cover=10.4,
        standard_error=1.37,
        number_of_points=500,
        country="England",
        ward_area_m2=66_557_077.88,
    ),
]
"""Same real 3-ward subset used in test_metrics_canopy.py's
TestComputeNationalCanopyRow (not cross-imported, to keep each test
module self-contained -- see that file for provenance of these values)."""

REAL_FOREST_RESEARCH_SOURCE = {
    "forest_research_canopy": {
        "name": "UK Ward Canopy Cover",
        "publisher": "Forest Research",
        "url": "https://data-forestry.opendata.arcgis.com/datasets/ecba26cfaf9d4b61bddc0e3284348d79_0/about",
    },
}
REAL_RETRIEVED_AT = "2026-10-01T06:26:49.114046+00:00"
"""The real retrieved_at from
data/manifest/forest_research_canopy/2026-10-01T06-26-49.114046+00-00.json
-- the actual manifest entry for the England-wide fetch this row's
value comes from."""
REAL_RAW_SHA256 = "1822d6fb194adf5e213cb3003184f7d39cb798be9474d5fc7c8555b2e6abd80d"


def _real_national_canopy_row():
    return compute_national_canopy_row(REAL_ENGLAND_WARD_RECORDS, year=2020)


class TestBuildMetricsRow:
    def test_real_values_and_provenance(self) -> None:
        row = _real_national_canopy_row()
        result = build_metrics_row(
            row,
            source_id="forest_research_canopy",
            retrieved_at=REAL_RETRIEVED_AT,
            raw_sha256=REAL_RAW_SHA256,
            sources=REAL_FOREST_RESEARCH_SOURCE,
        )
        assert result["area_code"] == "E92000001"
        assert result["area_name"] == "England"
        assert result["area_role"] == "national"
        assert result["metric_id"] == "canopy"
        assert result["year"] == 2020
        assert result["value"] == pytest.approx(row.value)
        assert result["flag"] == "partial_coverage"
        assert result["source_id"] == "forest_research_canopy"
        assert result["source_name"] == "UK Ward Canopy Cover"
        assert result["source_publisher"] == "Forest Research"
        assert result["source_url"].startswith("http")
        assert result["retrieved_at"] == REAL_RETRIEVED_AT
        assert result["raw_sha256"] == REAL_RAW_SHA256

    def test_drops_module_specific_extra_fields(self) -> None:
        """CanopyMetricRow has no extra fields beyond the schema, unlike
        e.g. GreenspaceMetricRow's accessible_area_m2 -- but the dict
        returned should still be exactly METRICS_CSV_SCHEMA's columns,
        nothing more, since the schema is strict=True."""
        row = _real_national_canopy_row()
        result = build_metrics_row(
            row,
            source_id="forest_research_canopy",
            retrieved_at=REAL_RETRIEVED_AT,
            raw_sha256=REAL_RAW_SHA256,
            sources=REAL_FOREST_RESEARCH_SOURCE,
        )
        assert set(result.keys()) == set(METRICS_CSV_SCHEMA.columns.keys())

    def test_raises_on_unknown_source_id(self) -> None:
        row = _real_national_canopy_row()
        with pytest.raises(ExportError, match="Unknown source_id"):
            build_metrics_row(
                row,
                source_id="not_a_real_source",
                retrieved_at=REAL_RETRIEVED_AT,
                raw_sha256=REAL_RAW_SHA256,
                sources=REAL_FOREST_RESEARCH_SOURCE,
            )

    def test_raises_on_empty_retrieved_at(self) -> None:
        row = _real_national_canopy_row()
        with pytest.raises(ExportError, match="retrieved_at"):
            build_metrics_row(
                row,
                source_id="forest_research_canopy",
                retrieved_at="",
                raw_sha256=REAL_RAW_SHA256,
                sources=REAL_FOREST_RESEARCH_SOURCE,
            )

    def test_raises_on_empty_raw_sha256(self) -> None:
        row = _real_national_canopy_row()
        with pytest.raises(ExportError, match="raw_sha256"):
            build_metrics_row(
                row,
                source_id="forest_research_canopy",
                retrieved_at=REAL_RETRIEVED_AT,
                raw_sha256="",
                sources=REAL_FOREST_RESEARCH_SOURCE,
            )


class TestRowsToDataframe:
    def test_real_row_passes_schema_validation(self) -> None:
        row = _real_national_canopy_row()
        result = build_metrics_row(
            row,
            source_id="forest_research_canopy",
            retrieved_at=REAL_RETRIEVED_AT,
            raw_sha256=REAL_RAW_SHA256,
            sources=REAL_FOREST_RESEARCH_SOURCE,
        )
        df = rows_to_dataframe([result])
        assert len(df) == 1
        assert list(df.columns) == list(METRICS_CSV_SCHEMA.columns.keys())

    def test_duplicate_area_metric_year_rejected(self) -> None:
        row = _real_national_canopy_row()
        result = build_metrics_row(
            row,
            source_id="forest_research_canopy",
            retrieved_at=REAL_RETRIEVED_AT,
            raw_sha256=REAL_RAW_SHA256,
            sources=REAL_FOREST_RESEARCH_SOURCE,
        )
        with pytest.raises(Exception, match="duplicate"):
            rows_to_dataframe([result, dict(result)])


class TestWriteMetricsCsv:
    def test_writes_real_row_to_csv(self, tmp_path) -> None:
        row = _real_national_canopy_row()
        result = build_metrics_row(
            row,
            source_id="forest_research_canopy",
            retrieved_at=REAL_RETRIEVED_AT,
            raw_sha256=REAL_RAW_SHA256,
            sources=REAL_FOREST_RESEARCH_SOURCE,
        )
        df = rows_to_dataframe([result])
        out = tmp_path / "metrics.csv"
        write_metrics_csv(df, out)
        assert out.exists()
        read_back = pd.read_csv(out)
        assert read_back.loc[0, "area_code"] == "E92000001"
        assert read_back.loc[0, "value"] == pytest.approx(row.value)
        assert "index" not in read_back.columns


class TestWriteReadme:
    def test_writes_markdown_table_with_real_value(self, tmp_path) -> None:
        row = _real_national_canopy_row()
        result = build_metrics_row(
            row,
            source_id="forest_research_canopy",
            retrieved_at=REAL_RETRIEVED_AT,
            raw_sha256=REAL_RAW_SHA256,
            sources=REAL_FOREST_RESEARCH_SOURCE,
        )
        df = rows_to_dataframe([result])
        out = tmp_path / "README.md"
        write_readme(df, out)
        content = out.read_text(encoding="utf-8")
        assert "do not hand-edit" in content.lower()
        assert "## canopy" in content
        assert "England" in content
        assert "national" in content

    def test_shows_only_latest_year_per_area(self, tmp_path) -> None:
        """Two years of the same area/metric should collapse to one row
        in the README (the latest), not list both -- P3.9's own wording:
        'latest value per metric per area'."""
        row_2020 = _real_national_canopy_row()
        result_2020 = build_metrics_row(
            row_2020,
            source_id="forest_research_canopy",
            retrieved_at=REAL_RETRIEVED_AT,
            raw_sha256=REAL_RAW_SHA256,
            sources=REAL_FOREST_RESEARCH_SOURCE,
        )
        result_2019 = dict(result_2020)
        result_2019["year"] = 2019
        result_2019["value"] = 99.9
        df = rows_to_dataframe([result_2020, result_2019])
        out = tmp_path / "README.md"
        write_readme(df, out)
        content = out.read_text(encoding="utf-8")
        assert "99.9" not in content
        lines_with_england = [line for line in content.splitlines() if "England" in line]
        assert len(lines_with_england) == 1


class TestBuildMetricsJson:
    def test_groups_real_row_by_metric_id(self) -> None:
        row = _real_national_canopy_row()
        result = build_metrics_row(
            row,
            source_id="forest_research_canopy",
            retrieved_at=REAL_RETRIEVED_AT,
            raw_sha256=REAL_RAW_SHA256,
            sources=REAL_FOREST_RESEARCH_SOURCE,
        )
        df = rows_to_dataframe([result])
        metrics_json = build_metrics_json(df)
        assert list(metrics_json.keys()) == ["canopy"]
        assert len(metrics_json["canopy"]) == 1
        assert metrics_json["canopy"][0]["area_name"] == "England"
        assert metrics_json["canopy"][0]["value"] == pytest.approx(row.value)

    def test_values_are_plain_json_safe_types_not_numpy(self) -> None:
        """A real, easy-to-miss gotcha: DataFrame.to_dict/iterrows yield
        numpy scalar types (numpy.int64/float64), which json.dumps
        can't serialise -- every value here must already be a plain
        Python int/float/str."""
        row = _real_national_canopy_row()
        result = build_metrics_row(
            row,
            source_id="forest_research_canopy",
            retrieved_at=REAL_RETRIEVED_AT,
            raw_sha256=REAL_RAW_SHA256,
            sources=REAL_FOREST_RESEARCH_SOURCE,
        )
        df = rows_to_dataframe([result])
        metrics_json = build_metrics_json(df)
        row_out = metrics_json["canopy"][0]
        assert type(row_out["year"]) is int
        assert type(row_out["value"]) is float
        assert type(row_out["area_code"]) is str
        import json

        json.dumps(metrics_json)  # must not raise

    def test_null_flag_note_becomes_json_null_not_nan(self) -> None:
        """A flag=none row's flag_note is genuinely null in metrics.csv
        (METRICS_CSV_SCHEMA requires it) -- confirms build_metrics_json
        converts that pandas NaN to a real JSON null, not the string
        "nan" or a NaN float (which json.dumps renders as the invalid
        literal `NaN`)."""
        row = _real_national_canopy_row()
        result = build_metrics_row(
            row,
            source_id="forest_research_canopy",
            retrieved_at=REAL_RETRIEVED_AT,
            raw_sha256=REAL_RAW_SHA256,
            sources=REAL_FOREST_RESEARCH_SOURCE,
        )
        result["flag"] = "none"
        result["flag_note"] = None
        df = rows_to_dataframe([result])
        metrics_json = build_metrics_json(df)
        assert metrics_json["canopy"][0]["flag_note"] is None


class TestBuildSourcesJson:
    def test_only_cited_sources_are_included(self) -> None:
        row = _real_national_canopy_row()
        result = build_metrics_row(
            row,
            source_id="forest_research_canopy",
            retrieved_at=REAL_RETRIEVED_AT,
            raw_sha256=REAL_RAW_SHA256,
            sources=REAL_FOREST_RESEARCH_SOURCE,
        )
        df = rows_to_dataframe([result])
        all_sources = {
            **REAL_FOREST_RESEARCH_SOURCE,
            "os_open_greenspace": {"name": "x", "publisher": "y", "url": "http://z"},
        }
        sources_json = build_sources_json(df, all_sources)
        assert list(sources_json.keys()) == ["forest_research_canopy"]
        assert sources_json["forest_research_canopy"]["publisher"] == "Forest Research"


class TestBuildAreasJson:
    def test_returns_the_full_registry_unfiltered(self) -> None:
        geography = {
            "E04012474": {"name": "Cholsey", "role": "subject"},
            "E92000001": {"name": "England", "role": "national"},
        }
        assert build_areas_json(geography) == geography


class TestWriteJson:
    def test_writes_real_metrics_json_readable_back(self, tmp_path) -> None:
        row = _real_national_canopy_row()
        result = build_metrics_row(
            row,
            source_id="forest_research_canopy",
            retrieved_at=REAL_RETRIEVED_AT,
            raw_sha256=REAL_RAW_SHA256,
            sources=REAL_FOREST_RESEARCH_SOURCE,
        )
        df = rows_to_dataframe([result])
        metrics_json = build_metrics_json(df)
        out = tmp_path / "metrics.json"
        write_json(metrics_json, out)

        import json

        read_back = json.loads(out.read_text(encoding="utf-8"))
        assert read_back["canopy"][0]["area_name"] == "England"
        assert out.read_text(encoding="utf-8").endswith("\n"), (
            "web/src/data/*.json must end with a newline -- prettier --check "
            "(make lint/CI) requires one and these files aren't prettierignore'd"
        )
