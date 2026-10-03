import { describe, expect, it } from "vitest";
import { compareValue } from "../src/lib/compare";
import { linear, niceTicks } from "../src/lib/chart";
import { narrativeSentence } from "../src/lib/narrative";
import type { MetricDef, MetricRow } from "../src/lib/types";

describe("compareValue", () => {
  it("rates higher_is_better", () => {
    expect(compareValue(12, 10, "higher_is_better", 10).verdict).toBe("better");
  });
  it("is similar within the band, inclusive", () => {
    expect(compareValue(11, 10, "higher_is_better", 10).verdict).toBe(
      "similar",
    );
    expect(compareValue(9, 10, "lower_is_better", 10).verdict).toBe("similar");
  });
  it("lower_is_better flips better/worse", () => {
    expect(compareValue(5, 10, "lower_is_better", 10).verdict).toBe("better");
    expect(compareValue(15, 10, "lower_is_better", 10).verdict).toBe("worse");
    expect(compareValue(5, 10, "higher_is_better", 10).verdict).toBe("worse");
  });
  it("is not rated for neutral, missing or zero reference", () => {
    expect(compareValue(5, 10, "neutral", 10).verdict).toBe("not_rated");
    expect(compareValue(5, undefined, "higher_is_better", 10).verdict).toBe(
      "not_rated",
    );
    expect(compareValue(5, 0, "higher_is_better", 10).verdict).toBe(
      "not_rated",
    );
  });
});

describe("chart helpers", () => {
  it("maps a linear scale", () => {
    expect(linear([0, 10], [0, 100])(5)).toBe(50);
    expect(linear([3, 3], [0, 100])(3)).toBe(50);
  });
  it("produces nice ticks from zero", () => {
    const { top, ticks } = niceTicks(11001);
    expect(ticks[0]).toBe(0);
    expect(top).toBeGreaterThanOrEqual(11001);
    expect(ticks.at(-1)).toBe(top);
  });
});

const def: MetricDef = {
  label: "Tree canopy cover",
  unit: "%",
  direction: "higher_is_better",
  similar_band_pct: 10,
};
const row = (value: number, year = 2021): MetricRow =>
  ({ value, year, unit: "%" }) as unknown as MetricRow;

describe("narrativeSentence", () => {
  it("covers worse, similar and better", () => {
    expect(
      narrativeSentence({
        def,
        cholsey: row(10),
        district: row(20),
        national: row(10.5),
      }),
    ).toBe(
      "Tree canopy cover in Cholsey is 10.0% (2021), worse than South Oxfordshire and similar to England.",
    );
    expect(
      narrativeSentence({
        def,
        cholsey: row(30),
        district: row(20),
        national: row(20),
      }),
    ).toContain("better than South Oxfordshire and better than England");
  });
  it("handles missing data", () => {
    expect(narrativeSentence({ def })).toContain("no data is available");
    expect(narrativeSentence({ def, cholsey: row(10) })).toContain(
      "no district or national figure",
    );
    expect(
      narrativeSentence({ def, cholsey: row(10), district: row(10) }),
    ).toBe(
      "Tree canopy cover in Cholsey is 10.0% (2021), similar to South Oxfordshire.",
    );
  });
});

import { rankSummary, trendSummary } from "../src/lib/narrative";

describe("summaries", () => {
  const r = (
    area_code: string,
    area_name: string,
    value: number,
    year = 2020,
  ) =>
    ({ area_code, area_name, value, year, unit: "%" }) as unknown as MetricRow;
  it("describes trends, single years and empty series", () => {
    expect(
      trendSummary("X", [r("a", "A", 1, 2010), r("a", "A", 2, 2020)]),
    ).toContain("rose from");
    expect(
      trendSummary("X", [r("a", "A", 3, 2010), r("a", "A", 2, 2020)]),
    ).toContain("fell from");
    expect(trendSummary("X", [r("a", "A", 1)])).toContain("only one year");
    expect(trendSummary("X", [])).toContain("no Cholsey data");
  });
  it("ranks Cholsey", () => {
    const rows = [r("a", "A", 1), r("c", "Cholsey", 5), r("b", "B", 9)];
    expect(rankSummary("X", rows, "c")).toContain("2nd highest of 3");
    expect(rankSummary("X", rows, "zz")).toContain("no Cholsey value");
  });
});

describe("narrative estimate flag", () => {
  it("labels flagged Cholsey values as estimates", () => {
    const flagged = {
      value: 10,
      year: 2021,
      unit: "%",
      flag: "parish_estimate",
    } as unknown as MetricRow;
    expect(narrativeSentence({ def, cholsey: flagged })).toContain(
      "(2021, estimate)",
    );
  });
});
