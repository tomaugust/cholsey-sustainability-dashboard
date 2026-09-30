# 0007. MCS installation data access investigation (P2.7, plan risk R1)

- **Status:** Proposed — this affects the resolution spec §3 explicitly specifies for metrics 5 (solar PV) and 6 (heat pumps), so per CLAUDE.md it's raised to the project lead rather than decided unilaterally. See Q-011 (STATUS.md).
- **Date:** 2026-09-30
- **Deciders:** Phase 2 (P2.7) investigation — decision pending Tom (Q-011)
- **Related:** P2.7; development-plan.md §3 Phase 2, §6 risk R1; `config/sources.yaml`'s `mcs_installations` entry; spec §3 metrics 5–6, §4 Data Sources

## Context

Spec §3 says metrics 5 (Solar PV uptake) and 6 (Heat pump uptake) come from "MCS installation database filtered to parish postcodes, divided by ONS dwelling count" — i.e. postcode-level MCS certification data. Plan risk R1 flagged this as the project's biggest data-access uncertainty and required P2.7 to investigate before building anything, with these fallbacks pre-identified: "MCS LSOA/LA aggregates apportioned, Ofgem FiT installation reports (postcode-district level) for PV history, DESNZ/Ofgem heat pump grant (BUS) statistics."

## Investigation (2026-09-30)

**MCS Data Dashboard** (`https://mcscertified.com/low-carbon-landscapes/mcs-data-dashboard/`, backed by `https://datadashboard.mcscertified.com/`): confirmed live — no self-service bulk/postcode-level download. The page states data is "free and open to the public... no restrictions on who can see this information" for *viewing*, but only offers per-chart image/data exports, not a full dataset. Data beyond the dashboard requires a formal request (`https://mcscertified.com/low-carbon-landscapes/mcs-data-requests/`) via a contact form — the page explicitly warns "data provided that exists beyond The MCS Data Dashboard may incur a charge" and that sharing is limited "as much as possible" per GDPR. Not suitable for an automated, zero-cost, re-fetchable pipeline (CLAUDE.md's "zero-cost" constraint) even if it would eventually work for a one-off snapshot.

**DESNZ solar PV deployment series** (the plan's national fallback pattern): the weekly/monthly "Solar PV deployment" statistical release (`weekly-solar-pv-installation-and-capacity-based-on-registration-date` and successors) is national-level only and was discontinued after June 2021 — not useful even while live, since it never had sub-national geography.

**DESNZ Boiler Upgrade Scheme (BUS) statistics** (heat pump fallback): the routinely-updated BUS collection publishes UK-national quarterly figures only. Geographic breakdowns (by local authority, region, or Parliamentary constituency) exist only as one-off "ad hoc request" releases (e.g. "grants paid by Local Authority", Dec 2023; "redemptions by ... region", Apr 2024) — not a routinely-refreshable series, and local-authority level (South Oxfordshire, ~140,000 population) is far coarser than parish (Cholsey, ~4,400) for the other 8 comparators' dashboard tiles too, not just Cholsey's.

**Ofgem FIT installation reports** (PV fallback): the collection page (`ofgem.gov.uk/.../public-reports-and-data-fit/installation-reports`) confirms quarterly "installation reports" exist, describing "a breakdown of accredited installations under the FIT within a specific quarter" — but its actual download links are not present in the page's static HTML (loaded via a JS-driven document system), so this session could not verify the real file's postcode-district granularity or a stable discovery pattern without further investigation (e.g. headless-browser rendering, not attempted here). FIT also closed to new applicants in 2019, so even if accessible, it would only cover installations up to that date — not current uptake as spec §3 requires ("current" = latest available year).

## Decision (proposed, pending Q-011)

No fetcher has been built for metrics 5/6 yet. Genuinely open, not something this session should guess at:

1. Accept a coarser-than-parish resolution for solar PV/heat pumps (e.g. local-authority BUS ad-hoc figures, flagged `resolution=local_authority` in provenance, refreshed only when a new ad-hoc release happens to appear) — a real deviation from spec §3's stated method, not just an implementation detail.
2. Pursue the MCS data-request process for a one-off postcode-level extract (incurs unknown cost, GDPR-limited, and wouldn't be automatable for `make refresh` — would need periodic manual re-requests).
3. Invest more investigation time in Ofgem's FIT installation reports specifically (headless-browser fetch to find the real download links, then verify postcode-district granularity) — the only lead not yet fully exhausted, but PV-only and capped at 2019.
4. Defer metrics 5/6 entirely (mark as "not available" on the dashboard with a stated reason) until a better source is found.

## Consequences

- P2.7 is logged as `blocked` in STATUS.md pending Q-011, not `todo` or `done` — the plan's own escalation path (CLAUDE.md: "Raise spec-level, scope, stack or comparator decisions with the project lead... don't decide them unilaterally").
- `config/sources.yaml`'s `mcs_installations` entry's `licence: "TBD"` and `discovery_rule` are updated with this investigation's findings but not resolved to a concrete `download_url`.
- Phase 2 can still reach its exit criteria with P2.7 logged as blocked and the rest of the phase's work packages done, per CLAUDE.md ("as many as can be, with the rest logged as blocked").
