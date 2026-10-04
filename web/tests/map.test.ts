import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  latToV,
  lonToU,
  metresPerUnit,
  ringCentroid,
} from "../src/lib/map/geo";
import { decodeHeights } from "../src/lib/map/assets";
import type { MapMeta } from "../src/lib/map/types";

const dir = new URL("../src/data/map/", import.meta.url);
const meta = JSON.parse(
  readFileSync(new URL("meta.json", dir), "utf-8"),
) as MapMeta;

describe("geo", () => {
  it("maps lon/lat to normalised mercator", () => {
    expect(lonToU(0)).toBeCloseTo(0.5);
    expect(latToV(0)).toBeCloseTo(0.5);
    expect(metresPerUnit(0)).toBeCloseTo(40_075_016.686, 0);
    expect(metresPerUnit(60)).toBeCloseTo(40_075_016.686 / 2, 0);
  });
  it("finds the centroid of a square", () => {
    const [x, y] = ringCentroid([
      [0, 0],
      [2, 0],
      [2, 2],
      [0, 2],
      [0, 0],
    ]);
    expect(x).toBeCloseTo(1);
    expect(y).toBeCloseTo(1);
  });
});

describe("baked terrain", () => {
  it("decodes to heights inside the recorded range", () => {
    const b = readFileSync(new URL("terrain.bin", dir));
    const buf = b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
    const h = decodeHeights(buf, meta);
    expect(h.length).toBe(meta.terrain.cols * meta.terrain.rows);
    expect(Math.min(...h)).toBeCloseTo(meta.terrain.min_m, 1);
    expect(Math.max(...h)).toBeCloseTo(meta.terrain.max_m, 1);
  });
  it("refuses a file of the wrong size", () => {
    expect(() => decodeHeights(new ArrayBuffer(10), meta)).toThrow(/expected/);
  });
});

import { dataset } from "../src/lib/data";
import {
  buildHomeLayers,
  buildLayer,
  buildPoster,
  mapAreaCodes,
} from "../src/lib/map/layers";
import parishesJson from "../src/data/map/parishes.json";

describe("map layers (built from the real dataset)", () => {
  it("covers Cholsey and every comparator, never Cholsey alone", () => {
    const codes = mapAreaCodes();
    expect(codes).toContain("E04012474");
    expect(codes.length).toBeGreaterThanOrEqual(9);
  });
  it("home layers are overview plus one per core metric, in tile order", () => {
    const layers = buildHomeLayers();
    expect(layers.map((l) => l.id)).toEqual([
      "overview",
      "canopy",
      "greenspace",
      "electricity",
      "gas",
      "solar_pv",
      "heat_pump",
    ]);
    expect(layers.find((l) => l.id === "greenspace")?.mode).toBe("greenspace");
  });
  it("values come straight from the data, with no data left as null", () => {
    const canopy = buildLayer("canopy");
    const cholsey = canopy.items.find((i) => i.code === "E04012474")!;
    expect(cholsey.value).toBe(10.4);
    expect(cholsey.label).toBe("10.4%");
    const solar = buildLayer("solar_pv");
    expect(solar.items.filter((i) => i.value !== null)).toHaveLength(1);
    expect(solar.items.find((i) => i.value === null)?.label).toBe("No data");
  });
  it("warns on the map when only one area has a figure", () => {
    expect(buildLayer("solar_pv").note).toMatch(/Only one area/);
    expect(buildLayer("heat_pump").note).toMatch(/Only one area/);
    expect(buildLayer("canopy").note).toBe("");
  });
  it("a changed dataset value changes the layer", () => {
    const changed = structuredClone(dataset);
    const rows = changed.metrics.canopy.filter(
      (r) => r.area_code === "E04012474",
    );
    rows[rows.length - 1].value = 55.5;
    expect(
      buildLayer("canopy", changed).items.find((i) => i.code === "E04012474")
        ?.value,
    ).toBe(55.5);
  });
  it("builds a poster with a path and centroid for each parish", () => {
    const meta = JSON.parse(
      readFileSync(new URL("meta.json", dir), "utf-8"),
    ) as MapMeta;
    const poster = buildPoster(parishesJson.features as never, meta.bbox_uv);
    expect(poster.items).toHaveLength(parishesJson.features.length);
    for (const p of poster.items) {
      expect(p.d.startsWith("M")).toBe(true);
      expect(p.cx).toBeGreaterThan(0);
      expect(p.cx).toBeLessThan(100);
      expect(p.cy).toBeGreaterThan(0);
      expect(p.cy).toBeLessThan(100);
    }
  });
});
