"""Tests for cholsey_pipeline.validate.data_quality (P3.8).

Uses both small real-valued fixtures (built from values already verified
live elsewhere this phase) and, for the completeness check, the actual
committed `data/processed/metrics.csv` -- confirming the real pipeline
output is currently clean except for its one known, documented gap
(Aldworth's canopy record, ADR-0006/P3.2), exactly matching
`config/dq_exceptions.yaml`.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from cholsey_pipeline.registry import REPO_ROOT, RegistryError
from cholsey_pipeline.validate.data_quality import (
    DQ_EXCEPTIONS_PATH,
    DqException,
    build_completeness_matrix,
    check_completeness,
    load_dq_exceptions,
    validate_ranges,
    validate_yoy_change,
)

METRICS_CSV_PATH = REPO_ROOT / "data" / "processed" / "metrics.csv"

CANOPY_METRIC = {"valid_range": [0, 100], "max_yoy_change_pct": 20}
ENERGY_METRIC = {"valid_range": [1000, 10000], "max_yoy_change_pct": 15}


def _row(area_code: str, metric_id: str, year: int, value: float) -> dict:
    return {"area_code": area_code, "metric_id": metric_id, "year": year, "value": value}


class TestValidateRanges:
    def test_real_cholsey_canopy_value_is_in_range(self) -> None:
        """Cholsey's real canopy figure, 10.4%, live-verified this phase."""
        df = pd.DataFrame([_row("E04012474", "canopy", 2021, 10.4)])
        assert validate_ranges(df, {"canopy": CANOPY_METRIC}) == []

    def test_out_of_range_value_is_reported(self) -> None:
        df = pd.DataFrame([_row("E04012474", "canopy", 2021, 150.0)])
        violations = validate_ranges(df, {"canopy": CANOPY_METRIC})
        assert len(violations) == 1
        assert "150.0" in violations[0]
        assert "E04012474/canopy/2021" in violations[0]

    def test_metric_with_no_valid_range_is_skipped(self) -> None:
        df = pd.DataFrame([_row("E04012474", "mystery_metric", 2021, -999.0)])
        assert validate_ranges(df, {"mystery_metric": {}}) == []

    def test_real_metrics_csv_passes_range_checks(self) -> None:
        """The actual committed metrics.csv, against the real metrics.yaml
        valid_range config -- every real value built so far should be
        plausible by construction (percentages/kWh within their real
        physical ranges)."""
        from cholsey_pipeline.registry import load_metrics

        df = pd.read_csv(METRICS_CSV_PATH)
        metrics = load_metrics()
        assert validate_ranges(df, metrics) == []


class TestValidateYoyChange:
    def test_small_change_passes(self) -> None:
        df = pd.DataFrame(
            [
                _row("E04012474", "electricity", 2023, 3588.4),
                _row("E04012474", "electricity", 2024, 3682.27),
            ]
        )
        assert validate_yoy_change(df, {"electricity": ENERGY_METRIC}) == []

    def test_large_change_is_reported(self) -> None:
        df = pd.DataFrame(
            [
                _row("E04012474", "electricity", 2023, 3000.0),
                _row("E04012474", "electricity", 2024, 6000.0),
            ]
        )
        violations = validate_yoy_change(df, {"electricity": ENERGY_METRIC})
        assert len(violations) == 1
        assert "100.0%" in violations[0]

    def test_large_change_excused_by_matching_exception(self) -> None:
        df = pd.DataFrame(
            [
                _row("E04012474", "electricity", 2023, 3000.0),
                _row("E04012474", "electricity", 2024, 6000.0),
            ]
        )
        exceptions = [
            DqException(
                metric_id="electricity",
                area_code="E04012474",
                year=2024,
                reason="test",
                added_by="test",
                date="2026-10-02",
            )
        ]
        assert validate_yoy_change(df, {"electricity": ENERGY_METRIC}, exceptions) == []

    def test_non_adjacent_years_use_the_previous_present_year_not_year_minus_one(self) -> None:
        """A gap year (e.g. 2022 missing) should compare 2021->2023
        directly, not treat the gap as some separate case."""
        df = pd.DataFrame(
            [
                _row("E04012474", "electricity", 2021, 3500.0),
                _row("E04012474", "electricity", 2023, 3600.0),
            ]
        )
        assert validate_yoy_change(df, {"electricity": ENERGY_METRIC}) == []

    def test_metric_with_no_max_yoy_is_skipped(self) -> None:
        df = pd.DataFrame(
            [
                _row("E04012474", "mystery_metric", 2023, 1.0),
                _row("E04012474", "mystery_metric", 2024, 1000.0),
            ]
        )
        assert validate_yoy_change(df, {"mystery_metric": {}}) == []


class TestCompletenessMatrix:
    def test_matrix_shape_and_values(self) -> None:
        df = pd.DataFrame(
            [
                _row("E04012474", "canopy", 2021, 10.4),
                _row("E04012474", "greenspace", 2021, 20.23),
            ]
        )
        matrix = build_completeness_matrix(df, ["canopy", "greenspace"], ["E04012474", "E04001147"])
        assert matrix.loc["E04012474", "canopy"]
        assert matrix.loc["E04012474", "greenspace"]
        assert not matrix.loc["E04001147", "canopy"]
        assert not matrix.loc["E04001147", "greenspace"]


class TestCheckCompleteness:
    def test_missing_row_with_no_exception_is_a_gap(self) -> None:
        df = pd.DataFrame([_row("E04012474", "canopy", 2021, 10.4)])
        gaps = check_completeness(df, ["canopy"], ["E04012474", "E04001147"])
        assert len(gaps) == 1
        assert "E04001147/canopy" in gaps[0]

    def test_missing_row_excused_by_exception_is_not_a_gap(self) -> None:
        df = pd.DataFrame([_row("E04012474", "canopy", 2021, 10.4)])
        exceptions = [
            DqException(
                metric_id="canopy",
                area_code="E04001147",
                reason="real gap",
                added_by="agent",
                date="2026-09-30",
            )
        ]
        gaps = check_completeness(df, ["canopy"], ["E04012474", "E04001147"], exceptions)
        assert gaps == []

    def test_real_metrics_csv_has_exactly_the_documented_aldworth_gap(self) -> None:
        """The real, committed metrics.csv should have no undocumented
        completeness gaps across the four metrics built so far (canopy,
        greenspace, electricity, gas) -- only Aldworth's real,
        dq_exceptions.yaml-documented canopy gap."""
        from cholsey_pipeline.registry import load_geography

        df = pd.read_csv(METRICS_CSV_PATH)
        geography = load_geography()
        area_codes = list(geography.keys())
        built_metric_ids = ["canopy", "greenspace", "electricity", "gas"]
        exceptions = load_dq_exceptions()

        gaps = check_completeness(df, built_metric_ids, area_codes, exceptions)
        assert gaps == []

    def test_real_metrics_csv_without_exceptions_shows_the_aldworth_gap(self) -> None:
        """Confirms the exceptions list is doing real work above -- without
        it, Aldworth's real canopy gap should show up as a violation."""
        from cholsey_pipeline.registry import load_geography

        df = pd.read_csv(METRICS_CSV_PATH)
        geography = load_geography()
        area_codes = list(geography.keys())
        built_metric_ids = ["canopy", "greenspace", "electricity", "gas"]

        gaps = check_completeness(df, built_metric_ids, area_codes, exceptions=None)
        assert len(gaps) == 1
        assert "E04001147/canopy" in gaps[0]


class TestLoadDqExceptions:
    def test_loads_the_real_committed_file(self) -> None:
        exceptions = load_dq_exceptions()
        assert len(exceptions) >= 1
        aldworth = next(e for e in exceptions if e.area_code == "E04001147")
        assert aldworth.metric_id == "canopy"
        assert aldworth.year is None
        assert aldworth.added_by
        assert aldworth.date

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(RegistryError, match="not found"):
            load_dq_exceptions(tmp_path / "does_not_exist.yaml")

    def test_raises_on_entry_missing_required_field(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "dq_exceptions.yaml"
        bad_file.write_text(
            "exceptions:\n  - metric_id: canopy\n    area_code: E04001147\n", encoding="utf-8"
        )
        with pytest.raises(RegistryError, match="missing required field"):
            load_dq_exceptions(bad_file)

    def test_real_file_path_constant_points_at_config_dir(self) -> None:
        assert DQ_EXCEPTIONS_PATH.name == "dq_exceptions.yaml"
        assert DQ_EXCEPTIONS_PATH.exists()
