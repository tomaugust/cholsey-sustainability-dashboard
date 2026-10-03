"""Tests for cholsey_pipeline.validate.metrics_schema (P3.1).

Uses real values already verified live in Phase 2 (Cholsey's LSOA
E01028619 electricity figures, P2.5 worklog: 795 meters, 2,852,776.90 kWh
total -> mean 3588.40 kWh/meter) rather than synthetic numbers, per
development-plan.md §5.1's "real, trimmed fixtures" preference.
"""

from __future__ import annotations

import pandas as pd
import pytest
from pandera.errors import SchemaError

from cholsey_pipeline.validate.metrics_schema import (
    METRICS_CSV_SCHEMA,
    RegistryReferenceError,
    validate_metrics_table,
    validate_registry_references,
)

CHOLSEY = "E04012474"
SOUTH_OXON = "E07000179"


def _real_row(**overrides: object) -> dict:
    """One real, valid metrics.csv row (Cholsey electricity, 2023)."""
    row = {
        "area_code": CHOLSEY,
        "area_name": "Cholsey",
        "area_role": "subject",
        "metric_id": "electricity",
        "year": 2023,
        "value": 3588.398614646338,
        "unit": "kWh/meter/year",
        "source_id": "desnz_lsoa_energy",
        "source_name": "Sub-national electricity and gas consumption (LSOA/MSOA)",
        "source_publisher": "DESNZ",
        "source_url": "https://www.gov.uk/government/statistics/lower-and-middle-super-output-areas-electricity-consumption",
        "retrieved_at": "2026-09-29",
        "raw_sha256": "a" * 64,
        "geography_used": "LSOA E01028619 (0.79), E01035751 (0.15), E01035752 (0.06)",
        "method": "address_weighted",
        "flag": "none",
        "flag_note": None,
    }
    row.update(overrides)
    return row


def _df(*rows: dict) -> pd.DataFrame:
    return pd.DataFrame(list(rows))


class TestMetricsCsvSchemaValid:
    def test_real_row_passes(self) -> None:
        METRICS_CSV_SCHEMA.validate(_df(_real_row()))

    def test_flagged_row_with_note_passes(self) -> None:
        row = _real_row(
            flag="parish_estimate",
            flag_note="3 postcodes suppressed; LSOA estimate used",
        )
        METRICS_CSV_SCHEMA.validate(_df(row))


class TestMetricsCsvSchemaProvenanceNulls:
    @pytest.mark.parametrize(
        "column",
        [
            "source_id",
            "source_name",
            "source_publisher",
            "source_url",
            "retrieved_at",
            "raw_sha256",
            "geography_used",
            "method",
        ],
    )
    def test_null_provenance_column_fails(self, column: str) -> None:
        row = _real_row(**{column: None})
        with pytest.raises(SchemaError):
            METRICS_CSV_SCHEMA.validate(_df(row))


class TestMetricsCsvSchemaEnums:
    def test_bad_area_role_fails(self) -> None:
        with pytest.raises(SchemaError):
            METRICS_CSV_SCHEMA.validate(_df(_real_row(area_role="parish")))

    def test_bad_method_fails(self) -> None:
        with pytest.raises(SchemaError):
            METRICS_CSV_SCHEMA.validate(_df(_real_row(method="guessed")))

    def test_bad_flag_fails(self) -> None:
        with pytest.raises(SchemaError):
            METRICS_CSV_SCHEMA.validate(_df(_real_row(flag="unknown")))


class TestMetricsCsvSchemaFlagNoteConsistency:
    def test_flag_none_with_a_note_fails(self) -> None:
        """A note attached to an unflagged row is misleading -- the UI
        would have nothing to show a tooltip for, but the note implies
        there's something the user should know."""
        row = _real_row(flag="none", flag_note="this shouldn't be here")
        with pytest.raises(SchemaError):
            METRICS_CSV_SCHEMA.validate(_df(row))

    def test_flagged_row_without_a_note_fails(self) -> None:
        row = _real_row(flag="suppression_fallback", flag_note=None)
        with pytest.raises(SchemaError):
            METRICS_CSV_SCHEMA.validate(_df(row))


class TestMetricsCsvSchemaUniqueness:
    def test_duplicate_area_metric_year_fails(self) -> None:
        with pytest.raises(SchemaError):
            METRICS_CSV_SCHEMA.validate(_df(_real_row(), _real_row(value=9999.0)))

    def test_same_area_metric_different_year_passes(self) -> None:
        METRICS_CSV_SCHEMA.validate(_df(_real_row(), _real_row(year=2022, value=3400.0)))


class TestMetricsCsvSchemaValueRanges:
    def test_year_out_of_range_fails(self) -> None:
        with pytest.raises(SchemaError):
            METRICS_CSV_SCHEMA.validate(_df(_real_row(year=1066)))

    def test_bad_sha256_length_fails(self) -> None:
        with pytest.raises(SchemaError):
            METRICS_CSV_SCHEMA.validate(_df(_real_row(raw_sha256="tooshort")))

    def test_non_url_source_url_fails(self) -> None:
        with pytest.raises(SchemaError):
            METRICS_CSV_SCHEMA.validate(_df(_real_row(source_url="not-a-url")))


class TestValidateRegistryReferences:
    REAL_METRICS = {"electricity": {}, "gas": {}}
    REAL_GEOGRAPHY = {CHOLSEY: {}, SOUTH_OXON: {}}
    REAL_SOURCES = {"desnz_lsoa_energy": {}}

    def test_real_references_pass(self) -> None:
        validate_registry_references(
            _df(_real_row()), self.REAL_METRICS, self.REAL_GEOGRAPHY, self.REAL_SOURCES
        )

    def test_unknown_metric_id_raises(self) -> None:
        row = _real_row(metric_id="not_a_real_metric")
        with pytest.raises(RegistryReferenceError, match="not_a_real_metric"):
            validate_registry_references(
                _df(row), self.REAL_METRICS, self.REAL_GEOGRAPHY, self.REAL_SOURCES
            )

    def test_unknown_area_code_raises(self) -> None:
        row = _real_row(area_code="E00000000")
        with pytest.raises(RegistryReferenceError, match="E00000000"):
            validate_registry_references(
                _df(row), self.REAL_METRICS, self.REAL_GEOGRAPHY, self.REAL_SOURCES
            )

    def test_unknown_source_id_raises(self) -> None:
        row = _real_row(source_id="not_a_real_source")
        with pytest.raises(RegistryReferenceError, match="not_a_real_source"):
            validate_registry_references(
                _df(row), self.REAL_METRICS, self.REAL_GEOGRAPHY, self.REAL_SOURCES
            )

    def test_all_problems_reported_together(self) -> None:
        row = _real_row(metric_id="bad_metric", area_code="E00000000", source_id="bad_source")
        with pytest.raises(RegistryReferenceError) as exc_info:
            validate_registry_references(
                _df(row), self.REAL_METRICS, self.REAL_GEOGRAPHY, self.REAL_SOURCES
            )
        message = str(exc_info.value)
        assert "bad_metric" in message
        assert "E00000000" in message
        assert "bad_source" in message


class TestValidateMetricsTable:
    def test_full_validation_passes_for_real_data(self) -> None:
        result = validate_metrics_table(
            _df(_real_row()),
            metrics={"electricity": {}},
            geography={CHOLSEY: {}},
            sources={"desnz_lsoa_energy": {}},
        )
        assert len(result) == 1

    def test_structural_failure_raised_before_registry_check(self) -> None:
        """A structurally invalid row shouldn't even reach the registry
        check -- fail on the more fundamental problem first."""
        row = _real_row(area_role="not_a_role", metric_id="also_not_real")
        with pytest.raises(SchemaError):
            validate_metrics_table(_df(row), metrics={}, geography={}, sources={})
