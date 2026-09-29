/**
 * Small formatting helpers shared across the dashboard's pages and charts.
 *
 * These start trivial in P0.5 and grow in Phase 4/5 (development-plan.md
 * §3, P4.2/P5.2) once real metric data exists — e.g. unit-aware number
 * formatting and the "latest available: YYYY" year label the spec (§3)
 * requires on every tile.
 */

/** Formats a data year for display, e.g. "latest available: 2023". */
export function formatLatestYearLabel(year: number): string {
  return `latest available: ${year}`;
}
