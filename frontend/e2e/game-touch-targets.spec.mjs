import { test, expect } from "@playwright/test";
import { games, deterministicStarts, start } from "./games.mjs";

for (const width of [320, 390]) {
  test(`all six games keep visible round controls at least 44px at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    for (const game of games) {
      await deterministicStarts(page, game);
      await start(page, game);
      await page.evaluate(() => globalThis.document.fonts.ready);
      const targets = await page.locator(".screen-pad button").evaluateAll((buttons) =>
        buttons.filter((button) => button.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true }))
          .map((button) => ({ label: button.textContent, rect: button.getBoundingClientRect().toJSON() })));
      expect(targets.length).toBeGreaterThan(0);
      for (const { label, rect } of targets) {
        expect(rect.width, `${game.key}: ${label} width`).toBeGreaterThanOrEqual(44);
        expect(rect.height, `${game.key}: ${label} height`).toBeGreaterThanOrEqual(44);
      }
      expect(await page.locator(".screen-pad").evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
    }
  });
}
