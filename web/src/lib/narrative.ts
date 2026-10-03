import { compareRows, type Verdict } from "./compare";
import { flagLabel, formatValue } from "./format";
import type { MetricDef, MetricRow } from "./types";

export interface NarrativeInput {
  def: MetricDef;
  cholsey?: MetricRow;
  district?: MetricRow;
  national?: MetricRow;
}

const PHRASE: Record<Verdict, string> = {
  better: "better than",
  similar: "similar to",
  worse: "worse than",
  not_rated: "not comparable with",
};

/** One deterministic sentence per metric. Only Cholsey's own figure is quoted
 * (so it can carry its provenance); the verdicts come from compare.ts. */
export function narrativeSentence(input: NarrativeInput): string {
  const { def, cholsey, district, national } = input;
  if (!cholsey) return `${def.label}: no data is available for Cholsey.`;
  const band = def.similar_band_pct ?? 10;
  const d = compareRows(cholsey, district, def.direction, band).verdict;
  const n = compareRows(cholsey, national, def.direction, band).verdict;
  const value = formatValue(cholsey.value, cholsey.unit);
  const note = flagLabel(cholsey.flag).toLowerCase();
  const est = note ? `, ${note}` : "";
  const lead = `${def.label} in Cholsey is ${value} (${cholsey.year}${est})`;
  if (!district && !national)
    return `${lead}; no district or national figure is available.`;
  const parts: string[] = [];
  if (district) parts.push(`${PHRASE[d]} South Oxfordshire`);
  if (national) parts.push(`${PHRASE[n]} England`);
  return `${lead}, ${parts.join(" and ")}.`;
}

/** Plain-text summary of Cholsey's series for the chart fallback. */
export function trendSummary(label: string, series: MetricRow[]): string {
  if (series.length === 0) return `${label}: no Cholsey data.`;
  const first = series[0];
  const last = series[series.length - 1];
  if (series.length === 1) {
    return `${label}: only one year (${first.year}) is available for Cholsey (${formatValue(first.value, first.unit)}), so no trend can be shown.`;
  }
  const dir =
    last.value > first.value
      ? "rose"
      : last.value < first.value
        ? "fell"
        : "was unchanged";
  return `${label} in Cholsey ${dir} from ${formatValue(first.value, first.unit)} in ${first.year} to ${formatValue(last.value, last.unit)} in ${last.year}.`;
}

/** Where Cholsey sits among the areas that have data (1 = highest value);
 * equal values share a rank and are reported as tied, never ordered. */
export function rankSummary(
  label: string,
  rows: MetricRow[],
  cholseyCode: string,
): string {
  const cholsey = rows.find((r) => r.area_code === cholseyCode);
  if (!cholsey) return `${label}: no Cholsey value to rank.`;
  const sorted = [...rows].sort((a, b) => b.value - a.value);
  const rank = 1 + rows.filter((r) => r.value > cholsey.value).length;
  const tied = rows.filter(
    (r) => r.area_code !== cholseyCode && r.value === cholsey.value,
  );
  const tie = tied.length
    ? `, tied with ${tied.map((r) => r.area_name).join(" and ")}`
    : "";
  return `${label}: Cholsey has the ${ordinal(rank)} highest of ${sorted.length} areas with data${tie} (highest ${sorted[0].area_name}, lowest ${sorted[sorted.length - 1].area_name}).`;
}

function ordinal(n: number): string {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return `${n}${s[(v - 20) % 10] ?? s[v] ?? s[0]}`;
}
