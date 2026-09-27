# Cholsey Parish Sustainability Dashboard — Technical Specification

Sep 27, 2026 · @Tom

> **Provenance of this file:** copied from Tom's Claude Doc *"Cholsey Parish Sustainability Dashboard — Technical Specification"* (revision 14, exported 2026-09-27). The only change is that the doc's embedded pipeline diagram has been redrawn below in Mermaid. This spec is owned by the project lead. Agents must not edit it. Propose changes through `docs/STATUS.md` → *Open questions* or a decision record (see `docs/development-plan.md` §4).

## 1. Overview & Purpose

Build a public-facing web dashboard for Cholsey Parish Council (South Oxfordshire) that tracks the parish's environmental and energy-transition indicators over time, benchmarks them against neighbouring parishes and the national/district average, and surfaces concrete, locally-actionable opportunities in response to the climate and biodiversity crisis.

**Core narrative the dashboard must tell:**

1. **Where Cholsey stands today** — current tree/green space cover, energy consumption, and low-carbon technology uptake.
2. **How Cholsey compares** — to immediate neighbour parishes, South Oxfordshire district, and England/GB national averages.
3. **How Cholsey is trending** — multi-year direction of travel for each metric (improving, static, worsening).
4. **What the parish council and residents can do about it** — each metric tile links to a specific, achievable action (e.g. tree planting scheme, community solar, retrofit advice sessions).

The intended audience is parish councillors and residents with no data background, so the dashboard should prioritise clear comparative visuals (this-parish-vs-neighbours-vs-national) over raw data tables.

## 2. Geographic Scope

| Level | Code | Name |
| --- | --- | --- |
| Civil parish | E04012474 | Cholsey |
| Electoral ward | E05011701 | Cholsey |
| LSOA (2021) | E01035751 | South Oxfordshire 015H |
| LSOA (2021) | E01028619 | South Oxfordshire 015B |
| MSOA | E02005972 | South Oxfordshire 015 |
| District | E07000179 | South Oxfordshire |
| County | E10000025 | Oxfordshire |
| Region | E12000008 | South East |

Cholsey covers 16.52 km², population 4,498 (2021 Census), OX10 postcode district. The parish sits across parts of more than one LSOA — confirm the exact LSOA-to-parish overlap using the ONS Output Area to Parish lookup before aggregating any LSOA-level dataset, since some LSOA area will fall outside the parish boundary (and vice versa).

**Comparator parishes** (immediate neighbours, for the benchmark charts) — confirm against the ONS Parish boundary layer, but likely candidates given Cholsey's location immediately south of Wallingford between the Thames and the Berkshire Downs:

- Wallingford (town)
- Moulsford
- South Stoke
- Brightwell-cum-Sotwell
- Aston Tirrold & Aston Upthorpe

**Benchmark levels:**

- Cholsey parish (primary unit)
- Comparator parishes (above)
- South Oxfordshire district average
- England (or Great Britain, dataset-dependent) national average

**Boundary source:** ONS Open Geography Portal — "Parishes (December 2023) Boundaries UK BFE/BFC" and "LSOA (2021) Boundaries" — use these to do all spatial joins rather than hand-drawn boundaries.

## 3. Metrics

| # | Metric | Unit | Derivation |
| --- | --- | --- | --- |
| 1 | Tree canopy cover | % of parish land area | Forest Research UK Ward Canopy Cover, area-weighted to parish boundary |
| 2 | Accessible green space | m² per resident; % of parish area | OS Open Greenspace polygons clipped to parish boundary, divided by ONS population |
| 3 | Domestic electricity consumption | mean kWh/meter/year; total MWh | DESNZ LSOA/postcode electricity statistics, LSOA share weighted by address-point count inside parish boundary |
| 4 | Domestic gas consumption | mean kWh/meter/year; total MWh | DESNZ LSOA/postcode gas statistics, same weighting method |
| 5 | Solar PV uptake | installations; % of dwellings; installed kWp | MCS installation database filtered to parish postcodes, divided by ONS dwelling count |
| 6 | Heat pump uptake | installations; % of dwellings | MCS installation database filtered to parish postcodes, divided by ONS dwelling count |
| 7 | EPC / insulation profile (optional stretch) | % of dwellings by EPC band | DLUHC EPC register, filtered to parish postcodes |

Each metric needs: **current value**, **5–10 year trend** (annual series where the source supports it), and a **comparator value** at parish, district and national level. Where postcode-level suppression removes small clusters (see Data Sources), fall back to the LSOA figure and flag it as "parish estimate" in the UI rather than silently interpolating.

## 4. Data Sources

| Dataset | Publisher | Resolution | Cadence | Format | Notes / limitations |
| --- | --- | --- | --- | --- | --- |
| [UK Ward Canopy Cover](https://data-forestry.opendata.arcgis.com/datasets/ecba26cfaf9d4b61bddc0e3284348d79_0/about) | Forest Research | Ward | One-off (2020 imagery) | GIS (Esri REST / Shapefile) | Ward, not parish — needs area-weighted reallocation to Cholsey's parish polygon |
| [OS Open Greenspace](https://www.ordnancesurvey.co.uk/products/os-open-greenspace) | Ordnance Survey | Polygon (site-level) | Periodic refresh | GML/GeoPackage/Shapefile | Free, OGL-licensed; no attribute for canopy, only greenspace type |
| [Sub-national electricity/gas consumption (LSOA/MSOA)](https://www.gov.uk/government/statistics/lower-and-middle-super-output-areas-electricity-consumption) | DESNZ | LSOA/MSOA | Annual | CSV | LSOA domestic-only; MSOA has non-domestic too |
| [Postcode level electricity/gas statistics](https://www.gov.uk/government/publications/postcode-level-domestic-gas-and-electricity-consumption-about-the-data) | DESNZ | Postcode | Annual | CSV | Postcodes suppressed if <5 meters, or if top 2 meters make up >90% of consumption; meters <100kWh/yr excluded |
| [MCS Data Dashboard / installation data](https://mcscertified.com/low-carbon-landscapes/mcs-data-dashboard/) | MCS (Microgeneration Certification Scheme) | Postcode / address | Continuously updated | Dashboard + downloadable data | Covers MCS-certified installs only — undercounts pre-2008 or non-certified installs |
| ONS mid-year population & dwelling counts | ONS | Parish/LSOA | Annual/Census | CSV | Needed to convert absolute counts into per-capita/per-dwelling rates |
| EPC register (optional) | DLUHC | Address/postcode | Continuously updated | CSV via API | Free but requires registration for bulk download |

**Licensing:** all sources above are Open Government Licence (OGL) or equivalent free-to-use — confirm OGL attribution is displayed in the dashboard footer.

**Known limitation to design around:** consumption and installation data lag by 1–2 years at publication (e.g. 2024 data published in 2025/26), so the "current" tile should show the latest available year explicitly labelled, not implied as real-time.

### Traceability requirements

Because this dashboard will be used to back parish council decisions and community asks (grant bids, planning responses, tree-planting proposals), every figure shown must be traceable back to its origin. Each data point carried through the pipeline must retain:

- **Source dataset name** and publisher (e.g. "DESNZ Sub-national electricity consumption, LSOA level")
- **Direct source URL** for that dataset
- **Date retrieved / dataset vintage** (the year the underlying data covers, and the date it was downloaded)
- **Geography level actually used** (e.g. "LSOA E01035751", not just "Cholsey") and the area-weighting/clipping method applied
- **Any suppression, estimation or interpolation flag** (e.g. "postcode suppressed — LSOA estimate used")

This metadata must travel with the value through ingestion, the geographic join, and into the front end — not just be documented separately on a methodology page. Every chart, tile and table cell should expose it on hover/click (a footnote icon or tooltip), so a councillor or resident can always answer "where did this number come from?" without leaving the page.

## 5. Data Pipeline & Architecture

*Five stages carry parish data from source to dashboard:*

```mermaid
flowchart LR
    A["<b>Sources</b><br/>5 open datasets"] --> B["<b>ETL</b><br/>fetch, parse, validate"]
    B --> C["<b>Geo-join</b><br/>clip to parish"]
    C --> D["<b>Data store</b><br/>versioned store"]
    D --> E["<b>Dashboard</b><br/>static site + charts"]
```

**Ingestion & ETL:** a scheduled job (run manually or via cron/GitHub Actions) fetches each source's latest published file, parses it, and validates row counts/schema against the previous run before overwriting anything — a silent schema change in a government CSV should fail loudly, not corrupt the dataset.

**Geographic join:** every dataset arrives at a different geography (ward, LSOA, postcode, address point). Use the ONS lookup tables (Postcode to LSOA to Parish, and the boundary shapefiles) to clip or area-weight each dataset down to the Cholsey parish polygon and the comparator parish polygons. Store the join logic as versioned, re-runnable code (not a one-off manual GIS clip) so it can be re-applied each year as boundaries or LSOA definitions change.

**Data store:** flat files (Parquet/CSV) or a lightweight SQLite database checked into the repo — no need for a hosted database given the small, annually-refreshed data volume. Keep one row per (parish, metric, year), plus provenance columns for source dataset name, source URL, geography level used, retrieval date and any suppression/estimation flag (see Section 4's Traceability requirements) — so every value on the dashboard can be traced back to its source without a separate lookup.

**Refresh cadence:** most source datasets update annually (DESNZ energy stats, MCS installs); canopy cover is closer to a one-off/multi-year refresh. Automate the check with a monthly GitHub Action (Section 7) that re-runs ingestion, validates against the previous run, and opens a pull request only when tests pass — a parish councillor then just needs to approve and merge, no developer required for the routine case.

## 6. Dashboard UX / Views

**Home / overview page**

- Five headline tiles (one per metric), each showing: current value, a small trend sparkline, and a coloured indicator of how Cholsey compares to the district/national average (better / similar / worse).
- A one-paragraph auto-generated or editable narrative summary at the top ("Cholsey's tree cover is X%, below the district average of Y%...").

**Per-metric detail page** (one per metric, same layout)

- Trend line chart: Cholsey vs comparator parishes vs national average, multi-year.
- Bar chart comparing Cholsey to each named comparator parish for the latest year.
- A short "What this means" explainer in plain English.
- An "Opportunities" panel: 2–4 concrete actions tied to that metric (e.g. for tree cover — link to Forestry England's free tree scheme; for heat pumps — link to Oxfordshire's retrofit advice service), each with a short description and an external link.

**Comparison page**

- A single table or radar/spider chart letting a visitor see all metrics for Cholsey vs one chosen comparator parish at once.

**Methodology / sources page**

- Plain-English description of each dataset, its resolution, its "as of" date, and a link to the source — required for credibility with a parish council audience who may ask "where does this number come from?"

**Non-negotiable UX principles:**

- Every number on the page must show its source dataset, geography level and year on hover/click, not just listed separately on a methodology page — this is a hard requirement, not a nice-to-have.
- Comparisons always show three points of reference together (Cholsey / comparators / national), never Cholsey in isolation.
- Mobile-responsive — likely to be viewed on phones at parish council meetings and by residents.

## 7. Tech Stack & Non-Functional Requirements

**Suggested stack** (lightweight, low ongoing cost — appropriate for a parish council with no dedicated IT budget):

- Static site generator or simple React/Next.js front end, deployed free on GitHub Pages / Netlify / Vercel.
- Charting: any standard JS charting library (e.g. Chart.js, Recharts, D3) — no need for a paid BI tool.
- Data processing: Python (pandas/geopandas) for the ETL and geographic join scripts, run offline and committed as static JSON/CSV consumed by the front end — avoids needing a live backend or database server.
- Version control & automation: Git repository hosted on GitHub, deployed via GitHub Pages. A GitHub Action scheduled monthly (cron) checks each source for a newer published file, re-runs the ETL and geographic join, and opens a pull request with the new data — it never auto-merges. The PR only shows as passing if automated tests succeed: schema/column checks against the previous run, sanity-range checks on values, row-count checks, and a check that parish + comparator totals still reconcile. A failing test blocks the PR and keeps the last known-good data live; a human still reviews and merges before anything reaches the published site.

**Non-functional requirements:**

- Must run with zero ongoing hosting cost (or near-zero), since this is a volunteer-run parish project.
- Must be maintainable by a non-specialist after handover — clear README, one-command data refresh.
- Accessible (WCAG 2.1 AA as a target) — this will be viewed by a broad range of residents.
- No personal data collected — this is aggregate public-sector open data only, so no GDPR/privacy concerns beyond standard open-data attribution.

## 8. Build Phases

| Phase | Deliverable | Key tasks |
| --- | --- | --- |
| 1. Boundaries & scope | Confirmed geography | Pull ONS parish/LSOA/ward boundaries for Cholsey; confirm final comparator parish list; resolve LSOA-parish overlap |
| 2. Data ingestion | Raw datasets fetched | Write fetch scripts for each of the 5 sources in Section 4; store raw files with version/date stamps |
| 3. Geographic join | Parish-level metric table | Clip/weight each dataset to Cholsey + comparators + district + national; output one clean table (parish, metric, year, value) |
| 4. Front end skeleton | Navigable but unstyled dashboard | Build the four page types in Section 6 with placeholder data |
| 5. Data wiring & charts | Working charts | Connect real data to trend lines, bar charts, tiles |
| 6. Narrative & opportunities content | Populated explainer text | Write "what this means" and "opportunities" copy per metric, in plain English, reviewed by the parish council |
| 7. Polish & accessibility pass | Launch-ready site | Mobile responsiveness, WCAG check, sources page, methodology page |
| 8. Handover | Documented, repeatable refresh | README covering the annual data-refresh process for a non-technical maintainer |

Each phase should be a reviewable, working increment — the coding agent should not attempt all 8 phases in one pass.
