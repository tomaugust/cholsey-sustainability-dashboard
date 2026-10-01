"""Tests for cholsey_pipeline.metrics.canopy (P3.2, metric 1).

Uses real values already verified live in prior phases: Cholsey ward
E05009737's real 2021 canopy figure (P2.3 fixture: 10.4%, standard error
1.37, 500 points) and the real parish-in-ward area weight ADR-0006
computed (99.4%), rather than synthetic numbers.
"""

from __future__ import annotations

import pytest

from cholsey_pipeline.fetch.forest_research_canopy import WardCanopyRecord
from cholsey_pipeline.metrics.canopy import (
    CHOLSEY_PARISH_CODE,
    compute_district_canopy_row,
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


# Real comparator ward-canopy records and weights, live-verified 2026-09-30
# (P3.2 comparator rows). 4 of Cholsey's 8 comparators (Aston Tirrold,
# Moulsford, Brightwell-cum-Sotwell, South Moreton) turned out to share
# Cholsey's own Forest Research ward (E05009737) -- confirmed by fetching
# that ward's real Dec 2018 boundary and computing each parish's real
# overlap, not assumed from the current-ward match. Crowmarsh and South
# Stoke's current ONS ward codes happen to match Forest Research's own
# codes directly (no vintage correction needed). Wallingford's Forest
# Research ward (E05009750, matched by NAME since its code doesn't match
# the current ONS ward E05011710) has a real, verified weight of 95.1%,
# not the 99.95% the current-vintage boundary would suggest -- a bigger
# vintage discrepancy than Cholsey's own 99.4% vs 100.0%, still handled
# the same documented way (real weight computed against Forest Research's
# actual ward polygon, not the current ONS one).
REAL_BENSON_CROWMARSH_WARD_RECORD = WardCanopyRecord(
    ward_code="E05009733",
    ward_name="Benson & Crowmarsh",
    designated="Rural",
    survey_year=2021,
    percent_canopy_cover=9.4,
    standard_error=1.31,
    number_of_points=500,
)
REAL_GORING_WARD_RECORD = WardCanopyRecord(
    ward_code="E05009743",
    ward_name="Goring",
    designated="Rural",
    survey_year=2021,
    percent_canopy_cover=16.6,
    standard_error=1.66,
    number_of_points=500,
)
REAL_WALLINGFORD_WARD_RECORD = WardCanopyRecord(
    ward_code="E05009750",
    ward_name="Wallingford",
    designated="Urban",
    survey_year=2021,
    percent_canopy_cover=15.8,
    standard_error=1.63,
    number_of_points=500,
)


class TestComputeComparatorCanopyRow:
    def test_aston_tirrold_shares_cholseys_ward(self) -> None:
        """Real finding: Aston Tirrold's parish boundary falls 100%
        inside Cholsey's own Forest Research ward (E05009737), verified
        against that ward's actual 2018-vintage boundary, not assumed."""
        row = compute_subject_canopy_row(
            REAL_CHOLSEY_WARD_RECORD,
            ward_weight=1.0,
            parish_code="E04008102",
            parish_name="Aston Tirrold",
            area_role="comparator",
        )
        assert row.area_code == "E04008102"
        assert row.area_role == "comparator"
        assert row.value == 10.4

    def test_wallingford_uses_its_own_real_forest_research_ward(self) -> None:
        """Wallingford's Forest Research ward record doesn't share
        Cholsey's -- it has its own (E05009750), matched by name since
        its code doesn't match the current ONS ward, with a real
        verified weight of 95.1% (not the current-vintage boundary's
        99.95%)."""
        row = compute_subject_canopy_row(
            REAL_WALLINGFORD_WARD_RECORD,
            ward_weight=0.951011,
            parish_code="E04012496",
            parish_name="Wallingford",
            area_role="comparator",
        )
        assert row.area_code == "E04012496"
        assert row.value == 15.8
        assert "E05009750" in row.geography_used

    def test_crowmarsh_and_south_stoke_use_current_ward_codes_directly(self) -> None:
        """Crowmarsh and South Stoke's Forest Research ward codes happen
        to match the current ONS ward codes exactly -- no vintage
        correction needed, unlike Cholsey/Wallingford."""
        crowmarsh = compute_subject_canopy_row(
            REAL_BENSON_CROWMARSH_WARD_RECORD,
            ward_weight=0.999805,
            parish_code="E04008118",
            parish_name="Crowmarsh",
            area_role="comparator",
        )
        assert crowmarsh.value == 9.4

        south_stoke = compute_subject_canopy_row(
            REAL_GORING_WARD_RECORD,
            ward_weight=0.9984,
            parish_code="E04008163",
            parish_name="South Stoke",
            area_role="comparator",
        )
        assert south_stoke.value == 16.6

    def test_comparator_rows_are_also_always_flagged(self) -> None:
        row = compute_subject_canopy_row(
            REAL_CHOLSEY_WARD_RECORD,
            ward_weight=1.0,
            parish_code="E04008148",
            parish_name="Moulsford",
            area_role="comparator",
        )
        assert row.flag == "parish_estimate"


# Real South Oxfordshire district data: all 21 of its real wards' Forest
# Research canopy records and current (Dec 2020) ward areas, live-verified
# 2026-10-01 (P3.7). Matched by code first, then by name for the wards
# whose Forest Research record uses a different vintage/code (Cholsey,
# Wallingford, Wheatley) -- same investigation method ADR-0006 and P3.2's
# comparator rows already established, not assumed.
REAL_SOUTH_OXON_WARD_RECORDS = [
    WardCanopyRecord("E05009733", "Benson & Crowmarsh", "Rural", 2021, 9.4, 1.31, 500),
    WardCanopyRecord("E05009734", "Berinsfield", "Rural", 2021, 11.4, 1.42, 500),
    WardCanopyRecord("E05009735", "Chalgrove", "Rural", 2021, 9.4, 1.31, 500),
    WardCanopyRecord("E05009736", "Chinnor", "Rural", 2021, 17.2, 1.69, 500),
    WardCanopyRecord("E05009737", "Cholsey", "Rural", 2021, 10.4, 1.37, 500),
    WardCanopyRecord("E05009738", "Didcot North East", "Urban", 2021, 16.6, 1.66, 500),
    WardCanopyRecord("E05009739", "Didcot South", "Urban", 2021, 12.8, 1.49, 500),
    WardCanopyRecord("E05009740", "Didcot West", "Urban", 2021, 15.4, 1.61, 500),
    WardCanopyRecord("E05009741", "Forest Hill & Holton", "Rural", 2021, 19.8, 1.78, 501),
    WardCanopyRecord("E05009742", "Garsington & Horspath", "Rural", 2021, 12.6, 1.48, 501),
    WardCanopyRecord("E05009743", "Goring", "Rural", 2021, 16.6, 1.66, 500),
    WardCanopyRecord("E05009744", "Haseley Brook", "Rural", 2021, 15.2, 1.61, 500),
    WardCanopyRecord("E05009745", "Henley-on-Thames", "Urban", 2021, 24.4, 1.92, 500),
    WardCanopyRecord("E05009746", "Kidmore End & Whitchurch", "Rural", 2021, 31.4, 2.08, 500),
    WardCanopyRecord("E05009747", "Sandford & the Wittenhams", "Rural", 2021, 14.6, 1.58, 500),
    WardCanopyRecord("E05009748", "Sonning Common", "Rural", 2021, 26.6, 1.98, 500),
    WardCanopyRecord("E05009749", "Thame", "Urban", 2021, 13.4, 1.52, 500),
    WardCanopyRecord("E05009750", "Wallingford", "Urban", 2021, 15.8, 1.63, 500),
    WardCanopyRecord("E05009751", "Watlington", "Rural", 2021, 23.8, 1.9, 500),
    WardCanopyRecord("E05009752", "Wheatley", "Rural", 2021, 13.0, 1.5, 500),
    WardCanopyRecord("E05009753", "Woodcote & Rotherfield", "Rural", 2021, 31.0, 2.07, 500),
]
REAL_SOUTH_OXON_WARD_AREAS_M2 = {
    "E05009733": 40305411.75120657,
    "E05009734": 13166924.214008918,
    "E05009735": 27907872.90296917,
    "E05009736": 41632081.20607154,
    "E05009737": 65958117.63365275,  # Cholsey -- current E05011701's area, matched by name
    "E05009738": 5246339.130966616,
    "E05009739": 2886861.3399699824,
    "E05009740": 1996440.4693362839,
    "E05009741": 61426823.06986511,
    "E05009742": 20428819.58102144,
    "E05009743": 17290312.355132066,
    "E05009744": 71665953.63907135,
    "E05009745": 6155314.698333546,
    "E05009746": 38838615.173626654,
    "E05009747": 49780973.12149239,
    "E05009748": 32920397.383389328,
    "E05009749": 12667209.873177672,
    "E05009750": 3869228.6443585157,  # Wallingford -- current E05011710's area, matched by name
    "E05009751": 75097888.86104754,
    "E05009752": 4688723.921376777,  # Wheatley -- current E05011711's area, matched by name
    "E05009753": 84591119.26032843,
}


class TestComputeDistrictCanopyRow:
    def test_real_south_oxfordshire_value(self) -> None:
        row = compute_district_canopy_row(
            REAL_SOUTH_OXON_WARD_RECORDS,
            REAL_SOUTH_OXON_WARD_AREAS_M2,
            district_code="E07000179",
            district_name="South Oxfordshire",
        )
        assert row.area_code == "E07000179"
        assert row.area_role == "district"
        assert row.year == 2021
        assert row.value == pytest.approx(18.9703889945608, rel=1e-9)

    def test_method_is_area_weighted_and_not_flagged(self) -> None:
        """A district aggregate across its own real wards is the
        district's own figure, not an estimate borrowed from elsewhere --
        unlike the subject/comparator rows, which are always flagged."""
        row = compute_district_canopy_row(
            REAL_SOUTH_OXON_WARD_RECORDS,
            REAL_SOUTH_OXON_WARD_AREAS_M2,
            district_code="E07000179",
            district_name="South Oxfordshire",
        )
        assert row.method == "area_weighted"
        assert row.flag == "none"
        assert row.flag_note == ""

    def test_raises_on_empty_records(self) -> None:
        with pytest.raises(ValueError, match="at least one ward record"):
            compute_district_canopy_row([], {}, district_code="E07000179", district_name="x")

    def test_raises_on_mismatched_survey_years(self) -> None:
        mismatched = [
            WardCanopyRecord("A", "A", "Rural", 2020, 10.0, 1.0, 500),
            WardCanopyRecord("B", "B", "Rural", 2021, 10.0, 1.0, 500),
        ]
        with pytest.raises(ValueError, match="same survey_year"):
            compute_district_canopy_row(
                mismatched, {"A": 1.0, "B": 1.0}, district_code="x", district_name="x"
            )

    def test_raises_on_missing_ward_area(self) -> None:
        with pytest.raises(ValueError, match="E05009733"):
            compute_district_canopy_row(
                [REAL_SOUTH_OXON_WARD_RECORDS[0]], {}, district_code="x", district_name="x"
            )
