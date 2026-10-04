import { expect, test } from "@playwright/test";

test("3D map loads, switches layer and opens a pin card from the keyboard", async ({
  page,
}) => {
  test.setTimeout(90_000);
  await page.goto("");
  await page.waitForSelector("[data-map-island][data-state=ready]", {
    timeout: 45_000,
  });
  await expect(page.locator("canvas.map-canvas")).toHaveAttribute(
    "data-ready",
    "true",
  );

  await page.click('.chip[data-layer-id="canopy"]');
  await expect(page.locator('.chip[data-layer-id="canopy"]')).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  const pin = page.locator('[data-layer-pins="canopy"] .map-pin-subject');
  await expect(pin).toBeVisible();
  await expect(pin.locator(".pin-value")).toHaveText("10.4%");

  await pin.focus();
  await page.keyboard.press("Enter");
  const card = page.locator("#card-canopy-E04012474");
  await expect(card).toBeVisible();
  await expect(card).toContainText("Source:");
  await expect(card).toContainText("Worse than South Oxfordshire");
  await page.keyboard.press("Escape");
  await expect(card).toBeHidden();
  await expect(pin).toBeFocused();
});

test("arrow keys rotate and plus/minus zoom without errors", async ({
  page,
}) => {
  test.setTimeout(90_000);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("");
  await page.waitForSelector("[data-map-island][data-state=ready]", {
    timeout: 45_000,
  });
  await page.locator("canvas.map-canvas").focus();
  for (const k of ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "+", "-"])
    await page.keyboard.press(k);
  expect(errors).toEqual([]);
});

test("without WebGL the flat map and every figure remain available", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const orig = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (
      this: HTMLCanvasElement,
      type: string,
      ...rest: unknown[]
    ) {
      if (type.startsWith("webgl")) return null;
      return (orig as (...a: unknown[]) => unknown).call(
        this,
        type,
        ...rest,
      ) as never;
    } as never;
  });
  await page.goto("metrics/canopy/");
  await page.waitForSelector("[data-map-island][data-state=fallback]", {
    timeout: 15_000,
  });
  await expect(page.locator(".map-poster")).toBeVisible();
  await expect(page.locator("[data-map-status]")).toContainText(
    "not available",
  );
  const pin = page.locator(".map-pin-subject");
  await pin.click();
  await expect(page.locator("#card-canopy-E04012474")).toBeVisible();
});

test("reduced motion: the map still loads and shows final values immediately", async ({
  browser,
}) => {
  const ctx = await browser.newContext({ reducedMotion: "reduce" });
  const page = await ctx.newPage();
  await page.goto("metrics/canopy/");
  await page.waitForSelector("[data-map-island][data-state=ready]", {
    timeout: 45_000,
  });
  await expect(page.locator(".map-pin-subject .pin-value")).toHaveText("10.4%");
  await ctx.close();
});

test("solar PV map says plainly that only Cholsey has a figure", async ({
  page,
}) => {
  await page.goto("metrics/solar_pv/");
  await expect(page.locator(".map-pin .pin-none").first()).toBeVisible();
  await expect(page.locator("[data-comparator-gap]")).toBeVisible();
});
