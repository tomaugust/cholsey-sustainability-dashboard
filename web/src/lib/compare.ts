import type { Direction, MetricRow } from "./types";

export type Verdict = "better" | "similar" | "worse" | "not_rated";

export interface Comparison {
  verdict: Verdict;
  /** Signed % difference of value from the reference, undefined if reference is 0 or missing. */
  diffPct?: number;
}

/** Better/similar/worse versus one reference value, using the metric's
 * `direction` and `similar_band_pct` (config/metrics.yaml). A `neutral`
 * direction or a missing/zero reference is "not_rated", never guessed. */
export function compareValue(
  value: number,
  reference: number | undefined,
  direction: Direction,
  similarBandPct: number,
): Comparison {
  if (reference === undefined || reference === 0 || direction === "neutral") {
    return { verdict: "not_rated" };
  }
  const diffPct = ((value - reference) / Math.abs(reference)) * 100;
  if (Math.abs(diffPct) <= similarBandPct)
    return { verdict: "similar", diffPct };
  const higher = diffPct > 0;
  const better = direction === "higher_is_better" ? higher : !higher;
  return { verdict: better ? "better" : "worse", diffPct };
}

export function compareRows(
  row: MetricRow | undefined,
  reference: MetricRow | undefined,
  direction: Direction,
  similarBandPct: number,
): Comparison {
  if (!row) return { verdict: "not_rated" };
  return compareValue(row.value, reference?.value, direction, similarBandPct);
}

const ICON: Record<Verdict, string> = {
  better: "▲",
  similar: "●",
  worse: "▼",
  not_rated: "–",
};
const TEXT: Record<Verdict, string> = {
  better: "Better than",
  similar: "Similar to",
  worse: "Worse than",
  not_rated: "No comparison with",
};

/** Icon + text so the indicator never relies on colour alone. */
export function verdictIcon(v: Verdict): string {
  return ICON[v];
}
export function verdictText(v: Verdict, referenceName: string): string {
  return `${TEXT[v]} ${referenceName}`;
}
