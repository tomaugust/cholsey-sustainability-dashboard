import { readFileSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { expect, test } from "@playwright/test";

const sources = JSON.parse(
  readFileSync(new URL("../src/data/sources.json", import.meta.url), "utf-8"),
) as Record<string, { attribution_text?: string }>;

test("footer carries the OGL text, every source attribution, refresh date and repo link", async ({
  page,
}) => {
  for (const route of ["", "metrics/canopy/", "methodology/"]) {
    await page.goto(route);
    const footer = page.locator("footer");
    await expect(footer).toContainText("Open Government Licence v3.0");
    for (const s of Object.values(sources)) {
      if (s.attribution_text)
        await expect(footer).toContainText(s.attribution_text);
    }
    await expect(footer.locator("time")).toHaveAttribute(
      "datetime",
      /^\d{4}-\d{2}-\d{2}$/,
    );
    await expect(
      footer.locator('a[href*="github.com/tomaugust"]'),
    ).toBeVisible();
  }
});

test("pages have description, canonical, social tags and (until launch) noindex", async ({
  page,
}) => {
  await page.goto("metrics/canopy/");
  await expect(page.locator('meta[name="description"]')).toHaveAttribute(
    "content",
    /Cholsey/,
  );
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
    "href",
    /\/metrics\/canopy\/$/,
  );
  await expect(page.locator('meta[property="og:image"]')).toHaveAttribute(
    "content",
    /social-card\.png$/,
  );
  await page.goto("");
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
    "href",
    /dashboard\/$/,
  );
  await page.goto("metrics/canopy/");
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute(
    "content",
    /noindex/,
  );
  const img = await page.request.get("social-card.png");
  expect(img.status()).toBe(200);
});

test("sitemap lists every page", async ({ page }) => {
  const res = await page.request.get("sitemap.xml");
  expect(res.status()).toBe(200);
  const xml = await res.text();
  for (const p of [
    "metrics/canopy/",
    "metrics/home_energy/",
    "compare/",
    "methodology/",
    "glossary/",
    "about/",
  ]) {
    expect(xml).toContain(p);
  }
});

async function gzipTotal(
  page: import("@playwright/test").Page,
  filter: (url: string) => boolean,
) {
  const pending: Promise<number>[] = [];
  page.on("response", (r) => {
    if (r.request().resourceType() === "font" || !filter(r.url())) return;
    pending.push(
      r
        .body()
        .then((b) => gzipSync(b).length)
        .catch(() => 0),
    );
  });
  return async () => (await Promise.all(pending)).reduce((a, b) => a + b, 0);
}

test("home initial load is under 500 KB (gzip estimate, excluding fonts and the lazy 3D chunk)", async ({
  browser,
}) => {
  // JavaScript off: the server-rendered page plus its CSS, images and scripts as first delivered.
  const ctx = await browser.newContext({ javaScriptEnabled: false });
  const page = await ctx.newPage();
  const total = await gzipTotal(page, () => true);
  await page.goto("", { waitUntil: "load" });
  expect(await total()).toBeLessThan(500 * 1024);
  await ctx.close();
});

test("home initial load with JavaScript on (lazy 3D chunk excluded) is under 500 KB", async ({
  page,
}) => {
  const lazy = /\/_astro\/(scene|terrain|imagery|parishes|greenspace|meta)\./;
  const total = await gzipTotal(page, (u) => !lazy.test(u));
  await page.goto("", { waitUntil: "load" });
  expect(await total()).toBeLessThan(500 * 1024);
});

test("the lazily loaded 3D chunk, with its baked assets, is under 450 KB (gzip estimate)", async ({
  page,
}) => {
  const total = await gzipTotal(page, (u) =>
    /\/_astro\/(scene|terrain|imagery|parishes|greenspace|meta)\./.test(u),
  );
  await page.goto("", { waitUntil: "load" });
  await page.waitForSelector(
    "[data-map-island][data-state=ready], [data-map-island][data-state=fallback]",
    {
      timeout: 30_000,
    },
  );
  const bytes = await total();
  expect(bytes).toBeGreaterThan(50 * 1024);
  expect(bytes).toBeLessThan(450 * 1024);
});
