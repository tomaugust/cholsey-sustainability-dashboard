/** Server-side preparation of map layers from the real dataset (Phase 9).
 * Pure functions: the 3D scene only draws what these return. */
import { dataset, getLatest, type Dataset } from "../data";
import { formatNumber, formatUnit } from "../format";
import { latToV, lonToU, ringCentroid, type Ring } from "./geo";
import type { LayerConfig, LayerItem, LayerMode } from "./types";

const MODE: Record<string, LayerMode> = { greenspace: "greenspace" };

/** Parishes that appear on the map: Cholsey and its comparators. */
export function mapAreaCodes(ds: Dataset = dataset): string[] {
  return Object.entries(ds.areas)
    .filter(([, a]) => a.role === "subject" || a.role === "comparator")
    .map(([code]) => code);
}

function shortLabel(value: number, unit: string): string {
  return unit === "%" ? `${formatNumber(value)}%` : formatNumber(value);
}

export function buildLayer(
  metricId: string,
  ds: Dataset = dataset,
): LayerConfig {
  const def = ds.config.metrics[metricId];
  const items: LayerItem[] = mapAreaCodes(ds).map((code) => {
    const row = getLatest(metricId, code, ds);
    return {
      code,
      name: ds.areas[code].name,
      role: ds.areas[code].role,
      value: row ? row.value : null,
      label: row ? shortLabel(row.value, row.unit) : "No data",
    };
  });
  return {
    id: metricId,
    mode: MODE[metricId] ?? "prisms",
    title: def.label,
    unit: formatUnit(def.unit),
    note:
      items.filter((i) => i.value !== null).length < 2
        ? "Only one area has a figure for this measure, so there is nothing to compare it with on the map."
        : "",
    items,
  };
}

/** The overview layer plus one layer per core metric, in tile order. */
export function buildHomeLayers(ds: Dataset = dataset): LayerConfig[] {
  const overview: LayerConfig = {
    id: "overview",
    mode: "overview",
    title: "Overview",
    unit: "",
    note: "",
    items: mapAreaCodes(ds).map((code) => ({
      code,
      name: ds.areas[code].name,
      role: ds.areas[code].role,
      value: null,
      label: ds.areas[code].role === "subject" ? "Cholsey" : "",
    })),
  };
  const ids = ds.config.tiles.flatMap((t) => t.metrics);
  return [overview, ...ids.map((m) => buildLayer(m, ds))];
}

export interface PosterParish {
  code: string;
  name: string;
  role: string;
  d: string;
  /** Centroid as a percentage of the poster box. */
  cx: number;
  cy: number;
}

/** Flat 2D poster: the nine parishes in Mercator, as SVG paths in a 0-1000 box. */
export function buildPoster(
  parishes: Array<{
    area_code: string;
    name: string;
    role: string;
    geometry: { coordinates: Ring[] };
  }>,
  bbox: { u0: number; u1: number; v0: number; v1: number },
) {
  const W = 1000;
  const H = Math.round((W * (bbox.v1 - bbox.v0)) / (bbox.u1 - bbox.u0));
  const pt = ([lon, lat]: [number, number]): [number, number] => [
    ((lonToU(lon) - bbox.u0) / (bbox.u1 - bbox.u0)) * W,
    ((latToV(lat) - bbox.v0) / (bbox.v1 - bbox.v0)) * H,
  ];
  const items: PosterParish[] = parishes.map((p) => {
    const ring = p.geometry.coordinates[0];
    const d =
      ring
        .map((c, i) => {
          const [x, y] = pt(c);
          return `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
        })
        .join("") + "Z";
    const [cx, cy] = pt(ringCentroid(ring));
    return {
      code: p.area_code,
      name: p.name,
      role: p.role,
      d,
      cx: (cx / W) * 100,
      cy: (cy / H) * 100,
    };
  });
  return { width: W, height: H, items };
}
