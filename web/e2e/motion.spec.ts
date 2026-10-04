import { expect, test } from "@playwright/test";

test("counted numbers end on exactly the formatted data value", async ({
  page,
}) => {
  await page.goto("");
  await page.locator(".tiles").scrollIntoViewIfNeeded();
  await page.waitForTimeout(3000);
  const bad = await page.locator(".tile [data-countup]").evaluateAll((els) =>
    els
      .map((e) => {
        const d = Number((e as HTMLElement).dataset.digits);
        const expected = new Intl.NumberFormat("en-GB", {
          minimumFractionDigits: d,
          maximumFractionDigits: d,
        }).format(Number((e as HTMLElement).dataset.countup));
        return { got: e.textContent, expected };
      })
      .filter((x) => x.got !== x.expected),
  );
  expect(bad).toEqual([]);
});

test("reduced motion shows everything immediately", async ({ browser }) => {
  const ctx = await browser.newContext({ reducedMotion: "reduce" });
  const page = await ctx.newPage();
  await page.goto("");
  await expect(page.locator(".strip").first()).toHaveClass(/\bin\b/);
  await expect(page.locator("h2#b-act")).toHaveCSS("opacity", "1");
  await ctx.close();
});

test("year scrubber moves the cursor and reads out sourced figures", async ({
  page,
}) => {
  await page.goto("metrics/home_energy/");
  const fig = page.locator("figure.chart[data-chart=trend]").first();
  const scrub = fig.locator("[data-scrub]");
  await expect(scrub).toBeVisible();
  const input = scrub.locator("input");
  const year = String(Number(await input.getAttribute("max")) - 3);
  await input.fill(year);
  await expect(fig.locator(".readout")).toContainText(`${year}:`);
  const items = fig.locator(".readout-item");
  expect(await items.count()).toBeGreaterThanOrEqual(2);
  for (const id of await items.evaluateAll((els) =>
    els.map((e) => e.getAttribute("data-prov-id")),
  )) {
    await expect(page.locator(`[id="${id}"].provenance`)).toHaveCount(1);
  }
  await scrub.locator(".play").click();
  await expect(scrub.locator(".play")).toHaveText("Pause");
  await scrub.locator(".play").click();
  await expect(scrub.locator(".play")).toHaveText("Play");
});

test("strips on the home page keep one marker per reference point with provenance", async ({
  page,
}) => {
  await page.goto("");
  const strips = page.locator(".strip");
  expect(await strips.count()).toBe(6);
  for (const strip of await strips.all()) {
    const ids = await strip
      .locator(".strip-track [data-prov-id]")
      .evaluateAll((els) => els.map((e) => e.getAttribute("data-prov-id")));
    expect(ids.length).toBeGreaterThanOrEqual(2);
    for (const id of ids)
      await expect(page.locator(`[id="${id}"].provenance`)).toHaveCount(1);
  }
});
