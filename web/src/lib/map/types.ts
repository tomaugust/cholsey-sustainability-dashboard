import type { Ring } from "./geo";

export interface MapMeta {
  bbox_uv: { u0: number; u1: number; v0: number; v1: number };
  bbox_lonlat: { west: number; east: number; north: number; south: number };
  terrain: { cols: number; rows: number; min_m: number; max_m: number };
  imagery: { width: number };
  sources: Array<{ attribution: string }>;
}

export interface BakedParish {
  area_code: string;
  name: string;
  role: string;
  geometry: { type: "Polygon"; coordinates: Ring[] };
}

export interface BakedSite {
  function: string;
  geometry: { type: "Polygon" | "MultiPolygon"; coordinates: unknown };
}

export interface MapAssets {
  meta: MapMeta;
  /** Heights in metres, row-major, row 0 = north. */
  heights: Float32Array;
  imagery: HTMLImageElement;
  parishes: BakedParish[];
  sites: BakedSite[];
}

/** One parish on one layer, prepared on the server from the real data. */
export interface LayerItem {
  code: string;
  name: string;
  role: string;
  /** Latest value, or null when the source has no figure for this area. */
  value: number | null;
  /** Short value text, already formatted on the server. */
  label: string;
}

export type LayerMode = "overview" | "prisms" | "greenspace";

export interface LayerConfig {
  id: string;
  mode: LayerMode;
  title: string;
  /** Reader-facing unit, e.g. "m² per resident"; empty for the overview. */
  unit: string;
  items: LayerItem[];
}
