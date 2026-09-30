"""Tests for cholsey_pipeline.metrics.canopy (P3.2, metric 1).

Uses real values already verified live in prior phases: Cholsey ward
E05009737's real 2021 canopy figure (P2.3 fixture: 10.4%, standard error
1.37, 500 points) and the real parish-in-ward area weight ADR-0006
computed (99.4%), rather than synthetic numbers.
"""

from __future__ import annotations

from cholsey_pipeline.fetch.forest_research_canopy import WardCanopyRecord
from cholsey_pipeline.metrics.canopy import (
    CHOLSEY_PARISH_CODE,
    compute_subject_canopy_row,
)

REAL_CHOLSEY_WARD_RECORD = WardCanopyRecord(
    ward_code="E05009737",
    ward_name="Cholsey",
    designated="Rural",
    survey_year=2021,
    percent_canopy_cover=10.4,
    standard_error=1.37,
    number_of_points=500,
)


class TestComputeSubjectCanopyRow:
    def test_real_cholsey_values(self) -> None:
        row = compute_subject_canopy_row(REAL_CHOLSEY_WARD_RECORD, ward_weight=0.994)
        assert row.area_code == CHOLSEY_PARISH_CODE
        assert row.area_name == "Cholsey"
        assert row.area_role == "subject"
        assert row.metric_id == "canopy"
        assert row.year == 2021
        assert row.value == 10.4
        assert row.unit == "%"

    def test_always_flagged_as_parish_estimate(self) -> None:
        """Even when the weight is ~1.0, the value is still a ward-level
        rate, not a parish-specific measurement -- must always be
        flagged (STATUS.md backlog note, CLAUDE.md's "flag estimates"
        rule)."""
        row = compute_subject_canopy_row(REAL_CHOLSEY_WARD_RECORD, ward_weight=1.0)
        assert row.flag == "parish_estimate"
        assert row.flag_note != ""

    def test_method_is_area_weighted_not_direct(self) -> None:
        """The ward is a genuinely different (larger) polygon than the
        parish (verified live 2026-09-30: ward ~66 km^2 vs parish
        ~15.9 km^2), so this is never method=direct even at weight 1.0."""
        row = compute_subject_canopy_row(REAL_CHOLSEY_WARD_RECORD, ward_weight=1.0)
        assert row.method == "area_weighted"

    def test_geography_used_names_the_real_ward(self) -> None:
        row = compute_subject_canopy_row(REAL_CHOLSEY_WARD_RECORD, ward_weight=0.994)
        assert "E05009737" in row.geography_used
        assert "Cholsey" in row.geography_used

    def test_partial_weight_note_mentions_percentage(self) -> None:
        row = compute_subject_canopy_row(REAL_CHOLSEY_WARD_RECORD, ward_weight=0.994)
        assert "99.4%" in row.flag_note

    def test_full_weight_note_says_wholly_inside(self) -> None:
        row = compute_subject_canopy_row(REAL_CHOLSEY_WARD_RECORD, ward_weight=1.0)
        assert "wholly inside" in row.flag_note
