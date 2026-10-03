/** Typed loaders: the site reads data only through these functions. */
import metricsJson from "@data/metrics.json";
import sourcesJson from "@data/sources.json";
import areasJson from "@data/areas.json";
import configJson from "@data/metric_config.json";
import type { Area, MetricConfig, MetricRow, Source, Tile } from "./types";

export const SUBJECT_CODE = "E04012474";

export interface Dataset {
  metrics: Record<string, MetricRow[]>;
  sources: Record<string, Source>;
  areas: Record<string, Area>;
  config: MetricConfig;
}

export const dataset: Dataset = {
  metrics: metricsJson as unknown as Record<string, MetricRow[]>,
  sources: sourcesJson as unknown as Record<string, Source>,
  areas: areasJson as unknown as Record<string, Area>,
  config: configJson as unknown as MetricConfig,
};

export function getTiles(ds: Dataset = dataset): Tile[] {
  return ds.config.tiles;
}

export function getTile(id: string, ds: Dataset = dataset): Tile | undefined {
  return ds.config.tiles.find((t) => t.id === id);
}

/** All years for one area and metric, oldest first. */
export function getSeries(
  metricId: string,
  areaCode: string,
  ds: Dataset = dataset,
): MetricRow[] {
  return (ds.metrics[metricId] ?? [])
    .filter((r) => r.area_code === areaCode)
    .sort((a, b) => a.year - b.year);
}

/** Latest available row, or undefined if the area has no data (never
 * interpolated or back-filled). */
export function getLatest(
  metricId: string,
  areaCode: string,
  ds: Dataset = dataset,
): MetricRow | undefined {
  return getSeries(metricId, areaCode, ds).at(-1);
}

export function areaCodesByRole(
  role: Area["role"],
  ds: Dataset = dataset,
): string[] {
  return Object.entries(ds.areas)
    .filter(([, a]) => a.role === role)
    .map(([code]) => code);
}

/** Cholsey, then comparators, then district and national: the three
 * reference points always appear together. */
export function getComparisonAreas(ds: Dataset = dataset): string[] {
  return [
    ...areaCodesByRole("subject", ds),
    ...areaCodesByRole("comparator", ds),
    ...areaCodesByRole("district", ds),
    ...areaCodesByRole("national", ds),
  ];
}

export function getReferenceRows(metricId: string, ds: Dataset = dataset) {
  const first = (role: Area["role"]) =>
    areaCodesByRole(role, ds)
      .map((c) => getLatest(metricId, c, ds))
      .find((r) => r !== undefined);
  return { district: first("district"), national: first("national") };
}

/** Prefix a site-relative path with Astro's configured base. */
export function href(path: string): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, "");
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}
