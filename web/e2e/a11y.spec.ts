import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const routes = [
  "",
  "metrics/canopy/",
  "metrics/greenspace/",
  "metrics/home_energy/",
  "metrics/solar_pv/",
  "metrics/heat_pump/",
  "compare/",
  "methodology/",
  "glossary/",
  "about/",
];

// Plan Phase 7: zero serious or critical axe violations on every page,
// with all chart data tables expanded so their contents are checked too.
/** Pretend WebGL is missing so the flat-map fallback renders quickly. */
async function withoutWebGL(page: import("@playwright/test").Page) {
  await page.addInitScript(() => {
    const orig = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (
      this: HTMLCanvasElement,
      type: string,
      ...rest: unknown[]
    ) {
      if (type.startsWith("webgl") || type === "experimental-webgl")
        return null;
      return (orig as (...a: unknown[]) => unknown).call(
        this,
        type,
        ...rest,
      ) as never;
    } as never;
  });
}

for (const route of routes) {
  test(`/${route}: no serious or critical axe violations (flat-map fallback)`, async ({
    page,
  }) => {
    await withoutWebGL(page);
    await page.goto(route);
    await page.evaluate(() =>
      document.querySelectorAll("details").forEach((d) => (d.open = true)),
    );
    const { violations } = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"])
      .analyze();
    const bad = violations.filter(
      (v) => v.impact === "serious" || v.impact === "critical",
    );
    expect(
      bad.map(
        (v) =>
          `${v.id}: ${v.help} (${v.nodes.length} nodes, e.g. ${v.nodes[0]?.target})`,
      ),
    ).toEqual([]);
  });
}

for (const route of routes) {
  test(`/${route}: no horizontal scroll at 360 px`, async ({ page }) => {
    await page.setViewportSize({ width: 360, height: 800 });
    await page.goto(route);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
  });
}

test("tap targets (nav links, summaries, select) are at least 44 px tall at 360 px", async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 800 });
  for (const route of ["", "metrics/home_energy/", "compare/"]) {
    await page.goto(route);
    const heights = await page
      .locator("nav a, summary, select, .opportunities a")
      .evaluateAll((els) =>
        els
          .filter((e) => (e as HTMLElement).offsetParent !== null)
          .map(
            (e) =>
              [
                e.textContent?.trim().slice(0, 30),
                e.getBoundingClientRect().height,
              ] as const,
          ),
      );
    const small = heights.filter(([, h]) => h < 43.5);
    expect(small, route).toEqual([]);
  }
});

for (const route of ["", "metrics/home_energy/"]) {
  test(`/${route}: no serious or critical axe violations with the 3D map running`, async ({
    page,
  }) => {
    test.setTimeout(90_000);
    await page.goto(route);
    await page.waitForSelector("[data-map-island][data-state=ready]", {
      timeout: 45_000,
    });
    await page.evaluate(() =>
      document.querySelectorAll("details").forEach((d) => (d.open = true)),
    );
    const { violations } = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"])
      .analyze();
    const bad = violations.filter(
      (v) => v.impact === "serious" || v.impact === "critical",
    );
    expect(
      bad.map(
        (v) =>
          `${v.id}: ${v.help} (${v.nodes.length} nodes, e.g. ${v.nodes[0]?.target})`,
      ),
    ).toEqual([]);
  });
}
