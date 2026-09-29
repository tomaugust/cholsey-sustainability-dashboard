"""Select comparator parishes by real polygon adjacency to Cholsey.

development-plan.md Phase 1, P1.3: "compute parishes whose polygons touch
Cholsey. Compare with the spec's candidate list... Record the final list as
an ADR and ask the project lead to confirm." This module does the
computation; the ADR and the project lead's confirmation are separate (see
docs/decisions/0003-comparator-parish-selection.md and Q-009 in STATUS.md)
-- this module deliberately does NOT decide the final comparator list on
its own, per CLAUDE.md's rule that comparator/scope decisions are not an
agent's to make unilaterally.
"""

from __future__ import annotations

import geopandas as gpd

SUBJECT_CODE = "E04012474"  # Cholsey
"""GSS code of the parish everything else is compared against (spec §2)."""

CODE_FIELD = "PARNCP23CD"
NAME_FIELD = "PARNCP23NM"


def find_touching_parishes(
    parishes: gpd.GeoDataFrame,
    subject_code: str = SUBJECT_CODE,
    buffer_m: float = 5.0,
) -> gpd.GeoDataFrame:
    """Return the rows of `parishes` whose polygon touches the subject's.

    `parishes` must include the subject parish's own row (it's excluded
    from the result) and must be in a metres-based CRS (British National
    Grid, EPSG:27700 -- what geography.boundaries.fetch_boundary already
    fetches). `buffer_m` tolerates the small gaps BFC (clipped) boundaries
    can have at shared edges due to clipping/simplification -- verified
    stable across buffer_m in {0, 1, 5, 20} for Cholsey's real neighbours
    (see the P1.3 worklog entry), so the default is a safe middle value,
    not a knob that changes the answer.

    "Touching" here means geometric intersection after buffering, which
    also catches parishes that share only a short boundary or a single
    point -- deliberately inclusive, since the plan says "touch", and a
    human (the project lead, via the ADR) decides which touching parishes
    actually make sense as comparators, not this function.
    """
    if subject_code not in set(parishes[CODE_FIELD]):
        raise ValueError(
            f"Subject parish '{subject_code}' not found in the supplied GeoDataFrame "
            f"-- fetch it along with the candidates first."
        )
    subject_geom = parishes.loc[parishes[CODE_FIELD] == subject_code, "geometry"].iloc[0]
    others = parishes[parishes[CODE_FIELD] != subject_code]
    subject_buffered = subject_geom.buffer(buffer_m)
    touching_mask = others.geometry.intersects(subject_buffered)
    return others[touching_mask].sort_values(NAME_FIELD).reset_index(drop=True)
