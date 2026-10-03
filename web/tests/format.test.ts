import { describe, expect, it } from "vitest";
import {
  formatLatestYearLabel,
  formatNumber,
  formatUnit,
  formatValue,
} from "../src/lib/format";

describe("formatLatestYearLabel", () => {
  it("formats a year with the required 'latest available' label (spec §3)", () => {
    expect(formatLatestYearLabel(2023)).toBe("latest available: 2023");
  });
});

describe("formatNumber", () => {
  it("uses thousands separators and no decimals for large values", () => {
    expect(formatNumber(3682.27)).toBe("3,682");
  });
  it("keeps decimals for small values", () => {
    expect(formatNumber(10.4)).toBe("10.4");
    expect(formatNumber(2.73)).toBe("2.73");
  });
});

describe("formatUnit / formatValue", () => {
  it("maps known units to reader-friendly labels", () => {
    expect(formatUnit("m2_per_resident")).toBe("m² per resident");
    expect(formatUnit("%_of_dwellings")).toBe("% of dwellings");
  });
  it("passes unknown units through", () => {
    expect(formatUnit("widgets")).toBe("widgets");
  });
  it("attaches a bare % directly to the number", () => {
    expect(formatValue(10.4, "%")).toBe("10.4%");
    expect(formatValue(3682.27, "kWh/meter/year")).toBe(
      "3,682 kWh per meter per year",
    );
  });
});
