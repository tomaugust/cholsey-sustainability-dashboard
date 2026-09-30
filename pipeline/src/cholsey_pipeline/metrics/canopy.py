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

District/national rows need a ward-to-LAD lookup (district) and a full
England-wide ward-area-weighted aggregate (national), neither built yet.
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
