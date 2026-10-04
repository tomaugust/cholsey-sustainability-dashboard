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

test("home page weight is under 500 KB (gzip estimate, excluding fonts)", async ({
  page,
}) => {
  const pending: Promise<number>[] = [];
  page.on("response", (r) => {
    if (r.request().resourceType() === "font") return;
    pending.push(
      r
        .body()
        .then((b) => gzipSync(b).length)
        .catch(() => 0),
    );
  });
  await page.goto("", { waitUntil: "networkidle" });
  const sizes = await Promise.all(pending);
  expect(sizes.length).toBeGreaterThan(1);
  expect(sizes.reduce((a, b) => a + b, 0)).toBeLessThan(500 * 1024);
});
