/** Shapes of the generated JSON in src/data/ (ADR-0013). The pipeline's
 * METRICS_CSV_SCHEMA (checked by pipeline/tests/contract) is the authority;
 * these mirror it. The site never computes provenance, only displays it. */

export type AreaRole = "subject" | "comparator" | "district" | "national";
export type Flag =
  "none" | "parish_estimate" | "suppression_fallback" | "partial_coverage";
export type Method =
  "direct" | "area_weighted" | "address_weighted" | "postcode_sum" | "clip";
export type Direction = "higher_is_better" | "lower_is_better" | "neutral";

export interface MetricRow {
  area_code: string;
  area_name: string;
  area_role: AreaRole;
  metric_id: string;
  year: number;
  value: number;
  unit: string;
  source_id: string;
  source_name: string;
  source_publisher: string;
  source_url: string;
  retrieved_at: string;
  raw_sha256: string;
  geography_used: string;
  method: Method;
  flag: Flag;
  flag_note: string | null;
}

export interface Area {
  name: string;
  role: AreaRole;
  area_km2?: number;
  notes?: string;
  [key: string]: unknown;
}

export interface Source {
  name: string;
  publisher: string;
  url: string;
  resolution?: string;
  cadence?: string;
  format?: string;
  licence?: string;
  attribution_text?: string;
  notes?: string;
  [key: string]: unknown;
}

export interface MetricDef {
  label: string;
  unit: string;
  direction: Direction;
  similar_band_pct?: number;
  spec_ref?: string;
}

export interface Tile {
  id: string;
  label: string;
  metrics: string[];
}

export interface MetricConfig {
  metrics: Record<string, MetricDef>;
  tiles: Tile[];
}
