/** Display helpers. Units come from config/metrics.yaml verbatim, so they are
 * mapped here to reader-friendly labels; unknown units pass through. */

const UNIT_LABELS: Record<string, string> = {
  "%": "%",
  m2_per_resident: "m² per resident",
  "kWh/meter/year": "kWh per meter per year",
  "%_of_dwellings": "% of dwellings",
};

export function formatLatestYearLabel(year: number): string {
  return `latest available: ${year}`;
}

export function formatUnit(unit: string): string {
  return UNIT_LABELS[unit] ?? unit;
}

/** Thousands separators; whole numbers above 100, else one decimal
 * (two below 10, so small uptake percentages stay legible). */
export function formatNumber(value: number): string {
  const abs = Math.abs(value);
  const digits = abs >= 100 ? 0 : abs >= 10 ? 1 : 2;
  return new Intl.NumberFormat("en-GB", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

export function formatValue(value: number, unit: string): string {
  const label = formatUnit(unit);
  return label === "%"
    ? `${formatNumber(value)}%`
    : `${formatNumber(value)} ${label}`;
}

export function formatDate(iso: string): string {
  return iso.slice(0, 10);
}
