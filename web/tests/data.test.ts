import { describe, expect, it } from "vitest";
import {
  SUBJECT_CODE,
  dataset,
  getComparisonAreas,
  getLatest,
  getReferenceRows,
  getSeries,
  getTile,
  getTiles,
  href,
} from "../src/lib/data";

describe("tiles", () => {
  it("has the five headline tiles with electricity+gas combined", () => {
    expect(getTiles().map((t) => t.id)).toEqual([
      "canopy",
      "greenspace",
      "home_energy",
      "solar_pv",
      "heat_pump",
    ]);
    expect(getTile("home_energy")?.metrics).toEqual(["electricity", "gas"]);
  });
  it("every tile metric has a definition and data for Cholsey", () => {
    for (const tile of getTiles()) {
      for (const m of tile.metrics) {
        expect(dataset.config.metrics[m]).toBeDefined();
        expect(getLatest(m, SUBJECT_CODE)).toBeDefined();
      }
    }
  });
});

describe("series and latest", () => {
  it("returns series oldest-first and latest as the last year", () => {
    const series = getSeries("electricity", SUBJECT_CODE);
    expect(series.map((r) => r.year)).toEqual(
      [...series.map((r) => r.year)].sort(),
    );
    expect(getLatest("electricity", SUBJECT_CODE)?.year).toBe(
      series.at(-1)?.year,
    );
  });
  it("returns undefined, never a fill-in, for an area with no data", () => {
    expect(getLatest("solar_pv", "E04012496")).toBeUndefined();
  });
});

describe("reference points", () => {
  it("lists Cholsey first and district + national last", () => {
    const areas = getComparisonAreas();
    expect(areas[0]).toBe(SUBJECT_CODE);
    expect(dataset.areas[areas.at(-2)!].role).toBe("district");
    expect(dataset.areas[areas.at(-1)!].role).toBe("national");
  });
  it("provides a district reference for every tile metric", () => {
    for (const tile of getTiles()) {
      for (const m of tile.metrics) {
        expect(getReferenceRows(m).district).toBeDefined();
      }
    }
  });
});

describe("provenance on loaded rows", () => {
  it("every row carries source, geography, method and retrieval date", () => {
    for (const rows of Object.values(dataset.metrics)) {
      for (const r of rows) {
        expect(
          r.source_id &&
            r.source_url &&
            r.geography_used &&
            r.method &&
            r.retrieved_at,
        ).toBeTruthy();
        expect(dataset.sources[r.source_id]).toBeDefined();
      }
    }
  });
});

describe("href", () => {
  it("prefixes the configured base", () => {
    expect(href("/compare/")).toMatch(/\/compare\/$/);
  });
});
