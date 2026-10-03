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
];

for (const route of routes) {
  test(`/${route} loads with one h1 and no console errors`, async ({
    page,
  }) => {
    const errors: string[] = [];
    page.on(
      "response",
      (r) => r.status() >= 400 && errors.push(`${r.status()} ${r.url()}`),
    );
    page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
    page.on("pageerror", (e) => errors.push(e.message));
    const response = await page.goto(route);
    expect(response?.status()).toBe(200);
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.locator("main#main")).toBeVisible();
    expect(errors).toEqual([]);
  });
}

test("every nav link resolves", async ({ page, request }) => {
  await page.goto("");
  const hrefs = await page
    .locator("nav a")
    .evaluateAll((as) => as.map((a) => (a as HTMLAnchorElement).href));
  expect(hrefs.length).toBeGreaterThanOrEqual(8);
  for (const h of hrefs) expect((await request.get(h)).status()).toBe(200);
});

test("compare page shows one comparator column when JS is on", async ({
  page,
}) => {
  await page.goto("compare/");
  await expect(page.locator("th[data-comparator]:visible")).toHaveCount(1);
  await page.selectOption("#comparator", { index: 1 });
  await expect(page.locator("th[data-comparator]:visible")).toHaveCount(1);
});

test("home page shows five tiles", async ({ page }) => {
  await page.goto("");
  await expect(page.locator("li.tile")).toHaveCount(5);
});
