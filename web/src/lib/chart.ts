/** Pure geometry helpers for the build-time SVG charts. */

export interface Scale {
  (v: number): number;
}

export function linear(
  domain: [number, number],
  range: [number, number],
): Scale {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  if (d0 === d1) return () => (r0 + r1) / 2;
  return (v) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);
}

/** "Nice" upper bound and ticks from 0 to max (zero baseline). */
export function niceTicks(
  max: number,
  count = 4,
): { top: number; ticks: number[] } {
  if (max <= 0) return { top: 1, ticks: [0, 1] };
  const raw = max / count;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step =
    [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) ?? mag * 10;
  const top = Math.ceil(max / step) * step;
  const ticks: number[] = [];
  for (let t = 0; t <= top + step / 1e6; t += step)
    ticks.push(Number(t.toFixed(10)));
  return { top, ticks };
}

export function pathFrom(points: Array<[number, number]>): string {
  return points
    .map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`)
    .join(" ");
}

export function slug(s: string): string {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function provId(
  ctx: string,
  row: { metric_id: string; area_code: string; year: number },
) {
  return `p-${ctx}-${row.metric_id}-${row.area_code}-${row.year}`;
}

/** Chart colours: kept in step with the CSS custom properties in global.css.
 * Series are also told apart by width and dash pattern, never colour alone. */
export const CHART = {
  cholsey: "#0b5d3b",
  district: "#1b4f9c",
  national: "#222222",
  comparator: "#6b6b6b",
  comparatorBar: "#767676",
} as const;

/** Axis tick label: whole numbers get thousands separators, no decimals. */
export function tickLabel(v: number): string {
  return Number.isInteger(v)
    ? new Intl.NumberFormat("en-GB").format(v)
    : new Intl.NumberFormat("en-GB", { maximumFractionDigits: 2 }).format(v);
}
