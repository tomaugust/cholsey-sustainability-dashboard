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
  await expect(pin.locator(".pin-value")).toContainText("10.4%");

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
  await expect(page.locator(".map-pin-subject .pin-value")).toContainText(
    "10.4%",
  );
  await ctx.close();
});

test("solar PV map says plainly that only Cholsey has a figure", async ({
  page,
}) => {
  await page.goto("metrics/solar_pv/");
  await expect(page.locator(".map-pin .pin-none").first()).toBeVisible();
  await expect(page.locator("[data-comparator-gap]")).toBeVisible();
});

test("on a phone the flat map shows first and 3D starts on request", async ({
  browser,
}) => {
  const ctx = await browser.newContext({
    viewport: { width: 390, height: 844 },
    hasTouch: true,
    isMobile: true,
  });
  const page = await ctx.newPage();
  await page.goto("");
  const island = page.locator("[data-map-island]");
  await page.waitForTimeout(1500);
  await expect(island).toHaveAttribute("data-state", "poster");
  const start = page.locator("[data-map-start]");
  await expect(start).toBeVisible();
  await start.click();
  await expect(island).toHaveAttribute("data-state", "ready", {
    timeout: 60_000,
  });
  await ctx.close();
});

test("solar PV map explains that one figure is not raised and flags estimates on pins", async ({
  page,
}) => {
  await page.goto("metrics/solar_pv/");
  await expect(page.locator("[data-map-legend]")).toContainText(
    "Only one area",
  );
  await expect(page.locator(".map-pin-subject .pin-value")).toContainText("*");
});

test("on the flat map pins sit inside their parish drawing", async ({
  browser,
}) => {
  const ctx = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 1280, height: 900 },
  });
  const page = await ctx.newPage();
  await page.goto("metrics/canopy/");
  const poster = await page.locator(".map-poster").boundingBox();
  const pin = await page
    .locator('[data-layer-pins="canopy"] .map-pin-subject')
    .boundingBox();
  expect(poster && pin).toBeTruthy();
  const cx = pin!.x + pin!.width / 2;
  expect(cx).toBeGreaterThan(poster!.x);
  expect(cx).toBeLessThan(poster!.x + poster!.width);
  expect(pin!.y + pin!.height).toBeGreaterThan(poster!.y);
  expect(pin!.y).toBeLessThan(poster!.y + poster!.height);
  await ctx.close();
});

test("plain scrolling over the map still scrolls the page", async ({
  page,
}) => {
  test.setTimeout(90_000);
  await page.goto("");
  await page.waitForSelector("[data-map-island][data-state=ready]", {
    timeout: 45_000,
  });
  await page.locator(".map-stage").scrollIntoViewIfNeeded();
  const box = (await page.locator(".map-stage").boundingBox())!;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  const before = await page.evaluate(() => window.scrollY);
  await page.mouse.wheel(0, 300);
  await page.waitForTimeout(500);
  expect(await page.evaluate(() => window.scrollY)).toBeGreaterThan(before);
});
