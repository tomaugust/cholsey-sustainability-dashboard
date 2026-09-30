# 0008. Which OS Open Greenspace function types count as "accessible green space" (metric 2)

- **Status:** Accepted (technical/methodology decision the plan itself delegates to this ADR — development-plan.md P3.3 says "Decide in an ADR which greenspace function types count as 'accessible'" — not a spec/scope/stack decision needing separate sign-off).
- **Date:** 2026-09-30
- **Deciders:** Phase 3 (P3.3) implementation
- **Related:** P3.3; development-plan.md risk R6; `config/sources.yaml`'s `os_open_greenspace` entry; `pipeline/src/cholsey_pipeline/metrics/greenspace.py`

## Context

Metric 2 is "accessible green space", output as m²/resident and % of parish area (spec §3, development-plan.md P3.3). The only real data source is OS Open Greenspace (`os_open_greenspace`, fetched live in P2.4), whose `greenspace_site` polygons carry a `function` attribute but **no accessibility flag** — the dataset's separate `access_point` layer records entry points, not whether the public can use a site at all, and is not currently read.

The real function values present in a live bbox-filtered read around Cholsey and its comparators (verified 2026-09-30 by actually running `fetch_greenspace_sites`, 203 real sites returned): `Playing Field`, `Religious Grounds`, `Allotments Or Community Growing Spaces`, `Tennis Court`, `Play Space` (Cholsey's own clipped subset), plus `Public Park Or Garden`, `Golf Course`, `Other Sports Facility`, `Cemetery`, `Bowling Green` seen in the wider P2.4 fixture / OS's own documented code list.

**Researched OS's own inclusion criteria and known critique before deciding**, rather than guessing which types are genuinely public:
- OS's technical documentation states `Playing Field` sites are only included "if used by the public at least some of the time" — school fields entirely enclosed and used only by the school are excluded from the dataset already. So `Playing Field`'s presence in the dataset is itself a (weak) public-use signal.
- OS's documentation states `Religious Grounds` is only populated "where there is a significant amount of accessible greenspace… more than 500m² of natural surface within the site" — a criterion about the *site having green space at all*, not about the public being free to walk it for recreation (as opposed to worship-related visiting).
- The **Open Spaces Society** publicly criticised OS Open Greenspace on exactly this point when it launched (grough.co.uk, 2017): it "shows a golf course on common land with a statutory right of access in the same way as an exclusive, private golf course," and includes "allotments, private school playing fields and private sports facilities" with no way to tell whether the public can actually use them. Their case officer called treating everything in the dataset as publicly accessible "seriously misleading."

## Decision

**Function types counted as "accessible green space" (included):**
- `Public Park Or Garden`
- `Playing Field` (OS's own inclusion rule already filters out enclosed, school/private-only fields)
- `Play Space`
- `Other Sports Facility`
- `Amenity - Residential Or Business`
- `Tennis Court`
- `Bowling Green`

**Function types excluded:**
- `Golf Course` — the dataset doesn't distinguish a fee-paying/members-only club from a rare public course; the Open Spaces Society's specific, documented criticism is exactly this ambiguity. Excluding avoids overstating public access.
- `Allotments Or Community Growing Spaces` — these are individually allocated private growing plots, not open, walkable public space, regardless of whether the wider site is community-run.
- `Religious Grounds` — OS's own inclusion criterion for this category is about on-site natural surface existing, not about general public recreational access; access is typically for worship-related visiting, not the kind of "accessible green space" the metric is meant to capture.
- `Cemetery` — primary function is burial/memorial, not public recreation; many are walkable but the type doesn't reliably signal general public accessibility any more than the excluded types above.

This is a defensible, documented line, not a certainty — the dataset genuinely cannot distinguish a village playing field open to all from a members-only tennis club within the same function code. If Tom or a future session wants a different line (e.g. including cemeteries), change this ADR's classification list and re-run `make refresh`; nothing else needs to change, since `metrics/greenspace.py` reads the type list from one place.

**District and national equivalents**: computed the same way (same function-type filter) once P3.7 needs them, per the plan's own "or flagged as unavailable" fallback if a district/national aggregate turns out not to be feasible from this dataset alone (not yet attempted).

## Consequences

- `pipeline/src/cholsey_pipeline/metrics/greenspace.py`'s `ACCESSIBLE_FUNCTION_TYPES` constant is the single place this list lives; sources.yaml's `os_open_greenspace` notes point here instead of repeating the rationale.
- Cholsey's own clipped site set (verified live 2026-09-30) happens to include `Playing Field`, `Tennis Court` and `Play Space` (all accessible) and `Allotments Or Community Growing Spaces`, `Religious Grounds` (both excluded) — so this ADR's line has a real, immediate effect on Cholsey's own metric 2 value, not just a hypothetical one for other parishes.
- A future session adding comparator/district/national rows should reuse `ACCESSIBLE_FUNCTION_TYPES` rather than re-deriving the classification.
