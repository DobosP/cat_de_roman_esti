// Historical witness extracts from 8186210a, frontend/e2e/gui-m0-replacement-parity.spec.mjs.
// Removed Home progress, setup and history surfaces superseded by ADR-0233.

test("Home keeps the exact six-card order and sole Intrusul highlight without an empty history wall", async ({ page }) => {
  await anonymous(page);
  await historyFixture(page, {});
  await page.goto("/");
  await expect(page).toHaveTitle("Cât de român ești?");
  const cards = page.locator(".games-grid .game-card");
  await expect(cards.locator(".game-card-title")).toHaveText(TITLES);
  const featured = page.locator(".game-card--featured");
  await expect(featured).toHaveCount(1);
  await expect(featured).toHaveAccessibleName("Joacă Intrusul — Începe aici");
  await expect(page.locator(".history-section")).toBeHidden();
  const importHistory = page.getByRole("button", { name: "Importă istoricul", exact: true });
  await expect(importHistory).toBeVisible();
  const bounds = await importHistory.boundingBox();
  expect(bounds.height).toBeGreaterThanOrEqual(44);
  expect(bounds.width).toBeGreaterThanOrEqual(44);
  await tabTo(page, importHistory);
  await expect(importHistory).toBeFocused();
  expect(await storedScores(page)).toBe("{}");
});

test("Home shows actual retained history instead of its first-play import action", async ({ page }) => {
  await anonymous(page);
  const history = existingHistory();
  await historyFixture(page, history);
  await page.goto("/");
  await expect(page.locator(".history-section")).toBeVisible();
  await expect(page.locator(".history-tabs")).toBeVisible();
  await expect(page.locator(".history-section").getByText(LOCAL_ENTRY.detail, { exact: true }).first()).toBeVisible();
  await expect(page.locator(".first-play-tools")).toHaveCount(0);
  expect(await storedScores(page)).toBe(JSON.stringify(history));
});

for (const width of [320, 390, 640]) {
  test(`Home retains one whole card column and a usable import control at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 920 });
    await anonymous(page);
    await historyFixture(page, {});
    await page.goto("/");
    const cards = page.locator(".games-grid .game-card");
    await expect(cards.locator(".game-card-title")).toHaveText(TITLES);
    for (const card of await cards.all()) await expect(card).toHaveCSS("opacity", "1");
    const columns = await page.locator(".games-grid").evaluate((grid) =>
      getComputedStyle(grid).gridTemplateColumns.split(/\s+/).filter(Boolean).length);
    expect(columns).toBe(1);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    const importHistory = page.getByRole("button", { name: "Importă istoricul", exact: true });
    await importHistory.scrollIntoViewIfNeeded();
    const bounds = await importHistory.boundingBox();
    expect(bounds.height).toBeGreaterThanOrEqual(44);
    expect(bounds.width).toBeGreaterThanOrEqual(44);
    await tabTo(page, importHistory);
    await expect(importHistory).toBeInViewport();
  });
}
