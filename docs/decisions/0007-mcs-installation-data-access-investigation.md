# 0007. MCS installation data access investigation (P2.7, plan risk R1)

- **Status:** Accepted — Tom answered Q-011 (STATUS.md, 2026-09-30): he manually retrieved the real MCS Data Dashboard export for South Oxfordshire (heat pump and solar PV), committed as reference data. This is closest to this ADR's Option 1 (coarser-than-parish resolution, flagged), but with the dashboard's own real, current MCS-certified figures rather than DESNZ's coarser/stale BUS ad-hoc releases.
- **Date:** 2026-09-30 (investigation); 2026-09-30 (answered and actioned)
- **Deciders:** Phase 2 (P2.7) investigation; decision by Tom (Q-011)
- **Related:** P2.7, P3.5; development-plan.md §3 Phase 2/3, §6 risk R1; `config/sources.yaml`'s `mcs_installations` entry; `fetch/mcs_installations.py`, `fetch/reference_data/mcs_installations/`, `metrics/mcs.py`; spec §3 metrics 5–6, §4 Data Sources

## Context

Spec §3 says metrics 5 (Solar PV uptake) and 6 (Heat pump uptake) come from "MCS installation database filtered to parish postcodes, divided by ONS dwelling count" — i.e. postcode-level MCS certification data. Plan risk R1 flagged this as the project's biggest data-access uncertainty and required P2.7 to investigate before building anything, with these fallbacks pre-identified: "MCS LSOA/LA aggregates apportioned, Ofgem FiT installation reports (postcode-district level) for PV history, DESNZ/Ofgem heat pump grant (BUS) statistics."

## Investigation (2026-09-30)

**MCS Data Dashboard** (`https://mcscertified.com/low-carbon-landscapes/mcs-data-dashboard/`, backed by `https://datadashboard.mcscertified.com/`): confirmed live — no self-service bulk/postcode-level download. The page states data is "free and open to the public... no restrictions on who can see this information" for *viewing*, but only offers per-chart image/data exports, not a full dataset. Data beyond the dashboard requires a formal request (`https://mcscertified.com/low-carbon-landscapes/mcs-data-requests/`) via a contact form — the page explicitly warns "data provided that exists beyond The MCS Data Dashboard may incur a charge" and that sharing is limited "as much as possible" per GDPR. Not suitable for an automated, zero-cost, re-fetchable pipeline (CLAUDE.md's "zero-cost" constraint) even if it would eventually work for a one-off snapshot.

**DESNZ solar PV deployment series** (the plan's national fallback pattern): the weekly/monthly "Solar PV deployment" statistical release (`weekly-solar-pv-installation-and-capacity-based-on-registration-date` and successors) is national-level only and was discontinued after June 2021 — not useful even while live, since it never had sub-national geography.

**DESNZ Boiler Upgrade Scheme (BUS) statistics** (heat pump fallback): the routinely-updated BUS collection publishes UK-national quarterly figures only. Geographic breakdowns (by local authority, region, or Parliamentary constituency) exist only as one-off "ad hoc request" releases (e.g. "grants paid by Local Authority", Dec 2023; "redemptions by ... region", Apr 2024) — not a routinely-refreshable series, and local-authority level (South Oxfordshire, ~140,000 population) is far coarser than parish (Cholsey, ~4,400) for the other 8 comparators' dashboard tiles too, not just Cholsey's.

**Ofgem FIT installation reports** (PV fallback): the collection page (`ofgem.gov.uk/.../public-reports-and-data-fit/installation-reports`) confirms quarterly "installation reports" exist, describing "a breakdown of accredited installations under the FIT within a specific quarter" — but its actual download links are not present in the page's static HTML (loaded via a JS-driven document system), so this session could not verify the real file's postcode-district granularity or a stable discovery pattern without further investigation (e.g. headless-browser rendering, not attempted here). FIT also closed to new applicants in 2019, so even if accessible, it would only cover installations up to that date — not current uptake as spec §3 requires ("current" = latest available year).

## Original options (proposed, before Q-011 was answered)

No fetcher had been built for metrics 5/6 at this point. Four options were put to Tom, none decided unilaterally:

1. Accept a coarser-than-parish resolution for solar PV/heat pumps (e.g. local-authority BUS ad-hoc figures, flagged `resolution=local_authority` in provenance, refreshed only when a new ad-hoc release happens to appear) — a real deviation from spec §3's stated method, not just an implementation detail.
2. Pursue the MCS data-request process for a one-off postcode-level extract (incurs unknown cost, GDPR-limited, and wouldn't be automatable for `make refresh` — would need periodic manual re-requests).
3. Invest more investigation time in Ofgem's FIT installation reports specifically (headless-browser fetch to find the real download links, then verify postcode-district granularity) — the only lead not yet fully exhausted, but PV-only and capped at 2019.
4. Defer metrics 5/6 entirely (mark as "not available" on the dashboard with a stated reason) until a better source is found.

## Resolution (2026-09-30, Q-011 answered)

Tom took a fifth path not on the original list, better than any of them: he manually operated the MCS Data Dashboard himself (browser session, not automated), filtered it to South Oxfordshire (the district Cholsey sits in) and technology (Air Source Heat Pump, Solar PV), and downloaded each chart's CSV export -- the same per-chart export mechanism this investigation had already found (no bulk download), just performed by a human instead of attempting to automate around GDPR/charging restrictions that make automation inappropriate anyway.

This is real, current, MCS-certified data (cumulative installation count, % of households with installations, yearly/monthly timelines back to 2009, tenure-type breakdown, average cost) -- committed as reference data (`fetch/reference_data/mcs_installations/`, see its `_provenance.json`) and loaded by `fetch/mcs_installations.py` (parsing only, no live HTTP call -- there is no bulk API to call). Two real, documented gaps: no installed-capacity (kWp) field in any of the exported charts, and whether the dashboard's own location filter goes finer than Local Authority (ward/parish) was not verified this session (browser automation against the real dashboard was attempted but blocked by this environment's outbound-proxy TLS handling, not by the dashboard itself -- worth revisiting with working browser access, since a parish-level dashboard filter would remove the need for any apportionment at all).

`metrics/mcs.py`'s `compute_subject_uptake_row` applies South Oxfordshire's own household-uptake rate uniformly to Cholsey (the same "coarser geography's rate applied to the parish" shape as metric 1's canopy-on-parish), `method=address_weighted`, always `flag=parish_estimate` -- effectively Option 1 above, but with the real MCS dashboard's own current figures rather than DESNZ's coarser, less current BUS ad-hoc releases. `compute_district_uptake_row` needs no apportionment at all, since South Oxfordshire already IS this project's district (spec §2, ADR-0003).

Real cross-check performed before trusting MCS's own "% of households" figures: independently fetched South Oxfordshire's real Census 2021 household count from nomis (61,497) and confirmed it's within ~0.1% of what MCS's own installs/percentage figures imply (~61,430-61,490) -- the two independent sources agree.

## Consequences

- P2.7 moves from `blocked` to `done` in STATUS.md -- the plan's own escalation path worked as intended: raised to the project lead rather than guessed, Tom made the real-world call, the agent then built on it.
- `config/sources.yaml`'s `mcs_installations` entry's `licence` stays `"TBD"` (MCS's reuse terms for dashboard exports were not confirmed this session) but its `fetcher`/`notes` now point at the real, committed reference data and loader module.
- P3.5 (metrics 5-6) is unblocked: subject and district rows are built (this ADR's resolution), comparator and national rows are not (see the P2.7/P3.5 worklog's "Not done" section) -- MCS's dashboard only gives South Oxfordshire's own figures from this session's manual pull; each comparator or a national/England aggregate would need its own manual dashboard session (or a live browser-automation investigation, still unverified per the gap noted above).
