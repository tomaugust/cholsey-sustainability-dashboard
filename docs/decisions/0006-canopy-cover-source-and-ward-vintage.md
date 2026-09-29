# 0006. Canopy cover source (Forest Research vs UKCEH Land Cover Map) and a ward-vintage correction

- **Status:** Accepted (resolves Q-008; a technical/data-quality investigation, not a scope/spec/stack decision needing separate sign-off — Q-008 already asked for exactly this evaluation).
- **Date:** 2026-09-29
- **Deciders:** Phase 2 (P2.3) implementation
- **Related:** P2.3; Q-008; development-plan.md risk R2; `pipeline/src/cholsey_pipeline/fetch/forest_research_canopy.py`; `config/sources.yaml`'s `forest_research_canopy`/`ukceh_land_cover_map` entries

## Context

Q-008 (raised during P1.1, answered by Tom 2026-09-28) asked whether to keep the working assumption behind the Forest Research canopy dataset's ward vintage, or investigate switching to UKCEH's Land Cover Map, which "may be more frequently updated." P2.3 exists to do that evaluation before building the canopy fetcher.

## Investigation

**1. What Forest Research's `UK_Ward_Canopy_Cover` dataset actually is.** Looked up its real ArcGIS item metadata (`arcgis.com/sharing/rest/content/items/<id>?f=json`) rather than trusting the "about" page's framing. Real findings, correcting two things this project had previously assumed without checking:
   - It is **not** a single "2020" survey. It's citizen-science i-Tree Canopy data collected **ward-by-ward between 2018 and 2022** — each ward carries its own `survyear` field. Cholsey's own record was surveyed in **2021**.
   - Cholsey's record uses **wardcode `E05009737`**, which does not exist in the current (December 2020) ward boundary layer P1.1 fetched (`E05011701`). Queried the December 2018 ward boundary layer directly and confirmed `E05009737` = "Cholsey" there — South Oxfordshire's wards were recoded/redrawn between the December 2018 and December 2020 editions, and this dataset uses the older one.
   - **Checked whether this actually matters**: fetched both ward polygons and Cholsey's parish polygon, and computed the parish's area-share inside each. Old ward (`E05009737`): 99.4%. Current ward (`E05011701`): 100.0%. The boundaries are a near-exact match for Cholsey specifically, despite the code change — so P1.5's existing ward-area-weight row (1.0, computed against `E05011701`) doesn't need correcting. But this was **luck**, not something the original "working assumption" had actually verified — a different parish/ward pair could easily have a real discrepancy from the same kind of recoding.

**2. What UKCEH's Land Cover Map actually offers.** The 10m-resolution annual raster product (LCM2020 onward) is free for non-commercial use via EIDC and does have real year-over-year releases — a genuine trend, unlike Forest Research's one-point-per-ward data. But it classifies each 10m pixel into **one dominant UK BAP Broad Habitat class** (e.g. "Broadleaved, Mixed and Yew Woodland"), not a canopy-cover percentage. That's a materially different measurement: it would undercount scattered, garden, hedgerow and street trees outside contiguous woodland parcels — exactly the kind of tree cover that matters most for a small, largely residential parish like Cholsey, as opposed to a rural area dominated by actual forest blocks.

## Decision

**1. Keep Forest Research's canopy dataset as metric 1's primary source.** It directly measures canopy cover %, matching the spec's stated metric definition, and switching to UKCEH LCM's woodland-habitat-class % would silently change what the metric actually means (from "tree canopy cover" to "% of area classified as woodland habitat") — a much bigger, undisclosed shift than the trend-vs-no-trend tradeoff Q-008 was actually asking about.

**2. Record UKCEH LCM as a documented stretch/backlog item, not built now.** `config/sources.yaml` has a `ukceh_land_cover_map` entry explaining what it offers and why it isn't a substitute, so a future session doesn't have to redo this investigation from scratch if a real annual woodland-cover trend line is ever wanted as a *supplementary*, clearly-labelled chart (never blended into metric 1's own number, per CLAUDE.md's "flag estimates, never silently interpolate").

**3. Do not correct P1.5's ward-area-weight row** — verified it's still correct for Cholsey (99.4% vs 100.0%, immaterial), so redoing that work would add no value. Documented the verification method (fetch both ward vintages, compute parish-in-ward area share) in case a similar vintage question comes up for a comparator parish later, where the answer might not be as forgiving.

## Consequences

- `config/sources.yaml`'s `forest_research_canopy` entry now has a real `download_url` (the live FeatureServer, found via the ArcGIS item API — not guessed) and corrected `cadence`/`notes` reflecting the real 2018-2022 per-ward survey years, not a fictional single "2020" date.
- `pipeline/src/cholsey_pipeline/fetch/forest_research_canopy.py` (P2.3) fetches by the dataset's own ward codes — callers must not assume a current ONS ward code will match; look up by name first if unsure.
- Q-008 moves to `actioned` in STATUS.md: Tom's suggestion was genuinely investigated (not just noted and deferred), with a real, specific reason for the decision reached.
- **New backlog item**: if a comparator's canopy/ward vintage is ever needed, repeat this ADR's verification method (don't assume the current ward code matches Forest Research's) — South Oxfordshire's ward recoding shows this isn't a hypothetical risk.
