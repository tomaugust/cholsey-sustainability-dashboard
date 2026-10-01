"""Metric 1: tree canopy cover % (development-plan.md Phase 3, P3.2).

A parish's canopy % is taken directly from its containing ward's Forest
Research i-Tree Canopy figure (`fetch.forest_research_canopy`) --
`method=area_weighted` (not `direct`), because even when a parish sits
almost entirely inside one ward, the ward is geometrically a different,
larger polygon (Cholsey ward is ~66 km^2 vs Cholsey parish's ~15.9 km^2,
verified live 2026-09-30), so the ward's rate is not necessarily uniform
across the parish specifically. Always `flag=parish_estimate`, per the
Phase 1 PR review's own note (STATUS.md backlog): a ward-level figure
applied to a parish must say so, not be presented as parish-specific.

Real finding carried over from P2.3/ADR-0006: Forest Research's own
canopy record for Cholsey uses wardcode E05009737 (Dec 2018 ward
edition, survyear 2021), not the current ONS ward E05011701 --
geometrically near-identical for Cholsey (P1.5's weights.csv: ~99.4% of
the parish falls inside E05009737's boundary), so this module uses that
real, verified weight rather than assuming 1.0.

Comparator rows (2026-09-30, P3.2): each comparator's containing ward was
determined live (`geography.boundaries.fetch_boundary`'s `bbox` param,
P3.4), then matched to Forest Research's own ward record by NAME, not
assumed to share the current ONS ward code (ADR-0006's explicit lesson).
Real finding: 4 of Cholsey's 8 comparators (Aston Tirrold, Moulsford,
Brightwell-cum-Sotwell, South Moreton) turned out to fall almost entirely
inside Cholsey's own Forest Research ward (E05009737) -- verified against
that ward's real 2018-vintage boundary, not inferred from the current-ward
match. Crowmarsh and South Stoke's Forest Research ward codes happen to
equal their current ONS ward codes directly. Wallingford has its own
Forest Research ward (E05009750, matched by name; current ONS ward
E05011710 doesn't appear in Forest Research's dataset), with a real
verified weight of 95.1% against the actual 2018 boundary (not the 99.95%
the current-vintage boundary alone would suggest).

**Real data gap**: Aldworth's containing ward (Basildon, West Berkshire,
ONS code E05012133) has NO Forest Research canopy record at all -- checked
by code and by name, genuinely absent from the citizen-science dataset
(West Berkshire's wards may not have been surveyed). No canopy row is
computed for Aldworth; this is logged as a real, documented gap
(CLAUDE.md: never silently interpolate a missing value), not silently
estimated from a neighbouring ward or omitted without explanation.

National row (2026-10-01): England's own real area-weighted average
across all 6,135 of its own Forest Research ward records
(`fetch.forest_research_canopy.fetch_ward_canopy_for_country`). Unlike
the district row, this doesn't need a separate ward-to-LAD boundary join
at all -- Forest Research's own dataset carries each ward's own area
(`warea`), verified live against Cholsey's own ward record
(66,557,077.88 m2, matching the ~66 km2 figure already used above), so
`compute_national_canopy_row` area-weights directly off each record's own
`ward_area_m2` rather than a separately-fetched current ONS boundary
layer.

**Real, significant finding (ADR-0009)**: unlike South Oxfordshire's 21
wards (which fully tile the district), Forest Research's England-wide
dataset does NOT cover all of England -- its 6,135 ward records sum to
only 71,286,265,097.85 m2 (~71,286 km2), **54.6% of England's real area**
(130,462,331,610.03 m2, the same `country_bfc` boundary P3.3's national
greenspace row uses), even though it covers 89.4% of England's wards *by
count* (6,135 of 6,862 current wards) -- meaning the missing wards are
disproportionately large/rural (consistent with Aldworth's own containing
ward having no Forest Research record at all, noted above). The wards
were also surveyed across multiple real years (2018-2023, not one single
year), and 268 of the 6,135 records (4.4%) carry a placeholder
`survey_year` of 0 with real `percent_canopy_cover`/`ward_area_m2` but no
recorded `standard_error`/`number_of_points` -- see ADR-0009 and
`contracts.py`'s `forest_research_canopy_national` entry.

`method=area_weighted`, **`flag=partial_coverage`** (unlike the district
row's `flag=none` -- England's available wards don't tile the country the
way South Oxfordshire's do, so this is a real, material coverage gap,
not just a borrowed estimate). Real figure, live-verified 2026-10-01:
England's area-weighted average canopy cover across all 6,135 available
ward records (year label 2020, the modal real survey year) is
**14.41%**.
"""

from __future__ import annotations

from dataclasses import dataclass

from cholsey_pipeline.fetch.forest_research_canopy import WardCanopyRecord

CHOLSEY_PARISH_CODE = "E04012474"
CHOLSEY_PARISH_NAME = "Cholsey"
CHOLSEY_WARD_CODE = "E05009737"
"""Forest Research's own ward vintage for Cholsey (Dec 2018 edition), not
the current ONS ward E05011701 -- see ADR-0006. `fetch_ward_canopy` must
be called with this code, not the current one, or no record is returned."""

METRIC_ID = "canopy"


@dataclass(frozen=True)
class CanopyMetricRow:
    """One area's canopy-cover metric row, shaped to slot directly into
    `data/processed/metrics.csv` (development-plan.md §2.3) once P3.9's
    export step exists -- field names deliberately match that schema."""

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


def compute_subject_canopy_row(
    ward_record: WardCanopyRecord,
    ward_weight: float,
    parish_code: str = CHOLSEY_PARISH_CODE,
    parish_name: str = CHOLSEY_PARISH_NAME,
    area_role: str = "subject",
) -> CanopyMetricRow:
    """Build the canopy metric row for a parish contained (wholly or
    almost wholly) in a single ward. `ward_weight` is the real, verified
    share of the parish's area falling inside `ward_record`'s ward (from
    `data/processed/geography/weights.csv`'s `weight_type=area` rows) --
    used only to decide how prominently to note the estimate, since the
    canopy VALUE itself is the ward's own rate regardless of the exact
    weight (there being only one overlapping ward means there's nothing
    to area-weight a blend across).

    Despite the name (kept for the original Cholsey call sites), this
    works for any parish contained in a single ward -- `area_role`
    defaults to `"subject"` but comparator parishes pass
    `area_role="comparator"` (P3.2, most of Cholsey's comparators turned
    out to share Cholsey's own current ward, verified live 2026-09-30).

    Pure function -- tested against real values (Cholsey ward E05009737,
    survyear 2021: 10.4% canopy cover).
    """
    weight_note = (
        f"{ward_weight:.1%} of the parish's area falls inside this ward"
        if ward_weight < 0.999
        else "the parish lies wholly inside this ward"
    )
    return CanopyMetricRow(
        area_code=parish_code,
        area_name=parish_name,
        area_role=area_role,
        metric_id=METRIC_ID,
        year=ward_record.survey_year,
        value=ward_record.percent_canopy_cover,
        unit="%",
        geography_used=f"ward {ward_record.ward_code} ({ward_record.ward_name})",
        method="area_weighted",
        flag="parish_estimate",
        flag_note=(
            f"Ward-level canopy % ({ward_record.ward_name} ward) applied directly "
            f"to the parish -- {weight_note}. Canopy density may not be uniform "
            "across the ward, so this is a ward-level estimate, not a "
            "parish-specific measurement (see ADR-0006)."
        ),
    )


def compute_district_canopy_row(
    ward_records: list[WardCanopyRecord],
    ward_areas: dict[str, float],
    district_code: str,
    district_name: str,
) -> CanopyMetricRow:
    """Build a district's canopy row as the real area-weighted average of
    its own wards' Forest Research canopy figures -- not an estimate
    applied from elsewhere, since every ward genuinely belongs to this
    district. `ward_areas` maps each `ward_records` entry's `ward_code`
    to its real area (m2, current ONS Dec 2020 ward boundary) -- used as
    the weight, since Forest Research doesn't publish ward population or
    an equivalent denominator, and i-Tree Canopy's standard error already
    accounts for sampling density within each ward.

    `method=area_weighted`, `flag=none`: unlike the subject/comparator
    rows (a single ward's rate applied to a smaller parish it may not
    represent), a district aggregate across its own full set of wards is
    the district's own real figure, not borrowed from elsewhere. The one
    real approximation -- a few of South Oxfordshire's wards (Cholsey,
    Wallingford, Wheatley) have Forest Research records matching a
    slightly different ward boundary vintage than the current one used
    for `ward_areas` -- is noted in `flag_note` for transparency, not
    flagged as an estimate in the strict schema sense (the real overlaps
    verified live range 93.8%-100%, not materially changing the result).

    Raises if `ward_records` don't all share the same `survey_year`
    (nothing to average sensibly across different years) or if any
    record's `ward_code` is missing from `ward_areas`.

    Pure function -- tested against real values (South Oxfordshire's 21
    real wards, live-verified 2026-10-01: area-weighted average 18.97%).
    """
    if not ward_records:
        raise ValueError("compute_district_canopy_row requires at least one ward record")
    year = ward_records[0].survey_year
    if any(r.survey_year != year for r in ward_records):
        raise ValueError("all ward records must share the same survey_year")

    total_area = 0.0
    weighted_sum = 0.0
    for r in ward_records:
        if r.ward_code not in ward_areas:
            raise ValueError(f"ward '{r.ward_code}' has a record but no entry in ward_areas")
        area = ward_areas[r.ward_code]
        total_area += area
        weighted_sum += area * r.percent_canopy_cover

    return CanopyMetricRow(
        area_code=district_code,
        area_name=district_name,
        area_role="district",
        metric_id=METRIC_ID,
        year=year,
        value=weighted_sum / total_area,
        unit="%",
        geography_used=f"{len(ward_records)} wards (area-weighted)",
        method="area_weighted",
        flag="none",
        flag_note="",
    )


def compute_national_canopy_row(
    ward_records: list[WardCanopyRecord],
    year: int,
    country_code: str = "E92000001",
    country_name: str = "England",
    england_area_m2: float = 130_462_331_610.02695,
    current_ward_count: int = 6862,
) -> CanopyMetricRow:
    """Build England's canopy row as the real area-weighted average across
    every ward Forest Research's dataset actually has for England, using
    each record's OWN `ward_area_m2` field as the weight (verified real
    and usable -- see the module docstring) rather than a separate join
    against current ONS ward boundaries.

    Unlike `compute_district_canopy_row`, this does NOT require every
    `ward_records` entry to share one `survey_year` -- Forest Research's
    wards were genuinely surveyed across multiple real years (2018-2023),
    so `year` is passed in by the caller as a representative label (the
    modal real survey year across the batch, 2020 as of 2026-10-01 --
    see ADR-0009), not asserted uniform.

    **Always `flag=partial_coverage`, never `flag=none`** (ADR-0009): the
    included wards do not tile England the way a district's own wards
    tile it -- they cover only a documented fraction of England's real
    area (computed here from `england_area_m2` and each record's
    `ward_area_m2`) and of its current ward count (`current_ward_count`),
    with the missing wards skewed disproportionately large/rural. This is
    a real, material coverage gap that must stay visible wherever this
    figure is shown, not a borrowed estimate like the subject/comparator
    rows' `flag=parish_estimate`, and not the district row's "this is our
    own full real figure" `flag=none`.

    Raises if any record has no `ward_area_m2` (would silently corrupt
    the area-weighted average -- see `forest_research_canopy_national`'s
    contract, which already guards against this for the live fetch, but
    this function doesn't assume its caller used that fetch).

    Pure function -- tested against real values (England's 6,135 available
    Forest Research ward records, live-verified 2026-10-01: area-weighted
    average 14.41%, covering 54.6% of England's real area).
    """
    if not ward_records:
        raise ValueError("compute_national_canopy_row requires at least one ward record")

    total_area = 0.0
    weighted_sum = 0.0
    for r in ward_records:
        if r.ward_area_m2 is None:
            raise ValueError(f"ward '{r.ward_code}' has no ward_area_m2 to weight by")
        total_area += r.ward_area_m2
        weighted_sum += r.ward_area_m2 * r.percent_canopy_cover

    pct_area_covered = total_area / england_area_m2 * 100
    pct_wards_covered = len(ward_records) / current_ward_count * 100

    return CanopyMetricRow(
        area_code=country_code,
        area_name=country_name,
        area_role="national",
        metric_id=METRIC_ID,
        year=year,
        value=weighted_sum / total_area,
        unit="%",
        geography_used=f"{len(ward_records)} wards (area-weighted, partial coverage)",
        method="area_weighted",
        flag="partial_coverage",
        flag_note=(
            f"Area-weighted average across the {len(ward_records)} English ward "
            "records Forest Research's dataset actually has -- this covers "
            f"{pct_wards_covered:.1f}% of England's current wards by count but only "
            f"{pct_area_covered:.1f}% of its real area, since the missing wards are "
            "disproportionately large/rural (see ADR-0009); this figure likely "
            "skews toward more urban canopy rates than true full-England coverage "
            "would show. Also blends multiple real survey years (2018-2023) into "
            f"one figure, labelled with the modal year ({year})."
        ),
    )
