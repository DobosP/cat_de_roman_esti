import { test, expect } from "@playwright/test";
import { games, deterministicStarts, start } from "./games.mjs";

const game = games.find(({ key }) => key === "conexiuni");

for (const width of [320, 390]) for (const textScale of [1, 2]) {
  test(`selection and remaining mistakes never overlap at ${width}px and ${textScale * 100}% text`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await deterministicStarts(page, game);
    await start(page, game);
    if (textScale === 2) await page.addStyleTag({ content: "html { font-size: 200% !important; }" });
    await page.evaluate(() => globalThis.document.fonts.ready);
    for (const selected of [0, 1, 2, 3, 4]) {
      if (selected) await page.locator(".connections-grid button").nth(selected - 1).click();
      await expect(page.locator(".next-move-progress")).toHaveText(`${selected}/4`);
      await expect(page.getByRole("img", { name: "4 greșeli disponibile", exact: true })).toBeVisible();
      const boxes = await page.locator(".connections-coach").evaluate((element) => ({
        parent: element.getBoundingClientRect().toJSON(),
        parts: [...element.querySelectorAll(":scope > span:not(.next-move-icon)")].map((part) => ({
          rect: part.getBoundingClientRect().toJSON(), client: part.clientWidth, scroll: part.scrollWidth,
        })),
      }));
      for (const { rect, client, scroll } of boxes.parts) {
        expect(rect.width).toBeGreaterThan(35);
        expect(rect.left).toBeGreaterThanOrEqual(boxes.parent.left);
        expect(rect.right).toBeLessThanOrEqual(boxes.parent.right);
        expect(scroll).toBeLessThanOrEqual(client + 1);
      }
      for (let a = 0; a < boxes.parts.length; a += 1) for (let b = a + 1; b < boxes.parts.length; b += 1) {
        const first = boxes.parts[a].rect, second = boxes.parts[b].rect;
        const overlaps = first.left < second.right && second.left < first.right && first.top < second.bottom && second.top < first.bottom;
        expect(overlaps, `parts ${a} and ${b} must stay separate`).toBe(false);
      }
      expect(await page.locator(".connections-screen").evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
    }
  });
}
