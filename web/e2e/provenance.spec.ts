import { readFileSync } from "node:fs";
import { expect, test } from "@playwright/test";

const pages = [
  "",
  "metrics/canopy/",
  "metrics/greenspace/",
  "metrics/home_energy/",
  "metrics/solar_pv/",
  "metrics/heat_pump/",
  "compare/",
];

// Provenance gate (development-plan.md Phase 5): zero exceptions.
for (const route of pages) {
  test(`/${route}: every [data-value] has a provenance element with source, geography, year`, async ({
    page,
  }) => {
    await page.goto(route);
    const problems = await page.evaluate(() => {
      const out: string[] = [];
      const els = document.querySelectorAll("[data-value]");
      if (els.length === 0) out.push("no [data-value] elements found");
      els.forEach((el) => {
        const id = el.getAttribute("data-prov-id");
        const prov = id ? document.getElementById(id) : null;
        if (!prov || !prov.classList.contains("provenance")) {
          out.push(
            `no provenance for ${id ?? "(no id)"}: ${el.textContent?.trim().slice(0, 40)}`,
          );
          return;
        }
        for (const f of ["source", "geography", "year"]) {
          const t = prov
            .querySelector(`[data-field="${f}"]`)
            ?.textContent?.trim();
          if (!t) out.push(`${id}: empty ${f}`);
        }
      });
      return out;
    });
    expect(problems).toEqual([]);
  });
}

test("provenance ids are unique per page", async ({ page }) => {
  for (const route of pages) {
    await page.goto(route);
    const dupes = await page.evaluate(() => {
      const seen = new Set<string>();
      const d: string[] = [];
      document.querySelectorAll("[id]").forEach((e) => {
        if (seen.has(e.id)) d.push(e.id);
        seen.add(e.id);
      });
      return d;
    });
    expect(dupes, route).toEqual([]);
  }
});

// Three-points rule: every trend and bar chart has Cholsey and a district/national
// reference, plus a comparator wherever the data has one. Where it has none (MCS
// solar/heat pump, ADR-0007) the page must say so explicitly.
for (const route of pages.filter((r) => r.startsWith("metrics/"))) {
  test(`/${route}: charts satisfy the three-points rule`, async ({ page }) => {
    await page.goto(route);
    const charts = page.locator("figure.chart");
    expect(await charts.count()).toBeGreaterThanOrEqual(2);
    for (let i = 0; i < (await charts.count()); i++) {
      const chart = charts.nth(i);
      const roles = await chart
        .locator("[data-role]")
        .evaluateAll((els) => [
          ...new Set(els.map((e) => e.getAttribute("data-role"))),
        ]);
      expect(roles).toContain("subject");
      expect(roles.some((r) => r === "district" || r === "national")).toBe(
        true,
      );
      if (!roles.includes("comparator")) {
        await expect(
          page.locator("[data-comparator-gap]").first(),
        ).toBeVisible();
      }
    }
  });
}

test("tile year labels equal the data's latest year, not the calendar year", async ({
  page,
}) => {
  const metrics = JSON.parse(
    readFileSync(new URL("../src/data/metrics.json", import.meta.url), "utf-8"),
  ) as Record<string, Array<{ area_code: string; year: number }>>;
  await page.goto("");
  const labels = await page
    .locator("[data-tile] [data-metric]")
    .evaluateAll((els) =>
      els.map((e) => ({
        metric: e.getAttribute("data-metric")!,
        text: e.querySelector(".year")?.textContent?.trim(),
      })),
    );
  expect(labels.length).toBe(6);
  for (const l of labels) {
    const max = Math.max(
      ...metrics[l.metric]
        .filter((r) => r.area_code === "E04012474")
        .map((r) => r.year),
    );
    expect(l.text).toBe(`latest available: ${max}`);
  }
});

test("hover/focus on a chart mark shows its provenance", async ({ page }) => {
  await page.goto("metrics/canopy/");
  const mark = page.locator("figure[data-chart=bars] .mark").first();
  await mark.focus();
  await expect(
    page.locator("figure[data-chart=bars] .chart-detail dl"),
  ).toContainText("Geography used");
});
