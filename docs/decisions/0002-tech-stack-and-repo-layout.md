# 0002. Tech stack and repository layout

- **Status:** Proposed. Awaiting confirmation by the project lead (Q-001 in STATUS.md).
- **Date:** 2026-09-27
- **Deciders:** Planning session (proposal), project lead (confirmation)
- **Related:** P0.2–P0.7; spec §5, §7; development-plan.md §2

## Context

Spec §7 suggests "a static site generator or simple React/Next.js front end", any standard JS charting library, Python (pandas/geopandas) for ETL, and GitHub Pages plus Actions. Its constraints are zero hosting cost, maintainability by a non-specialist, WCAG 2.1 AA, and every number showing provenance. The spec leaves the specific front-end framework and chart library open.

## Options considered

**Front end**
1. **Next.js (static export) + Recharts.** Familiar, but a heavy React runtime for a mostly static site, and static export has rough edges on GitHub Pages sub-paths. Content editing needs MDX or JSX knowledge.
2. **Astro (static) + Observable Plot.** Ships HTML with minimal JS. Markdown content collections let non-developers edit copy through a GitHub web edit. Plot renders plain SVG that is easy to pair with accessible tables. Needs islands for interactive tooltips, which Astro supports natively.
3. **Plain HTML + Chart.js.** Minimal tooling, but canvas charts are harder to make accessible, and templating many metric pages by hand gets error-prone.

**Pipeline**
1. **Python + pip/venv.** Standard, but slower and less reproducible installs.
2. **Python + uv (lockfile).** One-command, reproducible and fast. Good for CI and for cloud agent sessions.

**Processed data format**
1. **Parquet.** Compact, but binary, so data changes aren't visible in PR diffs.
2. **SQLite.** Queryable, but binary diffs again.
3. **CSV (canonical) + generated JSON for the site.** Human-readable diffs in refresh PRs, so a councillor can see what changed. The volume is tiny.

## Decision (proposed)

- **Pipeline:** Python 3.12, `uv`, `geopandas`/`shapely`/`pyogrio`, `pandera`, `pytest`, `ruff`.
- **Processed store:** `data/processed/metrics.csv` is canonical, with the provenance columns in plan §2.3. `export.py` generates the site JSON. Raw downloads are git-ignored. A committed manifest records the URL, sha256 and retrieval date of each download.
- **Front end:** Astro (static output) + TypeScript + Observable Plot. Vitest for unit tests. Playwright + axe-core for end-to-end and accessibility tests.
- **Hosting/CI:** GitHub Pages; GitHub Actions for CI, deploy and the monthly refresh.
- **Interface:** a `Makefile` with `setup`, `test`, `lint`, `refresh` and `site`.
- **Layout:** as in development-plan.md §2.2.

## Consequences

- Refresh PRs show readable CSV diffs, which supports human review before merge (spec §7).
- Non-developers can edit explainer and opportunity copy as Markdown.
- Contributors need Node and Python. `make setup` hides this.
- Raw files aren't in git. Reproducibility relies on upstream availability plus the manifest's sha256. If an upstream file disappears, we can't re-fetch that exact vintage. This risk is accepted given the file sizes (OS Open Greenspace is hundreds of MB). Small clipped extracts may be committed under `data/interim/` for audit.
- If the project lead prefers a different framework, write ADR-0003 to supersede this one before P0.5.
