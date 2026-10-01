"""Metric 2: accessible green space (development-plan.md Phase 3, P3.3).

OS Open Greenspace site polygons (`fetch.os_open_greenspace`), clipped to
the parish boundary, restricted to the function types ADR-0008 classifies
as genuinely publicly accessible, then divided by population (m2/resident)
and by parish area (% of parish area). Unlike metric 1 (a ward rate
applied to a parish it doesn't equal), this is a direct geometric
measurement of real polygons against the parish's own boundary --
`method=clip`, not `area_weighted`.

Always `flag=partial_coverage`: OS Open Greenspace itself does not cover
every kind of land the public can actually access -- notably it excludes
CRoW-protected open country/common land (Open Spaces Society's own
published criticism of the dataset, cited in ADR-0008), so this metric
systematically undercounts true accessible green space rather than
over- or exactly counting it.

Comparator rows (2026-09-30): all 8 comparators built, reusing
`fetch_greenspace_sites`' single bbox-wide fetch (203 real sites already
covering the whole study area) -- each comparator just needs its own
`geopandas.clip` and population denominator, no vintage-matching
complication like metric 1's Forest Research wards (OS Open Greenspace
is one current dataset, not a per-area citizen-science patchwork).

District row (2026-10-01): South Oxfordshire's own figure, built the
same way as the subject/comparator rows (`compute_subject_greenspace_row`
with `area_role="district"`) -- a fresh live clip against the real
district boundary (new `lad_bfc` layer, `geography.boundaries`), not a
sum of the 8 comparators already computed (they don't tile South
Oxfordshire). `boundary_label`/`population_label` params let the row's
text correctly describe a district boundary and a real Census 2021
population (149,085, nomis) rather than the parish-row wording's
"parish boundary"/"mid-2021 parish estimate", which would otherwise be
factually wrong for this row. Real figure: 45.26 m2/resident.

National row (2026-10-01): England's own figure. Unlike the subject/
comparator/district rows, this isn't built from a `geopandas.clip` call
made here against a committed fixture -- England's real accessible-site
set is 96,914 features (OS Open Greenspace, bbox-fetched for the whole
country), far too large to commit to the repo as a test fixture. The
live fetch, OS BFC boundary simplification (`shapely.simplify`,
tolerance=50m, preserve_topology=True -- needed because clipping
~150,817 raw site polygons against England's full-precision coastline
boundary did not complete in 30 minutes; simplifying first to a ~21x
smaller WKB, then splitting into a fast `.within()` pass for sites fully
inside the simplified boundary and an exact `gpd.clip()` only for the
much smaller set of boundary-straddling candidates, finished in ~261s --
is the reusable pattern for any future national-scale geometry work in
this pipeline) and the real site-level clip all happened in a one-off
script, not in a function tested here. `compute_national_greenspace_row`
therefore takes the already-computed accessible area directly (a real,
live-verified pre-aggregated total, same idea as `LsoaEnergyRecord`
carrying pre-aggregated totals rather than raw underlying records) and
reuses the same row-shaping/flag-note logic as the other roles via the
shared `_build_greenspace_row` helper. Real figures, verified live
2026-10-01: accessible area 1,940,711,368.3078492 m2 (96,914 sites),
England area (real, unsimplified BFC boundary) 130,462,331,610.02695 m2
(1.4875645286709653% of England), England population 56,490,048
(Census 2021, nomis, E92000001) -> 34.3549251065931 m2/resident.
"""

from __future__ import annotations

from dataclasses import dataclass

import geopandas as gpd

CHOLSEY_PARISH_CODE = "E04012474"
CHOLSEY_PARISH_NAME = "Cholsey"
METRIC_ID = "greenspace"

ACCESSIBLE_FUNCTION_TYPES = frozenset(
    {
        "Public Park Or Garden",
        "Playing Field",
        "Play Space",
        "Other Sports Facility",
        "Amenity - Residential Or Business",
        "Tennis Court",
        "Bowling Green",
    }
)
"""Which OS Open Greenspace `function` values count as accessible green
space -- see ADR-0008 for the full rationale (OS's own inclusion rules,
and the Open Spaces Society's documented critique of types this dataset
cannot reliably distinguish as public vs private, e.g. Golf Course).
Excluded: Golf Course, Allotments Or Community Growing Spaces, Religious
Grounds, Cemetery."""


@dataclass(frozen=True)
class GreenspaceMetricRow:
    """One area's accessible-greenspace metric row, shaped to slot into
    `data/processed/metrics.csv` (development-plan.md §2.3) once P3.9's
    export step exists. `accessible_area_m2` and `pct_of_parish_area` are
    extra fields beyond the strict metrics.csv schema, kept here for the
    detail page's "% of parish area" figure (spec §3 metric 2 wants both
    units, but metrics.csv/metrics.yaml only register one metric_id with
    one primary unit, m2_per_resident)."""

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
    accessible_area_m2: float
    pct_of_parish_area: float


def compute_subject_greenspace_row(
    clipped_sites: gpd.GeoDataFrame,
    parish_area_m2: float,
    population: int,
    year: int,
    parish_code: str = CHOLSEY_PARISH_CODE,
    parish_name: str = CHOLSEY_PARISH_NAME,
    area_role: str = "subject",
    boundary_label: str = "parish boundary",
    population_label: str = "the mid-2021 parish estimate",
) -> GreenspaceMetricRow:
    """Build the greenspace metric row for an area, given its OS Open
    Greenspace sites already clipped to that area's boundary (e.g. via
    `geopandas.clip`), the area's own area (m2, computed the same way
    P1.5's weights.py does -- `geom.area` in a metres-based CRS) and its
    population denominator.

    Despite the name (kept for the original Cholsey call sites), this
    works for any area -- `area_role` defaults to `"subject"` but
    comparators pass `area_role="comparator"` (P3.3) and the district
    passes `area_role="district"` (P3.7) with `boundary_label`/
    `population_label` overridden to describe the real boundary/
    population source actually used (e.g. South Oxfordshire's district
    boundary and its Census 2021 population, not a parish or a mid-2021
    estimate). Unlike metric 1's ward-vintage complications, there's no
    equivalent issue here: OS Open Greenspace is a single current
    dataset, so every area just needs its own clip of the same
    already-fetched site set.

    Pure function over already-clipped/already-looked-up inputs, same
    split as metric 1's `compute_subject_canopy_row` -- the live fetch
    and clip happen in a caller/script, not here, so this can be tested
    against a small committed fixture with no network.
    """
    accessible = clipped_sites[clipped_sites["function"].isin(ACCESSIBLE_FUNCTION_TYPES)]
    accessible_area_m2 = float(accessible.geometry.area.sum())
    return _build_greenspace_row(
        accessible_area_m2=accessible_area_m2,
        area_area_m2=parish_area_m2,
        population=population,
        year=year,
        area_code=parish_code,
        area_name=parish_name,
        area_role=area_role,
        boundary_label=boundary_label,
        population_label=population_label,
    )


def compute_national_greenspace_row(
    accessible_area_m2: float,
    england_area_m2: float,
    population: int,
    year: int,
    area_code: str = "E92000001",
    area_name: str = "England",
) -> GreenspaceMetricRow:
    """Build England's national greenspace row from an already-computed
    accessible area (see module docstring -- England's 96,914-site
    accessible set is fetched/clipped in a one-off script, not here, as
    it's far too large to commit as a test fixture). Shares the same
    row-shaping/flag-note logic as the subject/comparator/district rows
    via `_build_greenspace_row`.
    """
    return _build_greenspace_row(
        accessible_area_m2=accessible_area_m2,
        area_area_m2=england_area_m2,
        population=population,
        year=year,
        area_code=area_code,
        area_name=area_name,
        area_role="national",
        boundary_label="England boundary",
        population_label="the Census 2021 England population (nomis)",
    )


def _build_greenspace_row(
    *,
    accessible_area_m2: float,
    area_area_m2: float,
    population: int,
    year: int,
    area_code: str,
    area_name: str,
    area_role: str,
    boundary_label: str,
    population_label: str,
) -> GreenspaceMetricRow:
    """Shared row-shaping logic for every `area_role` (subject, comparator,
    district, national) -- see `compute_subject_greenspace_row`'s
    docstring for why the flag/method/unit are the same regardless of
    which area this is."""
    value = accessible_area_m2 / population
    pct_of_parish_area = accessible_area_m2 / area_area_m2 * 100

    return GreenspaceMetricRow(
        area_code=area_code,
        area_name=area_name,
        area_role=area_role,
        metric_id=METRIC_ID,
        year=year,
        value=value,
        unit="m2_per_resident",
        geography_used=f"{boundary_label} (BFC), clipped",
        method="clip",
        flag="partial_coverage",
        flag_note=(
            f"OS Open Greenspace sites within the {boundary_label}, restricted to "
            "function types classed as publicly accessible (see ADR-0008); "
            "excludes allotments, religious grounds, cemeteries and golf courses. "
            "OS Open Greenspace itself does not include CRoW open-access country "
            "or common land, so this systematically undercounts true accessible "
            f"green space, not just an estimate of the counted types. Population "
            f"denominator is {population_label}; the greenspace layer itself is "
            "OS's current periodic-refresh snapshot, not dated to a single year."
        ),
        accessible_area_m2=accessible_area_m2,
        pct_of_parish_area=pct_of_parish_area,
    )
