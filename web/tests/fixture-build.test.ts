import { execFileSync } from "node:child_process";
import {
  cpSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";

// End-to-end proof there are no hard-coded numbers: build the site against a
// fixture copy of the JSON with one changed value and check it appears.
describe("fixture build", () => {
  it(
    "shows a changed JSON value on the built pages",
    { timeout: 120_000 },
    () => {
      const dir = mkdtempSync(path.join(tmpdir(), "site-data-"));
      cpSync("src/data", dir, { recursive: true });
      const file = path.join(dir, "metrics.json");
      const metrics = JSON.parse(readFileSync(file, "utf-8"));
      const rows = metrics.canopy.filter(
        (r: { area_code: string }) => r.area_code === "E04012474",
      );
      rows[rows.length - 1].value = 77.7;
      writeFileSync(file, JSON.stringify(metrics));

      const out = path.join(dir, "dist");
      execFileSync("npx", ["astro", "build", "--outDir", out], {
        env: { ...process.env, SITE_DATA_DIR: dir },
        stdio: "pipe",
      });

      const home = readFileSync(path.join(out, "index.html"), "utf-8");
      const detail = readFileSync(
        path.join(out, "metrics/canopy/index.html"),
        "utf-8",
      );
      expect(home).toContain("77.7%");
      expect(detail).toContain("77.7%");
      expect(readdirSync(out)).toContain("compare");
    },
  );
});
